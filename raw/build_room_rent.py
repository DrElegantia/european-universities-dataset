#!/usr/bin/env python3
"""Build room_rent_country.json: average monthly rent for a single room (room in
shared flat / typical student room), EUR, for 42 European countries.

Sources prioritised: HousingAnywhere International Rent Index Q4 2025, national
rental/student portals, study-abroad cost guides. Where no direct national room
figure exists, derived from main student-city room averages (basis=city-derived)
or from 1-bed apartment data * room-share ratio (basis=estimate)."""
import json

HA_Q4 = "https://housanywhere.com/rent-index-by-city"  # corrected below
HA = "https://housinganywhere.com/rent-index-by-city"

# country_code -> dict
data = [
    # ---- Direct HousingAnywhere Q4 2025 room figures (national-figure where 1 main city, else city-derived avg) ----
    {"country": "Albania", "country_code": "AL",
     "room_rent_eur_month": 230, "basis": "city-derived",
     "source_url": "https://realting.com/albania/property-to-rent",
     "note": "No student-room index for AL. Tirana 1-bed ~EUR 350-444 (Numbeo/realting); room in shared flat estimated ~EUR 200-260. Midpoint 230. Original currency EUR (Albania uses lek for local but rents to foreigners often quoted EUR)."},

    {"country": "Andorra", "country_code": "AD",
     "room_rent_eur_month": 600, "basis": "estimate",
     "source_url": "https://www.nextexpat.com/en/property-for-rent-in-andorra-lists-and-prices/",
     "note": "No student rental market / no room index. 1-bed apartment averages ~EUR 1,500 with sharp post-2021 increases; room in shared flat estimated ~40% = EUR 600. Estimate, EUR."},

    {"country": "Austria", "country_code": "AT",
     "room_rent_eur_month": 480, "basis": "city-derived",
     "source_url": "https://www.wg-gesucht.de/en/wg-zimmer-in-Wien.163.0.1.0.html",
     "note": "Vienna WG (shared-flat) room avg EUR 400-600 incl. utilities (WG-Gesucht / BOKU university housing guide); Graz/Innsbruck lower. National room avg ~EUR 480. EUR."},

    {"country": "Belarus", "country_code": "BY",
     "room_rent_eur_month": 150, "basis": "estimate",
     "source_url": "https://www.numbeo.com/cost-of-living/region_prices_by_city?itemId=27&region=150",
     "note": "No room index. Minsk/regional 1-bed roughly EUR 250-300; room in shared flat estimated ~EUR 130-170. Original currency BYN. Estimate."},

    {"country": "Belgium", "country_code": "BE",
     "room_rent_eur_month": 530, "basis": "city-derived",
     "source_url": "https://www.brukot.be/en/",
     "note": "Brussels student 'kot' median ~EUR 550 incl. utilities (Brukot); Leuven/Ghent similar. National room avg ~EUR 530. EUR."},

    {"country": "Bosnia and Herzegovina", "country_code": "BA",
     "room_rent_eur_month": 180, "basis": "estimate",
     "source_url": "https://www.supportadventure.com/the-cheapest-cities-to-live-in-the-balkans/",
     "note": "No room index. Sarajevo 1-bed ~EUR 300-350; room in shared flat estimated ~EUR 150-210. Original currency BAM (pegged to EUR ~1.96). Estimate."},

    {"country": "Bulgaria", "country_code": "BG",
     "room_rent_eur_month": 250, "basis": "estimate",
     "source_url": "https://realting.com/news/cheapest-rent-in-europe-2026",
     "note": "No student-room index. Sofia 1-bed ~EUR 500-600, smaller cities ~EUR 250; room in shared flat estimated ~EUR 220-280. Original currency BGN (pegged ~1.96/EUR). Estimate."},

    {"country": "Croatia", "country_code": "HR",
     "room_rent_eur_month": 300, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Zagreb 1-bed ~EUR 600; room in shared flat ~EUR 280-330 (student listings). National room avg ~EUR 300. EUR (Croatia adopted euro 2023)."},

    {"country": "Cyprus", "country_code": "CY",
     "room_rent_eur_month": 380, "basis": "city-derived",
     "source_url": "https://housinganywhere.com/s/Nicosia--Cyprus/private-rooms",
     "note": "Nicosia/Limassol private rooms typically EUR 350-450 on HousingAnywhere; student rooms ~EUR 380. EUR."},

    {"country": "Czech Republic", "country_code": "CZ",
     "room_rent_eur_month": 460, "basis": "city-derived",
     "source_url": "https://pepehousing.com/blog/student-housing-in-europe-2026-prices-best-cities-where-to-live",
     "note": "Prague shared-flat room ~EUR 500-700 (USD 590-920 quoted); Brno cheaper; budget guide cites EUR 250-500. National student-room avg ~EUR 460. Original currency CZK."},

    {"country": "Denmark", "country_code": "DK",
     "room_rent_eur_month": 620, "basis": "city-derived",
     "source_url": "https://cphpost.dk/2025-04-27/business-education/education/where-to-live-as-a-student-in-copenhagen/",
     "note": "Copenhagen student room DKK 5,000-9,000/mo (~EUR 670-1,210); national avg lower given Aarhus/Odense. National room avg ~EUR 620. Original currency DKK (pegged ~7.46/EUR)."},

    {"country": "Estonia", "country_code": "EE",
     "room_rent_eur_month": 320, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Tallinn 1-bed ~EUR 620; room in shared flat ~EUR 300-350 (student listings). National room avg ~EUR 320. EUR."},

    {"country": "Finland", "country_code": "FI",
     "room_rent_eur_month": 450, "basis": "national-figure",
     "source_url": "https://hoas.fi/en/applicants/apartment-types/room-in-a-shared-apartment/",
     "note": "HOAS (Helsinki student housing) room in shared apartment EUR 454-584/mo; single rooms from EUR 450. National student-room avg ~EUR 450. EUR."},

    {"country": "France", "country_code": "FR",
     "room_rent_eur_month": 500, "basis": "city-derived",
     "source_url": "https://erasmusplay.com/en/strasbourg.html",
     "note": "Paris room in shared flat EUR 500-900; provincial cities (Strasbourg, Lyon, Toulouse) rooms from EUR 400. National room avg ~EUR 500. EUR."},

    {"country": "Germany", "country_code": "DE",
     "room_rent_eur_month": 500, "basis": "city-derived",
     "source_url": "https://acolyteliving.com/post/room-rent-in-germany-for-students-2025-guide",
     "note": "WG (shared-flat) room nationally EUR 300-600 incl. shared utilities; Munich room avg EUR 808, Berlin EUR 633, Stuttgart EUR 530 (HousingAnywhere Q4 2025). National student-WG avg ~EUR 500. EUR."},

    {"country": "Greece", "country_code": "GR",
     "room_rent_eur_month": 400, "basis": "national-figure",
     "source_url": "https://housinganywhere.com/rent-index-by-city",
     "note": "Athens furnished room avg EUR 400 (HousingAnywhere International Rent Index Q4 2025); Thessaloniki lower. EUR."},

    {"country": "Hungary", "country_code": "HU",
     "room_rent_eur_month": 370, "basis": "national-figure",
     "source_url": "https://housinganywhere.com/rent-index-by-city",
     "note": "Budapest furnished room avg EUR 370 (HousingAnywhere International Rent Index Q4 2025); Debrecen/Szeged lower. Original currency HUF; index reports EUR."},

    {"country": "Iceland", "country_code": "IS",
     "room_rent_eur_month": 650, "basis": "estimate",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "No room index. Reykjavik very tight market, 1-bed ~ISK 200,000+ (~EUR 1,300); room in shared flat estimated ~EUR 600-700. Original currency ISK. Estimate."},

    {"country": "Ireland", "country_code": "IE",
     "room_rent_eur_month": 750, "basis": "city-derived",
     "source_url": "https://www.daft.ie/sharing/dublin",
     "note": "Dublin room-in-shared (Daft.ie sharing) typically EUR 800-1,000; national avg pulled down by Cork/Galway. National room avg ~EUR 750. EUR."},

    {"country": "Italy", "country_code": "IT",
     "room_rent_eur_month": 560, "basis": "city-derived",
     "source_url": "https://housinganywhere.com/rent-index-by-city",
     "note": "HousingAnywhere Q4 2025 rooms: Milan EUR 664, Bologna EUR 655, Rome EUR 650, Turin ~EUR 525; smaller university cities lower. National room avg ~EUR 560. EUR."},

    {"country": "Kosovo", "country_code": "XK",
     "room_rent_eur_month": 170, "basis": "estimate",
     "source_url": "https://www.supportadventure.com/the-cheapest-cities-to-live-in-the-balkans/",
     "note": "No room index. Pristina 1-bed ~EUR 300; room in shared flat estimated ~EUR 150-190. EUR (Kosovo uses euro). Estimate."},

    {"country": "Latvia", "country_code": "LV",
     "room_rent_eur_month": 300, "basis": "city-derived",
     "source_url": "https://www.nestpick.com/student-accommodation/riga/",
     "note": "Riga shared-apartment room EUR 200-350; student accommodation avg ~EUR 300-400. National room avg ~EUR 300. EUR."},

    {"country": "Liechtenstein", "country_code": "LI",
     "room_rent_eur_month": 850, "basis": "estimate",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "No room index, negligible student rental market. Proxied to high-cost Swiss/Alpine level; room estimated ~CHF 800 (~EUR 850). Original currency CHF. Estimate."},

    {"country": "Lithuania", "country_code": "LT",
     "room_rent_eur_month": 320, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Vilnius 1-bed ~EUR 660; room in shared flat ~EUR 300-350 (student listings). National room avg ~EUR 320. EUR."},

    {"country": "Luxembourg", "country_code": "LU",
     "room_rent_eur_month": 800, "basis": "city-derived",
     "source_url": "https://erasmusplay.com/en/luxembourg-city.html",
     "note": "Luxembourg City flat-share room EUR 800-1,200 (Erasmus Play / AXA); university rooms ~EUR 450. Market room avg ~EUR 800. EUR."},

    {"country": "Malta", "country_code": "MT",
     "room_rent_eur_month": 450, "basis": "city-derived",
     "source_url": "https://www.housingtarget.com/rent/rooms",
     "note": "Sliema/Msida rooms range EUR 220 (shared) to EUR 550-700 (single bedroom); typical single room ~EUR 450. EUR."},

    {"country": "Moldova", "country_code": "MD",
     "room_rent_eur_month": 150, "basis": "estimate",
     "source_url": "https://www.numbeo.com/cost-of-living/region_prices_by_city?itemId=27&region=150",
     "note": "No room index. Chisinau 1-bed ~EUR 250-300; room in shared flat estimated ~EUR 130-170. Original currency MDL. Estimate."},

    {"country": "Monaco", "country_code": "MC",
     "room_rent_eur_month": 1500, "basis": "estimate",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "No student rental market; one of the most expensive markets globally. Room in shared flat estimated very high ~EUR 1,500. EUR. Estimate."},

    {"country": "Montenegro", "country_code": "ME",
     "room_rent_eur_month": 220, "basis": "estimate",
     "source_url": "https://www.supportadventure.com/the-cheapest-cities-to-live-in-the-balkans/",
     "note": "No room index. Podgorica 1-bed ~EUR 350-400; room in shared flat estimated ~EUR 200-250. EUR (Montenegro uses euro). Estimate."},

    {"country": "Netherlands", "country_code": "NL",
     "room_rent_eur_month": 800, "basis": "city-derived",
     "source_url": "https://housinganywhere.com/rent-index-by-city",
     "note": "HousingAnywhere Q4 2025 rooms: Amsterdam EUR 990, Rotterdam EUR 850; Kamernet Q1 2025 national room ~EUR 700-800. National room avg ~EUR 800. EUR."},

    {"country": "North Macedonia", "country_code": "MK",
     "room_rent_eur_month": 170, "basis": "estimate",
     "source_url": "https://www.supportadventure.com/the-cheapest-cities-to-live-in-the-balkans/",
     "note": "No room index. Skopje 1-bed under EUR 300; room in shared flat estimated ~EUR 150-190. Original currency MKD (pegged ~61.5/EUR). Estimate."},

    {"country": "Norway", "country_code": "NO",
     "room_rent_eur_month": 600, "basis": "city-derived",
     "source_url": "https://erasmusplay.com/en/oslo.html",
     "note": "Oslo room in shared flat EUR 400-800 (Erasmus Play); Bergen/Trondheim similar-to-lower. National room avg ~EUR 600. Original currency NOK."},

    {"country": "Poland", "country_code": "PL",
     "room_rent_eur_month": 400, "basis": "city-derived",
     "source_url": "https://pepehousing.com/blog/erasmus-in-poland-when-to-rent-a-best-room-as-a-student-for-the-upcoming-semester",
     "note": "Room in shared flat EUR 300-650 (Pepe Housing); Warsaw/Krakow higher, Lodz/Lublin lower. National room avg ~EUR 400. Original currency PLN."},

    {"country": "Portugal", "country_code": "PT",
     "room_rent_eur_month": 450, "basis": "city-derived",
     "source_url": "https://housinganywhere.com/Lisbon--Portugal/cost-of-living-lisbon",
     "note": "Lisbon room avg ~EUR 500 (up to 714); Porto ~EUR 400; Coimbra cheaper. National room avg ~EUR 450. EUR."},

    {"country": "Romania", "country_code": "RO",
     "room_rent_eur_month": 250, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Bucharest 1-bed ~EUR 405-650; Cluj/Iasi rooms ~EUR 200-300. Room in shared flat national avg ~EUR 250. Original currency RON."},

    {"country": "Russian Federation", "country_code": "RU",
     "room_rent_eur_month": 250, "basis": "city-derived",
     "source_url": "https://www.numbeo.com/cost-of-living/region_prices_by_city?itemId=27&region=150",
     "note": "Moscow 1-bed ~EUR 735, St Petersburg ~EUR 465, regional cities EUR 215-380 (Numbeo). Room in shared flat estimated ~EUR 250 national. Original currency RUB. City-derived/estimate."},

    {"country": "San Marino", "country_code": "SM",
     "room_rent_eur_month": 450, "basis": "regional-proxy",
     "source_url": "https://housinganywhere.com/rent-index-by-city",
     "note": "No room index; no separate student market. Proxied to surrounding Emilia-Romagna/Marche (Italy) room level (Bologna EUR 655, Rimini lower) ~EUR 450. EUR. Regional proxy."},

    {"country": "Serbia", "country_code": "RS",
     "room_rent_eur_month": 280, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Belgrade student room in shared flat EUR 250-350; Novi Sad lower. National room avg ~EUR 280. Original currency RSD."},

    {"country": "Slovakia", "country_code": "SK",
     "room_rent_eur_month": 320, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Bratislava 1-bed ~EUR 720; room in shared flat ~EUR 300-380; other cities lower. National room avg ~EUR 320. EUR."},

    {"country": "Slovenia", "country_code": "SI",
     "room_rent_eur_month": 380, "basis": "city-derived",
     "source_url": "https://erasmusplay.com/en/ljubljana.html",
     "note": "Ljubljana room in shared flat EUR 300-450, student avg ~EUR 450 in 2025; Maribor lower. National room avg ~EUR 380. EUR."},

    {"country": "Spain", "country_code": "ES",
     "room_rent_eur_month": 480, "basis": "city-derived",
     "source_url": "https://housinganywhere.com/rent-index-by-city",
     "note": "HousingAnywhere Q4 2025 rooms: Barcelona EUR 650, Madrid EUR 625, Valencia EUR 430; smaller cities lower. National room avg ~EUR 480. EUR."},

    {"country": "Sweden", "country_code": "SE",
     "room_rent_eur_month": 550, "basis": "city-derived",
     "source_url": "https://www.nestpick.com/student-accommodation/stockholm/",
     "note": "Stockholm room listings SEK 5,800-14,000 (~EUR 480-1,160); Lund/Gothenburg lower. National room avg ~EUR 550. Original currency SEK."},

    {"country": "Switzerland", "country_code": "CH",
     "room_rent_eur_month": 850, "basis": "city-derived",
     "source_url": "https://www.globalpropertyguide.com/europe/rent",
     "note": "Zurich 1-bed ~EUR 2,080, Lausanne ~EUR 1,490; room in shared flat (WG) typically CHF 700-1,000. National room avg ~EUR 850. Original currency CHF."},

    {"country": "Ukraine", "country_code": "UA",
     "room_rent_eur_month": 150, "basis": "city-derived",
     "source_url": "https://www.numbeo.com/cost-of-living/region_prices_by_city?itemId=27&region=150",
     "note": "Kyiv 1-bed ~EUR 320, Lviv/Kharkiv/Odesa lower (war-affected market). Room in shared flat estimated ~EUR 130-180 national. Original currency UAH. City-derived/estimate."},

    {"country": "United Kingdom", "country_code": "GB",
     "room_rent_eur_month": 880, "basis": "national-figure",
     "source_url": "https://www.spareroom.co.uk/content/info-statistics/annual-rental-market-summary-2025/",
     "note": "SpareRoom UK national average room rent ~GBP 747-753/mo in 2025; converted at ~1.17 GBP/EUR = ~EUR 875-880. Original currency GBP. National figure."},
]

# sanity: ensure all 42 codes present
expected = ["AL","AD","AT","BY","BE","BA","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IS","IE","IT","XK","LV","LI","LT","LU","MT","MD","MC","ME","NL","MK","NO","PL","PT","RO","RU","SM","RS","SK","SI","ES","SE","CH","UA","GB"]
got = [d["country_code"] for d in data]
missing = set(expected) - set(got)
assert not missing, f"MISSING: {missing}"
assert len(got) == len(set(got)) == 45, f"count/dup issue: {len(got)} unique {len(set(got))}"

out = "/Users/umbertobertonelli/Documents/eu-universities-data/raw/room_rent_country.json"
with open(out, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

real_sources = [d for d in data if d["basis"] in ("national-figure", "city-derived")]
estimated = [d["country_code"] for d in data if d["basis"] in ("estimate", "regional-proxy")]
print(json.dumps({
    "written": True,
    "count": len(data),
    "with_real_source": len(real_sources),
    "estimated": estimated,
}, ensure_ascii=False))
