"""Génère data/demo_v2 (doc fonctionnelle v2) : clients (DATA-US03), projets (DATA-US04),
opportunités (DATA-US05) et signaux (DATA-US06).

Usage, depuis la racine du repo :
    python data/demo_v2/generer_demo_v2.py

Clients, projets et opportunités sont fictifs : aucun vrai client, aucun vrai nom de personne.
Les signaux marqués is_real_source citent leur source exacte. Aucun compteur ni date du dernier
signal n'est stocké : ils se calculent à partir des autres fichiers.
"""

import json
from datetime import date
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent

CLIENTS = [
    {
        "id": "C-01",
        "name": "Maison Nova Drinks",
        "sector": "Boissons",
        "country": "France",
        "account_manager": "KAM senior Boissons (fictif)",
        "relationship_status": "strategic",
        "last_updated": "2026-11-05",
        "commercial_situation": (
            "Client établi en croissance, avec plusieurs projets actifs. "
            "Un échange commercial le 05/11/2026 a porté sur une nouvelle gamme."
        ),
        "history_summary": (
            "Partenaire de longue date sur les arômes de ses boissons. "
            "Les projets récents ont été menés jusqu'au lancement. "
            "Le client montre un intérêt récent pour une nouvelle catégorie : les boissons fonctionnelles."
        ),
    },
    {
        "id": "C-02",
        "name": "Nordic Food Industries",
        "sector": "Agroalimentaire",
        "country": "Suède",
        "account_manager": "KAM Europe du Nord (fictif)",
        "relationship_status": "active",
        "last_updated": "2026-10-28",
        "commercial_situation": (
            "Le client a formulé une demande sur des alternatives végétales. "
            "Il a communiqué une contrainte budgétaire pour les prochains projets."
        ),
        "history_summary": (
            "Relation suivie, avec des projets actifs en cours. "
            "Un projet précédent a reçu un retour technique sur sa texture. "
            "Ce retour est à prendre en compte dans les nouvelles propositions."
        ),
    },
    {
        "id": "C-03",
        "name": "Alimenta Distribution",
        "sector": "Distribution alimentaire",
        "country": "France",
        "account_manager": "Chargé de développement Distribution (fictif)",
        "relationship_status": "to_develop",
        "last_updated": "2026-10-15",
        "commercial_situation": (
            "Relation récente, avec un premier projet actif. "
            "Potentiel identifié sur une nouvelle référence aromatique pour sa marque de distributeur."
        ),
        "history_summary": (
            "Premiers échanges engagés cette année. "
            "Le client cherche à enrichir l'offre de sa marque de distributeur."
        ),
    },
]


PROJETS = [
    # C-01 Maison Nova Drinks : 3 projets actifs.
    {
        "id": "P-01",
        "client_id": "C-01",
        "name": "Reformulation de l'arôme agrumes de la gamme existante",
        "description": (
            "Travail en cours sur la gamme de boissons aromatisées existante : reformulation de son arôme "
            "agrumes, sans nouvelle saveur. Projet lancé le 10/10/2026, échantillon envoyé le 20/10/2026."
        ),
        "status": "active",
        "start_date": "2026-10-10",
    },
    {
        "id": "P-02",
        "client_id": "C-01",
        "name": "Boisson gazeuse à teneur réduite en sucre",
        "description": "Reformulation d'une boisson gazeuse pour réduire le sucre en gardant le profil aromatique.",
        "status": "active",
        "start_date": "2026-06-15",
    },
    {
        "id": "P-03",
        "client_id": "C-01",
        "name": "Boisson pétillante en édition saisonnière",
        "description": "Création d'un arôme pour une édition limitée d'hiver d'une boisson pétillante.",
        "status": "active",
        "start_date": "2026-09-01",
    },
    # C-02 Nordic Food Industries : 2 projets actifs et 1 terminé.
    {
        "id": "P-04",
        "client_id": "C-02",
        "name": "Arôme pour une gamme de soupes",
        "description": "Développement d'un arôme d'herbes aromatiques pour une gamme de soupes du client.",
        "status": "active",
        "start_date": "2026-09-15",
    },
    {
        "id": "P-05",
        "client_id": "C-02",
        "name": "Arôme pour une gamme de sauces",
        "description": "Développement d'un arôme fumé pour une gamme de sauces barbecue du client.",
        "status": "active",
        "start_date": "2026-10-01",
    },
    {
        "id": "P-06",
        "client_id": "C-02",
        "name": "Dessert végétal aromatisé",
        "description": (
            "Projet livré. Le client a fait un retour technique sur la texture, jugée trop épaisse en bouche."
        ),
        "status": "completed",
        "start_date": "2026-03-02",
    },
    # C-03 Alimenta Distribution : 1 projet actif.
    {
        "id": "P-07",
        "client_id": "C-03",
        "name": "Yaourt à la vanille de marque de distributeur",
        "description": "Premier projet avec le client : arôme vanille pour un yaourt de sa marque de distributeur.",
        "status": "active",
        "start_date": "2026-09-21",
    },
]


