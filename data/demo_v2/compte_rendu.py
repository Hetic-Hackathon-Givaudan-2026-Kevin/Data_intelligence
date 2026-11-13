"""Compte rendu de rendez-vous (DATA-US11) : extraction des notes et MeetingReport.

Deux moteurs d'extraction, même sortie :
- rules_v1 : règles et mots-clés, phrase par phrase, sans LLM ;
- llm_v2 : qwen2.5:3b en local via Ollama (OLLAMA_URL, aucune API externe), sortie JSON validée
  contre un schéma, puis garde-fou : un élément introuvable dans les notes passe en to_verify
  (s'il est retrouvé approximativement) ou est écarté. Si Ollama ne répond pas, dépasse le délai
  ou renvoie un JSON invalide : retour automatique à rules_v1, signalé dans `engine`.

Un élément extrait = {"point", "text", "status", "excerpt"} : `excerpt` est toujours un passage
copié des notes (ou d'une réponse) ; `status` vaut confirmed (dit explicitement) ou to_verify
(déduit, hésitant ou contradictoire). Les rubriques déduites (informations manquantes, prochaines
actions, équipes) sont toujours to_verify.

Variables d'environnement : OLLAMA_URL (défaut http://localhost:11434), OLLAMA_MODEL (défaut
qwen2.5:3b), OLLAMA_TIMEOUT en secondes (défaut 120).
"""

import json
import os
import re
import socket
import time
import unicodedata
import urllib.error
import urllib.request

CHECKLIST = {
    "client_objectives": "Objectifs du client",
    "real_need": "Besoin réel",
    "technical_constraints": "Contraintes techniques",
    "budget_constraints": "Contraintes budgétaires",
    "timeline": "Calendrier",
    "decision_criteria": "Critères de décision",
}
POINTS = list(CHECKLIST)
# Rubriques du compte rendu : les besoins regroupent objectifs, besoin réel et critères de décision.
RUBRIQUE = {"client_objectives": "needs", "real_need": "needs", "decision_criteria": "needs",
            "technical_constraints": "technical_constraints", "budget_constraints": "budget_constraints",
            "timeline": "timeline"}
RUBRIQUES_EXTRAITES = ["needs", "technical_constraints", "budget_constraints", "timeline"]
STATUTS = ("confirmed", "to_verify")

LIBELLES_EQUIPES = {"application": "Application", "creation": "Création", "marketing": "Marketing",
                    "regulatory": "Réglementation"}
CATEGORIES_CREATION = {"Nouvelle gamme", "Extension de gamme", "Nouvelle formulation", "Nouvelle référence"}
SOURCES_MARCHE = {"market_trend", "company_report"}
MOTS_REGLEMENTAIRES = ("reglement", "allegation", "etiquet", "additif", "regulat", "labelling", "claim")

MOIS = (r"janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre|"
        r"january|february|march|april|may|june|july|august|september|october|november|december")
# Mots-clés génériques FR/EN, appliqués au texte en minuscules sans accents (repris du banc V1).
MOTS_CLES = {
    "client_objectives": [r"\bobjecti(f|fs|ve|ves)\b", r"\bgoals?\b", r"\baims?\b", r"\bambition",
                          r"\bveu(t|lent)\b", r"\bsouhait", r"\bcherche(nt)? a\b", r"\bwants? to\b",
                          r"\blooking to\b", r"\bstrateg"],
    "real_need": [r"\bbesoins?\b", r"\bneeds?\b", r"\bneeded\b", r"\bleur faut\b", r"\bil faut\b",
                  r"\brequire", r"\battente"],
    "technical_constraints": [r"\btechni(que|cal)", r"\bstabl", r"\bstabilit", r"\bph ?\d", r"\bcuisson\b",
                              r"\bbaking\b", r"\ballergen", r"\bifra\b", r"\bformul", r"\bcahier des charges\b",
                              r"\bspecifications?\b", r"\breglementa", r"\bregulator", r"\bclean.label\b"],
    "budget_constraints": [r"\bbudget", r"\benveloppe\b", r"\d\s?k?€", r"\bk?eur\b", r"\bprix cible\b",
                           r"\btarget price\b", r"\bcout max", r"\bset aside\b", r"\bplafon"],
    "timeline": [r"\blancement\b", r"\blaunch", r"\bmise sur le marche\b", r"\bgo.to.market\b",
                 r"\becheance", r"\bdeadline", r"\bcalendrier\b", r"\btimeline\b", r"\bplanning\b",
                 rf"\b({MOIS})\s+20\d\d\b", r"\bq[1-4]\s?20\d\d\b", r"\btrimestre\b", r"\bsortie en\b"],
    "decision_criteria": [r"\bcriter", r"\bdecid", r"\bdecision", r"\btranch", r"\bchoisi",
                          r"\bselection", r"\bchoose\b", r"\bevaluat"],
}
# Hésitation ou absence : l'élément est noté, mais pas confirmé.
HESITATION = [r"\bpeut.etre\b", r"\bprobablement\b", r"\benvisag", r"\bpourrai", r"\ba confirmer\b",
              r"\bpas encore\b", r"\bnon fixe", r"\bpas fixe", r"\bmaybe\b", r"\bmight\b", r"\bpossibly\b",
              r"\bto be confirmed\b", r"\btbc\b", r"\bnot yet\b", r"\?"]
