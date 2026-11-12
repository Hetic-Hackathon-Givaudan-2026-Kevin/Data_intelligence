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

## Régénérer

Ne pas modifier les JSON à la main. Depuis la racine du repo :

```bash
python data/demo_v2/generer_demo_v2.py
pytest data/tests/test_clients_v2.py data/tests/test_projects_v2.py
```
