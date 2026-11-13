"""Contrôles de data/signaux/signaux_marche.json (signaux de marché Open Food Facts).

Lancer : pytest data/tests/test_signaux.py
Le fichier est produit par data/signaux/calculer_signaux.py à partir d'un Parquet hors
du repo : ces tests vérifient sa cohérence interne, pas son recalcul.
"""

import json
import math
from datetime import date
from pathlib import Path

import pytest

FICHIER = Path(__file__).resolve().parents[1] / "signaux" / "signaux_marche.json"
MIN_PRODUITS = 50
PRINCIPALE, ROBUSTESSE, RECENTE = "2020-2022", "2019-2022", "2023-2025"


@pytest.fixture(scope="module")
def signaux():
    with open(FICHIER, encoding="utf-8") as fichier:
        return json.load(fichier)


def avec_signal(signaux):
    return [(s["opportunite_id"], s["signal"]) for s in signaux["signaux"] if s["signal"]]


def evolution(annees, debut, fin):
    part = {a: annees[str(a)]["produits"] / annees[str(a)]["base"] for a in (debut, fin)}
    return 100 * part[fin] / part[debut] - 100


def test_source_et_licence(signaux):
    assert signaux["source"]["nom"] == "Open Food Facts"
    assert "ODbL" in signaux["source"]["licence"] and "ODbL" in signaux["licence_fichier"]
    date.fromisoformat(signaux["date_extraction"])
    date.fromisoformat(signaux["source"]["dernier_produit_ajoute"])
    assert signaux["pays"] == "en:france"
    assert set(signaux["periodes"]) == {PRINCIPALE, ROBUSTESSE, RECENTE}
    assert "non mûr" in signaux["periodes"][RECENTE]


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
    for opp, g in avec_signal(signaux):
        assert list(g["annees"]) == [str(a) for a in range(2019, 2026)], opp
        for v in g["annees"].values():
            assert 0 <= v["produits"] <= v["base"]
            assert v["part_pct"] == pytest.approx(100 * v["produits"] / v["base"], abs=1e-3)
        for cle, p in g["periodes"].items():
            assert cle == f"{p['debut']}-{p['fin']}"
            assert p["evolution_part_pct"] == pytest.approx(evolution(g["annees"], p["debut"], p["fin"]), abs=0.06)
            assert p["produits_min_par_an"] == min(g["annees"][str(a)]["produits"]
                                                   for a in range(p["debut"], p["fin"] + 1))
        assert "non mûr" in g["periodes"][RECENTE]["role"]


def test_regle_de_robustesse(signaux):
    for opp, g in avec_signal(signaux):
        e_p = g["periodes"][PRINCIPALE]["evolution_part_pct"]
        e_r = g["periodes"][ROBUSTESSE]["evolution_part_pct"]
        assez = g["produits_min_par_an_2019_2022"] >= MIN_PRODUITS
        assert g["produits_min_par_an_2019_2022"] == min(g["annees"][str(a)]["produits"] for a in range(2019, 2023))
        attendu = ("compte" if assez and e_p > 0 and e_r > 0
                   else "contraire" if assez and e_p < 0 and e_r < 0 else "indicatif")
        assert g["statut"] == attendu, opp
        assert g["compte"] == (attendu == "compte")


def test_texte_et_arrondi_a_la_dizaine(signaux):
    for opp, g in avec_signal(signaux):
        exacte = g["periodes"][PRINCIPALE]["evolution_part_pct"]
        assert g["evolution_affichee_pct"] % 10 == 0
        assert g["evolution_affichee_pct"] == int(math.copysign(math.floor(abs(exacte) / 10 + 0.5) * 10, exacte))
        assert g["trigger"].startswith("Part des nouveaux produits ")
        assert " en France : " in g["trigger"] and "(2020→2022, Open Food Facts)" in g["trigger"]
        pourcentage = "0 %" if g["evolution_affichee_pct"] == 0 else f"{g['evolution_affichee_pct']:+d} %"
        assert f" : {pourcentage} (" in g["trigger"], opp
        assert ("signal contraire" in g["trigger"]) == (g["statut"] == "contraire")
        assert ("indicatif" in g["trigger"]) == (g["statut"] == "indicatif")


def test_cas_valides_par_l_equipe(signaux):
    statut = {opp: g["statut"] for opp, g in avec_signal(signaux)}
    assert statut["OPP-03"] == "contraire"  # en baisse sur les deux périodes
    assert statut["OPP-07"] == "indicatif"  # 2019→2022 et 2020→2022 divergent