# Opportunités (DATA-US05) : les 6 de la doc v2, section 7. priority est calculée par priorite().
OPPORTUNITES = [
    {
        "id": "O-01",
        "client_id": "C-01",
        "title": "Nouvelle gamme de boissons fonctionnelles",
        "description": (
            "Le client s'intéresse à une nouvelle catégorie, les boissons fonctionnelles : "
            "possibilité d'accompagner le lancement d'une nouvelle gamme."
        ),
        "category": "Nouvelle gamme",
        "status": "to_qualify",
        "estimated_potential": "high",
        "feasibility": "to_confirm",
        "complexity": "high",
        "next_action": (
            "Organiser un échange avec le client afin de confirmer son intérêt pour une nouvelle gamme de "
            "boissons fonctionnelles et identifier ses contraintes de formulation."
        ),
    },
    {
        "id": "O-02",
        "client_id": "C-01",
        "title": "Extension d'une gamme aromatique",
        "description": (
            "Le travail en cours sur la gamme existante (P-01) peut ouvrir sur de nouvelles saveurs "
            "pour cette gamme."
        ),
        "category": "Extension de gamme",
        "status": "detected",
        "estimated_potential": "medium",
        "feasibility": "high",
        "complexity": "low",
        "next_action": (
            "Faire le point sur le retour de l'échantillon envoyé le 20/10/2026 (P-01) avant de proposer "
            "une extension de la gamme."
        ),
    },
    {
        "id": "O-03",
        "client_id": "C-02",
        "title": "Développement d'une formulation végétale",
        "description": "Le client a demandé des alternatives végétales : possibilité de développer une formulation dédiée.",
        "category": "Nouvelle formulation",
        "status": "to_qualify",
        "estimated_potential": "medium",
        "feasibility": "medium",
        "complexity": "high",
        "next_action": "Qualifier la demande : produit visé, marché suédois, calendrier et budget.",
    },
    {
        "id": "O-04",
        "client_id": "C-02",
        "title": "Amélioration de la texture d'un produit",
        "description": (
            "Le retour technique sur la texture du projet terminé P-06 peut justifier une proposition "
            "d'amélioration."
        ),
        "category": "Amélioration produit",
        "status": "detected",
        "estimated_potential": "low",
        "feasibility": "medium",
        "complexity": "medium",
        "next_action": "Revoir avec les équipes techniques le retour sur la texture de P-06 avant de recontacter le client.",
    },
    {
        "id": "O-05",
        "client_id": "C-02",
        "title": "Optimisation d'une formulation existante",
        "description": (
            "Le client a communiqué une contrainte budgétaire : possibilité d'optimiser le coût d'une "
            "formulation existante."
        ),
        "category": "Optimisation",
        "status": "detected",
        "estimated_potential": "low",
        "feasibility": "medium",
        "complexity": "medium",
        "next_action": "Confirmer le budget communiqué et identifier la formulation à optimiser.",
    },
    {
        "id": "O-06",
        "client_id": "C-03",
        "title": "Nouvelle référence aromatique pour une marque de distributeur",
        "description": (
            "La demande de produits plus naturels et à l'étiquette plus claire peut ouvrir une nouvelle "
            "référence aromatique pour la marque de distributeur du client."
        ),
        "category": "Nouvelle référence",
        "status": "detected",
        "estimated_potential": None,
        "feasibility": "to_confirm",
        "complexity": "low",
        "next_action": (
            "Présenter des pistes d'arômes naturels pour la marque de distributeur et confirmer l'intérêt "
            "du client."
        ),
    },
]

