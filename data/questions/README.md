# Banque de questions

## À quoi elle sert

Quand un brief client est incomplet, l'outil propose au commercial des questions
pour obtenir les champs encore manquants. Chaque question est rattachée à un
champ du brief (`champ_brief`, schéma v1.0) et à une opportunité, avec trois
étapes par opportunité : Ambition, Frein, Ouverture.

## D'où elle vient

`questions_source.csv` est l'export de la banque tenue par l'équipe G03
(36 questions, 12 opportunités). La colonne `Origine` indique la source de
chaque question : le PDF du sujet, une proposition d'Amir, ou une nouvelle
question, « retravaillée » si elle a été reformulée.

`questions.json` est généré à partir du CSV : ne pas le modifier à la main.

## Régénérer le JSON et lancer le test

Depuis la racine du repo :

```bash
python -m pip install pytest   # une fois, dans votre venv
python data/questions/convertir.py
pytest data/tests/test_questions.py
```

Le script n'utilise que la bibliothèque standard ; le test demande `pytest`.
Le dernier test vérifie que `questions.json` correspond bien au CSV : s'il
échoue, relancez `convertir.py`.

## Limites

- Les opportunités OPP-04 à OPP-12 sont des hypothèses de l'équipe, pas des
  besoins exprimés par Givaudan.
- Les clients évoqués sont fictifs.
- Aucune question n'est encore validée par un senior (toutes « Suggérée »).
- La cible consommateur n'a pas de champ dans le schéma v1.0 : les questions
  sur la cible sont rangées sous `marche`.
- `budget_matiere_eur_par_litre` ne convient qu'aux boissons ; pour les snacks
  ou autres produits solides, il faudra une autre unité.
- La liste des champs du brief est recopiée en dur dans le test : à mettre à
  jour si le schéma évolue.
