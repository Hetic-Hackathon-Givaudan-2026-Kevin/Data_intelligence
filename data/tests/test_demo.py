"""Contrôles du jeu de données de démo (data/demo/).

Lancer : pytest data/tests/test_demo.py
"""

import importlib.util
import json
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1]
DOSSIER_DEMO = DATA / "demo"
BANQUE = DATA / "questions" / "questions.json"

FICHIERS = ["clients.json", "opportunities.json", "questions.json",
            "best_practices.json", "users.json", "meetings.json"]
PRIORITES = {"high", "medium", "watch"}
OPPORTUNITES_AVEC_SIGNAL_REEL = {"OPP-01", "OPP-02", "OPP-03", "OPP-05", "OPP-06", "OPP-09", "OPP-10"}
STATUTS_CLIENT = {"strategic", "active", "to_develop"}
STATUTS_QUESTION = {"suggested", "validated"}

# Vraies marques interdites dans data/demo/ (comparaison sans accents ni majuscules).
MARQUES_INTERDITES = ["PepsiCo", "Danone", "Nestlé", "L'Oréal", "Loreal", "Unilever", "Coca-Cola",
                      "Coca Cola", "Mondelez", "Lactalis", "Ferrero", "Kraft Heinz", "Red Bull", "Heineken"]


def sans_accents(texte):
    return unicodedata.normalize("NFKD", texte.lower()).encode("ascii", "ignore").decode("ascii")


@pytest.fixture(scope="module")
def demo():
    donnees = {}
    for nom in FICHIERS:
        with open(DOSSIER_DEMO / nom, encoding="utf-8") as fichier:
            donnees[nom.removesuffix(".json")] = json.load(fichier)
    return donnees


@pytest.fixture(scope="module")
def banque():
    with open(BANQUE, encoding="utf-8") as fichier:
        return {q["id"]: q for q in json.load(fichier)["questions"]}


def test_comptes(demo):
    assert len(demo["clients"]) == 8
    assert len(demo["opportunities"]) == 12
    assert len(demo["questions"]) == 36
    assert len(demo["best_practices"]) == 5
    assert all(bp["status"] == "validated" for bp in demo["best_practices"])
    assert Counter(u["role"] for u in demo["users"]) == {"junior": 1, "senior": 1}


def test_ids_uniques(demo):
    for nom, objets in demo.items():
        ids = [o["id"] for o in objets]
        assert len(ids) == len(set(ids)), f"ids en double dans {nom}"


def test_valeurs_autorisees(demo):
    assert {c["status"] for c in demo["clients"]} <= STATUTS_CLIENT
    assert {o["priority"] for o in demo["opportunities"]} <= PRIORITES
    assert {q["status"] for q in demo["questions"]} <= STATUTS_QUESTION
    assert all(300_000 <= o["estimatedRevenue"] <= 1_800_000 for o in demo["opportunities"])


def test_coherence_clients_opportunites(demo):
    clients = {c["id"]: c for c in demo["clients"]}
    opportunites = {o["id"]: o for o in demo["opportunities"]}
    listees = [opp for c in demo["clients"] for opp in c["opportunityIds"]]
    assert sorted(listees) == sorted(opportunites), "chaque opportunité doit appartenir à un seul client"
    for opp in opportunites.values():
        assert opp["clientId"] in clients
        assert opp["id"] in clients[opp["clientId"]]["opportunityIds"]
    for client in demo["clients"]:
        assert len(client["opportunityIds"]) == sum(o["clientId"] == client["id"] for o in opportunites.values())
    assert any(not c["opportunityIds"] for c in demo["clients"]), "un client sans opportunité (pastille « Aucune »)"


def test_trois_questions_par_opportunite(demo):
    questions = {q["id"]: q for q in demo["questions"]}
    for opp in demo["opportunities"]:
        assert len(opp["recommendedQuestions"]) == 3, opp["id"]
        for qid in opp["recommendedQuestions"]:
            assert qid in questions, f"{opp['id']} : {qid} inexistante"
            assert questions[qid]["opportunityId"] == opp["id"]


def test_priorite_selon_les_triggers_qui_comptent(demo):
    attendu = {0: "watch", 1: "watch", 2: "medium"}
    for opp in demo["opportunities"]:
        assert 1 <= len(opp["triggers"]) <= 3, opp["id"]
        comptes = sum(t["counted"] for t in opp["triggers"])
        assert opp["priority"] == attendu.get(comptes, "high"), opp["id"]


