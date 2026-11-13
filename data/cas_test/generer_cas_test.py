"""Génère 30 cas de test fictifs pour valider l'extraction de la checklist.

Usage : python data/cas_test/generer_cas_test.py

Bibliothèque standard uniquement, graine 42, date de référence fixe 2026-11-12.
Sorties dans data/cas_test/sorties/ :
  - interactions.csv     : 5 à 10 interactions datées par client, étapes dans l'ordre ;
                           seul le dernier compte rendu de chaque client a evalue = true.
  - verite_terrain.json  : pour chaque compte rendu évalué, points présents / manquants,
                           contradiction de calendrier, hors sujet.

Scénarios (30 clients T-01 à T-30) : 10 complets, 10 partiels (2 à 4 points),
5 avec contradiction de calendrier, 5 hors sujet (suivi de livraison, aucun point).
Tous les clients et contenus sont fictifs.
"""

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

GRAINE = 42
DATE_REFERENCE = date(2026, 11, 12)
SORTIES = Path(__file__).resolve().parent / "sorties"

POINTS = [
    "client_objectives",
    "real_need",
    "technical_constraints",
    "budget_constraints",
    "timeline",
    "decision_criteria",
]

SEGMENTS = {
    "Savoury": "Taste & Wellbeing",
    "Beverages": "Taste & Wellbeing",
    "Sweet Goods": "Taste & Wellbeing",
    "Dairy": "Taste & Wellbeing",
    "Fine Fragrance": "Fragrance & Beauty",
    "Consumer Products": "Fragrance & Beauty",
}

ETAPES = ["prospection", "decouverte", "qualification", "proposition", "negociation", "closing"]

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"]
MOIS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]

# Contenu métier selon l'activité : arôme pour Taste & Wellbeing, parfum pour Fragrance & Beauty.
CONTENU = {
    "Taste & Wellbeing": {
        "objectif_fr": ["relancer sa gamme de bouillons", "réduire le sucre de ses boissons de 30 %",
                        "lancer une crème glacée vegan", "rajeunir sa gamme de biscuits"],
        "objectif_en": ["revamp its soup range", "cut sugar in its drinks by 30%",
                        "launch a vegan ice cream", "refresh its biscuit line"],
        "besoin_fr": ["un arôme vanille naturel", "un arôme fumé sans additif", "un arôme agrumes masquant l'amertume"],
        "besoin_en": ["a natural vanilla flavour", "a clean-label smoky flavour", "a citrus flavour that masks bitterness"],
        "contrainte_fr": ["l'arôme doit tenir une cuisson à 180 °C", "étiquetage « naturel » obligatoire", "stabilité à pH 3 exigée"],
        "contrainte_en": ["the flavour must survive baking at 180 °C", "natural labelling is mandatory", "it must stay stable at pH 3"],
    },
    "Fragrance & Beauty": {
        "objectif_fr": ["lancer un parfum féminin premium", "renouveler l'odeur de sa lessive phare",
                        "créer une ligne de bougies parfumées"],
        "objectif_en": ["launch a premium women's fragrance", "renew the scent of its flagship detergent",
                        "create a scented candle line"],
        "besoin_fr": ["un parfum boisé ambré", "une note fraîche qui tient après lavage", "un parfum floral sans allergène déclaré"],
        "besoin_en": ["a woody amber fragrance", "a fresh note that lasts after washing", "a floral scent without declarable allergens"],
        "contrainte_fr": ["la formule doit rester stable en base alcool", "aucun allergène IFRA au-dessus des seuils", "compatibilité avec une base tensioactive"],
        "contrainte_en": ["the formula must stay stable in an alcohol base", "no IFRA allergens above thresholds", "it must be compatible with a surfactant base"],
    },
}

CRITERES_FR = ["le coût et la tenue", "la qualité sensorielle lors du test consommateur", "le prix et le délai de livraison"]
CRITERES_EN = ["cost and performance", "sensory quality in the consumer test", "price and lead time"]


