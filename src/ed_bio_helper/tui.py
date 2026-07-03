import math
import os
from collections import Counter

from rich.cells import cell_len
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .biology import (
    canonical_genus_key,
    genus_min_distance,
    genus_terrain_hint,
    species_value,
    SPECIES_VALUE,
)

# Top-N species by base payout — drives the rare-candidate highlight in the
# system overview so the player can see at a glance which body might host one.
_TOP_PAYOUT_SPECIES: frozenset[str] = frozenset(
    name for name, _ in sorted(SPECIES_VALUE.items(), key=lambda kv: -kv[1])[:5]
)
from .geo import bearing, cardinal, haversine
from .predict import SPECIES_TO_GENUS, predict_species, temperature_band
from .state import AppState


def _fmt_credits(n: int) -> str:
    return f'{n:,} cr'


def _temp_style(local_t: float, ranges: list[tuple[float | None, float | None]]) -> str:
    """Style for the temperature square: green inside a window, red above every
    window (too hot), blue below every window (too cold), yellow in a gap between
    disjoint windows."""
    def lo(r):
        return r[0] if r[0] is not None else float('-inf')

    def hi(r):
        return r[1] if r[1] is not None else float('inf')

    if any(lo(r) <= local_t <= hi(r) for r in ranges):
        return 'bold green'
    if local_t > max(hi(r) for r in ranges):
        return 'bold red'
    if local_t < min(lo(r) for r in ranges):
        return 'bold blue'
    return 'bold yellow'


def _predicted_range(
    predictions: list[dict],
    slots: int | None = None,
    known_values: dict[str, int] | None = None,
) -> tuple[int, int]:
    """(worst_case, best_case) base payout across a body's predictions.

    Two levels of uncertainty to bound:
      1. Within a genus, multiple candidate species (e.g. Bacterium with 3
         options) fill a single slot — only one of A/B/C spawns. Best case is
         the most valuable candidate, worst case the cheapest.
      2. Across genera, the body only has `slots` biological signals, but the
         predictor may name candidate genera for *more* genera than will spawn
         (e.g. "Bacterium or Stratum" for a single-signal body). Best case is
         the `slots` most valuable genera; worst case the `slots` cheapest.

    `slots` is the body's bio-signal count. When None (unknown), every predicted
    genus is assumed to spawn.

    `known_values` maps genus_key → the confirmed base value for genera whose
    exact species is already known (sampled on foot or confirmed via codex). For
    such a genus there is no within-genus uncertainty left, so it contributes the
    same value to *both* bounds and always occupies a slot. Once every slot is a
    known genus the two bounds collapse to a single figure — the real payout.
    """
    known_values = known_values or {}
    by_genus_max: dict[str, int] = {}
    by_genus_min: dict[str, int] = {}
    for p in predictions:
        gk, v = p['genus_key'], p['value']
        by_genus_max[gk] = max(by_genus_max.get(gk, v), v)
        by_genus_min[gk] = min(by_genus_min.get(gk, v), v)

    # Known genera are definitely present and pin to a single value, so they take
    # slots unconditionally; only the remaining slots carry prediction spread.
    known_sum = sum(known_values.values())
    unknown_max = sorted(
        (v for gk, v in by_genus_max.items() if gk not in known_values), reverse=True)
    unknown_min = sorted(
        v for gk, v in by_genus_min.items() if gk not in known_values)
    if slots is not None:
        remaining = max(0, slots - len(known_values))
        unknown_max = unknown_max[:remaining]
        unknown_min = unknown_min[:remaining]
    return known_sum + sum(unknown_min), known_sum + sum(unknown_max)


def _predicted_total(predictions: list[dict], slots: int | None = None) -> int:
    """Best-case base payout — see :func:`_predicted_range`."""
    return _predicted_range(predictions, slots)[1]


def _distance_status(
    state: AppState,
    genus: str,
    lat: float,
    lon: float,
    radius: float,
    min_dist: int,
    in_srv: bool = False,
    on_surface: bool = True,
    in_lander: bool = False,
) -> tuple[str, str]:
    """Return (status_label, style) for current sampling readiness."""
    samples = state.get_samples_for_genus(genus)
    if not samples:
        return 'FIRST', 'cyan'

    nearest = min(
        haversine(lat, lon, s[0], s[1], radius)
        for s in samples
    )

    if nearest >= min_dist:
        return 'READY', 'green'
    else:
        remaining = int(min_dist - nearest)
        # A lander (Nomad) flies like the ship — never walk/drive when piloting one.
        if in_lander:
            verb = 'FLY'
        else:
            verb = 'FLY' if not on_surface else ('DRIVE' if in_srv else 'WALK')
        return f'{verb} {remaining} m more', 'red'