def test_format_des_triggers(demo):
    for opp in demo["opportunities"]:
        for t in opp["triggers"]:
            assert set(t) == {"text", "type", "counted", "source"}, opp["id"]
            assert t["type"] in {"real", "fictional"} and isinstance(t["counted"], bool)
            assert t["text"].strip()


def test_chaque_trigger_real_a_une_source(demo):
    reels = [t for o in demo["opportunities"] for t in o["triggers"] if t["type"] == "real"]
    assert reels, "aucun trigger real"
    for t in reels:
        assert t["source"] and "Open Food Facts" in t["source"] and "ODbL" in t["source"], t["text"]
    fictifs = [t for o in demo["opportunities"] for t in o["triggers"] if t["type"] == "fictional"]
    assert all(t["source"] is None and t["counted"] for t in fictifs)


def test_triggers_real_identiques_aux_signaux(demo):
    with open(DATA / "signaux" / "signaux_marche.json", encoding="utf-8") as fichier:
        signaux = {s["opportunite_id"]: s["signal"] for s in json.load(fichier)["signaux"]}
    reels_par_opp = {o["id"]: [t for t in o["triggers"] if t["type"] == "real"] for o in demo["opportunities"]}
    # Les 7 anciens triggers « croissance du marché » sont remplacés ; 04, 07 et 08 restent hors démo.
    assert {o for o, r in reels_par_opp.items() if r} == OPPORTUNITES_AVEC_SIGNAL_REEL
    for opp, reels in reels_par_opp.items():
        for t in reels:
            assert len(reels) == 1
            assert t["text"] == signaux[opp]["trigger"]
            assert t["counted"] == signaux[opp]["compte"]


def test_plus_aucune_croissance_inventee(demo):
    textes = [t["text"] for o in demo["opportunities"] for t in o["triggers"] if t["type"] == "fictional"]
    assert not [t for t in textes if t.lower().startswith("croissance")]


def test_textes_identiques_a_la_banque(demo, banque):
    assert {q["id"] for q in demo["questions"]} == set(banque)
    for q in demo["questions"]:
        source = banque[q["id"]]
        assert q["text"] == source["question"]
        assert q["justification"] == source["pourquoi"]
        assert q["step"] == source["etape"]
        assert q["briefField"] == source["champ_brief"]
        assert q["opportunityId"] == source["opportunite_id"]
    for bp in demo["best_practices"]:
        assert bp["content"].startswith(banque[bp["questionId"]]["question"] + " ")


def test_validated_exactement_celles_des_bonnes_pratiques(demo):
    validees = {q["id"] for q in demo["questions"] if q["status"] == "validated"}
    assert validees == {bp["questionId"] for bp in demo["best_practices"]}


def test_references_des_rdv(demo):
    clients = {c["id"]: c for c in demo["clients"]}
    questions = {q["id"]: q for q in demo["questions"]}
    assert {m["status"] for m in demo["meetings"]} == {"completed", "planned"}
    dates = {m["status"]: date.fromisoformat(m["date"]) for m in demo["meetings"]}  # AAAA-MM-JJ valide
    assert dates["completed"] < dates["planned"]
    for m in demo["meetings"]:
        assert m["opportunityId"] in clients[m["clientId"]]["opportunityIds"]
        assert all(questions[qid]["opportunityId"] == m["opportunityId"] for qid in m["questionsAsked"])


def test_aucune_vraie_marque():
    for fichier in sorted(DOSSIER_DEMO.iterdir()):
        if fichier.is_file():
            texte = sans_accents(fichier.read_text(encoding="utf-8"))
            for marque in MARQUES_INTERDITES:
                assert sans_accents(marque) not in texte, f"{marque} trouvé dans {fichier.name}"


def test_fichiers_a_jour_avec_le_generateur():
    spec = importlib.util.spec_from_file_location("generer_demo", DOSSIER_DEMO / "generer_demo.py")
    generateur = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generateur)
    for nom, attendu in generateur.generer_fichiers().items():
        with open(DOSSIER_DEMO / nom, encoding="utf-8", newline="") as fichier:
            assert fichier.read() == attendu, f"{nom} n'est pas à jour : lancer python data/demo/generer_demo.py"
