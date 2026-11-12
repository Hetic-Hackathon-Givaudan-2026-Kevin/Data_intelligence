"""Calcule les signaux de marché Open Food Facts des 12 opportunités -> signaux_marche.json.

Usage (venv avec duckdb), après extraire_off.py :
    python data/signaux/calculer_signaux.py D:/off/off_tags.parquet

Méthode : pour chaque opportunité, part des produits portant au moins un des tags parmi
les produits vendus en France ajoutés dans l'année (created_t) et ayant au moins une
catégorie (tags de catégories), au moins un label (tags de labels), ou les deux (règle
« catégories ET labels »).

Les produits récents ont eu moins de temps pour recevoir des catégories et labels précis
(biais de maturité, voir biais_maturite.py) : le signal affiché porte sur une période
« mûre », 2020→2022, contrôlée par 2019→2022. 2023→2025 est gardé, marqué non mûr.

Données Open Food Facts (https://world.openfoodfacts.org), licence ODbL : le fichier
produit est une base dérivée, elle aussi sous ODbL.
"""

import json
import math
import sys
from datetime import date
from pathlib import Path

import duckdb

CIBLE = Path(__file__).resolve().parent / "signaux_marche.json"
PAYS = "en:france"
ANNEES = list(range(2019, 2026))  # 2019 à 2025, dernières années complètes à la date d'extraction
MIN_PRODUITS = 50  # en dessous, une année est jugée trop petite : signal indicatif

# Périodes : (début, fin, rôle). La principale est affichée ; la robustesse doit aller dans le
# même sens ; la récente est seulement informative (non mûre).
PERIODE_PRINCIPALE = (2020, 2022)
PERIODE_ROBUSTESSE = (2019, 2022)
PERIODE_RECENTE = (2023, 2025)
PERIODES = {
    PERIODE_PRINCIPALE: "principale (affichée)",
    PERIODE_ROBUSTESSE: "robustesse",
    PERIODE_RECENTE: "récente : non mûr, indicatif",
}

# Tags validés avec l'équipe le 2026-11-12. libelle : complète « Part des nouveaux produits … ».
OPPORTUNITES = {
    "OPP-01": {"libelle": "boissons fonctionnelles",
               "categories": ["en:functional-drinks", "en:energy-drinks", "en:kombuchas", "en:sports-drinks"]},
    "OPP-02": {"libelle": "snacks bio ou équitables",
               "categories": ["en:snacks"],
               "labels": ["en:organic", "en:fair-trade", "en:rainforest-alliance"]},
    "OPP-03": {"libelle": "AOP, AOC ou Label Rouge",
               "labels": ["en:pdo", "fr:label-rouge", "fr:aoc"]},
    "OPP-04": {"libelle": "sans sucres ajoutés ou allégés en sucre",
               "labels": ["en:no-added-sugar", "en:low-or-no-sugar", "en:reduced-sugar", "en:low-sugar",
                          "en:no-sugar"]},
    "OPP-05": {"libelle": "alternatives végétales à la viande et aux laitiers",
               "categories": ["en:meat-analogues", "en:dairy-substitutes"]},
    "OPP-06": {"libelle": "bières, vins et cocktails sans alcool",
               "categories": ["en:non-alcoholic-beers", "en:non-alcoholic-wines", "en:alcohol-free-cocktails"]},
    "OPP-07": {"libelle": "allégés en sel",
               "labels": ["en:low-or-no-salt", "en:no-added-salt", "en:reduced-salt", "en:low-salt"]},
    "OPP-08": {"libelle": "sans additifs ni conservateurs",
               "labels": ["en:no-preservatives", "en:no-additives", "en:no-artificial-flavors",
                          "en:no-artificial-colors"]},
    "OPP-09": {"libelle": "de nutrition sportive",
               "categories": ["en:bodybuilding-supplements", "en:protein-bars", "en:protein-powders",
                              "en:dietary-drink-for-sport"]},
    "OPP-10": {"libelle": "kéfirs et yaourts au bifidus",
               "categories": ["en:kefir", "en:bifidus-yogurts"]},
    "OPP-11": {"sans_signal": "Pas de tag fiable : 10 produits par an au plus en France."},
    "OPP-12": {"sans_signal": "Signal propre au client (baisse des ventes d'une gamme), pas une tendance de marché."},
}


def arrondi_dizaine(valeur):
    """+101,3 -> 100 ; -24,7 -> -20 ; -1,3 -> 0 (arrondi au plus proche, symétrique)."""
    return int(math.copysign(math.floor(abs(valeur) / 10 + 0.5) * 10, valeur)) or 0


def texte_pourcentage(valeur):
    return "0 %" if valeur == 0 else f"{valeur:+d} %"


def evolution(annees, debut, fin):
    part = {a: annees[str(a)]["produits"] / annees[str(a)]["base"] for a in (debut, fin)}
    return 100 * part[fin] / part[debut] - 100 if part[debut] else float("inf")


def statut_signal(evol_principale, evol_robustesse, min_annuel):
    """compte : hausse sur les deux périodes et >= 50 produits chaque année ;
    contraire : baisse sur les deux ; indicatif : sinon (sens divergents ou trop peu de produits)."""
    if min_annuel < MIN_PRODUITS:
        return "indicatif", f"moins de {MIN_PRODUITS} produits sur une année"
    if evol_principale > 0 and evol_robustesse > 0:
        return "compte", None
    if evol_principale < 0 and evol_robustesse < 0:
        return "contraire", None
    return "indicatif", "2019→2022 et 2020→2022 divergent"


