"""API IA de l'équipe Data – Opportunity Radar. Swagger : http://localhost:8000/docs

Elle lit les fichiers JSON de Tech (dossier donnees/) et fait 3 choses :
  1. POST /questions        : 3 questions à poser pour une opportunité, avec leur objectif
  2. GET  /justification/ID : pourquoi cette opportunité est proposée (faits, hypothèses, à confirmer)
  3. POST /compte-rendu     : compte rendu structuré après le rendez-vous

Si Ollama est absent, trop lent ou répond mal, l'API utilise un plan B construit uniquement
avec les données (champ "source" = "simule"). La démo ne plante donc jamais.
"""

import json
import os
import re
from pathlib import Path
from typing import Annotated, Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

API_KEY = os.environ["API_KEY"]
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("MODEL", "llama3.2:1b")
TIMEOUT = float(os.environ.get("AI_TIMEOUT", "30"))
DOSSIER = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "donnees"))


def lire(nom: str):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


CLIENTS = {c["id"]: c for c in lire("clients.json")}
OPPORTUNITES = {o["id"]: o for o in lire("opportunities.json")}
SIGNAUX = lire("signals.json")
RDV = lire("meetings.json")
SYNTHESES = {i["client_id"]: i for i in lire("clients-insights.json")}
PREPAREES = lire("questions_preparees.json")

app = FastAPI(
    title="IA Data – Opportunity Radar",
    version="3.0.0",
    description="Données fictives (jeu de données de Tech). Chaque réponse indique sa source : "
    "`modele` (Ollama), `simule` (plan B) ou `donnees`.",
)


def verifier_cle(x_api_key: Annotated[str, Header()] = "") -> None:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Clé d'API invalide")


Cle = Depends(verifier_cle)


def opportunite(opportunity_id: str) -> dict:
    if opportunity_id not in OPPORTUNITES:
        raise HTTPException(status_code=404, detail=f"Opportunité inconnue : {opportunity_id}")
    return OPPORTUNITES[opportunity_id]


def signaux_de(opportunity_id: str) -> list[dict]:
    return [s for s in SIGNAUX if s["opportunity_id"] == opportunity_id]


def contexte(opp: dict) -> dict:
    """Tout ce que le modèle a le droit de voir, et rien d'autre."""
    return {
        "client": CLIENTS.get(opp["client_id"]),
        "synthese_client": SYNTHESES.get(opp["client_id"], {}).get("summary"),
        "opportunite": opp,
        "signaux": signaux_de(opp["id"]),
        "rendez_vous_passes": [
            {k: m[k] for k in ("date", "questions", "answers", "summary")}
            for m in RDV if m["opportunity_id"] == opp["id"] and m.get("status") == "realise"
        ],
    }


REGLES = (
    "Tu es l'assistant d'un commercial de Givaudan (arômes et parfums). Règles strictes : "
    "utilise UNIQUEMENT les données fournies ; n'invente aucun chiffre, nom ou fait ; "
    "si une information manque, écris « à confirmer » ; ne présente jamais une hypothèse comme un fait ; "
    "réponds en français, en phrases courtes ; réponds UNIQUEMENT avec un objet JSON valide."
)


def demander_json(consigne: str, modele: str, schema: dict | None = None) -> dict | None:
    """Demande une réponse JSON à Ollama. Avec `schema`, Ollama est obligé de respecter cette forme.
    None si panne, lenteur ou JSON invalide."""
    try:
        r = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": modele,
                "messages": [{"role": "system", "content": REGLES}, {"role": "user", "content": consigne}],
                "stream": False,
                "format": schema or "json",
                "options": {"temperature": 0.2},
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return json.loads(r.json()["message"]["content"])
    except Exception:
        return None


# ---------- État de l'API ----------
@app.get("/health")
def health() -> dict:
    try:
        httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3).raise_for_status()
        ollama = "ok"
    except Exception:
        ollama = "indisponible (plan B actif)"
    return {"status": "ok", "model": MODEL, "ollama": ollama, "opportunites": len(OPPORTUNITES)}


# ---------- Compatibilité avec l'API de Tech ----------
class Question(BaseModel):
    question: str


@app.post("/answer", dependencies=[Cle])
def answer(body: Question) -> dict:
    """Question libre (déjà appelée par l'API de Tech)."""
    try:
        r = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": MODEL, "messages": [{"role": "user", "content": body.question}], "stream": False},
            timeout=60,
        )
        r.raise_for_status()
    except Exception:
        raise HTTPException(status_code=503, detail="Modèle indisponible")
    return {"answer": r.json()["message"]["content"], "model": MODEL}


