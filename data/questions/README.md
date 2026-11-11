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

## Moteur V1

`moteur.py` propose, sans LLM, les questions à poser au prochain RDV pour
obtenir les champs du brief encore manquants (bibliothèque standard uniquement).

Règles :

- Noms de champ normalisés : le préfixe `brief.` est retiré, et tout sous-champ
  de `contraintes` (ex. `contraintes.regime`) devient `contraintes`. Un champ
  inconnu est ignoré avec un avertissement.
- Les questions au statut « À modifier » sont exclues.
- Une question par champ manquant, dans l'ordre de priorité ci-dessous, jusqu'à
  `nb` (3 par défaut). S'il manque moins de `nb` champs, une 2e question est
  ajoutée pour chaque champ manquant, dans le même ordre.
- Jamais de question pour un champ déjà rempli.
- Pour un même champ : d'abord l'opportunité demandée (`--opportunite`), puis
  « Validée » avant « Suggérée », puis l'id le plus petit.
- Avec `--brief` et sans `--opportunite`, l'opportunité est déduite du brief :
  les mots de `objectif`, `marche` et `profil_gout` sont comparés aux libellés
  des opportunités (minuscules, sans accents, sans « s » final, sans mots vides
  comme « de », « la », « pour » ; « sans » est gardé). Le plus de mots communs
  gagne, l'id le plus petit en cas d'égalité ; sans mot commun, pas
  d'opportunité.
- Avec `--brief`, les champs manquants sont ceux de
  `incertitudes.champs_manquants`, plus les champs du bloc `brief` qui valent
  « non renseigné ». Une liste vide n'est pas comptée comme manquante.
- La dernière ligne donne les ids joints par `;`, à copier dans la colonne
  `questions_proposees` de `data/eval/grille_fiabilite.csv`.

Ordre de priorité (**à valider avec l'équipe et les seniors**) :

1. `objectif`
2. `echeance_lancement`
3. `budget_matiere_eur_par_litre`
4. `contraintes`
5. `marche`
6. `profil_gout`
7. `insights_concurrence`

Exemples, depuis la racine du repo :

```bash
python data/questions/moteur.py --brief data/questions/exemples/brief_exemple.json
python data/questions/moteur.py --champs brief.objectif,contraintes.regime --opportunite OPP-05 --nb 3
pytest data/tests/
```

`exemples/brief_exemple.json` est un brief fictif conforme au schéma v1.0, avec
trois champs « non renseigné ».

Limites du moteur :

- Si l'opportunité n'a pas de question pour un champ manquant, le moteur en
  prend une d'une autre opportunité, qui peut citer un autre produit (ex. Q-03
  « boisson fonctionnelle » pour l'échéance d'un projet sans alcool). Piste à
  discuter : une question générique par champ.
- La déduction de l'opportunité compare des mots, sans comprendre le sens : un
  synonyme n'est pas reconnu, et un mot isolé peut suffire à choisir une
  opportunité.
