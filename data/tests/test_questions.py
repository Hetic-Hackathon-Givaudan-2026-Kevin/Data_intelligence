"""Contrôles de la banque de questions (data/questions/questions.json).

Lancer : pytest data/tests/test_questions.py
"""

import importlib.util
import json
from collections import OrderedDict
from pathlib import Path

import pytest

DOSSIER_QUESTIONS = Path(__file__).resolve().parents[1] / "questions"
FICHIER = DOSSIER_QUESTIONS / "questions.json"
SCRIPT = DOSSIER_QUESTIONS / "convertir.py"

# Champs du schéma data/schema/schema_brief_v1.json (v1.0), présent sur la
# branche data/schema-extraction-v1 : liste recopiée en dur tant que le schéma
# n'est pas sur cette branche. À mettre à jour si le schéma change.
CHAMPS_BRIEF = {
    "objectif",
    "marche",
    "profil_gout",
    "echeance_lancement",
    "budget_matiere_eur_par_litre",
    "contraintes",
    "insights_concurrence",
}
ETAPES = ["Ambition", "Frein", "Ouverture"]
STATUTS = {"Suggérée", "Validée", "À modifier"}
DEBUTS_FERMES = ("avez-vous", "est-ce que")  # questions fermées interdites


@pytest.fixture(scope="module")
def questions():
    with open(FICHIER, encoding="utf-8") as fichier:
        return json.load(fichier)["questions"]


def test_36_questions(questions):
    assert len(questions) == 36


def test_ids_uniques(questions):
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "ids en double"


def test_12_opportunites_de_3_questions_dans_l_ordre(questions):
    par_opportunite = OrderedDict()
    for q in questions:
        par_opportunite.setdefault(q["opportunite_id"], []).append(q["etape"])
    assert len(par_opportunite) == 12
    for opp, etapes in par_opportunite.items():
        assert etapes == ETAPES, f"{opp} : {etapes}"


def test_champ_brief_connu(questions):
    inconnus = {q["id"]: q["champ_brief"] for q in questions if q["champ_brief"] not in CHAMPS_BRIEF}
    assert not inconnus, f"champ_brief hors schéma v1.0 : {inconnus}"


def test_questions_ouvertes(questions):
    for q in questions:
        texte = (q["question"] or "").strip()
        assert texte.endswith("?"), f"{q['id']} ne finit pas par « ? »"
        assert not texte.lower().startswith(DEBUTS_FERMES), f"{q['id']} est une question fermée"


def test_pourquoi_non_vide(questions):
    vides = [q["id"] for q in questions if not (q["pourquoi"] or "").strip()]
    assert not vides, f"pourquoi vide : {vides}"


def test_statut_connu(questions):
    inconnus = {q["id"]: q["statut"] for q in questions if q["statut"] not in STATUTS}
    assert not inconnus, f"statut inconnu : {inconnus}"


def test_json_a_jour_avec_le_csv():
    """questions.json doit être exactement ce que convertir.py produit depuis le CSV."""
    spec = importlib.util.spec_from_file_location("convertir", SCRIPT)
    convertir = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(convertir)
    attendu = convertir.generer_json()
    with open(FICHIER, encoding="utf-8", newline="") as fichier:
        actuel = fichier.read()
    assert actuel == attendu, (
        "questions.json n'est pas à jour : lancer python data/questions/convertir.py"
    )
