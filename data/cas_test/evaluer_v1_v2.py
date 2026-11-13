"""Banc d'essai du compte rendu (DATA-US11) : rules_v1 contre llm_v2 sur les 30 cas de test.

Usage : python data/cas_test/evaluer_v1_v2.py [--delai 120]

Lit sorties/interactions.csv (comptes rendus evalue = true) et sorties/verite_terrain.json
(générés par generer_cas_test.py, graine 42). Pour chaque cas, extrait les éléments avec le moteur
de l'app (data/demo_v2/compte_rendu.py) en rules_v1 puis en llm_v2 (qwen2.5:3b via Ollama local,
délai maximum par cas), et mesure :
- rappel et précision par rubrique (besoins, contraintes techniques, contraintes budgétaires,
  calendrier, informations manquantes), au niveau (cas, point de la checklist) ;
- éléments inventés : texte introuvable dans les notes (avant garde-fou pour llm_v2, et dans la
  sortie finale) et éléments sur un point absent de la vérité terrain ;
- justesse confirmed / to_verify sur les points bien trouvés (attendu : to_verify pour le
  calendrier des cas à contradiction, confirmed sinon) ;
- retours à rules_v1, dépassements du délai, temps moyen par cas.
Écrit resultats_v1_v2.json et resultats_v1_v2.md dans data/cas_test/.
"""

import argparse
import csv
import importlib.util
import json
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
SORTIES = ICI / "sorties"
_spec = importlib.util.spec_from_file_location("compte_rendu", ICI.parent / "demo_v2" / "compte_rendu.py")
cr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cr)

RUBRIQUES = {"needs": ["client_objectives", "real_need", "decision_criteria"],
             "technical_constraints": ["technical_constraints"], "budget_constraints": ["budget_constraints"],
             "timeline": ["timeline"]}
LIBELLES = {"needs": "Besoins (objectifs, besoin réel, critères)", "technical_constraints": "Contraintes techniques",
            "budget_constraints": "Contraintes budgétaires", "timeline": "Calendrier",
            "missing_information": "Informations manquantes", "total": "Total (rubriques extraites)"}


def charger_cas():
    with open(SORTIES / "interactions.csv", encoding="utf-8") as f:
        notes = {r["interaction_id"]: r["compte_rendu"] for r in csv.DictReader(f) if r["evalue"] == "true"}
    verite = json.loads((SORTIES / "verite_terrain.json").read_text(encoding="utf-8"))
    return [{**c, "notes": notes[c["interaction_id"]]} for c in verite["cas"]], verite["graine"]


def statut_attendu(cas, point):
    return "to_verify" if cas["contradiction"] and point == "timeline" else "confirmed"


def resume_points(elements):
    """{point: statut} : to_verify si un des éléments du point l'est."""
    statuts = {}
    for e in elements:
        statuts[e["point"]] = "to_verify" if "to_verify" in (statuts.get(e["point"]), e["status"]) else e["status"]
    return statuts


def lancer(cas, mode, delai):
    brut = {}

    def appel(notes, **options):
        brut["texte"] = cr.appeler_ollama(notes, timeout=delai)
        return brut["texte"]

    debut = time.perf_counter()
    elements, engine = cr.extraire(cas["notes"], mode, appel=appel if mode == "llm_v2" else None, timeout=delai)
    duree = time.perf_counter() - debut
    return {"elements": elements, "engine": engine, "secondes": round(duree, 2), "sortie_brute": brut.get("texte")}


def ratio(a, b):
    return round(a / b, 3) if b else None


