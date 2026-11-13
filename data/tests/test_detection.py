"""Règles de détection des opportunités (DATA-US07) : data/demo_v2/regles_detection.json et detection.py.

Les clients fictifs des règles de garde (C-90…) n'existent que dans ces tests, jamais dans la démo.

Lancer : pytest data/tests/test_detection.py
"""

import importlib.util
import json
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"
CATEGORIES = {"Nouvelle gamme", "Extension de gamme", "Nouvelle formulation", "Amélioration produit",
              "Optimisation", "Nouvelle référence"}
SOURCE_TYPES = {"meeting_report", "project_history", "client_request", "market_trend",
                "commodity_price", "company_report", "regulation"}
ATTENDU = {  # les 6 opportunités de la doc v2 ; priorité (prudente) de la grille DATA-US09
    "O-01": ("C-01", "Nouvelle gamme de boissons fonctionnelles", "Nouvelle gamme", "to_qualify", "medium"),
    "O-02": ("C-01", "Extension d'une gamme aromatique", "Extension de gamme", "detected", "medium"),
    "O-03": ("C-02", "Développement d'une formulation végétale", "Nouvelle formulation", "to_qualify", "high"),
    "O-04": ("C-02", "Amélioration de la texture d'un produit", "Amélioration produit", "detected", "medium"),
    "O-05": ("C-02", "Optimisation d'une formulation existante", "Optimisation", "detected", "medium"),
    "O-06": ("C-03", "Nouvelle référence aromatique pour une marque de distributeur", "Nouvelle référence",
             "detected", "low"),
}


