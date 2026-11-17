# Fiche RGPD – Opportunity Radar (G03)

Mission O1 · Ossama · Relecture : Evrad (à faire)

Toutes les données du prototype sont fictives. Cette fiche décrit ce que l'outil traiterait **en vrai**, chez Givaudan, puis compare avec ce que fait le prototype aujourd'hui (vérifié dans le code le 17/11/2026).

## 1. Les données que l'outil utiliserait

| Donnée | Exemple (fictif) | Pourquoi on en a besoin | Donnée personnelle ? | Durée de conservation | Qui y accède |
|---|---|---|---|---|---|
| Nom de l'entreprise cliente | Maison Nova Drinks | Retrouver la bonne fiche | Non | Tant que le client est suivi | Le commercial du compte |
| Secteur, pays, statut de la relation | Boissons, France, stratégique | Situer le client et prioriser | Non | Tant que le client est suivi | Le commercial du compte, son manager |
| Responsable commercial du compte | « KAM senior Boissons » | Savoir à qui le compte est attribué | **Oui** si c'est un nom (salarié de Givaudan). Non si c'est un rôle | Tant que la personne suit le compte | Le commercial, son manager, l'administrateur de l'outil |
| Projets en cours | « Reformulation de l'arôme agrumes » | Ne pas proposer ce qui est déjà engagé | Non | Durée du projet, puis à définir avec le DPO | Le commercial du compte, les équipes internes mobilisées |
| Opportunités détectées | « Nouvelle gamme de boissons fonctionnelles » | Cœur du produit | Non | Tant que l'opportunité est ouverte, puis à définir avec le DPO | Le commercial du compte |
| Signaux client (comptes rendus, demandes) | « Échange du 05/11 : intérêt pour les boissons fonctionnelles » | Justifier l'opportunité (source, date, fiabilité) | Oui, si un nom de personne y figure | À définir avec le DPO | Le commercial du compte |
| Signaux de marché | Open Food Facts, INSEE, règlement UE | Expliquer « pourquoi maintenant » | Non (données publiques, sans personne) | Tant que la tendance est utile | Tous les commerciaux |
| Notes de rendez-vous | « Le client veut réduire le sucre » | Générer le compte rendu et les questions | Oui, si un nom de personne y figure | À définir avec le DPO | Le commercial du compte |
| Réponses du client aux questions | « Premier test au printemps » | Compléter la checklist (calendrier, budget…) | Oui, si un nom de personne y figure | À définir avec le DPO | Le commercial du compte |
| Questions et compte rendu produits par l'outil | 3 questions, compte rendu `rules_v1` | Préparer et suivre le rendez-vous | Non, s'ils ne reprennent aucun nom | Comme les notes dont ils viennent | Le commercial du compte, qui les valide |
| Contacts chez le client (nom, fonction, e-mail) | « Directrice R&D » | **Inutile aux questions** : reste dans le CRM | **Oui** | Non stocké par l'outil | Personne dans l'outil |
| Compte du commercial qui utilise l'outil | `kam.boissons.01` | Droits d'accès : un commercial ne voit que son portefeuille | **Oui** | Tant que la personne a accès à l'outil | L'administrateur de l'outil |
| Journal des appels (voir `TRACABILITE.md`) | Date, client, modèle, source, durée | Traçabilité et mesure de la qualité | Non, si aucun identifiant de personne n'y figure | À définir avec le DPO | L'équipe technique |

Les durées « à définir » sont à fixer par le DPO. Piste de départ : le référentiel CNIL « gestion des activités commerciales », non contraignant. Il retient la durée de la relation contractuelle pour les données clients, et 3 ans à compter de la collecte ou du dernier contact pour un prospect.

## 2. Les 4 principes

### Minimisation

On ne garde que ce qui sert au brief. Les questions se construisent à partir des besoins, des projets, des signaux et des points à confirmer. Le nom d'une personne n'y sert à rien : il ne doit pas être envoyé au LLM.

**État du prototype :**

- **Jeu `data/demo_v2/` : conforme.** Le champ `account_manager` contient un rôle (« KAM senior Boissons (fictif) ») et la règle 8 de `data/demo_v2/MODELE_DONNEES.md` interdit les noms de personnes.
- **API RAG (dépôt `Gr03-Marvels-MD4`) : non conforme.** Les 6 fiches `fiches_clients/client_*.md` contiennent le nom d'un responsable commercial dans la section « Identité » (exemple, `client_4.md` : « Responsable commercial : Thomas Leroy »). Chaque fiche a 6 sections et l'API en récupère 6 (`CLIENTS_TOP_K = 6` dans `config.py`). La section Identité, avec le nom, part donc au LLM à chaque appel. Elle est aussi renvoyée dans le champ `extraits` de la réponse.
- Les mêmes noms sont dans `fiches_clients/fiches_clients.json`, `fiches_clients/document_central.md` et `ia/donnees/clients.json` de ce dépôt.

