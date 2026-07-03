import json
import threading
import time
from datetime import datetime
from pathlib import Path

from .biology import BIO_SIGNAL_TYPE, canonical_genus_key, species_value
from .state import AppState


def _latest_journal(directory: Path) -> Path | None:
    files = sorted(directory.glob('Journal.*.log'))
    return files[-1] if files else None


_IN_SRV_FLAG_BIT = 1 << 26  # Status.json Flags bit 26 — currently inside an SRV


def _current_session_files(directory: Path) -> list[Path]:
    """Journal files of the current game session, oldest→newest.

    Each session begins with a `LoadGame` and lives in one file — but a very long
    session can roll over into `part:2…` files with no `LoadGame` at the top. Walk
    back from the newest file, including files until one contains a `LoadGame`, so a
    rolled-over session is reconstructed whole (capped so we never scan forever).
    """
    files = sorted(directory.glob('Journal.*.log'))
    chosen: list[Path] = []
    for f in reversed(files):
        chosen.append(f)
        try:
            if any('"event":"LoadGame"' in line for line in
                   f.open(encoding='utf-8', errors='replace')):
                break
        except OSError:
            break
        if len(chosen) >= 5:
            break
    return list(reversed(chosen))


def _bio_signal_count(event: dict) -> int:
    """Extract the biological signal count from an FSSBodySignals/SAASignalsFound event."""
    for sig in event.get('Signals', []):
        if sig.get('Type', '') == BIO_SIGNAL_TYPE:
            return sig.get('Count', 0)
    return 0


def _note_srv_present(state: AppState, event: dict) -> None:
    """Mark an SRV deployed from an Embark/Disembark that involves one (SRV:True).

    Proves a deployed SRV even when this session has no LaunchSRV (it was deployed in
    a prior session and carried over). Caller already holds the state lock.
    """
    if event.get('SRV') and event.get('ID') is not None:
        state.srv_deployed_ids.add(event['ID'])


def _apply_location(state: AppState, event: dict) -> None:
    """Apply system/body identity from any event that carries it.

    Only overwrites a field when the event actually provides it, so partial events
    (most carry only some of these) never blank out already-known context. Acquires
    the state lock itself (re-entrant), so it's safe to call inside another lock.
    """
    sys_name = event.get('StarSystem')
    sys_addr = event.get('SystemAddress')
    body = event.get('Body')
    body_id = event.get('BodyID')
    with state.lock:
        if sys_name:
            state.system_name = sys_name
        if sys_addr is not None:
            state.system_address = sys_addr
        if body:
            state.body_name = body
        if body_id is not None:
            state.body_id = body_id


def _focus_body_if_exploring(
    state: AppState, sys_addr: int, body_id: int, body_name: str
) -> None:
    """Point the current-body context at a body just FSS/DSS-scanned from the ship.

    When exploring from supercruise (jump, honk, probe) the game emits no
    ApproachBody/SupercruiseExit, and every FSDJump clears the body — so without
    this the prediction panel has no body_key to look up and shows "no scan data"
    even right after a scan. Only applies while off a surface, so it never
    overrides the body you're actually standing on.
    """
    with state.lock:
        if not state.on_surface and state.system_address == sys_addr:
            state.body_id = body_id
            if body_name:
                state.body_name = body_name


