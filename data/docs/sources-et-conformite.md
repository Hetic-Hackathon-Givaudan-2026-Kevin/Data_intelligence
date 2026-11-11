# Sources de données et conformité

## Inventaire des sources
| Source | Méthode d'accès | Statut | Format | Qualité observée |
|---|---|---|---|---|
| Notes fictives « Boissons Altitude » | Écrites par l'équipe Data | Confirmé | .txt | Réalistes mais synthétiques ; 4 types de notes |
| Données réelles Givaudan | Non accessibles pendant le hackathon | Bloqué | - | - |

## Alternative
Jeu synthétique construit sur la structure d'un vrai brief ; à remplacer si des données réelles deviennent disponibles.

## Conformité (analyse d'équipe, pas un avis juridique)
- Aucun scraping : pas de CGU, robots.txt ni CAPTCHA concernés
- Aucune donnée personnelle réelle : noms et coordonnées fictifs
- Traitement local (Ollama) : pas de transfert externe
- Champ `donnees_personnelles_ecartees` dans le schéma
- Décision : **GO**
- Traçabilité : source, date de création, finalité (prototype), volume (N notes)

## Limites
- Données synthétiques : résultats non généralisables à des notes réelles
