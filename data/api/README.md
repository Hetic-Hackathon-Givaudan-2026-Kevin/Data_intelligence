# API de démo

API FastAPI qui sert le jeu de démo (`data/demo/*.json`) et le moteur V1 de
questions (`data/questions/moteur.py`). Elle ne contient aucune donnée : elle
lit ces fichiers au démarrage.

## Lancer

Depuis la racine du repo, dans un venv :

```bash
pip install -r data/api/requirements.txt
uvicorn --app-dir data/api main:app --port 8001 --reload
```

Puis ouvrir la documentation interactive (Swagger) :
<http://localhost:8001/docs>. Arrêter avec `Ctrl+C`.

Le port 8001 évite le conflit avec l'ancienne API, sur 8000.

## Routes

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/sante` | Statut et nombre de questions chargées |
| GET | `/clients` | Liste des clients de démo |
| GET | `/clients/{id}` | Un client avec ses opportunités |
| GET | `/opportunites/{id}` | Une opportunité avec ses 3 questions (Ambition, Frein, Ouverture) |
| POST | `/questions` | Mode « champs du brief encore manquants » : questions du moteur V1, aux clés du jeu de démo |
| GET | `/bonnes-pratiques` | Les 5 bonnes pratiques |

Un id inconnu renvoie `404` avec un message (ex. `Client inconnu : C-99`).
CORS est ouvert à toutes les origines pour l'app front.

Exemple :

```bash
curl -X POST http://localhost:8001/questions -H "Content-Type: application/json" \
  -d '{"champs_manquants": ["brief.echeance_lancement", "brief.contraintes.regime"], "opportunite_id": "OPP-06"}'
```

## Tests

```bash
pytest data/tests/test_api.py
```

## Limites

- Démo uniquement : pas d'authentification, CORS ouvert, données fictives.
- Les JSON sont lus au démarrage : relancer l'API après `generer_demo.py`.
