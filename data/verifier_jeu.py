"""Contrôle d'ensemble du jeu de démo v2 (DATA-US12).

Vérifie data/demo_v2 sans rien modifier : ids uniques, clés étrangères, valeurs d'enum
(lues dans les tableaux de MODELE_DONNEES.md), aucun compteur stocké, aucune adresse e-mail
ni numéro de téléphone, aucun montant en euros dans les opportunités, chaque source réelle
citée avec sa licence.

Affiche OK / KO par contrôle ; code de retour 1 si un contrôle est KO.

Lancer depuis la racine du dépôt : python data/verifier_jeu.py
"""

import json
import re
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent / "demo_v2"
FICHIERS = ["clients", "projects", "opportunities", "signals", "meetings", "meeting_context"]


def charger_jeu(dossier=DEMO):
    return {nom: json.loads((dossier / f"{nom}.json").read_text(encoding="utf-8")) for nom in FICHIERS}


# --- Valeurs d'enum lues dans MODELE_DONNEES.md ---------------------------------------------------

def sections_doc(texte):
    """{titre de section: lignes} ; titre = texte du titre ## ou ### sans les #."""
    sections, titre = {}, ""
    for ligne in texte.splitlines():
        if ligne.startswith("#"):
            titre = ligne.lstrip("#").strip()
            sections[titre] = []
        else:
            sections.setdefault(titre, []).append(ligne)
    return sections


def valeurs_enum(sections, section, champ):
    """Valeurs entre backticks de la colonne « Valeurs possibles » de la ligne `champ` de la section."""
    colonne = None
    for ligne in sections[section]:
        if not ligne.startswith("|"):
            colonne = None
            continue
        cellules = [c.strip() for c in ligne.strip().strip("|").split("|")]
        if "Valeurs possibles" in cellules:
            colonne = cellules.index("Valeurs possibles")
        elif colonne is not None and cellules[0] == f"`{champ}`":
            jetons = re.findall(r"`([^`]+)`", cellules[colonne])
            return {None if j == "null" else j for j in jetons if re.fullmatch(r"[a-z0-9_.:]+", j)}
    raise KeyError(f"{section} / {champ} introuvable dans MODELE_DONNEES.md")


# --- Contrôles : chacun renvoie la liste des problèmes (vide = OK) ---------------------------------

