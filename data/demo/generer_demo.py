"""Génère le jeu de données de démo de l'app (data/demo/*.json).

Usage : python data/demo/generer_demo.py

Bibliothèque standard uniquement. Les questions viennent de
data/questions/questions.json : aucune question n'est recopiée ici.
Les signaux de marché viennent de data/signaux/signaux_marche.json (Open Food
Facts, ODbL). Les noms, montants et signaux client sont fictifs.
"""

import json
import re
from pathlib import Path

DOSSIER_DEMO = Path(__file__).resolve().parent
BANQUE = DOSSIER_DEMO.parent / "questions" / "questions.json"
SIGNAUX = DOSSIER_DEMO.parent / "signaux" / "signaux_marche.json"

# Emplacement du signal de marché réel dans la liste des triggers d'une opportunité.
SIGNAL_MARCHE = object()

AUTEUR_SENIOR = "Commercial Senior (démo)"

CLIENTS = [
    # id, name, sector, status, opportunityIds
    ("C-01", "Boissons Altitude", "Boissons & Snacks", "strategic", ["OPP-01", "OPP-02", "OPP-03", "OPP-11"]),
    ("C-02", "Laiterie Clairval", "Produits laitiers", "active", ["OPP-04", "OPP-10"]),
    ("C-03", "Verdane Foods", "Produits végétaux", "to_develop", ["OPP-05"]),
    ("C-04", "Brasserie Orvane", "Boissons", "active", ["OPP-06"]),
    ("C-05", "Saveurs Marcelin", "Plats préparés", "active", ["OPP-07", "OPP-08"]),
    ("C-06", "Vitalpas Nutrition", "Nutrition sportive", "to_develop", ["OPP-09"]),
    ("C-07", "Confiserie Belmonde", "Confiserie", "to_develop", ["OPP-12"]),
    ("C-08", "Maison Ilvane", "Cosmétique", "active", []),  # pastille grise « Aucune »
]

# Données propres à chaque opportunité ; le titre et les questions viennent de la banque.
# Triggers : texte = signal client fictif ; SIGNAL_MARCHE = signal réel Open Food Facts.
# Le nombre de triggers qui comptent fixe la priorité (règle 2 : 3+ -> high, 2 -> medium, sinon watch).
OPPORTUNITES = {
    "OPP-01": {
        "category": "Santé et bien-être",
        "estimatedRevenue": 1_800_000,
        "description": "Le client envisage une gamme de boissons à bénéfice fonctionnel.",
        "triggers": ["Intérêt exprimé pour une nouvelle catégorie", SIGNAL_MARCHE,
                     "Lancement concurrent récent"],
    },
    "OPP-02": {
        "category": "Durabilité",
        "estimatedRevenue": 1_200_000,
        "description": "Le client veut rendre ses snacks plus responsables sans perdre en goût.",
        "triggers": ["Engagement environnemental annoncé", "Demande des distributeurs : recettes plus durables",
                     SIGNAL_MARCHE],
    },
    "OPP-03": {
        "category": "Premiumisation",
        "estimatedRevenue": 900_000,
        "description": "Le client étudie une montée en gamme sur une partie de son offre.",
        "triggers": ["Montée en gamme évoquée en RDV", SIGNAL_MARCHE],
    },
    "OPP-04": {
        "category": "Reformulation",
        "estimatedRevenue": 1_100_000,
        "description": "Le client doit réduire le sucre de ses recettes en gardant leur goût.",
        "triggers": ["Objectif de réduction du sucre annoncé", "Évolution réglementaire attendue",
                     "Retours consommateurs sur le goût trop sucré"],
    },
    "OPP-05": {
        "category": "Végétal",
        "estimatedRevenue": 650_000,
        "description": "Le client veut élargir sa gamme de produits à base de protéines végétales.",
        "triggers": [SIGNAL_MARCHE, "Intérêt exprimé pour une gamme végétale"],
    },
    "OPP-06": {
        "category": "Nouvelle catégorie",
        "estimatedRevenue": 750_000,
        "description": "Le client prépare une boisson sans alcool pour de nouvelles occasions de consommation.",
        "triggers": [SIGNAL_MARCHE, "Projet de nouvelle boisson évoqué en RDV",
                     "Demande des distributeurs : alternatives sans alcool"],
    },
    "OPP-07": {
        "category": "Reformulation",
        "estimatedRevenue": 500_000,
        "description": "Le client doit baisser le sel de ses plats sans les rendre fades.",
        "triggers": ["Objectif de réduction du sel annoncé", "Évolution réglementaire attendue"],
    },
    "OPP-08": {
        "category": "Naturalité",
        "estimatedRevenue": 400_000,
        "description": "Le client souhaite des listes d'ingrédients plus courtes et plus lisibles.",
        "triggers": ["Intérêt exprimé pour des étiquettes plus courtes"],
    },
    "OPP-09": {
        "category": "Santé et bien-être",
        "estimatedRevenue": 350_000,
        "description": "Le client cherche à améliorer le goût de ses produits protéinés.",
        "triggers": [SIGNAL_MARCHE],
    },
    "OPP-10": {
        "category": "Santé et bien-être",
        "estimatedRevenue": 800_000,
        "description": "Le client veut développer une gamme orientée bien-être digestif.",
        "triggers": ["Intérêt exprimé pour des produits bien-être", SIGNAL_MARCHE],
    },
    "OPP-11": {
        "category": "Innovation goût",
        "estimatedRevenue": 600_000,
        "description": "Le client veut attirer les jeunes consommateurs avec des saveurs du monde.",
        "triggers": ["Succès des saveurs du monde chez les 18-25 ans"],
    },
    "OPP-12": {
        "category": "Relance de gamme",
        "estimatedRevenue": 300_000,
        "description": "Le client veut relancer une gamme dont les ventes baissent.",
        "triggers": ["Baisse des ventes de la gamme : -6 %"],
    },
}