DATE_MOIS = re.compile(rf"\b({MOIS})\s+(20\d\d)\b")
DATE_TRIMESTRE = re.compile(r"\bq([1-4])\s?(20\d\d)\b")
DATE_NUM = re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\b")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "120"))

SCHEMA_LLM = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {"point": {"type": "string", "enum": POINTS},
                       "text": {"type": "string"},
                       "status": {"type": "string", "enum": list(STATUTS)},
                       "excerpt": {"type": "string"}},
        "required": ["point", "text", "status", "excerpt"]}}},
    "required": ["items"],
}
PROMPT_LLM = """Tu extrais les informations d'un compte rendu de rendez-vous commercial (français ou anglais).
Points possibles :
- client_objectives : ce que le client veut faire (projet, lancement d'un produit, ambition).
- real_need : ce dont il a besoin de notre part (arôme, parfum, ingrédient).
- technical_constraints : contrainte technique, réglementaire ou de formulation.
- budget_constraints : budget, prix, enveloppe.
- timeline : date, échéance, lancement daté.
- decision_criteria : critères sur lesquels le client choisira.
Règles : une entrée par phrase utile ; "excerpt" est la phrase copiée mot pour mot depuis les notes ;
"status" vaut "confirmed" si c'est dit explicitement, "to_verify" si c'est incertain, hypothétique ou
contradictoire (par exemple deux dates différentes). N'invente rien et n'ajoute aucune entrée pour un point
absent des notes. Si les notes ne parlent d'aucun de ces points (par exemple une livraison), renvoie une
liste vide."""


# --- Texte ---------------------------------------------------------------------------------------

def normaliser(texte):
    t = unicodedata.normalize("NFKD", (texte or "").lower().replace("’", "'"))
    return re.sub(r"\s+", " ", "".join(c for c in t if not unicodedata.combining(c))).strip()


def phrases(texte):
    """Phrases des notes (fin de phrase suivie d'un espace, ou retour à la ligne)."""
    return [p.strip() for p in re.split(r"(?<=[.!?;])\s+|\n+", texte or "") if p.strip()]


def trouve(motifs, texte_normalise):
    return any(re.search(m, texte_normalise) for m in motifs)


def dates_calendrier(texte):
    t = normaliser(texte)
    dates = {f"{m} {a}" for m, a in DATE_MOIS.findall(t)}
    dates |= {f"q{q} {a}" for q, a in DATE_TRIMESTRE.findall(t)}
    dates |= {f"{j}/{m}/{a}" for j, m, a in DATE_NUM.findall(t)}
    return sorted(dates)


def present_dans(extrait, sources):
    return bool(extrait and extrait.strip()) and normaliser(extrait) in normaliser(" ".join(sources))


def mots(texte):
    return {m for m in re.findall(r"\w+", normaliser(texte)) if len(m) >= 3}


# --- Extraction ----------------------------------------------------------------------------------

