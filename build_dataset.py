#!/usr/bin/env python3
"""Build normalized relational CSVs + combined JSON + i18n from raw/*.json.
Adds: city + coordinates per university, controlled field_category, numeric
tuition ranges, expanded city cost-of-living, bilingual (IT/EN) labels.
Only reshapes/joins sourced data; never invents figures."""
import json, csv, re, unicodedata, os
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw"); DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)
def load(n):
    with open(os.path.join(RAW, n), encoding="utf-8") as f: return json.load(f)

CC = {"Albania":"AL","Andorra":"AD","Austria":"AT","Belarus":"BY","Belgium":"BE","Bosnia and Herzegovina":"BA","Bulgaria":"BG",
 "Croatia":"HR","Cyprus":"CY","Czech Republic":"CZ","Denmark":"DK","Estonia":"EE","Finland":"FI","France":"FR","Germany":"DE",
 "Greece":"GR","Hungary":"HU","Iceland":"IS","Ireland":"IE","Italy":"IT","Kosovo":"XK","Latvia":"LV","Liechtenstein":"LI",
 "Lithuania":"LT","Luxembourg":"LU","Malta":"MT","Moldova":"MD","Monaco":"MC","Montenegro":"ME","Netherlands":"NL","North Macedonia":"MK",
 "Norway":"NO","Poland":"PL","Portugal":"PT","Romania":"RO","Russian Federation":"RU","San Marino":"SM","Serbia":"RS","Slovakia":"SK",
 "Slovenia":"SI","Spain":"ES","Sweden":"SE","Switzerland":"CH","Ukraine":"UA","United Kingdom":"GB"}
CC2NAME = {v:k for k,v in CC.items()}

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)

# ---------- base universities + city + field_category ----------
world = json.load(open(os.path.join(ROOT,"world_universities.json"), encoding="utf-8"))
uni_city = load("uni_city.json")
TAX = load("field_taxonomy.json")["categories"]
TAXLAB = {c["code"]:(c["label_en"],c["label_it"]) for c in TAX}
def classify(name):
    n = norm(name)
    for c in TAX:
        for kw in c["keywords"]:
            if kw in n:
                return c["code"]
    return "COMP"

unis = []; i = 0
for u in world:
    if u["country"] not in CC: continue
    i += 1
    cinfo = uni_city.get(str(i), {"city":"","lat":"","lon":""})
    code = classify(u["name"])
    unis.append({
        "id": i, "name": u["name"], "country": u["country"], "country_code": CC[u["country"]],
        "city": cinfo["city"], "lat": cinfo["lat"], "lon": cinfo["lon"],
        "field_category": code, "field_category_en": TAXLAB[code][0], "field_category_it": TAXLAB[code][1],
        "domain": (u["domains"][0] if u.get("domains") else ""),
        "website": (u["web_pages"][0] if u.get("web_pages") else ""),
    })

# ---------- rankings (fuzzy join) ----------
STOP = {"university","universite","universitat","universita","universitaet","universidad","universidade","the","of","de","di","du",
 "del","della","der","den","das","la","le","el","and","et","for","studies","college","institute","institut","school","hochschule",
 "politecnico","politechnika","technical","technische","polytechnic","national","state","public","higher","education","sciences","science","applied"}
def toks(s): return {t for t in norm(s).split() if t and t not in STOP and len(t) > 1}
idx = {}
for u in unis: idx.setdefault(u["country_code"], []).append((toks(u["name"]), u))
def best_match(name, country):
    cc = CC.get(country)
    if not cc or cc not in idx: return None
    nt = toks(name)
    if not nt: return None
    best, bs = None, 0.0
    for ut, u in idx[cc]:
        if not ut: continue
        inter = len(nt & ut)
        if inter:
            sc = inter/len(nt|ut)
            if sc > bs: best, bs = u, sc
    return best if bs >= 0.6 else None
