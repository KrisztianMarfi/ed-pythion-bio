#!/usr/bin/env python3
"""Report unclaimed first-footfall bio bodies since the last Vista Genomics sale.

Walks the ED journals chronologically and finds every body that, since the last
``SellOrganicData``:
  * I scanned (has biological signals, with planet env data so we can predict),
  * still has the x5 first-footfall bonus available (system population 0, landable,
    ``WasFootfalled`` false), and
  * I never landed on (no Touchdown, no ScanOrganic on it).

Bodies whose *best-case* predicted payout (with the x5 bonus applied) clears a
threshold are emitted as a Reddit-ready table, sorted best-case descending.

Reuses the live app's prediction + value model so numbers match the TUI overview:
  - ``predict.predict_species`` for the candidate species,
  - ``tui._predicted_range`` for the (worst, best) base-payout bounds.
"""

import argparse
import json
import os
from pathlib import Path

from ed_bio_helper.predict import predict_species
from ed_bio_helper.tui import _predicted_range
from ed_bio_helper.biology import BIO_SIGNAL_TYPE, canonical_genus_key

_DEFAULT_JOURNAL_DIR = (
    Path.home()
    / '.steam/steam/steamapps/compatdata/359320/pfx'
    / 'drive_c/users/steamuser/Saved Games'
    / 'Frontier Developments/Elite Dangerous'
)


def _resolve_journal_dir(cli_arg: str | None) -> Path:
    if cli_arg:
        return Path(cli_arg).expanduser()
    env = os.environ.get('ED_JOURNAL_DIR')
    if env:
        return Path(env).expanduser()
    return _DEFAULT_JOURNAL_DIR


