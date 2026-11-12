"""Génère data/demo_v2/clients.json : portefeuille de clients fictifs (doc fonctionnelle v2, DATA-US03).

Usage, depuis la racine du repo :
    python data/demo_v2/generer_demo_v2.py

Tout est fictif : aucun vrai client, aucun vrai nom de personne. Le fichier ne contient
aucun compteur (projets, opportunités) : ils seront calculés à partir des autres fichiers.
"""

import json
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


def generer():
    """Renvoie le texte JSON exact de clients.json, sans rien écrire."""
    return json.dumps(CLIENTS, ensure_ascii=False, indent=2) + "\n"


def main():
    with open(DOSSIER / "clients.json", "w", encoding="utf-8", newline="\n") as fichier:
        fichier.write(generer())
    print(f"clients.json : {len(CLIENTS)} clients")


if __name__ == "__main__":
    main()
