"""Génère data/demo_v2 : clients fictifs (DATA-US03) et leurs projets (DATA-US04), doc fonctionnelle v2.

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


def texte_json(objets):
    return json.dumps(objets, ensure_ascii=False, indent=2) + "\n"


def generer():
    """Renvoie le texte JSON exact de clients.json, sans rien écrire."""
    return texte_json(CLIENTS)


def generer_fichiers():
    """Renvoie {nom de fichier: texte JSON exact}, sans rien écrire."""
    return {"clients.json": generer(), "projects.json": texte_json(PROJETS)}


def main():
    for nom, texte in generer_fichiers().items():
        with open(DOSSIER / nom, "w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(texte)
        print(f"{nom} : {len(json.loads(texte))} objets")


if __name__ == "__main__":
    main()
