"""Convertit questions_source.csv en questions.json (bibliothèque standard uniquement).

Usage : python data/questions/convertir.py

Le CSV est l'export de la banque de questions : UTF-8 avec BOM, séparateur
virgule, champs entre guillemets quand ils contiennent une virgule.
"""

import csv
import json
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
SOURCE = DOSSIER / "questions_source.csv"
CIBLE = DOSSIER / "questions.json"

# En-tête du CSV -> clé du JSON
COLONNES = {
    "ID": "id",
    "Étape du gabarit": "etape",
    "Question": "question",
    "Pourquoi cette question": "pourquoi",
    "Champ du brief (schéma v1.0)": "champ_brief",
    "Origine": "origine",
    "Statut": "statut",
    "Validée par": "validee_par",
    "Commentaire du senior": "commentaire_senior",
}
COLONNE_OPPORTUNITE = "Opportunité"  # ex. « OPP-01 · Boissons fonctionnelles »
SEPARATEUR_OPPORTUNITE = "·"


def nettoyer(valeur):
    """Supprime les espaces autour ; cellule vide -> None (null en JSON)."""
    if valeur is None:
        return None
    valeur = valeur.strip()
    return valeur or None


def decouper_opportunite(valeur):
    """« OPP-01 · Boissons fonctionnelles » -> ("OPP-01", "Boissons fonctionnelles")."""
    valeur = nettoyer(valeur)
    if valeur is None:
        return None, None
    if SEPARATEUR_OPPORTUNITE not in valeur:
        raise ValueError(f"Opportunité sans « {SEPARATEUR_OPPORTUNITE} » : {valeur!r}")
    identifiant, libelle = valeur.split(SEPARATEUR_OPPORTUNITE, 1)
    return nettoyer(identifiant), nettoyer(libelle)


def numero(question):
    """Q-07 -> 7, pour trier par id sans dépendre du nombre de chiffres."""
    return int(question["id"].split("-")[-1])


def lire_csv(chemin):
    # utf-8-sig retire le BOM s'il est présent (et fonctionne aussi sans BOM)
    with open(chemin, encoding="utf-8-sig", newline="") as fichier:
        lecteur = csv.DictReader(fichier, delimiter=",")
        manquantes = (set(COLONNES) | {COLONNE_OPPORTUNITE}) - set(lecteur.fieldnames or [])
        if manquantes:
            raise ValueError(f"Colonnes manquantes dans {chemin.name} : {sorted(manquantes)}")

        questions = []
        for ligne in lecteur:
            if not any((v or "").strip() for v in ligne.values()):
                continue  # ligne vide
            opp_id, opp = decouper_opportunite(ligne[COLONNE_OPPORTUNITE])
            question = {"id": nettoyer(ligne["ID"]), "opportunite_id": opp_id, "opportunite": opp}
            for entete, cle in COLONNES.items():
                if cle != "id":
                    question[cle] = nettoyer(ligne[entete])
            questions.append(question)
    return sorted(questions, key=numero)


def generer_json(chemin=SOURCE):
    """Texte exact de questions.json produit à partir du CSV (sans rien écrire)."""
    sortie = {"version": "1.0", "source": chemin.name, "questions": lire_csv(chemin)}
    return json.dumps(sortie, ensure_ascii=False, indent=2) + "\n"


def main():
    texte = generer_json()
    with open(CIBLE, "w", encoding="utf-8", newline="\n") as fichier:
        fichier.write(texte)
    nombre = len(json.loads(texte)["questions"])
    print(f"{nombre} questions -> {CIBLE.name}")  # ASCII : lisible dans toute console


if __name__ == "__main__":
    main()
