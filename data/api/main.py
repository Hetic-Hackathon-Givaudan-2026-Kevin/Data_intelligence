"""API de démo : clients, opportunités, bonnes pratiques et moteur V1 de questions.

Lancer depuis la racine du repo :
    uvicorn --app-dir data/api main:app --port 8001
puis ouvrir http://localhost:8001/docs

Les données viennent de data/demo/*.json et de data/questions/questions.json ;
les questions proposées viennent de data/questions/moteur.py. Rien n'est recopié ici.
Les routes /v2 (doc fonctionnelle v2) lisent data/demo_v2/*.json ; compteurs et dates y sont
calculés à partir des fichiers.
"""

import json
import sys
import unicodedata
import warnings
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DATA = Path(__file__).resolve().parents[1]
DOSSIER_DEMO = DATA / "demo"
sys.path.insert(0, str(DATA / "questions"))
import moteur  # noqa: E402  (data/questions/moteur.py)


def _lire(nom):
    with open(DOSSIER_DEMO / nom, encoding="utf-8") as fichier:
        return json.load(fichier)


# Chargées une fois au démarrage (relancer l'API après une régénération des JSON).
BANQUE = moteur.charger_banque()
CLIENTS = {c["id"]: c for c in _lire("clients.json")}
OPPORTUNITES = {o["id"]: o for o in _lire("opportunities.json")}
QUESTIONS_DEMO = {q["id"]: q for q in _lire("questions.json")}
BONNES_PRATIQUES = _lire("best_practices.json")
ORDRE_ETAPES = {"Ambition": 0, "Frein": 1, "Ouverture": 2}  # règle 3 de la doc (écran 3)


app = FastAPI(
    title="API Questions G03 (démo)",
    description=(
        "API de démonstration du hackathon HETIC × Givaudan (équipe G03).\n\n"
        "- Consulter les **clients**, **opportunités** et **bonnes pratiques** du jeu de démo "
        "(données fictives).\n"
        "- Obtenir les **questions à poser au prochain RDV** pour les champs du brief encore "
        "manquants (moteur V1 par règles, sans LLM).\n\n"
        "Aucune authentification : API de démo uniquement."
    ),
    version="1.0",
    openapi_tags=[
        {"name": "Santé", "description": "État de l'API."},
        {"name": "Clients", "description": "Clients fictifs et leurs opportunités."},
        {"name": "Opportunités", "description": "Opportunités et leurs 3 questions recommandées."},
        {"name": "Questions", "description": "Moteur V1 : questions pour les champs du brief manquants."},
        {"name": "Bonnes pratiques", "description": "Bonnes pratiques des commerciaux seniors (démo)."},
    ],
)
app.add_middleware(  # ouvert pour que l'app front puisse appeler l'API depuis une autre origine
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


def _introuvable(objet, identifiant):
    """objet : « Client inconnu » ou « Opportunité inconnue »."""
    raise HTTPException(status_code=404, detail=f"{objet} : {identifiant}")


class DemandeQuestions(BaseModel):
    champs_manquants: list[str] = Field(
        description="Champs du brief encore manquants. Le préfixe « brief. » et les sous-champs de "
                    "« contraintes » (ex. contraintes.regime) sont acceptés.",
    )
    opportunite_id: Optional[str] = Field(None, description="Opportunité à privilégier, ex. OPP-06.")
    nb: int = Field(3, ge=1, le=21, description="Nombre maximal de questions.")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "champs_manquants": ["brief.echeance_lancement", "brief.budget_matiere_eur_par_litre",
                                     "brief.contraintes.regime"],
                "opportunite_id": "OPP-06",
                "nb": 3,
            }]
        }
    }


class QuestionProposee(BaseModel):
    """Mêmes clés que data/demo/questions.json (section 9.3)."""
    id: str
    opportunityId: str
    text: str = Field(description="La question à poser.")
    justification: str = Field(description="Pourquoi poser cette question.")
    status: str = Field(description="suggested ou validated.")
    step: str = Field(description="Ambition, Frein ou Ouverture.")
    briefField: str = Field(description="Champ du brief (schéma v1.0) que la question aide à remplir.")


