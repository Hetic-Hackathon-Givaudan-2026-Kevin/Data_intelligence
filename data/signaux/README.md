# Signaux de marché (Open Food Facts)

Remplacent les signaux « croissance du marché » inventés du jeu de démo par des
chiffres calculés sur Open Food Facts.

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `extraire_off.py` | Lit une seule fois l'export CSV Open Food Facts (`.csv.gz`, tabulation) avec DuckDB et garde 5 colonnes dans un Parquet hors du repo : `code`, `created_t`, `countries_tags`, `categories_tags`, `labels_tags`. |
| `calculer_signaux.py` | Calcule les signaux des 12 opportunités à partir du Parquet et écrit `signaux_marche.json`. |
| `signaux_marche.json` | Pour chaque opportunité : tags, chiffres par année, évolution, règle de comptage, texte du trigger, source et date d'extraction. |

## Méthode

- Produits vendus en France (`countries_tags` contient `en:france`), par année
  d'ajout dans Open Food Facts (`created_t`), sur les 3 dernières années
  complètes : 2023, 2024, 2025.
- Pour chaque opportunité : part des produits portant au moins un des tags
  validés, parmi les ajouts de l'année qui ont au moins une catégorie (tags de
  catégories), au moins un label (tags de labels), ou les deux (OPP-02 :
  catégorie `en:snacks` ET un label bio ou équitable).
- Évolution relative de la part entre 2023 et 2025. Les chiffres bruts restent
  dans le JSON.
- Le signal **compte** pour la priorité si la part augmente et s'il y a au
  moins 50 produits chaque année. Sinon il est affiché comme « signal
  contraire » ou « indicatif », sans compter.
- OPP-11 et OPP-12 n'ont pas de signal (pas de tag fiable / signal propre au
  client).

## Régénérer

Le CSV (environ 1,5 Go compressé) et le Parquet restent hors du repo. Dans un
venv avec `duckdb` :

```bash
python data/signaux/extraire_off.py D:/en.openfoodfacts.org.products.csv.gz D:/off/off_tags.parquet
python data/signaux/calculer_signaux.py D:/off/off_tags.parquet
python data/demo/generer_demo.py
pytest data/tests/
```

`calculer_signaux.py` met la date du jour dans `date_extraction`.

## Limites

- **Nombre de produits référencés ≠ ventes.** Une part qui monte dit que plus
  de nouveaux produits de ce type sont saisis dans Open Food Facts, pas qu'ils
  se vendent plus.
- La base est contributive : les ajouts dépendent de l'activité des bénévoles
  (campagnes, applications), et les catégories sont souvent complétées plus
  tard, ce qui réduit la base des années récentes. La part corrige en partie
  ces effets, pas totalement.
- Petits échantillons : sous 50 produits par an, le signal est seulement
  indicatif (OPP-06, OPP-07, OPP-10).
- Les tags sont un choix de l'équipe (validé le 2026-11-12) : d'autres tags
  donneraient d'autres chiffres.

## Attribution et licence

Données issues d'[Open Food Facts](https://world.openfoodfacts.org), disponibles
sous licence [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
`signaux_marche.json` est une base dérivée : il est lui aussi sous ODbL 1.0, et
toute réutilisation doit citer Open Food Facts et garder cette licence.
