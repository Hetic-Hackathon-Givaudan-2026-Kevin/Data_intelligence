# Data_intelligence – Groupe G03 (Marvel)

**HETIC × Givaudan AI Challenge 2026 · Défi 01 « La relation commerciale à l'ère de l'IA »**

Dépôt de l'équipe Data/IA du produit **Opportunity Radar** : un outil qui aide un commercial Givaudan à voir son portefeuille, à comprendre pourquoi une opportunité lui est proposée et à préparer son rendez-vous.

**Toutes les informations de ce dépôt sont fictives.** Les fiches clients reprennent des noms de marques réelles (PepsiCo, Danone, Nestlé) du jeu de données de Tech, à titre d'illustration uniquement.

## Par où commencer

| Je cherche… | Fichier |
|---|---|
| Le **livrable Data du 12/11** (données, pipeline, modèle, métriques, API) | [`LIVRABLE_DATA_G03.md`](LIVRABLE_DATA_G03.md) |
| Comment **reproduire** le travail pas à pas | [`FICHE_DE_TRAVAIL.md`](FICHE_DE_TRAVAIL.md) |
| Les **résultats de l'évaluation** sur 30 cas (29/30) | [`docs/evaluation.md`](docs/evaluation.md) |
| La **comparaison V1 / V2** et les métriques, brique par brique (livrable du 13/11) | [`docs/COMPARAISON_V1_V2.md`](docs/COMPARAISON_V1_V2.md) |
| La présentation de la partie Data et le lien avec les tickets | [`README_DATA.md`](README_DATA.md) |

## Contenu du dépôt

| Dossier | Contenu |
|---|---|
| [`fiches_clients/`](fiches_clients/) | 6 fiches clients fictives, modèle standard de fiche, prompt, 18 questions préparées, document central, script de construction |
| [`ia/`](ia/) | API IA V1 (FastAPI) : questions, justification d'une opportunité, compte rendu de rendez-vous. 12 tests automatiques |
| [`docs/`](docs/) | Évaluation sur 30 cas, test des modèles Ollama |

## Dépôts liés

| Dépôt | Rôle |
|---|---|
| [Gr03-Marvels-MD4, branche `Amir`](https://github.com/Amir239278/Gr03-Marvels-MD4/tree/Amir) | API RAG (fork de `hmicn/example-rag`) : route **nom d'un client → 3 questions** à poser avant le premier appel |
| [app-hackathon](https://github.com/Hetic-Hackathon-Givaudan-2026-Kevin/app-hackathon) | Prototype de l'équipe Tech (Next.js) |

## Résultats en bref (12/11/2026)

| Mesure | Résultat |
|---|---|
| Évaluation de l'API RAG sur 30 cas | **29/30** (recherche 12/12, nom du client 12/12, génération 5/6) |
| Respect du format par le modèle | V1 (prompt seul) : 0/6 · V2 (RAG + schéma JSON imposé) : 5/6 |
| Durée d'une réponse | Médiane 34 s, sur un poste sans carte graphique |
| Modèles (locaux, via Ollama) | `qwen2.5:1.5b` (génération), `nomic-embed-text` (embeddings) |

Limites principales : données fictives, petit modèle local, questions non encore validées par un commercial senior. Détail dans le livrable, sections 5 et 9.

## Lancer l'API V1

```bash
cd ia
python -m venv .venv
source .venv/Scripts/activate        # macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # renseigner API_KEY (jamais commitée)
python -m pytest -q                  # 12 tests, Ollama non nécessaire
uvicorn main:app --env-file .env --port 8000
```

Swagger : http://localhost:8000/docs. Pour l'API RAG, voir le README du dépôt Gr03-Marvels-MD4.

## Reproduire la partie data/

Le jeu de démo v2 et son API, depuis la racine du dépôt (Python 3.11, Ollama
non nécessaire) :

```bash
pip install -r requirements.txt
python data/demo_v2/generer_demo_v2.py        # 1. régénère les JSON de data/demo_v2 (graine et date fixes)
python data/verifier_jeu.py                   # 2. contrôle d'ensemble : 7 contrôles OK attendus
python -m pytest data/tests -q                # 3. toute la suite de tests
uvicorn --app-dir data/api main:app --port 8001 --reload   # 4. API, Swagger : http://localhost:8001/docs
```

Les fiches clients se reconstruisent à partir de `ia/donnees/` :

```bash
cd fiches_clients && python build_fiches.py
```

Pour aller plus loin :
- [`docs/INTEGRATION_TECH.md`](docs/INTEGRATION_TECH.md) : routes `/v2`, exemples de réponse et changements à reprendre côté Tech ;
- [`data/cas_test/README.md`](data/cas_test/README.md) : banc d'essai du compte rendu V1 / V2.

## Équipe Data

| Membre | Branche |
|---|---|
| Amir Meraka | `amir`, fusionnée dans `main` |
| Ossama Farhaoui | `data/ossama` |
| Evrad Marold Okoue Nfane | `data/evrad` |
