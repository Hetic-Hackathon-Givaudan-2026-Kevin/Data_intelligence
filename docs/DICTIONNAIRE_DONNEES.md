# Dictionnaire de données – Opportunity Radar (G03)

Mission O4 · Ossama · Établi le 19/11/2026 à partir de `data/demo_v2/MODELE_DONNEES.md` et des fichiers de `data/demo_v2/`.

But : que Tech, le Product et la Data donnent le même sens au même mot. Les exemples viennent du jeu de démo ou de `MODELE_DONNEES.md` (données fictives).

## Lire ce document

- **Type :** texte, nombre, date (AAAA-MM-JJ), oui/non, liste, objet. « Texte (liste fermée) » veut dire que seules certaines valeurs sont permises ; elles sont données dans la colonne « Ce qu'il veut dire ».
- **Obligatoire :** « oui » = le champ est toujours présent. « Oui, peut être vide » = toujours présent, mais il peut valoir `null` ou une liste vide.
- **D'où il viendrait demain :** **hypothèse de travail, à confirmer avec l'équipe.** Le document de missions ne définit pas les trois outils de Givaudan. D'après ses tableaux de KPI, **Salesforce** est le CRM (clients, opportunités, rendez-vous) et **Pegasus** gère les briefs et les projets. Aucune ligne n'est attribuée à **Atlas** : son contenu est à confirmer. Deux autres origines sont possibles : « calculé par l'outil » (rien à importer) et « source publique » (Open Food Facts, INSEE, Union européenne).
- **Donnée personnelle :** « oui » si le champ contient, ou peut contenir, le nom d'une personne (voir `RGPD.md`).

## Les mots qui comptent

| Mot | Code dans les données | Ce qu'il veut dire |
|---|---|---|
| Projet | `Project` | Un travail **déjà engagé** avec le client |
| Opportunité | `Opportunity` | Un besoin possible, **pas encore engagé**. Jamais saisie à la main : elle est détectée à partir des signaux |
| Opportunité détectée | `status = detected` | L'outil a repéré une piste dans les signaux, mais le client n'a pas exprimé ce besoin lui-même |
| **Opportunité à qualifier** | `status = to_qualify` | Le client a exprimé ce besoin lui-même. Il reste à le qualifier au rendez-vous : objectifs, besoin réel, contraintes, budget, calendrier, critères de décision |
| Opportunité confirmée | `status = confirmed` | Objectifs et besoin réel confirmés dans les notes du rendez-vous, puis validés par le commercial |
| Signal | `Signal` | Une information datée qui justifie une opportunité. Signal client (propre à un client) ou signal de marché (public, propre à aucun client) |
| Fait / hypothèse / à confirmer | `fact` / `hypothesis` / `to_confirm` | Nature d'une information. Une hypothèse seule ne suffit jamais à créer une opportunité |
| Confirmé / à vérifier | `confirmed` / `to_verify` | Statut d'un élément du compte rendu : dit clairement dans les notes, ou déduit et incertain |
| Points de la checklist | `client_objectives`, `real_need`, `technical_constraints`, `budget_constraints`, `timeline`, `decision_criteria` | Les 6 informations à obtenir pendant le rendez-vous : objectifs du client, besoin réel, contraintes techniques, contraintes budgétaires, calendrier, critères de décision |

## 1. Clients

Fichier `clients.json`. Un client du portefeuille.

