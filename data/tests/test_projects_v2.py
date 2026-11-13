"""Contrôles de data/demo_v2/projects.json (DATA-US04).

Lancer : pytest data/tests/test_projects_v2.py
"""

import importlib.util
import json
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"
CLES = {"id", "client_id", "name", "description", "status", "start_date"}
STATUTS = {"active", "completed"}
ACTIFS_ATTENDUS = {"C-01": 3, "C-02": 2, "C-03": 1}  # doc v2, section 8
DATE_JEU = date(2026, 11, 12)


def charger(nom):
    with open(DOSSIER / nom, encoding="utf-8") as fichier:
        return json.load(fichier)


@pytest.fixture(scope="module")
def projets():
    return charger("projects.json")


@pytest.fixture(scope="module")
def clients():
    return {c["id"]: c for c in charger("clients.json")}


def test_ids_uniques(projets):
    ids = [p["id"] for p in projets]
    assert len(ids) == len(set(ids))


def test_champs_remplis(projets):
    for p in projets:
        assert set(p) == CLES, p["id"]
        assert all(isinstance(v, str) and v.strip() for v in p.values()), p["id"]


def test_client_existe(projets, clients):
    assert all(p["client_id"] in clients for p in projets)


def test_statuts_valides(projets):
    assert {p["status"] for p in projets} <= STATUTS


def test_projets_actifs_par_client(projets):
    actifs = Counter(p["client_id"] for p in projets if p["status"] == "active")
    assert dict(actifs) == ACTIFS_ATTENDUS


def test_projet_termine_de_c02_avec_retour_texture(projets):
    termines = [p for p in projets if p["client_id"] == "C-02" and p["status"] == "completed"]
    assert len(termines) == 1
    assert "texture" in termines[0]["description"]


def test_projet_gamme_existante_de_c01(projets):
    """Signal « projet existant » de l'opportunité « extension d'une gamme aromatique »."""
    p = [p for p in projets if p["client_id"] == "C-01" and p["status"] == "active"
         and "gamme existante" in p["name"]]
    assert len(p) == 1
    assert p[0]["start_date"] == "2026-10-10"
    assert "20/10/2026" in p[0]["description"]
    assert "extension" not in (p[0]["name"] + p[0]["description"]).lower()


def test_projets_actifs_de_c02_hors_opportunites(projets):
    """Projet = travail engagé ; le végétal, la texture et le coût restent des opportunités."""
    for p in projets:
        if p["client_id"] == "C-02" and p["status"] == "active":
            texte = (p["name"] + " " + p["description"]).lower()
            assert not any(m in texte for m in ("végétal", "texture", "coût", "budget")), p["id"]


def test_dates_valides_et_coherentes(projets, clients):
    for p in projets:
        debut = date.fromisoformat(p["start_date"])
        assert debut < DATE_JEU, p["id"]
        assert debut <= date.fromisoformat(clients[p["client_id"]]["last_updated"]), p["id"]


def test_fichier_a_jour_avec_le_generateur():
    spec = importlib.util.spec_from_file_location("generer_demo_v2", DOSSIER / "generer_demo_v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (DOSSIER / "projects.json").read_text(encoding="utf-8") == module.generer_fichiers()["projects.json"]
