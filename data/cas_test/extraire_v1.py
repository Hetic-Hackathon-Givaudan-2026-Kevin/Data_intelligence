"""Extraction V1 par règles et mots-clés (sans LLM) + mesure sur les cas de test.

Usage : python data/cas_test/extraire_v1.py

Lit data/cas_test/sorties/interactions.csv (lignes evalue = true), détecte les 6 points
de la checklist, une note hors sujet et une contradiction de calendrier, puis compare
à verite_terrain.json. Écrit sorties/predictions_v1.json et sorties/scores_v1.json et
affiche le tableau en Markdown.

Les mots-clés sont génériques (vocabulaire commercial FR/EN) et ne reprennent pas
les phrases du générateur.
"""

import csv
import importlib.util
import json
import re
import unicodedata
from pathlib import Path

SORTIES = Path(__file__).resolve().parent / "sorties"

POINTS = [
    "client_objectives",
    "real_need",
    "technical_constraints",
    "budget_constraints",
    "timeline",
    "decision_criteria",
]

# Mots-clés et mois : ceux du compte rendu de l'app (data/demo_v2/compte_rendu.py), une seule liste.
_spec = importlib.util.spec_from_file_location("compte_rendu", Path(__file__).resolve().parents[1] / "demo_v2" / "compte_rendu.py")
_compte_rendu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_compte_rendu)
MOIS = _compte_rendu.MOIS
MOTS_CLES = _compte_rendu.MOTS_CLES

LOGISTIQUE = [r"\blivraison", r"\bdelivery\b", r"\btransporteur", r"\bcarrier\b", r"\bcolis\b",
              r"\bparcel\b", r"\bpalette\b", r"\bpallet\b", r"\bdouane\b", r"\bcustoms\b",
              r"\bexpedition\b", r"\bshipment\b", r"\bcommande \d+", r"\border \d+"]

DATE_MOIS = re.compile(rf"\b({MOIS})\s+(20\d\d)\b")
DATE_TRIMESTRE = re.compile(r"\bq([1-4])\s?(20\d\d)\b")
DATE_NUM = re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\b")


def normaliser(texte):
    t = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def trouve(motifs, texte):
    return any(re.search(m, texte) for m in motifs)


def dates_calendrier(texte):
    """Dates de calendrier distinctes (mois + année, trimestre, jj/mm/aaaa)."""
    dates = {f"{m} {a}" for m, a in DATE_MOIS.findall(texte)}
    dates |= {f"q{q} {a}" for q, a in DATE_TRIMESTRE.findall(texte)}
    dates |= {f"{j}/{m}/{a}" for j, m, a in DATE_NUM.findall(texte)}
    return sorted(dates)


def extraire(texte):
    t = normaliser(texte)
    points = [p for p in POINTS if trouve(MOTS_CLES[p], t)]
    dates = dates_calendrier(t)
    hors_sujet = not points and trouve(LOGISTIQUE, t)
    return {
        "points_detectes": points,
        "hors_sujet": hors_sujet,
        "contradiction": len(dates) >= 2,
        "dates_vues": dates,
    }


def ratio(a, b):
    return a / b if b else None


def main():
    with open(SORTIES / "interactions.csv", encoding="utf-8") as f:
        evalues = {r["interaction_id"]: r for r in csv.DictReader(f) if r["evalue"] == "true"}
    verite = json.loads((SORTIES / "verite_terrain.json").read_text(encoding="utf-8"))["cas"]

    predictions, compte = [], {p: {"vp": 0, "fp": 0, "fn": 0} for p in POINTS}
    hs_ok = hs_fp = ctr_ok = ctr_fp = 0
    for cas in verite:
        pred = extraire(evalues[cas["interaction_id"]]["compte_rendu"])
        predictions.append({"interaction_id": cas["interaction_id"], **pred})
        for p in POINTS:
            vrai, vu = p in cas["points_presents"], p in pred["points_detectes"]
            if vrai and vu:
                compte[p]["vp"] += 1
            elif vu:
                compte[p]["fp"] += 1
            elif vrai:
                compte[p]["fn"] += 1
        hs_ok += cas["hors_sujet"] and pred["hors_sujet"]
        hs_fp += (not cas["hors_sujet"]) and pred["hors_sujet"]
        ctr_ok += cas["contradiction"] and pred["contradiction"]
        ctr_fp += (not cas["contradiction"]) and pred["contradiction"]

    def scores(c):
        pr, rp = ratio(c["vp"], c["vp"] + c["fp"]), ratio(c["vp"], c["vp"] + c["fn"])
        f1 = 2 * pr * rp / (pr + rp) if pr and rp else (0.0 if pr is not None and rp is not None else None)
        return {**c, "precision": pr, "rappel": rp, "f1": f1}

    total = {k: sum(compte[p][k] for p in POINTS) for k in ("vp", "fp", "fn")}
    resultat = {
        "par_point": {p: scores(compte[p]) for p in POINTS},
        "total_micro": scores(total),
        "hors_sujet": {"detectes": hs_ok, "attendus": sum(c["hors_sujet"] for c in verite), "faux_positifs": hs_fp},
        "contradictions": {"detectees": ctr_ok, "attendues": sum(c["contradiction"] for c in verite), "faux_positifs": ctr_fp},
        "points_inventes": total["fp"],
    }
    (SORTIES / "predictions_v1.json").write_text(json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8")
    (SORTIES / "scores_v1.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")

    fmt = lambda x: "—" if x is None else f"{x:.2f}"
    print("| Point | VP | FP | FN | Précision | Rappel | F1 |")
    print("|---|---|---|---|---|---|---|")
    for p in POINTS:
        s = resultat["par_point"][p]
        print(f"| {p} | {s['vp']} | {s['fp']} | {s['fn']} | {fmt(s['precision'])} | {fmt(s['rappel'])} | {fmt(s['f1'])} |")
    s = resultat["total_micro"]
    print(f"| **Total (micro)** | {s['vp']} | {s['fp']} | {s['fn']} | {fmt(s['precision'])} | {fmt(s['rappel'])} | {fmt(s['f1'])} |")
    h, c = resultat["hors_sujet"], resultat["contradictions"]
    print()
    print(f"- Notes hors sujet détectées : {h['detectes']}/{h['attendus']} (faux positifs : {h['faux_positifs']})")
    print(f"- Contradictions de calendrier détectées : {c['detectees']}/{c['attendues']} (faux positifs : {c['faux_positifs']})")
    print(f"- Points inventés (détectés mais absents) : {resultat['points_inventes']}")


if __name__ == "__main__":
    main()