def mesurer(cas_liste, resultats):
    compte = {r: {"vp": 0, "fp": 0, "fn": 0} for r in [*RUBRIQUES, "missing_information"]}
    statut_ok = statut_total = hors_point = introuvables = total_elements = 0
    hors_sujet_avec_elements = 0
    for cas, res in zip(cas_liste, resultats):
        points = resume_points(res["elements"])
        vrais = set(cas["points_presents"])
        for rub, pts in RUBRIQUES.items():
            for p in pts:
                if p in vrais and p in points:
                    compte[rub]["vp"] += 1
                    statut_total += 1
                    statut_ok += points[p] == statut_attendu(cas, p)
                elif p in points:
                    compte[rub]["fp"] += 1
                elif p in vrais:
                    compte[rub]["fn"] += 1
        for p in cr.POINTS:  # informations manquantes : point absent des éléments
            vu_manquant, vrai_manquant = p not in points, p not in vrais
            cle = "vp" if vu_manquant and vrai_manquant else "fp" if vu_manquant else "fn" if vrai_manquant else None
            if cle:
                compte["missing_information"][cle] += 1
        total_elements += len(res["elements"])
        hors_point += sum(e["point"] not in vrais for e in res["elements"])
        introuvables += sum(not cr.present_dans(e["excerpt"], [cas["notes"]]) for e in res["elements"])
        hors_sujet_avec_elements += cas["hors_sujet"] and bool(res["elements"])

    par_rubrique = {}
    for rub, c in compte.items():
        par_rubrique[rub] = {**c, "precision": ratio(c["vp"], c["vp"] + c["fp"]), "rappel": ratio(c["vp"], c["vp"] + c["fn"])}
    tot = {k: sum(compte[r][k] for r in RUBRIQUES) for k in ("vp", "fp", "fn")}
    par_rubrique["total"] = {**tot, "precision": ratio(tot["vp"], tot["vp"] + tot["fp"]),
                             "rappel": ratio(tot["vp"], tot["vp"] + tot["fn"])}
    gardes = [r["engine"]["guard"] for r in resultats if r["engine"]["guard"]]
    brut_total = sum(sum(g.values()) for g in gardes)
    return {
        "par_rubrique": par_rubrique,
        "elements": total_elements,
        "inventes_texte_sortie": introuvables,
        "taux_inventes_texte_sortie": ratio(introuvables, total_elements),
        "elements_point_absent": hors_point,
        "taux_elements_point_absent": ratio(hors_point, total_elements),
        "garde_fou": {"elements_bruts": brut_total,
                      "gardes": sum(g["kept"] for g in gardes),
                      "passes_to_verify": sum(g["downgraded"] for g in gardes),
                      "ecartes_introuvables": sum(g["dropped"] for g in gardes),
                      "taux_inventes_texte_brut": ratio(sum(g["dropped"] for g in gardes), brut_total)} if gardes else None,
        "justesse_statut": {"justes": statut_ok, "evalues": statut_total, "taux": ratio(statut_ok, statut_total)},
        "hors_sujet_avec_elements": hors_sujet_avec_elements,
        "retours_rules_v1": sum(r["engine"]["requested"] != r["engine"]["used"] for r in resultats),
        "depassements_delai": sum("délai" in (r["engine"]["fallback_reason"] or "") for r in resultats),
        "temps_moyen_s": round(sum(r["secondes"] for r in resultats) / len(resultats), 2),
        "temps_max_s": max(r["secondes"] for r in resultats),
    }


def fmt(x):
    return "—" if x is None else f"{x:.2f}"


