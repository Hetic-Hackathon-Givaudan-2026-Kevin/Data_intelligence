"""Compte rendu de rendez-vous (DATA-US11) : data/demo_v2/compte_rendu.py et meetings.json.

Aucun test n'appelle Ollama : le modèle est remplacé par une fonction `appel` simulée, ou par une
adresse fermée pour vérifier le retour à rules_v1.

Lancer : pytest data/tests/test_compte_rendu.py
"""

import importlib.util
import json
import socket
import urllib.error
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1]
DOSSIER = DATA / "demo_v2"
RUBRIQUES = ["needs", "technical_constraints", "budget_constraints", "timeline"]
DEDUITES = ["missing_information", "next_actions", "internal_teams"]


def charger(nom, chemin):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cr = charger("compte_rendu", DOSSIER / "compte_rendu.py")
MEETINGS = json.loads((DOSSIER / "meetings.json").read_text(encoding="utf-8"))


def elements(rapport):
    return [e for r in RUBRIQUES for e in rapport[r]]


def sortie(*items):
    return lambda notes, **_: json.dumps({"items": list(items)})


# --- rules_v1 -----------------------------------------------------------------------------------

def test_rules_v1_une_phrase_par_point():
    elts = cr.extraire_rules_v1("Le client veut lancer une boisson. Leur besoin : un arôme agrumes. Budget serré.")
    assert [(e["point"], e["status"]) for e in elts] == [
        ("client_objectives", "confirmed"), ("real_need", "confirmed"), ("budget_constraints", "confirmed")]
    assert elts[1]["excerpt"] == "Leur besoin : un arôme agrumes."


def test_rules_v1_hesitation_a_verifier():
    elts = cr.extraire_rules_v1("Le budget sera peut-être revu. Launch might be in March 2027.")
    assert {e["point"]: e["status"] for e in elts} == {"budget_constraints": "to_verify", "timeline": "to_verify"}


def test_rules_v1_deux_dates_calendrier_a_verifier():
    elts = cr.extraire_rules_v1("Lancement prévu en mars 2027. Plus tard, l'acheteur a parlé d'une sortie en mai 2027.")
    calendrier = [e for e in elts if e["point"] == "timeline"]
    assert len(calendrier) == 2 and all(e["status"] == "to_verify" for e in calendrier)


def test_rules_v1_note_hors_sujet_vide():
    assert cr.extraire_rules_v1("Suivi de livraison de la commande 1234 : colis attendu jeudi.") == []


# --- llm_v2 : schéma, garde-fou, retour à rules_v1 ----------------------------------------------

NOTES = "Le client veut lancer une boisson fonctionnelle. Leur besoin : un arôme agrumes."


def test_llm_v2_garde_fou():
    appel = sortie(
        {"point": "client_objectives", "text": "x", "status": "confirmed",
         "excerpt": "Le client veut lancer une boisson fonctionnelle."},              # exact : gardé
        {"point": "real_need", "text": "Il leur faut un arôme d'agrumes", "status": "confirmed",
         "excerpt": "besoin : un arôme d'agrumes"},                                   # proche : to_verify
        {"point": "budget_constraints", "text": "Budget de 50 000 euros", "status": "confirmed",
         "excerpt": "Le budget est de 50 000 euros."},                                # inventé : écarté
        {"point": "timeline", "text": "", "status": "to_verify", "excerpt": ""},      # vide : écarté
    )
    elts, engine = cr.extraire(NOTES, "llm_v2", appel=appel)
    assert engine["used"] == "llm_v2" and engine["fallback_reason"] is None
    assert engine["guard"] == {"kept": 1, "downgraded": 1, "dropped": 2}
    assert [(e["point"], e["status"]) for e in elts] == [("client_objectives", "confirmed"), ("real_need", "to_verify")]
    assert all(cr.present_dans(e["excerpt"], [NOTES]) for e in elts)  # tout élément gardé est dans les notes


