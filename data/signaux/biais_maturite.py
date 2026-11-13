"""Preuve du biais de maturité des signaux Open Food Facts (analyse, n'écrit rien dans le repo).

Les produits ajoutés récemment ont eu moins de temps pour recevoir des catégories et des
labels précis : leurs parts sont sous-estimées. Ce script compare 4 calculs de la même part.

Usage (venv avec duckdb) :
    # une fois : colonnes d'état et de complétude, hors repo (relit le CSV, ~40 s)
    python data/signaux/biais_maturite.py --extraire-etats D:/en.openfoodfacts.org.products.csv.gz D:/off/off_etats.parquet
    # analyse
    python data/signaux/biais_maturite.py D:/off/off_tags.parquet D:/off/off_etats.parquet

Données Open Food Facts, licence ODbL.
"""

import importlib.util
import sys
from pathlib import Path

import duckdb

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("calculer_signaux", ICI / "calculer_signaux.py")
cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cs)  # tags validés : cs.OPPORTUNITES

SCENARIOS = [
    ("A. 2023→2025 (non mûr)", 2023, 2025, "TRUE"),
    ("B. 2019→2022 (tous > 3 ans)", 2019, 2022, "TRUE"),
    ("C. 2020→2022 (même écart de 2 ans)", 2020, 2022, "TRUE"),
    ("D. 2023→2025, completeness ≥ 0,8", 2023, 2025, "k >= 0.8"),
]


def extraire_etats(csv, cible):
    duckdb.execute(f"""
        COPY (
            SELECT code, TRY_CAST(created_t AS BIGINT) AS created_t,
                   string_split(NULLIF(states_tags, ''), ',') AS states_tags,
                   TRY_CAST(completeness AS DOUBLE) AS completeness
            FROM read_csv('{Path(csv).as_posix()}', delim='\t', quote='', escape='', header=true,
                          all_varchar=true, ignore_errors=true, max_line_size=10000000)
        ) TO '{Path(cible).as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)


def charger(con, tags, etats):
    con.execute(f"""
        CREATE TABLE fr AS
        SELECT o.categories_tags AS categories_tags, o.labels_tags AS labels_tags,
               year(make_timestamp(o.created_t * 1000000)) AS annee, e.completeness AS k
        FROM '{Path(tags).as_posix()}' o
        JOIN (SELECT DISTINCT ON (code, created_t) * FROM '{Path(etats).as_posix()}') e USING (code, created_t)
        WHERE list_contains(o.countries_tags, '{cs.PAYS}')
    """)


def profondeur(con):
    """Nombre moyen de catégories et de labels par produit (qui en a), selon l'année d'ajout."""
    return con.execute("""
        SELECT annee, round(avg(len(categories_tags)) FILTER (len(categories_tags) > 0), 1),
               round(avg(len(labels_tags)) FILTER (len(labels_tags) > 0), 1)
        FROM fr WHERE annee BETWEEN 2017 AND 2025 GROUP BY 1 ORDER BY 1""").fetchall()


def parts(con, config, a0, a1, filtre="TRUE"):
    cats, labs = config.get("categories", []), config.get("labels", [])
    base, tags = [filtre], []
    if cats:
        base.append("len(categories_tags) > 0")
        tags.append("list_has_any(categories_tags, $c)")
    if labs:
        base.append("len(labels_tags) > 0")
        tags.append("list_has_any(labels_tags, $l)")
    params = {"a0": a0, "a1": a1, **({"c": cats} if cats else {}), **({"l": labs} if labs else {})}
    r = {a: (b, p) for a, b, p in con.execute(f"""
        SELECT annee, count(*), count(*) FILTER (WHERE {' AND '.join(tags)})
        FROM fr WHERE annee IN ($a0, $a1) AND {' AND '.join(base)} GROUP BY 1""", params).fetchall()}
    (b0, p0), (b1, p1) = r[a0], r[a1]
    evol = 100 * (p1 / b1) / (p0 / b0) - 100 if p0 else float("nan")
    return p0, p1, 100 * p0 / b0, 100 * p1 / b1, evol


def main(tags, etats):
    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect()
    charger(con, tags, etats)
    print("Nombre moyen de tags par produit, selon l'année d'ajout (France)")
    for annee, nb_cat, nb_lab in profondeur(con):
        print(f"  {annee} : {nb_cat} catégories, {nb_lab} labels")

    opportunites = {o: c for o, c in cs.OPPORTUNITES.items() if "sans_signal" not in c}
    resultats = {o: [parts(con, c, a0, a1, f) for _, a0, a1, f in SCENARIOS] for o, c in opportunites.items()}
    for i, (nom, a0, a1, _) in enumerate(SCENARIOS):
        print(f"\n{nom}")
        for opp, rs in resultats.items():
            p0, p1, q0, q1, e = rs[i]
            print(f"  {opp} {a0}: {p0:5d} ({q0:5.2f} %)  {a1}: {p1:5d} ({q1:5.2f} %)  évol {e:+6.1f} %")
        print(f"  -> {sum(rs[i][4] > 0 for rs in resultats.values())} hausses sur {len(resultats)}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--extraire-etats":
        extraire_etats(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
