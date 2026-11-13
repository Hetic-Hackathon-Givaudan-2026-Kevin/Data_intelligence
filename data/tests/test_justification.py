"""Justification commerciale des opportunités (DATA-US08) : data/demo_v2/justification.py.

Lancer : pytest data/tests/test_justification.py
"""

import json
import re
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"
RUBRIQUES = ["client_need", "why_now", "value_for_givaudan", "internal_teams", "facts", "hypotheses",
             "to_confirm", "risks"]
EQUIPES = ["application", "creation", "marketing", "regulatory"]
EURO = re.compile(r"€|\d[\d  .,]*\s*(k|M)?\s*(EUR|euros?)\b", re.IGNORECASE)  # un montant, pas l'unité d'un indice


def lire(nom):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


OPPORTUNITES = lire("opportunities.json")
SIGNAUX = lire("signals.json")
IDS_SIGNAUX = {s["id"] for s in SIGNAUX}
IDS_PROJETS = {p["id"] for p in lire("projects.json")}


def phrases(j):
    return [p for r in RUBRIQUES if r != "internal_teams" for p in j[r]]


@pytest.fixture(params=OPPORTUNITES, ids=lambda o: o["id"])
def opp(request):
    return request.param


def test_toutes_les_rubriques(opp):
    j = opp["justification"]
    assert list(j) == RUBRIQUES
    for r in ("client_need", "why_now", "value_for_givaudan", "facts"):
        assert j[r], (opp["id"], r)


def test_cite_au_moins_un_id_de_signal(opp):
    cites = {s for p in phrases(opp["justification"]) for s in p["sources"]} & IDS_SIGNAUX
    assert cites
    assert any(re.search(r"\bS-\d{2}\b", p["text"]) for p in opp["justification"]["client_need"])


def test_chaque_phrase_a_une_source_existante(opp):
    for p in phrases(opp["justification"]):
        assert p["text"].strip() and p["evidence_type"] in {"fact", "hypothesis", "to_confirm"}
        assert p["sources"], p["text"]
        for s in p["sources"]:
            if re.fullmatch(r"S-\d{2}", s):
                assert s in IDS_SIGNAUX, s
            elif re.fullmatch(r"P-\d{2}", s):
                assert s in IDS_PROJETS, s
            else:
                fichier = s.split("#")[0]
                assert (DOSSIER / fichier).exists(), s


def test_les_signaux_cites_sont_ceux_de_l_opportunite(opp):
    propres = {s["id"] for s in SIGNAUX if s["opportunity_id"] == opp["id"]}
    cites = {s for p in phrases(opp["justification"]) for s in p["sources"]} & IDS_SIGNAUX
    # les contraintes connues du RDV peuvent venir d'un autre signal du même client (ex. budget S-07)
    autres = cites - propres
    clients = {s["id"]: s["client_id"] for s in SIGNAUX}
    assert all(clients[s] == opp["client_id"] for s in autres), autres


def test_aucun_montant_en_euros(opp):
    for p in phrases(opp["justification"]):
        assert not EURO.search(p["text"]), p["text"]


def test_faits_et_hypotheses_ne_sont_pas_melanges(opp):
    j = opp["justification"]
    par_id = {s["id"]: s for s in SIGNAUX}
    assert all(p["evidence_type"] == "fact" for p in j["facts"])
    assert all(p["evidence_type"] == "hypothesis" for p in j["hypotheses"])
    assert all(p["evidence_type"] == "to_confirm" for p in j["to_confirm"])
    for p in j["facts"]:
        assert all(par_id[s]["evidence_type"] == "fact" for s in p["sources"] if s in par_id), p["text"]
    # une phrase qui reprend le contenu d'une hypothèse le dit dans son texte, où qu'elle soit
    for s in SIGNAUX:
        if s["opportunity_id"] == opp["id"] and s["evidence_type"] != "fact":
            for p in phrases(j):
                if s["description"][:40] in p["text"]:
                    assert p["evidence_type"] == s["evidence_type"], p["text"]
                    assert (p in j["hypotheses"] + j["to_confirm"]
                            or p["text"].startswith(("Hypothèse", "À confirmer"))), p["text"]


def test_hypothese_de_la_demo_classee_en_hypothese():
    o3 = next(o for o in OPPORTUNITES if o["id"] == "O-03")["justification"]
    assert o3["hypotheses"][0]["sources"] == ["S-05"]
    assert all("S-05" not in p["sources"] for p in o3["facts"])


def test_rubrique_hypotheses_reprend_toutes_les_phrases_marquees_hypothese(opp):
    """Potentiel déduit, piste, équipes, complexité… : toute phrase [hypothèse] figure dans « Hypothèses »,
    sauf celle qui redit un signal hypothèse déjà listé."""
    j = opp["justification"]
    signaux_hyp = {s for p in j["hypotheses"] for s in p["sources"] if s in IDS_SIGNAUX}
    for r in ("client_need", "why_now", "value_for_givaudan", "risks"):
        for p in j[r]:
            if p["evidence_type"] == "hypothesis" and not set(p["sources"]) <= signaux_hyp:
                assert p in j["hypotheses"], (r, p["text"])
    a_qualifier = [p for r in ("value_for_givaudan", "risks") for p in j[r] if p["evidence_type"] == "hypothesis"]
    if a_qualifier:
        assert j["hypotheses"]