Ces noms sont fictifs : aucune vraie personne n'est exposée. Aucun contact côté client n'apparaît dans les fiches, donc la phrase du livrable (« les données personnelles des contacts ne sont pas envoyées au modèle », `LIVRABLE_DATA_G03.md`, section 8) reste vraie au sens strict. Mais le nom d'un salarié est une donnée personnelle, inutile aux questions : il contredit le principe de minimisation.

**Correction proposée :** remplacer le nom par un rôle, comme dans `demo_v2`, dans `fiches_clients.json` (champ `account_manager`). Puis régénérer les fiches avec `generer_fiches_md.py` (ligne 15) et relancer `python ingest_clients.py`. Le dépôt appartient à Amir : correction à faire par lui, ou avec son accord.

### Pas de données sensibles

L'outil ne collecte jamais les données sensibles de l'article 9 du RGPD : origine raciale ou ethnique, opinions politiques, convictions religieuses ou philosophiques, appartenance syndicale, données génétiques ou biométriques, santé, vie ou orientation sexuelle. « Réduire le sucre » concerne un produit, pas la santé d'une personne.

Le risque réel, ce sont les **notes libres** : un commercial peut écrire « l'acheteur est en arrêt maladie ». Recommandation : une consigne claire aux commerciaux (« ni santé, ni vie privée, ni opinion dans les notes »), et un contrôle simple avant l'enregistrement, qui signale les mots à risque. Ce contrôle n'existe pas dans le prototype.

### Droits des personnes

Une personne dont le nom figure dans une note peut demander l'**accès** à ses données, leur **correction**, leur **effacement** ou s'**opposer** au traitement (articles 15, 16, 17 et 21 du RGPD). Givaudan doit répondre au plus tard dans un délai d'un mois (article 12).

Qui traite la demande :

1. Le **DPO de Givaudan** reçoit la demande et vérifie l'identité de la personne.
2. Le **commercial du compte** retrouve les notes concernées et les corrige ou les supprime.
3. L'**administrateur de l'outil** applique la suppression dans toutes les copies.

Point technique important : une note existe en plusieurs copies (le fichier source, la base `chroma_db/`, et le journal s'il est mis en place). Supprimer le fichier ne suffit pas. `ingest_clients.py` fait un `upsert` : il met à jour ou ajoute des morceaux, il n'en supprime jamais. Une section ou une fiche supprimée reste donc dans `chroma_db/`. Procédure pour le prototype : supprimer le dossier `chroma_db/`, puis relancer `python ingest_clients.py`.

### Hébergement

- **Le LLM tourne sur l'ordinateur.** Dans `config.py` de l'API RAG, `OLLAMA_HOST` vaut `http://localhost:11434`, c'est-à-dire « cet ordinateur ». Modèles : `qwen2.5:1.5b` (texte) et `nomic-embed-text` (recherche).
- **La base reste sur le disque.** ChromaDB est enregistrée dans `chroma_db/`, exclu de GitHub par `.gitignore`.
- **Aucun service d'IA externe** n'est appelé par l'API. La preuve par les tests est dans `SECURITE_LLM.md` (mission O2).
- **En vrai :** LLM hébergé sur un serveur de Givaudan, aucune donnée client envoyée à un service externe (`LIVRABLE_DATA_G03.md`, section 8).

Deux exceptions à connaître :

1. `ollama pull` télécharge le modèle depuis Internet, une seule fois. Aucune donnée client ne part : c'est un téléchargement.
2. **ngrok** rend l'API joignable depuis Internet, par toute personne qui a l'adresse. L'API RAG n'a pas de clé d'accès, contrairement à l'API V1 (`ia/`, en-tête `x-api-key`). Elle accepte aussi les appels de n'importe quel site (`allow_origins=["*"]` dans `api.py`). C'est acceptable pour une démo avec des données fictives, mais à exclure avec de vraies données.

## 3. Base légale

À valider avec le délégué à la protection des données (DPO) de Givaudan.

## 4. Écarts à corriger

| # | Écart | Où | Correction proposée | Qui |
|---|---|---|---|---|
| 1 | Nom du responsable commercial envoyé au LLM | Fiches de l'API RAG, `fiches_clients.json` | Remplacer le nom par un rôle | Amir, ou avec son accord |
| 2 | Effacement incomplet dans la base | `ingest_clients.py` | Vider `chroma_db/` avant de réingérer, ou supprimer les morceaux absents des fiches | Amir, ou avec son accord |
| 3 | API RAG sans clé, ouverte à tous les sites, exposée par ngrok | `api.py` | Clé d'accès comme l'API V1, CORS limité au domaine de Tech, pas de ngrok avec de vraies données | À voir avec Tech |
| 4 | Durées de conservation non fixées | Ce document | Décision du DPO | DPO de Givaudan |

## Références

- Règlement (UE) 2016/679 (RGPD), articles 9, 12, 15, 16, 17 et 21.
- CNIL, référentiel relatif à la gestion des activités commerciales : https://www.cnil.fr/sites/cnil/files/atoms/files/referentiel_traitements-donnees-caractere-personnel_gestion-activites-commerciales.pdf
