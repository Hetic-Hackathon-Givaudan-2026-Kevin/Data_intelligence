"""Contrôle d'ensemble du jeu de démo v2 (DATA-US12) : data/verifier_jeu.py.

Le script est lancé tel quel (code de retour 0, 7 contrôles OK), puis chaque contrôle est
vérifié sur une copie du jeu volontairement cassée : il doit passer KO.

Lancer : pytest data/tests/test_verifier_jeu.py
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1]
SCRIPT = DATA / "verifier_jeu.py"

spec = importlib.util.spec_from_file_location("verifier_jeu", SCRIPT)
vj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vj)


def test_script_tout_ok_code_retour_zero():
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.count("OK  ") == 7 and "KO" not in r.stdout
    assert "7/7 contrôles OK" in r.stdout


def test_enums_lues_dans_la_doc():
    s = vj.sections_doc((DATA / "demo_v2" / "MODELE_DONNEES.md").read_text(encoding="utf-8"))
    assert vj.valeurs_enum(s, "Opportunity", "complexity") == {"low", "medium", "high", "to_confirm"}
    assert vj.valeurs_enum(s, "Opportunity", "estimated_potential") == {"low", "medium", "high", None}
    assert vj.valeurs_enum(s, "MeetingReport", "status") == {"confirmed", "to_verify"}
    assert len(vj.valeurs_enum(s, "Signal", "source_type")) == 7


def modifier(fichier, fonction):
    def appliquer(dossier):
        chemin = dossier / f"{fichier}.json"
        d = json.loads(chemin.read_text(encoding="utf-8"))
        fonction(d)
        chemin.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return appliquer


def _set(cle, valeur, i=0):
    return lambda d: d[i].__setitem__(cle, valeur)


CASSES = {
    "ids uniques": modifier("projects", lambda d: d[1].__setitem__("id", d[0]["id"])),
    "clés étrangères valides": modifier("meetings", _set("opportunity_id", "O-99")),
    "valeurs d'enum conformes à MODELE_DONNEES.md": modifier("opportunities", _set("complexity", "unknown")),
    "aucun compteur stocké": modifier("clients", _set("active_projects", 2)),
    "aucune adresse e-mail ni numéro de téléphone": modifier(
        "clients", _set("history_summary", "Contact : acheteur@exemple.fr, 06 12 34 56 78.")),
    "aucun montant en euros dans les opportunités": modifier("opportunities", _set("next_action", "Viser 50 000 €.")),
    "chaque source réelle citée avec sa licence": modifier(
        "signals", lambda d: next(s for s in d if s["is_real_source"]).__setitem__("source_ref", "https://exemple.org")),
}


@pytest.mark.parametrize("controle", CASSES)
def test_chaque_controle_detecte_une_casse(controle, tmp_path):
    copie = tmp_path / "demo_v2"
    shutil.copytree(DATA / "demo_v2", copie, ignore=shutil.ignore_patterns("__pycache__"))
    CASSES[controle](copie)
    resultats = dict(vj.controles(copie))
    assert resultats[controle], f"{controle} aurait dû passer KO"
    assert all(not pb for nom, pb in resultats.items() if nom != controle), resultats


def test_montant_et_telephone_sans_faux_positif():
    assert not vj.MONTANT.findall("indice INSEE du sucre importé, en euros, +15 % sur un an")
    assert not vj.TELEPHONE.findall("https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/010002028 ; 2026-11-12")
