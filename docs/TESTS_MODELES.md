# Test des modèles Ollama – 12/11/2026

Test : `POST /questions` sur `opp-1a` (Maison Nova Drinks, nouvelle gamme de boissons fonctionnelles), PC portable sans carte graphique dédiée.

| Modèle | Durée | Forme respectée | Observation |
|---|---|---|---|
| `llama3.2:1b` | 27 s | Non | Questions mal rangées dans la réponse, catégories en liste |
| `qwen2.5:1.5b` | 45 s | Non | Bascule sur le plan B |
| `gemma2:2b` | 69 s | Oui | Questions correctes mais générales ; redemande le calendrier, partiellement connu |
| `llama3.2:3b` | 98 s | Non | Bascule sur le plan B |

Ces mesures ont été faites avant l'ajout du schéma JSON imposé à Ollama et de la lecture tolérante ; elles sont à refaire avec la version actuelle.

## Décision pour la démo
- Par défaut : questions préparées par Data et relues (plan B), réponse immédiate.
- En option : génération en direct avec `gemma2:2b` (`"model": "gemma2:2b"`, `AI_TIMEOUT=90`), en prévenant qu'elle prend environ une minute.

## Limites
- Petits modèles locaux : qualité et respect du format variables, temps de réponse long sur un PC sans carte graphique.
- Données fictives : les noms de marques réelles (PepsiCo, Danone, Nestlé…) viennent du jeu de données de Tech et ne correspondent à aucune information réelle.
- Le compte rendu simulé classe les phrases des notes par mots-clés : il ne comprend pas le sens.
- Les questions des fiches ont été générées par une IA et doivent être validées par un commercial senior.