def _append_escape_bearing(
    line: Text,
    lat: float,
    lon: float,
    nearest_pt: tuple[float, float, str],
    heading: float | None,
) -> None:
    """Append a 'walk this way' hint pointing directly away from the nearest sample."""
    escape = (bearing(lat, lon, nearest_pt[0], nearest_pt[1]) + 180) % 360
    line.append('   GO ', style='bold')
    if heading is not None:
        diff = (escape - heading + 540) % 360 - 180
        if abs(diff) <= 12:
            line.append('▲ ', style='bold green')
        elif diff > 0:
            line.append(f'▶ {int(diff)}° ', style='bold yellow')
        else:
            line.append(f'◀ {int(-diff)}° ', style='bold yellow')
    line.append(f'{int(escape):03d}° {cardinal(escape)}', style='bold cyan')


def _get_predictions(state: AppState) -> tuple[list[dict], dict]:
    """Return (predictions, scan) for the current body. predictions=[] if no data."""
    with state.lock:
        body_key = state.body_key
        region_id = state.region_id
        system_stars = dict(state.system_stars)
        scan = state.get_body_scan(body_key)

    planet_class = scan.get('planet_class', '')
    bio_signals = scan.get('bio_signals')
    if not planet_class or bio_signals == 0 or scan.get('landable') is False:
        return [], scan

    parent_ids: list[int] = scan.get('parent_body_ids', [])
    all_stars = list(system_stars.values())

    predictions = predict_species(
        planet_class=planet_class,
        atmosphere_type=scan.get('atmosphere_type', ''),
        surface_gravity=scan.get('surface_gravity'),
        surface_temperature=scan.get('surface_temperature'),
        surface_pressure=scan.get('surface_pressure'),
        volcanism=scan.get('volcanism', ''),
        atmosphere_composition=scan.get('atmosphere_composition'),
        distance_from_arrival_ls=scan.get('distance_from_arrival_ls'),
        region_id=region_id,
        parent_star_ids=parent_ids,
        system_stars=system_stars,
        parent_stars=all_stars,
        candidate_genera=scan.get('candidate_genera'),
    )
    return predictions, scan


