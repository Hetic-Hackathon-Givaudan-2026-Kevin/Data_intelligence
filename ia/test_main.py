"""Tests de l'API. Lancer : python -m pytest -q (Ollama non nécessaire)."""

import os

os.environ.setdefault("API_KEY", "test")

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
H = {"X-API-Key": "test"}


@pytest.fixture
def sans_ollama(monkeypatch):
    monkeypatch.setattr(main, "demander_json", lambda consigne, modele, schema=None: None)


def test_cle_obligatoire():
    assert client.post("/questions", json={"opportunity_id": "opp-1a"}).status_code == 401


def test_opportunite_inconnue():
    assert client.post("/questions", json={"opportunity_id": "x"}, headers=H).status_code == 404


def test_toutes_les_opportunites_ont_3_questions_et_une_justification(sans_ollama):
    for oid in main.OPPORTUNITES:
        r = client.post("/questions", json={"opportunity_id": oid}, headers=H).json()
        assert len(r["questions"]) == 3 and r["source"] == "simule", oid
        assert all(q["objectif"] and q["information_recherchee"] in main.INFOS for q in r["questions"]), oid
        j = client.get(f"/justification/{oid}", headers=H).json()
        assert j["pourquoi"] and (j["faits"] or j["hypotheses"]), oid


def test_questions_du_modele(monkeypatch):
    qs = [{"question": f"Q{i} ?", "objectif": "O", "information_recherchee": "Calendrier"} for i in range(3)]
    monkeypatch.setattr(main, "demander_json", lambda c, m, schema=None: {"questions": qs})
    assert client.post("/questions", json={"opportunity_id": "opp-1a"}, headers=H).json()["source"] == "modele"


def test_questions_du_modele_invalides_plan_b(monkeypatch):
    monkeypatch.setattr(main, "demander_json", lambda c, m, schema=None: {"questions": [{"question": "Q ?", "objectif": "O", "information_recherchee": "Météo"}]})
    assert client.post("/questions", json={"opportunity_id": "opp-1a"}, headers=H).json()["source"] == "simule"


def test_justification_hypothese_jamais_presentee_comme_fait():
    j = client.get("/justification/opp-3a", headers=H).json()  # uniquement une hypothèse
    assert not j["faits"] and j["hypotheses"] and "hypothèses" in j["pourquoi"]


NOTES = "Veut une gamme energie a base de the, profil naturel. Etiquette sans aromes artificiels. Lancement prevu en juin 2027. Budget non aborde."
CHECK = {"objectifs_client": True, "besoin_reel": True, "contraintes_techniques": True, "calendrier": True}


def test_compte_rendu_plan_b(sans_ollama):
    r = client.post("/compte-rendu", json={"opportunity_id": "opp-1a", "checklist": CHECK, "notes": NOTES}, headers=H).json()
    cr = r["compte_rendu"]
    assert r["source"] == "simule" and set(cr) == set(main.RUBRIQUES)
    assert any("2027" in e["texte"] and e["statut"] == "confirme" for e in cr["calendrier"])
    assert not any(e["statut"] == "confirme" for e in cr["contraintes_budgetaires"])
    manquant = " ".join(e["texte"] for e in cr["informations_manquantes"])
    assert "Contraintes budgétaires" in manquant and "Critères de décision" in manquant


def test_compte_rendu_modele_garde_les_manquants(monkeypatch):
    e = [{"texte": "x", "statut": "confirme"}]
    monkeypatch.setattr(main, "demander_json", lambda c, m, schema=None: {k: ([] if k == "informations_manquantes" else e) for k in main.RUBRIQUES})
    r = client.post("/compte-rendu", json={"opportunity_id": "opp-1a", "checklist": CHECK, "notes": NOTES}, headers=H).json()
    assert r["source"] == "modele" and "Critères de décision" in " ".join(x["texte"] for x in r["compte_rendu"]["informations_manquantes"])


def test_case_inconnue_refusee():
    assert client.post("/compte-rendu", json={"opportunity_id": "opp-1a", "checklist": {"humeur": True}}, headers=H).status_code == 422


def test_answer_sans_ollama(monkeypatch):
    monkeypatch.setattr(main, "OLLAMA_URL", "http://127.0.0.1:9")
    assert client.post("/answer", json={"question": "Bonjour"}, headers=H).status_code == 503


def test_reponse_mal_rangee_du_petit_modele(monkeypatch):
    # Forme réellement renvoyée par llama3.2:1b le 12/11
    brut = {"questions": [{"question": "Quel est le marché principal ?", "objectif": "identifier le marché", "information_recherchee": "['Objectifs du client', 'Marché']"}],
            "answers": {"question": "Quel calendrier de lancement est prévu ?", "objectif": "determinez le calendrier", "information_recherchee": "['Calendrier', 'Lancement']"},
            "question": "Quel est le budget alloué ?", "objectif": "determinez le budget", "information_recherchee": "['Contraintes budgétaires', 'Budget']"}
    monkeypatch.setattr(main, "demander_json", lambda c, m, schema=None: brut)
    r = client.post("/questions", json={"opportunity_id": "opp-1a"}, headers=H).json()
    assert r["source"] == "modele"
    assert {q["information_recherchee"] for q in r["questions"]} == {"Objectifs du client", "Calendrier", "Contraintes budgétaires"}
    assert all(q["objectif"][0].isupper() for q in r["questions"])


def test_schema_envoye_a_ollama(monkeypatch):
    vu = {}
    monkeypatch.setattr(main, "demander_json", lambda c, m, schema=None: vu.setdefault("schema", schema))
    client.post("/questions", json={"opportunity_id": "opp-1a"}, headers=H)
    assert vu["schema"]["properties"]["questions"]["minItems"] == 3
