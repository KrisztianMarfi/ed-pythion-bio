import json
from datetime import datetime, timezone
from pathlib import Path

from .biology import BIO_SIGNAL_TYPE, species_value


def _short_planet(pc: str) -> str:
    return (
        pc.replace(' body', '')
        .replace('High metal content', 'HMC')
        .replace('Rocky ice', 'RockyIce')
        .replace('Metal rich', 'MetalRich')
        or '?'
    )


def _collect(journal_dir: Path) -> dict:
    """Single chronological pass over all journals since the last Vista sale.

    Mirrors history.compute_unsold_earnings: a SellOrganicData clears the tally,
    and only Analyse scans after the last sale count. Correlates each bio-bearing
    body with its parent star (via the planet's Parents chain) and planet class.
    """
    stars: dict[tuple, dict] = {}      # (sysaddr, bodyid) -> star fields
    planets: dict[tuple, dict] = {}    # (sysaddr, bodyid) -> {pc, parents}
    biosig: dict[tuple, int] = {}      # (sysaddr, bodyid) -> biological signal count
    bodyname: dict[tuple, str] = {}
    sysname: dict[int, str] = {}
    population: dict[int, int] = {}
    first_footfall: set[tuple] = set()
    scans: dict[tuple, set] = {}       # (sysaddr, bodyid) -> {species_loc, ...}
    last_sell: str | None = None

    for jfile in sorted(journal_dir.glob('Journal.*.log')):
        try:
            text = jfile.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for raw in text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                e = json.loads(raw)
            except json.JSONDecodeError:
                continue
            kind = e.get('event', '')

            if kind == 'SellOrganicData':
                last_sell = e.get('timestamp')
                scans.clear()

            elif kind in ('FSDJump', 'Location'):
                sa = e.get('SystemAddress')
                if sa is not None and 'Population' in e:
                    population[sa] = e.get('Population', 0)

            elif kind == 'Scan':
                sa = e.get('SystemAddress')
                bid = e.get('BodyID')
                if sa is None or bid is None:
                    continue
                key = (sa, bid)
                sysname[sa] = e.get('StarSystem', sysname.get(sa, ''))
                if 'StarType' in e:
                    stars[key] = {
                        'type': e['StarType'],
                        'mass': e.get('StellarMass'),
                        'lum': e.get('Luminosity', ''),
                    }
                    bodyname[key] = e.get('BodyName', '')
                elif e.get('PlanetClass'):
                    planets[key] = {'pc': e['PlanetClass'], 'parents': e.get('Parents', [])}
                    bodyname[key] = e.get('BodyName', '')
                    if e.get('Landable') and e.get('WasFootfalled') is False:
                        first_footfall.add(key)

            elif kind == 'SAASignalsFound':
                key = (e.get('SystemAddress'), e.get('BodyID'))
                for sig in e.get('Signals', []):
                    if sig.get('Type') == BIO_SIGNAL_TYPE:
                        biosig[key] = sig.get('Count')

            elif kind == 'ScanOrganic' and e.get('ScanType') == 'Analyse':
                sa = e.get('SystemAddress')
                bid = e.get('Body')  # numeric body id in ScanOrganic events
                if sa is None or bid is None:
                    continue
                sp = e.get('Species_Localised', e.get('Species', ''))
                scans.setdefault((sa, bid), set()).add(sp)

    return {
        'stars': stars, 'planets': planets, 'biosig': biosig, 'bodyname': bodyname,
        'sysname': sysname, 'population': population, 'first_footfall': first_footfall,
        'scans': scans, 'last_sell': last_sell,
    }


def _parent_star(data: dict, sa: int, bid: int) -> dict | None:
    """Resolve a planet's parent star, walking its Parents chain; fall back to the
    primary star (body 0) when the parent is an unscanned binary barycentre."""
    pl = data['planets'].get((sa, bid))
    if pl:
        for entry in pl['parents']:
            if 'Star' in entry:
                st = data['stars'].get((sa, entry['Star']))
                if st:
                    return st
    return data['stars'].get((sa, 0))