def element(point, extrait, statut):
    libelle = CHECKLIST[point]
    texte = extrait if normaliser(extrait).startswith(normaliser(libelle)) else f"{libelle} : {extrait}"
    return {"point": point, "text": texte, "status": statut, "excerpt": extrait}


def calendrier_contradictoire(elements):
    """Deux dates différentes ou plus dans le calendrier : chaque élément du calendrier est à vérifier."""
    if len(dates_calendrier(" ".join(e["excerpt"] for e in elements if e["point"] == "timeline"))) >= 2:
        for e in elements:
            if e["point"] == "timeline":
                e["status"] = "to_verify"
    return elements


def extraire_rules_v1(notes):
    """Une phrase des notes devient un élément pour chaque point dont elle contient un mot-clé."""
    elements = []
    for p in phrases(notes):
        t = normaliser(p)
        statut = "to_verify" if trouve(HESITATION, t) else "confirmed"
        elements += [element(point, p, statut) for point in POINTS if trouve(MOTS_CLES[point], t)]
    return calendrier_contradictoire(elements)


def appeler_ollama(notes, url=None, model=None, timeout=None):
    """Appelle Ollama en local (/api/chat, JSON contraint par SCHEMA_LLM) ; renvoie le texte produit."""
    corps = {"model": model or OLLAMA_MODEL, "stream": False, "format": SCHEMA_LLM,
             "options": {"temperature": 0, "seed": 42},
             "messages": [{"role": "system", "content": PROMPT_LLM}, {"role": "user", "content": notes}]}
    requete = urllib.request.Request(f"{(url or OLLAMA_URL).rstrip('/')}/api/chat", json.dumps(corps).encode("utf-8"),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(requete, timeout=timeout or OLLAMA_TIMEOUT) as reponse:
        return json.loads(reponse.read().decode("utf-8"))["message"]["content"]


def valider_sortie_llm(texte):
    """Valide la sortie contre SCHEMA_LLM ; ValueError si elle n'est pas conforme."""
    donnees = json.loads(texte)
    if not isinstance(donnees, dict) or not isinstance(donnees.get("items"), list):
        raise ValueError("objet {items: [...]} attendu")
    for e in donnees["items"]:
        if not isinstance(e, dict) or set(SCHEMA_LLM["properties"]["items"]["items"]["required"]) - set(e):
            raise ValueError(f"élément incomplet : {e!r}")
        if e["point"] not in POINTS or e["status"] not in STATUTS:
            raise ValueError(f"point ou statut inconnu : {e!r}")
        if not isinstance(e["text"], str) or not isinstance(e["excerpt"], str):
            raise ValueError(f"texte attendu : {e!r}")
    return donnees["items"]


def garde_fou(elements_llm, notes):
    """Un élément dont l'extrait (ou le texte) est dans les notes est gardé, avec l'extrait exact ;
    retrouvé seulement en partie (au moins 60 % de ses mots dans une phrase des notes) : to_verify,
    avec cette phrase pour extrait ; sinon écarté. Renvoie (éléments, compte)."""
    gardes, compte = [], {"kept": 0, "downgraded": 0, "dropped": 0}
    liste_phrases = phrases(notes)
    for e in elements_llm:
        extrait = next((x.strip() for x in (e["excerpt"], e["text"]) if present_dans(x, [notes])), None)
        if extrait:
            gardes.append(element(e["point"], extrait, e["status"]))
            compte["kept"] += 1
            continue
        cherches = mots(e["excerpt"]) or mots(e["text"])
        meilleure = max(liste_phrases, key=lambda p: len(cherches & mots(p)), default=None)
        if cherches and meilleure and len(cherches & mots(meilleure)) / len(cherches) >= 0.6:
            gardes.append(element(e["point"], meilleure, "to_verify"))
            compte["downgraded"] += 1
        else:
            compte["dropped"] += 1
    # doublons (même point, même extrait) : un seul, le plus prudent
    uniques = {}
    for e in gardes:
        cle = (e["point"], e["excerpt"])
        if cle not in uniques or e["status"] == "to_verify":
            uniques[cle] = e
    return list(uniques.values()), compte


def extraire(notes, mode="rules_v1", appel=None, url=None, model=None, timeout=None):
    """Renvoie (éléments, engine). engine = {requested, used, model, fallback_reason, guard}."""
    engine = {"requested": mode, "used": "rules_v1", "model": None, "fallback_reason": None, "guard": None}
    if mode == "llm_v2":
        if not (notes or "").strip():
            engine["fallback_reason"] = "notes vides : rien à envoyer au modèle"
        else:
            try:
                brut = (appel or appeler_ollama)(notes, url=url, model=model, timeout=timeout)
                elements, compte = garde_fou(valider_sortie_llm(brut), notes)
                engine.update(used="llm_v2", model=model or OLLAMA_MODEL, guard=compte)
                return elements, engine
            except (socket.timeout, TimeoutError) as erreur:
                engine["fallback_reason"] = f"délai dépassé ({erreur.__class__.__name__})"
            except urllib.error.URLError as erreur:
                motif = getattr(erreur, "reason", erreur)
                engine["fallback_reason"] = ("délai dépassé" if isinstance(motif, (socket.timeout, TimeoutError))
                                             else f"Ollama injoignable ({motif})")
            except (ValueError, KeyError, TypeError) as erreur:  # json.JSONDecodeError est un ValueError
                engine["fallback_reason"] = f"JSON invalide ({erreur})"
            except OSError as erreur:
                engine["fallback_reason"] = f"Ollama injoignable ({erreur})"
    return extraire_rules_v1(notes), engine


# --- Compte rendu --------------------------------------------------------------------------------

def item(texte, statut="to_verify", extrait=None, point=None, **autres):
    return {"point": point, "text": texte, "status": statut, "excerpt": extrait, **autres}


def equipes(opp, elements, signaux, sources_texte):
    """Équipes à mobiliser, déduites (to_verify) : application si une contrainte technique est notée ;
    création si la catégorie demande un nouvel arôme et qu'un objectif ou un besoin est noté ;
    marketing si un objectif est noté et qu'un signal de marché est rattaché ; réglementation si un
    mot réglementaire figure dans les notes ou qu'un règlement est rattaché."""
    par_point = {p: [e for e in elements if e["point"] == p] for p in POINTS}
    types = {s["source_type"]: s["id"] for s in signaux}
    resultat = []
    if par_point["technical_constraints"]:
        e = par_point["technical_constraints"][0]
        resultat.append(item("Application : une contrainte technique est notée.", extrait=e["excerpt"], team="application"))
    besoin = par_point["client_objectives"] + par_point["real_need"]
    if opp["category"] in CATEGORIES_CREATION and besoin:
        resultat.append(item(f"Création : un nouvel arôme est à créer (catégorie « {opp['category']} ») et le besoin "
                             "est noté.", extrait=besoin[0]["excerpt"], team="creation"))
    marche = [i for t, i in types.items() if t in SOURCES_MARCHE]
    if par_point["client_objectives"] and marche:
        resultat.append(item(f"Marketing : objectif noté et signal de marché rattaché ({', '.join(marche)}).",
                             extrait=par_point["client_objectives"][0]["excerpt"], team="marketing"))
    phrase_reg = next((p for s in sources_texte for p in phrases(s)
                       if any(m in normaliser(p) for m in MOTS_REGLEMENTAIRES)), None)
    if phrase_reg:
        resultat.append(item("Réglementation : un point réglementaire est noté.", extrait=phrase_reg, team="regulatory"))
    elif "regulation" in types:
        resultat.append(item(f"Réglementation : un règlement est rattaché à l'opportunité ({types['regulation']}).",
                             team="regulatory"))
    return resultat


def construire_rapport(elements, opp, client, contexte, signaux, engine, sources_texte):
    """MeetingReport (Meeting.summary) à partir des éléments extraits."""
    rubriques = {r: [e for e in elements if RUBRIQUE[e["point"]] == r] for r in RUBRIQUES_EXTRAITES}
    couverts = {e["point"] for e in elements}
    connus = {k["point"]: k["information"] for k in contexte["known"]}
    manquants = [item(f"{CHECKLIST[p]}" + (f" (connu avant le rendez-vous : {connus[p]} À reconfirmer.)"
                                            if p in connus else ""), point=p)
                 for p in POINTS if p not in couverts]
    les_equipes = equipes(opp, elements, signaux, sources_texte)

    actions = [item(f"Vérifier auprès du client : {e['excerpt']}", extrait=e["excerpt"], point=e["point"])
               for e in elements if e["status"] == "to_verify"]
    actions += [item(f"Obtenir l'information manquante : {CHECKLIST[m['point']].lower()}.", point=m["point"])
                for m in manquants]
    if rubriques["budget_constraints"]:
        actions.append(item("Intégrer la contrainte budgétaire à la proposition commerciale.",
                            extrait=rubriques["budget_constraints"][0]["excerpt"], point="budget_constraints"))
    actions += [item(f"Transmettre les éléments recueillis à l'équipe {LIBELLES_EQUIPES[e['team']]}.",
                     extrait=e["excerpt"]) for e in les_equipes]

    confirmes = {e["point"] for e in elements if e["status"] == "confirmed"}
    if {"client_objectives", "real_need"} <= confirmes:
        decision, raison = "confirmed", ("Objectifs du client et besoin réel confirmés dans les notes : statut proposé "
                                         "« confirmed », à valider par le commercial.")
    elif not elements:
        decision, raison = "to_qualify", "Aucune information de la checklist n'a été recueillie."
    else:
        reste = [CHECKLIST[p].lower() for p in ("client_objectives", "real_need") if p not in confirmes]
        decision, raison = "to_qualify", (f"Pas encore confirmé dans les notes : {', '.join(reste)}. À écarter seulement "
                                          "si le client confirme ne pas avoir ce besoin.")

    n_conf = sum(e["status"] == "confirmed" for e in elements)
    resume = (f"Rendez-vous avec {client['name']} au sujet de « {opp['title']} ». "
              f"{n_conf} élément(s) confirmé(s) et {len(elements) - n_conf} à vérifier dans les notes ; "
              f"{len(manquants)} point(s) de la checklist encore manquant(s)."
              + ("" if any(s.strip() for s in sources_texte) else " Aucune note saisie."))
    return {
        "summary": resume,
        "needs": rubriques["needs"],
        "technical_constraints": rubriques["technical_constraints"],
        "budget_constraints": rubriques["budget_constraints"],
        "timeline": rubriques["timeline"],
        "missing_information": manquants,
        "next_actions": actions,
        "internal_teams": les_equipes,
        "opportunity_decision": decision,
        "decision_reason": raison,
        "generated_by": engine["used"],
        "engine": engine,
        "validated": False,
    }


def construire_meeting(identifiant, opp, client, contexte, signaux, jour, notes="", reponses=None, coches=(),
                       mode="rules_v1", **options_llm):
    """Meeting complet (MODELE_DONNEES.md). reponses : {point: réponse} ; coches : points cochés.

    Les réponses sont des éléments confirmés (le commercial les a saisies pour ce point) ; un point
    coché sans rien dans les notes ni les réponses devient un élément to_verify sans extrait."""
    reponses = {p: r.strip() for p, r in (reponses or {}).items() if r and r.strip()}
    notes = (notes or "").strip()
    elements, engine = extraire(notes, mode, **options_llm)
    elements += [element(p, r, "confirmed") for p, r in reponses.items()]
    couverts = {e["point"] for e in elements}
    elements += [item("Point coché pendant le rendez-vous, sans détail dans les notes.", point=p)
                 for p in POINTS if p in coches and p not in couverts]
    elements.sort(key=lambda e: POINTS.index(e["point"]))
    sources_texte = [notes, *reponses.values()]
    rapport = construire_rapport(elements, opp, client, contexte, signaux, engine, sources_texte)
    return {
        "id": identifiant,
        "client_id": client["id"],
        "opportunity_id": opp["id"],
        "date": jour,
        "status": "completed",
        "objective": contexte["objective"],
        "questions": [{k: q[k] for k in ("question", "why", "information_sought")} for q in contexte["questions"]],
        "answers": [{"information_sought": p, "answer": reponses[p]} for p in POINTS if p in reponses],
        "collected_points": [p for p in POINTS if any(e["point"] == p for e in elements)],
        "notes": notes,
        "summary": rapport,
        "next_actions": [a["text"] for a in rapport["next_actions"]],
    }
