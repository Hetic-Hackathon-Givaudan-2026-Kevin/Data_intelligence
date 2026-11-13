# Fiches clients fictives – Givaudan Opportunity Radar

**Équipe G03 · Data** · Document de travail · Novembre 2026

> **Données fictives.** Ces fiches servent uniquement aux tests et aux exercices du prototype. Les noms de marques connues sont utilisés à titre d'illustration : aucun chiffre, projet ou échange ne correspond à la réalité, ni chez Givaudan ni chez ces entreprises.

## Objet

Ce document répond à la consigne du formateur : définir un modèle standard de fiche client, rédiger un prompt qui permet à une IA de remplir la fiche et de générer 3 questions avant le premier appel, et centraliser 6 fiches complètes.

Les fiches reprennent le jeu de données de l'équipe Tech (fichiers `clients.json`, `projects.json`, `opportunities.json`, `signals.json`, `clients-insights.json`), pour que la démo et les exercices utilisent les mêmes informations. Les 6 clients retenus sont ceux du secteur alimentaire et boissons.

| # | Client | Secteur | Projets actifs | Opportunités | À qualifier |
|---|---|---|---|---|---|
| 1 | Maison Nova Drinks | Boissons | 3 | 2 | 1 |
| 2 | Nordic Food Industries | Agroalimentaire | 2 | 3 | 1 |
| 3 | Alimenta Distribution | Distribution alimentaire | 1 | 1 | 0 |
| 4 | PepsiCo | Boissons & Snacks | 4 | 3 | 2 |
| 5 | Danone | Produits laitiers | 2 | 1 | 1 |
| 6 | Nestlé | Nutrition | 3 | 2 | 1 |

## Modèle de fiche client

Chaque fiche suit la même structure, dans cet ordre. Le modèle technique (JSON) est fourni dans `modele_fiche_client.json`.

| Section | Contenu | Source |
|---|---|---|
| Identité | Nom, secteur, pays, responsable commercial, statut de la relation, date de mise à jour | `clients.json` |
| Indicateurs | Projets actifs, opportunités détectées, opportunités à qualifier | Calculés à partir des projets et opportunités |
| Ce qu'il faut savoir | Situation, besoins exprimés, signaux récents, points d'attention | `clients-insights.json` |
| Projets | Nom, description, date de début | `projects.json` |
| Opportunités et signaux | Statut, priorité, potentiel ; pour chaque signal : source, date, fiabilité, **fait ou hypothèse** | `opportunities.json`, `signals.json` |
| Historique | Événements datés | `clients-insights.json` |
| 3 questions préparatoires | Question, pourquoi, information recherchée, opportunité ou projet lié | Générées par IA avec le prompt ci-dessous, à relire par l'équipe |
| À confirmer | Tout ce qui est inconnu ou incertain | Déduit des données |

Règle commune : une information absente n'est jamais inventée, elle va dans « À confirmer ».

## Prompt destiné à l'IA

Un appel par client. On remplace `{{MODELE}}` par le modèle JSON et `{{DONNEES_CLIENT}}` par les données du client. Fichier complet : `prompt_fiche_client.md`.

**Message système**

```text
Tu es l'assistant d'un commercial de Givaudan (arômes et parfums). Tu prépares sa fiche client avant le premier appel.

RÈGLES STRICTES
1. Utilise UNIQUEMENT les données fournies. N'invente aucun chiffre, aucun nom, aucun fait.
2. Une information absente reste absente : écris-la dans "a_confirmer".
3. Distingue les faits des hypothèses. Un signal "hypothese" ne doit jamais être présenté comme un fait (« la veille suggère », pas « le client veut »).
4. Les données sont fictives : ne les présente jamais comme des informations réelles de Givaudan ou du client.
5. Réponds en français, en phrases courtes, compréhensibles par un commercial junior.
6. Réponds UNIQUEMENT avec un objet JSON valide qui respecte exactement le modèle fourni.
```

**Message utilisateur**