def _build_system_overview(state: AppState) -> Panel:
    """Snapshot of every bio-bearing body in the current system.

    Lets the player compare bodies at a glance — predicted genera and bonus payout —
    without flipping focus to each one individually to read the prediction panel.
    """
    with state.lock:
        sys_addr = state.system_address
        system_name = state.system_name
        current_bkey = state.body_key
        region_id = state.region_id
        system_stars = dict(state.system_stars)
        system_population = state.system_population
        scans = {k: dict(v) for k, v in state.body_scans.items()}
        progress = {k: dict(v) for k, v in state.progress.items()}
        confirmed = {k: set(v) for k, v in state.confirmed.items()}

    title = 'System Bio Overview'
    if sys_addr is None:
        return Panel(Text('(no system selected)', style='dim'), title=title, border_style='blue')

    prefix = f'{sys_addr}_'
    all_stars = list(system_stars.values())

    entries: list[dict] = []
    for bkey, scan in scans.items():
        if not bkey.startswith(prefix):
            continue
        bio_signals = scan.get('bio_signals')
        if not bio_signals:
            continue

        landable = scan.get('landable')
        if landable is False:
            predictions: list[dict] = []
            initial = worst = best = 0
            genera_text = Text('(not landable)', style='dim')
        else:
            # Blind prediction — every genus the environment allows, with no DSS
            # narrowing. This feeds the "Initial" column so the player keeps sight
            # of the optimistic pre-DSS figure even after DSS narrows the field.
            predictions = predict_species(
                planet_class=scan.get('planet_class', ''),
                atmosphere_type=scan.get('atmosphere_type', ''),
                surface_gravity=scan.get('surface_gravity'),
                surface_temperature=scan.get('surface_temperature'),
                surface_pressure=scan.get('surface_pressure'),
                volcanism=scan.get('volcanism', ''),
                atmosphere_composition=scan.get('atmosphere_composition'),
                distance_from_arrival_ls=scan.get('distance_from_arrival_ls'),
                region_id=region_id,
                parent_star_ids=scan.get('parent_body_ids', []),
                system_stars=system_stars,
                parent_stars=all_stars,
            )
            # Collapse uncertainty for genera whose exact species we already know:
            # sampled on foot (progress carries the species' base value) or codex-
            # confirmed (SRV/ship scan). These pin to one value so best == worst for
            # them, and once every signal is accounted for the two columns converge.
            known_values: dict[str, int] = {}
            for sp_loc in confirmed.get(bkey, set()):
                v = species_value(sp_loc)
                gk = SPECIES_TO_GENUS.get(sp_loc)
                if v is not None and gk is not None:
                    known_values[gk] = v
            for gk, entry in progress.get(bkey, {}).items():
                cred = entry.get('credits')
                if cred:
                    known_values[canonical_genus_key(gk)] = cred

            dss_genera = set(scan.get('candidate_genera') or [])

            # Initial: the blind best case — preserved as-is, never narrowed by DSS.
            initial = _predicted_range(predictions, slots=bio_signals)[1]

            # Best/Worst: once DSS confirms which genera are actually present, narrow
            # the range to those; collapse any genus whose exact species we now know.
            ranged = (
                [p for p in predictions if p['genus_key'] in dss_genera]
                if dss_genera else predictions
            )
            worst, best = _predicted_range(
                ranged, slots=bio_signals, known_values=known_values)
            if predictions:
                # First word of species name is the genus (Bacterium Aurasus → Bacterium).
                genus_display: dict[str, str] = {}
                genus_order: list[str] = []
                for p in predictions:
                    gk = p['genus_key']
                    if gk not in genus_display:
                        genus_display[gk] = p['name'].split()[0]
                        genus_order.append(gk)
                # Genera fully sampled (3/3) on this body — highlight to show progress.
                completed_genera = {
                    canonical_genus_key(gk)
                    for gk, entry in progress.get(bkey, {}).items()
                    if entry.get('completed')
                }
                # DSS-confirmed genera (computed above): blind candidates that aren't
                # in this set were predicted but ruled out — grey them out so the
                # player can see what the system overpredicted vs what actually spawned.
                # Map genus → first top-5 rare species predicted in it (if any).
                rare_by_genus: dict[str, str] = {}
                for p in predictions:
                    if p['name'] in _TOP_PAYOUT_SPECIES and p['genus_key'] not in rare_by_genus:
                        rare_by_genus[p['genus_key']] = p['name']
                genera_text = Text()
                for i, gk in enumerate(genus_order):
                    if i > 0:
                        genera_text.append(', ', style='dim')
                    if gk in completed_genera:
                        genera_text.append(genus_display[gk], style='bold bright_green')
                    elif dss_genera and gk not in dss_genera:
                        # Predicted but DSS confirmed absent — rule it out visually.
                        genera_text.append(genus_display[gk], style='grey50 strike')
                    elif gk in rare_by_genus:
                        # Replace the genus label with the full "Genus Species" so the
                        # player can tell which rare hit the body might land.
                        genera_text.append(rare_by_genus[gk], style='bold dark_orange')
                    else:
                        genera_text.append(genus_display[gk], style='dim cyan')
            else:
                genera_text = Text('(awaiting body scan)', style='dim')

        body_name = scan.get('body_name', '')
        if body_name and system_name and body_name.startswith(system_name):
            short = body_name[len(system_name):].strip() or body_name
        else:
            short = body_name or bkey.split('_', 1)[1]

        first_ff = scan.get('first_footfall', False)
        is_bonus = first_ff and system_population == 0
        dss_done = bool(scan.get('candidate_genera_loc'))

        # Real earnings tallied from completed (3/3) genus entries on this body.
        # FF bonus is per-genus-entry (set at sample time), so honour each entry's flag.
        earned = 0
        for genus_entry in progress.get(bkey, {}).values():
            if not genus_entry.get('completed'):
                continue
            c = genus_entry.get('credits', 0)
            ff_entry = genus_entry.get('first_footfall') and system_population == 0
            earned += c * 5 if ff_entry else c

        entries.append({
            'bkey': bkey,
            'short': short,
            'planet_class': scan.get('planet_class', '') or '?',
            'landable': landable,
            'bio_signals': bio_signals,
            'genera_text': genera_text,
            'initial_value': initial,
            'best_value': best,
            'worst_value': worst,
            'is_bonus': is_bonus,
            'dss_done': dss_done,
            'earned': earned,
        })

    if not entries:
        return Panel(
            Text('(no bio-bearing bodies scanned in this system)', style='dim'),
            title=title, border_style='blue',
        )

    # Highest blind potential first — the practical "what's worth DSSing" order, and
    # stable regardless of how far DSS/sampling has since narrowed each body.
    entries.sort(key=lambda e: (-e['initial_value'], -e['best_value'], -e['bio_signals'], e['short']))

    table = Table(box=None, padding=(0, 2, 0, 0), show_header=True, expand=False,
                  header_style='bold')
    table.add_column('Body')
    table.add_column('Class')
    table.add_column('Bio', justify='right')
    table.add_column('Genera')
    table.add_column('Initial', justify='right')
    table.add_column('Best case', justify='right')
    table.add_column('Worst case', justify='right')
    table.add_column('Earned', justify='right')

    for e in entries:
        is_current = e['bkey'] == current_bkey
        body_text = Text()
        body_text.append('▸ ' if is_current else '  ', style='bold yellow' if is_current else 'dim')
        body_text.append(e['short'], style='bold yellow' if is_current else 'white')

        if e['landable'] is False:
            class_text = Text(f"{e['planet_class']} (not landable)", style='dim')
        else:
            class_text = Text(e['planet_class'], style='white')

        bio_text = Text(str(e['bio_signals']), style='bold cyan')
        if e['dss_done']:
            bio_text.append(' DSS', style='green')

        mult = 5 if e['is_bonus'] else 1

        def _value_cell(val: int) -> Text:
            if e['landable'] is False or val == 0:
                return Text('—', style='dim')
            cell = Text(_fmt_credits(val * mult), style='bold yellow')
            if e['is_bonus']:
                cell.append(' ×5', style='bold magenta')
            return cell

        initial_text = _value_cell(e['initial_value'])
        best_text = _value_cell(e['best_value'])
        worst_text = _value_cell(e['worst_value'])

        if e['earned'] > 0:
            earned_text = Text(_fmt_credits(e['earned']), style='bold green')
        else:
            earned_text = Text('—', style='dim')

        table.add_row(body_text, class_text, bio_text, e['genera_text'],
                      initial_text, best_text, worst_text, earned_text)

    # Note any locally-learned ruleset widenings so the player knows predictions
    # have been calibrated from their own samples (see corrections.py).
    subtitle = None
    corr = getattr(state, 'corrections', None)
    if corr is not None and corr.applied_count:
        subtitle = f'local ruleset: {corr.applied_count} bound correction(s) applied'

    return Panel(table, title=title, border_style='blue', subtitle=subtitle)