# ---------- 1. Les 3 questions ----------
INFOS = ["Objectifs du client", "Besoin réel", "Contraintes techniques", "Contraintes budgétaires", "Calendrier", "Critères de décision"]


class QuestionsDemande(BaseModel):
    opportunity_id: str = Field(examples=["opp-1a"])
    model: str | None = Field(default=None, description="Modèle Ollama. Par défaut : MODEL du .env")


class QuestionPreparee(BaseModel):
    question: str
    objectif: str
    information_recherchee: str


class QuestionsReponse(BaseModel):
    opportunity_id: str
    questions: list[QuestionPreparee]
    source: Literal["modele", "simule"]
    model: str | None


SCHEMA_QUESTIONS = {
    "type": "object",
    "properties": {"questions": {"type": "array", "minItems": 3, "maxItems": 3, "items": {
        "type": "object",
        "properties": {"question": {"type": "string"}, "objectif": {"type": "string"},
                       "information_recherchee": {"type": "string", "enum": INFOS}},
        "required": ["question", "objectif", "information_recherchee"]}}},
    "required": ["questions"],
}


def extraire_questions(out) -> list[dict]:
    """Récupère toutes les questions, même mal rangées par un petit modèle, et normalise la catégorie."""
    trouvees = []

    def parcourir(x):
        if isinstance(x, dict):
            if isinstance(x.get("question"), str) and x["question"].strip():
                trouvees.append(x)
            for v in x.values():
                parcourir(v)
        elif isinstance(x, list):
            for v in x:
                parcourir(v)

    parcourir(out)
    propres = []
    for q in trouvees:
        brut = str(q.get("information_recherchee", ""))
        info = next((i for i in INFOS if i.lower() in brut.lower()), None)
        objectif = " ".join(str(q.get("objectif", "")).split())
        texte = " ".join(q["question"].split())  # supprime les retours à la ligne du modèle
        if info and objectif and texte.endswith("?") and texte not in [p["question"] for p in propres]:
            propres.append({"question": texte, "objectif": objectif[0].upper() + objectif[1:], "information_recherchee": info})
    return propres[:3]


def questions_plan_b(opp: dict) -> list[dict]:
    """Questions préparées par Data, complétées par des questions types sur les informations manquantes."""
    qs = list(PREPAREES.get(opp["id"], []))
    titre = opp["title"][0].lower() + opp["title"][1:]
    types = [
        {"question": f"Qu'attendez-vous précisément de ce projet : {titre} ?", "objectif": "Comprendre le besoin réel derrière l'opportunité.", "information_recherchee": "Besoin réel"},
        {"question": "Quelles contraintes de formulation, de profil (goût ou parfum) ou de réglementation devons-nous respecter ?", "objectif": "Éviter de proposer une piste inadaptée.", "information_recherchee": "Contraintes techniques"},
        {"question": "Quel calendrier envisagez-vous pour ce projet ?", "objectif": "Évaluer l'urgence et planifier les propositions.", "information_recherchee": "Calendrier"},
        {"question": "Quel budget ou quel coût cible avez-vous en tête ?", "objectif": "Choisir entre une solution existante et un développement spécifique.", "information_recherchee": "Contraintes budgétaires"},
        {"question": "Qui prendra la décision, et selon quels critères ?", "objectif": "Comprendre le processus de décision du client.", "information_recherchee": "Critères de décision"},
    ]
    for t in types:
        if len(qs) >= 3:
            break
        if t["information_recherchee"] not in {q["information_recherchee"] for q in qs}:
            qs.append(t)
    return qs[:3]


@app.post("/questions", dependencies=[Cle])
def questions(body: QuestionsDemande) -> QuestionsReponse:
    opp = opportunite(body.opportunity_id)
    modele = body.model or MODEL
    consigne = (
        "Propose exactement 3 questions à poser au client avant le rendez-vous sur cette opportunité. "
        "Chaque question est ouverte, porte sur une information qui MANQUE dans les données, et ne répète pas "
        "une question déjà posée dont la réponse est connue. "
        'Réponds avec {"questions": [{"question": "...", "objectif": "...", "information_recherchee": "..."}]}, '
        f"où information_recherchee vaut une de ces valeurs : {INFOS}.\n\nDONNÉES :\n"
        + json.dumps(contexte(opp), ensure_ascii=False)
    )
    qs = extraire_questions(demander_json(consigne, modele, SCHEMA_QUESTIONS))
    if len(qs) == 3:
        return QuestionsReponse(opportunity_id=opp["id"], questions=[QuestionPreparee(**q) for q in qs], source="modele", model=modele)
    return QuestionsReponse(opportunity_id=opp["id"], questions=[QuestionPreparee(**q) for q in questions_plan_b(opp)], source="simule", model=None)


