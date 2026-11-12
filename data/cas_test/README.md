# Cas de test du compte rendu

30 comptes rendus fictifs pour mesurer l'extraction de la checklist de
rendez-vous (Meeting Copilot). Bibliothèque standard uniquement, graine fixe.

| Fichier | Rôle |
| --- | --- |
| `generer_cas_test.py` | Génère les cas (graine 42, date de référence 2026-11-12) : 10 complets, 10 partiels, 5 avec un calendrier contradictoire, 5 hors sujet ; français et anglais |
| `sorties/interactions.csv` | 5 à 10 interactions datées par client ; seul le dernier compte rendu (`evalue = true`) est évalué |
| `sorties/verite_terrain.json` | Vérité terrain : points présents et manquants, contradiction, hors sujet |
| `extraire_v1.py` | Banc historique V1 : détection des points sur le texte entier (mots-clés de `data/demo_v2/compte_rendu.py`) ; écrit `sorties/predictions_v1.json` et `sorties/scores_v1.json` |
| `evaluer_v1_v2.py` | Banc DATA-US11 : moteurs de l'app `rules_v1` et `llm_v2` (qwen2.5:3b via Ollama local) sur les 30 cas ; écrit `resultats_v1_v2.json` et `resultats_v1_v2.md` |

```bash
python data/cas_test/generer_cas_test.py
python data/cas_test/extraire_v1.py
python data/cas_test/evaluer_v1_v2.py --delai 120   # environ 30 min sur CPU : Ollama doit tourner
python data/cas_test/evaluer_v1_v2.py --md-seulement   # réécrit le rapport depuis le JSON
```

Résultats et limites : [`resultats_v1_v2.md`](resultats_v1_v2.md).
