"""Cohérence entre data/demo_v2/MODELE_DONNEES.md et les fichiers JSON de data/demo_v2/ (DATA-US02).

Lancer : pytest data/tests/test_modele_donnees.py
"""

import json
import re
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parents[1] / "demo_v2"
FICHIERS = {"Client": "clients.json", "Project": "projects.json", "Opportunity": "opportunities.json",
            "Signal": "signals.json", "Meeting": "meetings.json"}
ENTITES = list(FICHIERS) + ["MeetingReport"]


def lire_modele():
    """{entité: {champ: obligatoire (bool)}} à partir des tableaux « Champ | Type | Obligatoire »."""
    texte = (DOSSIER / "MODELE_DONNEES.md").read_text(encoding="utf-8")
    modele, entite, dans_tableau = {}, None, False
    for ligne in texte.splitlines():
        titre = re.match(r"^### (\w+)\s*$", ligne)
        if titre:
            entite, dans_tableau = titre.group(1), False
            modele.setdefault(entite, {})
            continue
        if ligne.startswith("## "):
            entite = None
        if entite and ligne.startswith("| Champ | Type | Obligatoire"):
            dans_tableau = True
            continue
        if entite and dans_tableau:
            cellules = [c.strip() for c in ligne.strip().strip("|").split("|")]
            champ = re.fullmatch(r"`(\w+)`", cellules[0]) if cellules else None
            if champ:
                modele[entite][champ.group(1)] = cellules[2].startswith("oui")
            elif not ligne.startswith("|"):
                dans_tableau = False
    return modele


@pytest.fixture(scope="module")
def modele():
    return lire_modele()


def test_toutes_les_entites_documentees(modele):
    for entite in ENTITES:
        assert modele.get(entite), entite


@pytest.mark.parametrize("entite", list(FICHIERS))
def test_champs_des_fichiers_documentes_et_obligatoires_presents(modele, entite):
    chemin = DOSSIER / FICHIERS[entite]
    if not chemin.exists():
        pytest.skip(f"{FICHIERS[entite]} pas encore créé")
    objets = json.loads(chemin.read_text(encoding="utf-8"))
    documentes = modele[entite]
    obligatoires = {c for c, oui in documentes.items() if oui}
    for objet in objets:
        assert set(objet) <= set(documentes), (entite, set(objet) - set(documentes))
        assert obligatoires <= set(objet), (entite, objet.get("id"), obligatoires - set(objet))


def test_meeting_suit_la_section_8(modele):
    section_8 = {"id", "client_id", "opportunity_id", "objective", "questions", "answers", "notes", "summary",
                 "next_actions"}
    assert section_8 | {"date", "status", "collected_points"} == set(modele["Meeting"])


def test_meeting_report_sans_prochaines_actions(modele):
    rapport = set(modele["MeetingReport"])
    assert {"generated_by", "validated", "missing_information", "internal_teams"} <= rapport
    assert not any("action" in champ for champ in rapport)  # elles restent dans Meeting.next_actions


def test_valeurs_fermees_du_compte_rendu():
    texte = (DOSSIER / "MODELE_DONNEES.md").read_text(encoding="utf-8")
    ligne = {m.group(1): m.group(0) for m in re.finditer(r"^\| `(\w+)` \|.*$", texte, re.M)}
    assert all(f"`{v}`" in ligne["opportunity_decision"] for v in ("confirmed", "to_qualify", "discarded"))
    assert all(f"`{v}`" in ligne["internal_teams"] for v in ("application", "creation", "marketing", "regulatory"))
    assert "`{information_sought, answer}`" in ligne["answers"]


def test_schema_mermaid_present():
    texte = (DOSSIER / "MODELE_DONNEES.md").read_text(encoding="utf-8")
    bloc = re.search(r"```mermaid\n(.*?)```", texte, re.S)
    assert bloc and bloc.group(1).startswith("erDiagram")
    for entite in ("CLIENT", "PROJECT", "OPPORTUNITY", "SIGNAL", "MEETING", "MEETING_REPORT"):
        assert re.search(rf"^\s+{entite} \{{", bloc.group(1), re.M), entite
