"""Justification commerciale d'une opportunité (DATA-US08), générée par règles, sans LLM.

Chaque phrase vient d'un champ des données et porte :
    {"text": …, "evidence_type": "fact" | "hypothesis" | "to_confirm", "sources": [ids ou champs]}
Les sources sont des ids de signal ou de projet (S-01, P-01), ou un champ (clients.json#C-01,
opportunities.json#O-01, grille_qualification.json#feasibility). Aucun montant, aucune affirmation
sur les produits ou technologies de Givaudan : seulement ce que disent les signaux.

Rubriques : client_need, why_now (hors règlements), value_for_givaudan (dont le cadre réglementaire),
internal_teams (codes), facts, hypotheses (toutes les phrases marquées hypothèse), to_confirm, risks.
"""

from datetime import date

LIBELLES_SOURCE = {
    "meeting_report": "compte rendu", "project_history": "historique de projet", "client_request": "demande du client",
    "market_trend": "tendance de marché", "commodity_price": "prix de matière première",
    "company_report": "rapport d'entreprise", "regulation": "règlement",
}
LIBELLES_RELATION = {"strategic": "stratégique", "active": "active", "to_develop": "à développer"}
LIBELLES_STATUT = {"detected": "détectée", "to_qualify": "à qualifier", "confirmed": "confirmée"}
LIBELLES_PRIORITE = {"high": "haute", "medium": "moyenne", "low": "basse"}
LIBELLES_EQUIPES = {"application": "Application", "creation": "Création", "marketing": "Marketing",
                    "regulatory": "Réglementation"}
ORDRE_EQUIPES = ["application", "creation", "marketing", "regulatory"]  # codes du modèle de données
# Équipes selon la catégorie : application pour toute opportunité (l'arôme s'intègre au produit du
# client), création quand un nouvel arôme est à créer.
EQUIPES_PAR_CATEGORIE = {
    "Nouvelle gamme": ["application", "creation"],
    "Extension de gamme": ["application", "creation"],
    "Nouvelle formulation": ["application", "creation"],
    "Nouvelle référence": ["application", "creation"],
    "Amélioration produit": ["application"],
    "Optimisation": ["application"],
}
SOURCES_MARKETING = {"market_trend", "company_report"}
PREFIXES = {"fact": "", "hypothesis": "Hypothèse : ", "to_confirm": "À confirmer : "}


def phrase(texte, evidence_type, sources):
    return {"text": texte, "evidence_type": evidence_type, "sources": list(sources)}


