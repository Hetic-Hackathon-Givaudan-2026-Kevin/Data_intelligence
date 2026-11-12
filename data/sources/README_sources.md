# Sources open data complémentaires

Revue du 2026-11-12 pour Givaudan Opportunity Radar (doc fonctionnelle v2) : sources
pouvant étayer les signaux des opportunités (source, date, confiance, fait ou hypothèse).
Déjà utilisées et hors de cette revue : Open Food Facts, rapport intégré Givaudan 2025,
table Ciqual, registre européen des allégations de santé.

Règles appliquées : open data ou API officielle, licence claire et réutilisable, aucune
donnée personnelle, aucune API payante, aucun scraping. Chaque source ci-dessous a été
ouverte (page de licence, API interrogée) ; rien n'a été inventé.

Besoins : **1** tendances de marché par catégorie, **2** prix et coûts, **3** réglementation,
**4** conversations commerciales ou comptes rendus de réunion.

## Décisions

| # | Source | Producteur | Licence | Accès | Besoin | Décision | Raison |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Indices de prix et cours des matières premières, `IPPMP-NF`, sucre en euros (idbank `010002028`) | INSEE | Licence Ouverte 2.0 (Etalab), mention « Source : Insee » | API SDMX sans clé, XML, mensuel | 2 | **GO** | Coût d'une matière première, mis à jour chaque mois : étaie la contrainte budgétaire. |
| 2 | EU Food Flavourings (Union list, règlement 1334/2008) | Commission européenne, DG SANTE | CC BY 4.0 | API JSON sans clé | 3 | **GO** | Arômes autorisés dans l'UE, par catégorie d'aliments, avec la référence du règlement. |
| 3 | EU Food Additives (Union list, règlement 1333/2008) | Commission européenne, DG SANTE | CC BY 4.0 | API JSON sans clé | 3 | **GO conditionnel** | Licence et accès vérifiés, mais pas encore de cas d'usage dans la démo. |
| 4 | IPCH ECOICOP v2 (`prc_hicp_minr`) | Eurostat | CC BY 4.0 | API JSON sans clé, mensuel | 2 | **NO-GO** comme signal sur la Suède | TVA alimentaire suédoise passée de 12 % à 6 % le 1er avril 2026 : la baisse des prix vient surtout de la taxe. Ce sont en plus des prix payés par les consommateurs, pas des coûts d'ingrédients. |
| 5 | IPC alimentation, table `TAB6599` | Statistics Sweden (SCB) | CC0 | API PxWeb v2 JSON, mensuel | 2 | **NO-GO** comme signal | Même raison (TVA suédoise) ; fait doublon avec Eurostat pour la Suède. |
| 6 | AMI Meeting Corpus | Université d'Édimbourg | CC BY 4.0 | Hugging Face | 4 | **GO conditionnel**, pas pour l'instant | Réunions jouées autour de la conception d'un produit, en anglais ; résumés à vérifier dans les annotations. Mis de côté par l'équipe. |
| 7 | QMSum | Yale LILY | MIT (dépôt) | GitHub, JSON | 4 | **GO conditionnel** | Garder seulement la partie AMI / ICSI : la partie parlementaire nomme des élus. Licence ICSI à vérifier. |
| 8 | saas-sales-conversations | DeepMost Innovations | Apache 2.0 | Hugging Face | 4 | **GO conditionnel**, pas pour l'instant | Données synthétiques, mais sur le logiciel, pas l'alimentaire ; vérifier `company_name`. Mis de côté par l'équipe. |
| 9 | MeetingBank, DialogSum | Universitaires | CC BY-NC-SA 4.0 | Hugging Face | 4 | **NO-GO** | Usage commercial interdit ; MeetingBank contient des élus nommés. |
| 10 | Oqali (Observatoire de l'alimentation) | INRAE / Anses | Pas de licence trouvée | — | 1 | **NO-GO** pour l'instant | Ni jeu de données sur data.gouv.fr, ni licence claire trouvés. |

Le besoin 1 (tendances par catégorie pour la France et la Suède) n'est couvert par aucune
source ouverte vérifiée, en dehors d'Open Food Facts.

Vus mais pas vérifiés, donc hors du tableau : FAO Food Price Index (les bases statistiques
de la FAO sont sous CC BY 4.0 « sauf mention contraire », page de l'indice non ouverte),
FAOSTAT, Agreste, FranceAgriMer, Open Beauty Facts.

## Échantillons (hors du repo)

Dans `D:\open_data\`, un dossier par source, avec un `PROVENANCE.json` (URL, licence,
date d'extraction) :

| Dossier | Contenu |
| --- | --- |
| `insee_ippmp_sucre\` | `010002028.xml` (réponse brute) et `010002028.csv` : 36 mois, 2023-10 à 2026-09 |
| `eu_food_flavourings\` | `food_flavourings_200.json` : 200 premiers enregistrements (lecture arrêtée là) |

Les signaux tirés de ces sources iront dans `signals.json` avec le ticket US06 ; aucun n'est
encore créé.

## Points d'attention pour US06

- **Sucre (INSEE)** : l'indice passe de 80,4 (2025-09) à 92,9 (2026-09), soit +15,5 % sur
  un an, après une forte baisse (152,1 en 2023-10). C'est un prix mondial à l'import, pas
  le coût du client ni le prix de vente : le sucre vendu aux consommateurs baisse sur la
  même période.
- **Le signal sucre devra afficher les deux chiffres** : +15 % sur un an (2025-09 → 2026-09),
  mais environ −39 % par rapport à octobre 2023 (152,1 → 92,9).
- **Arômes (UE)** : la liste dit ce qui est autorisé, pas ce qui est tendance ; elle ne
  couvre pas l'étiquetage.

## Attribution

- Données INSEE : « Source : Insee », Licence Ouverte 2.0 —
  <https://www.insee.fr/fr/information/2008466>.
- EU Food Flavourings : © Union européenne, Commission européenne (DG SANTE), CC BY 4.0 —
  <https://data.europa.eu/data/datasets/food-flavourings>.