rk = load("rankings_the.json")
rankings_rows = []; uni_rank = {}; matched = 0
for r in rk["universities"]:
    m = best_match(r["name"], r["country"])
    if m: matched += 1; uni_rank[m["id"]] = r
    rankings_rows.append({"the_name":r["name"],"country":r["country"],"matched_university_id":(m["id"] if m else ""),
        "world_rank":r.get("world_rank",""),"overall_score":r.get("overall_score",""),"teaching":r.get("teaching",""),
        "research":r.get("research",""),"citations_or_research_quality":r.get("citations_or_research_quality",""),
        "international_outlook":r.get("international_outlook",""),"industry_income":r.get("industry_income","")})
for u in unis:
    r = uni_rank.get(u["id"])
    u["the_world_rank"] = r.get("world_rank","") if r else ""
    u["the_overall_score"] = r.get("overall_score","") if r else ""
    u["the_teaching"] = r.get("teaching","") if r else ""
    u["the_research"] = r.get("research","") if r else ""
    u["the_citations"] = r.get("citations_or_research_quality","") if r else ""
    u["the_international_outlook"] = r.get("international_outlook","") if r else ""
    u["the_industry_income"] = r.get("industry_income","") if r else ""

# ---------- ETER: real fields offered per institution ----------
ETER_CC = {"UK":"GB","EL":"GR"}
BUCKET = {"Medicine&Health":"MED","Engineering&Technology":"ENG","ComputerScience&IT":"ICT","NaturalSciences&Math":"SCI",
 "Business&Economics":"BUS","SocialSciences":"SOC","Humanities&Languages":"HUM","Education":"EDU","Agriculture&Veterinary":"AGR",
 "Arts&Design":"ART","Law":"LAW","Architecture":"ARC"}
idx2 = {}
for u in unis:
    idx2.setdefault(u["country_code"], []).append((toks(u["name"]), norm(u["city"]) if u["city"] else "", u))
eter_codes_by_uid = {}; eter_matched = 0
for e in load("eter_fields.json"):
    cc = ETER_CC.get(e["country_code"], e["country_code"])
    if cc not in idx2: continue
    nt = toks(e["institution_name"]);
    if not nt: continue
    ecity = norm(e.get("city","") or "")
    best, bs = None, 0.0
    for ut, ucity, u in idx2[cc]:
        if not ut: continue
        inter = len(nt & ut)
        if not inter: continue
        sc = inter/len(nt|ut)
        if ecity and ucity and ecity == ucity: sc += 0.15
        if sc > bs: best, bs = u, sc
    if best and bs >= 0.55:
        eter_matched += 1
        codes = {BUCKET[b] for b in (e.get("fields",[]) + e.get("ambiguous_buckets",[])) if b in BUCKET}
        eter_codes_by_uid.setdefault(best["id"], set()).update(codes)
for u in unis:
    codes = eter_codes_by_uid.get(u["id"])
    if codes:
        u["fields_offered"] = "|".join(sorted(codes)); u["fields_source"] = "ETER"
    else:
        u["fields_offered"] = u["field_category"]; u["fields_source"] = "name-heuristic"

# ---------- ROOM RENT (comparable metric on EVERY university) ----------
rr_country = {r["country_code"]: r for r in load("room_rent_country.json")}
rr_city = {(r["city"], r["country_code"]): r for r in load("room_rent_city.json")}
# augment city room rent with values DERIVED from the Numbeo 1-bedroom data we already have (room ~= 0.6 x 1-bed)
for fn in ["cost_of_living.json","cost_of_living_extra_1.json","cost_of_living_extra_2.json"]:
    p = os.path.join(RAW, fn)
    if not os.path.exists(p): continue
    for c in json.load(open(p, encoding="utf-8")):
        cc = c.get("country_code") or CC.get(c.get("country",""), "")
        city = c.get("city"); rent1 = c.get("monthly_rent_eur")
        if city and cc and isinstance(rent1,(int,float)) and (city,cc) not in rr_city:
            rr_city[(city,cc)] = {"city":city,"country_code":cc,"room_rent_eur_month":round(rent1*0.6),
                "source_url":c.get("source_numbeo_url",""),"note":"derived from Numbeo 1-bedroom rent x0.6 (single-room share estimate)"}
