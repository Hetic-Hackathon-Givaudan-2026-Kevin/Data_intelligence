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
| GET | `/v2/dashboard` | Clients suivis, opportunités détectées, à qualifier, RDV à préparer (rendez-vous `planned` de `meetings.json` : 0 dans la démo, les 2 exemples sont `completed`) |
| GET | `/v2/clients?q=` | Portefeuille avec `active_projects`, `detected_opportunities` (toutes les opportunités du client), `to_qualify` ; `q` cherche dans le nom (sans majuscules ni accents) |
| GET | `/v2/clients/{id}` | Fiche client : projets, opportunités avec `last_signal_date`, chronologie (plus récent d'abord), synthèse « Ce qu'il faut savoir » |
| GET | `/v2/opportunities/{id}` | Opportunité, client, signaux complets, justification commerciale (section 5.2, DATA-US08) |
| GET | `/v2/opportunities/{id}/meeting` | Contexte du Meeting Copilot (`data/demo_v2/meeting_context.json`) ; chaque question porte `opportunity_id` et `opportunity_link` (DATA-US10) |
| POST | `/v2/meetings/report?mode=rules_v1` | Reçoit `opportunity_id`, `collected_points`, `answers` et `notes` ; renvoie un **Meeting** (non enregistré) dont `summary` est le **MeetingReport** (`data/demo_v2/MODELE_DONNEES.md`). `mode` : `rules_v1` (défaut) ou `llm_v2` |

Règles V1 (sans LLM) :

- **Synthèse client** : situation (`commercial_situation`), projets actifs du
  plus récent au plus ancien, besoins exprimés (signaux `meeting_report` et
  `client_request`), autres signaux des 90 derniers jours avant le 2026-11-12,
  points d'attention (opportunités à qualifier, faisabilité à confirmer,
  hypothèses). Chaque phrase porte `fact`, `hypothesis` ou `to_confirm`.
- **Justification** (DATA-US08) : la justification commerciale stockée dans
  `opportunities.json` (besoin du client, pourquoi maintenant, intérêt pour
  Givaudan, faits, hypothèses, à confirmer, risques ; chaque phrase avec son
  `evidence_type` et ses `sources`), plus `reasoning` (détail du score de la
  grille de qualification) et `provenance` ; `information_used` et `to_verify`
  sont gardés pour compatibilité.
- **Compte rendu** (DATA-US11, `data/demo_v2/compte_rendu.py`) : rubriques
  séparées (`needs`, `technical_constraints`, `budget_constraints`, `timeline`,
  `missing_information`, `next_actions`, `internal_teams`). Chaque élément porte
  `status` : `confirmed` (dit explicitement dans les notes) ou `to_verify`
  (déduit, hésitant, contradictoire ou seulement coché), et l'`excerpt` exact
  des notes dont il vient. Rien n'est inventé : les rubriques déduites
  (manquants, actions, équipes) sont toujours `to_verify`.
  - `mode=rules_v1` : mots-clés phrase par phrase ; hésitation (« peut-être »,
    « à confirmer », « pas encore »…) ou deux dates de calendrier différentes →
    `to_verify` ; une réponse (`answers`) est confirmée ; un point coché sans
    détail est `to_verify`.
  - `mode=llm_v2` : qwen2.5:3b **en local via Ollama**, aucune API externe.
    Sortie JSON contrainte et validée contre un schéma, puis garde-fou : un
    élément dont l'extrait est introuvable dans les notes passe en `to_verify`
    s'il est retrouvé en partie (60 % de ses mots dans une phrase), sinon il est
    écarté. Si Ollama ne répond pas, dépasse le délai ou renvoie un JSON
    invalide : retour automatique à `rules_v1`, signalé dans `summary.engine`
    (`requested`, `used`, `fallback_reason`) et `generated_by`.
  - `opportunity_decision` : `confirmed` si objectifs et besoin réel sont
    `confirmed`, sinon `to_qualify` ; jamais `discarded` automatiquement.
  - `internal_teams` (section 2.4) : `application` si une contrainte technique
    est notée ; `creation` si l'opportunité demande un nouvel arôme et qu'un
    objectif ou un besoin est noté ; `marketing` si un objectif est noté et que
    l'opportunité a un signal de marché ; `regulatory` si un mot réglementaire
    est dans les notes ou si l'opportunité a un signal réglementaire.
  - `Meeting.next_actions` reprend les textes de `summary.next_actions`.

  Un point de checklist inconnu, une date invalide ou un `mode` inconnu
  renvoie `422`.

### Ollama (mode `llm_v2`)

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `OLLAMA_URL` | `http://localhost:11434` | Adresse de l'Ollama local (sur le poste de dev, 11434 répond ; rien n'écoute sur 11435) |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Modèle (`ollama pull qwen2.5:3b`, environ 1,9 Go) |
| `OLLAMA_TIMEOUT` | `120` | Délai maximum d'un appel, en secondes |

Sur le poste de dev (CPU), un compte rendu llm_v2 prend de 14 à 76 s (43 s en moyenne sur 30 cas). Résultats
comparés des deux modes sur 30 cas : `data/cas_test/resultats_v1_v2.md`.

Un id inconnu renvoie `404` avec un message (ex. `Client inconnu : C-99`).
CORS est ouvert à toutes les origines pour l'app front.

Exemple :

```bash
curl -X POST http://localhost:8001/questions -H "Content-Type: application/json" \
  -d '{"champs_manquants": ["brief.echeance_lancement", "brief.contraintes.regime"], "opportunite_id": "OPP-06"}'
```

## Tests

```bash
pytest data/tests/test_api.py data/tests/test_api_v2.py data/tests/test_compte_rendu.py
```

## Limites

- Démo uniquement : pas d'authentification, CORS ouvert, données fictives.
- Les JSON sont lus au démarrage : relancer l'API après `generer_demo.py` ou
  `generer_demo_v2.py` (ou lancer avec `--reload`).
- Synthèse, justification et compte rendu rules_v1 sont des modèles de texte :
  ils reformulent les données, ils n'en inventent pas. En llm_v2, le garde-fou
  écarte ou marque `to_verify` ce qui n'est pas dans les notes, mais
  l'attribution d'une phrase à un point peut être fausse (voir le banc d'essai).