# Règle de priorité (doc v2, section 5.3 : « une classification par règles métier suffit »).
DATE_REFERENCE = "2026-11-12"  # date du jeu de démo, fixe
JOURS_URGENCE = 30
SOURCES_CLIENT = {"meeting_report", "client_request"}  # le client s'est exprimé lui-même
POINTS_CONFIANCE = {"high": 2, "medium": 1, "low": 0}
POINTS_POTENTIEL = {"high": 2, "medium": 1, "low": 0, None: 0}
POINTS_FAISABILITE = {"high": 2, "medium": 1, "low": 0, "to_confirm": 0}
SEUIL_HIGH, SEUIL_MEDIUM = 5, 3

FICHIER_OFF = DOSSIER.parent / "signaux" / "signaux_marche.json"
GIVAUDAN = "Rapport intégré Givaudan 2025 (giv-2025-integrated-report.pdf)"


def detail_priorite(opportunite, signaux):
    """Points de chaque critère : confiance (meilleur signal), potentiel, faisabilité, urgence."""
    propres = [s for s in signaux if s["opportunity_id"] == opportunite["id"]]
    reference = date.fromisoformat(DATE_REFERENCE)
    return {
        "confidence": max(POINTS_CONFIANCE[s["confidence"]] for s in propres),
        "potential": POINTS_POTENTIEL[opportunite["estimated_potential"]],
        "feasibility": POINTS_FAISABILITE[opportunite["feasibility"]],
        "urgency": int(any(s["source_type"] in SOURCES_CLIENT
                           and (reference - date.fromisoformat(s["source_date"])).days <= JOURS_URGENCE
                           for s in propres)),
    }


def score_priorite(opportunite, signaux):
    """Confiance (meilleur signal) + potentiel + faisabilité + urgence, de 0 à 7."""
    return sum(detail_priorite(opportunite, signaux).values())


def priorite(opportunite, signaux):
    score = score_priorite(opportunite, signaux)
    return "high" if score >= SEUIL_HIGH else "medium" if score >= SEUIL_MEDIUM else "low"


def signal_off(signaux_off, opp_off):
    """Chiffres Open Food Facts de la période affichée (2020→2022), relus dans signaux_marche.json.

    source_date = fin de la période observée (et non la date d'extraction, qui va dans source_ref) :
    sinon la « date du dernier signal » présenterait une tendance de 2022 comme récente.
    """
    g = next(s["signal"] for s in signaux_off["signaux"] if s["opportunite_id"] == opp_off)
    periode = next(p for p in g["periodes"].values() if p["role"].startswith("principale"))
    ref = (f"data/signaux/signaux_marche.json#{opp_off} (données Open Food Facts au "
           f"{signaux_off['source']['dernier_produit_ajoute']}, extraites le {signaux_off['date_extraction']})")
    return {"pct": f"{g['evolution_affichee_pct']:+d} %",
            "n0": g["annees"][str(periode["debut"])]["produits"], "n1": g["annees"][str(periode["fin"])]["produits"],
            "date": f"{periode['fin']}-12-31", "ref": ref}