def phrase(point, langue, activite, rng):
    """Phrase qui couvre un point de la checklist."""
    c = CONTENU[activite]
    annee = rng.choice([2027, 2028])
    m = rng.randrange(12)
    if langue == "fr":
        choix = {
            "client_objectives": [f"Le client veut {rng.choice(c['objectif_fr'])}.",
                                  f"Leur objectif : {rng.choice(c['objectif_fr'])}."],
            "real_need": [f"Le vrai besoin, c'est {rng.choice(c['besoin_fr'])}.",
                          f"Il leur faut {rng.choice(c['besoin_fr'])}."],
            "technical_constraints": [f"Contrainte technique : {rng.choice(c['contrainte_fr'])}.",
                                      f"Côté technique, {rng.choice(c['contrainte_fr'])}."],
            "budget_constraints": [f"Le budget est plafonné à {rng.randint(20, 90)} € le kilo.",
                                   f"Enveloppe de {rng.randint(50, 400)} k€ pour le projet."],
            "timeline": [f"Lancement prévu en {MOIS_FR[m]} {annee}.",
                         f"Mise sur le marché visée pour {MOIS_FR[m]} {annee}."],
            "decision_criteria": [f"Ils trancheront selon {rng.choice(CRITERES_FR)}.",
                                  f"Critères de choix : {rng.choice(CRITERES_FR)}."],
        }
    else:
        choix = {
            "client_objectives": [f"The customer wants to {rng.choice(c['objectif_en'])}.",
                                  f"Their goal is to {rng.choice(c['objectif_en'])}."],
            "real_need": [f"What they really need is {rng.choice(c['besoin_en'])}.",
                          f"The underlying need: {rng.choice(c['besoin_en'])}."],
            "technical_constraints": [f"Technical constraint: {rng.choice(c['contrainte_en'])}.",
                                      f"On the technical side, {rng.choice(c['contrainte_en'])}."],
            "budget_constraints": [f"Budget is capped at {rng.randint(20, 90)} EUR per kg.",
                                   f"They have set aside {rng.randint(50, 400)}k EUR for the project."],
            "timeline": [f"Launch planned for {MOIS_EN[m]} {annee}.",
                         f"Target go-to-market: {MOIS_EN[m]} {annee}."],
            "decision_criteria": [f"They will decide based on {rng.choice(CRITERES_EN)}.",
                                  f"Selection criteria: {rng.choice(CRITERES_EN)}."],
        }
    return rng.choice(choix[point])


def phrase_contradiction(langue, rng):
    """Calendrier avec deux dates différentes."""
    annee = rng.choice([2027, 2028])
    m1, m2 = rng.sample(range(12), 2)
    if langue == "fr":
        return (f"Lancement prévu en {MOIS_FR[m1]} {annee}. Plus tard dans la réunion, "
                f"l'acheteur a parlé d'une sortie en {MOIS_FR[m2]} {annee}.")
    return (f"Launch planned for {MOIS_EN[m1]} {annee}. Later in the meeting, "
            f"the buyer mentioned a release in {MOIS_EN[m2]} {annee}.")


def phrase_hors_sujet(langue, rng):
    commande = rng.randint(1000, 9999)
    if langue == "fr":
        return rng.choice([
            f"Suivi de livraison de la commande {commande} : le transporteur a deux jours de retard, colis attendu jeudi.",
            f"Appel logistique : la palette de la commande {commande} est bloquée en douane, bon de livraison renvoyé.",
        ])
    return rng.choice([
        f"Delivery follow-up on order {commande}: the carrier is two days late, parcel expected Thursday.",
        f"Logistics call: the pallet for order {commande} is held at customs, delivery note resent.",
    ])