def collect(journal_dir: Path, all_history: bool = False) -> dict:
    """One chronological pass over all journals.

    Per-body scan/DSS/footfall data is cleared on every SellOrganicData, so what
    survives to the end is exactly the post-last-sale window (mirrors stats.py /
    history.compute_unsold_earnings). System-level reference data (star types,
    population, names, region) is kept across sales — it stays true regardless.

    With ``all_history=True`` the sale clear is skipped, so every never-landed FF
    body across the whole journal history is kept regardless of sales.
    """
    # Persistent (system-level) reference data
    stars: dict[tuple, tuple] = {}      # (sa, bodyid) -> (star_type, luminosity)
    population: dict[int, int] = {}      # sa -> population
    sysname: dict[int, str] = {}         # sa -> system name
    region: dict[int, int] = {}          # sa -> codex region id
    genus_names: dict[str, str] = {}     # genus key -> localised name (all history)

    # Per-body data, cleared on each sale
    scans: dict[tuple, dict] = {}        # (sa, bid) -> env fields from planet Scan
    biosig: dict[tuple, int] = {}        # (sa, bid) -> biological signal count
    dss_keys: dict[tuple, set] = {}      # (sa, bid) -> {canonical genus key}
    dss_loc: dict[tuple, list] = {}      # (sa, bid) -> [localised genus names]
    landed: set[tuple] = set()           # (sa, bid) I touched down on / sampled
    last_sell: str | None = None

    cur_sa: int | None = None  # system the player is currently in (for CodexEntry)

    def _clear_body_data() -> None:
        scans.clear()
        biosig.clear()
        dss_keys.clear()
        dss_loc.clear()
        landed.clear()

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
                if not all_history:
                    _clear_body_data()

            elif kind in ('FSDJump', 'Location'):
                sa = e.get('SystemAddress')
                cur_sa = sa
                if sa is not None:
                    if 'Population' in e:
                        population[sa] = e.get('Population', 0)
                    if e.get('StarSystem'):
                        sysname[sa] = e['StarSystem']

            elif kind == 'CodexEntry':
                region_raw = e.get('Region', '')
                if (cur_sa is not None and isinstance(region_raw, str)
                        and region_raw.startswith('$Codex_RegionName_')):
                    try:
                        region[cur_sa] = int(region_raw.rstrip(';').split('_')[-1])
                    except ValueError:
                        pass

            elif kind == 'Scan':
                sa = e.get('SystemAddress')
                bid = e.get('BodyID')
                if sa is None or bid is None:
                    continue
                key = (sa, bid)
                if e.get('StarSystem'):
                    sysname[sa] = e['StarSystem']
                star_type = e.get('StarType')
                if star_type is not None:
                    stars[key] = (star_type, e.get('Luminosity', ''))
                    continue
                if not e.get('PlanetClass'):
                    continue
                atmo_comp: dict[str, float] = {}
                for entry in e.get('AtmosphereComposition', []) or []:
                    if isinstance(entry, dict) and 'Name' in entry:
                        atmo_comp[entry['Name']] = entry.get('Percent', 0.0)
                parent_ids: list[int] = []
                for p in e.get('Parents', []) or []:
                    if isinstance(p, dict):
                        for pid in p.values():
                            if isinstance(pid, int):
                                parent_ids.append(pid)
                scans[key] = {
                    'body_name': e.get('BodyName', ''),
                    'planet_class': e.get('PlanetClass', ''),
                    'landable': bool(e.get('Landable')),
                    'was_footfalled': bool(e.get('WasFootfalled', True)),
                    'atmosphere_type': e.get('AtmosphereType', ''),
                    'surface_gravity': e.get('SurfaceGravity'),
                    'surface_temperature': e.get('SurfaceTemperature'),
                    'surface_pressure': e.get('SurfacePressure'),
                    'volcanism': e.get('Volcanism', ''),
                    'atmosphere_composition': atmo_comp,
                    'distance_from_arrival_ls': e.get('DistanceFromArrivalLS'),
                    'parent_body_ids': parent_ids,
                }

            elif kind == 'FSSBodySignals':
                sa, bid = e.get('SystemAddress'), e.get('BodyID')
                if sa is None or bid is None:
                    continue
                for sig in e.get('Signals', []) or []:
                    if sig.get('Type') == BIO_SIGNAL_TYPE:
                        biosig[(sa, bid)] = sig.get('Count', 0)

            elif kind == 'SAASignalsFound':
                sa, bid = e.get('SystemAddress'), e.get('BodyID')
                if sa is None or bid is None:
                    continue
                key = (sa, bid)
                for sig in e.get('Signals', []) or []:
                    if sig.get('Type') == BIO_SIGNAL_TYPE:
                        biosig[key] = sig.get('Count', 0)
                keys, loc = set(), []
                for g in e.get('Genuses', []) or []:
                    if isinstance(g, dict) and 'Genus' in g:
                        gk = canonical_genus_key(g['Genus'])
                        name = g.get('Genus_Localised', g.get('Genus', ''))
                        keys.add(gk)
                        loc.append(name)
                        if name:
                            genus_names[gk] = name  # authoritative game display name
                if keys:
                    dss_keys[key] = keys
                    dss_loc[key] = loc

            elif kind == 'Touchdown':
                sa = e.get('SystemAddress', cur_sa)
                bid = e.get('BodyID')
                if sa is not None and bid is not None:
                    landed.add((sa, bid))

            elif kind == 'ScanOrganic':
                sa = e.get('SystemAddress')
                bid = e.get('Body')  # numeric body id in ScanOrganic events
                if sa is not None and bid is not None:
                    landed.add((sa, bid))

    return {
        'stars': stars, 'population': population, 'sysname': sysname, 'region': region,
        'genus_names': genus_names,
        'scans': scans, 'biosig': biosig, 'dss_keys': dss_keys, 'dss_loc': dss_loc,
        'landed': landed, 'last_sell': last_sell, 'all_history': all_history,
    }


# Genus key -> display fallback when the player never DSS'd that genus (so it has no
# game-supplied localised name). Most species names start with the genus word; the
# few single-organism "genera" don't, so override those.
from ed_bio_helper.predict import _CATALOG  # noqa: E402

_GENUS_FALLBACK = {
    '$Codex_Ent_Ground_Struct_Ice_Name;': 'Crystalline Shards',
    '$Codex_Ent_Cone_Name;': 'Bark Mound',
    '$Codex_Ent_Vents_Name;': 'Sinuous Tubers',
}
for _gk, _sp in _CATALOG.items():
    if _gk not in _GENUS_FALLBACK and _sp:
        _GENUS_FALLBACK.setdefault(_gk, next(iter(_sp.values()))['name'].split()[0])


def _genus_display(gk: str, genus_names: dict[str, str]) -> str:
    return genus_names.get(gk) or _GENUS_FALLBACK.get(gk) or gk


def _system_stars(stars: dict, sa: int) -> dict[int, tuple]:
    """All star (body_id -> (type, lum)) entries for one system."""
    return {bid: v for (s, bid), v in stars.items() if s == sa}


