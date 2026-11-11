"""Moteur V1 par règles (sans LLM) : propose les questions à poser au prochain RDV.

Bibliothèque standard uniquement.

Exemples :
    python data/questions/moteur.py --champs objectif,brief.contraintes.regime
    python data/questions/moteur.py --brief data/questions/exemples/brief_exemple.json
    python data/questions/moteur.py --champs marche --opportunite OPP-09 --nb 2
"""

import argparse
import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

FICHIER_QUESTIONS = Path(__file__).resolve().parent / "questions.json"

# Ordre de priorité des champs du brief (schéma v1.0) — à valider avec l'équipe
# et les seniors.
PRIORITE_CHAMPS = [
    "objectif",
    "echeance_lancement",
    "budget_matiere_eur_par_litre",
    "contraintes",
    "marche",
    "profil_gout",
    "insights_concurrence",
]
STATUT_EXCLU = "À modifier"
RANG_STATUT = {"Validée": 0, "Suggérée": 1}  # plus petit = préféré
NON_RENSEIGNE = "non renseigné"
PREFIXE_BRIEF = "brief."
SEPARATEUR_GRILLE = ";"  # colonne questions_proposees de data/eval/grille_fiabilite.csv

# Déduction de l'opportunité à partir du brief
CHAMPS_POUR_OPPORTUNITE = ["objectif", "marche", "profil_gout"]
MOTS_VIDES = {
    "de", "des", "du", "d", "la", "le", "les", "l", "un", "une", "pour", "et", "en", "au", "aux",
    # présents dans presque tous les briefs : faussaient le choix (ex. « marché » -> OPP-03)
    "marche", "gamme",
}
MOTS_GARDES_AVEC_S = {"sans"}  # « sans » est gardé tel quel (utile pour « sans alcool »)


def charger_banque(chemin=FICHIER_QUESTIONS):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)["questions"]


def normaliser_champ(nom):
    """« brief.contraintes.regime » -> « contraintes ». Champ inconnu -> None + avertissement."""
    champ = (nom or "").strip()
    if champ.startswith(PREFIXE_BRIEF):
        champ = champ[len(PREFIXE_BRIEF):]
    if champ.startswith("contraintes."):
        champ = "contraintes"
    if champ not in PRIORITE_CHAMPS:
        warnings.warn(f"Champ inconnu ignoré : {nom!r}", UserWarning, stacklevel=3)
        return None
    return champ


def normaliser_champs(noms):
    """Normalise, retire les doublons et range dans l'ordre de priorité."""
    champs = {normaliser_champ(nom) for nom in noms}
    return [c for c in PRIORITE_CHAMPS if c in champs]


def _numero(question):
    return int(question["id"].split("-")[-1])


def proposer_questions(champs_manquants, opportunite_id=None, nb=3, banque=None):
    """Renvoie au plus `nb` questions (id, question, pourquoi, champ_brief).

    Règles :
    - seuls les champs manquants sont couverts, dans l'ordre de PRIORITE_CHAMPS ;
    - une question par champ, puis, s'il manque moins de `nb` champs, une
      2e question par champ manquant (toujours dans l'ordre de priorité) ;
    - questions « À modifier » exclues ;
    - pour un même champ : d'abord l'opportunité demandée, puis « Validée »
      avant « Suggérée », puis l'id le plus petit.
    """
    if banque is None:
        banque = charger_banque()
    champs = normaliser_champs(champs_manquants)
    if not champs or nb <= 0:
        return []

    if opportunite_id and not any(q["opportunite_id"] == opportunite_id for q in banque):
        warnings.warn(f"Opportunité inconnue : {opportunite_id!r}", UserWarning, stacklevel=2)

    def cle_tri(q):
        hors_opportunite = bool(opportunite_id) and q["opportunite_id"] != opportunite_id
        return (hors_opportunite, RANG_STATUT.get(q["statut"], len(RANG_STATUT)), _numero(q))

    candidats = {
        champ: sorted(
            (q for q in banque if q["champ_brief"] == champ and q["statut"] != STATUT_EXCLU),
            key=cle_tri,
        )
        for champ in champs
    }

    tours = 2 if len(champs) < nb else 1
    retenues = []
    for tour in range(tours):
        for champ in champs:
            if len(retenues) == nb:
                break
            if len(candidats[champ]) > tour:
                retenues.append(candidats[champ][tour])

    return [
        {"id": q["id"], "question": q["question"], "pourquoi": q["pourquoi"], "champ_brief": q["champ_brief"]}
        for q in retenues
    ]