# ---------- 2. La justification ----------
SOURCES = {"compte_rendu": "compte rendu", "demande_client": "demande du client", "historique": "historique commercial", "projet": "suivi de projet", "veille_marche": "veille marché"}


@app.get("/justification/{opportunity_id}", dependencies=[Cle])
def justification(opportunity_id: str) -> dict:
    """Pourquoi cette opportunité est proposée. Construit uniquement à partir des signaux (rien d'inventé)."""
    opp = opportunite(opportunity_id)
    sig = signaux_de(opp["id"])
    jour = lambda d: f"{d[8:10]}/{d[5:7]}/{d[:4]}"
    ligne = lambda s: f"{s['description'].rstrip('.')} ({SOURCES.get(s['source_type'], s['source_type'])}, {jour(s['source_date'])}, fiabilité {s['confidence']})"
    faits = [ligne(s) for s in sig if s["evidence_type"] == "fait"]
    hypotheses = [ligne(s) for s in sig if s["evidence_type"] != "fait"]
    a_confirmer = []
    if opp.get("feasibility") == "a_confirmer":
        a_confirmer.append("Faisabilité")
    if not opp.get("estimated_potential"):
        a_confirmer.append("Potentiel commercial (non renseigné)")
    a_confirmer += [f"Vérifier : {s['description'].rstrip('.')}" for s in sig if s["evidence_type"] != "fait"]
    a_confirmer += ["Budget", "Calendrier"]
    if faits:
        texte = f"Cette opportunité s'appuie sur {len(faits)} fait(s) : " + " ; ".join(faits) + "."
        if hypotheses:
            texte += " Elle est renforcée par une hypothèse à vérifier : " + " ; ".join(hypotheses) + "."
    else:
        texte = "Cette opportunité repose uniquement sur des hypothèses, à vérifier avec le client : " + " ; ".join(hypotheses) + "."
    return {
        "opportunity_id": opp["id"],
        "pourquoi": texte,
        "faits": faits,
        "hypotheses": hypotheses,
        "a_confirmer": a_confirmer,
        "prochaine_action": opp.get("next_action"),
        "source": "donnees",
    }


# ---------- 3. Le compte rendu ----------
CHECKLIST = {
    "objectifs_client": "Objectifs du client",
    "besoin_reel": "Besoin réel",
    "contraintes_techniques": "Contraintes techniques",
    "contraintes_budgetaires": "Contraintes budgétaires",
    "calendrier": "Calendrier",
    "criteres_decision": "Critères de décision",
}
RUBRIQUES = ["resume", "besoins", "contraintes_techniques", "contraintes_budgetaires", "calendrier",
             "informations_manquantes", "prochaines_actions", "equipes_internes"]
EQUIPES = [
    (r"texture|technique|stabilit|formul|amertume", "Application"),
    (r"goût|gout|arôme|arome|saveur|profil", "Création"),
    (r"cible|consommateur|positionnement|marché|marche", "Marketing"),
    (r"naturel|végétal|vegetal|étiquet|etiquet|réglement|reglement|allergène|allergene|sucre|sel", "Réglementation"),
]
MOTS = {
    "besoins": r"veut|souhait|besoin|cherche|gamme|projet|envisage|intéress|interess",
    "contraintes_techniques": r"texture|technique|stabilit|étiquet|etiquet|naturel|sans |végétal|vegetal|amertume",
    "contraintes_budgetaires": r"budget|coût|cout|prix|€|euro",
    "calendrier": r"lancement|date|calendrier|délai|delai|mois|semaine|20\d\d|été|ete|hiver|printemps|automne",
}


class Element(BaseModel):
    texte: str
    statut: Literal["confirme", "a_verifier"]


class CompteRenduDemande(BaseModel):
    opportunity_id: str = Field(examples=["opp-1a"])
    checklist: dict[str, bool] = Field(
        default_factory=dict, description=f"Cases cochées. Clés possibles : {list(CHECKLIST)}",
        examples=[{"objectifs_client": True, "besoin_reel": True, "contraintes_techniques": True, "calendrier": True}],
    )
    notes: str = Field(default="", examples=["Veut une gamme energie a base de the, profil naturel. Lancement prevu en juin 2027. Budget non aborde."])
    model: str | None = None


