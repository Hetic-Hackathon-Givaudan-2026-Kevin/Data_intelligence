# Jeu de données de démo

Données fictives pour l'app (section 9.3 de la doc fonctionnelle) : un fichier
JSON par objet, clés en anglais. Chaque fichier contient une liste d'objets.

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

## Valeurs possibles

- Client `status` : `strategic`, `active`, `to_develop`. Un client sans
  opportunité (`C-08`) sert à afficher la pastille grise « Aucune ».
- Opportunité `priority` : `high` (3 triggers ou plus), `medium` (2),
  `watch` (1), selon la règle 2 de la doc.
- `estimatedRevenue` : en euros, entre 300 000 et 1 800 000.
- Question `status` : `suggested`, ou `validated` pour les 5 questions liées à
  une bonne pratique. `step` et `briefField` reprennent la banque
  (`Ambition` / `Frein` / `Ouverture`, champs du brief v1.0).
- Bonne pratique `status` : `validated`.
- Utilisateur `role` : `junior`, `senior`.
- RDV `status` : `completed`, `planned`.

## Régénérer

Les questions viennent de `data/questions/questions.json` : ne pas modifier les
JSON à la main. Depuis la racine du repo :

```bash
python data/demo/generer_demo.py
pytest data/tests/test_demo.py
```

Le dernier test vérifie que les fichiers correspondent au générateur.

## Limites

- Noms de clients, chiffres et signaux (`triggers`) fictifs : toute
  ressemblance avec une entreprise existante est fortuite.
- Le statut `validated` est simulé pour la démo : ce n'est pas une vraie
  validation par un senior.
- Pas d'authentification : les deux profils n'ont pas de mot de passe
  (section 9.4 de la doc).