BONNES_PRATIQUES = [
    # id, title, questionId, phrase d'explication ajoutée après la question
    ("BP-01", "Comprendre les ambitions du client", "Q-01",
     "Une question ouverte sur ses projets fait parler le client de ses priorités avant de parler produit."),
    ("BP-02", "Faire nommer le frein principal", "Q-02",
     "Le frein nommé par le client montre où notre offre peut vraiment aider."),
    ("BP-03", "Demander une référence concrète", "Q-09",
     "Un produit de référence cadre mieux le goût recherché qu'une liste d'adjectifs."),
    ("BP-04", "Chiffrer le budget tôt", "Q-18",
     "Un budget chiffré dès le premier RDV évite de proposer des pistes hors de portée."),
    ("BP-05", "Faire décrire la perte de goût", "Q-20",
     "La perte décrite par le client donne la cible que la solution devra atteindre."),
]

UTILISATEURS = [
    {"id": "U-JUNIOR", "name": "Commercial Junior (démo)", "role": "junior"},
    {"id": "U-SENIOR", "name": AUTEUR_SENIOR, "role": "senior"},
]


def priorite(nb_triggers_comptes):
    """Règle 2 de la doc, sur les triggers qui comptent : 3 ou plus -> high, 2 -> medium, 0 ou 1 -> watch."""
    if nb_triggers_comptes >= 3:
        return "high"
    if nb_triggers_comptes == 2:
        return "medium"
    return "watch"


def charger_signaux(chemin=SIGNAUX):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def construire_triggers(triggers, signal, source):
    """Triggers au format {text, type, counted, source} : real (Open Food Facts) ou fictional."""
    resultat = []
    for trigger in triggers:
        if trigger is SIGNAL_MARCHE:
            if signal is None:
                raise ValueError("Signal de marché demandé mais absent de signaux_marche.json")
            resultat.append({"text": signal["trigger"], "type": "real", "counted": signal["compte"],
                             "source": source})
        else:
            resultat.append({"text": trigger, "type": "fictional", "counted": True, "source": None})
    return resultat