@pytest.mark.parametrize("appel, motif", [
    (lambda notes, **_: "pas du json", "JSON invalide"),
    (sortie({"point": "prix", "text": "x", "status": "confirmed", "excerpt": "x"}), "JSON invalide"),
    (sortie({"point": "timeline", "text": "x", "status": "peut-être", "excerpt": "x"}), "JSON invalide"),
    (lambda notes, **_: json.dumps({"elements": []}), "JSON invalide"),
])
def test_llm_v2_json_invalide_retour_rules_v1(appel, motif):
    elts, engine = cr.extraire(NOTES, "llm_v2", appel=appel)
    assert engine["requested"] == "llm_v2" and engine["used"] == "rules_v1"
    assert engine["fallback_reason"].startswith(motif)
    assert elts == cr.extraire_rules_v1(NOTES)


def leve(erreur):
    def appel(notes, **_):
        raise erreur
    return appel


@pytest.mark.parametrize("erreur, motif", [
    (urllib.error.URLError(ConnectionRefusedError("refusée")), "Ollama injoignable"),
    (socket.timeout("timed out"), "délai dépassé"),
    (urllib.error.URLError(socket.timeout("timed out")), "délai dépassé"),
])
def test_llm_v2_ollama_absent_ou_lent_retour_rules_v1(erreur, motif):
    elts, engine = cr.extraire(NOTES, "llm_v2", appel=leve(erreur))
    assert engine["used"] == "rules_v1" and engine["fallback_reason"].startswith(motif)
    assert elts == cr.extraire_rules_v1(NOTES)


def test_llm_v2_adresse_fermee_retour_rules_v1():
    """Vrai appel HTTP vers un port fermé : pas d'exception, retour à rules_v1."""
    elts, engine = cr.extraire(NOTES, "llm_v2", url="http://127.0.0.1:9", timeout=2)
    # refus de connexion ou expiration selon le système (Windows laisse souvent expirer)
    assert engine["used"] == "rules_v1" and engine["fallback_reason"].startswith(("Ollama injoignable", "délai dépassé"))


def test_llm_v2_n_appelle_que_le_local_par_defaut():
    assert cr.OLLAMA_URL.startswith(("http://localhost", "http://127.0.0.1")) or "OLLAMA_URL" in __import__("os").environ
    assert cr.OLLAMA_MODEL == "qwen2.5:3b" or "OLLAMA_MODEL" in __import__("os").environ


# --- meetings.json : 2 exemples statiques pour TECH --------------------------------------------

def test_deux_rendez_vous_o01_o03():
    assert [(m["id"], m["opportunity_id"]) for m in MEETINGS] == [("M-01", "O-01"), ("M-02", "O-03")]
    opps = {o["id"]: o for o in json.loads((DOSSIER / "opportunities.json").read_text(encoding="utf-8"))}
    for m in MEETINGS:
        assert m["client_id"] == opps[m["opportunity_id"]]["client_id"]
        assert m["status"] == "completed" and m["notes"].strip() and m["date"] <= "2026-11-12"
        assert m["summary"]["generated_by"] == "rules_v1" and m["summary"]["validated"] is False
        assert m["next_actions"] == [a["text"] for a in m["summary"]["next_actions"]]


@pytest.mark.parametrize("meeting", MEETINGS, ids=lambda m: m["id"])
def test_rien_n_est_invente(meeting):
    r, sources = meeting["summary"], [meeting["notes"], *(a["answer"] for a in meeting["answers"])]
    for rubrique in RUBRIQUES + DEDUITES:
        for e in r[rubrique]:
            assert e["status"] in ("confirmed", "to_verify")
            if e["excerpt"] is not None:
                assert cr.present_dans(e["excerpt"], sources), (rubrique, e["excerpt"])
            if e["status"] == "confirmed":
                assert e["excerpt"], (rubrique, e["text"])
    for e in elements(r):
        assert e["excerpt"] or e["text"].startswith("Point coché")
    for rubrique in DEDUITES:
        assert all(e["status"] == "to_verify" for e in r[rubrique]), rubrique


