# API IA Data

Lit les JSON de `donnees/` (jeu de données de Tech) et fait 3 choses.

| Route | Entrée | Sortie | Écran |
|---|---|---|---|
| `POST /questions` | `{"opportunity_id": "opp-1a", "model": "optionnel"}` | 3 questions `{question, objectif, information_recherchee}` | Préparation du rendez-vous |
| `GET /justification/{opportunity_id}` | – | `pourquoi`, `faits`, `hypotheses`, `a_confirmer`, `prochaine_action` | Détail de l'opportunité |
| `POST /compte-rendu` | `{"opportunity_id", "checklist": {...}, "notes": "..."}` | 8 rubriques, chaque élément `confirme` ou `a_verifier` | Compte rendu |
| `GET /health` | – | État de l'API et d'Ollama (sans clé) | – |
| `POST /answer` | `{"question": "..."}` | `{answer, model}` (compatibilité avec l'API Tech) | – |

Toutes les routes sauf `/health` exigent l'en-tête `X-API-Key`. Depuis un navigateur via ngrok, ajouter `ngrok-skip-browser-warning: true`.

Cases de la checklist : `objectifs_client`, `besoin_reel`, `contraintes_techniques`, `contraintes_budgetaires`, `calendrier`, `criteres_decision`.

## Champ `source`
| Valeur | Signification |
|---|---|
| `modele` | Réponse générée par Ollama |
| `simule` | Plan B : construit uniquement à partir des données (questions préparées par Data, règles) |
| `donnees` | Justification calculée à partir des signaux |

Le plan B s'active si Ollama est absent, dépasse `AI_TIMEOUT` secondes, ou renvoie une forme invalide. La démo ne plante donc jamais.

## Garanties
- Le modèle ne reçoit que les données de l'opportunité concernée, avec interdiction d'inventer.
- Ollama reçoit un schéma JSON qui impose la forme de la réponse (3 questions, catégories autorisées).
- Une hypothèse n'est jamais présentée comme un fait dans la justification.
- Les cases non cochées apparaissent toujours dans « informations manquantes » ; une note « budget non abordé » ne devient jamais un fait.

## Configuration (`.env`, voir `.env.example`)
| Variable | Rôle | Défaut |
|---|---|---|
| `API_KEY` | Clé exigée dans `X-API-Key` | obligatoire |
| `OLLAMA_URL` | Adresse d'Ollama | `http://localhost:11434` |
| `MODEL` | Modèle par défaut | `llama3.2:1b` |
| `AI_TIMEOUT` | Délai avant le plan B (secondes) | `30` |
| `DATA_DIR` | Dossier des JSON | `donnees/` |

Si Tech modifie ses JSON, remplacer les fichiers de `donnees/` et redémarrer.
