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

## Régénérer

Ne pas modifier `clients.json` à la main. Depuis la racine du repo :

```bash
python data/demo_v2/generer_demo_v2.py
pytest data/tests/test_clients_v2.py
```
