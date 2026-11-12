# Signaux de marché (Open Food Facts)

Remplacent les signaux « croissance du marché » inventés du jeu de démo par des
chiffres calculés sur Open Food Facts.

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `extraire_off.py` | Lit une seule fois l'export CSV Open Food Facts (`.csv.gz`, tabulation) avec DuckDB et garde 5 colonnes dans un Parquet hors du repo : `code`, `created_t`, `countries_tags`, `categories_tags`, `labels_tags`. |
| `calculer_signaux.py` | Calcule les signaux des 12 opportunités à partir du Parquet et écrit `signaux_marche.json`. |
| `signaux_marche.json` | Pour chaque opportunité : tags, chiffres par année (2019-2025), évolution sur 3 périodes, statut, texte du trigger, source et date d'extraction. |
| `biais_maturite.py` | Preuve du biais de maturité (tableaux ci-dessous). N'écrit rien dans le repo. |

## Méthode

- Produits vendus en France (`countries_tags` contient `en:france`), par année
  d'ajout dans Open Food Facts (`created_t`).
- Pour chaque opportunité : part des produits portant au moins un des tags
  validés, parmi les ajouts de l'année qui ont au moins une catégorie (tags de
  catégories), au moins un label (tags de labels), ou les deux (OPP-02 :
  catégorie `en:snacks` ET un label bio ou équitable). Les chiffres bruts
  restent dans le JSON.
- **Période affichée : 2020→2022**, évolution relative de la part, arrondie à la
  dizaine dans le texte (le chiffre exact reste dans le JSON).
- **Statut** :
  - `compte` : la part monte à la fois sur 2019→2022 et sur 2020→2022, avec au
    moins 50 produits chaque année de 2019 à 2022 ; le trigger compte pour la
    priorité ;
  - `contraire` : la part baisse sur les deux périodes (OPP-03) ;
  - `indicatif` : les deux périodes divergent (OPP-07) ou il y a moins de
    50 produits une année.
- **2023→2025 est gardé dans le JSON, marqué « non mûr, indicatif »** : il ne
  sert ni au texte ni au statut.
- OPP-11 et OPP-12 n'ont pas de signal (pas de tag fiable / signal propre au
  client).

## Pourquoi pas 2023→2025 : le biais de maturité

Les produits ajoutés récemment ont eu moins de temps pour recevoir des
catégories et labels précis. Sur 2023→2025, presque toutes les parts baissent ;
sur une période où tous les produits ont plus de 3 ans, la baisse disparaît.

Nombre moyen de tags par produit (produits vendus en France qui en ont), selon
l'année d'ajout :

| Année d'ajout | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Catégories | 7,3 | 6,7 | 6,4 | 6,4 | 6,3 | 6,1 | 6,1 | 6,0 | 5,5 |
| Labels | 3,4 | 2,7 | 2,8 | 2,9 | 2,8 | 2,8 | 2,8 | 2,5 | 2,4 |

Évolution de la part selon la période (entre parenthèses : produits la première
et la dernière année) :

| Opp. | A. 2023→2025 (non mûr) | B. 2019→2022 | C. 2020→2022 (affichée) | D. 2023→2025, completeness ≥ 0,8 |
| --- | --- | --- | --- | --- |
| OPP-01 Boissons fonctionnelles | −3,7 % (163→101) | +97,4 % (197→172) | +100,6 % (139→172) | +25,9 % (5→3) |
| OPP-02 Snacks bio ou équitables | −8,6 % (922→659) | +17,6 % (1 784→882) | +8,1 % (1 397→882) | +11,7 % (77→42) |
| OPP-03 AOP, AOC ou Label Rouge | −13,3 % (850→1 038) | −31,6 % (2 526→754) | −29,4 % (1 801→754) | −2,0 % (48→23) |
| OPP-04 Sucre réduit | −12,0 % (1 016→1 259) | +10,8 % (2 153→1 041) | +17,3 % (1 496→1 041) | +3,8 % (69→35) |
| OPP-05 Alternatives végétales | +45,0 % (346→323) | +48,8 % (614→404) | +31,0 % (500→404) | +13,0 % (52→28) |
| OPP-06 Sans alcool | −24,7 % (64→31) | +58,3 % (90→63) | +32,6 % (77→63) | −70,0 % (7→1) |
| OPP-07 Sel réduit | −91,1 % (88→11) | +15,6 % (210→106) | −1,3 % (181→106) | −100,0 % (13→0) |
| OPP-08 Sans additifs ni conservateurs | −12,2 % (2 734→3 378) | +11,8 % (5 932→2 895) | +17,4 % (4 155→2 895) | −23,2 % (213→80) |
| OPP-09 Nutrition sportive | −37,0 % (382→155) | +17,0 % (713→369) | +29,5 % (462→369) | +29,1 % (13→8) |
| OPP-10 Kéfirs et bifidus | +11,5 % (39→28) | +94,8 % (65→56) | +12,1 % (81→56) | −30,1 % (6→2) |
| **Hausses** | **2 sur 10** | **9 sur 10** | **8 sur 10** | 5 sur 10 |

La colonne D n'est pas exploitable : `states_tags` n'a pas d'état pour les
labels, `en:categories-completed` signifie seulement « catégorie non vide »,
`en:checked` est trop rare, et `completeness` laisse quelques produits par
opportunité tout en étant lui-même biaisé par la maturité (médiane 0,38 en 2023,
0,16 en 2025).

## Régénérer

Le CSV (environ 1,5 Go compressé) et les Parquet restent hors du repo. Dans un
venv avec `duckdb` :

```bash
python data/signaux/extraire_off.py D:/en.openfoodfacts.org.products.csv.gz D:/off/off_tags.parquet
python data/signaux/calculer_signaux.py D:/off/off_tags.parquet
python data/demo/generer_demo.py
pytest data/tests/

# preuve du biais (facultatif)
python data/signaux/biais_maturite.py --extraire-etats D:/en.openfoodfacts.org.products.csv.gz D:/off/off_etats.parquet
python data/signaux/biais_maturite.py D:/off/off_tags.parquet D:/off/off_etats.parquet
```

`calculer_signaux.py` met la date du jour dans `date_extraction`.

## Limites

- **Nombre de produits référencés ≠ ventes.** Une part qui monte dit que plus
  de nouveaux produits de ce type sont saisis dans Open Food Facts, pas qu'ils
  se vendent plus.
- **La tendance date de 3 à 5 ans** (2019-2022) : elle dit ce qui montait alors,
  pas forcément ce qui monte aujourd'hui.
- **Années Covid** : 2020-2021 ont pu modifier les lancements et les habitudes
  de saisie.
- **Parts sensibles à ce qui a été ajouté chaque année dans Open Food Facts** :
  la base est contributive, et les ajouts dépendent de l'activité des
  bénévoles (campagnes, applications, imports de fabricants). La part corrige
  en partie l'effet de volume, pas les changements de composition.
- Petits échantillons : sous 50 produits par an, le signal est seulement
  indicatif.
- Les tags sont un choix de l'équipe (validé le 2026-11-12) : d'autres tags
  donneraient d'autres chiffres.

## Attribution et licence

Données issues d'[Open Food Facts](https://world.openfoodfacts.org), disponibles
sous licence [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
`signaux_marche.json` est une base dérivée : il est lui aussi sous ODbL 1.0, et
toute réutilisation doit citer Open Food Facts et garder cette licence.
