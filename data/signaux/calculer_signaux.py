"""Calcule les signaux de marché Open Food Facts des 12 opportunités -> signaux_marche.json.

Usage (venv avec duckdb), après extraire_off.py :
    python data/signaux/calculer_signaux.py D:/off/off_tags.parquet

Méthode : pour chaque opportunité, part des produits portant au moins un des tags parmi
les produits vendus en France ajoutés dans l'année (created_t) et ayant au moins une
catégorie (tags de catégories), au moins un label (tags de labels), ou les deux (règle
« catégories ET labels »). Évolution relative de cette part entre 2023 et 2025.

Données Open Food Facts (https://world.openfoodfacts.org), licence ODbL : le fichier
produit est une base dérivée, elle aussi sous ODbL.
"""

import json
import sys
from datetime import date
from pathlib import Path

import duckdb

CIBLE = Path(__file__).resolve().parent / "signaux_marche.json"
PAYS = "en:france"
ANNEES = [2023, 2024, 2025]  # 3 dernières années complètes à la date d'extraction
MIN_PRODUITS = 50  # en dessous, une année est jugée trop petite : signal indicatif

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


def libelle_trigger(libelle, evolution, compte, min_annuel):
    texte = (f"Part des nouveaux produits {libelle} en France : {evolution:+.0f} % "
             f"({ANNEES[0]}→{ANNEES[-1]}, Open Food Facts)")
    if min_annuel < MIN_PRODUITS:
        texte += f" — indicatif, moins de {MIN_PRODUITS} produits sur une année"
    elif not compte:
        texte += " — signal contraire"
    return texte


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
    debut, fin = annees[str(ANNEES[0])], annees[str(ANNEES[-1])]
    evolution = 100 * (fin["produits"] / fin["base"]) / (debut["produits"] / debut["base"]) - 100
    min_annuel = min(v["produits"] for v in annees.values())
    compte = evolution > 0 and min_annuel >= MIN_PRODUITS
    return {
        "regle": "catégories ET labels" if categories and labels else "au moins un des tags",
        "denominateur": " et ".join(
            (["au moins une catégorie"] if categories else []) + (["au moins un label"] if labels else [])
        ),
        "annees": annees,
        "evolution_part_pct": round(evolution, 1),
        "produits_min_par_an": min_annuel,
        "compte": compte,
        "trigger": libelle_trigger(config["libelle"], evolution, compte, min_annuel),
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
        "version": "1.0",
        "source": {
            "nom": "Open Food Facts",
            "url": "https://world.openfoodfacts.org/data",
            "fichier": "en.openfoodfacts.org.products.csv.gz",
            "licence": "ODbL 1.0 (base de données) — https://opendatacommons.org/licenses/odbl/1-0/",
            "dernier_produit_ajoute": dernier_ajout,
        },
        "date_extraction": date.today().isoformat(),
        "pays": PAYS,
        "periode": {"debut": ANNEES[0], "fin": ANNEES[-1]},
        "methode": (
            "Part des produits portant au moins un des tags parmi les produits vendus en France ajoutés "
            "dans l'année et ayant au moins une catégorie (ou un label, selon les tags). Évolution relative "
            f"de la part entre {ANNEES[0]} et {ANNEES[-1]}. Le signal compte s'il augmente et s'il y a au "
            f"moins {MIN_PRODUITS} produits chaque année. Nombre de produits référencés ≠ ventes."
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