| Champ | Ce qu'il veut dire | Type | Exemple | Obligatoire | D'où il viendrait demain | Donnée personnelle |
|---|---|---|---|---|---|---|
| `id` | Identifiant du client : `C-` + 2 chiffres | Texte | `C-01` | Oui | Salesforce (identifiant du compte) | Non |
| `name` | Nom de l'entreprise cliente | Texte | `Maison Nova Drinks` | Oui | Salesforce | Non |
| `sector` | Secteur d'activité | Texte | `Boissons` | Oui | Salesforce | Non |
| `country` | Pays, en français | Texte | `France` | Oui | Salesforce | Non |
| `account_manager` | Responsable commercial du compte. Dans la démo : un rôle, jamais un nom | Texte | `KAM senior Boissons (fictif)` | Oui | Salesforce (propriétaire du compte) | **Oui** si c'est un nom de personne |
| `relationship_status` | Statut de la relation : `strategic` (stratégique), `active` (actif), `to_develop` (à développer) | Texte (liste fermée) | `strategic` | Oui | Salesforce | Non |
| `last_updated` | Date de la dernière mise à jour des informations du client | Date | `2026-11-05` | Oui | Salesforce | Non |
| `commercial_situation` | Situation commerciale, en 2 phrases au plus | Texte | `Client établi en croissance, avec plusieurs projets actifs. …` | Oui | Salesforce (saisi par le commercial) | Non |
| `history_summary` | Résumé de l'historique, en 2 ou 3 phrases | Texte | `Partenaire de longue date sur les arômes de ses boissons. …` | Oui | Salesforce (saisi par le commercial) | Non |

Les compteurs (projets actifs, opportunités détectées, à qualifier) ne sont pas stockés : l'API v2 les calcule (`active_projects`, `detected_opportunities`, `to_qualify`).

## 2. Projets

Fichier `projects.json`. Un travail déjà engagé avec le client.

