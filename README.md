# Data_intelligence – Groupe G03 (Marvel)

**HETIC × Givaudan AI Challenge 2026 · Défi 01 « La relation commerciale à l'ère de l'IA »**

Dépôt de l'équipe Data/IA du produit **Opportunity Radar** : un outil qui aide un commercial Givaudan à voir son portefeuille, à comprendre pourquoi une opportunité lui est proposée et à préparer son rendez-vous.

**Toutes les données de ce dépôt sont fictives.**

## Par où commencer

| Je cherche… | Fichier |
|---|---|
| Le **livrable Data du 12/11** (données, pipeline, modèle, métriques, API) | [`LIVRABLE_DATA_G03.md`](LIVRABLE_DATA_G03.md) |
| Comment **reproduire** le travail pas à pas | [`FICHE_DE_TRAVAIL.md`](FICHE_DE_TRAVAIL.md) |
| Les **résultats de l'évaluation** sur 30 cas (29/30) | [`docs/evaluation.md`](docs/evaluation.md) |
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

## Équipe Data

| Membre | Branche |
|---|---|
| Amir Meraka | `amir`, fusionnée dans `main` |
| Ossama Farhaoui | `data/ossama` |
| Evrad Marold Okoue Nfane | `data/evrad` |