def ids_pour_grille(questions):
    """Ids joints par « ; » pour la colonne questions_proposees de la grille de fiabilité."""
    return SEPARATEUR_GRILLE.join(q["id"] for q in questions)


def _non_renseigne(valeur):
    if isinstance(valeur, str):
        return valeur.strip().lower() == NON_RENSEIGNE
    if isinstance(valeur, list):  # ex. ["non renseigné"] ; une liste vide n'est pas comptée
        return bool(valeur) and all(_non_renseigne(v) for v in valeur)
    return False


def champs_depuis_brief(brief):
    """incertitudes.champs_manquants + champs du bloc « brief » qui valent « non renseigné »."""
    champs = list((brief.get("incertitudes") or {}).get("champs_manquants") or [])
    for cle, valeur in (brief.get("brief") or {}).items():
        if isinstance(valeur, dict):
            champs += [f"{cle}.{sous}" for sous, v in valeur.items() if _non_renseigne(v)]
        elif _non_renseigne(valeur):
            champs.append(cle)
    return champs


def mots_significatifs(texte):
    """Minuscules, sans accents, sans « s » final, sans mots vides ; « (hypothèse) » ignoré."""
    texte = re.sub(r"\(.*?\)", " ", texte or "")
    texte = unicodedata.normalize("NFKD", texte.lower()).encode("ascii", "ignore").decode("ascii")
    mots = set()
    for mot in re.findall(r"[a-z0-9]+", texte):
        if mot.endswith("s") and len(mot) > 1 and mot not in MOTS_GARDES_AVEC_S:
            mot = mot[:-1]
        if mot not in MOTS_VIDES:
            mots.add(mot)
    return mots


def deduire_opportunite(brief, banque=None):
    """Opportunité dont le libellé partage le plus de mots avec objectif, marche et profil_gout.

    Égalité -> id le plus petit ; aucun mot commun -> (None, []).
    Renvoie (opportunite_id, mots communs triés).
    """
    if banque is None:
        banque = charger_banque()
    bloc = brief.get("brief") or {}
    textes = []
    for champ in CHAMPS_POUR_OPPORTUNITE:
        valeur = bloc.get(champ)
        for texte in valeur if isinstance(valeur, list) else [valeur]:
            if isinstance(texte, str) and not _non_renseigne(texte):
                textes.append(texte)
    mots_brief = mots_significatifs(" ".join(textes))

    libelles = {q["opportunite_id"]: q["opportunite"] for q in banque}
    meilleure, meilleurs_mots = None, set()
    for opp in sorted(libelles, key=lambda o: int(o.split("-")[-1])):
        communs = mots_brief & mots_significatifs(libelles[opp])
        if len(communs) > len(meilleurs_mots):  # strictement plus : l'id le plus petit gagne les égalités
            meilleure, meilleurs_mots = opp, communs
    return meilleure, sorted(meilleurs_mots)


def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")  # accents lisibles même si la sortie est redirigée
    warnings.formatwarning = lambda message, *_args, **_kwargs: f"Avertissement : {message}\n"
    parser = argparse.ArgumentParser(description="Propose les questions à poser au prochain RDV.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--champs", help="champs manquants séparés par des virgules")
    source.add_argument("--brief", type=Path, help="brief JSON au format du schéma v1.0")
    parser.add_argument("--opportunite", help="id d'opportunité à privilégier, ex. OPP-04")
    parser.add_argument("--nb", type=int, default=3, help="nombre maximal de questions (défaut : 3)")
    args = parser.parse_args(argv)

    opportunite = args.opportunite
    if args.brief:
        with open(args.brief, encoding="utf-8-sig") as fichier:
            brief = json.load(fichier)
        champs = champs_depuis_brief(brief)
        if not opportunite:
            opportunite, mots = deduire_opportunite(brief)
            if opportunite:
                print(f"Opportunité déduite : {opportunite} (mots communs : {', '.join(mots)})")
            else:
                print("Aucune opportunité reconnue")
    else:
        champs = [c for c in args.champs.split(",") if c.strip()]

    questions = proposer_questions(champs, opportunite_id=opportunite, nb=args.nb)
    print(f"Champs manquants : {', '.join(normaliser_champs(champs)) or 'aucun'}")
    for q in questions:
        print(f"\n[{q['id']}] ({q['champ_brief']}) {q['question']}\n    Pourquoi : {q['pourquoi']}")
    print(f"\nquestions_proposees : {ids_pour_grille(questions)}")


if __name__ == "__main__":
    main()