def test_a_confirmer_reprend_les_criteres_inconnus_cites_ailleurs(opp):
    j = opp["justification"]
    sources = {s for p in j["to_confirm"] for s in p["sources"]}
    for r in ("value_for_givaudan", "risks"):
        for p in j[r]:
            if p["evidence_type"] == "to_confirm":
                assert set(p["sources"]) <= sources, (r, p["text"])


def test_un_reglement_n_est_pas_un_pourquoi_maintenant(opp):
    reglements = {s["id"] for s in SIGNAUX if s["opportunity_id"] == opp["id"] and s["source_type"] == "regulation"}
    j = opp["justification"]
    assert not any(set(p["sources"]) & reglements for p in j["why_now"])
    for r in reglements:
        cadre = [p for p in j["value_for_givaudan"] if p["sources"] == [r]]
        assert len(cadre) == 1 and cadre[0]["text"].startswith("Cadre réglementaire")
        piste = [p for p in j["value_for_givaudan"] if r in p["sources"] and p["text"].startswith("Piste")]
        assert len(piste) == 1 and piste[0]["evidence_type"] == "hypothesis" and piste[0] in j["hypotheses"]


def test_s11_ne_garde_que_le_fait():
    s11 = next(s for s in SIGNAUX if s["id"] == "S-11")
    assert s11["evidence_type"] == "fact" and "872/2012" in s11["description"] and "limonène" in s11["description"]
    assert "piste" not in s11["description"] and "nouvelle référence" not in s11["description"]
    o6 = next(o for o in OPPORTUNITES if o["id"] == "O-06")["justification"]
    assert any("S-11" in p["sources"] and "Nouvelle référence" in p["text"] for p in o6["hypotheses"])


def test_criteres_inconnus_donnent_une_partie_a_confirmer(opp):
    a_confirmer = " ".join(p["text"] for p in opp["justification"]["to_confirm"])
    if opp["missing_criteria"]:
        assert opp["justification"]["to_confirm"]
        for c in opp["missing_criteria"]:
            assert any(f"grille_qualification.json#{c}" in p["sources"] for p in opp["justification"]["to_confirm"]), c
    if opp["priority_status"] == "provisional":
        assert "Priorité provisoire" in a_confirmer


def test_valeur_commerciale_en_niveau(opp):
    valeur = opp["justification"]["value_for_givaudan"]
    potentiel = valeur[0]["text"]
    if opp["estimated_potential"] is None:
        assert potentiel.startswith("Valeur commerciale non estimée") and valeur[0]["evidence_type"] == "to_confirm"
    else:
        assert "jamais un montant" in potentiel
    assert any(p["text"].startswith("Relation client") for p in valeur)


def test_equipes_selon_la_categorie_et_les_signaux(opp):
    equipes = opp["justification"]["internal_teams"]
    assert equipes and set(equipes) <= set(EQUIPES) and equipes == [e for e in EQUIPES if e in equipes]
    assert "application" in equipes
    types = {s["source_type"] for s in SIGNAUX if s["opportunity_id"] == opp["id"]}
    assert ("regulatory" in equipes) == ("regulation" in types)
    assert ("marketing" in equipes) == bool(types & {"market_trend", "company_report"})


def test_pourquoi_maintenant_commence_par_le_signal_le_plus_recent(opp):
    propres = [s for s in SIGNAUX if s["opportunity_id"] == opp["id"]]
    recent = max(propres, key=lambda s: (s["source_date"], s["id"]))
    premier = opp["justification"]["why_now"][0]
    assert premier["sources"] == [recent["id"]] and "Signal le plus récent" in premier["text"]


def test_aucune_affirmation_sur_givaudan_hors_sources(opp):
    """Givaudan n'est cité que dans des phrases sourcées par un signal qui le cite déjà."""
    par_id = {s["id"]: s for s in SIGNAUX}
    for p in phrases(opp["justification"]):
        if "Givaudan" in p["text"]:
            assert any("Givaudan" in par_id[s]["description"] for s in p["sources"] if s in par_id), p["text"]


def test_justification_identique_dans_l_api():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    import importlib.util

    from fastapi.testclient import TestClient
    spec = importlib.util.spec_from_file_location("api_main_justif", DOSSIER.parent / "api" / "main.py")
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    client = TestClient(api.app)
    for o in OPPORTUNITES:
        j = client.get(f"/v2/opportunities/{o['id']}").json()["justification"]
        assert {k: j[k] for k in RUBRIQUES} == o["justification"], o["id"]