```text
TÂCHE
1. Remplis la fiche client en recopiant les données fournies dans le modèle (identite, indicateurs, synthese, historique, projets, opportunites avec leurs signaux).
   Calcule les indicateurs : projets au statut "actif", nombre d'opportunités, opportunités au statut "a_qualifier".
2. Rédige exactement 3 questions préparatoires à poser avant le premier appel. Chaque question :
   - est ouverte, en langage naturel, une seule idée par question ;
   - vise une information qui MANQUE dans les données (ne redemande pas ce qui est déjà connu, ni une question déjà posée dans un rendez-vous si la réponse est connue) ;
   - est liée à une opportunité ou à un projet du client (champ "lien" = son identifiant) ;
   - indique "pourquoi" elle est utile, en citant l'élément des données qui la justifie ;
   - indique l'"information_recherchee" parmi : Objectifs du client, Besoin réel, Contraintes techniques, Contraintes budgétaires, Calendrier, Critères de décision.
   Priorité : les opportunités "a_qualifier" et de priorité "haute", puis les hypothèses à vérifier. Varie les informations recherchées.
3. Liste dans "a_confirmer" tout ce qui reste inconnu ou incertain (faisabilité "a_confirmer", potentiel non renseigné, signaux "hypothese", points d'attention).
4. Dans "meta", mets "donnees": "fictives".

MODÈLE
{{MODELE}}

DONNÉES DU CLIENT
{{DONNEES_CLIENT}}
```

**Contrôle avant d'intégrer une fiche** : JSON valide, exactement 3 questions liées à un identifiant existant, aucune information absente des données, indicateurs égaux aux compteurs de `clients.json`, relecture humaine des questions.

# Les 6 fiches clients

## Maison Nova Drinks

| Secteur | Pays | Responsable commercial | Statut | Mise à jour |
|---|---|---|---|---|
| Boissons | France | Thomas Leroy | Client stratégique | 05/11/2026 |

Projets actifs : **3** · Opportunités détectées : **2** · À qualifier : **1**

### Ce qu'il faut savoir
Client stratégique avec trois projets actifs et un échange récent sur une nouvelle gamme.

- **Besoins exprimés** : Explorer une nouvelle catégorie de boissons ; Profils aromatiques naturels
- **Signaux récents** : Intérêt exprimé pour une nouvelle catégorie lors du dernier échange
- **Points d'attention** : Objectifs et contraintes de formulation à confirmer ; Opportunité sur la nouvelle gamme à qualifier

### Projets
| Projet | Description | Début |
|---|---|---|
| Boisson pétillante aux agrumes | Formulation d'une boisson pétillante au profil agrumes. | 10/10/2026 |
| Gamme de thés glacés | Arômes naturels pour une gamme de thés glacés. | 15/06/2026 |
| Sirop premium | Travail sur le profil aromatique d'un sirop haut de gamme. | 02/03/2026 |

### Opportunités et signaux
| Opportunité | Statut | Priorité | Potentiel | Signal (source, date, fiabilité) |
|---|---|---|---|---|
| Nouvelle gamme de boissons fonctionnelles | À qualifier | Haute | Élevée | Intérêt exprimé pour une nouvelle catégorie. (Compte rendu, 05/11/2026, Moyenne, **Fait**) |
| Extension d'une gamme aromatique | Détectée | Moyenne | Moyenne | Projet existant et évolution du portefeuille. (Historique, 10/10/2026, Moyenne, **Hypothèse**) |

### Historique
- 05/11/2026 : Échange commercial sur une nouvelle gamme
- 20/10/2026 : Envoi d'un échantillon
- 10/10/2026 : Projet de formulation lancé
- 18/09/2026 : Rendez-vous de cadrage sur l'évolution du portefeuille