def date_fr(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def ids(sources):
    return ", ".join(sources)


def definition(niveau):
    """Définition de la grille, en minuscule et sans point final, pour l'insérer dans une phrase."""
    d = niveau["definition"].rstrip(".")
    return d[0].lower() + d[1:]


def niveau_grille(critere, valeur):
    return next(n for n in critere["niveaux"] if n["valeur"] == valeur)


def phrase_signal(s, texte):
    """Phrase tirée d'un signal : préfixée si ce n'est pas un fait, pour ne pas mélanger."""
    return phrase(PREFIXES[s["evidence_type"]] + texte, s["evidence_type"], [s["id"]])


def equipes(opp, signaux):
    """(codes, phrase) : équipes selon la catégorie, plus marketing si un signal de marché ou un
    rapport est rattaché, et réglementation si un règlement l'est."""
    codes = dict.fromkeys(EQUIPES_PAR_CATEGORIE[opp["category"]])
    raisons = [f"{' et '.join(LIBELLES_EQUIPES[c] for c in codes)} (catégorie « {opp['category']} »)"]
    sources = [f"opportunities.json#{opp['id']}"]
    marketing = [s["id"] for s in signaux if s["source_type"] in SOURCES_MARKETING]
    if marketing:
        codes["marketing"] = None
        raisons.append(f"Marketing ({ids(marketing)})")
        sources += marketing
    reglement = [s["id"] for s in signaux if s["source_type"] == "regulation"]
    if reglement:
        codes["regulatory"] = None
        raisons.append(f"Réglementation ({ids(reglement)})")
        sources += reglement
    ordonnes = [c for c in ORDRE_EQUIPES if c in codes]
    return ordonnes, phrase(f"Équipes à mobiliser : {', '.join(raisons)}.", "hypothesis", sources)


def justifier(opp, client, signaux, contexte_rdv, criteres, sources_criteres, checklist):
    """Justification de l'opportunité.

    signaux : ceux de l'opportunité ; contexte_rdv : son entrée de meeting_context.json ;
    criteres : {id: critère de la grille} ; sources_criteres : {critère: [ids]} (QUALIFICATIONS) ;
    checklist : {point: libellé}.
    """
    par_date = sorted(signaux, key=lambda s: (s["source_date"], s["id"]), reverse=True)
    clients = [s for s in par_date if s["client_id"] is not None]
    # un règlement n'est pas un « pourquoi maintenant » : il va dans le cadre réglementaire
    reglementaires = [s for s in par_date if s["source_type"] == "regulation"]
    datables = [s for s in par_date if s["source_type"] != "regulation"] or par_date
    marche = [s for s in datables if s["client_id"] is None]

    besoin = [phrase_signal(s, f"{s['description'].rstrip('.')} ({s['id']}, {LIBELLES_SOURCE[s['source_type']]} du "
                               f"{date_fr(s['source_date'])}).") for s in clients]

    recent = datables[0]
    maintenant = [phrase_signal(recent, f"Signal le plus récent : {LIBELLES_SOURCE[recent['source_type']]} du "
                                        f"{date_fr(recent['source_date'])} ({recent['id']}).")]
    maintenant += [phrase_signal(s, f"Signal de marché rattaché ({LIBELLES_SOURCE[s['source_type']]}, "
                                    f"{date_fr(s['source_date'])}, {s['id']}) : {s['description']}") for s in marche]

    potentiel = criteres["estimated_potential"]
    if opp["estimated_potential"] == potentiel["valeur_inconnue"]:
        valeur = [phrase("Valeur commerciale non estimée : aucun signal ni projet ne dit l'ampleur du besoin.",
                         "to_confirm", ["grille_qualification.json#estimated_potential"])]
    else:
        n = niveau_grille(potentiel, opp["estimated_potential"])
        src = sources_criteres["estimated_potential"]
        valeur = [phrase(f"Valeur commerciale estimée : potentiel {n['libelle']} (niveau, jamais un montant), car "
                         f"{definition(n)} ({ids(src)}).", "hypothesis", src)]
    valeur.append(phrase(f"Relation client : {client['name']}, statut "
                         f"{LIBELLES_RELATION[client['relationship_status']]}.", "fact", [f"clients.json#{client['id']}"]))
    for s in reglementaires:
        valeur.append(phrase_signal(s, f"Cadre réglementaire ({date_fr(s['source_date'])}, {s['id']}) : "
                                       f"{s['description']}"))
        valeur.append(phrase(f"Piste : ce cadre réglementaire ({s['id']}) pourrait servir « {opp['title']} » ; le "
                             "lien reste à vérifier.", "hypothesis", [s["id"], f"opportunities.json#{opp['id']}"]))
    codes_equipes, phrase_equipes = equipes(opp, signaux)
    valeur.append(phrase_equipes)

    faits = [phrase(f"{LIBELLES_SOURCE[s['source_type']].capitalize()} du {date_fr(s['source_date'])} ({s['id']}) — "
                    f"{'source réelle' if s['is_real_source'] else 'donnée fictive de démo'}.", "fact", [s["id"]])
             for s in par_date if s["evidence_type"] == "fact"]
    hypotheses = [phrase(f"{s['description'].rstrip('.')} ({s['id']}).", "hypothesis", [s["id"]])
                  for s in par_date if s["evidence_type"] == "hypothesis"]
    a_confirmer = [phrase(f"{s['description'].rstrip('.')} ({s['id']}).", "to_confirm", [s["id"]])
                   for s in par_date if s["evidence_type"] == "to_confirm"]
    if opp["status"] != "confirmed":
        a_confirmer.append(phrase(f"Le besoin n'est pas encore confirmé par le client (statut : "
                                  f"{LIBELLES_STATUT[opp['status']]}).", "to_confirm", [f"opportunities.json#{opp['id']}"]))
    for c in opp["missing_criteria"]:
        point = criteres[c]["point_de_rdv_si_inconnu"]
        a_confirmer.append(phrase(f"{criteres[c]['nom']} à établir : à vérifier au prochain rendez-vous (point "
                                  f"« {checklist[point]} »).", "to_confirm", [f"grille_qualification.json#{c}"]))
    if opp["priority_status"] == "provisional":
        a_confirmer.append(phrase(f"Priorité provisoire : {LIBELLES_PRIORITE[opp['priority']]} aujourd'hui, jusqu'à "
                                  f"{LIBELLES_PRIORITE[opp['priority_max']]} selon ces critères.", "to_confirm",
                                  ["grille_qualification.json"]))

    risques = []
    complexite = criteres["complexity"]
    if opp["complexity"] != complexite["valeur_inconnue"]:
        n = niveau_grille(complexite, opp["complexity"])
        src = sources_criteres["complexity"]
        risques.append(phrase(f"Complexité {n['libelle']} : {definition(n)} ({ids(src)}).", "hypothesis", src))
    else:
        risques.append(phrase(f"{complexite['nom']} non évaluée : le risque technique reste inconnu (voir « à "
                              "confirmer »).", "to_confirm", ["grille_qualification.json#complexity"]))
    faisabilite = criteres["feasibility"]
    if opp["feasibility"] not in (faisabilite["valeur_inconnue"], "high"):
        n = niveau_grille(faisabilite, opp["feasibility"])
        src = sources_criteres["feasibility"]
        risques.append(phrase(f"Faisabilité {n['libelle']} : {definition(n)} ({ids(src)}).", "hypothesis", src))
    for k in contexte_rdv["known"]:
        risques.append(phrase(f"Contrainte connue, {checklist[k['point']].lower()} : {k['information']} "
                              f"({k['signal_id']}).", "fact", [k["signal_id"]]))

    # « Hypothèses » reprend toutes les phrases marquées hypothèse (potentiel déduit, piste, équipes,
    # complexité, faisabilité…), sauf celles qui redisent un signal hypothèse déjà listé.
    deja = {s for p in hypotheses for s in p["sources"]}
    hypotheses += [p for p in besoin + maintenant + valeur + risques
                   if p["evidence_type"] == "hypothesis" and not set(p["sources"]) <= deja]

    return {
        "client_need": besoin,
        "why_now": maintenant,
        "value_for_givaudan": valeur,
        "internal_teams": codes_equipes,
        "facts": faits,
        "hypotheses": hypotheses,
        "to_confirm": a_confirmer,
        "risks": risques,
    }
