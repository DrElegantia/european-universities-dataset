# Schema

All amounts in EUR per year unless stated. Some tuition cells are strings (they may carry a range or a qualifier like `not found / see notes`, `uncapped, provider-set`). Numeric where a single clean figure exists.

## universities.csv
| field | type | notes |
|---|---|---|
| id | int | primary key |
| name | str | institution name (from Hipolabs) |
| country | str | English country name |
| country_code | str | ISO 3166-1 alpha-2 (XK = Kosovo) |
| state_province | str | often empty |
| domain | str | primary domain |
| website | str | primary URL |
| the_world_rank | str | THE 2026 world rank if matched (e.g. `1`, `=3`, `601-800`); empty if unranked/unmatched |
| the_overall_score | float | THE 2026 overall score (higher = better); empty if unranked/unmatched |

## tuition_by_country.csv
| field | type | notes |
|---|---|---|
| country, country_code | str | join key to universities |
| currency | str | local currency of the fee system |
| bachelor_eu, master_eu | str | annual tuition for home/EU/EEA students |
| bachelor_noneu, master_noneu | str | annual tuition for third-country students |
| basis | str | flat / income-based / per-credit / free-if-state-funded etc. |
| official_student_budget_eur_month | num | national student-budget or visa means benchmark (may be empty) |
| notes | str | qualifications, exceptions, year |
| sources | str | ` | `-separated source URLs |

## tuition_exceptions.csv
`country, university, field, level, amount_eur_year, note, source_url` — institution-specific tuition that differs from the national framework.

## cost_of_living_city.csv
`city, country, country_code, currency, monthly_rent_eur, monthly_other_eur, monthly_total_eur, official_student_budget_eur_month, source_numbeo_url, source_official_url, access_note`. `rent` = student 1-bed/shared; `other` = food/transport/utilities/personal excl. rent; `total` = rent+other.

## cost_of_living_country.csv
`country, country_code, official_student_budget_eur_month, source_url, note` — official national benchmark per country.

## scholarships.csv
`scope (EU-wide|national), country, name, provider, coverage, eligibility, source_url`.

## faculties.csv
`id, university, city, country, country_code, faculty`.

## university_rankings.csv
`the_name, country, matched_university_id, world_rank, overall_score, teaching, research, citations_or_research_quality, international_outlook, industry_income` — THE 2026; all scores higher = better, range 0-100; `matched_university_id` links to `universities.id` (empty if not matched).