### 3 questions préparatoires avant le premier appel
| # | Question | Pourquoi | Information recherchée |
|---|---|---|---|
| 1 | Pour cette nouvelle gamme de boissons fonctionnelles, quel bénéfice voulez-vous mettre en avant en priorité (énergie, détente, immunité…) ? | Le dernier échange confirme l'intérêt, mais pas le bénéfice visé : c'est la base du brief pour les équipes de création. | Besoin réel |
| 2 | Quel budget prévisionnel avez-vous prévu pour ce lancement ? | Le budget n'a pas été évoqué lors du rendez-vous du 05/11 ; sans lui, impossible de choisir entre une solution existante et un développement spécifique. | Contraintes budgétaires |
| 3 | Souhaitez-vous que vos prochains produits reprennent les profils naturels de vos thés glacés, ou partir sur une nouvelle signature aromatique ? | L'extension de gamme est une hypothèse tirée de l'historique : la question vérifie l'intérêt sans l'affirmer. | Objectifs du client |

### À confirmer
- Faisabilité de « Nouvelle gamme de boissons fonctionnelles »
- Hypothèse à vérifier : Projet existant et évolution du portefeuille.
- Objectifs et contraintes de formulation à confirmer
- Opportunité sur la nouvelle gamme à qualifier

## Nordic Food Industries

| Secteur | Pays | Responsable commercial | Statut | Mise à jour |
|---|---|---|---|---|
| Agroalimentaire | Danemark | Marie Curie | Actif | 04/11/2026 |

Projets actifs : **2** · Opportunités détectées : **3** · À qualifier : **1**

### Ce qu'il faut savoir
Client actif avec deux projets en cours et plusieurs pistes d'amélioration identifiées.

- **Besoins exprimés** : Alternatives végétales ; Meilleure texture sur un produit existant
- **Signaux récents** : Demande récente sur les alternatives végétales ; Retour technique sur un projet précédent
- **Points d'attention** : Contrainte budgétaire déjà communiquée ; Faisabilité de la formulation végétale à confirmer

### Projets
| Projet | Description | Début |
|---|---|---|
| Sauce crémeuse | Amélioration de la texture d'une sauce crémeuse. | 12/05/2026 |
| Plat cuisiné | Optimisation de la recette d'un plat cuisiné. | 20/08/2026 |

### Opportunités et signaux
| Opportunité | Statut | Priorité | Potentiel | Signal (source, date, fiabilité) |
|---|---|---|---|---|
| Développement d'une formulation végétale | À qualifier | Haute | Élevée | Demande concernant des alternatives végétales. (Demande client, 04/11/2026, Haute, **Fait**) |
| Amélioration de la texture d'un produit | Détectée | Moyenne | Non renseigné | Retour technique sur un projet précédent. (Historique, 22/10/2026, Moyenne, **Fait**) |
| Optimisation d'une formulation existante | Détectée | Basse | Faible | Contrainte budgétaire communiquée. (Compte rendu, 09/10/2026, Haute, **Fait**) |

### Historique
- 04/11/2026 : Demande d'alternatives végétales reçue
- 22/10/2026 : Retour technique sur la texture d'un produit
- 09/10/2026 : Contrainte budgétaire communiquée en rendez-vous
- 20/08/2026 : Lancement du projet d'optimisation de recette

### 3 questions préparatoires avant le premier appel
| # | Question | Pourquoi | Information recherchée |
|---|---|---|---|
| 1 | Pour la formulation végétale, quels critères de goût et de texture sont non négociables pour vous ? | Le besoin végétal est confirmé sur deux produits, mais la faisabilité dépend de ces critères. | Contraintes techniques |
| 2 | Sur la sauce crémeuse, qu'est-ce qui ne vous a pas convenu dans la texture lors du dernier essai ? | Le retour technique du 22/10 existe, mais son contenu précis n'est pas documenté. | Besoin réel |
| 3 | Quel coût cible devons-nous respecter pour la revue de votre formulation existante ? | Une contrainte budgétaire a été communiquée le 09/10, sans montant : il faut un chiffre pour proposer une solution compatible. | Contraintes budgétaires |