def construire_signaux(signaux_off):
    """Signaux (DATA-US06) : fictifs de la doc, et réels avec leur source exacte."""
    f01, f03 = signal_off(signaux_off, "OPP-01"), signal_off(signaux_off, "OPP-05")
    return [
        {"id": "S-01", "opportunity_id": "O-01",
         "description": ("Compte rendu de l'échange commercial du 05/11/2026 : le client exprime un intérêt pour "
                         "une nouvelle catégorie, les boissons fonctionnelles."),
         "source_type": "meeting_report", "source_date": "2026-11-05", "confidence": "high",
         "evidence_type": "fact", "is_real_source": False, "source_ref": None},
        {"id": "S-02", "opportunity_id": "O-01",
         "description": (f"Part des nouveaux produits boissons fonctionnelles en France : {f01['pct']} entre "
                         f"2020 et 2022 (Open Food Facts). Petit échantillon : {f01['n0']} produits en 2020, "
                         f"{f01['n1']} en 2022. Produits référencés, pas des ventes."),
         "source_type": "market_trend", "source_date": f01["date"], "confidence": "medium",
         "evidence_type": "fact", "is_real_source": True, "source_ref": f01["ref"]},
        {"id": "S-03", "opportunity_id": "O-02",
         "description": ("Projet existant P-01 : reformulation de l'arôme agrumes de la gamme existante, "
                         "échantillon envoyé le 20/10/2026."),
         "source_type": "project_history", "source_date": "2026-10-20", "confidence": "medium",
         "evidence_type": "fact", "is_real_source": False, "source_ref": "data/demo_v2/projects.json#P-01"},
        {"id": "S-04", "opportunity_id": "O-03",
         "description": "Demande du client concernant des alternatives végétales.",
         "source_type": "client_request", "source_date": "2026-10-22", "confidence": "high",
         "evidence_type": "fact", "is_real_source": False, "source_ref": None},
        {"id": "S-05", "opportunity_id": "O-03",
         "description": (f"Part des nouveaux produits alternatives végétales à la viande et aux laitiers en "
                         f"France : {f03['pct']} entre 2020 et 2022 (Open Food Facts ; {f03['n0']} produits en "
                         f"2020, {f03['n1']} en 2022). Chiffre français : le client est en Suède, la tendance "
                         "n'y est pas mesurée."),
         "source_type": "market_trend", "source_date": f03["date"], "confidence": "low",
         "evidence_type": "hypothesis", "is_real_source": True, "source_ref": f03["ref"]},
        {"id": "S-06", "opportunity_id": "O-04",
         "description": "Retour technique du client sur le projet terminé P-06 : texture jugée trop épaisse en bouche.",
         "source_type": "project_history", "source_date": "2026-06-30", "confidence": "high",
         "evidence_type": "fact", "is_real_source": False, "source_ref": "data/demo_v2/projects.json#P-06"},
        {"id": "S-07", "opportunity_id": "O-05",
         "description": "Compte rendu : le client a communiqué une contrainte budgétaire pour ses prochains projets.",
         "source_type": "meeting_report", "source_date": "2026-10-28", "confidence": "high",
         "evidence_type": "fact", "is_real_source": False, "source_ref": None},
        {"id": "S-08", "opportunity_id": "O-05",
         "description": ("Coût de matière première : indice INSEE du sucre importé, en euros, +15 % sur un an "
                         "(09/2025 → 09/2026), mais environ −39 % depuis octobre 2023. Prix mondial à "
                         "l'import, pas le coût réel du client."),
         "source_type": "commodity_price", "source_date": "2026-09-30", "confidence": "medium",
         "evidence_type": "fact", "is_real_source": True,
         "source_ref": ("https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/010002028 "
                        "(échantillon : D:/open_data/insee_ippmp_sucre/010002028.csv)")},
        {"id": "S-09", "opportunity_id": "O-06",
         "description": ("Givaudan cite la demande de transparence, de produits durables et clean label, et "
                         "d'ingrédients naturels parmi les tendances de sa stratégie 2030 (rapport intégré "
                         "2025, pp. 49-50). Tendance mondiale, pas propre aux marques de distributeur."),
         "source_type": "company_report", "source_date": "2026-01-29", "confidence": "medium",
         "evidence_type": "fact", "is_real_source": True, "source_ref": f"{GIVAUDAN}, pp. 49-50"},
        {"id": "S-10", "opportunity_id": "O-06",
         "description": ("Premier projet en cours avec le client : P-07 (arôme vanille pour un yaourt de sa "
                         "marque de distributeur)."),
         "source_type": "project_history", "source_date": "2026-09-21", "confidence": "medium",
         "evidence_type": "fact", "is_real_source": False, "source_ref": "data/demo_v2/projects.json#P-07"},
        {"id": "S-11", "opportunity_id": "O-06",
         "description": ("Fait réglementaire : le limonène (note d'agrumes) figure dans la liste de l'Union des "
                         "substances aromatisantes pour la catégorie « All categories of flavoured foods », "
                         "sans restriction indiquée (règlement d'exécution (UE) n° 872/2012, JO L 267 du "
                         "02/10/2012). L'autorisation est un fait ; son lien avec la nouvelle référence "
                         "(par exemple une référence agrumes) est une piste."),
         "source_type": "regulation", "source_date": "2012-10-02", "confidence": "high",
         "evidence_type": "fact", "is_real_source": True,
         "source_ref": ("https://ec.europa.eu/food/food-feed-portal/screen/food-flavourings/search/details/"
                        "POL-FFL-IMPORT-3388 (échantillon : D:/open_data/eu_food_flavourings/"
                        "food_flavourings_200.json)")},
    ]


