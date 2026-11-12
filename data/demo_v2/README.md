# Jeu de données de démo v2

Données de démo selon la doc fonctionnelle v2 (ticket DATA-US03, app-hackathon#13).

**Données fictives, sans lien avec de vrais clients de Givaudan.** Noms
d'entreprises, interlocuteurs et situations sont inventés : toute ressemblance
avec une entreprise existante est fortuite. `account_manager` est un rôle
fictif, jamais le nom d'une personne.

## `clients.json`

Liste de clients, clés en anglais :

| Clé | Contenu |
| --- | --- |
| `id` | Identifiant (`C-01`, …) |
| `name` | Nom fictif de l'entreprise |
| `sector` | Secteur |
| `country` | Pays |
| `account_manager` | Rôle fictif du responsable du compte |
| `relationship_status` | `strategic`, `active` ou `to_develop` |
| `last_updated` | Date de dernière mise à jour (AAAA-MM-JJ, fictive et fixe) |
| `commercial_situation` | Situation commerciale (2 phrases au plus) |
| `history_summary` | Résumé de l'historique (2 à 3 phrases) |

Les 3 clients ont des profils différents : C-01 stratégique en croissance,
C-02 actif avec une contrainte budgétaire, C-03 à développer.

Le fichier ne contient **aucun compteur** (projets, opportunités) : ils seront
calculés à partir des autres fichiers, pour ne jamais se contredire. Les textes
restent donc qualitatifs (« plusieurs projets actifs »).

## `projects.json`

Projets associés aux clients (doc v2, section 8), clés en anglais :

| Clé | Contenu |
| --- | --- |
| `id` | Identifiant (`P-01`, …) |
| `client_id` | Client du projet (id de `clients.json`) |
| `name` | Nom fictif du projet, sans vrai nom de produit ni de marque |
| `description` | Description courte |
| `status` | `active` ou `completed` |
| `start_date` | Date de début (AAAA-MM-JJ, fictive et fixe) |

Projets actifs par client, comme dans la doc : 3 pour C-01, 2 pour C-02, 1 pour
C-03.

**Projet ≠ opportunité** : un projet est un travail déjà engagé, une opportunité
un besoin pas encore engagé. Aucun projet ne fait ce que proposent les
opportunités de la doc. Projets et `commercial_situation` servent de signaux :

- `P-01` (C-01, actif) : reformulation de l'arôme agrumes de la gamme existante,
  sans extension. Signal « projet existant » pour l'opportunité « extension d'une
  gamme aromatique ». Dates d'exemple de la doc : lancé le 10/10/2026, échantillon
  envoyé le 20/10/2026 (dans la description, faute de champ dédié).
- `P-06` (C-02, terminé) porte un retour technique sur la texture : signal pour
  l'opportunité « amélioration de la texture ».
- `P-04` et `P-05` (C-02, actifs) sont des projets courants (soupes, sauces). La
  demande sur le végétal et la contrainte budgétaire de C-02 restent dans sa
  `commercial_situation` : signaux pour les opportunités correspondantes.

Les dates de début sont antérieures au `last_updated` du client.

## `opportunities.json`

Les 6 opportunités de la doc v2 (section 7), clés de la section 8 :

| Clé | Valeurs |
| --- | --- |
| `id`, `client_id`, `title`, `description`, `category`, `next_action` | Texte |
| `status` | `detected`, `to_qualify`, `confirmed` |
| `priority` | `high`, `medium`, `low`, **calculée** par la règle ci-dessous |
| `estimated_potential` | `low`, `medium`, `high` ou `null` (non renseigné) : niveau indicatif, **jamais un montant** |
| `feasibility` | `low`, `medium`, `high` ou `to_confirm` |
| `complexity` | `low`, `medium`, `high` |

Les compteurs et la date du dernier signal ne sont pas stockés : ils se
calculent à partir des signaux. Pour les pastilles du portefeuille et de la
fiche client :

- **opportunités détectées** = toutes les opportunités du client, quel que
  soit leur statut ;
- **à qualifier** = celles dont `status` vaut `to_qualify`.

Maison Nova Drinks : 2 détectées et 1 à qualifier, comme dans la doc. Nordic
Food Industries : 3 et 1. Alimenta Distribution : 1 et 0.

### Règle de priorité (section 5.3)

La doc demande de tenir compte de la pertinence du signal, du potentiel, de la
faisabilité, de l'urgence et de la confiance ; une classification par règles
suffit pour le prototype. Score de 0 à 7 :

| Critère | Points |
| --- | --- |
| Confiance du meilleur signal de l'opportunité | high 2, medium 1, low 0 |
| `estimated_potential` | high 2, medium 1, low ou `null` 0 |
| `feasibility` | high 2, medium 1, low ou `to_confirm` 0 |
| Urgence : le client s'est exprimé lui-même (`meeting_report` ou `client_request`) dans les 30 jours avant le 2026-11-12, date fixe du jeu | 1 |

`high` si le score vaut 5 ou plus, `medium` de 3 à 4, `low` en dessous.

## `signals.json`

Au moins un signal par opportunité. Clés de la section 8 (`id`,
`opportunity_id`, `description`, `source_type`, `source_date`, `confidence`,
`evidence_type`) plus deux **extensions** : `is_real_source` (booléen) et
`source_ref` (URL ou fichier, obligatoire si `is_real_source` vaut `true`).

- `source_type` : `meeting_report` (compte rendu), `project_history`,
  `client_request`, `market_trend`, `commodity_price`, `company_report`,
  `regulation`.
- `source_date` : date de l'information (date de l'échange, des données ou de
  la publication). Pour une tendance calculée sur une période, c'est la **fin
  de la période observée** (Open Food Facts : 2022-12-31 ; INSEE : dernier jour
  du mois observé), pas la date d'extraction, qui va dans `source_ref` : sinon
  la « date du dernier signal » présenterait une tendance ancienne comme
  récente.
