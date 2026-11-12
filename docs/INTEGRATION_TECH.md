# Intégration DATA → TECH

Ce qu'il faut savoir pour brancher l'app sur les données et l'API de la démo v2.
Référence complète des champs : [MODELE_DONNEES.md](../data/demo_v2/MODELE_DONNEES.md).

## Changements à reprendre côté TECH

1. **MeetingReport en rubriques séparées** (DATA-US11). `Meeting.summary` n'est
   plus un texte : c'est un objet avec les rubriques `needs`,
   `technical_constraints`, `budget_constraints`, `timeline`,
   `missing_information`, `next_actions` et `internal_teams`.
   - Chaque rubrique est une liste d'éléments
     `{point, text, status, excerpt}`, plus `team` dans `internal_teams`.
   - `status` vaut `confirmed` (dit dans les notes) ou `to_verify` (déduit,
     hésitant ou contradictoire). À afficher différemment.
   - `excerpt` est le passage exact des notes. Il vaut `null` pour un élément
     déduit et n'est jamais `null` si l'élément est `confirmed`.
   - Nouveau champ `engine` : `{requested, used, model, fallback_reason, guard}`.
     Si `requested` ≠ `used`, llm_v2 est retombé sur rules_v1 : afficher
     `fallback_reason`.
   - Autres champs du compte rendu : `opportunity_decision`
     (`confirmed` / `to_qualify` / `discarded`), `decision_reason`,
     `generated_by` et `validated`.
2. **Nouveaux champs d'opportunité** (DATA-US08, DATA-US09) :
   - `priority_max` : priorité si les critères inconnus prennent leur valeur
     haute ;
   - `priority_status` : `stable` ou `provisional`. Si la priorité est
     provisoire, afficher par exemple « moyenne à haute » ;
   - `missing_criteria` : liste parmi `estimated_potential`, `feasibility` et
     `complexity` ;
   - `justification` : objet structuré, avec les rubriques `client_need`,
     `why_now`, `value_for_givaudan`, `internal_teams`, `facts`, `hypotheses`,
     `to_confirm` et `risks`. Chaque phrase s'écrit
     `{text, evidence_type, sources}`.
3. **`complexity` peut valoir `to_confirm`** (complexité inconnue), comme
   `feasibility`. Un enum à quatre valeurs : `low`, `medium`, `high`,
   `to_confirm`.

## Emplacement des fichiers

| Fichier | Contenu |
| --- | --- |
| [data/demo_v2/clients.json](../data/demo_v2/clients.json) | 3 clients fictifs |
| [data/demo_v2/projects.json](../data/demo_v2/projects.json) | 7 projets |
| [data/demo_v2/opportunities.json](../data/demo_v2/opportunities.json) | 6 opportunités détectées par règles, avec priorité et justification |
| [data/demo_v2/signals.json](../data/demo_v2/signals.json) | 11 signaux (client et marché) |
| [data/demo_v2/meetings.json](../data/demo_v2/meetings.json) | 2 rendez-vous terminés, compte rendu rules_v1 |
| [data/demo_v2/meeting_context.json](../data/demo_v2/meeting_context.json) | Préparation du rendez-vous par opportunité (connu, manquant, questions) |
| [data/demo_v2/MODELE_DONNEES.md](../data/demo_v2/MODELE_DONNEES.md) | Modèle de données : champs, enums, règles |
| [data/api/main.py](../data/api/main.py) | API FastAPI ([README](../data/api/README.md)) |
| [data/demo_v2/compte_rendu.py](../data/demo_v2/compte_rendu.py) | Moteurs du compte rendu (rules_v1, llm_v2) |
| [data/verifier_jeu.py](../data/verifier_jeu.py) | Contrôle d'ensemble du jeu (`python data/verifier_jeu.py`) |

Les JSON sont générés par
[generer_demo_v2.py](../data/demo_v2/generer_demo_v2.py) : ne pas les modifier
à la main.

## Lancer l'API