def phrase_contexte(etape, langue, rng):
    """Compte rendu court des interactions non évaluées."""
    fr = {
        "prospection": "Premier contact, présentation de Givaudan.",
        "decouverte": "Visite du site et échange sur la gamme actuelle.",
        "qualification": "Point avec l'équipe R&D du client.",
        "proposition": "Envoi des échantillons et de la fiche produit.",
        "negociation": "Échange sur les conditions commerciales.",
        "closing": "Relecture du contrat avec les achats.",
    }
    en = {
        "prospection": "First contact, Givaudan introduction.",
        "decouverte": "Site visit and talk about the current range.",
        "qualification": "Meeting with the customer's R&D team.",
        "proposition": "Samples and product sheet sent.",
        "negociation": "Discussion of commercial terms.",
        "closing": "Contract review with procurement.",
    }
    return (fr if langue == "fr" else en)[etape]


def main():
    rng = random.Random(GRAINE)
    scenarios = ["complet"] * 10 + ["partiel"] * 10 + ["contradiction"] * 5 + ["hors_sujet"] * 5
    rng.shuffle(scenarios)
    segments = list(SEGMENTS)

    lignes, verite = [], []
    for i, scenario in enumerate(scenarios, start=1):
        client_id = f"T-{i:02d}"
        segment = segments[(i - 1) % len(segments)]
        activite = SEGMENTS[segment]
        langue = rng.choice(["fr", "en"])

        # Points présents selon le scénario.
        if scenario == "complet":
            presents = list(POINTS)
        elif scenario == "partiel":
            presents = rng.sample(POINTS, rng.randint(2, 4))
        elif scenario == "contradiction":
            autres = [p for p in POINTS if p != "timeline"]
            presents = ["timeline"] + rng.sample(autres, rng.randint(2, 4))
        else:
            presents = []
        presents = [p for p in POINTS if p in presents]  # ordre stable

        # Compte rendu évalué.
        if scenario == "hors_sujet":
            texte = phrase_hors_sujet(langue, rng)
        else:
            morceaux = []
            for p in presents:
                if p == "timeline" and scenario == "contradiction":
                    morceaux.append(phrase_contradiction(langue, rng))
                else:
                    morceaux.append(phrase(p, langue, activite, rng))
            rng.shuffle(morceaux)
            texte = " ".join(morceaux)

        # Historique : n interactions, dates croissantes, étapes qui avancent dans l'ordre.
        n = rng.randint(5, 10)
        ecarts = [rng.randint(5, 30) for _ in range(n - 1)]
        derniere = DATE_REFERENCE - timedelta(days=rng.randint(0, 10))
        dates = [derniere]
        for e in reversed(ecarts):
            dates.insert(0, dates[0] - timedelta(days=e))
        etapes = sorted(rng.choices(range(len(ETAPES)), k=n))

        for k in range(n):
            evalue = k == n - 1
            etape = ETAPES[etapes[k]]
            lignes.append({
                "interaction_id": f"{client_id}-I{k + 1:02d}",
                "client_id": client_id,
                "client_nom": f"Client test {client_id}",
                "segment": segment,
                "activite": activite,
                "date": dates[k].isoformat(),
                "etape": etape,
                "langue": langue,
                "compte_rendu": texte if evalue else phrase_contexte(etape, langue, rng),
                "evalue": "true" if evalue else "false",
            })

        verite.append({
            "client_id": client_id,
            "interaction_id": f"{client_id}-I{n:02d}",
            "scenario": scenario,
            "langue": langue,
            "points_presents": presents,
            "points_manquants": [p for p in POINTS if p not in presents],
            "contradiction": scenario == "contradiction",
            "hors_sujet": scenario == "hors_sujet",
        })

    SORTIES.mkdir(parents=True, exist_ok=True)
    with open(SORTIES / "interactions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    with open(SORTIES / "verite_terrain.json", "w", encoding="utf-8") as f:
        json.dump({"date_reference": DATE_REFERENCE.isoformat(), "graine": GRAINE, "cas": verite},
                  f, ensure_ascii=False, indent=2)
    print(f"{len(lignes)} interactions, {len(verite)} cas évalués -> {SORTIES}")


if __name__ == "__main__":
    main()
