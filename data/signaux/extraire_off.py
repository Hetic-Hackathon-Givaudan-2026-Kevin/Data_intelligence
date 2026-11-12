"""Lit une seule fois l'export CSV Open Food Facts et garde les colonnes utiles en Parquet.

Usage (venv avec duckdb) :
    python data/signaux/extraire_off.py D:/en.openfoodfacts.org.products.csv.gz D:/off/off_tags.parquet

Le CSV (plusieurs Go) et le Parquet restent hors du repo. Colonnes gardées :
code, created_t (date d'ajout), countries_tags, categories_tags, labels_tags
(les tags sont stockés en listes). Données Open Food Facts : licence ODbL.
"""

import sys
import time
from pathlib import Path

import duckdb


def extraire(source, cible):
    cible = Path(cible)
    cible.parent.mkdir(parents=True, exist_ok=True)
    debut = time.time()
    con = duckdb.connect()
    # Séparateur tabulation, pas de guillemets (le texte libre en contient), lignes mal formées ignorées.
    con.execute(f"""
        COPY (
            SELECT
                code,
                TRY_CAST(created_t AS BIGINT) AS created_t,
                string_split(NULLIF(countries_tags, ''), ',')  AS countries_tags,
                string_split(NULLIF(categories_tags, ''), ',') AS categories_tags,
                string_split(NULLIF(labels_tags, ''), ',')     AS labels_tags
            FROM read_csv('{Path(source).as_posix()}',
                delim='\t', quote='', escape='', header=true, all_varchar=true,
                ignore_errors=true, max_line_size=10000000)
        ) TO '{cible.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    lignes = con.execute(f"SELECT count(*) FROM '{cible.as_posix()}'").fetchone()[0]
    print(f"{lignes} produits -> {cible} ({cible.stat().st_size / 1e6:.0f} Mo) en {time.time() - debut:.0f} s")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    extraire(sys.argv[1], sys.argv[2])
