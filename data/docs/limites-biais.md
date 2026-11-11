# Limites et biais (brouillon, à compléter avec les résultats mesurés)

## 1. Données
| Limite | Conséquence | Statut |
|---|---|---|
| Notes **fictives**, écrites par l'équipe | Les performances mesurées ne garantissent rien sur de vraies notes de commerciaux | Certain |
| Un seul client fictif (Boissons Altitude), un seul secteur | Résultats non généralisables à d'autres clients ou métiers | Certain |
| Petit jeu de référence (N = ?) | Les scores ont une marge d'erreur large ; un cas change le score de plusieurs points | À chiffrer |
| Notes en français, style homogène | Pas de test sur notes bruitées (fautes, abréviations, langue mixte) | À vérifier |

## 2. Biais d'évaluation
| Biais | Risque | Parade |
|---|---|---|
| Mêmes personnes écrivent les notes **et** les JSON attendus | Le jeu de référence reflète leur façon de lire les notes | Faire relire une partie des annotations par une autre personne |
| Notes écrites pour ressembler au schéma | Extraction plus facile que dans la réalité | Inclure des cas pièges : `hors_sujet`, `incomplete`, contradictions, données personnelles |
| Réglage du prompt sur les 30 cas puis mesure sur les mêmes 30 | Score gonflé (sur-ajustement) | Réserver quelques cas jamais utilisés pour régler le prompt |

## 3. Modèle (LLM local)
- Variabilité : deux exécutions peuvent donner deux sorties différentes → mesurer sur plusieurs passes ou fixer la température.
- Risque d'**invention** : valeur renseignée alors que la note ne la contient pas (au lieu de « non renseigné »). C'est l'erreur la plus grave pour un commercial ; elle est mesurée séparément.
- Dépend du modèle choisi et de la machine (temps de réponse non garanti).

## 4. Schéma v1.0
- « non renseigné » mélange texte et nombre selon les champs (ex. budget) : à gérer côté Tech.
- `incertitudes.contradictions_detectees` peut diverger de `positions_contradictoires` : contrôlé par test.
- Pas de gestion des notes dans une autre langue.

## 5. Données personnelles et conformité
- Aucune donnée personnelle réelle dans le jeu. Le champ `donnees_personnelles_ecartees` indique si de telles données ont été écartées : son fonctionnement n'est testé que sur des cas fictifs.
- Avec de vraies notes : base légale, minimisation et durée de conservation à documenter avant tout usage (analyse d'équipe, pas un avis juridique).

## 6. Ce que les résultats permettent de conclure (et ce qu'ils ne permettent pas)
- ✅ Démontrent la faisabilité de l'extraction structurée sur des notes de ce type.
- ❌ Ne démontrent pas la performance sur des notes réelles ni sur d'autres clients.

## 7. Sources
- Notes fictives : écrites par l'équipe Data (voir `docs/sources-et-conformite.md`).
- Schéma : `data/schema/schema_brief_v1.json`.
- Mesures : `data/eval/` (à renseigner).