def _dispatch(event: dict, state: AppState, bootstrap: bool = False) -> None:
    """Apply a single journal event to app state.

    bootstrap=True skips credit accumulation (used for startup catch-up where past
    Analyse events are already counted in the seeded session/unsold totals).
    """
    kind = event.get('event', '')

    if kind == 'FSDJump':
        with state.lock:
            state.system_name = event.get('StarSystem', state.system_name)
            state.system_address = event.get('SystemAddress', state.system_address)
            state.clear_current_body()
            state.clear_system()
            state.system_population = event.get('Population', 0)
        return

    if kind in ('Location', 'SupercruiseExit'):
        _apply_location(state, event)
        if kind == 'Location':
            with state.lock:
                state.system_population = event.get('Population', state.system_population)

    elif kind == 'ApproachBody':
        _apply_location(state, event)

    elif kind in ('SupercruiseEntry', 'LeaveBody'):
        with state.lock:
            state.clear_current_body()

    elif kind == 'Scan':
        body_id = event.get('BodyID')
        star_type = event.get('StarType')
        if star_type is not None:
            # Star scan — record for parent-star lookups
            luminosity = event.get('Luminosity', '')
            with state.lock:
                if body_id is not None:
                    state.system_stars[body_id] = (star_type, luminosity)
                if not event.get('WasDiscovered', True):
                    state.system_first_discovered = True
        else:
            # Planet/moon scan
            landable = bool(event.get('Landable'))
            detailed = event.get('ScanType') == 'Detailed'
            # Store landable bodies (sampling candidates) always; store non-landable
            # bodies only when the player deliberately FSS-resolved them ('Detailed'),
            # so the panel can explain "not landable" without persisting the passive
            # AutoScan flood from honking past every body.
            if body_id is not None and (landable or detailed):
                sys_addr = event.get('SystemAddress')
                if sys_addr is None:
                    with state.lock:
                        sys_addr = state.system_address
                if sys_addr is not None:
                    bkey = f'{sys_addr}_{body_id}'
                    atmo_comp_raw = event.get('AtmosphereComposition', [])
                    atmo_comp: dict[str, float] = {}
                    if isinstance(atmo_comp_raw, list):
                        for entry in atmo_comp_raw:
                            if isinstance(entry, dict) and 'Name' in entry:
                                atmo_comp[entry['Name']] = entry.get('Percent', 0.0)
                    parents_raw = event.get('Parents', [])
                    parent_ids: list[int] = []
                    for p in parents_raw:
                        if isinstance(p, dict):
                            for pid in p.values():
                                if isinstance(pid, int):
                                    parent_ids.append(pid)
                    scan_data = {
                        'body_name': event.get('BodyName', ''),
                        'planet_class': event.get('PlanetClass', ''),
                        'landable': landable,
                        'atmosphere_type': event.get('AtmosphereType', ''),
                        'surface_gravity': event.get('SurfaceGravity'),
                        'surface_temperature': event.get('SurfaceTemperature'),
                        'surface_pressure': event.get('SurfacePressure'),
                        'volcanism': event.get('Volcanism', ''),
                        'atmosphere_composition': atmo_comp,
                        'distance_from_arrival_ls': event.get('DistanceFromArrivalLS'),
                        'parent_body_ids': parent_ids,
                        # Store first-footfall status directly — persists across sessions
                        # and avoids the body_id timing problem (FSS fires before ApproachBody)
                        'first_footfall': not event.get('WasFootfalled', True),
                    }
                    state.store_body_scan(bkey, scan_data)
                    # A 'Detailed' scan is the player deliberately resolving a body in
                    # the FSS — follow it so the panel reflects what they're looking at.
                    if detailed:
                        _focus_body_if_exploring(
                            state, sys_addr, body_id, event.get('BodyName', '')
                        )

    elif kind == 'FSSBodySignals':
        body_id = event.get('BodyID')
        sys_addr = event.get('SystemAddress')
        if body_id is not None and sys_addr is not None:
            bio_count = _bio_signal_count(event)
            bkey = f'{sys_addr}_{body_id}'
            body_name = event.get('BodyName', '')
            state.store_body_scan(bkey, {'bio_signals': bio_count, 'body_name': body_name})
            _focus_body_if_exploring(state, sys_addr, body_id, body_name)

    elif kind == 'SAASignalsFound':
        body_id = event.get('BodyID')
        sys_addr = event.get('SystemAddress')
        if body_id is not None and sys_addr is not None:
            bio_count = _bio_signal_count(event)
            genera_raw = event.get('Genuses', [])
            candidate_genera: set[str] = {
                canonical_genus_key(g['Genus'])
                for g in genera_raw if isinstance(g, dict) and 'Genus' in g
            }
            candidate_genera_loc: list[str] = [
                g.get('Genus_Localised', g.get('Genus', ''))
                for g in genera_raw if isinstance(g, dict) and 'Genus' in g
            ]
            bkey = f'{sys_addr}_{body_id}'
            body_name = event.get('BodyName', '')
            data: dict = {'bio_signals': bio_count, 'body_name': body_name}
            if candidate_genera:
                data['candidate_genera'] = candidate_genera
                data['candidate_genera_loc'] = candidate_genera_loc
            state.store_body_scan(bkey, data)
            _focus_body_if_exploring(state, sys_addr, body_id, body_name)

    elif kind == 'Touchdown':
        with state.lock:
            state.on_surface = True
            # A vehicle we're piloting that touches down under our control just flew
            # → it's a lander (behavioral fallback, name-independent).
            if state.current_vehicle_id is not None and event.get('PlayerControlled', True):
                state.mark_flyer(state.current_vehicle_id)
            _apply_location(state, event)
            lat = event.get('Latitude')
            lon = event.get('Longitude')
            if lat is not None:
                state.lat = lat
            if lon is not None:
                state.lon = lon

    elif kind == 'Liftoff':
        # PlayerControlled=False means the ship lifted off without the commander
        # aboard (dismissed while on foot / in the SRV). The player is still on the
        # surface sampling, so don't clear surface state or the active scan.
        if not event.get('PlayerControlled', True):
            return
        # Keep the active scan/tracking species across a ship liftoff — the player
        # often hops to a new patch and lands again to keep sampling the same genus.
        # Only actually leaving the body (LeaveBody / SupercruiseEntry, which clear
        # the current body via clear_current_body) resets the tracked species.
        with state.lock:
            # Two very different liftoffs share this event: the mothership taking off,
            # or a flying lander (Nomad) hopping to the next patch with us aboard it.
            # current_vehicle_id tells them apart.
            flying_lander = state.current_vehicle_id is not None
            if flying_lander:
                # We're still in the lander — it just proved it flies. Keep our
                # in-vehicle pose and its deployment; don't clear surface tracking.
                state.mark_flyer(state.current_vehicle_id)
            else:
                state.on_foot = False
                state.on_surface = False
                state.in_srv = False
            _apply_location(state, event)
            # Warn only about vehicles left behind: everything deployed except the one
            # we're piloting. Flying the Nomad off from a parked Scarab warns; lifting
            # the lone Nomad we're flying does not. (Skip during bootstrap replay.)
            stranded = state.srv_deployed_ids - {state.current_vehicle_id}
            if not bootstrap and stranded:
                state.srv_liftoff_warn_pending = True

    elif kind == 'Disembark':
        with state.lock:
            state.on_foot = True
            state.on_surface = True
            state.in_srv = False
            # Standing on the planet, no longer piloting anything — the vehicle we got
            # out of is now strandable.
            state.current_vehicle_id = None
            _apply_location(state, event)
            # Getting out onto the planet from an SRV proves that SRV is deployed —
            # catches an SRV carried over from a prior session (no LaunchSRV this run).
            _note_srv_present(state, event)

    elif kind == 'Embark':
        with state.lock:
            state.on_foot = False
            if event.get('SRV', False):
                state.in_srv = True
                # Boarding a lander/SRV — we're now piloting it (its type/lander-ness
                # was learned earlier from LaunchSRV/RestockVehicle/DockSRV by id).
                state.current_vehicle_id = event.get('ID')
            else:
                state.in_srv = False
                state.on_surface = False
                state.current_vehicle_id = None  # boarded the mothership
            _apply_location(state, event)
            # Boarding the SRV likewise proves it's deployed (carried-over case).
            _note_srv_present(state, event)

    elif kind == 'CodexEntry':
        # Parse region ID from e.g. "$Codex_RegionName_18;" → 18
        region_raw = event.get('Region', '')
        if isinstance(region_raw, str) and region_raw.startswith('$Codex_RegionName_'):
            try:
                region_id = int(region_raw.rstrip(';').split('_')[-1])
                with state.lock:
                    state.region_id = region_id
            except ValueError:
                pass

        # A biological codex entry (e.g. from an SRV/ship scan) confirms a species is
        # present on the body, even before on-foot sampling. Strip the variant suffix
        # ("Concha Renibus - Mulberry" → "Concha Renibus") and keep only real exobio
        # species — this filters out geological entries (geysers, fumaroles).
        sa = event.get('SystemAddress')
        bid = event.get('BodyID')
        name_loc = event.get('Name_Localised', '')
        if sa is not None and bid is not None and name_loc:
            species_loc = name_loc.split(' - ')[0].strip()
            if species_value(species_loc) is not None:
                state.add_confirmed_species(f'{sa}_{bid}', species_loc)

    elif kind == 'ScanOrganic':
        scan_type = event.get('ScanType', '')
        genus = event.get('Genus', '')
        genus_loc = event.get('Genus_Localised', genus)
        species = event.get('Species', '')
        species_loc = event.get('Species_Localised', species)
        variant_loc = event.get('Variant_Localised', '')

        with state.lock:
            state.current_genus = genus
            state.current_genus_loc = genus_loc
            state.current_species = species
            state.current_species_loc = species_loc
            state.current_variant_loc = variant_loc

            lat = state.lat
            lon = state.lon
            ts = event.get('timestamp', datetime.utcnow().isoformat())

        val = species_value(species_loc) or 0
        with state.lock:
            state.update_progress(
                genus, genus_loc, species, species_loc, variant_loc, scan_type, val,
                count_credits=not bootstrap,
            )
            if scan_type in ('Log', 'Sample') and lat is not None and lon is not None:
                state.record_sample(genus, lat, lon, ts)
            if scan_type == 'Analyse':
                state.clear_current_scan()

        # Confirmed spawn → feed the ruleset calibrator. A sampled species is
        # ground truth; if the predictor missed it, widen the local ruleset to
        # fit (see corrections.py). Idempotent per (body, species), so running on
        # every Log/Sample/Analyse is harmless. Done off the state lock.
        if state.corrections is not None and genus and species:
            with state.lock:
                bkey = state.body_key
                region_id = state.region_id
                sys_stars = dict(state.system_stars)
                body_nm = state.body_name
            scan = state.get_body_scan(bkey)
            # Only diagnose against a full surface scan: a real Detailed scan always
            # carries temperature. Without it we have a partial record (e.g. FSS-only)
            # and a "miss" would be an artifact of missing data, not a real one.
            if (bkey and scan.get('planet_class') and scan.get('landable') is not False
                    and scan.get('surface_temperature') is not None):
                state.corrections.observe(
                    genus, species, bkey, body_nm, ts,
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
                    system_stars=sys_stars,
                    parent_stars=list(sys_stars.values()),
                )

    elif kind == 'SellOrganicData':
        # A sale empties the scanner. Only react live — at startup the seeded
        # unsold total already accounts for past sales.
        if not bootstrap:
            with state.lock:
                state.unsold_credits = 0

    elif kind == 'LaunchSRV':
        # Ground SRVs (Scarab/Scorpion) — and any lander that ever launches this way —
        # self-identify here with SRVType/_Localised. You drive out directly into it.
        srv_id = event.get('ID')
        if srv_id is not None:
            state.register_vehicle(
                srv_id, event.get('SRVType'), event.get('SRVType_Localised'),
            )
            with state.lock:
                state.srv_deployed_ids.add(srv_id)
                state.current_vehicle_id = srv_id
                state.in_srv = True

    elif kind == 'LaunchFighter':
        # The Nomad (and combat SLFs) deploy through the fighter bay. The event has no
        # SRVType, only an id — its lander-ness comes from the id we tagged earlier via
        # RestockVehicle, or from the behavioral fallback once it flies. PlayerControlled
        # is False when an NPC crew flies the ship's fighter (we're still aboard the ship).
        fid = event.get('ID')
        if fid is not None and event.get('PlayerControlled', False):
            with state.lock:
                state.srv_deployed_ids.add(fid)
                state.current_vehicle_id = fid
                state.in_srv = True
                state.lander_ids.add(fid)  # launched from the bay & flown by us

    elif kind in ('DockSRV', 'DockFighter', 'SRVDestroyed', 'FighterDestroyed'):
        srv_id = event.get('ID')
        # DockSRV carries the lander's SRVType/_Localised — learn it (harmless on dock,
        # and a last chance to tag the name if RestockVehicle was missed).
        state.register_vehicle(
            srv_id, event.get('SRVType'), event.get('SRVType_Localised'),
        )
        with state.lock:
            if srv_id is not None:
                state.srv_deployed_ids.discard(srv_id)
                # Docking/destroying resolves any "unknown SRV out" sentinel (-1) too —
                # it was this SRV, we just hadn't seen its LaunchSRV (e.g. logged in in it).
                state.srv_deployed_ids.discard(-1)
                if state.current_vehicle_id in (srv_id, -1):
                    state.current_vehicle_id = None
                    state.in_srv = False
            else:
                # No ID (older logs / safety) — clear all; you can only dock the one you're in.
                state.srv_deployed_ids.clear()
                state.current_vehicle_id = None
                state.in_srv = False

    elif kind == 'RestockVehicle':
        # Fired in the hangar when you prep a vehicle (before LaunchFighter). Carries
        # Type/_Localised, so it's how we learn "id 29 is a Nomad" ahead of launch —
        # letting the chip read "NOMAD OUT" from the moment it's deployed.
        state.register_vehicle(
            event.get('ID'), event.get('Type'), event.get('Type_Localised'),
        )

    elif kind == 'Loadout':
        # Current ship: prefer the commander's custom name, else the localised ship
        # type, else a prettified model id (some ships have no _Localised, e.g. mandalay).
        name = (
            event.get('ShipName')
            or event.get('Ship_Localised')
            or event.get('Ship', '').replace('_', ' ').title()
        )
        if name:
            with state.lock:
                state.ship_name = name

    elif kind in ('LoadGame', 'Shutdown'):
        with state.lock:
            state.clear_current_scan()
            # New game session: nothing is deployed yet (a prior session's SRV is gone),
            # and its per-vehicle tags don't carry over.
            state.srv_deployed_ids = set()
            state.current_vehicle_id = None
            state.in_srv = False
            state.srv_types = {}
            state.srv_localised = {}
            state.lander_ids = set()


