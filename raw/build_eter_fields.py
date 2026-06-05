#!/usr/bin/env python3
"""Build eter_fields.json from the ETER full dump (Zenodo record 8074821).

A broad ISCED-F field is marked "offered" by an institution if, in ANY available
year and at ANY ISCED level (5, 6, 7, 7-long, combined 5-7), the institution
records students OR graduates > 0 in that field. The special code 's'
(value 1-3 recoded for confidentiality) also counts as >0. Codes 'c'
(confidential, magnitude unknown), 'm', 'a', 'x*', 'nc' do NOT count.

ISCED-F 2013 broad field (FOE code) -> target bucket:
  FOE00 Generic programmes               -> (dropped: not a discipline)
  FOE01 Education                        -> Education
  FOE02 Arts and humanities              -> Humanities&Languages + Arts&Design (split, see note)
  FOE03 Social sciences, journalism/info -> SocialSciences
  FOE04 Business, administration and law -> Business&Economics + Law (split)
  FOE05 Natural sciences, math, stats    -> NaturalSciences&Math
  FOE06 ICT                              -> ComputerScience&IT
  FOE07 Engineering, manuf., construction-> Engineering&Technology + Architecture (split)
  FOE08 Agriculture, forestry, vet       -> Agriculture&Veterinary
  FOE09 Health and welfare               -> Medicine&Health
  FOE10 Services                         -> (no clean target bucket; dropped)

NOTE ON BUCKET GRANULARITY: ETER only provides the 11 ISCED-F *broad* (1-digit)
fields. The requested target taxonomy has 12 buckets that are FINER than ETER in
three places: it separates Humanities&Languages from Arts&Design (both inside
FOE02), Business&Economics from Law (both inside FOE04), and Engineering&Technology
from Architecture (both inside FOE07). ETER's 1-digit data cannot distinguish these.
To avoid fabricating a precision the source does not have, a broad field that maps
to two target buckets is reported by assigning it to the PRIMARY bucket only and
recording the broad field code in `isced_broad` so the ambiguity is transparent.
The split-secondary buckets (Arts&Design, Law, Architecture) are therefore NOT
independently derivable from ETER 1-digit data and are only present where FOE02/
FOE04/FOE07 is, flagged via `ambiguous_buckets`.
"""
import csv, json, sys

SRC = 'ETER_fullDump.csv'
OUT = 'eter_fields.json'

# FOE broad code -> (primary target bucket, [secondary buckets sharing this broad code])
FOE_MAP = {
    '01': ('Education', []),
    '02': ('Humanities&Languages', ['Arts&Design']),
    '03': ('SocialSciences', []),
    '04': ('Business&Economics', ['Law']),
    '05': ('NaturalSciences&Math', []),
    '06': ('ComputerScience&IT', []),
    '07': ('Engineering&Technology', ['Architecture']),
    '08': ('Agriculture&Veterinary', []),
    '09': ('Medicine&Health', []),
    # FOE00 (generic) and FOE10 (services) intentionally omitted: no clean bucket.
}

# ISCED levels whose FOE breakdowns we scan (students + graduates).
LEVELS = ['ISCED5', 'ISCED6', 'ISCED7', 'ISCED7LONG', 'ISCED5_7']
PREFIXES = ['STUD.', 'GRAD.']  # RES. (ISCED8/PhD) handled separately below


def is_positive(v):
    if v is None:
        return False
    v = v.strip()
    if v == '':
        return False
    if v == 's':  # 1-3, recoded -> genuinely > 0
        return True
    try:
        return float(v.replace(',', '.')) > 0
    except ValueError:
        return False  # m, a, x, xc, xr, nc, c -> not counted


def main():
    f = open(SRC, encoding='utf-8-sig')
    r = csv.reader(f, delimiter=';')
    hdr = next(r)
    idx = {h: i for i, h in enumerate(hdr)}

    # Pre-resolve column indices for every (prefix, level, foe) we care about.
    cols = []  # (foe_code, col_index)
    for prefix in PREFIXES:
        for lvl in LEVELS:
            for foe in FOE_MAP:
                name = f'{prefix}{lvl}FOE{foe}'
                if name in idx:
                    cols.append((foe, idx[name]))
    # PhD (ISCED8) students/graduates by field, under RES.
    for sub in ['STUDISCED8', 'GRADISCED8']:
        for foe in FOE_MAP:
            name = f'RES.{sub}FOE{foe}'
            if name in idx:
                cols.append((foe, idx[name]))

    i_eter = idx['BAS.ETERID']
    i_name = idx['BAS.INSTNAME']
    i_nameen = idx['BAS.INSTNAMEENGL']
    i_country = idx['BAS.COUNTRY']
    i_city = idx['GEO.CITY']
    i_year = idx['BAS.REFYEAR']

    inst = {}  # eterid -> dict
    for row in r:
        eid = row[i_eter].strip()
        if not eid:
            continue
        rec = inst.get(eid)
        if rec is None:
            rec = {
                'eter_id': eid,
                'name': '', 'name_en': '', 'country': '', 'city': '',
                'best_year': -1,
                'foe': set(),
            }
            inst[eid] = rec
        try:
            yr = int(row[i_year])
        except (ValueError, IndexError):
            yr = -1
        # Keep identity fields from the most recent year that has a non-empty name.
        nm = row[i_name].strip() if i_name < len(row) else ''
        if yr >= rec['best_year'] and nm:
            rec['best_year'] = yr
            rec['name'] = nm
            ne = row[i_nameen].strip() if i_nameen < len(row) else ''
            rec['name_en'] = ne
            ct = row[i_country].strip() if i_country < len(row) else ''
            rec['country'] = ct
            cy = row[i_city].strip() if i_city < len(row) else ''
            rec['city'] = cy
        # Accumulate FOE presence across ALL years.
        for foe, ci in cols:
            if ci < len(row) and is_positive(row[ci]):
                rec['foe'].add(foe)

    out = []
    for eid, rec in inst.items():
        buckets = []
        ambiguous = []
        isced_broad = []
        for foe in sorted(rec['foe']):
            primary, secondary = FOE_MAP[foe]
            if primary not in buckets:
                buckets.append(primary)
            isced_broad.append('FOE' + foe)
            for s in secondary:
                if s not in ambiguous:
                    ambiguous.append(s)
        if not buckets:
            continue  # no field data at all -> skip (avoids empty fabricated entries)
        out.append({
            'eter_id': eid,
            'institution_name': rec['name_en'] or rec['name'],
            'institution_name_local': rec['name'],
            'country_code': rec['country'],
            'city': rec['city'],
            'data_year': rec['best_year'] if rec['best_year'] > 0 else None,
            'fields': buckets,
            'isced_broad': isced_broad,
            'ambiguous_buckets': ambiguous,
        })

    out.sort(key=lambda d: (d['country_code'], d['institution_name']))
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('total institutions in dump:', len(inst))
    print('institutions with >=1 field:', len(out))
    print('written to', OUT)


if __name__ == '__main__':
    main()
