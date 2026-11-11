"""Tests de l'API de démo (data/api/main.py).

Lancer : pytest data/tests/test_api.py  (demande fastapi et httpx, voir data/api/requirements.txt)
"""

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="fastapi absent : pip install -r data/api/requirements.txt")
pytest.importorskip("httpx", reason="httpx absent : pip install -r data/api/requirements.txt")
from fastapi.testclient import TestClient  # noqa: E402

DATA = Path(__file__).resolve().parents[1]
ETAPES = ["Ambition", "Frein", "Ouverture"]
CLES_QUESTION_DEMO = {"id", "opportunityId", "text", "justification", "status", "step", "briefField"}

_spec = importlib.util.spec_from_file_location("api_main", DATA / "api" / "main.py")
api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api)


def lire(nom):
    with open(DATA / "demo" / nom, encoding="utf-8") as fichier:
        return json.load(fichier)


@pytest.fixture(scope="module")
def client():
    return TestClient(api.app)


def test_sante(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok", "questions_chargees": 36}


def test_clients(client):
    reponse = client.get("/clients")
    assert reponse.status_code == 200
    assert reponse.json() == lire("clients.json")


def test_un_client_avec_ses_opportunites(client):
    reponse = client.get("/clients/C-01")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["name"] == "Boissons Altitude"
    assert [o["id"] for o in corps["opportunities"]] == corps["opportunityIds"]
    assert client.get("/clients/C-08").json()["opportunities"] == []


def test_une_opportunite_avec_ses_questions(client):
    reponse = client.get("/opportunites/OPP-06")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert sorted(q["id"] for q in corps["questions"]) == sorted(corps["recommendedQuestions"])
    assert [q["step"] for q in corps["questions"]] == ETAPES
    assert all(q["opportunityId"] == "OPP-06" for q in corps["questions"])


def test_questions_de_l_opportunite_triees_par_etape(client, monkeypatch):
    # Même si recommendedQuestions est dans le désordre, la route trie Ambition, Frein, Ouverture.
    opp = dict(api.OPPORTUNITES["OPP-06"], recommendedQuestions=["Q-18", "Q-16", "Q-17"])
    monkeypatch.setitem(api.OPPORTUNITES, "OPP-06", opp)
    corps = client.get("/opportunites/OPP-06").json()
    assert [q["step"] for q in corps["questions"]] == ETAPES
    assert [q["id"] for q in corps["questions"]] == ["Q-16", "Q-17", "Q-18"]


def test_post_questions(client):
    reponse = client.post("/questions", json={
        "champs_manquants": ["brief.echeance_lancement", "brief.budget_matiere_eur_par_litre",
                             "brief.contraintes.regime"],
        "opportunite_id": "OPP-06",
    })
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["champs_manquants"] == ["echeance_lancement", "budget_matiere_eur_par_litre", "contraintes"]
    assert set(corps) == {"champs_manquants", "questions", "questions_proposees", "avertissements"}
    assert len(corps["questions"]) == 3
    demo = {q["id"]: q for q in lire("questions.json")}
    for q in corps["questions"]:
        assert set(q) == CLES_QUESTION_DEMO
        assert q == demo[q["id"]]  # mêmes valeurs que le jeu de démo
    assert corps["questions_proposees"] == ";".join(q["id"] for q in corps["questions"])
    assert corps["avertissements"] == []


def test_post_questions_identique_au_moteur(client):
    champs = ["objectif", "marche"]
    corps = client.post("/questions", json={"champs_manquants": champs, "nb": 4}).json()
    attendu = api.moteur.proposer_questions(champs, nb=4)
    assert [q["id"] for q in corps["questions"]] == [q["id"] for q in attendu]
    assert [q["briefField"] for q in corps["questions"]] == [q["champ_brief"] for q in attendu]


def test_post_questions_champ_inconnu_et_liste_vide(client):
    corps = client.post("/questions", json={"champs_manquants": ["rdv.date", "objectif"], "nb": 1}).json()
    assert [q["briefField"] for q in corps["questions"]] == ["objectif"]
    assert any("rdv.date" in a for a in corps["avertissements"])
    vide = client.post("/questions", json={"champs_manquants": []}).json()
    assert vide["questions"] == [] and vide["questions_proposees"] == ""


def test_post_questions_nb_invalide(client):
    assert client.post("/questions", json={"champs_manquants": ["objectif"], "nb": 0}).status_code == 422


def test_bonnes_pratiques(client):
    reponse = client.get("/bonnes-pratiques")
    assert reponse.status_code == 200
    assert reponse.json() == lire("best_practices.json")
    assert len(reponse.json()) == 5


@pytest.mark.parametrize("methode,url,corps,attendu", [
    ("get", "/clients/C-99", None, "C-99"),
    ("get", "/opportunites/OPP-99", None, "OPP-99"),
    ("post", "/questions", {"champs_manquants": ["objectif"], "opportunite_id": "OPP-99"}, "OPP-99"),
])
def test_404_id_inconnu(client, methode, url, corps, attendu):
    reponse = client.request(methode.upper(), url, json=corps)
    assert reponse.status_code == 404
    assert "inconnu" in reponse.json()["detail"] and attendu in reponse.json()["detail"]


def test_cors_ouvert(client):
    reponse = client.get("/sante", headers={"Origin": "http://localhost:5173"})
    assert reponse.headers.get("access-control-allow-origin") == "*"
