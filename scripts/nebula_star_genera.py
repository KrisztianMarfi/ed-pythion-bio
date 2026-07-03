#!/usr/bin/env python3
"""Reference list: organisms gated on a nebula, and organisms gated on star type.

Catalog-derived (not journal-derived): walks predict._CATALOG and pulls out every
species whose spawn ruleset depends on a ``nebula`` condition or a ``star`` /
``parent_star`` condition. These are the "go to a nebula" / "find this star type"
targets that the normal body-scan prediction can't fully confirm on its own.
"""

from ed_bio_helper.predict import _CATALOG


def _fmt_star(v) -> str:
    """Render a star ruleset value: 'A', a list of types, or (type, luminosity) tuples."""
    if isinstance(v, str):
        return v
    parts = []
    for e in v:
        if isinstance(e, (tuple, list)) and len(e) == 2:
            parts.append(f'{e[0]}{e[1]}')   # e.g. ('B','IV') -> 'BIV'
        else:
            parts.append(str(e))
    return ', '.join(parts)


def nebula_rows() -> list[dict]:
    rows = []
    for genus in _CATALOG.values():
        for sp in genus.values():
            scopes = {rs['nebula'] for rs in sp['rulesets'] if 'nebula' in rs}
            if scopes:
                conds = []
                for rs in sp['rulesets']:
                    if 'nebula' not in rs:
                        continue
                    bt = rs.get('body_type')
                    atm = rs.get('atmosphere')
                    if bt:
                        conds.append('/'.join(bt))
                    if atm:
                        conds.append('/'.join(atm) + ' atm')
                    if 'volcanism' in rs:
                        conds.append('volcanism')
                rows.append({
                    'name': sp['name'], 'value': sp['value'],
                    'scope': ', '.join(sorted(scopes)),
                    'cond': '; '.join(dict.fromkeys(conds)) or '-',
                })
    return sorted(rows, key=lambda r: -r['value'])


def star_rows() -> list[dict]:
    rows = []
    for genus in _CATALOG.values():
        for sp in genus.values():
            reqs, kinds = set(), set()
            for rs in sp['rulesets']:
                if 'star' in rs:
                    reqs.add(_fmt_star(rs['star'])); kinds.add('arrival/any')
                if 'parent_star' in rs:
                    reqs.add(_fmt_star(rs['parent_star'])); kinds.add('parent')
            if reqs:
                rows.append({
                    'name': sp['name'], 'value': sp['value'],
                    'stars': ' | '.join(sorted(reqs)),
                    'kind': ', '.join(sorted(kinds)),
                })
    return sorted(rows, key=lambda r: -r['value'])


def render() -> str:
    out = []
    out.append('# Nebula- and star-gated organisms')
    out.append('')

    out.append('## Gated on a NEBULA')
    out.append('')
    out.append('*Must be at/near a nebula to spawn.*')
    out.append('')
    out.append('Species | Value | Nebula | Body conditions')
    out.append('---|---:|---|---')
    for r in nebula_rows():
        out.append(f"{r['name']} | {r['value']:,} Cr | {r['scope']} | {r['cond']}")

    out.append('')
    out.append('## Gated on STAR TYPE')
    out.append('')
    out.append('*Codes: O B A F G K M (hot→cool main sequence), MS/S (S-type), '
               'AeBe (Herbig Ae/Be protostar), C (carbon); a trailing roman numeral '
               'is the luminosity class (e.g. BIV = B-type, class IV). '
               '"parent" = the body\'s parent star; "arrival/any" = a star in the system.*')
    out.append('')
    out.append('Species | Value | Star type(s) | Match')
    out.append('---|---:|---|---')
    for r in star_rows():
        out.append(f"{r['name']} | {r['value']:,} Cr | {r['stars']} | {r['kind']}")
    out.append('')
    return '\n'.join(out)


if __name__ == '__main__':
    print(render())