### À confirmer
- Faisabilité de « Développement d'une formulation végétale »
- Potentiel de « Amélioration de la texture d'un produit » (non renseigné)
- Contrainte budgétaire déjà communiquée
- Faisabilité de la formulation végétale à confirmer

## Alimenta Distribution

| Secteur | Pays | Responsable commercial | Statut | Mise à jour |
|---|---|---|---|---|
| Distribution alimentaire | Espagne | Marc Lelièvre | Actif | 02/11/2026 |

Projets actifs : **1** · Opportunités détectées : **1** · À qualifier : **0**

### Ce qu'il faut savoir
Distributeur avec un projet actif et une première piste liée à une tendance de consommation.

- **Besoins exprimés** : Nouvelles références pour sa marque de distributeur
- **Signaux récents** : Tendance de consommation relevée par la veille marché
- **Points d'attention** : Signal à confirmer : il repose sur une veille et non sur une demande du client

### Projets
| Projet | Description | Début |
|---|---|---|
| Biscuits aromatisés marque distributeur | Gamme de biscuits aromatisés pour une marque de distributeur. | 14/09/2026 |

### Opportunités et signaux
| Opportunité | Statut | Priorité | Potentiel | Signal (source, date, fiabilité) |
|---|---|---|---|---|
| Nouvelle référence aromatique pour une marque de distributeur | Détectée | Moyenne | Moyenne | Tendance de consommation et demande potentielle. (Veille marché, 02/11/2026, Faible, **Hypothèse**) |

### Historique
- 02/11/2026 : Tendance de consommation relevée par la veille marché
- 15/10/2026 : Point de suivi sur le projet de gamme
- 14/09/2026 : Lancement du projet de marque distributeur

### 3 questions préparatoires avant le premier appel
| # | Question | Pourquoi | Information recherchée |
|---|---|---|---|
| 1 | Quelles nouvelles saveurs vos clients en magasin vous demandent-ils le plus en ce moment ? | L'opportunité repose sur une veille de marché, pas sur une demande du client : la question vérifie si le besoin existe vraiment. | Besoin réel |
| 2 | Quel prix de vente visez-vous pour une nouvelle référence de votre marque distributeur ? | Le prix cible a été demandé le 02/11, sans réponse : il conditionne le choix de l'arôme. | Contraintes budgétaires |
| 3 | Qui décide du lancement d'une nouvelle référence chez vous, et selon quels critères ? | Aucune information sur le processus de décision du distributeur. | Critères de décision |

### À confirmer
- Faisabilité de « Nouvelle référence aromatique pour une marque de distributeur »
- Hypothèse à vérifier : Tendance de consommation et demande potentielle.
- Signal à confirmer : il repose sur une veille et non sur une demande du client

## PepsiCo

| Secteur | Pays | Responsable commercial | Statut | Mise à jour |
|---|---|---|---|---|
| Boissons & Snacks | États-Unis | Thomas Leroy | Client stratégique | 01/11/2026 |

Projets actifs : **4** · Opportunités détectées : **3** · À qualifier : **2**

### Ce qu'il faut savoir
Client stratégique avec quatre projets actifs, centrés sur la réduction du sucre et du sel.

- **Besoins exprimés** : Réduire le sucre sans dégrader le goût ; Réduire le sel sur les snacks
- **Signaux récents** : Objectif de réduction du sucre évoqué récemment ; Demande d'étude sur la réduction du sel
- **Points d'attention** : Objectifs de réduction à confirmer avec le client ; Deux opportunités à qualifier

### Projets
| Projet | Description | Début |
|---|---|---|
| Boisson énergisante | Travail sur le profil aromatique d'une boisson énergisante. | 06/04/2026 |
| Snack salé | Exhausteur de goût pour un snack salé. | 18/05/2026 |
| Boisson zéro sucre | Masquage de l'amertume d'une boisson sans sucre. | 13/07/2026 |
| Gamme de chips à teneur réduite en sel | Arômes pour une gamme de chips moins salée. | 07/09/2026 |