def titre(libelle):
    """Libellé de la banque sans « (hypothèse) »."""
    return re.sub(r"\s*\(hypothèse\)", "", libelle).strip()


def charger_banque(chemin=BANQUE):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)["questions"]


def construire(banque, signaux):
    """Renvoie {nom de fichier: liste d'objets}."""
    client_de = {opp: cid for cid, _, _, _, opps in CLIENTS for opp in opps}
    signal_de = {s["opportunite_id"]: s["signal"] for s in signaux["signaux"]}
    source = (f"{signaux['source']['nom']} ({signaux['source']['licence'].split(' (')[0]}), "
              f"données au {signaux['source']['dernier_produit_ajoute']}, "
              f"extraites le {signaux['date_extraction']} — data/signaux/signaux_marche.json")
    triggers_de = {opp: construire_triggers(d["triggers"], signal_de.get(opp), source)
                   for opp, d in OPPORTUNITES.items()}
    questions_de = {}
    libelle_de = {}
    for q in banque:
        questions_de.setdefault(q["opportunite_id"], []).append(q["id"])
        libelle_de[q["opportunite_id"]] = q["opportunite"]
    validees = {qid for _, _, qid, _ in BONNES_PRATIQUES}
    texte_de = {q["id"]: q["question"] for q in banque}

    clients = [
        {"id": cid, "name": nom, "sector": secteur, "status": statut, "opportunityIds": opps}
        for cid, nom, secteur, statut, opps in CLIENTS
    ]
    opportunities = [
        {
            "id": opp,
            "clientId": client_de[opp],
            "title": titre(libelle_de[opp]),
            "category": d["category"],
            "priority": priorite(sum(t["counted"] for t in triggers_de[opp])),
            "estimatedRevenue": d["estimatedRevenue"],
            "description": d["description"],
            "triggers": triggers_de[opp],
            "recommendedQuestions": questions_de[opp],
        }
        for opp, d in OPPORTUNITES.items()
    ]
    questions = [
        {
            "id": q["id"],
            "opportunityId": q["opportunite_id"],
            "text": q["question"],
            "justification": q["pourquoi"],
            "status": "validated" if q["id"] in validees else "suggested",
            "step": q["etape"],
            "briefField": q["champ_brief"],
        }
        for q in banque
    ]
    best_practices = [
        {"id": bid, "title": titre_bp, "content": f"{texte_de[qid]} {explication}",
         "author": AUTEUR_SENIOR, "status": "validated", "questionId": qid}
        for bid, titre_bp, qid, explication in BONNES_PRATIQUES
    ]
    meetings = [
        {
            "id": "M-01",
            "clientId": "C-01",
            "opportunityId": "OPP-01",
            "date": "2026-10-20",  # extension de la section 9.3 ; date fictive, passée
            "questionsAsked": questions_de["OPP-01"],
            "customerFeedback": "Intérêt pour une boisson fonctionnelle aux agrumes ; "
                                "un premier test est envisagé au printemps.",
            "status": "completed",
        },
        {
            "id": "M-02",
            "clientId": "C-04",
            "opportunityId": "OPP-06",
            "date": "2026-11-18",  # date fictive, à venir
            "questionsAsked": [],
            "customerFeedback": None,
            "status": "planned",
        },
    ]
    return {
        "clients.json": clients,
        "opportunities.json": opportunities,
        "questions.json": questions,
        "best_practices.json": best_practices,
        "users.json": UTILISATEURS,
        "meetings.json": meetings,
    }


def generer_fichiers(banque=None, signaux=None):
    """Renvoie {nom de fichier: texte JSON exact}, sans rien écrire."""
    objets = construire(charger_banque() if banque is None else banque,
                        charger_signaux() if signaux is None else signaux)
    return {nom: json.dumps(liste, ensure_ascii=False, indent=2) + "\n" for nom, liste in objets.items()}


def main():
    for nom, texte in generer_fichiers().items():
        with open(DOSSIER_DEMO / nom, "w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(texte)
        print(f"{nom} : {len(json.loads(texte))} objets")


if __name__ == "__main__":
    main()