class CompteRenduReponse(BaseModel):
    opportunity_id: str
    client_id: str
    compte_rendu: dict[str, list[Element]]
    decision_opportunite: Literal["a_confirmer", "a_ecarter"]
    source: Literal["modele", "simule"]
    model: str | None


SCHEMA_CR = {
    "type": "object",
    "properties": {k: {"type": "array", "items": {"type": "object",
        "properties": {"texte": {"type": "string"}, "statut": {"type": "string", "enum": ["confirme", "a_verifier"]}},
        "required": ["texte", "statut"]}} for k in RUBRIQUES},
    "required": RUBRIQUES,
}


def manquants(checklist: dict[str, bool]) -> list[Element]:
    return [Element(texte=f"{nom} : non collecté pendant le rendez-vous.", statut="a_verifier")
            for k, nom in CHECKLIST.items() if not checklist.get(k)]


def compte_rendu_plan_b(opp: dict, body: CompteRenduDemande) -> dict[str, list[Element]]:
    phrases = [p.strip() for p in re.split(r"(?<=[.!?;])\s+|\n", body.notes) if p.strip()]
    cr: dict[str, list[Element]] = {k: [] for k in RUBRIQUES}
    cr["resume"] = [Element(texte=f"Rendez-vous sur l'opportunité « {opp['title']} ».", statut="confirme")]
    for p in phrases:
        if re.search(r"non abord|pas abord|inconnu|à confirmer|a confirmer|pas encore|pas évoqu|pas evoqu", p, re.I):
            continue  # une information non obtenue ne devient jamais un fait
        for rubrique, motif in MOTS.items():
            if re.search(motif, p, re.I):
                cr[rubrique].append(Element(texte=p, statut="confirme"))
                break
    for rubrique in ("besoins", "contraintes_techniques", "contraintes_budgetaires", "calendrier"):
        if not cr[rubrique]:
            cr[rubrique] = [Element(texte="Non renseigné dans les notes.", statut="a_verifier")]
    cr["prochaines_actions"] = [Element(texte=opp.get("next_action") or "À définir.", statut="a_verifier")]
    equipes = [e for motif, e in EQUIPES if re.search(motif, body.notes + " " + opp["title"], re.I)]
    cr["equipes_internes"] = [Element(texte=e, statut="a_verifier") for e in dict.fromkeys(equipes)] or [Element(texte="À déterminer.", statut="a_verifier")]
    return cr


@app.post("/compte-rendu", dependencies=[Cle])
def compte_rendu(body: CompteRenduDemande) -> CompteRenduReponse:
    opp = opportunite(body.opportunity_id)
    inconnues = set(body.checklist) - set(CHECKLIST)
    if inconnues:
        raise HTTPException(status_code=422, detail=f"Cases inconnues : {sorted(inconnues)}")
    modele = body.model or MODEL
    cochees = [CHECKLIST[k] for k, v in body.checklist.items() if v]
    consigne = (
        "Rédige le compte rendu de ce rendez-vous commercial. "
        f"Réponds avec un objet JSON dont les clés sont exactement {RUBRIQUES} ; chaque valeur est une liste d'objets "
        '{"texte": "...", "statut": "confirme" ou "a_verifier"}. '
        "« confirme » seulement si l'information figure dans les notes ; tout le reste est « a_verifier ».\n\n"
        f"DONNÉES : {json.dumps(contexte(opp), ensure_ascii=False)}\n"
        f"INFORMATIONS COCHÉES : {cochees}\nNOTES DU COMMERCIAL : {body.notes or '(aucune)'}"
    )
    out = demander_json(consigne, modele, SCHEMA_CR)
    cr, source = None, "simule"
    if out and all(isinstance(out.get(k), list) and out[k] for k in RUBRIQUES if k != "informations_manquantes"):
        try:
            cr = {k: [Element(**e) for e in out.get(k, [])] for k in RUBRIQUES}
            source = "modele"
        except Exception:
            cr = None
    if cr is None:
        cr, modele = compte_rendu_plan_b(opp, body), None
    # Garantie : les cases non cochées apparaissent toujours dans les informations manquantes
    deja = " ".join(e.texte.lower() for e in cr["informations_manquantes"])
    cr["informations_manquantes"] += [e for e in manquants(body.checklist) if e.texte.split(" :")[0].lower() not in deja]
    if not cr["informations_manquantes"]:
        cr["informations_manquantes"] = [Element(texte="Aucune : toutes les informations de la checklist ont été collectées.", statut="confirme")]
    return CompteRenduReponse(opportunity_id=opp["id"], client_id=opp["client_id"], compte_rendu=cr,
                              decision_opportunite="a_confirmer", source=source, model=modele)
