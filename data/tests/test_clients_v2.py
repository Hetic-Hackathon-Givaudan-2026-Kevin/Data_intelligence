"""Contrôles de data/demo_v2/clients.json (DATA-US03).

Lancer : pytest data/tests/test_clients_v2.py
"""

import importlib.util
import json
import re
from datetime import date
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"
CLES = {"id", "name", "sector", "country", "account_manager", "relationship_status",
        "last_updated", "commercial_situation", "history_summary"}
STATUTS = {"strategic", "active", "to_develop"}
MOTS_COMPTEUR = re.compile(r"count|nb|nombre|total|number|projects?|opportunit(y|ies)", re.IGNORECASE)


@pytest.fixture(scope="module")
def clients():
    with open(DOSSIER / "clients.json", encoding="utf-8") as fichier:
        return json.load(fichier)


def phrases(texte):
    return [p for p in re.split(r"[.!?](?:\s|$)", texte) if p.strip()]


def test_au_moins_3_clients_ids_uniques(clients):
    assert len(clients) >= 3
    ids = [c["id"] for c in clients]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"C-\d{2}", i) for i in ids)


def test_tous_les_champs_remplis(clients):
    for c in clients:
        assert set(c) == CLES, c["id"]
        assert all(isinstance(v, str) and v.strip() for v in c.values()), c["id"]
        date.fromisoformat(c["last_updated"])


def test_statuts_valides_et_varies(clients):
    statuts = [c["relationship_status"] for c in clients]
    assert set(statuts) <= STATUTS
    assert len(set(statuts)) >= 2


def test_aucun_compteur(clients):
    for c in clients:
        morceaux = [m for cle in c for m in re.split(r"_|(?<=[a-z])(?=[A-Z])", cle)]  # snake_case et camelCase
        assert not any(MOTS_COMPTEUR.fullmatch(m) for m in morceaux), c["id"]
        assert not any(isinstance(v, (int, float, list)) for v in c.values()), c["id"]


def test_longueur_des_textes(clients):
    for c in clients:
        assert len(phrases(c["commercial_situation"])) <= 2, c["id"]
        assert 2 <= len(phrases(c["history_summary"])) <= 3, c["id"]


def test_responsable_fictif(clients):
    assert all("(fictif)" in c["account_manager"] for c in clients)


def test_fichier_a_jour_avec_le_generateur():
    spec = importlib.util.spec_from_file_location("generer_demo_v2", DOSSIER / "generer_demo_v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (DOSSIER / "clients.json").read_text(encoding="utf-8") == module.generer()