Depuis la racine du dépôt (Python 3.11) :

```bash
pip install -r requirements.txt
uvicorn --app-dir data/api main:app --port 8001 --reload
# documentation interactive : http://localhost:8001/docs
pytest data/tests   # toute la suite
```

Les compteurs (`active_projects`, `to_qualify`, `last_signal_date`…) ne sont
pas stockés : l'API les calcule à chaque lecture.

## Routes /v2

Les exemples ci-dessous sont de vraies réponses de l'API, raccourcies (`…`).

**`GET /v2/dashboard`**

```json
{"followed_clients": 3, "detected_opportunities": 6, "to_qualify": 2, "meetings_to_prepare": 0}
```

**`GET /v2/clients?q=nova`** : liste des clients, avec une recherche par nom
optionnelle.

```json
[{"id": "C-01", "name": "Maison Nova Drinks", "sector": "Boissons", "country": "France",
  "relationship_status": "strategic", "last_updated": "2026-11-05",
  "active_projects": 3, "detected_opportunities": 2, "to_qualify": 1, "…": "…"}]
```

**`GET /v2/clients/{id}`** : fiche client, avec `projects`, `opportunities`,
`timeline` et `summary`.

```json
{"id": "C-01", "name": "Maison Nova Drinks", "…": "…",
 "projects": [{"id": "P-01", "status": "active", "start_date": "2026-10-10", "…": "…"}],
 "opportunities": [{"id": "O-01", "priority": "medium", "priority_status": "provisional", "…": "…"}],
 "timeline": [{"date": "2026-11-05", "type": "signal", "ref": "S-01",
               "event": "Compte rendu de l'échange commercial du 05/11/2026 : …"}],
 "summary": "…"}
```

**`GET /v2/opportunities/{id}`** : opportunité, avec le client, les signaux
complets, la justification et `last_signal_date`.

```json
{"id": "O-01", "title": "Nouvelle gamme de boissons fonctionnelles", "status": "to_qualify",
 "priority": "medium", "priority_max": "high", "priority_status": "provisional",
 "missing_criteria": ["feasibility"], "estimated_potential": "high",
 "feasibility": "to_confirm", "complexity": "high",
 "justification": {
   "client_need": [{"text": "Compte rendu de l'échange commercial du 05/11/2026 : …",
                    "evidence_type": "fact", "sources": ["S-01"]}],
   "why_now": ["…"], "value_for_givaudan": ["…"], "internal_teams": ["application", "creation", "marketing"],
   "facts": ["…"], "hypotheses": ["…"], "to_confirm": ["…"], "risks": ["…"]},
 "last_signal_date": "2026-11-05", "client": {"…": "…"}, "signals": ["…"]}
```

**`GET /v2/opportunities/{id}/meeting`** : préparation du rendez-vous, avec
`known`, `missing`, les questions et la checklist.

```json
{"client": {"id": "C-01", "name": "Maison Nova Drinks"},
 "opportunity": {"id": "O-01", "title": "Nouvelle gamme de boissons fonctionnelles", "status": "to_qualify"},
 "objective": "Comprendre les intentions du client …",
 "known": [], "missing": [{"point": "client_objectives", "label": "Objectifs du client"}, "…"],
 "questions": [{"id": "Q-01", "opportunity_id": "O-01",
                "question": "Quels nouveaux segments de boissons envisagez-vous de développer dans les prochains mois ?",
                "information_sought": "client_objectives",
                "opportunity_link": "Opportunité « Nouvelle gamme de boissons fonctionnelles » (O-01) : …",
                "origin": "banque de questions"}, "…"],
 "checklist": ["…"]}
```

**`POST /v2/meetings/report?mode=rules_v1`** : renvoie un Meeting, sans
l'enregistrer, dont `summary` est le MeetingReport.

Corps de la requête :

```json
{"opportunity_id": "O-01", "collected_points": ["timeline"], "answers": [],
 "notes": "Le client veut lancer une boisson fonctionnelle. Lancement peut-être en mars 2027."}
```