def generate_stats(journal_dir: Path) -> str:
    """Build the bio-payout-by-star report for everything scanned since the last sale."""
    data = _collect(journal_dir)
    rows = []
    for (sa, bid), species in data['scans'].items():
        base = sum(species_value(n) or 0 for n in species)
        bonus_ok = (sa, bid) in data['first_footfall'] and data['population'].get(sa, 0) == 0
        st = _parent_star(data, sa, bid)
        pl = data['planets'].get((sa, bid), {})
        rows.append({
            'body': data['bodyname'].get((sa, bid)) or f"{data['sysname'].get(sa, sa)} b{bid}",
            'star': st['type'] if st else '?',
            'mass': st['mass'] if st else None,
            'pc': pl.get('pc', '?'),
            'sig': data['biosig'].get((sa, bid), len(species)),
            'base': base,
            'bonus': base * 5 if bonus_ok else base,
            'ff': bonus_ok,
            'species': sorted(species),
        })
    rows.sort(key=lambda r: r['base'], reverse=True)

    out = []
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    boundary = data['last_sell'] or '(no prior sale found — all history)'
    out.append('Elite Dangerous — exobiology stats by star')
    out.append(f'Generated {now}')
    out.append(f'Scanned since last Vista Genomics sale: {boundary}')
    out.append('')
    out.append(
        f"{'Star':<11}{'Mass(Mo)':<10}{'Planet':<10}{'Bio':<5}{'Payout':>14}  "
        f"{'Body':<28}  Species"
    )
    out.append('-' * 120)
    base_tot = bonus_tot = 0
    for r in rows:
        base_tot += r['base']
        bonus_tot += r['bonus']
        mass = f"{r['mass']:.2f}" if r['mass'] is not None else '?'
        body = f"{r['body']}{' *' if r['ff'] else ''}"
        species = ', '.join(r['species']) or '-'
        out.append(
            f"{r['star']:<11}{mass:<10}{_short_planet(r['pc']):<10}{r['sig']:<5}"
            f"{r['base']:>14,}  {body:<28}  {species}"
        )
    out.append('-' * 120)
    out.append(f"BASE TOTAL:  {base_tot:>14,} Cr across {len(rows)} bodies")
    out.append(f"WITH FIRST-FOOTFALL BONUS (x5 where * applies): {bonus_tot:,} Cr")
    out.append('')

    # Summary by star type
    agg: dict[str, list] = {}
    for r in rows:
        a = agg.setdefault(r['star'], [0, 0])
        a[0] += r['base']
        a[1] += 1
    out.append('Summary by star type (base values)')
    out.append(f"{'Star':<11}{'Bodies':<8}{'Total':>15}{'Avg/body':>14}")
    for star, (p, b) in sorted(agg.items(), key=lambda x: -x[1][0]):
        out.append(f"{star:<11}{b:<8}{p:>15,}{p // b if b else 0:>14,}")
    out.append('')

    # Species tally: how many bodies each species appeared on, and its total value
    counts: dict[str, list] = {}
    for r in rows:
        for name in r['species']:
            c = counts.setdefault(name, [0, 0])
            c[0] += 1
            c[1] += species_value(name) or 0
    out.append('Species tally (count across bodies, base value)')
    for name, (n, value) in sorted(counts.items(), key=lambda x: (-x[1][0], x[0])):
        out.append(f"  {f'{name} ({n})':<40}{value:>14,}")
    out.append('')
    return '\n'.join(out)


def write_stats(journal_dir: Path, out_path: Path) -> None:
    """Write the stats report to out_path; never raises (best-effort side effect)."""
    try:
        out_path.write_text(generate_stats(journal_dir), encoding='utf-8')
    except OSError:
        pass
