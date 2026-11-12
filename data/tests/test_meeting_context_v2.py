"""Contrôles de data/demo_v2/meeting_context.json (contexte du Meeting Copilot, doc v2 section 4.4).

Lancer : pytest data/tests/test_meeting_context_v2.py
"""

import importlib.util
import json
import re
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1]
DOSSIER = DATA / "demo_v2"
POINTS = ["client_objectives", "real_need", "technical_constraints", "budget_constraints", "timeline",
          "decision_criteria"]
REPRISES = {"O-01": ["Q-01", "Q-02", "Q-03"], "O-03": ["Q-13", "Q-14", "Q-15"]}
# Question fermée : commence par une inversion verbe-sujet ou « Est-ce que ».
FERMEE = re.compile(r"^(Est-ce que|Avez|Êtes|Etes|Pouvez|Souhaitez|Voulez|Allez|Faites|Comptez|Envisagez)"
                    r"[- ]vous\b|^Est-ce que", re.IGNORECASE)


def charger(chemin):
    return json.loads(chemin.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contextes():
    return charger(DOSSIER / "meeting_context.json")


def test_une_entree_par_opportunite(contextes):
    opps = [o["id"] for o in charger(DOSSIER / "opportunities.json")]
    assert [c["opportunity_id"] for c in contextes] == opps


def test_connus_et_manquants_partagent_la_checklist(contextes):
    signaux = {s["id"] for s in charger(DOSSIER / "signals.json")}
    for c in contextes:
        connus = [k["point"] for k in c["known"]]
        assert sorted(connus + c["missing"], key=POINTS.index) == POINTS, c["opportunity_id"]
        assert all(k["information"].strip() and k["signal_id"] in signaux for k in c["known"])
        assert c["objective"].strip()


def test_18_questions_ouvertes_sur_un_point_manquant(contextes):
    questions = [(c, q) for c in contextes for q in c["questions"]]
    assert len(questions) == 18
    assert len({q["id"] for _, q in questions}) == 18
    for c, q in questions:
        assert len(c["questions"]) == 3
        assert q["information_sought"] in c["missing"], q["id"]
        assert q["question"].endswith("?") and q["why"].strip()
        assert not FERMEE.search(q["question"]), q["question"]


def test_une_seule_idee_par_question(contextes):
    for c in contextes:
        for q in c["questions"]:
            assert ", et" not in q["question"], q["id"]
            assert q["question"].count("?") == 1, q["id"]


def test_projet_en_contexte_pas_en_contrainte(contextes):
    """O-02 : P-01 est un projet en cours (contexte), pas une information de la checklist."""
    o02 = next(c for c in contextes if c["opportunity_id"] == "O-02")
    assert o02["known"] == [] and len(o02["missing"]) == 6
    assert "P-01" in o02["objective"]
    assert not any("20/10" in q["question"] for q in o02["questions"])


def test_questions_reprises_de_la_banque(contextes):
    banque = {q["id"]: q for q in charger(DATA / "questions" / "questions.json")["questions"]}
    par_opp = {c["opportunity_id"]: c["questions"] for c in contextes}
    for opp, ids in REPRISES.items():
        assert [q["id"] for q in par_opp[opp]] == ids
        for q in par_opp[opp]:
            assert q["question"] == banque[q["id"]]["question"] and q["why"] == banque[q["id"]]["pourquoi"]
    for opp, qs in par_opp.items():
        if opp not in REPRISES:
            assert all(q["origin"] == "rédigée pour la démo" for q in qs)


def test_fichier_a_jour_avec_le_generateur():
    spec = importlib.util.spec_from_file_location("generer_demo_v2", DOSSIER / "generer_demo_v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    texte = (DOSSIER / "meeting_context.json").read_text(encoding="utf-8")
    assert texte == module.generer_fichiers()["meeting_context.json"]
