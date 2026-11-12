"""Grille de qualification (DATA-US09) : data/demo_v2/grille_qualification.json et calcul de priorité.

Lancer : pytest data/tests/test_grille_qualification.py
"""

import importlib.util
import json
import re
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"

_spec = importlib.util.spec_from_file_location("generer_demo_v2", DOSSIER / "generer_demo_v2.py")
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)

GRILLE = json.loads((DOSSIER / "grille_qualification.json").read_text(encoding="utf-8"))
CHECKLIST = set(g.CHECKLIST)


def lire(nom):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


def opportunite(potentiel="medium", faisabilite="medium", complexite="low"):
    """Opportunité de test (O-90), avec un signal de confiance moyenne, sans urgence."""
    opp = {"id": "O-90", "estimated_potential": potentiel, "feasibility": faisabilite, "complexity": complexite}
    signaux = [{"id": "S-90", "opportunity_id": "O-90", "confidence": "medium", "source_type": "project_history",
                "source_date": "2026-01-01"}]
    return opp, signaux


# --- La grille ----------------------------------------------------------------------------------

def test_la_grille_couvre_tous_les_criteres_du_calcul():
    opp, signaux = opportunite()
    assert set(g.detail_priorite(opp, signaux)) == {c["id"] for c in GRILLE["criteres"]}
    assert set(g.CRITERES_QUALIFIES) <= {c["id"] for c in GRILLE["criteres"]}
    assert {"confidence", "estimated_potential", "feasibility", "complexity", "urgency"} == set(g.CRITERES)


@pytest.mark.parametrize("critere", GRILLE["criteres"], ids=lambda c: c["id"])
def test_chaque_critere_est_lisible(critere):
    assert critere["nom"].strip() and critere["d_ou_vient_l_information"].strip()
    assert len(critere["niveaux"]) >= 2
    for n in critere["niveaux"]:
        assert n["libelle"].strip() and n["definition"].strip() and isinstance(n["points"], int)
    if critere["peut_etre_inconnu"]:
        assert critere["point_de_rdv_si_inconnu"] in CHECKLIST
        assert critere["valeur_inconnue"] not in [n["valeur"] for n in critere["niveaux"]]


def test_les_niveaux_reprennent_les_valeurs_d_enum_existantes():
    niveaux = {c["id"]: {n["valeur"] for n in c["niveaux"]} for c in GRILLE["criteres"]}
    for c in ("confidence", "estimated_potential", "feasibility", "complexity"):
        assert niveaux[c] == {"low", "medium", "high"}, c
    assert GRILLE["seuils"]["high"] > GRILLE["seuils"]["medium"]


# --- Un critère inconnu ne fait pas tomber en low sans le dire -----------------------------------

def test_inconnu_n_est_pas_faible():
    connu_faible = g.evaluer_priorite(*opportunite(faisabilite="low"))
    inconnu = g.evaluer_priorite(*opportunite(faisabilite="to_confirm"))
    assert inconnu["score_min"] == connu_faible["score_min"]
    assert inconnu["score_max"] > inconnu["score_min"]
    assert inconnu["missing_criteria"] == ["feasibility"]
    assert connu_faible["missing_criteria"] == []


@pytest.mark.parametrize("champ, inconnu", [("estimated_potential", None), ("feasibility", "to_confirm"),
                                             ("complexity", "to_confirm")])
def test_critere_inconnu_toujours_signale(champ, inconnu):
    opp, signaux = opportunite()
    opp[champ] = inconnu
    e = g.evaluer_priorite(opp, signaux)
    assert champ in e["missing_criteria"]
    if e["priority"] == "low":  # jamais un low silencieux
        assert e["priority_status"] == "provisional" or e["missing_criteria"]


def test_priorite_provisoire_quand_les_bornes_different():
    e = g.evaluer_priorite(*opportunite(potentiel=None, faisabilite="to_confirm", complexite="to_confirm"))
    assert e["priority_status"] == "provisional" and e["priority"] != e["priority_max"]
    assert set(e["missing_criteria"]) == {"estimated_potential", "feasibility", "complexity"}


def test_priorite_stable_quand_les_bornes_donnent_le_meme_niveau():
    # faisabilité inconnue : score de 0 à 2, low dans les deux cas ; le critère reste signalé
    e = g.evaluer_priorite(*opportunite(potentiel="low", faisabilite="to_confirm", complexite="high"))
    assert (e["score_min"], e["score_max"]) == (0, 2)
    assert e["priority_status"] == "stable" and e["missing_criteria"] == ["feasibility"]


def test_aucune_opportunite_de_la_demo_en_low_silencieux():
    for o in lire("opportunities.json"):
        if o["priority"] == "low":
            assert o["priority_status"] == "provisional" and o["missing_criteria"], o["id"]
        assert (o["priority_status"] == "provisional") == (o["priority"] != o["priority_max"]), o["id"]


# --- La complexité change le score ---------------------------------------------------------------

def test_la_complexite_change_le_score():
    scores = {c: g.evaluer_priorite(*opportunite(complexite=c))["score_min"] for c in ("low", "medium", "high")}
    assert scores["low"] == scores["medium"] > scores["high"]


def test_la_complexite_ne_compte_pas_deux_fois_la_nouveaute():
    """Nouvelle catégorie : potentiel high (+2) et complexité high (-1), la nouveauté reste un plus."""
    complexite = next(c for c in GRILLE["criteres"] if c["id"] == "complexity")
    potentiel = next(c for c in GRILLE["criteres"] if c["id"] == "estimated_potential")
    pts = lambda c, v: next(n["points"] for n in c["niveaux"] if n["valeur"] == v)  # noqa: E731
    assert pts(potentiel, "high") + pts(complexite, "high") > 0
    assert "deux fois" in complexite["pourquoi_ces_points"]


def test_une_complexite_elevee_fait_baisser_la_priorite():
    rang = {"low": 0, "medium": 1, "high": 2}
    facile = g.evaluer_priorite(*opportunite(potentiel="high", faisabilite="high", complexite="low"))
    difficile = g.evaluer_priorite(*opportunite(potentiel="high", faisabilite="high", complexite="high"))
    assert rang[difficile["priority"]] < rang[facile["priority"]]


# --- QUALIFICATIONS : chaque valeur cite sa source ou vaut inconnu -------------------------------

def test_chaque_qualification_cite_sa_source_ou_vaut_inconnu():
    ids = {s["id"] for s in lire("signals.json")} | {p["id"] for p in lire("projects.json")}
    for cle, q in g.QUALIFICATIONS.items():
        for champ, valeur in q.items():
            if valeur is g.INCONNU:
                assert champ in g.CRITERES_QUALIFIES, (cle, champ)  # seuls les critères peuvent être inconnus
                continue
            sources = valeur[1:]
            assert sources and all(re.fullmatch(r"[SP]-\d{2}", s) and s in ids for s in sources), (cle, champ)


def test_les_valeurs_inconnues_sont_stockees_avec_les_codes_du_modele():
    for o in lire("opportunities.json"):
        attendus = [c for c, inconnu in (("estimated_potential", None), ("feasibility", "to_confirm"),
                                         ("complexity", "to_confirm")) if o[c] == inconnu]
        assert o["missing_criteria"] == attendus, o["id"]
