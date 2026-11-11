# Sillage — partie Data (Givaudan AI Innovation Challenge, équipe G03, Défi 01)

MVP : transformer une note de RDV brute en brief structuré, fiable et vérifiable.

## Rôle de la partie Data
Construire et valider l'intelligence : extraction des briefs, contrôle, mesure de fiabilité.

## Arborescence
| Dossier | Contenu |
|---|---|
| `schema/` | `schema_brief_v1.json` : source de vérité du format de sortie |
| `extraction/` | Prompt, extraction LLM (Ollama), contrôle de forme, pipeline |
| `notes/` | Notes fictives (données synthétiques) |
| `eval/` | Annotations de référence et grille de fiabilité |
| `tests/` | Tests pytest |
| `docs/` | `CONTRAT.md` (explication du schéma pour Tech), `choix-approche.md` |

## Règle d'exécution
Tous les scripts se lancent depuis `data/` :
```bash
cd data
pip install -r requirements.txt
pytest
python extraction/pipeline.py
```
`sorties/` est généré par le pipeline et n'est pas versionné.

## Vision (hors MVP)
Préparation avant RDV et aide pendant le RDV : pistes écartées pour le prototype.

## Données
Fictives (pas d'accès aux données Givaudan). À remplacer si de vraies données arrivent.