# augment from external city-rent datasets if present (bulk dataset + market portals): city-level for many more cities
for _bf in ["city_rent_bulk.json","room_rent_city_portals.json"]:
    _bp = os.path.join(RAW, _bf)
    if not os.path.exists(_bp): continue
    for c in json.load(open(_bp, encoding="utf-8")):
        cc = c.get("country_code",""); city = c.get("city","")
        rr = c.get("room_rent_eur_month")
        if city and cc and isinstance(rr,(int,float)) and (city,cc) not in rr_city:
            rr_city[(city,cc)] = {"city":city,"country_code":cc,"room_rent_eur_month":round(rr),
                "source_url":c.get("source_url",""),"note":c.get("note","market portal")}
rr_city_rows = sorted(({"city":r["city"],"country_code":r["country_code"],"country":CC2NAME.get(r["country_code"],""),
    "monthly_room_rent_eur":r["room_rent_eur_month"],"source_url":r.get("source_url",""),"note":r.get("note","")}
    for r in rr_city.values()), key=lambda x:(x["country_code"],x["city"]))
rr_country_rows = sorted(({"country":r["country"],"country_code":r["country_code"],"monthly_room_rent_eur":r["room_rent_eur_month"],
    "basis":r.get("basis",""),"source_url":r.get("source_url",""),"note":r.get("note","")}
    for r in rr_country.values()), key=lambda x:x["country"])
for u in unis:
    key = (u["city"], u["country_code"])
    if u["city"] and key in rr_city:
        rc = rr_city[key]
        u["monthly_room_rent_eur"] = rc["room_rent_eur_month"]; u["room_rent_level"] = "city"; u["room_rent_source"] = rc.get("source_url","")
    elif u["country_code"] in rr_country:
        rc = rr_country[u["country_code"]]
        u["monthly_room_rent_eur"] = rc["room_rent_eur_month"]; u["room_rent_level"] = "country:"+rc.get("basis","") ; u["room_rent_source"] = rc.get("source_url","")
    else:
        u["monthly_room_rent_eur"] = ""; u["room_rent_level"] = ""; u["room_rent_source"] = ""

# ---------- tuition (numeric, bilingual) ----------
tu = load("tuition_enriched.json")["countries"]
def n(v): return "" if v is None else v
tuition_rows = []
budget_by_country = {}
for r in tu:
    tuition_rows.append({"country":r["country"],"country_code":r["cc"],"currency":r["currency"],"fee_type":r["fee_type"],
        "data_quality":r["data_quality"],
        "bachelor_eu_min_eur":n(r["bach_eu_min"]),"bachelor_eu_max_eur":n(r["bach_eu_max"]),
        "master_eu_min_eur":n(r["mast_eu_min"]),"master_eu_max_eur":n(r["mast_eu_max"]),
        "bachelor_noneu_min_eur":n(r["bach_noneu_min"]),"bachelor_noneu_max_eur":n(r["bach_noneu_max"]),
        "master_noneu_min_eur":n(r["mast_noneu_min"]),"master_noneu_max_eur":n(r["mast_noneu_max"]),
        "official_student_budget_eur_month":n(r["budget"]),"notes_it":r["notes_it"],"notes_en":r["notes_en"]})
    if r.get("budget") is not None: budget_by_country[r["country"]] = (r["budget"], "")