def ids_uniques(jeu):
    problemes = []
    for nom in ["clients", "projects", "opportunities", "signals", "meetings"]:
        ids = [o["id"] for o in jeu[nom]]
        problemes += [f"{nom}.json : id en double {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    ids_q = [q["id"] for e in jeu["meeting_context"] for q in e["questions"]]
    problemes += [f"meeting_context.json : question en double {i}" for i in sorted({i for i in ids_q if ids_q.count(i) > 1})]
    ctx = [e["opportunity_id"] for e in jeu["meeting_context"]]
    problemes += [f"meeting_context.json : opportunité en double {i}" for i in sorted({i for i in ctx if ctx.count(i) > 1})]
    return problemes


def cles_etrangeres(jeu):
    clients = {c["id"] for c in jeu["clients"]}
    opps = {o["id"]: o for o in jeu["opportunities"]}
    p = []
    for pr in jeu["projects"]:
        if pr["client_id"] not in clients:
            p.append(f"projects {pr['id']} → client {pr['client_id']} inconnu")
    for o in jeu["opportunities"]:
        if o["client_id"] not in clients:
            p.append(f"opportunities {o['id']} → client {o['client_id']} inconnu")
    for s in jeu["signals"]:
        if s["opportunity_id"] not in opps:
            p.append(f"signals {s['id']} → opportunité {s['opportunity_id']} inconnue")
        elif s["client_id"] is not None and s["client_id"] != opps[s["opportunity_id"]]["client_id"]:
            p.append(f"signals {s['id']} → client {s['client_id']} différent de celui de {s['opportunity_id']}")
        if s["client_id"] is not None and s["client_id"] not in clients:
            p.append(f"signals {s['id']} → client {s['client_id']} inconnu")
    for m in jeu["meetings"]:
        if m["opportunity_id"] not in opps:
            p.append(f"meetings {m['id']} → opportunité {m['opportunity_id']} inconnue")
        elif m["client_id"] != opps[m["opportunity_id"]]["client_id"]:
            p.append(f"meetings {m['id']} → client {m['client_id']} différent de celui de {m['opportunity_id']}")
        if m["client_id"] not in clients:
            p.append(f"meetings {m['id']} → client {m['client_id']} inconnu")
    for e in jeu["meeting_context"]:
        if e["opportunity_id"] not in opps:
            p.append(f"meeting_context → opportunité {e['opportunity_id']} inconnue")
    sans_signal = set(opps) - {s["opportunity_id"] for s in jeu["signals"]}
    p += [f"opportunities {o} sans signal" for o in sorted(sans_signal)]
    return p


def enums_conformes(jeu, doc):
    s = sections_doc(doc)
    v = lambda sec, champ: valeurs_enum(s, sec, champ)  # noqa: E731
    points = v("Meeting", "collected_points")
    p = []

    def verifier(lieu, valeur, permis):
        if valeur not in permis:
            p.append(f"{lieu} = {valeur!r} hors de {sorted(map(str, permis))}")

    for c in jeu["clients"]:
        verifier(f"clients {c['id']}.relationship_status", c["relationship_status"], v("Client", "relationship_status"))
    for pr in jeu["projects"]:
        verifier(f"projects {pr['id']}.status", pr["status"], v("Project", "status"))
    for o in jeu["opportunities"]:
        for champ in ["status", "priority", "priority_max", "priority_status", "estimated_potential",
                      "feasibility", "complexity"]:
            verifier(f"opportunities {o['id']}.{champ}", o[champ], v("Opportunity", champ))
        for crit in o["missing_criteria"]:
            verifier(f"opportunities {o['id']}.missing_criteria", crit, v("Opportunity", "missing_criteria"))
        j = o["justification"]
        for equipe in j["internal_teams"]:
            verifier(f"opportunities {o['id']}.justification.internal_teams", equipe, v("Opportunity", "internal_teams"))
        for rub, phrases in j.items():
            if isinstance(phrases, list):
                for ph in phrases:
                    if isinstance(ph, dict) and "evidence_type" in ph:
                        verifier(f"opportunities {o['id']}.justification.{rub}.evidence_type", ph["evidence_type"],
                                 v("Opportunity", "evidence_type"))
    for sg in jeu["signals"]:
        for champ in ["source_type", "confidence", "evidence_type"]:
            verifier(f"signals {sg['id']}.{champ}", sg[champ], v("Signal", champ))
        if not isinstance(sg["is_real_source"], bool):
            p.append(f"signals {sg['id']}.is_real_source n'est pas un booléen")
    for m in jeu["meetings"]:
        verifier(f"meetings {m['id']}.status", m["status"], v("Meeting", "status"))
        for pt in m["collected_points"]:
            verifier(f"meetings {m['id']}.collected_points", pt, points)
        for q in m["questions"]:
            verifier(f"meetings {m['id']}.questions.information_sought", q["information_sought"], points)
        for a in m["answers"]:
            verifier(f"meetings {m['id']}.answers.information_sought", a["information_sought"], points)
        r = m["summary"]
        if r is None:
            continue
        verifier(f"meetings {m['id']}.summary.opportunity_decision", r["opportunity_decision"],
                 v("MeetingReport", "opportunity_decision"))
        verifier(f"meetings {m['id']}.summary.generated_by", r["generated_by"], v("MeetingReport", "generated_by"))
        for champ in ["requested", "used"]:
            verifier(f"meetings {m['id']}.summary.engine.{champ}", r["engine"][champ], v("MeetingReport", champ))
        for rub in ["needs", "technical_constraints", "budget_constraints", "timeline", "missing_information",
                    "next_actions", "internal_teams"]:
            for e in r[rub]:
                verifier(f"meetings {m['id']}.summary.{rub}.status", e["status"], v("MeetingReport", "status"))
                verifier(f"meetings {m['id']}.summary.{rub}.point", e.get("point"), points | {None})
                if "team" in e:
                    verifier(f"meetings {m['id']}.summary.{rub}.team", e["team"], v("MeetingReport", "team"))
    for e in jeu["meeting_context"]:
        for pt in e["missing"]:
            verifier(f"meeting_context {e['opportunity_id']}.missing", pt, points)
        for q in e["questions"]:
            verifier(f"meeting_context {q['id']}.information_sought", q["information_sought"], points)
    return p


def cles(objet, chemin=""):
    if isinstance(objet, dict):
        for k, val in objet.items():
            yield f"{chemin}.{k}", k
            yield from cles(val, f"{chemin}.{k}")
    elif isinstance(objet, list):
        for i, val in enumerate(objet):
            yield from cles(val, f"{chemin}[{i}]")


def aucun_compteur(jeu, doc):
    debut = doc.index("## Champs calculés, jamais stockés")
    table = doc[debut:doc.index("\n## ", debut + 1)]
    interdits = set(re.findall(r"^\| `([a-z_]+)` \|", table, flags=re.M))
    motif = re.compile(r"(^|_)(count|nb|nombre|total)(_|$)")
    return [f"{nom}.json{chemin} : compteur stocké" for nom, d in jeu.items()
            for chemin, k in cles(d) if k in interdits or motif.search(k)]


def textes(objet, chemin=""):
    if isinstance(objet, str):
        yield chemin, objet
    elif isinstance(objet, dict):
        for k, val in objet.items():
            yield from textes(val, f"{chemin}.{k}")
    elif isinstance(objet, list):
        for i, val in enumerate(objet):
            yield from textes(val, f"{chemin}[{i}]")


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TELEPHONE = re.compile(r"(?<![\w/.-])(?:\+\d{1,3}[\s.-]?\(?\d\)?[\s.-]?\d{1,4}(?:[\s.-]?\d{2,4}){2,4}"
                       r"|0\d(?:[\s.-]?\d{2}){4})(?![\w/-])")


def aucune_donnee_contact(jeu):
    p = []
    for nom, d in jeu.items():
        for chemin, t in textes(d):
            p += [f"{nom}.json{chemin} : e-mail « {x} »" for x in EMAIL.findall(t)]
            p += [f"{nom}.json{chemin} : téléphone « {x} »" for x in TELEPHONE.findall(t)]
    return p


MONTANT = re.compile(r"\d[\d\s .,]*\s?(?:k|K|M|millions?\s+d'|milliers\s+d')?\s?(?:€|euros?\b|EUR\b)"
                     r"|(?:€|EUR)\s?\d")


def aucun_montant_euros(jeu):
    p = [f"opportunities.json{chemin} : montant « {x.strip()} »"
         for chemin, t in textes(jeu["opportunities"]) for x in MONTANT.findall(t)]
    p += [f"opportunities {o['id']}.estimated_potential est un nombre" for o in jeu["opportunities"]
          if isinstance(o["estimated_potential"], (int, float))]
    return p


# Famille de source réelle : (repère dans source_ref, nom cité dans « Attribution », licence ou régime d'usage)
SOURCES_REELLES = [
    ("signaux_marche.json", "Open Food Facts", "ODbL"),
    ("insee.fr", "INSEE", "Licence Ouverte 2.0"),
    ("food-flavourings", "EU Food Flavourings", "CC BY 4.0"),
    ("Givaudan", "Givaudan 2025", "citation courte avec page"),
]


def sources_reelles_licence(jeu, readme):
    debut = readme.index("## Attribution")
    attribution = " ".join(readme[debut:].split())
    p = []
    for sg in jeu["signals"]:
        if not sg["is_real_source"]:
            continue
        ref = sg["source_ref"] or ""
        if not ref:
            p.append(f"signals {sg['id']} : source réelle sans source_ref")
            continue
        famille = next((f for f in SOURCES_REELLES if f[0] in ref), None)
        if famille is None:
            p.append(f"signals {sg['id']} : source réelle non répertoriée ({ref})")
            continue
        _, nom, licence = famille
        bloc = attribution[max(0, attribution.find(nom) - 60):attribution.find(nom) + len(nom) + 80]
        if nom not in attribution or licence not in bloc:
            p.append(f"signals {sg['id']} : « {nom} » cité sans « {licence} » dans demo_v2/README.md#Attribution")
        if licence == "citation courte avec page" and not re.search(r"\bpp?\.\s?\d", ref):
            p.append(f"signals {sg['id']} : citation courte sans page ({ref})")
    return p


def controles(dossier=DEMO):
    jeu = charger_jeu(dossier)
    doc = (dossier / "MODELE_DONNEES.md").read_text(encoding="utf-8")
    readme = (dossier / "README.md").read_text(encoding="utf-8")
    return [
        ("ids uniques", ids_uniques(jeu)),
        ("clés étrangères valides", cles_etrangeres(jeu)),
        ("valeurs d'enum conformes à MODELE_DONNEES.md", enums_conformes(jeu, doc)),
        ("aucun compteur stocké", aucun_compteur(jeu, doc)),
        ("aucune adresse e-mail ni numéro de téléphone", aucune_donnee_contact(jeu)),
        ("aucun montant en euros dans les opportunités", aucun_montant_euros(jeu)),
        ("chaque source réelle citée avec sa licence", sources_reelles_licence(jeu, readme)),
    ]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    resultats = controles()
    for nom, problemes in resultats:
        print(f"{'OK' if not problemes else 'KO'}  {nom}")
        for pb in problemes:
            print(f"      - {pb}")
    ko = sum(1 for _, pb in resultats if pb)
    print(f"\n{len(resultats) - ko}/{len(resultats)} contrôles OK")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