# ---------------------------------------------------------------------------
# Startup context bootstrap
# ---------------------------------------------------------------------------

def backfill_footfall(journal_dir: Path, state: AppState) -> None:
    """Recover first-footfall status from *all* past journals, not just this session.

    First-footfall is carried only by the body `Scan` event (`WasFootfalled`), which
    usually fires when the system is FSS-scanned — often a separate session from the
    one where the body is actually landed on. The current-session catch-up
    (`_current_session_files`) therefore misses it, and nothing later re-announces it,
    so a bonus body whose Scan predates this session would never show the ×5.

    Mirror history.py's cross-journal pass: scan every journal for landable planet
    Scans reported as not-yet-footfalled and record `first_footfall=True` on that
    body. We only ever assert True (never False) here — `store_body_scan` keeps it
    sticky, so this can't clobber live data regardless of ordering.
    """
    found: dict[str, str] = {}  # body_key -> body_name
    for jfile in sorted(journal_dir.glob('Journal.*.log')):
        try:
            text = jfile.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for raw in text.splitlines():
            # Cheap pre-filter: skip the json.loads cost on the non-Scan flood.
            if '"event":"Scan"' not in raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if (event.get('event') == 'Scan' and event.get('Landable')
                    and event.get('WasFootfalled') is False):
                sa = event.get('SystemAddress')
                bid = event.get('BodyID')
                if sa is not None and bid is not None:
                    found[f'{sa}_{bid}'] = event.get('BodyName', '')

    # Apply in one locked pass + a single save. store_body_scan persists on every
    # call, which is O(n²) across the thousands of bodies an explorer accumulates;
    # since we only ever assert True here, merge directly and save once. Sticky-True
    # still lives in store_body_scan to protect the live Scan path.
    if not found:
        return
    with state.lock:
        for bkey, body_name in found.items():
            entry = state.body_scans.setdefault(bkey, {})
            entry['first_footfall'] = True
            entry.setdefault('body_name', body_name)
    state.save()