# Meeting Copilot (doc v2, section 4.4) : checklist de rendez-vous, dans l'ordre de la doc.
CHECKLIST = {
    "client_objectives": "Objectifs du client",
    "real_need": "Besoin réel",
    "technical_constraints": "Contraintes techniques",
    "budget_constraints": "Contraintes budgétaires",
    "timeline": "Calendrier",
    "decision_criteria": "Critères de décision",
}
FICHIER_BANQUE = DOSSIER.parent / "questions" / "questions.json"

# Par opportunité : objectif du RDV, points déjà connus (avec le signal qui les apporte) et
# 3 questions. ("Q-xx", point) = question reprise de la banque ; sinon question rédigée ici.
CONTEXTE_RDV = {
    "O-01": {
        "objective": ("Comprendre les intentions du client concernant le développement d'une nouvelle gamme "
                      "et déterminer les contraintes associées."),
        "known": {},
        "questions": [("Q-01", "client_objectives"), ("Q-02", "technical_constraints"), ("Q-03", "timeline")],
    },
    "O-02": {
        "objective": "Recueillir le retour sur l'échantillon de P-01 et tester l'intérêt pour de nouvelles saveurs.",
        "known": {"technical_constraints": ("La gamme existante et son arôme agrumes sont connus : projet P-01 "
                                            "en cours, échantillon envoyé le 20/10/2026.", "S-03")},
        "questions": [
            ("Quelles saveurs aimeriez-vous voir rejoindre la gamme, et pour quels moments de consommation ?",
             "Fait émerger l'ambition du client pour sa gamme.", "client_objectives"),
            ("Qu'attendent vos clients de plus que ce que la gamme propose aujourd'hui ?",
             "Vérifie qu'il existe un vrai besoin d'extension.", "real_need"),
            ("Comment allez-vous juger le retour sur l'échantillon envoyé le 20/10 ?",
             "Montre sur quels critères le client décidera.", "decision_criteria"),
        ],
    },
    "O-03": {
        "objective": "Qualifier la demande sur les alternatives végétales : produit visé, ambition et contraintes.",
        "known": {"budget_constraints": ("Le client a communiqué une contrainte budgétaire pour ses prochains "
                                         "projets.", "S-07")},
        "questions": [("Q-13", "client_objectives"), ("Q-14", "real_need"), ("Q-15", "technical_constraints")],
    },
    "O-04": {
        "objective": "Comprendre le problème de texture de P-06 et ce qu'il faudrait pour le résoudre.",
        "known": {
            "technical_constraints": ("Texture de P-06 jugée trop épaisse en bouche (retour technique).", "S-06"),
            "budget_constraints": ("Le client a communiqué une contrainte budgétaire pour ses prochains "
                                   "projets.", "S-07"),
        },
        "questions": [
            ("Sur quels produits ce problème de texture se pose-t-il encore aujourd'hui ?",
             "Vérifie que le besoin d'amélioration existe toujours.", "real_need"),
            ("Quels critères utiliserez-vous pour juger qu'une nouvelle texture vous convient ?",
             "Donne les critères de réussite d'un nouvel essai.", "decision_criteria"),
            ("Quel calendrier envisagez-vous pour tester une version améliorée ?",
             "Mesure l'urgence et planifie les essais.", "timeline"),
        ],
    },
    "O-05": {
        "objective": "Identifier la formulation à optimiser et ce qui ne doit pas changer, dans le budget communiqué.",
        "known": {"budget_constraints": ("Le client a communiqué une contrainte budgétaire pour ses prochains "
                                         "projets.", "S-07")},
        "questions": [
            ("Quelle formulation existante souhaiteriez-vous optimiser en priorité, et pourquoi celle-là ?",
             "Précise le besoin réel derrière la contrainte budgétaire.", "real_need"),
            ("Quelles caractéristiques du produit ne doivent pas changer pendant l'optimisation ?",
             "Fixe les contraintes techniques avant tout essai.", "technical_constraints"),
            ("Comment arbitrerez-vous entre le coût et le goût ?",
             "Montre sur quels critères le client décidera.", "decision_criteria"),
        ],
    },
    "O-06": {
        "objective": "Découvrir les attentes du client pour sa marque de distributeur et tester l'intérêt pour des "
                     "arômes naturels.",
        "known": {},
        "questions": [
            ("Quelle place voulez-vous donner aux références naturelles dans votre marque de distributeur ?",
             "Fait émerger l'ambition du client pour sa marque.", "client_objectives"),
            ("Quelles attentes de vos clients voulez-vous couvrir avec une nouvelle référence aromatique ?",
             "Vérifie qu'il existe un besoin réel.", "real_need"),
            ("Sur quels critères choisissez-vous un nouvel arôme pour vos produits ?",
             "Montre sur quels critères le client décidera.", "decision_criteria"),
        ],
    },
}