class ReponseQuestions(BaseModel):
    champs_manquants: list[str] = Field(description="Champs reconnus, dans l'ordre de priorité.")
    questions: list[QuestionProposee]
    questions_proposees: str = Field(
        description="Ids joints par « ; », pour la colonne questions_proposees de la grille de fiabilité.",
    )
    avertissements: list[str] = Field(description="Ex. champs inconnus ignorés.")


@app.get("/sante", tags=["Santé"], summary="État de l'API")
def sante():
    """Renvoie le statut de l'API et le nombre de questions chargées depuis la banque."""
    return {"statut": "ok", "questions_chargees": len(BANQUE)}


@app.get("/clients", tags=["Clients"], summary="Liste des clients de démo")
def lister_clients():
    """Renvoie les clients fictifs du jeu de démo (`data/demo/clients.json`)."""
    return list(CLIENTS.values())


@app.get("/clients/{client_id}", tags=["Clients"], summary="Un client et ses opportunités")
def lire_client(client_id: str):
    """Renvoie le client et le détail de ses opportunités. 404 si l'id est inconnu (ex. `C-99`)."""
    client = CLIENTS.get(client_id) or _introuvable("Client inconnu", client_id)
    return {**client, "opportunities": [OPPORTUNITES[o] for o in client["opportunityIds"]]}


@app.get("/opportunites/{opportunite_id}", tags=["Opportunités"], summary="Une opportunité et ses 3 questions")
def lire_opportunite(opportunite_id: str):
    """Renvoie l'opportunité et ses questions recommandées, triées Ambition, Frein, Ouverture
    (règle 3 de la doc, écran 3). 404 si l'id est inconnu (ex. `OPP-99`)."""
    opp = OPPORTUNITES.get(opportunite_id) or _introuvable("Opportunité inconnue", opportunite_id)
    questions = sorted((QUESTIONS_DEMO[q] for q in opp["recommendedQuestions"]),
                       key=lambda q: (ORDRE_ETAPES.get(q["step"], len(ORDRE_ETAPES)), q["id"]))
    return {**opp, "questions": questions}


@app.post("/questions", tags=["Questions"],
          summary="Mode « champs du brief encore manquants » : questions à poser au prochain RDV",
          response_model=ReponseQuestions)
def proposer_questions(demande: DemandeQuestions):
    """Mode **« champs du brief encore manquants »** : à partir des champs du brief qui manquent
    encore, propose les questions à poser au prochain RDV (moteur V1, `data/questions/moteur.py`).

    Une question par champ manquant dans l'ordre de priorité (objectif, échéance, budget,
    contraintes, marché, profil de goût, insights concurrence), puis une 2e question par champ
    s'il en manque moins que `nb`. Les questions sont renvoyées avec les clés du jeu de démo
    (section 9.3). Les champs inconnus sont ignorés et signalés dans `avertissements`.
    404 si `opportunite_id` est inconnu.
    """
    if demande.opportunite_id and demande.opportunite_id not in OPPORTUNITES:
        _introuvable("Opportunité inconnue", demande.opportunite_id)
    with warnings.catch_warnings(record=True) as alertes:
        warnings.simplefilter("always")
        champs = moteur.normaliser_champs(demande.champs_manquants)
        questions = moteur.proposer_questions(
            champs, opportunite_id=demande.opportunite_id, nb=demande.nb, banque=BANQUE,
        )
    return {
        "champs_manquants": champs,
        "questions": [QUESTIONS_DEMO[q["id"]] for q in questions],  # ordre du moteur conservé
        "questions_proposees": moteur.ids_pour_grille(questions),
        "avertissements": sorted({str(a.message) for a in alertes}),
    }


@app.get("/bonnes-pratiques", tags=["Bonnes pratiques"], summary="Les bonnes pratiques")
def lister_bonnes_pratiques():
    """Renvoie les 5 bonnes pratiques de démo (`data/demo/best_practices.json`)."""
    return BONNES_PRATIQUES


