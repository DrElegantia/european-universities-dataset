# European Universities Dataset

Structured, **source-cited** data on European universities: institutions, tuition fees, student cost of living, scholarships and quality indicators (rankings). Built as a clean data layer for a web app to be developed on top (e.g. a "study in Europe" cost/quality explorer).

The data is **relational**: a base list of all European universities, plus dimension tables you join to it by `country` / `country_code` / `city` / university name. Most public-university tuition in Europe is set at the **country level** (country × cycle × EU/non-EU), so tuition lives in a per-country table; institution-specific exceptions (e.g. non-EU engineering fees, English-taught medicine) are in a separate table.

## What's inside

| File (`data/`) | Rows | What it is |
|---|---|---|
| `universities.csv` | 2392 | Every European university (name, country, domain, website) + THE world rank & overall score where matched |
| `tuition_by_country.csv` | 45 | Tuition framework per country: bachelor/master × EU/non-EU, basis, official student budget, notes, sources |
| `tuition_exceptions.csv` | 29 | Institution-specific tuition where it differs from the national rule (with source URL each) |
| `cost_of_living_city.csv` | 23 | Monthly student cost of living per city (rent / other / total), Numbeo + official budget, with access notes |
| `cost_of_living_country.csv` | 26 | Official national student-budget / visa financial-means benchmark per country |
| `scholarships.csv` | 20 | EU-wide (Erasmus+, Erasmus Mundus) + national scholarships, with eligibility and source |
| `faculties.csv` | 120 | Main faculties/fields for 24 reference universities |
| `university_rankings.csv` | 1043 | Times Higher Education 2026 quality indicators for every ranked European university |
| `dataset.json` | - | All of the above in one JSON, plus `meta` |

`raw/` keeps the **original sourced research** (one JSON per dimension) so every figure is traceable. `build_dataset.py` reshapes `raw/` + the upstream base list into `data/`. Re-run with `python3 build_dataset.py`.

## How to join (for the app)

- **University → tuition**: `universities.country_code` → `tuition_by_country.country_code`
- **University → institution-specific tuition**: match `tuition_exceptions.university` to `universities.name` (fall back to the country framework when absent)
- **University → cost of living**: by `city` to `cost_of_living_city`, else by `country_code` to `cost_of_living_country`
- **University → scholarships**: EU-wide rows (`scope = EU-wide`) apply to all; national rows by `country`
- **University → quality**: `universities.the_world_rank` / `the_overall_score` (already joined), or full detail via `university_rankings.matched_university_id` → `universities.id`

## Important data caveats (read before building UI copy)

- **Tuition granularity.** For most European **public** universities tuition is uniform across faculties and set nationally; only the cases in `tuition_exceptions.csv` (and non-EU / English-taught / medicine programmes) differ. Do not present a per-faculty fee unless it exists in the exceptions table.
- **EU vs non-EU.** "EU" columns mean home/EU/EEA students; "non-EU" means third-country. Post-Brexit, EU students in the UK pay **international** rates.
- **`not found` / `not researched`.** Where no authoritative figure exists, the field says so explicitly. Never render these as `0` or invent a number.
- **Ranking coverage.** Only ~1,043 of the 2,392 universities are ranked by THE; the rest legitimately have no quality score. 474 were auto-matched to the base list by name (Jaccard ≥ 0.6, precision-first); the full 1,043 remain in `university_rankings.csv`.
- **Cost of living** is a point-in-time estimate (Numbeo, accessed June 2026) plus official student-budget benchmarks; treat as indicative, not a guaranteed budget.
- **Currencies.** Non-euro countries show EUR-converted figures with the original currency and conversion noted in `notes` / `access_note`.

## Sources

Every figure is traceable to an official or standard source. See `SOURCES.md` for the full list. Primary sources: national study portals and ministries, EU **Eurydice** national-fee pages, university fee pages, **Numbeo** (cost of living), **Times Higher Education** 2026 (rankings), **Hipolabs** university-domains-list (base institution list, MIT).

## Field definitions

See `SCHEMA.md`.
