# Traçabilité des résultats – Opportunity Radar (G03)

Mission O3 · Ossama · Vérifié dans le code et les données le 19/11/2026.

Un commercial doit pouvoir demander « d'où sort ce résultat ? » et obtenir une réponse. Ce document dit, pour chaque résultat de l'outil, ce qui le produit, avec quelles données, et comment le commercial en voit l'origine.

Le prototype a trois briques :

- l'**API de démo v2** (`data/api/main.py`, données `data/demo_v2/`) ;
- l'**API RAG** (dépôt `Gr03-Marvels-MD4`) ;
- l'**API V1** (`ia/main.py`, données `ia/donnees/`).

## 1. Les résultats et leur origine

| Résultat | Ce qui le produit | Les données qu'il utilise | Comment le commercial voit d'où il vient |
|---|---|---|---|
| Opportunité (v2) | `data/demo_v2/detection.py` et `regles_detection.json` : règles, sans LLM. Priorité : `grille_qualification.json` | Signaux client, projets, secteur du client | `GET /v2/opportunities/{id}` renvoie les `signals` complets (du plus récent au plus ancien), `last_signal_date`, `justification.provenance` (signal, type, date, source ou « source fictive (démo) »), `reasoning` (détail du score), `priority_status` et `missing_criteria` |
| Justification (v2) | `data/demo_v2/justification.py` : règles, sans LLM. Stockée dans `opportunities.json` | Signaux de l'opportunité, projets, statut de la relation, grille de qualification, contraintes de `meeting_context.json` | Chaque phrase porte `evidence_type` (fait, hypothèse, à confirmer) et `sources`, jamais vide (`S-01`, `P-01`, `clients.json#C-01`…). Faits, hypothèses et points à confirmer sont dans des rubriques séparées |
| Justification (V1) | `ia/main.py`, `GET /justification/{id}` : calcul, sans LLM | Signaux de `ia/donnees/` | `"source": "donnees"`. Chaque fait cite dans son texte le type de source, la date et la fiabilité, mais **pas l'identifiant du signal** |
| 3 questions (API RAG) | `clients.py` de `Gr03-Marvels-MD4`, LLM local `qwen2.5:1.5b` | Sections de la fiche du client, retrouvées dans ChromaDB | Champs `source` (modele, mixte, simule), `origine` de chaque question (modele, prepare), `model`, `duree_s` et `extraits` (section, texte, score) de la réponse |
| 3 questions (Meeting Copilot v2) | `meeting_context.json`, généré par `generer_demo_v2.py`, servi par `GET /v2/opportunities/{id}/meeting` | Banque de questions (`data/questions/questions.json`), points manquants de la checklist, critères inconnus de l'opportunité | `id` (`Q-xx` = banque de questions, `O-xx-Qn` = rédigée pour la démo), `origin`, `information_sought`, `opportunity_link`. La liste `known` cite le signal qui apporte chaque point déjà connu |
| 3 questions (V1) | `ia/main.py`, `POST /questions`, LLM local | Données de l'opportunité dans `ia/donnees/` | `source` (modele, simule) et `model`. **Pas d'extraits** : on ne voit pas ce qui a été donné au modèle |
| Compte rendu (v2) | `data/demo_v2/compte_rendu.py`, `POST /v2/meetings/report`, en mode `rules_v1` (règles) ou `llm_v2` (`qwen2.5:3b` local) | Notes, réponses et points cochés du rendez-vous, opportunité | Chaque élément porte `status` (`confirmed` ou `to_verify`) et `excerpt`, le passage copié mot pour mot des notes. `generated_by` et `engine` disent quel moteur a été demandé et utilisé, et pourquoi on est revenu aux règles. `validated` dit si le commercial a validé |
| Compte rendu (V1) | `ia/main.py`, `POST /compte-rendu` | Checklist et notes | `source`, `model`, et un `statut` par élément (`confirme`, `a_verifier`). **Pas d'extrait des notes** |

### Faits et hypothèses

- **v2 : séparation complète.** Chaque signal et chaque phrase de justification porte `evidence_type`. Chaque élément du compte rendu porte `confirmed` ou `to_verify`. Une hypothèse seule ne suffit pas à créer une opportunité.
- **API RAG : séparation dans la consigne seulement.** Le prompt interdit de présenter une hypothèse comme un fait, mais la réponse ne dit pas si une question part d'un fait ou d'une hypothèse.
- **V1 :** la justification sépare `faits`, `hypotheses` et `a_confirmer`.

### Ce qui manque

1. **API RAG : aucun lien entre une question et l'extrait qui l'a inspirée.** Le commercial voit les 6 sections données au modèle, mais pas laquelle justifie chaque question.
   > Recommandation : demander au modèle d'indiquer la section utilisée pour chaque question, et vérifier qu'elle fait partie des `extraits`.
2. **API V1 : moins traçable que la v2.** Les questions n'ont pas d'extraits, le compte rendu n'a pas d'extraits des notes, et la justification ne cite pas l'identifiant des signaux.
   > Recommandation : aligner la V1 sur le format de la v2, ou montrer la v2 au jury.