# ---------------------------------------------------------------------------------------------
# V2 (doc fonctionnelle v2) : lit data/demo_v2/. Compteurs et dates calculés à partir des fichiers.
# ---------------------------------------------------------------------------------------------

DOSSIER_V2 = DATA / "demo_v2"
sys.path.insert(0, str(DOSSIER_V2))
import generer_demo_v2 as regles_v2  # noqa: E402  (checklist, date de référence, règle de priorité)


def _lire_v2(nom):
    with open(DOSSIER_V2 / nom, encoding="utf-8") as fichier:
        return json.load(fichier)


CLIENTS_V2 = {c["id"]: c for c in _lire_v2("clients.json")}
PROJETS_V2 = _lire_v2("projects.json")
OPPORTUNITES_V2 = {o["id"]: o for o in _lire_v2("opportunities.json")}
SIGNAUX_V2 = _lire_v2("signals.json")
CONTEXTES_RDV = {c["opportunity_id"]: c for c in _lire_v2("meeting_context.json")}
RDV_V2 = _lire_v2("meetings.json") if (DOSSIER_V2 / "meetings.json").exists() else []
CHECKLIST = regles_v2.CHECKLIST
DATE_REFERENCE = date.fromisoformat(regles_v2.DATE_REFERENCE)
JOURS_SIGNAL_RECENT = 90
ECHELLE = (sum(min(n["points"] for n in c["niveaux"]) for c in regles_v2.CRITERES.values()),
           sum(max(n["points"] for n in c["niveaux"]) for c in regles_v2.CRITERES.values()))  # score mini, maxi
MOTS_REGLEMENTAIRES = ("réglement", "reglement", "allégation", "allegation", "étiquet", "etiquet", "additif")

app.openapi_tags += [
    {"name": "V2 – Portefeuille", "description": "Doc v2 : tableau de bord, portefeuille et fiche client."},
    {"name": "V2 – Opportunités", "description": "Doc v2 : détail d'une opportunité et justification."},
    {"name": "V2 – Meeting Copilot", "description": "Doc v2 : préparation du RDV et compte rendu (V1, par modèle)."},
]


def _sans_accents(texte):
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()


def _projets(client_id):
    return [p for p in PROJETS_V2 if p["client_id"] == client_id]


def _opportunites(client_id):
    return [o for o in OPPORTUNITES_V2.values() if o["client_id"] == client_id]


def _signaux(opportunity_id):
    return [s for s in SIGNAUX_V2 if s["opportunity_id"] == opportunity_id]


def _compteurs(client_id):
    opps = _opportunites(client_id)
    return {
        "active_projects": sum(p["status"] == "active" for p in _projets(client_id)),
        "detected_opportunities": len(opps),  # toutes les opportunités du client
        "to_qualify": sum(o["status"] == "to_qualify" for o in opps),
    }


def _avec_dernier_signal(opp):
    return {**opp, "last_signal_date": max(s["source_date"] for s in _signaux(opp["id"]))}


def _phrase(texte, evidence_type, source):
    return {"text": texte, "evidence_type": evidence_type, "source": source}