def ecrire_md(res, chemin):
    v1, v2, p = res["rules_v1"], res["llm_v2"], res["protocole"]
    lignes = [
        "# Banc d'essai du compte rendu : rules_v1 contre llm_v2",
        "",
        f"Ticket DATA-US11. Généré par `python data/cas_test/evaluer_v1_v2.py` le {p['date']}.",
        "",
        "## Protocole",
        "",
        f"- **Cas** : les {p['cas']} comptes rendus évalués de `sorties/interactions.csv`, produits par "
        f"`generer_cas_test.py` (graine {p['graine']}, date de référence 2026-11-12) : 10 complets, 10 partiels, "
        "5 avec deux dates de calendrier contradictoires, 5 hors sujet. Moitié français, moitié anglais. Fictifs.",
        "- **Vérité terrain** : `sorties/verite_terrain.json`, points de la checklist présents ou manquants par cas.",
        "- **Moteurs** : ceux de l'app, `data/demo_v2/compte_rendu.py`. rules_v1 : mots-clés phrase par phrase. "
        f"llm_v2 : {p['modele']} via Ollama local ({p['ollama_url']}), température 0, graine 42, JSON contraint par "
        f"schéma, puis garde-fou. Délai maximum : {p['delai_s']} s par cas ; au-delà, retour à rules_v1 compté comme "
        "dépassement.",
        "- **Rubriques** : précision et rappel au niveau (cas, point). Besoins = objectifs, besoin réel, critères "
        "de décision. Informations manquantes = points absents des éléments, comparés aux points manquants de la "
        "vérité terrain.",
        "- **Éléments inventés** : extrait introuvable dans les notes (avant garde-fou pour llm_v2, et en sortie) ; "
        "et, à part, éléments attribués à un point absent de la vérité terrain.",
        "- **Justesse confirmed / to_verify** : sur les points bien trouvés ; attendu to_verify pour le calendrier des "
        "5 cas à contradiction, confirmed ailleurs (les cas ne contiennent pas d'autre hésitation).",
        f"- **Machine** : {p['machine']}.",
        "",
        "## Résultats",
        "",
        "| Rubrique | Précision V1 | Rappel V1 | Précision V2 | Rappel V2 |",
        "|---|---|---|---|---|",
    ]
    for rub in [*RUBRIQUES, "missing_information", "total"]:
        a, b = v1["par_rubrique"][rub], v2["par_rubrique"][rub]
        lignes.append(f"| {LIBELLES[rub]} | {fmt(a['precision'])} | {fmt(a['rappel'])} | {fmt(b['precision'])} | "
                      f"{fmt(b['rappel'])} |")
    g = v2["garde_fou"] or {}
    lignes += [
        "",
        "| Indicateur | rules_v1 | llm_v2 |",
        "|---|---|---|",
        f"| Éléments produits (après garde-fou) | {v1['elements']} | {v2['elements']} |",
        f"| Extraits inventés avant garde-fou (introuvables dans les notes) | 0 | "
        f"{g.get('ecartes_introuvables', '—')} / {g.get('elements_bruts', '—')} ({fmt(g.get('taux_inventes_texte_brut'))}) |",
        f"| Passés en to_verify par le garde-fou (retrouvés en partie) | — | {g.get('passes_to_verify', '—')} |",
        f"| Extraits inventés dans la sortie finale | {v1['inventes_texte_sortie']} | {v2['inventes_texte_sortie']} |",
        f"| Éléments sur un point absent de la vérité terrain | {v1['elements_point_absent']} "
        f"({fmt(v1['taux_elements_point_absent'])}) | {v2['elements_point_absent']} ({fmt(v2['taux_elements_point_absent'])}) |",
        f"| Notes hors sujet avec au moins un élément (sur 5) | {v1['hors_sujet_avec_elements']} | "
        f"{v2['hors_sujet_avec_elements']} |",
        f"| Justesse confirmed / to_verify | {v1['justesse_statut']['justes']}/{v1['justesse_statut']['evalues']} "
        f"({fmt(v1['justesse_statut']['taux'])}) | {v2['justesse_statut']['justes']}/{v2['justesse_statut']['evalues']} "
        f"({fmt(v2['justesse_statut']['taux'])}) |",
        f"| Retours à rules_v1 | — | {v2['retours_rules_v1']} |",
        f"| dont dépassements du délai ({p['delai_s']} s) | — | {v2['depassements_delai']} |",
        f"| Temps moyen par cas | {v1['temps_moyen_s']} s | {v2['temps_moyen_s']} s (max {v2['temps_max_s']} s) |",
        "",
        "Les cas qui retombent sur rules_v1 sont comptés avec la sortie de rules_v1 dans les métriques de llm_v2 : "
        "c'est ce que verrait l'utilisateur.",
        "",
        "## Limites",
        "",
        "- **Cas synthétiques** : les comptes rendus sont produits par un générateur à phrases types. Les mots-clés de "
        "rules_v1 sont génériques mais ce vocabulaire leur est favorable ; de vraies notes (abréviations, fautes, "
        "phrases longues mêlant plusieurs points) seraient plus dures pour rules_v1.",
        "- **30 cas seulement** : un écart de 1 ou 2 éléments change les taux de plusieurs points.",
        "- **Statut** : la vérité terrain ne porte un to_verify que sur le calendrier contradictoire ; l'hésitation "
        "(« peut-être », « à confirmer ») n'est pas présente dans les cas et n'est donc pas mesurée ici.",
        "- **Prochaines actions et équipes** : déduites par les mêmes règles dans les deux modes à partir des éléments "
        "extraits ; elles n'ont pas de vérité terrain et ne sont pas évaluées.",
        "- **Prompt** : écrit une fois, de façon générique, sans réglage sur ces 30 cas.",
        "- **Reproductibilité** : température 0 et graine fixe, mais un LLM sur CPU peut varier légèrement d'une "
        "machine à l'autre ; les temps dépendent de la machine.",
        f"- **Notes hors sujet en llm_v2** : sur {v2['hors_sujet_avec_elements']} des 5 notes hors sujet (suivi de "
        "livraison), le modèle colle le même extrait sur tous les points de la checklist, en `confirmed`. Le "
        "garde-fou ne le détecte pas : l'extrait existe bien dans les notes, c'est son attribution aux points qui "
        "est fausse.",
        "",
        "## Prochaine étape",
        "",
        "- Règle de garde-fou à tester : **un même extrait attribué à plus de 2 points passe en `to_verify`**. Elle "
        "devra être évaluée sur de nouveaux cas, pas sur ces 30 : régler le moteur sur le banc qui sert à "
        "l'évaluer fausserait la mesure.",
        "",
        "## Conclusion",
        "",
        "- **rules_v1 reste le mode par défaut.**",
        f"- **llm_v2 est une option expérimentale** : {v2['temps_moyen_s']:.0f} s par cas en moyenne sur ce poste, "
        "des erreurs d'attribution (éléments rangés sous un mauvais point, notes hors sujet remplies), et des "
        "résultats plus faibles sur les notes en anglais.",
        "- Le sans-faute de rules_v1 vient en partie du vocabulaire du générateur de cas. Une comparaison honnête "
        "demandera des notes rédigées par des humains.",
        "",
    ]
    chemin.write_text("\n".join(lignes), encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delai", type=float, default=120, help="délai maximum par cas pour llm_v2 (secondes)")
    parser.add_argument("--machine", default="poste local, CPU, Ollama Windows")
    parser.add_argument("--md-seulement", action="store_true",
                        help="réécrit resultats_v1_v2.md à partir de resultats_v1_v2.json, sans relancer les moteurs")
    args = parser.parse_args()
    if args.md_seulement:
        ecrire_md(json.loads((ICI / "resultats_v1_v2.json").read_text(encoding="utf-8")), ICI / "resultats_v1_v2.md")
        print((ICI / "resultats_v1_v2.md").read_text(encoding="utf-8"))
        return
    cas_liste, graine = charger_cas()
    res = {"protocole": {"date": time.strftime("%Y-%m-%d"), "cas": len(cas_liste), "graine": graine,
                         "modele": cr.OLLAMA_MODEL, "ollama_url": cr.OLLAMA_URL, "delai_s": args.delai,
                         "machine": args.machine}}
    par_cas = {"rules_v1": [], "llm_v2": []}
    for mode in ("rules_v1", "llm_v2"):
        for i, cas in enumerate(cas_liste, 1):
            r = lancer(cas, mode, args.delai)
            par_cas[mode].append(r)
            print(f"{mode} {i:02d}/{len(cas_liste)} {cas['client_id']} {r['secondes']} s "
                  f"{r['engine']['used']} {r['engine']['fallback_reason'] or ''}", flush=True)
        res[mode] = mesurer(cas_liste, par_cas[mode])
    res["par_cas"] = [{"client_id": c["client_id"], "scenario": c["scenario"], "langue": c["langue"],
                       "points_presents": c["points_presents"],
                       **{m: {"points": resume_points(par_cas[m][i]["elements"]), "engine": par_cas[m][i]["engine"],
                              "secondes": par_cas[m][i]["secondes"]} for m in par_cas},
                       "llm_v2_sortie_brute": par_cas["llm_v2"][i]["sortie_brute"]}
                      for i, c in enumerate(cas_liste)]
    (ICI / "resultats_v1_v2.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ecrire_md(res, ICI / "resultats_v1_v2.md")
    print((ICI / "resultats_v1_v2.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
