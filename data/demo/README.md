# Jeu de données de démo

Données de démo pour l'app (section 9.3 de la doc fonctionnelle) : un fichier
JSON par objet, clés en anglais. Chaque fichier contient une liste d'objets.
Tout est fictif, sauf les signaux de marché marqués `real` (Open Food Facts).

| Fichier | Objet | Clés |
| --- | --- | --- |
| `clients.json` | Client (8) | `id`, `name`, `sector`, `status`, `opportunityIds` |
| `opportunities.json` | Opportunité (12) | `id`, `clientId`, `title`, `category`, `priority`, `estimatedRevenue`, `description`, `triggers`, `recommendedQuestions` |
| `questions.json` | Question (36) | `id`, `opportunityId`, `text`, `justification`, `status`, `step`, `briefField` |
| `best_practices.json` | Bonne pratique (5) | `id`, `title`, `content`, `author`, `status`, `questionId` |
| `users.json` | Profil (2) | `id`, `name`, `role` |
| `meetings.json` | RDV (2) | `id`, `clientId`, `opportunityId`, `date`*, `questionsAsked`, `customerFeedback`, `status` |

\* `date` (AAAA-MM-JJ, fictive) est une **extension de la section 9.3**, qui ne
la prévoit pas : `M-01` (completed) est dans le passé, `M-02` (planned) dans
les jours qui suivent la création du jeu (novembre 2026). Les dates sont fixes
et ne se décalent pas avec le temps.

Chaque trigger est un objet `{text, type, counted, source}` au lieu d'un simple
texte (**extension de la section 9.3**) :

- `type: "real"` : signal de marché calculé sur Open Food Facts
  (`data/signaux/signaux_marche.json`), `source` renseignée. Il remplace
  l'ancien trigger inventé « croissance du marché » des opportunités 01, 02,
  03, 05, 06, 09 et 10. `counted` vaut `true` seulement si la part des nouveaux
  produits augmente entre 2023 et 2025 avec au moins 50 produits chaque année ;
  sinon le texte précise « signal contraire » ou « indicatif ».
- `type: "fictional"` : signal client inventé, `source: null`, `counted: true`.

## Valeurs possibles

- Client `status` : `strategic`, `active`, `to_develop`. Un client sans
  opportunité (`C-08`) sert à afficher la pastille grise « Aucune ».
- Opportunité `priority` : selon la règle 2 de la doc, appliquée aux seuls
  triggers dont `counted` vaut `true` : `high` (3 ou plus), `medium` (2),
  `watch` (0 ou 1).
- `estimatedRevenue` : en euros, entre 300 000 et 1 800 000.
- Question `status` : `suggested`, ou `validated` pour les 5 questions liées à
  une bonne pratique. `step` et `briefField` reprennent la banque
  (`Ambition` / `Frein` / `Ouverture`, champs du brief v1.0).
- Bonne pratique `status` : `validated`.
- Utilisateur `role` : `junior`, `senior`.
- RDV `status` : `completed`, `planned`.

## Régénérer

Les questions viennent de `data/questions/questions.json` et les signaux de
marché de `data/signaux/signaux_marche.json` : ne pas modifier les JSON à la
main. Depuis la racine du repo :

```bash
python data/demo/generer_demo.py
pytest data/tests/test_demo.py
```

Le dernier test vérifie que les fichiers correspondent au générateur.

## Limites

- Noms de clients, montants et signaux client (`type: "fictional"`) fictifs :
  toute ressemblance avec une entreprise existante est fortuite.
- Les signaux `real` comptent des produits référencés dans Open Food Facts, pas
  des ventes (voir `data/signaux/README.md`).

## Attribution

Les signaux de marché `real` sont dérivés d'Open Food Facts
(<https://world.openfoodfacts.org>), base disponible sous licence
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Toute réutilisation
doit citer Open Food Facts.
- Le statut `validated` est simulé pour la démo : ce n'est pas une vraie
  validation par un senior.
- Pas d'authentification : les deux profils n'ont pas de mot de passe
  (section 9.4 de la doc).
