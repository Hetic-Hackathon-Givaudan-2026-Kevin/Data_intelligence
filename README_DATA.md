# Partie Data / IA – Givaudan Opportunity Radar (équipe G03)

Responsable : Amir (Data). **Toutes les données sont fictives.**

## Contenu
| Dossier | Contenu | Pour qui |
|---|---|---|
| `ia/` | API IA (FastAPI) qui lit le jeu de données de Tech et fournit questions, justification et compte rendu | Tech (intégration) |
| `ia/donnees/` | JSON de Tech (clients, projets, opportunités, signaux, rendez-vous, synthèses) + questions préparées par Data | API |
| `fiches_clients/` | Livrables du formateur : modèle de fiche, prompt, 6 fiches, 18 questions, document central | Formateur, équipe |
| `docs/` | Test des modèles Ollama, limites | Jury, équipe |

## Comment ça s'assemble
```
JSON de Tech ──► Écran (Tech, Next.js) ──► API Tech (Express) ──► API IA Data (ce dépôt, port 8000) ──► Ollama
```
L'écran affiche les données de Tech. Pour les 3 blocs « IA », il appelle l'API Data.

## Lancer l'API (Windows, Git Bash)
```bash
cd ia
python -m venv .venv
source .venv/Scripts/activate        # macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # mettre une vraie valeur dans API_KEY (jamais commitée)
python -m pytest -q                  # 12 tests, Ollama non nécessaire
uvicorn main:app --env-file .env --port 8000
```
Swagger : http://localhost:8000/docs. Exposer pour Tech : `ngrok http 8000` (ngrok 3.29 ou plus).

## Correspondance avec les tickets
| Ticket | Livrable |
|---|---|
| DATA-US08, TECH-US14 Justification | `GET /justification/{opportunity_id}` |
| DATA-US10, TECH-US16 et US17 Questions | `POST /questions` |
| DATA-US11, TECH-US18 Compte rendu | `POST /compte-rendu` |
| Consigne formateur (6 fiches, prompt, 3 questions) | `fiches_clients/` |

Détails des routes : `ia/README.md`.