def calculer(con, config):
    categories, labels = config.get("categories", []), config.get("labels", [])
    conditions_base, conditions_tags = [], []
    if categories:
        conditions_base.append("len(categories_tags) > 0")
        conditions_tags.append("list_has_any(categories_tags, $categories)")
    if labels:
        conditions_base.append("len(labels_tags) > 0")
        conditions_tags.append("list_has_any(labels_tags, $labels)")
    lignes = con.execute(f"""
        SELECT annee, count(*) AS base,
               count(*) FILTER (WHERE {' AND '.join(conditions_tags)}) AS produits
        FROM fr
        WHERE annee IN (SELECT unnest($annees)) AND {' AND '.join(conditions_base)}
        GROUP BY annee ORDER BY annee
    """, {"annees": ANNEES, **({"categories": categories} if categories else {}),
          **({"labels": labels} if labels else {})}).fetchall()
    annees = {str(a): {"produits": p, "base": b, "part_pct": round(100 * p / b, 3)} for a, b, p in lignes}

    periodes = {}
    for (debut, fin), role in PERIODES.items():
        periodes[f"{debut}-{fin}"] = {
            "debut": debut, "fin": fin, "role": role,
            "evolution_part_pct": round(evolution(annees, debut, fin), 1),
            "produits_min_par_an": min(annees[str(a)]["produits"] for a in range(debut, fin + 1)),
        }

    evol_p = evolution(annees, *PERIODE_PRINCIPALE)
    evol_r = evolution(annees, *PERIODE_ROBUSTESSE)
    min_annuel = min(annees[str(a)]["produits"]
                     for a in range(min(PERIODE_ROBUSTESSE[0], PERIODE_PRINCIPALE[0]), PERIODE_PRINCIPALE[1] + 1))
    statut, raison = statut_signal(evol_p, evol_r, min_annuel)
    affichee = arrondi_dizaine(evol_p)
    trigger = (f"Part des nouveaux produits {config['libelle']} en France : {texte_pourcentage(affichee)} "
               f"({PERIODE_PRINCIPALE[0]}→{PERIODE_PRINCIPALE[1]}, Open Food Facts)")
    if statut == "contraire":
        trigger += " — signal contraire"
    elif statut == "indicatif":
        trigger += f" — indicatif ({raison})"

    return {
        "regle": "catégories ET labels" if categories and labels else "au moins un des tags",
        "denominateur": " et ".join(
            (["au moins une catégorie"] if categories else []) + (["au moins un label"] if labels else [])
        ),
        "annees": annees,
        "periodes": periodes,
        "produits_min_par_an_2019_2022": min_annuel,
        "statut": statut,
        "compte": statut == "compte",
        "evolution_affichee_pct": affichee,
        "trigger": trigger,
    }


def main(parquet):
    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE fr AS
        SELECT categories_tags, labels_tags, year(make_timestamp(created_t * 1000000)) AS annee
        FROM '{Path(parquet).as_posix()}'
        WHERE list_contains(countries_tags, '{PAYS}')
    """)
    dernier_ajout = con.execute(f"""
        SELECT strftime(max(make_timestamp(created_t * 1000000)), '%Y-%m-%d') FROM '{Path(parquet).as_posix()}'
    """).fetchall()[0][0]

    signaux = []
    for opp, config in OPPORTUNITES.items():
        entree = {"opportunite_id": opp,
                  "tags": {"categories": config.get("categories", []), "labels": config.get("labels", [])}}
        if "sans_signal" in config:
            entree.update({"signal": None, "raison": config["sans_signal"]})
        else:
            entree["signal"] = calculer(con, config)
        signaux.append(entree)

    sortie = {
        "version": "1.1",
        "source": {
            "nom": "Open Food Facts",
            "url": "https://world.openfoodfacts.org/data",
            "fichier": "en.openfoodfacts.org.products.csv.gz",
            "licence": "ODbL 1.0 (base de données) — https://opendatacommons.org/licenses/odbl/1-0/",
            "dernier_produit_ajoute": dernier_ajout,
        },
        "date_extraction": date.today().isoformat(),
        "pays": PAYS,
        "periodes": {f"{d}-{f}": role for (d, f), role in PERIODES.items()},
        "methode": (
            "Part des produits portant au moins un des tags parmi les produits vendus en France ajoutés "
            "dans l'année et ayant au moins une catégorie (ou un label, selon les tags). Évolution relative "
            f"de la part sur {PERIODE_PRINCIPALE[0]}→{PERIODE_PRINCIPALE[1]} (affichée, arrondie à la "
            f"dizaine) et {PERIODE_ROBUSTESSE[0]}→{PERIODE_ROBUSTESSE[1]} (robustesse). Le signal compte "
            f"si la part monte sur les deux périodes avec au moins {MIN_PRODUITS} produits chaque année ; "
            "contraire si elle baisse sur les deux ; indicatif sinon. "
            f"{PERIODE_RECENTE[0]}→{PERIODE_RECENTE[1]} est non mûr (biais de maturité), indicatif. "
            "Nombre de produits référencés ≠ ventes."
        ),
        "licence_fichier": "ODbL 1.0 : base dérivée d'Open Food Facts.",
        "signaux": signaux,
    }
    with open(CIBLE, "w", encoding="utf-8", newline="\n") as fichier:
        json.dump(sortie, fichier, ensure_ascii=False, indent=2)
        fichier.write("\n")
    print(f"{len(signaux)} opportunites -> {CIBLE.name}")  # ASCII : lisible dans toute console


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "D:/off/off_tags.parquet")