def _date_fr(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def _synthese(client):
    """« Ce qu'il faut savoir sur ce client » (V1, par règles). Chaque phrase porte fact,
    hypothesis ou to_confirm (section 5.5) et sa source."""
    opps = _opportunites(client["id"])
    signaux = [s for o in opps for s in _signaux(o["id"])]
    actifs = sorted((p for p in _projets(client["id"]) if p["status"] == "active"),
                    key=lambda p: p["start_date"], reverse=True)
    besoins = [s for s in signaux if s["source_type"] in regles_v2.SOURCES_CLIENT]
    recents = [s for s in signaux if s not in besoins
               and (DATE_REFERENCE - date.fromisoformat(s["source_date"])).days <= JOURS_SIGNAL_RECENT]
    attention = []
    for o in opps:
        if o["status"] == "to_qualify":
            action = o["next_action"][0].lower() + o["next_action"][1:]
            attention.append(_phrase(f"« {o['title']} » est à qualifier : {action}", "to_confirm", o["id"]))
        elif o["feasibility"] == "to_confirm":
            attention.append(_phrase(f"La faisabilité de « {o['title']} » reste à confirmer.", "to_confirm", o["id"]))
    attention += [_phrase(f"Hypothèse à vérifier : {s['description']}", "hypothesis", s["id"])
                  for s in signaux if s["evidence_type"] == "hypothesis"]
    return {
        "title": "Ce qu'il faut savoir sur ce client",
        "situation": [_phrase(client["commercial_situation"], "fact", f"clients.json#{client['id']}")],
        "important_projects": [_phrase(f"{p['name']} (en cours depuis le {_date_fr(p['start_date'])}).", "fact",
                                       p["id"]) for p in actifs],
        "expressed_needs": [_phrase(s["description"], s["evidence_type"], s["id"]) for s in besoins],
        "recent_signals": [_phrase(f"{s['description']} ({_date_fr(s['source_date'])})", s["evidence_type"], s["id"])
                           for s in sorted(recents, key=lambda s: s["source_date"], reverse=True)],
        "attention_points": attention,
    }


def _chronologie(client_id):
    evenements = [{"date": p["start_date"], "type": "project_start", "ref": p["id"],
                   "event": f"Début du projet {p['id']} : {p['name']}"} for p in _projets(client_id)]
    evenements += [{"date": s["source_date"], "type": "signal", "ref": s["id"],
                    "event": s["description"]} for o in _opportunites(client_id) for s in _signaux(o["id"])]
    return sorted(evenements, key=lambda e: (e["date"], e["ref"]), reverse=True)


@app.get("/v2/dashboard", tags=["V2 – Portefeuille"], summary="Indicateurs du tableau de bord")
def tableau_de_bord_v2():
    """Clients suivis, opportunités détectées, à qualifier et RDV à préparer, calculés à partir des
    fichiers. RDV à préparer : 0 tant qu'il n'y a pas de `meetings.json`."""
    return {
        "followed_clients": len(CLIENTS_V2),
        "detected_opportunities": len(OPPORTUNITES_V2),
        "to_qualify": sum(o["status"] == "to_qualify" for o in OPPORTUNITES_V2.values()),
        "meetings_to_prepare": sum(r.get("status") != "completed" for r in RDV_V2),
    }


@app.get("/v2/clients", tags=["V2 – Portefeuille"], summary="Portefeuille clients, avec recherche par nom")
def lister_clients_v2(q: Optional[str] = None):
    """Chaque client avec `active_projects`, `detected_opportunities` (toutes ses opportunités) et
    `to_qualify`. `q` filtre par nom, sans tenir compte des majuscules ni des accents."""
    clients = CLIENTS_V2.values()
    if q:
        clients = [c for c in clients if _sans_accents(q) in _sans_accents(c["name"])]
    return [{**c, **_compteurs(c["id"])} for c in clients]


@app.get("/v2/clients/{client_id}", tags=["V2 – Portefeuille"], summary="Fiche client")
def lire_client_v2(client_id: str):
    """Le client et ses compteurs, ses projets, ses opportunités (avec `last_signal_date`), la
    chronologie (de la plus récente à la plus ancienne) et la synthèse « Ce qu'il faut savoir ».
    404 si l'id est inconnu."""
    client = CLIENTS_V2.get(client_id) or _introuvable("Client inconnu", client_id)
    return {
        **client, **_compteurs(client_id),
        "projects": _projets(client_id),
        "opportunities": [_avec_dernier_signal(o) for o in _opportunites(client_id)],
        "timeline": _chronologie(client_id),
        "summary": _synthese(client),
    }


def _raisonnement_score(opp, signaux):
    """Explication du score, selon la grille de qualification (DATA-US09)."""
    detail = regles_v2.detail_priorite(opp, SIGNAUX_V2)
    evaluation = regles_v2.evaluer_priorite(opp, SIGNAUX_V2)
    client = CLIENTS_V2[opp["client_id"]]
    types = sorted({s["source_type"] for s in signaux})

    def pts(c):
        mini, maxi = detail[c]
        return f"{mini}" if mini == maxi else f"{mini} à {maxi} (inconnu)"

    score = (f"score {evaluation['score_min']}" if evaluation["score_min"] == evaluation["score_max"]
             else f"score {evaluation['score_min']} à {evaluation['score_max']}")
    statut = ("stable" if opp["priority_status"] == "stable"
              else f"provisoire, jusqu'à {opp['priority_max']} selon les critères inconnus")
    return (
        f"{len(signaux)} signal(s) relient {client['name']} à « {opp['title']} » ({', '.join(types)}). "
        f"Priorité {opp['priority']} ({statut}) : {score} sur une échelle de {ECHELLE[0]} à {ECHELLE[1]} (confiance du meilleur "
        f"signal {pts('confidence')}, potentiel {pts('estimated_potential')}, faisabilité {pts('feasibility')}, "
        f"complexité {pts('complexity')}, urgence {pts('urgency')})."
    )


def _justification(opp, signaux):
    """Justification commerciale stockée dans opportunities.json (DATA-US08 : besoin du client,
    pourquoi maintenant, intérêt pour Givaudan, faits, hypothèses, à confirmer, risques), plus
    l'explication du score (`reasoning`) et la provenance des signaux (section 5.2).
    `information_used` et `to_verify` sont gardés pour compatibilité avec l'app."""
    raisonnement = _raisonnement_score(opp, signaux)
    a_verifier = []
    if opp["status"] != "confirmed":
        a_verifier.append(f"Le besoin n'est pas confirmé auprès du client (statut : {opp['status']}).")
    a_verifier += [f"Hypothèse : {s['description']}" for s in signaux if s["evidence_type"] != "fact"]
    a_verifier += [f"{regles_v2.CRITERES[c]['nom']} inconnu(e) : à vérifier au prochain rendez-vous."
                   for c in opp["missing_criteria"]]
    a_verifier += [f"Information manquante : {CHECKLIST[p]}." for p in CONTEXTES_RDV[opp["id"]]["missing"]]
    return {
        **opp["justification"],
        "information_used": [f"{s['id']} : {s['description']}" for s in signaux],
        "provenance": [{"signal_id": s["id"], "source_type": s["source_type"], "source_date": s["source_date"],
                        "source": s["source_ref"] if s["is_real_source"] else "source fictive (démo)",
                        "is_real_source": s["is_real_source"]} for s in signaux],
        "reasoning": raisonnement,
        "to_verify": a_verifier,
    }


@app.get("/v2/opportunities/{opportunity_id}", tags=["V2 – Opportunités"], summary="Détail d'une opportunité")
def lire_opportunite_v2(opportunity_id: str):
    """L'opportunité (avec `last_signal_date`), son client, ses signaux complets et la justification
    par règles (section 5.2). 404 si l'id est inconnu."""
    opp = OPPORTUNITES_V2.get(opportunity_id) or _introuvable("Opportunité inconnue", opportunity_id)
    signaux = sorted(_signaux(opportunity_id), key=lambda s: s["source_date"], reverse=True)
    return {**_avec_dernier_signal(opp), "client": CLIENTS_V2[opp["client_id"]], "signals": signaux,
            "justification": _justification(opp, signaux)}


@app.get("/v2/opportunities/{opportunity_id}/meeting", tags=["V2 – Meeting Copilot"],
         summary="Contexte du Meeting Copilot")
def contexte_rdv_v2(opportunity_id: str):
    """Client, opportunité, objectif du RDV, informations connues et manquantes parmi les 6 points
    de la checklist, et 3 questions suggérées. 404 si l'id est inconnu."""
    opp = OPPORTUNITES_V2.get(opportunity_id) or _introuvable("Opportunité inconnue", opportunity_id)
    contexte = CONTEXTES_RDV[opportunity_id]
    connus = {k["point"] for k in contexte["known"]}
    return {
        "client": {"id": opp["client_id"], "name": CLIENTS_V2[opp["client_id"]]["name"]},
        "opportunity": {"id": opp["id"], "title": opp["title"], "status": opp["status"]},
        "objective": contexte["objective"],
        "known": [{**k, "label": CHECKLIST[k["point"]]} for k in contexte["known"]],
        "missing": [{"point": p, "label": CHECKLIST[p]} for p in contexte["missing"]],
        "questions": [{**q, "information_sought_label": CHECKLIST[q["information_sought"]]}
                      for q in contexte["questions"]],
        "checklist": [{"point": p, "label": l, "known": p in connus} for p, l in CHECKLIST.items()],
    }


class Reponse(BaseModel):
    """Objet de Meeting.answers (MODELE_DONNEES.md)."""
    information_sought: str = Field(description=f"Point de la checklist : {', '.join(CHECKLIST)}.")
    answer: str = Field(description="Réponse obtenue.")


class DemandeCompteRendu(BaseModel):
    opportunity_id: str = Field(description="Opportunité du rendez-vous, ex. O-01.")
    collected_points: list[str] = Field(default=[], description=f"Points cochés parmi : {', '.join(CHECKLIST)}.")
    answers: list[Reponse] = Field(default=[], description="Réponses, chacune reliée à un point de la checklist.")
    notes: str = Field("", description="Notes libres du rendez-vous.")
    date: Optional[str] = Field(None, description="Date du rendez-vous (AAAA-MM-JJ) ; par défaut, la date du jeu.")

    model_config = {"json_schema_extra": {"examples": [{
        "opportunity_id": "O-01",
        "collected_points": ["client_objectives", "technical_constraints"],
        "answers": [{"information_sought": "client_objectives",
                     "answer": "Lancer une gamme de boissons fonctionnelles l'an prochain."}],
        "notes": "Goût et coût sont les freins cités.",
    }]}}


# Équipes internes (section 2.4), codes du modèle de données ; libellés français pour le texte.
LIBELLES_EQUIPES = {"application": "Application", "creation": "Création", "marketing": "Marketing",
                    "regulatory": "Réglementation"}
CATEGORIES_CREATION = {"Nouvelle gamme", "Extension de gamme", "Nouvelle formulation", "Nouvelle référence"}
SOURCES_MARCHE = {"market_trend", "company_report"}
POINTS_BESOIN = ["client_objectives", "real_need"]
POINTS_CONTRAINTE = ["technical_constraints", "budget_constraints", "timeline"]


def _equipes(opp, collectes, texte):
    """application : contraintes techniques recueillies ; creation : nouvel arôme à créer (catégorie)
    et objectifs ou besoin recueillis ; marketing : objectifs recueillis et signal de marché ;
    regulatory : mot-clé réglementaire dans les notes ou réponses, ou signal réglementaire."""
    types = {s["source_type"] for s in _signaux(opp["id"])}
    equipes = []
    if "technical_constraints" in collectes:
        equipes.append("application")
    if opp["category"] in CATEGORIES_CREATION and collectes & set(POINTS_BESOIN):
        equipes.append("creation")
    if "client_objectives" in collectes and types & SOURCES_MARCHE:
        equipes.append("marketing")
    if any(m in texte.lower() for m in MOTS_REGLEMENTAIRES) or "regulation" in types:
        equipes.append("regulatory")
    return equipes


@app.post("/v2/meetings/report", tags=["V2 – Meeting Copilot"], summary="Générer le compte rendu (V1)")
def compte_rendu_v2(demande: DemandeCompteRendu):
    """Renvoie un **Meeting** complet (voir `data/demo_v2/MODELE_DONNEES.md`), non enregistré, dont
    `summary` est le **MeetingReport** produit par un modèle de texte (`generated_by: rules_v1`,
    `validated: false`). Les prochaines actions sont seulement dans `next_actions`.

    - `collected_points` = points cochés + points qui ont une réponse dans `answers`.
    - Points non recueillis → `missing_information` (ceux connus avant le RDV : « à reconfirmer »).
    - `opportunity_decision` : `confirmed` si objectifs et besoin réel sont recueillis, sinon
      `to_qualify` ; jamais `discarded` automatiquement (c'est au commercial d'écarter).
    - `internal_teams` : application, creation, marketing, regulatory (règles dans `_equipes`).

    404 si l'opportunité est inconnue, 422 si un point de checklist ou la date est invalide.
    """
    opp = OPPORTUNITES_V2.get(demande.opportunity_id) or _introuvable("Opportunité inconnue", demande.opportunity_id)
    inconnus = [p for p in demande.collected_points + [r.information_sought for r in demande.answers]
                if p not in CHECKLIST]
    if inconnus:
        raise HTTPException(status_code=422, detail=f"Points de checklist inconnus : {', '.join(inconnus)}")
    try:
        jour = date.fromisoformat(demande.date) if demande.date else DATE_REFERENCE
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Date invalide (AAAA-MM-JJ attendu) : {demande.date}")

    contexte, client = CONTEXTES_RDV[opp["id"]], CLIENTS_V2[opp["client_id"]]
    reponses = {r.information_sought: r.answer.strip() for r in demande.answers}
    collectes = set(demande.collected_points) | set(reponses)
    ordonnes = [p for p in CHECKLIST if p in collectes]
    manquants = [p for p in CHECKLIST if p not in collectes]
    connus = {k["point"]: k["information"] for k in contexte["known"]}
    notes = demande.notes.strip()

    def recueilli(points):
        return [f"{CHECKLIST[p]} : {reponses[p]}" if reponses.get(p)
                else f"{CHECKLIST[p]} : information recueillie pendant le rendez-vous (voir notes)."
                for p in points if p in collectes]

    besoins = recueilli(POINTS_BESOIN)
    besoins += [s["description"] for s in _signaux(opp["id"]) if s["source_type"] in regles_v2.SOURCES_CLIENT]
    contraintes = recueilli(POINTS_CONTRAINTE)
    contraintes += [f"{CHECKLIST[p]} (connu avant le rendez-vous) : {i}" for p, i in connus.items()
                    if p in POINTS_CONTRAINTE and p not in collectes]

    besoin_manquant = [CHECKLIST[p].lower() for p in POINTS_BESOIN if p not in collectes]
    if not besoin_manquant:
        decision, raison = "confirmed", ("Objectifs du client et besoin réel recueillis : statut proposé "
                                         "« confirmed », à valider par le commercial.")
    elif not collectes:
        decision, raison = "to_qualify", "Aucune information de la checklist n'a été recueillie."
    else:
        decision, raison = "to_qualify", (f"Il manque encore : {', '.join(besoin_manquant)}. À écarter seulement "
                                          "si le client confirme ne pas avoir ce besoin.")

    equipes = _equipes(opp, collectes, " ".join([notes, *reponses.values()]))
    actions = [f"Obtenir l'information manquante : {CHECKLIST[p].lower()}." for p in manquants]
    actions += [f"Transmettre les éléments recueillis à l'équipe {LIBELLES_EQUIPES[e]}." for e in equipes]
    if "budget_constraints" in collectes:
        actions.append("Intégrer la contrainte budgétaire à la proposition commerciale.")

    return {
        "id": f"M-{len(RDV_V2) + 1:02d}",
        "client_id": client["id"],
        "opportunity_id": opp["id"],
        "date": jour.isoformat(),
        "status": "completed",
        "objective": contexte["objective"],
        "questions": [{k: q[k] for k in ("question", "why", "information_sought")} for q in contexte["questions"]],
        "answers": [{"information_sought": p, "answer": reponses[p]} for p in CHECKLIST if p in reponses],
        "collected_points": ordonnes,
        "notes": notes,
        "summary": {
            "summary": (f"Rendez-vous avec {client['name']} au sujet de « {opp['title']} ». "
                        f"Objectif : {contexte['objective']} "
                        + (f"Notes du commercial : {notes}" if notes else "Aucune note saisie.")),
            "identified_needs": besoins,
            "communicated_constraints": contraintes,
            "missing_information": [CHECKLIST[p] + (" (connu avant le rendez-vous, à reconfirmer)"
                                                    if p in connus else "") for p in manquants],
            "opportunity_decision": decision,
            "decision_reason": raison,
            "internal_teams": equipes,
            "generated_by": "rules_v1",
            "validated": False,
        },
        "next_actions": actions,
    }
