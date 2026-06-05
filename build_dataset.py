#!/usr/bin/env python3
"""Build normalized relational CSVs + combined JSON from the raw sourced data.
All figures originate in raw/*.json (each with explicit source URLs). This script
only reshapes and joins; it never invents values."""
import json, csv, re, unicodedata, os

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return json.load(f)

CC = {
 "Albania":"AL","Andorra":"AD","Austria":"AT","Belarus":"BY","Belgium":"BE","Bosnia and Herzegovina":"BA","Bulgaria":"BG",
 "Croatia":"HR","Cyprus":"CY","Czech Republic":"CZ","Denmark":"DK","Estonia":"EE","Finland":"FI","France":"FR",
 "Germany":"DE","Greece":"GR","Hungary":"HU","Iceland":"IS","Ireland":"IE","Italy":"IT","Kosovo":"XK","Latvia":"LV","Liechtenstein":"LI",
 "Lithuania":"LT","Luxembourg":"LU","Malta":"MT","Moldova":"MD","Monaco":"MC","Montenegro":"ME","Netherlands":"NL","North Macedonia":"MK",
 "Norway":"NO","Poland":"PL","Portugal":"PT","Romania":"RO","Russian Federation":"RU","San Marino":"SM","Serbia":"RS","Slovakia":"SK",
 "Slovenia":"SI","Spain":"ES","Sweden":"SE","Switzerland":"CH","Ukraine":"UA","United Kingdom":"GB"}

# ---------- base universities (from Hipolabs European subset) ----------
world = json.load(open(os.path.join(ROOT, "world_universities.json"), encoding="utf-8"))
unis = []
i = 0
for u in world:
    if u["country"] in CC:
        i += 1
        unis.append({
            "id": i, "name": u["name"], "country": u["country"], "country_code": CC[u["country"]],
            "state_province": u.get("state-province") or "",
            "domain": (u["domains"][0] if u.get("domains") else ""),
            "website": (u["web_pages"][0] if u.get("web_pages") else ""),
        })

# ---------- fuzzy join helpers ----------
STOP = {"university","universite","universitat","universita","universitaet","universidad","universidade",
        "the","of","de","di","du","del","della","der","den","das","la","le","el","and","et","for","studies",
        "college","institute","institut","school","hochschule","politecnico","politechnika","technical","technische",
        "polytechnic","national","state","public","higher","education","sciences","science","applied"}

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9 ]"," ", s)
    return s

def tokens(s):
    return {t for t in norm(s).split() if t and t not in STOP and len(t) > 1}

# index universities by country_code -> list of (tokenset, uni)
idx = {}
for u in unis:
    idx.setdefault(u["country_code"], []).append((tokens(u["name"]), u))

THE_COUNTRY_TO_CC = dict(CC)  # THE uses same English country names for our set

def best_match(name, country):
    cc = THE_COUNTRY_TO_CC.get(country)
    if not cc or cc not in idx:
        return None
    nt = tokens(name)
    if not nt:
        return None
    best, best_score = None, 0.0
    for ut, u in idx[cc]:
        if not ut:
            continue
        inter = len(nt & ut)
        if inter == 0:
            continue
        score = inter / len(nt | ut)  # Jaccard
        if score > best_score:
            best, best_score = u, score
    return best if best_score >= 0.6 else None

# ---------- rankings ----------
rk = load("rankings_the.json")
rk_unis = rk["universities"]
rankings_rows = []
matched = 0
uni_rank = {}  # uni id -> (world_rank, overall)
for r in rk_unis:
    m = best_match(r["name"], r["country"])
    uid = m["id"] if m else ""
    if m:
        matched += 1
        uni_rank[m["id"]] = (r.get("world_rank",""), r.get("overall_score",""))
    rankings_rows.append({
        "the_name": r["name"], "country": r["country"], "matched_university_id": uid,
        "world_rank": r.get("world_rank",""), "overall_score": r.get("overall_score",""),
        "teaching": r.get("teaching",""), "research": r.get("research",""),
        "citations_or_research_quality": r.get("citations_or_research_quality",""),
        "international_outlook": r.get("international_outlook",""),
        "industry_income": r.get("industry_income",""),
    })

for u in unis:
    wr, ov = uni_rank.get(u["id"], ("",""))
    u["the_world_rank"] = wr
    u["the_overall_score"] = ov

# ---------- tuition by country ----------
def fmt(v):
    if v is None: return "not found / see notes"
    return str(v)

tuition_rows = []
eu15 = load("tuition_eu15.json")
for r in eu15:
    tuition_rows.append({
        "country": r["country"], "country_code": CC.get(r["country"],""), "currency": r["currency"],
        "bachelor_eu": fmt(r["bachelor_eu"]), "master_eu": fmt(r["master_eu"]),
        "bachelor_noneu": fmt(r["bachelor_noneu"]), "master_noneu": fmt(r["master_noneu"]),
        "basis": r["basis"], "official_student_budget_eur_month": "",
        "notes": r["notes"], "sources": " | ".join(r["sources"]),
    })
other = load("tuition_other_countries.json")
for r in other:
    tuition_rows.append({
        "country": r["country"], "country_code": CC.get(r["country"],""), "currency": r["currency"],
        "bachelor_eu": r["bachelor_eu"], "master_eu": r["master_eu"],
        "bachelor_noneu": r["bachelor_noneu"], "master_noneu": r["master_noneu"],
        "basis": r["basis"],
        "official_student_budget_eur_month": ("" if r.get("official_student_budget_eur_month") is None else r["official_student_budget_eur_month"]),
        "notes": r["notes"], "sources": " | ".join(r["sources"]),
    })