## 2. Vérification des signaux (`data/demo_v2/signals.json`)

**Méthode.** Contrôle des 11 signaux, champ par champ, d'après `data/demo_v2/MODELE_DONNEES.md` : source (`source_type`, `source_ref`), date (`source_date`), fiabilité (`confidence`), nature (`evidence_type`), source réelle ou fictive (`is_real_source`). Contrôle complémentaire : `python data/verifier_jeu.py` affiche `7/7 contrôles OK`.

| Signal | Type de source | Date | Fiabilité | Nature | Source réelle | `source_ref` |
|---|---|---|---|---|---|---|
| S-01 | meeting_report | 2026-11-05 | high | fact | non | **vide** |
| S-02 | market_trend | 2022-12-31 | medium | fact | oui | `signaux_marche.json#OPP-01` |
| S-03 | project_history | 2026-10-20 | medium | fact | non | `projects.json#P-01` |
| S-04 | client_request | 2026-10-22 | high | fact | non | **vide** |
| S-05 | market_trend | 2022-12-31 | low | hypothesis | oui | `signaux_marche.json#OPP-05` |
| S-06 | project_history | 2026-06-30 | high | fact | non | `projects.json#P-06` |
| S-07 | meeting_report | 2026-10-28 | high | fact | non | **vide** |
| S-08 | commodity_price | 2026-09-30 | medium | fact | oui | URL INSEE |
| S-09 | company_report | 2026-01-29 | medium | fact | oui | Rapport intégré Givaudan 2025, pp. 49-50 |
| S-10 | project_history | 2026-09-21 | medium | fact | non | `projects.json#P-07` |
| S-11 | regulation | 2012-10-02 | high | fact | oui | URL de la Commission européenne |

**Résultat.**

- 11 signaux sur 11 ont une date au bon format, une fiabilité, une nature et une opportunité rattachée.
- 10 faits et 1 hypothèse (S-05).
- Les 5 sources réelles ont toutes une `source_ref` (règle 4 du modèle de données respectée). Les références internes existent : les projets `P-01`, `P-06`, `P-07` et les entrées `OPP-01`, `OPP-05` de `signaux_marche.json`.

**Signaux incomplets.**

| Signal | Ce qui manque | Ce qu'il faudrait faire |
|---|---|---|
| S-01, S-04, S-07 | Pas de `source_ref` (comptes rendus et demande client). C'est autorisé parce que ces signaux sont fictifs, mais le commercial n'a rien à ouvrir | En vrai : un lien vers le compte rendu ou la demande dans le CRM |
| S-09 | Référence à un PDF (titre et pages), sans lien ni fichier dans le dépôt | Ajouter l'adresse publique du rapport |
| S-08, S-11 | L'adresse publique fonctionne, mais l'échantillon cité est sur un disque local (`D:/open_data/...`), absent du dépôt | Mettre l'échantillon dans le dépôt, ou retirer la mention du disque local |
| S-02, S-05 | Tendance de marché arrêtée au 2022-12-31, presque 4 ans avant la date de référence du jeu (2026-11-12). La date est visible, mais la justification la cite dans « pourquoi maintenant » | Signaler l'âge de la donnée dans la phrase, ou chercher une période plus récente |

## 3. Journal des appels (recommandation)

C'est une recommandation écrite : rien n'est codé.

À chaque utilisation de l'outil, l'API ajoute une ligne à un journal, avec seulement :

| Champ | Exemple | Pourquoi |
|---|---|---|
| Date et heure | `2026-11-19T12:25:03+01:00` | Savoir quand le résultat a été produit |
| Route | `/questions-client` | Savoir quel résultat a été produit |
| Client | `4` (identifiant, pas le nom) | Retrouver la fiche utilisée |
| Modèle | `qwen2.5:1.5b`, ou `null` sans LLM | Savoir quelle IA a écrit |
| Source | `modele`, `mixte`, `simule`, `donnees`, `rules_v1`, `llm_v2` | Savoir si l'IA, les règles ou le plan B ont répondu |
| Durée | `27.5` (secondes) | Suivre le temps de réponse |
| Code de réponse | `200` | Repérer les erreurs |

Exemple de ligne (valeurs du test 2 de `SECURITE_LLM.md`) :

```json
{"date": "2026-11-19T12:25:03+01:00", "route": "/questions-client", "client_id": "4", "model": "qwen2.5:1.5b", "source": "modele", "duree_s": 27.5, "code": 200}
```

**Jamais dans le journal :** le contenu des notes, les réponses du client, le texte des questions, les extraits de fiche, ni aucun nom de personne. Le journal sert à retrouver l'origine d'un résultat, pas à en garder une copie (minimisation, voir `RGPD.md`).

**Ce qu'il permettrait :** répondre à « d'où vient ce résultat ? » à partir de la date et du client, mesurer la part de réponses en plan B, et suivre les temps de réponse.

**Durée de conservation :** à définir avec le DPO de Givaudan. Si un identifiant de commercial est ajouté, pour contrôler les accès, le journal devient une donnée personnelle (voir `RGPD.md`).
