"""Tests du moteur V1 (data/questions/moteur.py).

Lancer : pytest data/tests/test_moteur.py
"""

import importlib.util
import json
from pathlib import Path

import pytest

DOSSIER_QUESTIONS = Path(__file__).resolve().parents[1] / "questions"
BRIEF_EXEMPLE = DOSSIER_QUESTIONS / "exemples" / "brief_exemple.json"

_spec = importlib.util.spec_from_file_location("moteur", DOSSIER_QUESTIONS / "moteur.py")
moteur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(moteur)

TOUS_LES_CHAMPS = list(moteur.PRIORITE_CHAMPS)


def q(id_, champ, statut="Suggérée", opp="OPP-01"):
    """Question minimale pour une banque de test."""
    return {"id": id_, "opportunite_id": opp, "champ_brief": champ, "statut": statut,
            "question": f"Question {id_} ?", "pourquoi": "Test."}


@pytest.fixture(scope="module")
def banque():
    return moteur.charger_banque()


def ids(questions):
    return [x["id"] for x in questions]


@pytest.mark.parametrize("nb", [1, 2, 3, 5, 7])
def test_au_plus_nb_questions(nb):
    assert len(moteur.proposer_questions(TOUS_LES_CHAMPS, nb=nb)) == nb


@pytest.mark.parametrize("champs", [
    ["objectif"],
    ["marche", "profil_gout"],
    ["contraintes", "insights_concurrence", "budget_matiere_eur_par_litre"],
    TOUS_LES_CHAMPS,
])
def test_seulement_des_champs_manquants(champs):
    for nb in (1, 3, 6):
        proposees = moteur.proposer_questions(champs, nb=nb)
        assert {x["champ_brief"] for x in proposees} <= set(champs)


def test_ordre_de_priorite():
    proposees = moteur.proposer_questions(["insights_concurrence", "marche", "objectif"], nb=3)
    assert [x["champ_brief"] for x in proposees] == ["objectif", "marche", "insights_concurrence"]


def test_deuxieme_question_si_moins_de_champs_que_nb():
    proposees = moteur.proposer_questions(["objectif", "contraintes"], nb=3)
    assert [x["champ_brief"] for x in proposees] == ["objectif", "contraintes", "objectif"]


@pytest.mark.parametrize("champs,nb", [(["objectif"], 3), (["marche", "objectif"], 4), (TOUS_LES_CHAMPS, 7)])
def test_pas_de_doublon(champs, nb):
    proposees = ids(moteur.proposer_questions(champs, nb=nb))
    assert len(proposees) == len(set(proposees))


def test_questions_a_modifier_exclues():
    banque_test = [q("Q-01", "objectif", "À modifier"), q("Q-02", "objectif"), q("Q-03", "objectif", "À modifier")]
    assert ids(moteur.proposer_questions(["objectif"], nb=3, banque=banque_test)) == ["Q-02"]


def test_validee_preferee_a_suggeree():
    banque_test = [q("Q-01", "objectif"), q("Q-02", "objectif", "Validée")]
    assert ids(moteur.proposer_questions(["objectif"], nb=1, banque=banque_test)) == ["Q-02"]


def test_prefixe_brief_et_sous_champs_de_contraintes():
    sans_prefixe = moteur.proposer_questions(["objectif", "contraintes"], nb=2)
    avec_prefixe = moteur.proposer_questions(["brief.objectif", "brief.contraintes.regime"], nb=2)
    assert avec_prefixe == sans_prefixe
    assert moteur.normaliser_champ("contraintes.allergenes_exclus") == "contraintes"


def test_champ_inconnu_ignore_avec_avertissement():
    with pytest.warns(UserWarning, match="rdv.date"):
        proposees = moteur.proposer_questions(["rdv.date", "objectif"], nb=1)
    assert [x["champ_brief"] for x in proposees] == ["objectif"]


def test_preference_pour_l_opportunite(banque):
    opportunite = {x["id"]: x["opportunite_id"] for x in banque}
    sans = moteur.proposer_questions(["profil_gout"], nb=1)
    avec = moteur.proposer_questions(["profil_gout"], opportunite_id="OPP-05", nb=1)
    assert opportunite[sans[0]["id"]] != "OPP-05"  # sinon le test ne prouve rien
    assert opportunite[avec[0]["id"]] == "OPP-05"


def test_liste_vide_donne_liste_vide():
    assert moteur.proposer_questions([]) == []
    assert moteur.ids_pour_grille([]) == ""


def test_format_pour_la_grille():
    proposees = moteur.proposer_questions(["objectif", "echeance_lancement"], nb=2)
    assert moteur.ids_pour_grille(proposees) == ";".join(ids(proposees))


def test_champs_lus_depuis_le_brief_exemple():
    with open(BRIEF_EXEMPLE, encoding="utf-8") as fichier:
        brief = json.load(fichier)
    assert moteur.normaliser_champs(moteur.champs_depuis_brief(brief)) == [
        "echeance_lancement", "budget_matiere_eur_par_litre", "contraintes",
    ]


def test_opportunite_deduite_du_brief_exemple():
    with open(BRIEF_EXEMPLE, encoding="utf-8") as fichier:
        brief = json.load(fichier)
    opportunite, mots = moteur.deduire_opportunite(brief)
    assert opportunite == "OPP-06"
    assert {"boisson", "sans", "alcool"} <= set(mots)


def test_aucune_opportunite_sans_mot_reconnu():
    brief = {"brief": {"objectif": "Projet confidentiel", "marche": "France", "profil_gout": ["vanille"]}}
    assert moteur.deduire_opportunite(brief) == (None, [])


def test_champ_non_renseigne_hors_champs_manquants_est_ajoute():
    brief = {"brief": {"objectif": "non renseigné", "marche": "France", "contraintes": {"regime": "Non renseigné"}},
             "incertitudes": {"champs_manquants": ["brief.profil_gout"]}}
    assert moteur.normaliser_champs(moteur.champs_depuis_brief(brief)) == ["objectif", "contraintes", "profil_gout"]