# micro-states not researched
for ms in ["Andorra","Liechtenstein","San Marino","Monaco"]:
    tuition_rows.append({"country":ms,"country_code":CC[ms],"currency":"EUR",
        "bachelor_eu":"not researched","master_eu":"not researched","bachelor_noneu":"not researched","master_noneu":"not researched",
        "basis":"micro-state, 1-2 institutions; not covered in this release","official_student_budget_eur_month":"",
        "notes":"Micro-state with very few institutions; tuition framework not researched in this release.","sources":""})

# ---------- tuition exceptions (institution-specific) ----------
exc_rows = []
for r in eu15:
    for e in r.get("university_exceptions", []):
        exc_rows.append({
            "country": r["country"], "university": e["university"], "field": e.get("field",""),
            "level": e.get("level",""), "amount_eur_year": fmt(e.get("amount_eur")),
            "note": e.get("note",""), "source_url": e.get("source_url",""),
        })

# ---------- cost of living: city ----------
col = load("cost_of_living.json")
col_city_rows = []
budget_by_country = {}
for c in col:
    col_city_rows.append({
        "city": c["city"], "country": c["country"], "country_code": CC.get(c["country"],""), "currency": c["currency"],
        "monthly_rent_eur": c["monthly_rent_eur"], "monthly_other_eur": c["monthly_other_eur"],
        "monthly_total_eur": c["monthly_total_eur"],
        "official_student_budget_eur_month": ("" if c.get("official_student_budget_eur") is None else c["official_student_budget_eur"]),
        "source_numbeo_url": c.get("source_numbeo_url",""), "source_official_url": c.get("source_official_url",""),
        "access_note": c.get("access_note",""),
    })
    if c.get("official_student_budget_eur") is not None and c["country"] not in budget_by_country:
        budget_by_country[c["country"]] = (c["official_student_budget_eur"], c.get("source_official_url",""))

# ---------- cost of living: country (official student budget) ----------
for r in other:
    b = r.get("official_student_budget_eur_month")
    if b is not None and r["country"] not in budget_by_country:
        src = r["sources"][0] if r.get("sources") else ""
        budget_by_country[r["country"]] = (b, src)
col_country_rows = []
for country, (b, src) in sorted(budget_by_country.items()):
    col_country_rows.append({
        "country": country, "country_code": CC.get(country,""),
        "official_student_budget_eur_month": b, "source_url": src,
        "note": "Official figure: national student-budget estimate or study-visa financial-means benchmark (see source).",
    })

# ---------- scholarships ----------
sch = load("scholarships.json")
sch_rows = []
for s in sch["eu_wide"]:
    sch_rows.append({"scope":"EU-wide","country":"","name":s["name"],"provider":s["provider"],
        "coverage":s["coverage"],"eligibility":s["eligibility"],"source_url":s["source_url"]})
for blk in sch["by_country"]:
    for s in blk["scholarships"]:
        sch_rows.append({"scope":"national","country":blk["country"],"name":s["name"],"provider":s["provider"],
            "coverage":s["coverage"],"eligibility":s["eligibility"],"source_url":s["source_url"]})

# ---------- faculties ----------
df = load("datasets_and_faculties.json")
fac_rows = []
fid = 0
for u in df["universities"]:
    for fac in u["faculties"]:
        fid += 1
        fac_rows.append({"id":fid,"university":u["name"],"city":u["city"],"country":u["country"],
            "country_code":u["country_code"],"faculty":fac})

# ---------- write CSVs ----------
def write_csv(name, rows, fields):
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"  {name}: {len(rows)} rows")

print("Writing CSVs:")
write_csv("universities.csv", unis, ["id","name","country","country_code","state_province","domain","website","the_world_rank","the_overall_score"])
write_csv("tuition_by_country.csv", tuition_rows, ["country","country_code","currency","bachelor_eu","master_eu","bachelor_noneu","master_noneu","basis","official_student_budget_eur_month","notes","sources"])
write_csv("tuition_exceptions.csv", exc_rows, ["country","university","field","level","amount_eur_year","note","source_url"])
write_csv("cost_of_living_city.csv", col_city_rows, ["city","country","country_code","currency","monthly_rent_eur","monthly_other_eur","monthly_total_eur","official_student_budget_eur_month","source_numbeo_url","source_official_url","access_note"])
write_csv("cost_of_living_country.csv", col_country_rows, ["country","country_code","official_student_budget_eur_month","source_url","note"])
write_csv("scholarships.csv", sch_rows, ["scope","country","name","provider","coverage","eligibility","source_url"])
write_csv("faculties.csv", fac_rows, ["id","university","city","country","country_code","faculty"])
write_csv("university_rankings.csv", rankings_rows, ["the_name","country","matched_university_id","world_rank","overall_score","teaching","research","citations_or_research_quality","international_outlook","industry_income"])

# ---------- combined JSON ----------
combined = {
    "meta": {
        "description": "European universities dataset: institutions, tuition, cost of living, scholarships and THE quality indicators.",
        "universities_count": len(unis), "countries_count": len(set(u["country"] for u in unis)),
        "rankings_source": rk["source"], "rankings_edition": rk["edition_year"],
        "rankings_matched_to_universities": matched, "rankings_total_european": len(rk_unis),
    },
    "universities": unis,
    "tuition_by_country": tuition_rows,
    "tuition_exceptions": exc_rows,
    "cost_of_living_city": col_city_rows,
    "cost_of_living_country": col_country_rows,
    "scholarships": sch_rows,
    "faculties": fac_rows,
    "university_rankings": rankings_rows,
}
with open(os.path.join(DATA, "dataset.json"), "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=1)
print(f"\ndataset.json written. Universities: {len(unis)} | THE rankings matched: {matched}/{len(rk_unis)} ({100*matched//len(rk_unis)}%)")