| Champ | Ce qu'il veut dire | Type | Exemple | Obligatoire | D'où il viendrait demain | Donnée personnelle |
|---|---|---|---|---|---|---|
| `id` | Identifiant du projet : `P-` + 2 chiffres | Texte | `P-01` | Oui | Pegasus | Non |
| `client_id` | Client du projet (`id` d'un client) | Texte | `C-01` | Oui | Pegasus, relié au compte Salesforce | Non |
| `name` | Nom du projet, sans vrai nom de produit ni de marque | Texte | `Reformulation de l'arôme agrumes de la gamme existante` | Oui | Pegasus | Non |
| `description` | Description courte | Texte | `Travail en cours sur la gamme de boissons aromatisées existante : …` | Oui | Pegasus | Non |
| `status` | Statut : `active` (en cours) ou `completed` (terminé) | Texte (liste fermée) | `active` | Oui | Pegasus | Non |
| `start_date` | Date de début | Date | `2026-10-10` | Oui | Pegasus | Non |

## 3. Opportunités

Fichier `opportunities.json`. Un besoin possible, pas encore engagé.

| Champ | Ce qu'il veut dire | Type | Exemple | Obligatoire | D'où il viendrait demain | Donnée personnelle |
|---|---|---|---|---|---|---|
| `id` | Identifiant : `O-` + 2 chiffres | Texte | `O-01` | Oui | Calculé par l'outil (détection) | Non |
| `client_id` | Client concerné | Texte | `C-01` | Oui | Calculé par l'outil, à partir des signaux du client | Non |
| `title` | Intitulé de l'opportunité | Texte | `Nouvelle gamme de boissons fonctionnelles` | Oui | Calculé par l'outil (règle de détection) | Non |
| `description` | Explication brève | Texte | `Le client s'intéresse à une nouvelle catégorie, les boissons fonctionnelles : …` | Oui | Saisi par le commercial (Salesforce) | Non |
| `category` | Catégorie : `Nouvelle gamme`, `Extension de gamme`, `Nouvelle formulation`, `Amélioration produit`, `Optimisation`, `Nouvelle référence` | Texte | `Nouvelle gamme` | Oui | Calculé par l'outil (règle de détection) | Non |
| `status` | `detected` (détectée), `to_qualify` (à qualifier), `confirmed` (confirmée) : voir « Les mots qui comptent » | Texte (liste fermée) | `to_qualify` | Oui | Calculé par l'outil, puis mis à jour dans Salesforce une fois confirmée | Non |
| `priority` | Priorité : `high`, `medium`, `low`. Calculée par la grille de qualification ; si des critères sont inconnus, on prend leurs valeurs les plus basses | Texte (liste fermée) | `medium` | Oui | Calculé par l'outil | Non |
| `priority_max` | Priorité obtenue avec les valeurs les plus hautes des critères inconnus | Texte (liste fermée) | `high` | Oui | Calculé par l'outil | Non |
| `priority_status` | `stable` (la priorité ne changera pas) ou `provisional` (elle peut changer quand les critères inconnus seront connus) | Texte (liste fermée) | `provisional` | Oui | Calculé par l'outil | Non |
| `missing_criteria` | Critères encore inconnus, à vérifier au prochain rendez-vous : `estimated_potential`, `feasibility`, `complexity` | Liste | `["feasibility"]` | Oui, peut être vide | Calculé par l'outil | Non |
| `estimated_potential` | Potentiel indicatif : `low`, `medium`, `high`, ou `null` si inconnu. **Jamais un montant** | Texte (liste fermée) | `high` | Oui, peut être vide | Saisi par le commercial (Salesforce) | Non |
| `feasibility` | Faisabilité : `low`, `medium`, `high`, ou `to_confirm` si inconnue | Texte (liste fermée) | `to_confirm` | Oui | Saisi par le commercial (Salesforce) | Non |
| `complexity` | Complexité technique : `low`, `medium`, `high`, ou `to_confirm` si inconnue. Une complexité élevée fait baisser la priorité | Texte (liste fermée) | `high` | Oui | Saisi par le commercial (Salesforce) | Non |
| `next_action` | Prochaine action recommandée | Texte | `Organiser un échange avec le client afin de confirmer son intérêt …` | Oui | Saisi par le commercial (Salesforce) | Non |
| `justification` | Pourquoi l'opportunité est proposée (détail ci-dessous). Générée par règles, sans LLM | Objet | voir ci-dessous | Oui | Calculé par l'outil | Non |

**Détail de `justification`.** Chaque rubrique est une liste de phrases. Chaque phrase porte `text` (la phrase), `evidence_type` (`fact`, `hypothesis`, `to_confirm`) et `sources` (d'où elle vient, jamais vide).

| Rubrique | Ce qu'elle veut dire | Exemple de phrase |
|---|---|---|
| `client_need` | Besoin du client : ce qu'il a dit ou fait | `Compte rendu de l'échange commercial du 05/11/2026 : …` (source `S-01`) |
| `why_now` | Pourquoi maintenant : signal le plus récent, puis tendances de marché | `Signal le plus récent : compte rendu du 05/11/2026 (S-01).` |
| `value_for_givaudan` | Intérêt pour Givaudan : potentiel (un niveau, jamais un montant), statut de la relation, cadre réglementaire | `Valeur commerciale estimée : potentiel élevé (niveau, jamais un montant), …` |
| `internal_teams` | Équipes à mobiliser : `application`, `creation`, `marketing`, `regulatory` (liste de codes, pas de phrases) | `["application", "creation", "marketing"]` |
| `facts` | Faits | – |
| `hypotheses` | Hypothèses | – |
| `to_confirm` | Points à confirmer (statut non confirmé, critères inconnus, priorité provisoire) | – |
| `risks` | Risques (complexité, faisabilité, contraintes connues) | – |

## 4. Signaux

Fichier `signals.json`. Une information datée qui justifie une opportunité.

| Champ | Ce qu'il veut dire | Type | Exemple | Obligatoire | D'où il viendrait demain | Donnée personnelle |
|---|---|---|---|---|---|---|
| `id` | Identifiant : `S-` + 2 chiffres | Texte | `S-01` | Oui | Calculé par l'outil (à l'import) | Non |
| `opportunity_id` | Opportunité que le signal justifie. Rempli par la détection, jamais à la main | Texte | `O-01` | Oui | Calculé par l'outil | Non |
| `client_id` | Client dont parle le signal ; `null` pour un signal de marché | Texte | `C-01` | Oui, peut être vide | Salesforce ou Pegasus, selon le type de source | Non |
| `category` | Catégorie à laquelle se rattache un signal de marché ; `null` pour un signal client | Texte | `Nouvelle gamme` | Oui, peut être vide | Calculé par l'outil | Non |
| `description` | Ce que dit le signal | Texte | `Compte rendu de l'échange commercial du 05/11/2026 : le client exprime un intérêt …` | Oui | Salesforce (compte rendu, demande), Pegasus (historique de projet), ou source publique (marché) | **Oui, possible** : un compte rendu peut citer une personne |
| `source_type` | Type de source : `meeting_report` (compte rendu), `client_request` (demande du client), `project_history` (historique de projet), `market_trend` (tendance de marché), `commodity_price` (prix d'une matière première), `company_report` (rapport d'entreprise), `regulation` (règlement) | Texte (liste fermée) | `meeting_report` | Oui | Déduit de l'origine du signal | Non |
| `source_date` | Date de l'information ; pour une tendance, la fin de la période observée | Date | `2026-11-05` | Oui | Comme `description` | Non |
| `confidence` | Fiabilité : `low`, `medium`, `high` | Texte (liste fermée) | `high` | Oui | Calculé par l'outil, ou saisi par le commercial | Non |
| `evidence_type` | Nature : `fact` (fait), `hypothesis` (hypothèse), `to_confirm` (à confirmer) | Texte (liste fermée) | `fact` | Oui | Saisi par le commercial, ou calculé par l'outil | Non |
| `is_real_source` | La source existe-t-elle vraiment ? (`false` = inventée pour la démo) | Oui/non | `false` | Oui | Calculé par l'outil | Non |
| `source_ref` | Où retrouver la source : adresse web ou fichier. Peut être vide seulement si la source est inventée | Texte | `data/signaux/signaux_marche.json#OPP-01 (…)` | Oui, peut être vide | Lien vers la fiche Salesforce ou Pegasus, ou adresse de la source publique | Non |

## 5. Rendez-vous

Fichier `meetings.json`. Un rendez-vous commercial préparé avec le Meeting Copilot.

| Champ | Ce qu'il veut dire | Type | Exemple | Obligatoire | D'où il viendrait demain | Donnée personnelle |
|---|---|---|---|---|---|---|
| `id` | Identifiant : `M-` + 2 chiffres | Texte | `M-01` | Oui | Salesforce (événement) | Non |
| `client_id` | Client rencontré, le même que celui de l'opportunité | Texte | `C-01` | Oui | Salesforce | Non |
| `opportunity_id` | Opportunité dont on parle | Texte | `O-01` | Oui | Calculé par l'outil | Non |
| `date` | Date du rendez-vous | Date | `2026-11-10` | Oui | Salesforce (agenda) | Non |
| `status` | `planned` (prévu) ou `completed` (réalisé) | Texte (liste fermée) | `completed` | Oui | Salesforce | Non |
| `objective` | Objectif du rendez-vous | Texte | `Comprendre les intentions du client concernant le développement d'une nouvelle gamme …` | Oui | Calculé par l'outil, modifiable par le commercial | Non |
| `questions` | Les 3 questions suggérées (détail ci-dessous) | Liste d'objets | `[{"question": "Quels nouveaux segments de boissons envisagez-vous …", …}]` | Oui | Calculé par l'outil | Non |
| `answers` | Réponses obtenues, chacune reliée à un point de la checklist ; vide si le rendez-vous est prévu | Liste d'objets | `[{"information_sought": "timeline", "answer": "Premier test au printemps."}]` | Oui, peut être vide | Saisi par le commercial dans l'outil | **Oui, possible** |
| `collected_points` | Points de la checklist cochés pendant le rendez-vous ; vide s'il est prévu | Liste | `["client_objectives", "real_need", "technical_constraints", "timeline", "decision_criteria"]` | Oui, peut être vide | Saisi par le commercial dans l'outil | Non |
| `notes` | Notes libres du rendez-vous ; vides s'il est prévu | Texte | `Le client veut lancer deux boissons fonctionnelles sous sa propre marque. …` | Oui, peut être vide | Saisi par le commercial dans l'outil, puis copié dans Salesforce | **Oui, possible** : c'est le champ le plus à risque |
| `summary` | Le compte rendu (détail ci-dessous) ; `null` tant qu'il n'est pas généré | Objet | voir ci-dessous | Oui, peut être vide | Calculé par l'outil, validé par le commercial | **Oui, possible** (il recopie des passages des notes) |
| `next_actions` | Prochaines actions, recopiées du compte rendu ; vide si le rendez-vous est prévu | Liste | `["Vérifier auprès du client : Lancement envisagé pour septembre 2027, …"]` | Oui, peut être vide | Calculé par l'outil, puis tâches dans Salesforce | Non |

**Détail de `questions` et `answers`.**

| Champ | Ce qu'il veut dire | Exemple |
|---|---|---|
| `questions[].question` | La question à poser | `Quels nouveaux segments de boissons envisagez-vous de développer dans les prochains mois ?` |
| `questions[].why` | Pourquoi elle est importante | `Comprendre les ambitions du client et repérer de nouveaux besoins.` |
| `questions[].information_sought` | Le point de la checklist qu'elle cherche à obtenir | `client_objectives` |
| `answers[].information_sought` | Le point de la checklist auquel la réponse se rapporte | `timeline` |
| `answers[].answer` | La réponse obtenue | `Premier test au printemps.` |

**Détail de `summary` (le compte rendu).** Les rubriques `needs`, `technical_constraints`, `budget_constraints`, `timeline`, `missing_information`, `next_actions` et `internal_teams` sont des listes d'éléments. Chaque élément porte `point` (point de la checklist), `text`, `status` (`confirmed` ou `to_verify`) et `excerpt` (le passage des notes, mot pour mot, dont il vient).

| Champ | Ce qu'il veut dire | Exemple |
|---|---|---|
| `summary` | Résumé du rendez-vous | `Rendez-vous avec Maison Nova Drinks au sujet de « Nouvelle gamme de boissons fonctionnelles ». …` |
| `needs` | Besoins : objectifs, besoin réel, critères de décision | `Objectifs du client : Le client veut lancer deux boissons fonctionnelles sous sa propre marque.` (`confirmed`) |
| `technical_constraints` | Contraintes techniques | – |
| `budget_constraints` | Contraintes budgétaires | – |
| `timeline` | Calendrier ; tout passe en `to_verify` si les notes citent deux dates différentes | – |
| `missing_information` | Points de la checklist encore manquants | – |
| `next_actions` | Prochaines actions, toujours `to_verify` | – |
| `internal_teams` | Équipes à mobiliser, avec la raison ; chaque élément porte aussi `team` | `Application : une contrainte technique est notée.` |
| `opportunity_decision` | Statut proposé pour l'opportunité : `confirmed`, `to_qualify` ou `discarded` (écartée, prévu pour plus tard) | `confirmed` |
| `decision_reason` | Raison de ce statut | `Objectifs du client et besoin réel confirmés dans les notes : …` |
| `generated_by` | Moteur réellement utilisé : `rules_v1` (règles) ou `llm_v2` (IA locale) | `rules_v1` |
| `engine` | Moteur demandé, moteur utilisé, modèle, raison d'un retour aux règles, résultat du garde-fou | `{"requested": "rules_v1", "used": "rules_v1", "model": null, …}` |
| `validated` | Le commercial a-t-il validé le compte rendu ? | `false` |

## 6. Différences avec l'application de Tech (pour information)

Comparaison faite avec les fichiers de `app-hackathon/web/data/json/` présents sur le poste d'Ossama (version du 12/11/2026). Les deux côtés n'ont pas le même jeu de données : Tech a 12 clients, 27 projets, 18 opportunités, 18 signaux et 11 rendez-vous ; la démo v2 de la Data a 3 clients, 7 projets, 6 opportunités, 11 signaux et 2 rendez-vous.

### Champs qui n'ont pas le même nom

| Objet | Côté Data (`demo_v2`, API v2) | Côté Tech (`web/data/json/`) | Remarque |
|---|---|---|---|
| Clients | `active_projects` | `projectsCount` | La Data le calcule, Tech le stocke |
| Clients | `detected_opportunities` | `opportunitiesDetected` | Idem |
| Clients | `to_qualify` | `opportunitiesToQualify` | Idem |
| Questions suggérées | `information_sought` | `info_sought` (`suggested-questions.json`) | Même sens |
| Justification | `to_confirm` (stocké) ; `to_verify` (renvoyé par l'API v2) | `to_verify` (`opportunity-justifications.json`) | L'API v2 garde `to_verify` pour Tech |

### Champs présents d'un seul côté

| Objet | Seulement côté Data | Seulement côté Tech |
|---|---|---|
| Clients | `commercial_situation`, `history_summary` | – (la synthèse est dans un fichier à part, `clients-insights.json`) |
| Opportunités | `priority_max`, `priority_status`, `missing_criteria`, `justification` | – (la justification est dans un fichier à part, `opportunity-justifications.json`, avec `reasoning` et `to_verify`) |
| Signaux | `client_id`, `category`, `is_real_source`, `source_ref` | – |
| Rendez-vous | `collected_points` | – |
| Questions suggérées (fichier) | `known`, `missing` (`meeting_context.json`) | `id`, `client_id`, `blocker` (`suggested-questions.json`) |
| Questions suggérées (chaque question) | `id`, `opportunity_id`, `opportunity_link`, `origin` | – |

### Même nom, contenu différent

| Champ | Côté Data | Côté Tech |
|---|---|---|
| Identifiants | `C-01`, `P-01`, `O-01`, `S-01`, `M-01` | `1`, `proj-1a`, `opp-1a`, `sig-1a`, `meet-1a` |
| `clients.last_updated` | `2026-11-05` | `05/11/2026` (format français) |
| `clients.relationship_status` | Codes : `strategic`, `active`, `to_develop` | Libellés : `Client stratégique`, `Actif`, `En négociation` (« En négociation » n'a pas d'équivalent côté Data) |
| `clients.account_manager` | Un rôle (`KAM senior Boissons (fictif)`) | **Des noms de personnes** (10 noms différents, par exemple `Thomas Leroy`) : contraire à la règle 8 de `MODELE_DONNEES.md` et à `RGPD.md` |
| `projects.status` | `active`, `completed` | `actif` |
| `opportunities.status` | `detected`, `to_qualify`, `confirmed` | `detectee`, `a_qualifier` |
| `opportunities.priority` | `high`, `medium`, `low` | `haute`, `moyenne`, `basse` |
| `opportunities.estimated_potential` | `high`, `medium`, `low`, `null` | `elevee`, `moyenne`, `faible`, `null` |
| `opportunities.feasibility` | `high`, `medium`, `low`, `to_confirm` | `elevee`, `moyenne`, `a_confirmer` |
| `opportunities.complexity` | `high`, `medium`, `low`, `to_confirm` | `elevee`, `moyenne`, `faible` |
| `opportunities.category` | 6 catégories | 14 catégories, dont `Réduction de sel` et `Nouvelle fragrance` |
| `signals.source_type` | `meeting_report`, `client_request`, `project_history`, `market_trend`, `commodity_price`, `company_report`, `regulation` | `compte_rendu`, `demande_client`, `historique`, `projet`, `veille_marche` (`historique` et `projet` correspondent tous deux à `project_history` ?) |
| `signals.confidence` | `high`, `medium`, `low` | `haute`, `moyenne`, `faible` |
| `signals.evidence_type` | `fact`, `hypothesis`, `to_confirm` | `fait`, `hypothese` (pas de « à confirmer ») |
| `meetings.status` | `planned`, `completed` | `a_preparer`, `realise` |
| `meetings.questions` | Liste d'objets `{question, why, information_sought}` | Liste de textes |
| `meetings.answers` | Liste d'objets `{information_sought, answer}` | Liste de textes |
| `meetings.summary` | Objet compte rendu (rubriques, statuts, extraits) | Un texte |

Pour brancher l'application sur les données de la Data, il faudra une table de correspondance des valeurs : codes anglais côté Data, libellés français affichés par l'application.