def bootstrap_context(journal_dir: Path, state: AppState) -> None:
    """Read the current journal from the beginning to restore system/body context.

    Runs with bootstrap=True so Analyse events don't add to the credit totals —
    those are already counted in the seeded session/unsold figures.
    """
    backfill_footfall(journal_dir, state)
    for journal in _current_session_files(journal_dir):
        try:
            with journal.open(encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        _dispatch(json.loads(line), state, bootstrap=True)
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass

    # If a scan was in progress when the app last closed, current_genus will be
    # empty (LoadGame/Shutdown clears it). Best-effort restore from an incomplete
    # progress entry for the current body — progress has no timestamp, so if
    # several are unfinished we just take the first.
    with state.lock:
        body_key = state.body_key
        if body_key and not state.current_genus:
            body_prog = state.progress.get(body_key, {})
            for genus_key, entry in body_prog.items():
                if not entry.get('completed', False):
                    state.current_genus = genus_key
                    state.current_genus_loc = entry.get('genus_loc', genus_key)
                    state.current_species = entry.get('species', '')
                    state.current_species_loc = entry.get('species_loc', '')
                    state.current_variant_loc = entry.get('variant_loc', '')
                    break

    # Authoritative cross-check: if Status.json says we're physically in an SRV right
    # now, one is deployed no matter what the replay reconstructed (covers a deploy
    # that predated the replayed window). Use a sentinel id when we don't know it.
    try:
        data = json.loads((journal_dir / 'Status.json').read_text())
        if data.get('Flags', 0) & _IN_SRV_FLAG_BIT:
            with state.lock:
                if not state.srv_deployed_ids:
                    state.srv_deployed_ids.add(-1)
                # We're physically in some SRV/lander; if the replay didn't pin down
                # which, adopt the sentinel as the one we're piloting so it isn't
                # counted as "left behind" (type unknown → treated as a plain SRV).
                if state.current_vehicle_id is None:
                    state.current_vehicle_id = (
                        -1 if -1 in state.srv_deployed_ids
                        else next(iter(state.srv_deployed_ids), None)
                    )
                state.in_srv = True
    except (OSError, json.JSONDecodeError):
        pass


# ---------------------------------------------------------------------------
# Live tailer
# ---------------------------------------------------------------------------

def journal_tailer(journal_dir: Path, state: AppState, stop: threading.Event) -> None:
    """Tail the latest journal file; switch to a newer file when one appears."""
    current_file: Path | None = None
    offset: int = 0

    while not stop.is_set():
        latest = _latest_journal(journal_dir)
        if latest and latest != current_file:
            current_file = latest
            offset = current_file.stat().st_size  # seek to end on startup

        if current_file:
            try:
                size = current_file.stat().st_size
                if size > offset:
                    with current_file.open('rb') as fh:
                        fh.seek(offset)
                        new_data = fh.read(size - offset)
                    offset = size
                    for line in new_data.decode('utf-8', errors='replace').splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            _dispatch(json.loads(line), state)
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass

        stop.wait(1.0)


# ---------------------------------------------------------------------------
# Replay mode
# ---------------------------------------------------------------------------

def replay_journal(path: Path, state: AppState, speed: float = 1.0) -> None:
    """Feed a journal file through the event pipeline as if live."""
    events: list[dict] = []
    with path.open(encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    prev_ts: datetime | None = None
    for event in events:
        ts_str = event.get('timestamp', '')
        try:
            ts = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            ts = None

        if ts and prev_ts and speed > 0:
            delta = (ts - prev_ts).total_seconds()
            if delta > 0:
                # Cap at 3 s real time per gap so huge in-game pauses don't stall replay.
                time.sleep(min(delta / speed, 3.0))
        prev_ts = ts

        _dispatch(event, state)