# ---------- tuition exceptions (mapped to universities by id) ----------
# explicit map: exception label -> Hipolabs university id (names differ from the curated labels)
EXC_ID = {"Heidelberg University":839,"TU Munich":816,"Sciences Po (Paris)":499,"Sorbonne Universite (Paris)":487,
 "Politecnico di Milano":999,"Universita di Bologna":1012,"Sapienza Universita di Roma":1048,"University of Amsterdam":1172,
 "TU Delft":1166,"KU Leuven":133,"Universidad Complutense Madrid":1838,"Universitat de Barcelona":1830,"University of Vienna":71,
 "ETH Zurich":1963,"EPFL (Lausanne)":1962,"KTH (Stockholm)":1912,"Lund University":1915,"University of Copenhagen":286,
 "University of Helsinki":310,"Trinity College Dublin":974,"University of Warsaw":1302,"Charles University (Prague)":237,
 "University of Lisbon":1378,"University of Coimbra":1374}
id2name = {u["id"]:u["name"] for u in unis}
eu15 = load("tuition_eu15.json")
exc_rows = []
for r in eu15:
    for e in r.get("university_exceptions", []):
        uid = EXC_ID.get(e["university"], "")
        exc_rows.append({"country":r["country"],"matched_university_id":uid,"university":e["university"],
            "matched_university_name":(id2name.get(uid,"") if uid else ""),"field":e.get("field",""),"level":e.get("level",""),
            "amount_eur_year":("" if e.get("amount_eur") is None else e["amount_eur"]),"note":e.get("note",""),"source_url":e.get("source_url","")})

# ---------- cost of living: city (merge base 23 + extras) ----------
col_city_rows = []
seen_city = set()
def add_col(city, country, cc, cur, rent, other, total, budget, numbeo, official, note):
    if rent in (None,"") : return  # skip rows with no real rent (fall back to country)
    if (city,cc) in seen_city: return
    seen_city.add((city,cc))
    col_city_rows.append({"city":city,"country":country,"country_code":cc,"currency":cur,
        "monthly_rent_eur":rent,"monthly_other_eur":n(other),"monthly_total_eur":n(total),
        "official_student_budget_eur_month":n(budget),"source_numbeo_url":n(numbeo),"source_official_url":n(official),"access_note":n(note)})
for c in load("cost_of_living.json"):
    add_col(c["city"],c["country"],CC.get(c["country"],""),c["currency"],c["monthly_rent_eur"],c["monthly_other_eur"],
        c["monthly_total_eur"],c.get("official_student_budget_eur"),c.get("source_numbeo_url"),c.get("source_official_url"),c.get("access_note"))
    if c.get("official_student_budget_eur") is not None and c["country"] not in budget_by_country:
        budget_by_country[c["country"]] = (c["official_student_budget_eur"], c.get("source_official_url",""))
for fn in ["cost_of_living_extra_1.json","cost_of_living_extra_2.json"]:
    p = os.path.join(RAW, fn)
    if not os.path.exists(p): continue
    for c in json.load(open(p, encoding="utf-8")):
        cc = c.get("country_code","")
        add_col(c["city"], CC2NAME.get(cc,""), cc, c.get("currency","EUR"), c.get("monthly_rent_eur"), c.get("monthly_other_eur"),
            c.get("monthly_total_eur"), None, c.get("source_numbeo_url"), "", c.get("access_note"))

# ---------- cost of living: country (official + derived national average) ----------
col_country_rows = []
have_country = set()
for country,(b,src) in sorted(budget_by_country.items()):
    col_country_rows.append({"country":country,"country_code":CC.get(country,""),"official_student_budget_eur_month":b,
        "source_url":src,"note":"Official national student-budget estimate or study-visa financial-means benchmark (see source)."})
    have_country.add(country)
# derived national fallback: for countries with city Numbeo data but no official budget,
# use the average monthly_total of their cities (clearly flagged as derived, not official)
from statistics import mean
city_totals = {}
for r in col_city_rows:
    t = r.get("monthly_total_eur")
    if isinstance(t,(int,float)) and r["country"]:
        city_totals.setdefault(r["country"], []).append(t)
for country, vals in sorted(city_totals.items()):
    if country in have_country or not vals: continue
    col_country_rows.append({"country":country,"country_code":CC.get(country,""),
        "official_student_budget_eur_month":round(mean(vals)),
        "source_url":"https://www.numbeo.com/cost-of-living/",
        "note":f"Derived: average of {len(vals)} Numbeo city total(s) in this country (no official national benchmark available); indicative."})
    have_country.add(country)