### Opportunités et signaux
| Opportunité | Statut | Priorité | Potentiel | Signal (source, date, fiabilité) |
|---|---|---|---|---|
| Réduction du sucre sur une gamme de boissons | À qualifier | Haute | Élevée | Objectif de réduction du sucre évoqué lors du dernier échange. (Compte rendu, 01/11/2026, Haute, **Fait**) |
| Snacks à teneur réduite en sel | À qualifier | Moyenne | Moyenne | Demande d'étude sur la réduction du sel. (Demande client, 14/10/2026, Moyenne, **Fait**) |
| Nouvelle saveur saisonnière pour une boisson | Détectée | Basse | Faible | Tendance aux saveurs saisonnières observée sur le marché. (Veille marché, 05/10/2026, Faible, **Hypothèse**) |

### Historique
- 01/11/2026 : Échange sur la réduction du sucre d'une gamme de boissons
- 14/10/2026 : Demande d'étude sur la réduction du sel
- 07/09/2026 : Lancement du projet de chips à teneur réduite en sel
- 13/07/2026 : Début du projet de boisson zéro sucre

### 3 questions préparatoires avant le premier appel
| # | Question | Pourquoi | Information recherchée |
|---|---|---|---|
| 1 | Quel taux de réduction du sucre visez-vous, et sur quelles boissons en priorité ? | L'intention est confirmée depuis le 01/11, mais l'objectif chiffré reste à obtenir. | Objectifs du client |
| 2 | Comment allez-vous valider que le goût reste acceptable après la réduction (tests consommateurs, panel interne) ? | Le critère de réussite conditionne le niveau de complexité technique du projet. | Critères de décision |
| 3 | Pour vos snacks, quel niveau de réduction du sel attendez-vous, et pour quelle échéance ? | La demande d'étude du 14/10 ne précise ni l'objectif ni le calendrier. | Calendrier |

### À confirmer
- Faisabilité de « Réduction du sucre sur une gamme de boissons »
- Hypothèse à vérifier : Tendance aux saveurs saisonnières observée sur le marché.
- Objectifs de réduction à confirmer avec le client
- Deux opportunités à qualifier

## Danone

| Secteur | Pays | Responsable commercial | Statut | Mise à jour |
|---|---|---|---|---|
| Produits laitiers | France | Claire Moreau | Actif | 30/10/2026 |

Projets actifs : **2** · Opportunités détectées : **1** · À qualifier : **1**

### Ce qu'il faut savoir
Client actif avec deux projets en cours et une question récente sur le végétal.

- **Besoins exprimés** : Profils aromatiques adaptés aux produits laitiers ; Premières réflexions sur le végétal
- **Signaux récents** : Question récente sur les alternatives végétales
- **Points d'attention** : Besoin végétal à qualifier avant toute proposition

### Projets
| Projet | Description | Début |
|---|---|---|
| Dessert lacté | Profil vanille pour un dessert lacté. | 08/06/2026 |
| Yaourt à boire | Arôme fruits rouges pour un yaourt à boire. | 21/09/2026 |

### Opportunités et signaux
| Opportunité | Statut | Priorité | Potentiel | Signal (source, date, fiabilité) |
|---|---|---|---|---|
| Alternative végétale à un produit laitier | À qualifier | Haute | Élevée | Question posée sur les alternatives végétales. (Demande client, 30/10/2026, Moyenne, **Fait**) |

### Historique
- 30/10/2026 : Question du client sur les alternatives végétales
- 08/10/2026 : Retour sur l'échantillon d'arôme fruits rouges
- 21/09/2026 : Lancement du projet de yaourt à boire

### 3 questions préparatoires avant le premier appel
| # | Question | Pourquoi | Information recherchée |
|---|---|---|---|
| 1 | Si vous lanciez une première référence végétale, sur quel produit de votre gamme commenceriez-vous ? | L'intérêt est exploratoire et aucun projet n'est défini : il faut un point de départ concret. | Besoin réel |
| 2 | Qu'est-ce qui vous retient aujourd'hui de lancer un projet végétal (goût, texture, coût, demande des consommateurs) ? | Identifier le frein principal permet de savoir où Givaudan peut aider. | Contraintes techniques |
| 3 | Votre retour sur l'échantillon d'arôme fruits rouges du yaourt à boire est-il positif, et que faudrait-il ajuster ? | Un retour sur l'échantillon a eu lieu le 08/10, mais son contenu n'est pas documenté ; le projet en cours conditionne la relation. | Objectifs du client |

