"""Tests des routes /v2 de l'API de démo (data/api/main.py, doc fonctionnelle v2).

Lancer : pytest data/tests/test_api_v2.py  (demande fastapi et httpx, voir data/api/requirements.txt)
"""

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="fastapi absent : pip install -r data/api/requirements.txt")
pytest.importorskip("httpx", reason="httpx absent : pip install -r data/api/requirements.txt")
from fastapi.testclient import TestClient  # noqa: E402

DATA = Path(__file__).resolve().parents[1]
EVIDENCE = {"fact", "hypothesis", "to_confirm"}
OPPORTUNITES = ["O-01", "O-02", "O-03", "O-04", "O-05", "O-06"]

_spec = importlib.util.spec_from_file_location("api_main_v2", DATA / "api" / "main.py")
api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api)


def lire(nom):
    return json.loads((DATA / "demo_v2" / nom).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def client():
    return TestClient(api.app)


def test_dashboard(client):
    assert client.get("/v2/dashboard").json() == {
        "followed_clients": 3, "detected_opportunities": 6, "to_qualify": 2, "meetings_to_prepare": 0,
    }


def test_clients_avec_compteurs_calcules(client):
    corps = client.get("/v2/clients").json()
    compteurs = {c["id"]: (c["active_projects"], c["detected_opportunities"], c["to_qualify"]) for c in corps}
    assert compteurs == {"C-01": (3, 2, 1), "C-02": (2, 3, 1), "C-03": (1, 1, 0)}
    assert {c["id"]: c["name"] for c in corps} == {c["id"]: c["name"] for c in lire("clients.json")}


@pytest.mark.parametrize("q, attendus", [("nova", ["C-01"]), ("NORDIC", ["C-02"]), ("alimenta", ["C-03"]),
                                         ("zzz", []), ("i", ["C-01", "C-02", "C-03"])])
def test_recherche_par_nom(client, q, attendus):
    assert [c["id"] for c in client.get("/v2/clients", params={"q": q}).json()] == attendus


def test_fiche_client(client):
    corps = client.get("/v2/clients/C-01").json()
    assert corps["name"] == "Maison Nova Drinks"
    assert [p["id"] for p in corps["projects"]] == ["P-01", "P-02", "P-03"]
    signaux = lire("signals.json")
    for o in corps["opportunities"]:
        assert o["last_signal_date"] == max(s["source_date"] for s in signaux if s["opportunity_id"] == o["id"])
    dates = [e["date"] for e in corps["timeline"]]
    assert dates == sorted(dates, reverse=True)
    assert {"2026-11-05", "2026-10-20", "2026-10-10"} <= set(dates)  # chronologie de la doc
    synthese = corps["summary"]
    assert synthese["title"] == "Ce qu'il faut savoir sur ce client"
    rubriques = ["situation", "important_projects", "expressed_needs", "recent_signals", "attention_points"]
    assert all(synthese[r] for r in rubriques)
    assert all(p["evidence_type"] in EVIDENCE and p["text"].strip() for r in rubriques for p in synthese[r])


def test_opportunite_signaux_et_justification(client):
    corps = client.get("/v2/opportunities/O-03").json()
    assert corps["client"]["id"] == "C-02"
    assert sorted(s["id"] for s in corps["signals"]) == ["S-04", "S-05"]
    assert corps["signals"] == sorted([s for s in lire("signals.json") if s["opportunity_id"] == "O-03"],
                                      key=lambda s: s["source_date"], reverse=True)
    j = corps["justification"]
    assert set(j) == {"information_used", "provenance", "reasoning", "to_verify",  # score et provenance
                      "client_need", "why_now", "value_for_givaudan", "internal_teams", "facts", "hypotheses",
                      "to_confirm", "risks"}  # justification commerciale (DATA-US08)
    stockee = next(o for o in lire("opportunities.json") if o["id"] == "O-03")["justification"]
    assert {k: j[k] for k in stockee} == stockee
    assert "score 5 sur une échelle de -1 à 7" in j["reasoning"] and "Priorité high (stable)" in j["reasoning"]
    assert any(t.startswith("Hypothèse") for t in j["to_verify"])  # S-05 est une hypothèse
    assert all(p["source"] for p in j["provenance"])


def test_contexte_rdv(client):
    corps = client.get("/v2/opportunities/O-01/meeting").json()
    assert corps["client"]["name"] == "Maison Nova Drinks"
    assert [q["id"] for q in corps["questions"]] == ["Q-01", "Q-02", "Q-03"]
    manquants = {m["point"] for m in corps["missing"]}
    assert all(q["information_sought"] in manquants for q in corps["questions"])
    assert len(corps["checklist"]) == 6


def champs_du_modele():
    spec = importlib.util.spec_from_file_location("test_modele_donnees", DATA / "tests" / "test_modele_donnees.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lire_modele()


def equipes(rapport):
    return [e["team"] for e in rapport["internal_teams"]]


def test_compte_rendu_suit_le_modele_de_donnees(client):
    """Réponse = Meeting, summary = MeetingReport (DATA-US11) ; Meeting.next_actions = textes de summary.next_actions."""
    modele = champs_du_modele()
    corps = client.post("/v2/meetings/report", json={"opportunity_id": "O-01"}).json()
    assert set(corps) == set(modele["Meeting"])
    assert set(corps["summary"]) == set(modele["MeetingReport"])
    assert corps["id"] == "M-03" and corps["status"] == "completed" and corps["client_id"] == "C-01"  # M-01, M-02 : meetings.json
    r = corps["summary"]
    assert r["generated_by"] == "rules_v1" and r["validated"] is False
    assert r["engine"] == {"requested": "rules_v1", "used": "rules_v1", "model": None, "fallback_reason": None,
                           "guard": None}
    assert all(set(q) == {"question", "why", "information_sought"} for q in corps["questions"])
    assert corps["next_actions"] == [a["text"] for a in r["next_actions"]]


def test_compte_rendu_points_reponses_et_equipes(client):
    corps = client.post("/v2/meetings/report", json={
        "opportunity_id": "O-05", "collected_points": ["budget_constraints"],
        "answers": [{"information_sought": "technical_constraints", "answer": "Garder la même texture."}],
        "notes": "Le client veut garder la même allégation sur l'étiquette.",
    }).json()
    assert corps["collected_points"] == ["client_objectives", "technical_constraints", "budget_constraints"]
    assert corps["answers"] == [{"information_sought": "technical_constraints", "answer": "Garder la même texture."}]
    r = corps["summary"]
    assert [m["point"] for m in r["missing_information"]] == ["real_need", "timeline", "decision_criteria"]
    assert r["technical_constraints"] == [{"point": "technical_constraints", "status": "confirmed",
                                           "text": "Contraintes techniques : Garder la même texture.",
                                           "excerpt": "Garder la même texture."}]  # réponse = confirmée
    assert [(e["status"], e["excerpt"]) for e in r["budget_constraints"]] == [("to_verify", None)]  # cochée sans détail
    assert r["needs"][0]["excerpt"] == "Le client veut garder la même allégation sur l'étiquette."
    assert equipes(r) == ["application", "regulatory"]
    assert r["internal_teams"][1]["excerpt"] == "Le client veut garder la même allégation sur l'étiquette."
    assert r["opportunity_decision"] == "to_qualify"
    assert "Obtenir l'information manquante : calendrier." in corps["next_actions"]


def test_compte_rendu_sans_rien_coche(client):
    corps = client.post("/v2/meetings/report", json={"opportunity_id": "O-04"}).json()
    r = corps["summary"]
    assert len(r["missing_information"]) == 6 and corps["collected_points"] == []
    assert all(m["status"] == "to_verify" and m["excerpt"] is None for m in r["missing_information"])
    technique = next(m for m in r["missing_information"] if m["point"] == "technical_constraints")
    assert "connu avant le rendez-vous" in technique["text"] and "À reconfirmer" in technique["text"]
    assert r["internal_teams"] == [] and r["opportunity_decision"] == "to_qualify"
    assert "Aucune note saisie." in r["summary"]


def test_compte_rendu_objectifs_et_besoin_confirmes_dans_les_notes(client):
    corps = client.post("/v2/meetings/report", json={
        "opportunity_id": "O-01", "date": "2026-11-18",
        "notes": "Le client veut lancer une boisson fonctionnelle. Leur besoin : un arôme agrumes."}).json()
    assert corps["date"] == "2026-11-18"
    assert corps["summary"]["opportunity_decision"] == "confirmed"
    assert equipes(corps["summary"]) == ["creation", "marketing"]  # nouvelle gamme + signal de marché


def test_compte_rendu_points_coches_sans_detail_restent_a_verifier(client):
    """Cocher objectifs et besoin sans rien noter ne suffit pas à confirmer (rien dans les notes)."""
    corps = client.post("/v2/meetings/report", json={
        "opportunity_id": "O-01", "collected_points": ["client_objectives", "real_need"]}).json()
    r = corps["summary"]
    assert all(e["status"] == "to_verify" and e["excerpt"] is None for e in r["needs"])
    assert r["opportunity_decision"] == "to_qualify"


def test_compte_rendu_jamais_ecarte_automatiquement(client):
    for opp in OPPORTUNITES:
        r = client.post("/v2/meetings/report", json={"opportunity_id": opp}).json()["summary"]
        assert r["opportunity_decision"] != "discarded"
        assert set(equipes(r)) <= {"application", "creation", "marketing", "regulatory"}


@pytest.mark.parametrize("methode, url, corps, attendu", [
    ("get", "/v2/clients/C-99", None, "Client inconnu : C-99"),
    ("get", "/v2/opportunities/O-99", None, "Opportunité inconnue : O-99"),
    ("get", "/v2/opportunities/O-99/meeting", None, "Opportunité inconnue : O-99"),
    ("post", "/v2/meetings/report", {"opportunity_id": "O-99"}, "Opportunité inconnue : O-99"),
])
def test_404_id_inconnu(client, methode, url, corps, attendu):
    reponse = getattr(client, methode)(url, **({"json": corps} if corps else {}))
    assert reponse.status_code == 404
    assert reponse.json()["detail"] == attendu


@pytest.mark.parametrize("corps", [
    {"opportunity_id": "O-01", "collected_points": ["prix"]},
    {"opportunity_id": "O-01", "answers": [{"information_sought": "prix", "answer": "x"}]},
    {"opportunity_id": "O-01", "date": "18/11/2026"},
])
def test_entree_invalide_422(client, corps):
    assert client.post("/v2/meetings/report", json=corps).status_code == 422


def test_cors_ouvert(client):
    reponse = client.get("/v2/dashboard", headers={"Origin": "http://localhost:5173"})
    assert reponse.headers["access-control-allow-origin"] == "*"
