"""Détection des opportunités (DATA-US07) : applique data/demo_v2/regles_detection.json aux signaux
et aux projets de chaque client.

    from detection import charger_regles, detecter
    opportunites, signaux = detecter(clients, projets, signaux_bruts, charger_regles())

Entrée : signaux bruts, avec `client_id` (null pour un signal de marché) et `category` (catégorie
d'opportunité d'un signal de marché, null pour un signal client), sans `opportunity_id`.
Sortie : les opportunités détectées (id, client_id, title, category, status, rule_id, justification,
signal_ids) et une copie des signaux dont `opportunity_id` est rempli (None si non rattaché).
Les règles communes sont écrites en clair dans regles_detection.json.
"""

import json
import unicodedata
from pathlib import Path

FICHIER_REGLES = Path(__file__).resolve().parent / "regles_detection.json"


def charger_regles(chemin=FICHIER_REGLES):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))["regles"]


def normaliser(texte):
    """Minuscules, sans accents, apostrophes unifiées : la recherche de mots-clés y est insensible."""
    texte = unicodedata.normalize("NFKD", texte.replace("’", "'")).encode("ascii", "ignore").decode()
    return texte.lower()


def contient(texte, mot):
    return normaliser(mot) in normaliser(texte)


def projet_cite(signal, projets):
    """Le projet cité par source_ref (« data/demo_v2/projects.json#P-01 »), ou None."""
    ref = signal.get("source_ref") or ""
    if "projects.json#" not in ref:
        return None
    pid = ref.split("projects.json#")[1].split()[0]
    return next((p for p in projets if p["id"] == pid), None)


def declenche(regle, signal, projets):
    """Le signal remplit-il la condition de la règle (type, mot-clé, statut du projet cité) ?"""
    condition = regle["condition"]
    if signal["source_type"] not in condition["types_de_signaux"]:
        return False
    if not any(contient(signal["description"], m) for m in condition["mots_cles"]):
        return False
    if condition["statut_du_projet_cite"]:
        projet = projet_cite(signal, projets)
        if projet is None or projet["status"] != condition["statut_du_projet_cite"]:
            return False
    return True


def trouver_theme(regle, signaux):
    """Premier thème de la règle mentionné par un des signaux : (mot-clé, texte du titre) ou None."""
    for theme in regle["opportunite"]["themes"]:
        if any(contient(s["description"], theme["si_le_signal_contient"]) for s in signaux):
            return theme["si_le_signal_contient"], theme["dans_le_titre"]
    return None


def deja_engage(regle, theme, projets_client):
    """Un projet actif du client fait-il déjà ce que propose l'opportunité ?"""
    mots = []
    for mot in regle["deja_engage_si_un_projet_actif_contient"]:
        if "{theme}" in mot:
            if theme is None:
                continue
            mot = mot.replace("{theme}", theme[0])
        mots.append(mot)
    return any(contient(f"{p['name']} {p['description']}", m)
               for p in projets_client if p["status"] == "active" for m in mots)


def detecter(clients, projets, signaux, regles):
    """Renvoie (opportunités détectées, signaux avec opportunity_id rempli)."""
    opportunites, rattachement = [], {}
    for client in clients:
        propres = [s for s in signaux if s.get("client_id") == client["id"]]
        projets_client = [p for p in projets if p["client_id"] == client["id"]]
        for regle in regles:
            condition = regle["condition"]
            if condition["secteurs_client"] and client["sector"] not in condition["secteurs_client"]:
                continue
            declencheurs = [s for s in propres if declenche(regle, s, projets)]
            if len(declencheurs) < condition["nombre_min_signaux"]:
                continue
            if all(s["evidence_type"] == "hypothesis" for s in declencheurs):
                continue  # une hypothèse seule ne suffit pas
            theme = trouver_theme(regle, declencheurs)
            if deja_engage(regle, theme, projets_client):
                continue
            sortie = regle["opportunite"]
            libelle = theme[1] if theme else sortie["theme_par_defaut"]
            opp = {
                "id": f"O-{len(opportunites) + 1:02d}",
                "client_id": client["id"],
                "title": sortie["titre_type"].replace("{theme}", libelle or ""),
                "category": sortie["categorie"],
                "status": regle["statut_initial"],
                "rule_id": regle["id"],
                "justification": regle["justification_type"],
                "theme": theme[0] if theme else None,
                "signal_ids": [s["id"] for s in declencheurs],
            }
            for s in declencheurs:
                if s["id"] in rattachement:
                    raise ValueError(f"{s['id']} déclenche deux opportunités ({rattachement[s['id']]}, {opp['id']}) : "
                                     "un signal n'est rattaché qu'à une opportunité.")
                rattachement[s["id"]] = opp["id"]
            opportunites.append(opp)

    for s in signaux:
        if s.get("client_id") is not None:
            continue
        cibles = [o for o in opportunites if o["category"] == s.get("category")
                  and (o["theme"] is None or contient(s["description"], o["theme"]))]
        if len(cibles) > 1:
            raise ValueError(f"Signal de marché {s['id']} rattachable à plusieurs opportunités "
                             f"({', '.join(o['id'] for o in cibles)}) : un signal n'a qu'une opportunité.")
        if cibles:
            rattachement[s["id"]] = cibles[0]["id"]
            cibles[0]["signal_ids"].append(s["id"])

    signaux_sortie = [{**s, "opportunity_id": rattachement.get(s["id"])} for s in signaux]
    return opportunites, signaux_sortie