def charger_module(nom):
    spec = importlib.util.spec_from_file_location(nom, DOSSIER / f"{nom}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


detection = charger_module("detection")
generateur = charger_module("generer_demo_v2")
REGLES = detection.charger_regles()


def lire(nom):
    return json.loads((DOSSIER / nom).read_text(encoding="utf-8"))


# --- Fichier de règles -------------------------------------------------------------------------

def test_une_regle_par_type_d_opportunite():
    assert [r["id"] for r in REGLES] == [f"R-0{i}" for i in range(1, 7)]
    assert {r["opportunite"]["categorie"] for r in REGLES} == CATEGORIES


@pytest.mark.parametrize("regle", REGLES, ids=lambda r: r["id"])
def test_regle_complete_et_lisible(regle):
    assert regle["nom"].strip() and regle["justification_type"].strip() and regle["pourquoi_ce_statut"].strip()
    c = regle["condition"]
    assert c["types_de_signaux"] and set(c["types_de_signaux"]) <= SOURCE_TYPES
    assert c["mots_cles"] and c["nombre_min_signaux"] >= 1
    assert c["statut_du_projet_cite"] in {None, "active", "completed"}
    assert regle["statut_initial"] in {"detected", "to_qualify"}
    # to_qualify seulement si la règle part de ce que le client a exprimé lui-même
    if regle["statut_initial"] == "to_qualify":
        assert set(c["types_de_signaux"]) <= generateur.SOURCES_CLIENT
    titre = regle["opportunite"]["titre_type"]
    assert ("{theme}" in titre) == (regle["opportunite"]["theme_par_defaut"] is not None)


# --- Démo : les 6 opportunités ressortent à l'identique ------------------------------------------

def test_les_six_opportunites_de_la_demo_sont_detectees():
    opportunites = {o["id"]: o for o in lire("opportunities.json")}
    assert {i: (o["client_id"], o["title"], o["category"], o["status"], o["priority"])
            for i, o in opportunites.items()} == ATTENDU


def test_regle_et_signaux_de_chaque_opportunite():
    detectees, _ = generateur.detecter_demo(generateur.construire_signaux(
        json.loads(generateur.FICHIER_OFF.read_text(encoding="utf-8"))))
    assert {o["id"]: (o["rule_id"], o["signal_ids"]) for o in detectees} == {
        "O-01": ("R-01", ["S-01", "S-02"]),
        "O-02": ("R-02", ["S-03"]),
        "O-03": ("R-03", ["S-04", "S-05"]),
        "O-04": ("R-04", ["S-06"]),
        "O-05": ("R-05", ["S-07", "S-08"]),
        "O-06": ("R-06", ["S-10", "S-09", "S-11"]),
    }


def test_signaux_client_et_signaux_de_marche():
    opportunites = {o["id"]: o for o in lire("opportunities.json")}
    for s in lire("signals.json"):
        if s["client_id"] is None:  # signal de marché réel, propre à aucun client
            assert s["is_real_source"] and s["category"] == opportunites[s["opportunity_id"]]["category"], s["id"]
        else:
            assert s["category"] is None, s["id"]
            assert s["client_id"] == opportunites[s["opportunity_id"]]["client_id"], s["id"]


def test_chaque_opportunite_a_un_signal_client():
    clients = {s["opportunity_id"] for s in lire("signals.json") if s["client_id"]}
    assert clients == set(ATTENDU)


# --- Règles de garde, sur des clients fictifs propres aux tests ----------------------------------

def client(cid="C-90", sector="Boissons"):
    return {"id": cid, "name": f"Client de test {cid}", "sector": sector}


def signal(sid, cid="C-90", description="Le client exprime un intérêt pour une nouvelle gamme.",
           source_type="meeting_report", evidence_type="fact", category=None, source_ref=None):
    return {"id": sid, "client_id": cid, "category": category, "description": description,
            "source_type": source_type, "source_date": "2026-11-01", "confidence": "high",
            "evidence_type": evidence_type, "is_real_source": cid is None, "source_ref": source_ref}


def projet(pid, name, status="active", cid="C-90", description="Projet de test."):
    return {"id": pid, "client_id": cid, "name": name, "description": description, "status": status,
            "start_date": "2026-09-01"}


def test_client_sans_signal_aucune_opportunite():
    opportunites, _ = detection.detecter([client()], [projet("P-90", "Projet courant")], [], REGLES)
    assert opportunites == []


def test_client_sans_signal_ne_recupere_pas_les_signaux_d_un_autre():
    signaux = [signal("S-90", cid="C-91")]
    opportunites, _ = detection.detecter([client("C-90"), client("C-91")], [], signaux, REGLES)
    assert [o["client_id"] for o in opportunites] == ["C-91"]


def test_anti_doublon_une_seule_opportunite_avec_les_deux_signaux():
    signaux = [signal("S-90"), signal("S-91", description="Demande : une nouvelle gamme de boissons.",
                                      source_type="client_request")]
    opportunites, sortie = detection.detecter([client()], [], signaux, REGLES)
    assert len(opportunites) == 1
    assert opportunites[0]["category"] == "Nouvelle gamme"
    assert opportunites[0]["signal_ids"] == ["S-90", "S-91"]
    assert {s["opportunity_id"] for s in sortie} == {opportunites[0]["id"]}


def test_hypothese_seule_ne_suffit_pas():
    signaux = [signal("S-90", evidence_type="hypothesis")]
    opportunites, sortie = detection.detecter([client()], [], signaux, REGLES)
    assert opportunites == []
    assert sortie[0]["opportunity_id"] is None


def test_hypothese_accompagnee_d_un_fait_suffit():
    signaux = [signal("S-90", evidence_type="hypothesis"), signal("S-91")]
    opportunites, _ = detection.detecter([client()], [], signaux, REGLES)
    assert [o["signal_ids"] for o in opportunites] == [["S-90", "S-91"]]


def test_travail_deja_engage_ne_devient_pas_une_opportunite():
    signaux = [signal("S-90", description="Demande du client concernant des alternatives végétales.",
                      source_type="client_request")]
    deja = [projet("P-90", "Formulation végétale pour une gamme de desserts")]
    assert detection.detecter([client()], deja, signaux, REGLES)[0] == []
    # le même signal sans ce projet produit bien l'opportunité
    assert [o["title"] for o in detection.detecter([client()], [], signaux, REGLES)[0]] == [
        "Développement d'une formulation végétale"]
    # un projet terminé n'est plus un travail engagé
    termine = [projet("P-90", "Formulation végétale pour une gamme de desserts", status="completed")]
    assert len(detection.detecter([client()], termine, signaux, REGLES)[0]) == 1


def test_signal_de_marche_seul_ne_cree_pas_d_opportunite():
    marche = [signal("S-90", cid=None, source_type="market_trend", category="Nouvelle gamme",
                     source_ref="https://exemple.test")]
    opportunites, sortie = detection.detecter([client()], [], marche, REGLES)
    assert opportunites == [] and sortie[0]["opportunity_id"] is None


def test_signal_de_marche_rattache_par_categorie():
    signaux = [signal("S-90", description="Intérêt pour une nouvelle gamme de boissons fonctionnelles."),
               signal("S-91", cid=None, description="Tendance : boissons fonctionnelles en hausse.",
                      source_type="market_trend", category="Nouvelle gamme", source_ref="https://exemple.test"),
               signal("S-92", cid=None, description="Tendance : desserts végétaux.", source_type="market_trend",
                      category="Nouvelle formulation", source_ref="https://exemple.test")]
    opportunites, sortie = detection.detecter([client()], [], signaux, REGLES)
    assert [(o["title"], o["signal_ids"]) for o in opportunites] == [
        ("Nouvelle gamme de boissons fonctionnelles", ["S-90", "S-91"])]
    assert {s["id"]: s["opportunity_id"] for s in sortie} == {"S-90": "O-01", "S-91": "O-01", "S-92": None}


def test_secteur_du_client_respecte():
    signaux = [signal("S-90", description="Projet en cours pour sa marque de distributeur.",
                      source_type="project_history")]
    assert detection.detecter([client(sector="Boissons")], [], signaux, REGLES)[0] == []
    trouvees = detection.detecter([client(sector="Distribution alimentaire")], [], signaux, REGLES)[0]
    assert [o["category"] for o in trouvees] == ["Nouvelle référence"]


def test_statut_du_projet_cite_respecte():
    ref = "data/demo_v2/projects.json#P-90"
    signaux = [signal("S-90", description="Retour technique du client : texture trop épaisse.",
                      source_type="project_history", source_ref=ref)]
    actif = [projet("P-90", "Dessert", status="active")]
    termine = [projet("P-90", "Dessert", status="completed")]
    assert detection.detecter([client()], actif, signaux, REGLES)[0] == []
    assert [o["title"] for o in detection.detecter([client()], termine, signaux, REGLES)[0]] == [
        "Amélioration de la texture d'un produit"]


def test_signal_de_marche_ambigu_refuse():
    signaux = [signal("S-90", cid="C-90"), signal("S-91", cid="C-91"),
               signal("S-92", cid=None, description="Tendance générale.", source_type="market_trend",
                      category="Nouvelle gamme", source_ref="https://exemple.test")]
    with pytest.raises(ValueError, match="plusieurs opportunités"):
        detection.detecter([client("C-90"), client("C-91")], [], signaux, REGLES)
