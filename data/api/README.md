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

### Routes v2 (doc fonctionnelle v2, `data/demo_v2/`)

Tous les compteurs et toutes les dates sont calculés à partir des fichiers ;
rien n'est saisi dans l'API.

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/v2/dashboard` | Clients suivis, opportunités détectées, à qualifier, RDV à préparer (0 sans `meetings.json`) |
| GET | `/v2/clients?q=` | Portefeuille avec `active_projects`, `detected_opportunities` (toutes les opportunités du client), `to_qualify` ; `q` cherche dans le nom (sans majuscules ni accents) |
| GET | `/v2/clients/{id}` | Fiche client : projets, opportunités avec `last_signal_date`, chronologie (plus récent d'abord), synthèse « Ce qu'il faut savoir » |
| GET | `/v2/opportunities/{id}` | Opportunité, client, signaux complets, justification (section 5.2) |
| GET | `/v2/opportunities/{id}/meeting` | Contexte du Meeting Copilot (`data/demo_v2/meeting_context.json`) |
| POST | `/v2/meetings/report` | Reçoit `opportunity_id`, `collected_points`, `answers` et `notes` ; renvoie un **Meeting** (non enregistré) dont `summary` est le **MeetingReport** (`data/demo_v2/MODELE_DONNEES.md`) |

Règles V1 (sans LLM) :

- **Synthèse client** : situation (`commercial_situation`), projets actifs du
  plus récent au plus ancien, besoins exprimés (signaux `meeting_report` et
  `client_request`), autres signaux des 90 derniers jours avant le 2026-11-12,
  points d'attention (opportunités à qualifier, faisabilité à confirmer,
  hypothèses). Chaque phrase porte `fact`, `hypothesis` ou `to_confirm`.
- **Justification** : informations utilisées (signaux), provenance (source
  réelle ou « source fictive (démo) »), raisonnement (détail du score de
  priorité), éléments à vérifier (statut, hypothèses, faisabilité, potentiel,
  points manquants de la checklist).
- **Compte rendu** (`generated_by: rules_v1`, `validated: false`) :
  - `collected_points` = points cochés + points qui ont une réponse ;
  - points non recueillis → `missing_information` (ceux connus avant le RDV
    sont marqués « à reconfirmer ») ;
  - `opportunity_decision` : `confirmed` si objectifs et besoin réel sont
    recueillis, sinon `to_qualify` ; jamais `discarded` automatiquement ;
  - `internal_teams` (section 2.4) : `application` si les contraintes
    techniques sont recueillies ; `creation` si l'opportunité demande un nouvel
    arôme (nouvelle gamme, extension, nouvelle formulation, nouvelle référence)
    et que les objectifs ou le besoin sont recueillis ; `marketing` si les
    objectifs sont recueillis et que l'opportunité a un signal de marché ;
    `regulatory` si un mot-clé réglementaire apparaît dans les notes ou les
    réponses, ou si l'opportunité a un signal réglementaire ;
  - les prochaines actions sont seulement dans `next_actions` (pas dans
    `summary`) ; la contrainte budgétaire, portée par le commercial, y devient
    une action, pas une équipe.

  Un point de checklist inconnu ou une date invalide renvoie `422`.

Un id inconnu renvoie `404` avec un message (ex. `Client inconnu : C-99`).
CORS est ouvert à toutes les origines pour l'app front.

Exemple :

```bash
curl -X POST http://localhost:8001/questions -H "Content-Type: application/json" \
  -d '{"champs_manquants": ["brief.echeance_lancement", "brief.contraintes.regime"], "opportunite_id": "OPP-06"}'
```

## Tests

```bash
pytest data/tests/test_api.py data/tests/test_api_v2.py
```

## Limites

- Démo uniquement : pas d'authentification, CORS ouvert, données fictives.
- Les JSON sont lus au démarrage : relancer l'API après `generer_demo.py` ou
  `generer_demo_v2.py` (ou lancer avec `--reload`).
- Synthèse, justification et compte rendu sont des modèles de texte V1 : ils
  reformulent les données, ils n'en inventent pas.