def _build_prediction_panel(
    predictions: list[dict], scan: dict, footfall_bonus: bool = False
) -> Panel:
    if not scan:
        return Panel(
            Text('(no FSS/DSS scan data for this body)', style='dim'),
            title='Predicted Species', border_style='blue',
        )
    if scan.get('landable') is False:
        pc = scan.get('planet_class', '')
        msg = f'(not landable — no surface biology){f"  ·  {pc}" if pc else ""}'
        return Panel(
            Text(msg, style='dim'),
            title='Predicted Species', border_style='blue',
        )
    if scan.get('bio_signals') == 0:
        return Panel(
            Text('(no biological signals detected)', style='dim'),
            title='Predicted Species', border_style='blue',
        )
    if not scan.get('planet_class'):
        return Panel(
            Text('(awaiting body scan)', style='dim'),
            title='Predicted Species', border_style='blue',
        )

    bio_signals = scan.get('bio_signals')
    candidate_genera_loc: list[str] = scan.get('candidate_genera_loc', [])
    lines: list[Text] = []

    if bio_signals is not None:
        count_line = Text()
        count_line.append('Bio signals: ', style='bold')
        count_line.append(str(bio_signals), style='bold cyan')
        count_line.append('   Predicted: ', style='bold')
        predicted_count = len(predictions)
        color = 'green' if bio_signals == predicted_count else 'yellow'
        count_line.append(str(predicted_count), style=f'bold {color}')
        lines.append(count_line)

    if candidate_genera_loc:
        genera_line = Text()
        genera_line.append('Genera (DSS): ', style='bold')
        genera_line.append(', '.join(sorted(candidate_genera_loc)), style='cyan')
        lines.append(genera_line)

    mult = 5 if footfall_bonus else 1
    if footfall_bonus:
        ff_line = Text()
        ff_line.append('First footfall ×5 active', style='bold magenta')
        ff_line.append(' — values shown at bonus rate', style='dim')
        lines.append(ff_line)

    if not predictions:
        lines.append(Text('  (no matches — check region/star data)', style='dim'))
        return Panel(Text('\n').join(lines), title='Predicted Species', border_style='blue')

    # Group visually by genus: same-genus entries are read together.
    predictions = sorted(predictions, key=lambda p: (p['genus_key'], p['name']))

    # Multi-column species table sized to terminal width.
    # Each column: 2-char indent + 32-char name + 14-char value ≈ 48 chars wide.
    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80
    num_cols = max(1, min(3, (term_width - 4) // 48))
    num_rows = math.ceil(len(predictions) / num_cols)

    species_table = Table(box=None, padding=(0, 3, 0, 0), show_header=False, expand=False)
    for _ in range(num_cols):
        species_table.add_column(no_wrap=True)

    for row_idx in range(num_rows):
        cells = []
        for col_idx in range(num_cols):
            item_idx = col_idx * num_rows + row_idx
            if item_idx < len(predictions):
                p = predictions[item_idx]
                cell = Text()
                cell.append(f"  {p['name']}  ", style='white')
                cell.append(_fmt_credits(p['value'] * mult), style='bold yellow')
            else:
                cell = Text('')
            cells.append(cell)
        species_table.add_row(*cells)

    total_min = _predicted_total(predictions, slots=bio_signals)
    total_line = Text()
    total_line.append('Est. payout: ', style='bold')
    if footfall_bonus:
        total_line.append(_fmt_credits(total_min * 5), style='bold yellow')
        total_line.append('  ×5 FF', style='bold magenta')
    else:
        total_line.append(_fmt_credits(total_min), style='bold yellow')
        total_line.append(' — ', style='dim')
        total_line.append(_fmt_credits(total_min * 5), style='bold yellow')
        total_line.append('  (1× — 5×)', style='dim')

    return Panel(
        Group(Text('\n').join(lines), Text(''), species_table, Text(''), total_line),
        title='Predicted Species', border_style='blue',
    )


def build_display(state: AppState) -> Group:
    with state.lock:
        system = state.system_name or '?'
        body = state.body_name or '?'
        on_foot = state.on_foot
        on_surface = state.on_surface
        in_srv = state.in_srv
        ship_name = state.ship_name
        current_vehicle_id = state.current_vehicle_id
        in_lander = current_vehicle_id in state.lander_ids
        current_vehicle_name = state.srv_localised.get(current_vehicle_id) or 'Lander'
        stranded_ids = set(state.srv_deployed_ids) - {current_vehicle_id}
        stranded_label = state.stranded_label()
        body_key = state.body_key
        # first_footfall: body_scans is the authoritative persistent source
        first_footfall = state.body_scans.get(body_key or '', {}).get('first_footfall', False)
        system_first_discovered = state.system_first_discovered
        genus = state.current_genus
        genus_loc = state.current_genus_loc
        species_loc = state.current_species_loc
        variant_loc = state.current_variant_loc
        lat = state.lat
        lon = state.lon
        radius = state.planet_radius
        heading = state.heading
        body_progress = state.get_body_progress()
        confirmed_species = state.get_confirmed_species(body_key)
        genus_known_count = (
            body_progress.get(genus, {}).get('sample_count', 0) if genus else 0
        )
        system_population = state.system_population
        session_credits = state.session_credits
        unsold_credits = state.unsold_credits
        region_id = state.region_id
        system_stars = dict(state.system_stars)

    # First footfall is known from the FSS scan (WasFootfalled) long before the first
    # organic scan, and the x5 bonus applies in unpopulated systems. Treat it as a
    # body-wide flag so every value display reflects the bonus the moment it's confirmed.
    footfall_bonus = first_footfall and system_population == 0

    # --- Header ---
    # Single location indicator: lander name (Nomad) / SRV / on foot / current ship
    # (first footfall is shown per-body elsewhere, so it's dropped from the bar).
    if in_lander:
        location = current_vehicle_name
    elif in_srv:
        location = 'SRV'
    elif on_foot:
        location = 'on foot'
    else:
        location = ship_name or 'ship'
    header = Text.assemble(
        ('System: ', 'bold'),
        (system, 'bold yellow' if system_first_discovered else 'white'),
    )
    if system_first_discovered:
        header.append('*', style='bold yellow')
    header.append_text(Text.assemble(
        ('    Body: ', 'bold'),
        (body, 'white'),
        ('    Location: ', 'bold'),
        (location, 'bold cyan'),
    ))

    # Standing reminder that a vehicle is deployed and strandable — everything out
    # except the one we're piloting (so flying the Nomad off from a parked Scarab
    # still shows "SRV OUT", but the lone Nomad we're flying shows nothing). Label is
    # the lander's name ("NOMAD OUT") or "SRV", or both joined. Shown until re-dock;
    # the audio alarm escalates it at FSD charge. Reserve a stable width when hidden.
    _srv_chip = ' ⚠ SRV OUT '
    header.append('    ')
    if stranded_ids:
        header.append(f' ⚠ {stranded_label} OUT ', style='bold white on red')
    else:
        header.append(' ' * cell_len(_srv_chip))

    # Earnings summary, inline with the rest of the status bar.
    header.append('    ')
    header.append('Session total: ', style='bold')
    header.append(_fmt_credits(session_credits), style='bold yellow')
    header.append('    ')
    header.append('Since last sale: ', style='bold')
    header.append(_fmt_credits(unsold_credits), style='bold yellow')

    # --- Sampling guidance ---
    # Always build as a list and pad to _GUIDANCE_LINES to prevent layout shift.
    _GUIDANCE_LINES = 5  # genus + terrain + min-dist + nearest/status + value
    lines: list[Text] = []

    if not genus and not on_surface:
        lines.append(Text('Land and disembark to begin sampling.', style='dim'))
    elif not genus:
        lines.append(Text('(scan an organism to start tracking)', style='dim'))
    else:
        # A tracked genus stays visible even when off the surface (boarding/lifting
        # off for a ship hop) — only leaving the body clears it. Show a hint that
        # sampling resumes on the ground.
        min_dist = genus_min_distance(genus)
        base_val = species_value(species_loc) if species_loc else None
        is_footfall_bonus = footfall_bonus

        genus_line = Text()
        genus_line.append('Current genus: ', style='bold')
        genus_line.append(genus_loc or genus)
        if not on_surface:
            genus_line.append('  (tracking — land & disembark to resume)', style='dim')
        lines.append(genus_line)

        terrain = genus_terrain_hint(genus)
        if terrain:
            terrain_line = Text()
            terrain_line.append('Terrain:       ', style='bold')
            terrain_line.append(terrain, style='dim cyan')
            lines.append(terrain_line)

        if min_dist is not None:
            dist_line = Text()
            dist_line.append('Min sample distance: ', style='bold')
            dist_line.append(f'{min_dist} m', style='bold white')
            lines.append(dist_line)

            if lat is not None and lon is not None and radius:
                status_label, status_style = _distance_status(
                    state, genus, lat, lon, radius, min_dist,
                    in_srv=in_srv, on_surface=on_surface, in_lander=in_lander,
                )
                samples = state.get_samples_for_genus(genus)
                dist_line2 = Text()
                if samples:
                    nearest = float('inf')
                    nearest_pt: tuple[float, float, str] | None = None
                    for s in samples:
                        d = haversine(lat, lon, s[0], s[1], radius)
                        if d < nearest:
                            nearest, nearest_pt = d, s
                    dist_line2.append('Nearest prior sample: ', style='bold')
                    dist_line2.append(f'{int(nearest)} m', style='bold white')
                    dist_line2.append('   STATUS: ', style='bold')
                    dist_line2.append(status_label, style=f'bold {status_style}')
                    # Not yet clear of the radius — point the way away from it.
                    if nearest < min_dist and nearest_pt is not None:
                        _append_escape_bearing(dist_line2, lat, lon, nearest_pt, heading)
                elif genus_known_count > 0:
                    dist_line2.append('STATUS: ', style='bold')
                    dist_line2.append('READY', style='bold green')
                    dist_line2.append(f'  ({genus_known_count} prior pos. untracked)', style='dim')
                else:
                    dist_line2.append('STATUS: ', style='bold')
                    dist_line2.append(status_label, style=f'bold {status_style}')
                lines.append(dist_line2)
            else:
                lines.append(Text('(position unavailable)', style='dim'))
        else:
            lines.append(Text('(unknown genus distance)', style='dim'))

        val_line = Text()
        val_line.append('Predicted species value: ', style='bold')
        if species_loc:
            val_line.append(species_loc)
            val_line.append('  -  ', style='dim')
            if base_val is not None:
                if is_footfall_bonus:
                    val_line.append(_fmt_credits(base_val * 5), style='bold yellow')
                    val_line.append('  x5 FF', style='bold magenta')
                else:
                    val_line.append(_fmt_credits(base_val), style='bold yellow')
            else:
                val_line.append('? cr', style='dim')
        else:
            val_line.append('(species not yet identified)', style='dim')
        lines.append(val_line)

    while len(lines) < _GUIDANCE_LINES:
        lines.append(Text(''))
    guidance = Text('\n').join(lines)

    # --- Per-body progress ---
    predictions, pred_scan = _get_predictions(state)
    scanned_names = {
        entry.get('species_loc', entry.get('species', ''))
        for entry in body_progress.values()
    }
    # A body yields exactly one species per genus, so once a genus is resolved — by an
    # on-foot sample OR a codex sighting (e.g. SRV scan) — its other predicted
    # candidates can never appear. Drop them rather than leave phantoms to-find.
    resolved_genera = {canonical_genus_key(gk) for gk in body_progress}
    resolved_genera |= {
        p['genus_key'] for p in predictions if p['name'] in confirmed_species
    }
    # Species confirmed via codex but not yet sampled — render as "sighted" (0/3).
    sighted = sorted(
        n for n in confirmed_species if n not in scanned_names
    )
    pred_by_name = {p['name']: p for p in predictions}
    unscanned = [
        p for p in predictions
        if p['name'] not in scanned_names
        and p['name'] not in confirmed_species
        and p['genus_key'] not in resolved_genera
    ]
    # Genera still ambiguous (multiple candidates, none resolved yet): only one will
    # actually be present, so flag them as alternatives instead of separate finds.
    genus_candidate_counts = Counter(p['genus_key'] for p in unscanned)

    # genus_key -> (genus display name, hint)  — deduplicated across all entries
    terrain_seen: dict[str, tuple[str, str]] = {}

    # Species-precise temperature square: each organism only spawns where the body's
    # surface temperature falls inside *that species'* window. Compare against the
    # body average surface temperature (the quantity those windows are derived from) —
    # NOT the Status.json local ambient temperature, which drifts off the body average
    # and isn't a sampling gate, so using it flagged present species as "too hot".
    # ■ green=in window, red=too hot, blue=too cold; grey=no temp/band data (placeholder
    # kept so rows stay aligned and the panel doesn't shift as data arrives).
    _temp_value = pred_scan.get('surface_temperature')
    _temp_ready = _temp_value is not None and bool(pred_scan.get('planet_class'))
    _band_params = dict(
        planet_class=pred_scan.get('planet_class', ''),
        atmosphere_type=pred_scan.get('atmosphere_type', ''),
        surface_gravity=pred_scan.get('surface_gravity'),
        surface_pressure=pred_scan.get('surface_pressure'),
        volcanism=pred_scan.get('volcanism', ''),
        atmosphere_composition=pred_scan.get('atmosphere_composition'),
        distance_from_arrival_ls=pred_scan.get('distance_from_arrival_ls'),
        region_id=region_id,
        parent_star_ids=pred_scan.get('parent_body_ids', []),
        system_stars=system_stars,
        parent_stars=list(system_stars.values()),
    )

    def _add_temp_square(cell: Text, genus_key: str, species_name: str) -> None:
        # Always emit a 2-char square so every row aligns regardless of data; grey
        # is the no-data placeholder that prevents layout shift.
        ranges = (
            temperature_band(genus_key, species_name=species_name, **_band_params)
            if _temp_ready and genus_key else None
        )
        style = _temp_style(_temp_value, ranges) if ranges else 'grey37'
        cell.append('■ ', style=style)

    # Collect (genus_key, species_name, cell) so we can sort by genus before rendering.
    # Each cell is a two-line Text: "Genus Species  x/3" on top, "value  x5 FF" below.
    species_entries: list[tuple[str, str, Text]] = []

    for g_key, entry in body_progress.items():
        sp_loc = entry.get('species_loc', entry.get('species', g_key))
        count = entry.get('sample_count', 0)
        completed = entry.get('completed', False)
        credits  = entry.get('credits', 0)
        first_ff = entry.get('first_footfall', False)
        is_bonus = first_ff and system_population == 0
        payout   = credits * 5 if is_bonus else credits

        cell = Text()
        _add_temp_square(cell, canonical_genus_key(g_key), sp_loc)
        cell.append(sp_loc, style='white')
        cell.append('  ')
        if completed:
            cell.append('3/3 DONE', style='bold green')
        else:
            cell.append(f'{count}/3', style='bold cyan')
        cell.append('\n  ')
        if completed:
            cell.append(f'+{_fmt_credits(payout)}', style='bold yellow')
        else:
            cell.append(_fmt_credits(payout), style='bold yellow')
        if is_bonus:
            cell.append('  x5 FF', style='bold magenta')
        species_entries.append((canonical_genus_key(g_key), sp_loc, cell))
        hint = genus_terrain_hint(g_key)
        if hint and g_key not in terrain_seen:
            terrain_seen[g_key] = (sp_loc.split()[0], hint)

    for name in sighted:
        p = pred_by_name.get(name)
        val = p['value'] if p else (species_value(name) or 0)
        g_key = p['genus_key'] if p else ''
        cell = Text()
        _add_temp_square(cell, g_key, name)
        cell.append(name, style='white')
        cell.append('  ')
        cell.append('0/3 SIGHTED', style='bold cyan')
        cell.append('\n  ')
        cell.append(_fmt_credits(val * 5 if footfall_bonus else val), style='bold yellow')
        if footfall_bonus:
            cell.append('  x5 FF', style='bold magenta')
        species_entries.append((g_key, name, cell))
        hint = genus_terrain_hint(g_key)
        if hint and g_key not in terrain_seen:
            terrain_seen[g_key] = (name.split()[0], hint)

    for p in unscanned:
        cell = Text()
        _add_temp_square(cell, p['genus_key'], p['name'])
        cell.append(p['name'], style='grey50')
        cell.append('  ')
        cell.append('0/3', style='grey50')
        if genus_candidate_counts[p['genus_key']] > 1:
            cell.append(f"  (one of {genus_candidate_counts[p['genus_key']]})", style='dim italic')
        cell.append('\n  ')
        cell.append(_fmt_credits(p['value'] * 5 if footfall_bonus else p['value']), style='grey50')
        if footfall_bonus:
            cell.append('  ×5', style='grey50')
        species_entries.append((p['genus_key'], p['name'], cell))
        hint = genus_terrain_hint(p['genus_key'])
        if hint and p['genus_key'] not in terrain_seen:
            terrain_seen[p['genus_key']] = (p['name'].split()[0], hint)

    species_entries.sort(key=lambda e: (e[0], e[1]))
    species_cells = [c for _, _, c in species_entries]

    # Render species as a multi-column table. Each cell is two lines; bottom cell
    # padding gives the blank-row spacer between items. Pack columns by measuring
    # the actual widest cell line rather than budgeting for worst-case species
    # names — short-named bodies pack tighter and get more columns automatically.
    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80
    if species_cells:
        max_cell_width = max(
            max(len(line) for line in c.plain.split('\n'))
            for c in species_cells
        )
        slot_width = max_cell_width + 3  # +3 for the Table right-padding per column
        body_num_cols = max(1, min(6, (term_width - 4) // slot_width))
    else:
        body_num_cols = 1

    if not species_cells:
        species_block = Text('  (no organisms scanned on this body)', style='dim')
    else:
        body_num_rows = math.ceil(len(species_cells) / body_num_cols)
        species_block = Table(box=None, padding=(0, 3, 1, 0), show_header=False, expand=False)
        for _ in range(body_num_cols):
            species_block.add_column(no_wrap=True)
        for row_idx in range(body_num_rows):
            cells = []
            for col_idx in range(body_num_cols):
                item_idx = col_idx * body_num_rows + row_idx
                if item_idx < len(species_cells):
                    cells.append(species_cells[item_idx])
                else:
                    cells.append(Text(''))
            species_block.add_row(*cells)

    # Trailing block: terrain hints stay full-width below the species table.
    # (Session/unsold totals now live on the header bar.)
    trailing_lines: list[Text] = []
    if terrain_seen:
        trailing_lines.append(Text(''))
        hint_line = Text()
        hint_line.append('Terrain hints: ', style='bold')
        for i, (genus_display, hint) in enumerate(terrain_seen.values()):
            if i > 0:
                hint_line.append(', ', style='dim')
            hint_line.append(genus_display, style='white')
            hint_line.append(' — ', style='dim')
            hint_line.append(hint, style='dark_orange')
        trailing_lines.append(hint_line)

    # Leading blank keeps the species table from butting against the top border.
    body_content = Group(Text(''), species_block, Text('\n').join(trailing_lines))

    # Assemble panels
    return Group(
        Panel(header, title='[bold]ED Bio Helper[/]', border_style='blue'),
        Panel(guidance, title='Sampling', border_style='blue'),
        Panel(body_content, title='This Body', border_style='blue'),
        _build_prediction_panel(predictions, pred_scan, footfall_bonus),
        _build_system_overview(state),
    )