# ---------- scholarships (bilingual) ----------
SCH_IT = {
 "Erasmus+ Mobility Grant (study abroad)":("Contributo mensile ~200-500 EUR per 3-12 mesi all'estero + esenzione tasse nell'ateneo ospitante.","Studenti iscritti a un ateneo con Carta Erasmus, per un periodo di studio presso un partner all'estero."),
 "Erasmus Mundus Joint Masters (EMJM) Scholarship":("Borsa completa: 1.400 EUR/mese fino a 24 mesi + viaggio, installazione e assicurazione.","Studenti di tutto il mondo con una prima laurea, ammessi a un master congiunto Erasmus Mundus in almeno tre paesi."),
 "DAAD Scholarships":("Stipendio mensile (es. 992 EUR studenti, 1.300 dottorandi) + viaggio forfettario; non rimborsabile.","Laureati internazionali, dottorandi e postdoc per studio/ricerca in Germania."),
 "France Excellence Eiffel Scholarship":("Stipendio 2.100 EUR/mese (dal 2026) + trasporto, assicurazione, alloggio; esenzione tasse nei diplomi nazionali pubblici.","Studenti internazionali (non francesi) nominati da un ateneo francese per master o dottorato."),
 "Invest Your Talent in Italy":("Esenzione totale tasse + 10.000 EUR di stipendio (trimestrale).","Cittadini di paesi idonei, per master in inglese in ingegneria, architettura/design, economia/management."),
 "DSU regional scholarship (Diritto allo Studio Universitario)":("Su base ISEE: esenzione tasse, alloggio, mensa e contributo annuale; varia per regione/reddito.","Studenti iscritti (italiani e internazionali, anche extra-UE) sotto le soglie regionali di reddito."),
 "Holland Scholarship":("Una tantum 5.000 EUR nel primo anno.","Studenti internazionali extra-SEE iscritti a triennale o magistrale in un ateneo olandese aderente."),
 "Orange Tulip Scholarship (OTS)":("Premi variabili per ateneo: da esenzioni parziali a copertura totale delle tasse, alcuni con indennita.","Cittadini di specifici paesi Neso ammessi a un programma olandese aderente."),
 "VLIR-UOS ICP Connect Scholarships":("Copre tasse, viaggio, assicurazione e spese di vitto e alloggio per l'intero programma.","Candidati da 29 paesi in via di sviluppo ammessi a programmi in inglese delle Fiandre."),
 "ARES Scholarships":("Copre tasse, viaggio internazionale, indennita di sussistenza, iscrizione, visto e assicurazione.","Residenti/professionisti di paesi partner per master avanzati o formazione continua."),
 "MAEC-AECID Scholarships":("A seconda del bando: stipendio mensile (~1.200 EUR), contributo tasse, viaggio e assicurazione.","Laureati internazionali e spagnoli, soprattutto post-laurea; alcuni bandi per paesi in via di sviluppo."),
 "Ernst Mach Grant":("Contributo mensile + assicurazione e supporto viaggio/installazione, secondo la variante.","Dottorandi, post-laurea, postdoc e giovani docenti esteri per soggiorni brevi (non laurea intera)."),
 "Swiss Government Excellence Scholarships":("Borsa per ricerca o studio in atenei svizzeri; benefici variabili per paese/tipo.","Ricercatori a inizio carriera da ~180 paesi con master, con un supervisore ospitante svizzero confermato."),
 "Swedish Institute Scholarships for Global Professionals (SISGP)":("Tasse complete, stipendio SEK 12.000/mese, viaggio SEK 15.000, assicurazione medica, network SI.","Cittadini di paesi idonei con esperienza lavorativa, ammessi a un master idoneo in inglese."),
 "Danish Government Scholarships under the Cultural Agreements":("Copre tasse + contributo mensile ~DKK 6.090 (lordo) per le spese di vita.","Studenti master/PhD molto qualificati in scambio da paesi idonei (Europa, Cina, Giappone, Israele, Egitto, Russia)."),
 "University tuition-fee scholarships / waivers":("Esenzioni tasse 50-100%; alcune con contributo di trasferimento (es. Univ. Helsinki esenzione 100% + 5.000 EUR).","Studenti extra-UE/SEE paganti, ammessi a un programma in inglese; tramite la domanda al programma."),
 "Government of Ireland International Education Scholarships (GOI-IES)":("Stipendio 10.000 EUR per un anno + esenzione totale delle tasse dall'ateneo ospitante.","Studenti extra-UE/SEE per un anno a tempo pieno a livello NFQ 9 o 10 (master/dottorato)."),
 "Stefan Banach NAWA Scholarship Programme":("Stipendio PLN 2.500/mese, esenzione tasse negli atenei pubblici, corso preparatorio, viaggio PLN 2.500.","Cittadini di 36 paesi partner dell'aiuto polacco, per master a tempo pieno in polacco o inglese."),
 "Government Scholarships for Developing Countries":("Borsa per studio in atenei pubblici cechi in ceco o inglese (master e dottorato) nella cooperazione allo sviluppo.","Cittadini di una lista definita di paesi in via di sviluppo per master e dottorati."),
 "Camoes Institute Scholarships":("Borse per corsi di lingua/cultura portoghese e, nella cooperazione bilaterale, per l'alta formazione; pagate dall'Ambasciata.","Studenti stranieri per lingua/cultura, e cittadini dei PALOP e Timor Est nei programmi di cooperazione."),
}
sch = load("scholarships.json"); sch_rows = []
def sch_row(scope, country, s):
    it = SCH_IT.get(s["name"], ("",""))
    return {"scope":scope,"country":country,"name":s["name"],"provider":s["provider"],
        "coverage_en":s["coverage"],"coverage_it":it[0],"eligibility_en":s["eligibility"],"eligibility_it":it[1],"source_url":s["source_url"]}