def construire_contexte_rdv(banque):
    """meeting_context.json : objectif, points connus et manquants de la checklist, 3 questions."""
    par_id = {q["id"]: q for q in banque}
    contextes = []
    for opp_id, c in CONTEXTE_RDV.items():
        questions = []
        for q in c["questions"]:
            if len(q) == 2:  # reprise de la banque
                b = par_id[q[0]]
                questions.append({"id": q[0], "question": b["question"], "why": b["pourquoi"],
                                  "information_sought": q[1], "origin": "banque de questions"})
            else:
                questions.append({"id": f"{opp_id}-Q{len(questions) + 1}", "question": q[0], "why": q[1],
                                  "information_sought": q[2], "origin": "rédigée pour la démo"})
        contextes.append({
            "opportunity_id": opp_id,
            "objective": c["objective"],
            "known": [{"point": p, "information": info, "signal_id": s} for p, (info, s) in c["known"].items()],
            "missing": [p for p in CHECKLIST if p not in c["known"]],
            "questions": questions,
        })
    return contextes


def construire_opportunites(signaux):
    """Ajoute priority, calculée par la règle, juste après status (ordre des champs de la doc)."""
    resultat = []
    for o in OPPORTUNITES:
        o = dict(o)
        champs = list(o.items())
        i = [k for k, _ in champs].index("status") + 1
        resultat.append(dict(champs[:i] + [("priority", priorite(o, signaux))] + champs[i:]))
    return resultat


def texte_json(objets):
    return json.dumps(objets, ensure_ascii=False, indent=2) + "\n"


def generer():
    """Renvoie le texte JSON exact de clients.json, sans rien écrire."""
    return texte_json(CLIENTS)


def generer_fichiers(signaux_off=None, banque=None):
    """Renvoie {nom de fichier: texte JSON exact}, sans rien écrire."""
    if signaux_off is None:
        signaux_off = json.loads(FICHIER_OFF.read_text(encoding="utf-8"))
    if banque is None:
        banque = json.loads(FICHIER_BANQUE.read_text(encoding="utf-8"))["questions"]
    signaux = construire_signaux(signaux_off)
    return {
        "clients.json": generer(),
        "projects.json": texte_json(PROJETS),
        "opportunities.json": texte_json(construire_opportunites(signaux)),
        "signals.json": texte_json(signaux),
        "meeting_context.json": texte_json(construire_contexte_rdv(banque)),
    }


def main():
    for nom, texte in generer_fichiers().items():
        with open(DOSSIER / nom, "w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(texte)
        print(f"{nom} : {len(json.loads(texte))} objets")


if __name__ == "__main__":
    main()
