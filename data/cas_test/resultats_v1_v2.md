# Banc d'essai du compte rendu : rules_v1 contre llm_v2

Ticket DATA-US11. Généré par `python data/cas_test/evaluer_v1_v2.py` le 2026-11-12.

## Protocole

- **Cas** : les 30 comptes rendus évalués de `sorties/interactions.csv`, produits par `generer_cas_test.py` (graine 42, date de référence 2026-11-12) : 10 complets, 10 partiels, 5 avec deux dates de calendrier contradictoires, 5 hors sujet. Moitié français, moitié anglais. Fictifs.
- **Vérité terrain** : `sorties/verite_terrain.json`, points de la checklist présents ou manquants par cas.
- **Moteurs** : ceux de l'app, `data/demo_v2/compte_rendu.py`. rules_v1 : mots-clés phrase par phrase. llm_v2 : qwen2.5:3b via Ollama local (http://localhost:11434), température 0, graine 42, JSON contraint par schéma, puis garde-fou. Délai maximum : 120.0 s par cas ; au-delà, retour à rules_v1 compté comme dépassement.
- **Rubriques** : précision et rappel au niveau (cas, point). Besoins = objectifs, besoin réel, critères de décision. Informations manquantes = points absents des éléments, comparés aux points manquants de la vérité terrain.
- **Éléments inventés** : extrait introuvable dans les notes (avant garde-fou pour llm_v2, et en sortie) ; et, à part, éléments attribués à un point absent de la vérité terrain.
- **Justesse confirmed / to_verify** : sur les points bien trouvés ; attendu to_verify pour le calendrier des 5 cas à contradiction, confirmed ailleurs (les cas ne contiennent pas d'autre hésitation).
- **Machine** : poste local, CPU, Ollama Windows.

## Résultats

| Rubrique | Précision V1 | Rappel V1 | Précision V2 | Rappel V2 |
|---|---|---|---|---|
| Besoins (objectifs, besoin réel, critères) | 1.00 | 1.00 | 0.70 | 0.83 |
| Contraintes techniques | 1.00 | 1.00 | 0.78 | 0.95 |
| Contraintes budgétaires | 1.00 | 1.00 | 0.85 | 0.94 |
| Calendrier | 1.00 | 1.00 | 0.90 | 0.85 |
| Informations manquantes | 1.00 | 1.00 | 0.74 | 0.58 |
| Total (rubriques extraites) | 1.00 | 1.00 | 0.77 | 0.87 |

| Indicateur | rules_v1 | llm_v2 |
|---|---|---|
| Éléments produits (après garde-fou) | 123 | 126 |
| Extraits inventés avant garde-fou (introuvables dans les notes) | 0 | 25 / 151 (0.17) |
| Passés en to_verify par le garde-fou (retrouvés en partie) | — | 2 |
| Extraits inventés dans la sortie finale | 0 | 0 |
| Éléments sur un point absent de la vérité terrain | 0 (0.00) | 29 (0.23) |
| Notes hors sujet avec au moins un élément (sur 5) | 0 | 2 |
| Justesse confirmed / to_verify | 111/111 (1.00) | 93/97 (0.96) |
| Retours à rules_v1 | — | 0 |
| dont dépassements du délai (120.0 s) | — | 0 |
| Temps moyen par cas | 0.0 s | 43.15 s (max 75.9 s) |

Les cas qui retombent sur rules_v1 sont comptés avec la sortie de rules_v1 dans les métriques de llm_v2 : c'est ce que verrait l'utilisateur.

## Limites

- **Cas synthétiques** : les comptes rendus sont produits par un générateur à phrases types. Les mots-clés de rules_v1 sont génériques mais ce vocabulaire leur est favorable ; de vraies notes (abréviations, fautes, phrases longues mêlant plusieurs points) seraient plus dures pour rules_v1.
- **30 cas seulement** : un écart de 1 ou 2 éléments change les taux de plusieurs points.
- **Statut** : la vérité terrain ne porte un to_verify que sur le calendrier contradictoire ; l'hésitation (« peut-être », « à confirmer ») n'est pas présente dans les cas et n'est donc pas mesurée ici.
- **Prochaines actions et équipes** : déduites par les mêmes règles dans les deux modes à partir des éléments extraits ; elles n'ont pas de vérité terrain et ne sont pas évaluées.
- **Prompt** : écrit une fois, de façon générique, sans réglage sur ces 30 cas.
- **Reproductibilité** : température 0 et graine fixe, mais un LLM sur CPU peut varier légèrement d'une machine à l'autre ; les temps dépendent de la machine.
- **Notes hors sujet en llm_v2** : sur 2 des 5 notes hors sujet (suivi de livraison), le modèle colle le même extrait sur tous les points de la checklist, en `confirmed`. Le garde-fou ne le détecte pas : l'extrait existe bien dans les notes, c'est son attribution aux points qui est fausse.

## Prochaine étape

- Règle de garde-fou à tester : **un même extrait attribué à plus de 2 points passe en `to_verify`**. Elle devra être évaluée sur de nouveaux cas, pas sur ces 30 : régler le moteur sur le banc qui sert à l'évaluer fausserait la mesure.

## Conclusion

- **rules_v1 reste le mode par défaut.**
- **llm_v2 est une option expérimentale** : 43 s par cas en moyenne sur ce poste, des erreurs d'attribution (éléments rangés sous un mauvais point, notes hors sujet remplies), et des résultats plus faibles sur les notes en anglais.
- Le sans-faute de rules_v1 vient en partie du vocabulaire du générateur de cas. Une comparaison honnête demandera des notes rédigées par des humains.