for s in sch["eu_wide"]: sch_rows.append(sch_row("EU-wide","",s))
for blk in sch["by_country"]:
    for s in blk["scholarships"]: sch_rows.append(sch_row("national",blk["country"],s))

# ---------- faculties (with field_category) ----------
df = load("datasets_and_faculties.json"); fac_rows = []; fid = 0
FAC_MAP = [("medic",["MED"]),("health",["MED"]),("pharm",["MED"]),("dent",["MED"]),
 ("engineer",["ENG"]),("technolog",["ENG"]),("aerospace",["ENG"]),("mechanical",["ENG"]),("electrical",["ENG"]),("civil",["ENG"]),("informat",["ICT"]),("computer",["ICT"]),
 ("architect",["ARC"]),("urban",["ARC"]),("design",["ART"]),("art",["ART"]),("music",["ART"]),("film",["ART"]),
 ("business",["BUS"]),("econom",["BUS"]),("management",["BUS"]),
 ("law",["LAW"]),("juris",["LAW"]),("criminolog",["LAW"]),
 ("agri",["AGR"]),("veterin",["AGR"]),("forest",["AGR"]),
 ("social",["SOC"]),("politic",["SOC"]),("public admin",["SOC"]),("international affairs",["SOC"]),("international relations",["SOC"]),
 ("humanit",["HUM"]),("letter",["HUM"]),("philolog",["HUM"]),("language",["HUM"]),("philosoph",["HUM"]),("arts, humanities",["HUM"]),("cultural",["HUM"]),
 ("educat",["EDU"]),("sport",["EDU"]),("theolog",["THEO"]),
 ("science",["SCI"]),("physic",["SCI"]),("chemistr",["SCI"]),("biolog",["SCI"]),("mathemat",["SCI"]),("natural",["SCI"]),("geoscience",["SCI"])]