@pytest.mark.parametrize("meeting", MEETINGS, ids=lambda m: m["id"])
def test_rubriques_coherentes(meeting):
    r = meeting["summary"]
    couverts = {e["point"] for e in elements(r)}
    assert couverts == set(meeting["collected_points"])
    assert {m["point"] for m in r["missing_information"]} == set(cr.POINTS) - couverts
    assert all(cr.RUBRIQUE[e["point"]] == rub for rub in RUBRIQUES for e in r[rub])
    assert {e["team"] for e in r["internal_teams"]} <= set(cr.LIBELLES_EQUIPES)


def test_exemples_montrent_les_deux_statuts():
    statuts = {e["status"] for m in MEETINGS for e in elements(m["summary"])}
    assert statuts == {"confirmed", "to_verify"}
    m1 = MEETINGS[0]["summary"]
    assert [e["status"] for e in m1["timeline"]] == ["to_verify"]  # « envisagé… à confirmer »


def test_meetings_a_jour_avec_le_generateur():
    module = charger("generer_demo_v2", DOSSIER / "generer_demo_v2.py")
    assert (DOSSIER / "meetings.json").read_text(encoding="utf-8") == module.generer_fichiers()["meetings.json"]


# --- API : paramètre mode ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    module = charger("api_main_cr", DATA / "api" / "main.py")
    return module, TestClient(module.app)


def test_api_mode_llm_v2_sans_ollama_retombe_sur_rules_v1(api, monkeypatch):
    module, client = api
    monkeypatch.setattr(module.compte_rendu, "OLLAMA_URL", "http://127.0.0.1:9")
    monkeypatch.setattr(module.compte_rendu, "OLLAMA_TIMEOUT", 2)
    corps = client.post("/v2/meetings/report?mode=llm_v2", json={"opportunity_id": "O-01", "notes": NOTES}).json()
    engine = corps["summary"]["engine"]
    assert engine["requested"] == "llm_v2" and engine["used"] == "rules_v1" and engine["fallback_reason"]
    assert corps["summary"]["generated_by"] == "rules_v1"


def test_api_mode_llm_v2_avec_modele_simule(api, monkeypatch):
    module, client = api
    monkeypatch.setattr(module.compte_rendu, "appeler_ollama", sortie(
        {"point": "real_need", "text": "x", "status": "confirmed", "excerpt": "Leur besoin : un arôme agrumes."}))
    r = client.post("/v2/meetings/report?mode=llm_v2", json={"opportunity_id": "O-01", "notes": NOTES}).json()["summary"]
    assert r["generated_by"] == "llm_v2" and r["engine"]["model"] == "qwen2.5:3b"
    assert [e["point"] for e in r["needs"]] == ["real_need"]


def test_api_mode_inconnu_422(api):
    _, client = api
    assert client.post("/v2/meetings/report?mode=gpt", json={"opportunity_id": "O-01"}).status_code == 422


# --- Banc d'essai V1/V2 (data/cas_test) : partie rules_v1 revérifiée sans LLM --------------------

def test_banc_resultats_complets_et_v1_reproductible():
    ev = charger("evaluer_v1_v2", DATA / "cas_test" / "evaluer_v1_v2.py")
    res = json.loads((DATA / "cas_test" / "resultats_v1_v2.json").read_text(encoding="utf-8"))
    assert res["protocole"]["cas"] == 30 and len(res["par_cas"]) == 30  # aucun cas retiré
    cas, _ = ev.charger_cas()
    v1 = ev.mesurer(cas, [ev.lancer(c, "rules_v1", 1) for c in cas])
    assert v1["par_rubrique"] == res["rules_v1"]["par_rubrique"]
    v2 = res["llm_v2"]
    assert v2["inventes_texte_sortie"] == 0  # garde-fou : rien d'introuvable dans la sortie finale
    assert set(v2) >= {"par_rubrique", "garde_fou", "justesse_statut", "retours_rules_v1", "depassements_delai",
                       "temps_moyen_s"}
    assert (DATA / "cas_test" / "resultats_v1_v2.md").read_text(encoding="utf-8").count("## ") >= 3