- `evidence_type` (section 5.5) : `fact` (présent dans une source),
  `hypothesis` (interprétation), `to_confirm`.

Signaux fictifs, repris de la doc : intérêt exprimé (O-01), projet existant
P-01 (O-02), demande sur le végétal (O-03), retour technique sur P-06 (O-04),
contrainte budgétaire (O-05), et premier projet en cours P-07 (O-06, signal
propre au client).

Signaux réels :

| Opp. | Source | Confiance | Remarque |
| --- | --- | --- | --- |
| O-01 | Open Food Facts, boissons fonctionnelles 2020→2022 (`data/signaux/signaux_marche.json`) | medium | Petit échantillon. |
| O-03 | Open Food Facts, alternatives végétales 2020→2022 | low | Chiffre français, client en Suède : `hypothesis`. |
| O-05 | INSEE, sucre importé en euros (idbank 010002028) | medium | +15 % sur un an, mais environ −39 % depuis octobre 2023 ; coût de matière première, pas le coût du client. |
| O-06 | Rapport intégré Givaudan 2025, pp. 49-50 | medium | Tendance clean label et naturalité, mondiale. `source_date` = date du PDF (2026-01-29). |
| O-06 | EU Food Flavourings, limonène (`POL-FFL-IMPORT-3388`) | high | Règlement d'exécution (UE) n° 872/2012. L'autorisation est un fait ; son lien avec la nouvelle référence (par exemple agrumes) est une piste. |

Le signal O-06 « veille marché fictive » de la doc est remplacé par ces deux
signaux réels. Les chiffres Open Food Facts sont relus dans
`data/signaux/signaux_marche.json` à chaque génération. Les échantillons INSEE
et UE sont hors du repo (`D:\open_data\`, voir `data/sources/README_sources.md`).

## Régénérer

Ne pas modifier les JSON à la main. Depuis la racine du repo :

```bash
python data/demo_v2/generer_demo_v2.py
pytest data/tests/test_clients_v2.py data/tests/test_projects_v2.py data/tests/test_opportunities_signals_v2.py
```

## Attribution

Open Food Facts (ODbL 1.0), INSEE (Licence Ouverte 2.0, « Source : Insee »),
Commission européenne — EU Food Flavourings (CC BY 4.0), Givaudan 2025
Integrated Report (citation courte avec page).
