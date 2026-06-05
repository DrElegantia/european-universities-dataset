#!/usr/bin/env python3
"""Assign a city (+ lat/lon) to each European university by matching its name
against the GeoNames cities15000 gazetteer, restricted to the same country and
preferring the most populous match. Outputs uni_city.json (id->city info) and
cities_rank.json (cities sorted by university count) for cost-of-living coverage."""
import json, csv, re, unicodedata, os
ROOT = os.path.dirname(os.path.abspath(__file__))

CC = {"Albania":"AL","Andorra":"AD","Austria":"AT","Belarus":"BY","Belgium":"BE","Bosnia and Herzegovina":"BA","Bulgaria":"BG",
 "Croatia":"HR","Cyprus":"CY","Czech Republic":"CZ","Denmark":"DK","Estonia":"EE","Finland":"FI","France":"FR","Germany":"DE",
 "Greece":"GR","Hungary":"HU","Iceland":"IS","Ireland":"IE","Italy":"IT","Kosovo":"XK","Latvia":"LV","Liechtenstein":"LI",
 "Lithuania":"LT","Luxembourg":"LU","Malta":"MT","Moldova":"MD","Monaco":"MC","Montenegro":"ME","Netherlands":"NL","North Macedonia":"MK",
 "Norway":"NO","Poland":"PL","Portugal":"PT","Romania":"RO","Russian Federation":"RU","San Marino":"SM","Serbia":"RS","Slovakia":"SK",
 "Slovenia":"SI","Spain":"ES","Sweden":"SE","Switzerland":"CH","Ukraine":"UA","United Kingdom":"GB"}
ISO = set(CC.values())

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)

# city names that are actually institution words (GeoNames has a Madrid barrio "Universidad", etc.)
CITY_BLOCK = {"universidad","universitat","universite","university","politecnica","politecnico",
              "institut","instituto","college","academia","academy","central","nacional","national","federal","state"}

# build gazetteer: country_code -> list of (cityname_norm, pop, canonical, lat, lon) sorted by pop desc
gaz = {}
with open(os.path.join(ROOT,"cities15000.txt"), encoding="utf-8") as f:
    for line in f:
        p = line.split("\t")
        if len(p) < 15: continue
        cc = p[8]
        if cc not in ISO: continue
        try: pop = int(p[14])
        except: pop = 0
        lat, lon = p[4], p[5]
        canonical = p[1]
        names = set()
        names.add(norm(p[2]))  # asciiname
        for alt in p[3].split(","):
            an = norm(alt)
            if an and an.isascii() and len(an) >= 4:
                names.add(an)
        for nm in names:
            nm = nm.strip()
            if len(nm) >= 4 and nm not in CITY_BLOCK:
                gaz.setdefault(cc, []).append((nm, pop, canonical, lat, lon))
for cc in gaz:
    gaz[cc].sort(key=lambda x: -x[1])  # population desc

world = json.load(open(os.path.join(ROOT,"world_universities.json"), encoding="utf-8"))
uni_city = {}
counts = {}
i = 0; matched = 0
for u in world:
    if u["country"] not in CC: continue
    i += 1
    cc = CC[u["country"]]
    un = norm(u["name"])
    found = None
    for nm, pop, canonical, lat, lon in gaz.get(cc, []):
        if re.search(r"\b" + re.escape(nm) + r"\b", un):
            found = (canonical, lat, lon); break
    if found:
        matched += 1
        uni_city[i] = {"city": found[0], "lat": found[1], "lon": found[2]}
        key = (found[0], cc)
        counts[key] = counts.get(key, 0) + 1
    else:
        uni_city[i] = {"city":"", "lat":"", "lon":""}

json.dump(uni_city, open(os.path.join(ROOT,"raw","uni_city.json"),"w"))
cities_rank = sorted([{"city":c,"country_code":cc,"university_count":n} for (c,cc),n in counts.items()], key=lambda x:-x["university_count"])
json.dump(cities_rank, open(os.path.join(ROOT,"raw","cities_rank.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)

EXISTING = {"Munich","Heidelberg","Paris","Milan","Bologna","Rome","Amsterdam","Delft","Leuven","Madrid",
"Barcelona","Vienna","Zurich","Lausanne","Stockholm","Lund","Copenhagen","Helsinki","Dublin","Warsaw","Prague","Lisbon","Coimbra"}
to_fetch = [r for r in cities_rank if r["city"] not in EXISTING and r["university_count"] >= 2][:90]
json.dump(to_fetch, open(os.path.join(ROOT,"raw","cities_to_fetch.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Universita totali: {i} | con citta assegnata: {matched} ({100*matched//i}%)")
print(f"Citta distinte: {len(counts)} | da arricchire con Numbeo (top, count>=2, escluse le 23 esistenti): {len(to_fetch)}")
print("Top 50 citta per numero di atenei:")
for r in cities_rank[:50]:
    print(f"  {r['university_count']:4d}  {r['city']} ({r['country_code']})")