### À confirmer
- Faisabilité de « Alternative végétale à un produit laitier »
- Besoin végétal à qualifier avant toute proposition

## Nestlé

| Secteur | Pays | Responsable commercial | Statut | Mise à jour |
|---|---|---|---|---|
| Nutrition | Suisse | Pierre Martin | Actif | 28/10/2026 |

Projets actifs : **3** · Opportunités détectées : **2** · À qualifier : **1**

### Ce qu'il faut savoir
Client actif avec trois projets dans le domaine de la nutrition.

- **Besoins exprimés** : Masquer l'amertume des protéines ; Profils de goût adaptés à la nutrition
- **Signaux récents** : Retour technique récent sur l'amertume d'une boisson
- **Points d'attention** : Contraintes techniques de la formulation à confirmer

### Projets
| Projet | Description | Début |
|---|---|---|
| Boisson nutritionnelle | Masquage de goût pour une boisson nutritionnelle. | 23/03/2026 |
| Barre protéinée | Profil chocolat pour une barre protéinée. | 29/06/2026 |
| Céréales infantiles | Arôme vanille pour des céréales infantiles. | 02/09/2026 |

### Opportunités et signaux
| Opportunité | Statut | Priorité | Potentiel | Signal (source, date, fiabilité) |
|---|---|---|---|---|
| Masquage d'amertume sur une boisson enrichie en protéines | À qualifier | Haute | Élevée | Retour technique sur l'amertume d'une boisson. (Projet, 28/10/2026, Haute, **Fait**) |
| Extension de la gamme de barres protéinées | Détectée | Moyenne | Moyenne | Intérêt pour de nouveaux goûts exprimé en suivi de projet. (Compte rendu, 12/10/2026, Moyenne, **Hypothèse**) |

### Historique
- 28/10/2026 : Retour technique sur l'amertume de la boisson nutritionnelle
- 12/10/2026 : Point de suivi du projet de barre protéinée
- 02/09/2026 : Lancement du projet de céréales infantiles

### 3 questions préparatoires avant le premier appel
| # | Question | Pourquoi | Information recherchée |
|---|---|---|---|
| 1 | Quelles contraintes d'étiquetage devons-nous respecter pour masquer l'amertume de la boisson protéinée (arômes naturels uniquement, allergènes) ? | Le besoin est confirmé sur une protéine de pois ; il manque les contraintes réglementaires de la formulation. | Contraintes techniques |
| 2 | À quelle date souhaitez-vous disposer de la version reformulée de la boisson ? | Aucun calendrier n'est connu pour cette opportunité à priorité haute. | Calendrier |
| 3 | Quels nouveaux profils de goût envisagez-vous pour élargir votre gamme de barres protéinées ? | L'intérêt pour de nouveaux goûts est une hypothèse issue d'un suivi de projet : la question le vérifie. | Objectifs du client |

### À confirmer
- Hypothèse à vérifier : Intérêt pour de nouveaux goûts exprimé en suivi de projet.
- Contraintes techniques de la formulation à confirmer

# Limites

- Les questions ont été générées par une IA (Claude) avec le prompt ci-dessus. Elles doivent être relues par l'équipe Data, puis validées par un commercial senior.
- Les fiches dépendent du jeu de données de Tech : si Tech le modifie, il faut régénérer les fiches (`python build_fiches.py`, depuis `fiches_clients/`).
- Les noms de marques réelles (PepsiCo, Danone, Nestlé) peuvent prêter à confusion. Alternative : les remplacer par des noms fictifs, d'un commun accord avec Tech.
