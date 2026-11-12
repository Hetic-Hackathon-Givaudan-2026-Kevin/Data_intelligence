# Construit les 6 fiches clients (modèle standard) à partir des JSON de Tech + questions.json
import json
L=lambda f: json.load(open(f"../ia/donnees/{f}",encoding="utf-8"))
C,P,O,S,M,I=[L(f) for f in ["clients.json","projects.json","opportunities.json","signals.json","meetings.json","clients-insights.json"]]
Q=json.load(open("questions.json",encoding="utf-8"))
IDS=["1","2","3","4","5","6"]
fiches=[]
for cid in IDS:
    c=next(x for x in C if x["id"]==cid); ins=next(x for x in I if x["client_id"]==cid)
    opps=[o for o in O if o["client_id"]==cid]; oids={o["id"] for o in opps}
    projs=[p for p in P if p["client_id"]==cid]
    pids={p["id"] for p in projs}
    qs=[{"question":q,"pourquoi":w,"information_recherchee":i,"lien":l} for q,w,i,l in Q[cid]]
    for q in qs: assert q["lien"] in oids|pids, (cid,q["lien"])
    a_conf=[]
    for o in opps:
        if o["feasibility"]=="a_confirmer": a_conf.append(f"Faisabilité de « {o['title']} »")
        if not o.get("estimated_potential"): a_conf.append(f"Potentiel de « {o['title']} » (non renseigné)")
        for s in S:
            if s["opportunity_id"]==o["id"] and s["evidence_type"]!="fait": a_conf.append(f"Hypothèse à vérifier : {s['description']}")
    a_conf+=ins["summary"]["attention_points"]
    fiches.append({
      "identite":{k:c[k] for k in ["id","name","sector","country","account_manager","relationship_status","last_updated"]},
      "indicateurs":{"projets_actifs":sum(p["status"]=="actif" for p in projs),"opportunites_detectees":len(opps),"opportunites_a_qualifier":sum(o["status"]=="a_qualifier" for o in opps)},
      "synthese":ins["summary"],
      "historique":ins["history"],
      "projets":projs,
      "opportunites":[{**o,"signaux":[s for s in S if s["opportunity_id"]==o["id"]]} for o in opps],
      "questions_preparatoires":qs,
      "a_confirmer":list(dict.fromkeys(a_conf)),
      "meta":{"donnees":"fictives","questions":"générées par IA (Claude) avec prompt_fiche_client.md, à relire par l'équipe Data","source":"jeu de données Tech (clients.json, projects.json, opportunities.json, signals.json, clients-insights.json)"}})
    # contrôle de cohérence avec les compteurs déclarés par Tech
    assert fiches[-1]["indicateurs"]["opportunites_detectees"]==c["opportunitiesDetected"] and fiches[-1]["indicateurs"]["opportunites_a_qualifier"]==c["opportunitiesToQualify"] and fiches[-1]["indicateurs"]["projets_actifs"]==c["projectsCount"], cid
    assert len(qs)==3
json.dump(fiches,open("fiches_clients.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
modele={
 "identite":{"id":"string","name":"string (nom fictif)","sector":"string","country":"string","account_manager":"string (nom fictif)","relationship_status":"string","last_updated":"JJ/MM/AAAA"},
 "indicateurs":{"projets_actifs":"int","opportunites_detectees":"int","opportunites_a_qualifier":"int"},
 "synthese":{"situation":"string","important_projects":["string"],"expressed_needs":["string"],"recent_signals":["string"],"attention_points":["string"]},
 "historique":[{"date":"AAAA-MM-JJ","event":"string"}],
 "projets":[{"id":"string","client_id":"string","name":"string","description":"string","status":"actif | termine","start_date":"AAAA-MM-JJ"}],
 "opportunites":[{"id":"string","title":"string","category":"string","status":"detectee | a_qualifier | confirmee","priority":"haute | moyenne | basse","estimated_potential":"elevee | moyenne | faible | null (non renseigné)","feasibility":"a_confirmer | moyenne | elevee","complexity":"faible | moyenne | elevee","next_action":"string",
   "signaux":[{"description":"string","source_type":"compte_rendu | demande_client | historique | projet | veille_marche","source_date":"AAAA-MM-JJ","confidence":"faible | moyenne | haute","evidence_type":"fait | hypothese"}]}],
 "questions_preparatoires":[{"question":"string","pourquoi":"string","information_recherchee":"Objectifs du client | Besoin réel | Contraintes techniques | Contraintes budgétaires | Calendrier | Critères de décision","lien":"id d'une opportunité ou d'un projet"}],
 "a_confirmer":["string"],
 "meta":{"donnees":"fictives","questions":"string","source":"string"}}
json.dump(modele,open("modele_fiche_client.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("OK", [f["identite"]["name"] for f in fiches])
