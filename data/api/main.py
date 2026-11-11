"""API de démo : clients, opportunités, bonnes pratiques et moteur V1 de questions.

Lancer depuis la racine du repo :
    uvicorn --app-dir data/api main:app --port 8001
puis ouvrir http://localhost:8001/docs

Les données viennent de data/demo/*.json et de data/questions/questions.json ;
les questions proposées viennent de data/questions/moteur.py. Rien n'est recopié ici.
"""

import json
import sys
import warnings
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
