"""Contrôles de data/demo_v2/opportunities.json (DATA-US05) et signals.json (DATA-US06).

Lancer : pytest data/tests/test_opportunities_signals_v2.py
"""

import importlib.util
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"
CLES_OPP = ["id", "client_id", "title", "description", "category", "status", "priority",
            "estimated_potential", "feasibility", "complexity", "next_action"]
CLES_SIGNAL = {"id", "opportunity_id", "description", "source_type", "source_date", "confidence",
               "evidence_type", "is_real_source", "source_ref"}
STATUTS = {"detected", "to_qualify", "confirmed"}
NIVEAUX = {"low", "medium", "high"}
SOURCE_TYPES = {"meeting_report", "project_history", "client_request", "market_trend",
                "commodity_price", "company_report", "regulation"}
DATE_JEU = date(2026, 11, 12)


def charger(nom):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def opportunites():
    return charger("opportunities.json")


@pytest.fixture(scope="module")
def signaux():
    return charger("signals.json")


def textes(objets):
    return [str(v) for o in objets for v in o.values() if v is not None]


def test_six_opportunites_par_client_et_statut(opportunites):
    assert len(opportunites) == 6
    assert len({o["id"] for o in opportunites}) == 6
    assert Counter(o["client_id"] for o in opportunites) == {"C-01": 2, "C-02": 3, "C-03": 1}
    a_qualifier = Counter(o["client_id"] for o in opportunites if o["status"] == "to_qualify")
    assert {c: a_qualifier.get(c, 0) for c in ("C-01", "C-02", "C-03")} == {"C-01": 1, "C-02": 1, "C-03": 0}


def test_champs_et_valeurs_des_opportunites(opportunites):
    clients = {c["id"] for c in charger("clients.json")}
    for o in opportunites:
        assert list(o) == CLES_OPP, o["id"]
        assert o["client_id"] in clients
        assert o["status"] in STATUTS
        assert o["priority"] in NIVEAUX
        assert o["estimated_potential"] in NIVEAUX | {None}
        assert o["feasibility"] in NIVEAUX | {"to_confirm"}
        assert o["complexity"] in NIVEAUX
        assert all(o[k].strip() for k in ("title", "description", "category", "next_action"))


def test_aucun_compteur_ni_date_du_dernier_signal(opportunites):
    for o in opportunites:
        assert not any(re.search(r"count|nb_|last_signal|signal_date|signals", k) for k in o), o["id"]


def test_signaux_valides(signaux):
    assert len({s["id"] for s in signaux}) == len(signaux)
    for s in signaux:
        assert set(s) == CLES_SIGNAL, s["id"]
        assert s["source_type"] in SOURCE_TYPES
        assert s["confidence"] in NIVEAUX
        assert s["evidence_type"] in {"fact", "hypothesis", "to_confirm"}
        assert isinstance(s["is_real_source"], bool)
        assert date.fromisoformat(s["source_date"]) < DATE_JEU, s["id"]


def test_au_moins_un_signal_par_opportunite(opportunites, signaux):
    ids = {o["id"] for o in opportunites}
    assert {s["opportunity_id"] for s in signaux} == ids  # chaque signal pointe une opportunité existante


def test_signal_reel_a_une_source(signaux):
    for s in signaux:
        if s["is_real_source"]:
            assert s["source_ref"] and s["source_ref"].strip(), s["id"]


def test_signaux_reels_attendus(signaux):
    reels = {s["opportunity_id"] for s in signaux if s["is_real_source"]}
    assert reels == {"O-01", "O-03", "O-05", "O-06"}
    # O-06 : la veille marché fictive de la doc est remplacée par des signaux réels
    assert not any(s["opportunity_id"] == "O-06" and not s["is_real_source"]
                   and s["source_type"] in {"market_trend", "company_report"} for s in signaux)


def test_source_date_open_food_facts_fin_de_periode(signaux):
    """Date d'un signal OFF = fin de la période observée, pas la date d'extraction."""
    off = json.loads((DOSSIER.parent / "signaux" / "signaux_marche.json").read_text(encoding="utf-8"))
    fins = {s["opportunite_id"]: next(p["fin"] for p in s["signal"]["periodes"].values()
                                      if p["role"].startswith("principale"))
            for s in off["signaux"] if s["signal"]}
    signaux_off = [s for s in signaux if (s["source_ref"] or "").startswith("data/signaux/signaux_marche.json")]
    assert len(signaux_off) == 2
    for s in signaux_off:
        opp_off = s["source_ref"].split("#")[1].split()[0]
        assert s["source_date"] == f"{fins[opp_off]}-12-31", s["id"]
        assert off["date_extraction"] in s["source_ref"]


def test_projets_cites_existent(opportunites, signaux):
    projets = {p["id"] for p in charger("projects.json")}
    cites = {m for t in textes(opportunites) + textes(signaux) for m in re.findall(r"\bP-\d{2}\b", t)}
    assert cites and cites <= projets


def test_aucun_montant_en_euros(opportunites, signaux):
    for t in textes(opportunites) + textes(signaux):
        assert not re.search(r"€|\d[\d  .,]*\s*(k|M)?\s*(EUR|euros?)\b", t, re.IGNORECASE), t


def test_priorite_suit_la_regle(opportunites, signaux):
    """Confiance du meilleur signal + potentiel + faisabilité + urgence ; high >= 5, medium >= 3."""
    points = {"high": 2, "medium": 1, "low": 0, "to_confirm": 0, None: 0}
    for o in opportunites:
        propres = [s for s in signaux if s["opportunity_id"] == o["id"]]
        urgence = any(s["source_type"] in {"meeting_report", "client_request"}
                      and (DATE_JEU - date.fromisoformat(s["source_date"])).days <= 30 for s in propres)
        score = (max(points[s["confidence"]] for s in propres) + points[o["estimated_potential"]]
                 + points[o["feasibility"]] + urgence)
        attendu = "high" if score >= 5 else "medium" if score >= 3 else "low"
        assert o["priority"] == attendu, (o["id"], score)


def test_fichiers_a_jour_avec_le_generateur():
    spec = importlib.util.spec_from_file_location("generer_demo_v2", DOSSIER / "generer_demo_v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fichiers = module.generer_fichiers()
    for nom in ("opportunities.json", "signals.json"):
        assert (DOSSIER / nom).read_text(encoding="utf-8") == fichiers[nom], nom