def build_rows(data: dict, threshold: int) -> list[dict]:
    rows = []
    for key, scan in data['scans'].items():
        sa, bid = key
        # Must be a scanned, landable bio body with the FF bonus still available...
        if not scan['landable'] or scan['was_footfalled']:
            continue
        sig = data['biosig'].get(key, 0)
        if not sig:
            continue
        if data['population'].get(sa, 0) != 0:   # x5 FF bonus only when population 0
            continue
        if key in data['landed']:                # never landed
            continue

        candidate_genera = data['dss_keys'].get(key) or None
        sys_stars = _system_stars(data['stars'], sa)
        predictions = predict_species(
            planet_class=scan['planet_class'],
            atmosphere_type=scan['atmosphere_type'],
            surface_gravity=scan['surface_gravity'],
            surface_temperature=scan['surface_temperature'],
            surface_pressure=scan['surface_pressure'],
            volcanism=scan['volcanism'],
            atmosphere_composition=scan['atmosphere_composition'],
            distance_from_arrival_ls=scan['distance_from_arrival_ls'],
            region_id=data['region'].get(sa),
            parent_star_ids=scan['parent_body_ids'],
            system_stars=sys_stars,
            parent_stars=list(sys_stars.values()),
            candidate_genera=candidate_genera,
        )
        if not predictions:
            continue

        worst_base, best_base = _predicted_range(predictions, slots=sig)
        best, worst = best_base * 5, worst_base * 5   # x5 first-footfall bonus
        if best <= threshold:
            continue

        # Genera to show: prefer what the DSS actually reported (confirmed genera);
        # else the predicted set (body was FSS-scanned but never surface-mapped).
        dss = key in data['dss_loc']
        if dss:
            genera = sorted(set(data['dss_loc'][key]))
        else:
            genera = sorted({_genus_display(p['genus_key'], data['genus_names'])
                             for p in predictions})

        sys = data['sysname'].get(sa, str(sa))
        body = scan['body_name'] or f'{sys} {bid}'
        short = body[len(sys):].strip() if body.startswith(sys) else body
        rows.append({
            'sa': sa, 'system': sys, 'body': short or body, 'dss': dss,
            'genera': genera, 'best': best, 'worst': worst, 'signals': sig,
        })
    rows.sort(key=lambda r: r['best'], reverse=True)
    return rows


def _table(rows: list[dict], show_signals: bool = False) -> list[str]:
    if show_signals:
        lines = ['System | Body | Signals | Genera | Best case | Worst case',
                 '---|---|---:|---|---:|---:']
    else:
        lines = ['System | Body | Genera | Best case | Worst case',
                 '---|---|---|---:|---:']
    for r in rows:
        link = f'[{r["system"]}](https://spansh.co.uk/system/{r["sa"]})'
        genera = ', '.join(r['genera'])
        sig = f'{r["signals"]} | ' if show_signals else ''
        lines.append(
            f'{link} | {r["body"]} | {sig}{genera} | '
            f'{r["best"]:,} Cr | {r["worst"]:,} Cr'
        )
    return lines


def render(rows: list[dict], data: dict, threshold: int) -> str:
    confirmed = [r for r in rows if r['dss']]
    predicted = [r for r in rows if not r['dss']]

    out = []
    out.append('# Unclaimed first-footfall bodies')
    out.append('')
    if data['all_history']:
        out.append('Across all journal history (sales ignored).')
    else:
        boundary = data['last_sell'] or '(no prior sale — all history)'
        out.append(f'Since last Vista Genomics sale ({boundary}).')
    out.append('')
    out.append(f'*Filter: scanned, never landed, x5 bonus, best case > {threshold:,} Cr. '
               f'{len(rows)} bodies — {len(confirmed)} DSS-confirmed, '
               f'{len(predicted)} FSS-only.*')

    out.append('')
    out.append(f'## DSS-confirmed genera ({len(confirmed)})')
    out.append('')
    out += _table(confirmed)

    out.append('')
    out.append(f'## FSS-only — genera predicted, not surface-mapped ({len(predicted)})')
    out.append('')
    out.append('*Signals = bio-signal count; only that many of the listed genera '
               'actually spawn (best case picks the most valuable, worst the cheapest).*')
    out.append('')
    out += _table(predicted, show_signals=True)
    out.append('')
    return '\n'.join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal-dir', default=None)
    parser.add_argument('--threshold', type=int, default=10_000_000,
                        help='Min best-case payout (Cr) to include. Default 10,000,000.')
    parser.add_argument('--all-history', action='store_true',
                        help='Ignore the last-sale boundary: list every never-landed '
                             'FF body across the whole journal history.')
    args = parser.parse_args()

    journal_dir = _resolve_journal_dir(args.journal_dir)
    data = collect(journal_dir, all_history=args.all_history)
    rows = build_rows(data, args.threshold)
    print(render(rows, data, args.threshold))


if __name__ == '__main__':
    main()