def fac_category(fac):
    f = fac.lower()
    for kw, codes in FAC_MAP:
        if kw in f: return codes[0]
    return "COMP"
for u in df["universities"]:
    for fac in u["faculties"]:
        fid += 1; code = fac_category(fac)
        fac_rows.append({"id":fid,"university":u["name"],"city":u["city"],"country":u["country"],"country_code":u["country_code"],
            "faculty":fac,"field_category":code,"field_category_en":TAXLAB[code][0],"field_category_it":TAXLAB[code][1]})

# ---------- i18n ----------
i18n = {
 "field_categories":{c["code"]:{"en":c["label_en"],"it":c["label_it"]} for c in TAX},
 "fee_type":{"free":{"en":"Free","it":"Gratis"},"flat":{"en":"Flat fee","it":"Tariffa fissa"},
   "income_based":{"en":"Income-based","it":"In base al reddito"},"per_credit":{"en":"Per credit (ECTS)","it":"Per credito (ECTS)"},
   "free_or_paid":{"en":"Free in national language / paid otherwise","it":"Gratis in lingua nazionale / a pagamento altrimenti"},
   "state_funded_or_paid":{"en":"State-funded places + fee-paying places","it":"Posti finanziati dallo Stato + posti a pagamento"}},
 "data_quality":{"official":{"en":"Official","it":"Ufficiale"},"official_range":{"en":"Official (range)","it":"Ufficiale (intervallo)"},
   "indicative":{"en":"Indicative (portal)","it":"Indicativo (portale)"},"partial":{"en":"Home official, intl not published","it":"Nazionale ufficiale, internazionale non pubblicato"},
   "not_available":{"en":"Not available","it":"Non disponibile"}},
 "ui":{
   "app_title":{"en":"EduMap Europe","it":"EduMap Europe"},
   "search":{"en":"Search universities","it":"Cerca universita"},
   "country":{"en":"Country","it":"Paese"},"city":{"en":"City","it":"Citta"},"field":{"en":"Field","it":"Ambito"},
   "tuition":{"en":"Tuition","it":"Retta"},"cost_of_living":{"en":"Cost of living","it":"Costo della vita"},
   "scholarships":{"en":"Scholarships","it":"Borse di studio"},"ranking":{"en":"Ranking (THE)","it":"Classifica (THE)"},
   "bachelor":{"en":"Bachelor","it":"Triennale"},"master":{"en":"Master","it":"Magistrale"},
   "eu_students":{"en":"EU / home students","it":"Studenti UE / nazionali"},"noneu_students":{"en":"Non-EU students","it":"Studenti extra-UE"},
   "per_month":{"en":"per month","it":"al mese"},"per_year":{"en":"per year","it":"all'anno"},
   "rent":{"en":"Rent","it":"Affitto"},"other_costs":{"en":"Other costs","it":"Altre spese"},
   "data_not_available":{"en":"Data not available","it":"Dato non disponibile"},
   "source":{"en":"Source","it":"Fonte"},"compare":{"en":"Compare","it":"Confronta"},
   "world_rank":{"en":"World rank","it":"Posizione mondiale"},"overall_score":{"en":"Overall score","it":"Punteggio complessivo"},
   "ranked_only":{"en":"Ranked only","it":"Solo classificate"},"city_estimate":{"en":"City estimate","it":"Stima citta"},
   "country_estimate_fallback":{"en":"National estimate (no city data)","it":"Stima nazionale (nessun dato citta)"}}
}
json.dump(i18n, open(os.path.join(DATA,"i18n.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- write CSVs ----------
def w(name, rows, fields):
    with open(os.path.join(DATA,name),"w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(rows)
    print(f"  {name}: {len(rows)} rows")
# university_fields long table (one row per offered field) for the field filter
uf_rows = []
for u in unis:
    for code in (u["fields_offered"].split("|") if u["fields_offered"] else []):
        uf_rows.append({"university_id":u["id"],"university":u["name"],"country_code":u["country_code"],
            "field_category":code,"field_category_en":TAXLAB.get(code,(code,code))[0],"field_category_it":TAXLAB.get(code,(code,code))[1],
            "source":u["fields_source"]})

print("Writing CSVs:")
w("universities.csv",unis,["id","name","country","country_code","city","lat","lon","field_category","field_category_en","field_category_it","fields_offered","fields_source","monthly_room_rent_eur","room_rent_level","room_rent_source","domain","website","the_world_rank","the_overall_score","the_teaching","the_research","the_citations","the_international_outlook","the_industry_income"])
w("room_rent_city.csv",rr_city_rows,["city","country","country_code","monthly_room_rent_eur","source_url","note"])
w("room_rent_country.csv",rr_country_rows,["country","country_code","monthly_room_rent_eur","basis","source_url","note"])
w("university_fields.csv",uf_rows,["university_id","university","country_code","field_category","field_category_en","field_category_it","source"])
w("tuition_by_country.csv",tuition_rows,["country","country_code","currency","fee_type","data_quality","bachelor_eu_min_eur","bachelor_eu_max_eur","master_eu_min_eur","master_eu_max_eur","bachelor_noneu_min_eur","bachelor_noneu_max_eur","master_noneu_min_eur","master_noneu_max_eur","official_student_budget_eur_month","notes_it","notes_en"])
w("tuition_exceptions.csv",exc_rows,["country","matched_university_id","matched_university_name","university","field","level","amount_eur_year","note","source_url"])
w("cost_of_living_city.csv",col_city_rows,["city","country","country_code","currency","monthly_rent_eur","monthly_other_eur","monthly_total_eur","official_student_budget_eur_month","source_numbeo_url","source_official_url","access_note"])
w("cost_of_living_country.csv",col_country_rows,["country","country_code","official_student_budget_eur_month","source_url","note"])
w("scholarships.csv",sch_rows,["scope","country","name","provider","coverage_en","coverage_it","eligibility_en","eligibility_it","source_url"])
w("faculties.csv",fac_rows,["id","university","city","country","country_code","faculty","field_category","field_category_en","field_category_it"])
w("field_taxonomy.csv",[{"code":c["code"],"label_en":c["label_en"],"label_it":c["label_it"]} for c in TAX],["code","label_en","label_it"])
w("university_rankings.csv",rankings_rows,["the_name","country","matched_university_id","world_rank","overall_score","teaching","research","citations_or_research_quality","international_outlook","industry_income"])

combined = {"meta":{"description":"European universities dataset: institutions (with city+coordinates+field), tuition, cost of living, scholarships, THE quality indicators. Bilingual IT/EN.",
  "universities_count":len(unis),"countries_count":len(set(u["country"] for u in unis)),
  "universities_with_city":sum(1 for u in unis if u["city"]),"cost_of_living_cities":len(col_city_rows),
  "rankings_source":rk["source"],"rankings_edition":rk["edition_year"],"rankings_matched":matched,
  "fields_source":"ETER (Zenodo full dump) where matched, else name heuristic","universities_with_eter_fields":eter_matched},
  "universities":unis,"tuition_by_country":tuition_rows,"tuition_exceptions":exc_rows,"cost_of_living_city":col_city_rows,
  "cost_of_living_country":col_country_rows,"room_rent_city":rr_city_rows,"room_rent_country":rr_country_rows,
  "scholarships":sch_rows,"faculties":fac_rows,"university_fields":uf_rows,
  "field_taxonomy":[{"code":c["code"],"label_en":c["label_en"],"label_it":c["label_it"]} for c in TAX],"university_rankings":rankings_rows}
json.dump(combined, open(os.path.join(DATA,"dataset.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
fc = Counter(u["field_category"] for u in unis)
print(f"\nUniversities: {len(unis)} | with city: {combined['meta']['universities_with_city']} | COL cities: {len(col_city_rows)} | THE matched: {matched}")
print("Field categories:", dict(fc))
