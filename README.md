# European Universities Dataset

Structured, **source-cited**, **bilingual (IT/EN)** data on European universities: institutions (with city, coordinates and a controlled field category), tuition fees (numeric EUR ranges), student cost of living per city, scholarships and quality indicators (Times Higher Education rankings). Built as a clean data layer for a web app on top (a "study in Europe" cost/quality explorer).

The data is **relational**: a base list of all European universities plus dimension tables joined by `country_code` / `city` / university name. Most public-university tuition in Europe is set at the **country level** (country × cycle × EU/non-EU), so tuition lives in a per-country table; institution-specific exceptions are separate.

## What's inside (`data/`)

| File | Rows | What it is |
|---|---|---|
| `universities.csv` | 2392 | Every European university: name, country, **city + lat/lon**, **field_category** (controlled, IT+EN), domain, website, THE world rank + overall score |
| `tuition_by_country.csv` | 45 | Tuition per country as **numeric EUR min/max** for bachelor/master × EU/non-EU + `fee_type` + `data_quality` + bilingual notes |
| `tuition_exceptions.csv` | 29 | Institution-specific tuition where it differs from the national rule (each with source) |
| `cost_of_living_city.csv` | 66 | Monthly student cost of living per city (rent / other / total), Numbeo, with access notes |
| `cost_of_living_country.csv` | 26 | Official national student-budget / visa benchmark per country (fallback) |
| `scholarships.csv` | 20 | EU-wide + national scholarships, coverage & eligibility **in IT and EN**, with source |
| `faculties.csv` | 120 | Faculties for 24 reference universities, each mapped to a `field_category` |
| `field_taxonomy.csv` | 14 | The controlled field vocabulary (code, label_en, label_it) |
| `university_rankings.csv` | 1043 | THE 2026 quality indicators for every ranked European university |
| `i18n.json` | - | UI strings + enum labels (field categories, fee_type, data_quality) in EN/IT |
| `dataset.json` | - | Everything in one JSON, plus `meta` |

`raw/` keeps the original sourced research; `build_dataset.py` regenerates `data/` from `raw/` (run `python3 build_dataset.py`). `assign_cities.py` derives the city per university from the GeoNames gazetteer.

## How to join (for the app)

- **University → tuition**: `universities.country_code` → `tuition_by_country.country_code`. Use the numeric `*_min_eur` / `*_max_eur` columns for price filters; show `fee_type` and a `data_quality` badge.
- **University → institution-specific tuition**: match `tuition_exceptions.university` to `universities.name`; show it instead of the country framework when present.
- **University → cost of living**: by `universities.city` → `cost_of_living_city.city` (same country_code); **if the city is not present, fall back** to `cost_of_living_country` by `country_code`.
- **University → field filter**: `universities.field_category` (one of the 14 codes in `field_taxonomy.csv`). Every university has exactly one, so the filter has clean buckets.
- **University → scholarships**: `scope = EU-wide` rows apply to all; `national` rows by `country`.
- **University → quality**: `universities.the_world_rank` / `the_overall_score`, full pillar scores via `university_rankings.matched_university_id` → `universities.id`.
- **Map**: `universities.lat` / `lon` (city-level coordinates) for the 1540 universities with a resolved city.

## Important data caveats

- **No invented numbers.** Where no authoritative figure exists the field is empty and `data_quality` says `not_available` / `partial`. International (non-EU) fees in several Eastern-European countries are HEI-set ranges flagged `indicative` (from official study portals), not flat tariffs. Never render an empty value as `0`.
- **EU vs non-EU.** `*_eu_*` = home/EU/EEA (for non-EU countries this means domestic/state-funded); `*_noneu_*` = international. Post-Brexit, EU students in the UK pay international rates.
- **Field category is institution-level**, classified from the university name (e.g. "Technical University" → Engineering & Technology; general universities → Comprehensive). It is the institution's primary character, not an exhaustive programme list. ~62% of fields are Comprehensive.
- **City** is derived from the university name via GeoNames (1540 of 2392 resolved; the rest fall back to national cost of living). Coordinates are city-level, not campus-level.
- **Cost of living** is a point-in-time Numbeo estimate (accessed June 2026) plus official student-budget benchmarks; indicative, not a guaranteed budget. 66 cities have city-level data; uncovered cities use the national figure. (Numbeo rate-limited the run, so coverage can be extended later.)
- **Currencies.** Non-euro countries show EUR-converted figures with the original currency in `currency` and details in the notes.

## Sources

Every figure is traceable. See `SOURCES.md`. Primary sources: national study portals and ministries, EU Eurydice national-fee pages, university fee pages, Numbeo (cost of living), Times Higher Education 2026 (rankings), Hipolabs university-domains-list (base list, MIT), GeoNames (cities, CC-BY).

See `SCHEMA.md` for field definitions.