Réponse (raccourcie) :

```json
{"id": "M-03", "client_id": "C-01", "opportunity_id": "O-01", "status": "completed", "…": "…",
 "summary": {
   "needs": [{"point": "client_objectives", "text": "Objectifs du client : Le client veut lancer une boisson fonctionnelle.",
              "status": "confirmed", "excerpt": "Le client veut lancer une boisson fonctionnelle."}],
   "technical_constraints": [], "budget_constraints": [],
   "timeline": [{"point": "timeline", "text": "Calendrier : Lancement peut-être en mars 2027.",
                 "status": "to_verify", "excerpt": "Lancement peut-être en mars 2027."}],
   "missing_information": [{"point": "real_need", "text": "Besoin réel", "status": "to_verify", "excerpt": null}, "…"],
   "next_actions": [{"point": "timeline", "text": "Vérifier auprès du client : Lancement peut-être en mars 2027.",
                     "status": "to_verify", "excerpt": "Lancement peut-être en mars 2027."}],
   "internal_teams": [{"point": null, "team": "creation", "status": "to_verify", "text": "Création : …", "excerpt": "…"}],
   "opportunity_decision": "to_qualify", "decision_reason": "Pas encore confirmé dans les notes : besoin réel. …",
   "generated_by": "rules_v1",
   "engine": {"requested": "rules_v1", "used": "rules_v1", "model": null, "fallback_reason": null, "guard": null},
   "validated": false},
 "next_actions": ["Vérifier auprès du client : Lancement peut-être en mars 2027."]}
```

Un id inconnu renvoie `404`. Un point de checklist inconnu, une date invalide
ou un `mode` inconnu renvoie `422`.

## Modes rules_v1 / llm_v2

- **`rules_v1`** (défaut, recommandé pour la démo) : règles par mots-clés,
  sans LLM, instantané. Une hésitation (« peut-être », « à confirmer »…) ou
  deux dates différentes passent l'élément en `to_verify`.
- **`llm_v2`** (expérimental) : qwen2.5:3b **en local via Ollama**, aucune API
  externe. Il faut d'abord lancer `ollama pull qwen2.5:3b` puis laisser
  Ollama tourner sur `http://localhost:11434`. Variables d'environnement :
  `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` (120 s par défaut).
  - Un garde-fou écarte ce qui est introuvable dans les notes.
  - Si Ollama est absent, trop lent ou renvoie un JSON invalide, l'API
    revient automatiquement à rules_v1, ce qui se voit dans `engine`.
  - Environ 43 s par compte rendu sur CPU.
  - Erreurs d'attribution possibles : voir
    [resultats_v1_v2.md](../data/cas_test/resultats_v1_v2.md).

## Ce qui est fictif, ce qui est réel

- **Fictif** :
  - les clients, projets, opportunités et rendez-vous ;
  - les signaux client (`is_real_source: false`) ;
  - les 30 cas de test de [data/cas_test](../data/cas_test/README.md).

  Les noms sont inventés, `account_manager` est un rôle et non une personne.
  Il n'y a aucun montant en euros, aucune donnée personnelle et aucun lien
  avec de vrais clients de Givaudan.
- **Réel** : les 5 signaux de marché `is_real_source: true`, chacun avec sa
  `source_ref` :
  - Open Food Facts (ODbL 1.0) ;
  - INSEE, indice du sucre (Licence Ouverte 2.0, « Source : Insee ») ;
  - Commission européenne, EU Food Flavourings (CC BY 4.0) ;
  - rapport intégré Givaudan 2025 (citation courte avec page).

  Détail des sources et des licences :
  [README_sources.md](../data/sources/README_sources.md) et
  [demo_v2/README.md](../data/demo_v2/README.md#attribution).
- **Calculé par règles** : la détection des opportunités, la priorité (grille
  de qualification), la justification, les questions et le compte rendu
  rules_v1. Rien n'est saisi à la main.
