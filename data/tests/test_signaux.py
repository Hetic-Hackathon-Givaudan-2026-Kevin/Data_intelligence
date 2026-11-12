"""Contrôles de data/signaux/signaux_marche.json (signaux de marché Open Food Facts).

Lancer : pytest data/tests/test_signaux.py
Le fichier est produit par data/signaux/calculer_signaux.py à partir d'un Parquet hors
du repo : ces tests vérifient sa cohérence interne, pas son recalcul.
"""

import json
from datetime import date
from pathlib import Path

import pytest

FICHIER = Path(__file__).resolve().parents[1] / "signaux" / "signaux_marche.json"
MIN_PRODUITS = 50


@pytest.fixture(scope="module")
def signaux():
    with open(FICHIER, encoding="utf-8") as fichier:
        return json.load(fichier)


def test_source_et_licence(signaux):
    assert signaux["source"]["nom"] == "Open Food Facts"
    assert "ODbL" in signaux["source"]["licence"] and "ODbL" in signaux["licence_fichier"]
    date.fromisoformat(signaux["date_extraction"])
    date.fromisoformat(signaux["source"]["dernier_produit_ajoute"])
    assert signaux["periode"] == {"debut": 2023, "fin": 2025}
    assert signaux["pays"] == "en:france"


def test_12_opportunites(signaux):
    ids = [s["opportunite_id"] for s in signaux["signaux"]]
    assert ids == [f"OPP-{n:02d}" for n in range(1, 13)]


def test_sans_signal_explique(signaux):
    for s in signaux["signaux"]:
        if s["signal"] is None:
            assert s["raison"].strip()
            assert s["tags"] == {"categories": [], "labels": []}
        else:
            assert s["tags"]["categories"] or s["tags"]["labels"]
            assert all(t.startswith(("en:", "fr:")) for t in s["tags"]["categories"] + s["tags"]["labels"])


def test_chiffres_coherents(signaux):
    for s in signaux["signaux"]:
        g = s["signal"]
        if g is None:
            continue
        annees = g["annees"]
        assert list(annees) == ["2023", "2024", "2025"], s["opportunite_id"]
        for v in annees.values():
            assert 0 <= v["produits"] <= v["base"]
            assert v["part_pct"] == pytest.approx(100 * v["produits"] / v["base"], abs=1e-3)
        part = {a: v["produits"] / v["base"] for a, v in annees.items()}
        assert g["evolution_part_pct"] == pytest.approx(100 * part["2025"] / part["2023"] - 100, abs=0.06)
        assert g["produits_min_par_an"] == min(v["produits"] for v in annees.values())


def test_regle_de_comptage(signaux):
    for s in signaux["signaux"]:
        g = s["signal"]
        if g is None:
            continue
        attendu = g["evolution_part_pct"] > 0 and g["produits_min_par_an"] >= MIN_PRODUITS
        assert g["compte"] == attendu, s["opportunite_id"]
        assert "Open Food Facts" in g["trigger"] and "2023→2025" in g["trigger"]
        if g["produits_min_par_an"] < MIN_PRODUITS:
            assert "indicatif" in g["trigger"]
        elif not g["compte"]:
            assert "signal contraire" in g["trigger"]
