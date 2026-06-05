# Schema

All tuition/cost amounts in EUR. Numeric columns are blank only when no sourced figure exists (see `data_quality`). Bilingual fields exist for controlled vocabularies and key notes.

## universities.csv
| field | notes |
|---|---|
| id | primary key |
| name, country, country_code | institution + ISO alpha-2 (XK = Kosovo) |
| city | derived from name via GeoNames (blank if unresolved) |
| lat, lon | city-level coordinates (for the map); blank if no city |
| field_category | one of 14 codes in `field_taxonomy.csv` (primary field of the institution) |
| field_category_en, field_category_it | bilingual label |
| domain, website | primary domain / URL |
| the_world_rank | THE 2026 world rank if matched (`1`, `=3`, `601-800`); blank otherwise |
| the_overall_score | THE 2026 overall score (higher = better); blank otherwise |

## tuition_by_country.csv
| field | notes |
|---|---|
| country, country_code, currency | join key + local fee currency |
| fee_type | free / flat / income_based / per_credit / free_or_paid / state_funded_or_paid |
| data_quality | official / official_range / indicative / partial / not_available |
| bachelor_eu_min_eur, bachelor_eu_max_eur | home/EU bachelor annual range (EUR) |
| master_eu_min_eur, master_eu_max_eur | home/EU master |
| bachelor_noneu_min_eur, bachelor_noneu_max_eur | international bachelor |
| master_noneu_min_eur, master_noneu_max_eur | international master |
| official_student_budget_eur_month | national student-budget / visa benchmark |
| notes_it, notes_en | bilingual qualifications |

For non-EU countries the `*_eu_*` columns represent domestic/state-funded study. min = max means a single flat figure.

## tuition_exceptions.csv
`country, university, field, level, amount_eur_year, note, source_url` — institution-specific tuition.

## cost_of_living_city.csv
`city, country, country_code, currency, monthly_rent_eur, monthly_other_eur, monthly_total_eur, official_student_budget_eur_month, source_numbeo_url, source_official_url, access_note`. rent = student 1-bed outside centre; other = single-person costs excl. rent; total = rent + other.

## cost_of_living_country.csv
`country, country_code, official_student_budget_eur_month, source_url, note` — national fallback.

## scholarships.csv
`scope (EU-wide|national), country, name, provider, coverage_en, coverage_it, eligibility_en, eligibility_it, source_url`.

## faculties.csv
`id, university, city, country, country_code, faculty, field_category, field_category_en, field_category_it`.

## field_taxonomy.csv
`code, label_en, label_it` — 14 categories: MED, ENG, ART, BUS, LAW, AGR, ARC, EDU, THEO, ICT, SOC, HUM, SCI, COMP.

## university_rankings.csv
`the_name, country, matched_university_id, world_rank, overall_score, teaching, research, citations_or_research_quality, international_outlook, industry_income` — THE 2026; scores 0-100, higher = better; `matched_university_id` → `universities.id` (blank if unmatched).

## i18n.json
`field_categories`, `fee_type`, `data_quality` (each code → {en, it}) and `ui` (UI strings → {en, it}).
