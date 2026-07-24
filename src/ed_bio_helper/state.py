import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .biology import is_lander_type


def _state_path() -> Path:
    xdg = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))
    p = Path(xdg) / 'ed-bio-helper' / 'state.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


class AppState:
    """All mutable runtime state, shared across threads via a single lock."""

    def __init__(self) -> None:
        self.lock = threading.RLock()

        # Optional ruleset-calibration tracker (corrections.Corrections), wired in
        # by the entry point. None in contexts that don't use it (e.g. some tests).
        self.corrections: Any = None

        # Current location context
        self.system_name: str = ''
        self.system_address: int | None = None
        self.body_name: str = ''
        self.body_id: int | None = None

        # Current ship display name (from Loadout: custom name, else ship type)
        self.ship_name: str = ''

        # On-foot status (from Status.json Flags2 bit 0)
        self.on_foot: bool = False
        # True when on foot OR in SRV — keeps guidance panel active while driving
        self.on_surface: bool = False
        self.in_srv: bool = False

        # SRV deployment: set of vehicle IDs currently out (from LaunchSRV,
        # LaunchFighter, and Embark/Disembark SRV:true). Cleared on dock/destroy and
        # on session/body change. Rebuilt from the journal at startup, not persisted —
        # the journal is the source of truth each launch. Drives the "…OUT" header
        # chip and the leave-it-behind alarm.
        self.srv_deployed_ids: set[int] = set()
        # The deployed vehicle we're currently piloting (a Nomad/SRV id), or None when
        # on foot or aboard the mothership. The pivot of the "what gets left behind"
        # math: stranded = srv_deployed_ids - {current_vehicle_id}. Not persisted.
        self.current_vehicle_id: int | None = None
        # Per-vehicle metadata learned from the journal (session-scoped, rebuilt like
        # srv_deployed_ids): id -> SRVType string, id -> localised name, and the ids
        # known to be flying "landers" (Nomad-class) — by type name (is_lander_type)
        # or by having been observed to fly. Drive the chip label and the FLY override.
        self.srv_types: dict[int, str] = {}
        self.srv_localised: dict[int, str] = {}
        self.lander_ids: set[int] = set()
        # FSD spool-up in progress (Status.json Flags bit 17) — the strand danger point.
        self.fsd_charging: bool = False
        # One-shot flag: a player-controlled Liftoff happened with an SRV still out.
        # Set by the journal, consumed by the live loop to play a gentle heads-up.
        self.srv_liftoff_warn_pending: bool = False

        # Player position (from Status.json, updated ~4 Hz)
        self.lat: float | None = None
        self.lon: float | None = None
        self.planet_radius: float | None = None
        self.heading: float | None = None  # degrees 0-359, -1 when stationary/airless
        self.local_temperature: float | None = None  # K at player's location (Odyssey surface)

        # Active scan (set on ScanOrganic Log/Sample, cleared on body change)
        self.current_genus: str = ''           # canonical codex key
        self.current_genus_loc: str = ''       # localised display name
        self.current_species: str = ''         # canonical codex key
        self.current_species_loc: str = ''     # localised display name
        self.current_variant_loc: str = ''     # localised variant display name

        # Per-body sample locations: {body_key: {genus_codex: [(lat, lon, ts), ...]}}
        self.samples: dict[str, dict[str, list[tuple[float, float, str]]]] = {}

        # Per-body scan progress: {body_key: {genus_codex: ProgressEntry}}
        self.progress: dict[str, dict[str, dict[str, Any]]] = {}

        # System/region context (cleared on FSDJump)
        self.system_stars: dict[int, tuple[str, str]] = {}  # {body_id: (star_type, luminosity)}
        self.region_id: int | None = None  # Codex region ID, from CodexEntry.Region
        self.system_first_discovered: bool = False  # primary star WasDiscovered=false
        self.system_population: int = 0  # populated systems give no x5 bonus

        # Per-body scan data from FSS/DSS events: {body_key: {field: value}}
        self.body_scans: dict[str, dict] = {}

        # Per-body species confirmed via biological CodexEntry (e.g. SRV/ship scan)
        # but not necessarily sampled on foot: {body_key: {species_loc, ...}}
        self.confirmed: dict[str, set[str]] = {}

        # Session totals (not persisted, reset on app start)
        self.session_credits: int = 0
        self.session_log: list[tuple[str, int, bool]] = []  # [(species_loc, credits, is_bonus)]
        # Estimated unsold bio data carried since the last Vista Genomics sale. Seeded
        # from journal history at startup, then grows on each Analyse and resets on a sale.
        self.unsold_credits: int = 0

        # When True, save() is a no-op. Used to batch a burst of mutations (notably
        # the startup journal replay in bootstrap_context, which fires hundreds of
        # setters) into a single write instead of rewriting the whole state file on
        # every event — the latter is O(events × state-size) and dominates startup
        # once state.json grows large.
        self._save_suspended: bool = False

        self._state_file = _state_path()
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        try:
            data = json.loads(self._state_file.read_text())
            self.samples = data.get('samples', {})
            self.progress = data.get('progress', {})
            self.body_scans = data.get('body_scans', {})
            self.confirmed = {k: set(v) for k, v in data.get('confirmed', {}).items()}
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        if self._save_suspended:
            return
        with self.lock:
            data = {
                'samples': self.samples,
                'progress': self.progress,
                'body_scans': self.body_scans,
                'confirmed': {k: sorted(v) for k, v in self.confirmed.items()},
            }
        try:
            self._state_file.write_text(json.dumps(data, indent=2))
        except OSError:
            pass

    @contextmanager
    def batched_save(self):
        """Suspend per-setter saves for the duration, then persist once on exit.

        For bursts of mutations (e.g. the startup journal replay) this turns hundreds
        of full-file rewrites into a single one. Reentrant-safe: a nested use won't
        prematurely re-enable saving.
        """
        already = self._save_suspended
        self._save_suspended = True
        try:
            yield
        finally:
            if not already:
                self._save_suspended = False
                self.save()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def body_key(self) -> str | None:
        if self.system_address is not None and self.body_id is not None:
            return f'{self.system_address}_{self.body_id}'
        return None

    def record_sample(self, genus: str, lat: float, lon: float, ts: str) -> None:
        """Record a sample position for the given genus on the current body."""
        key = self.body_key
        if key is None:
            return
        self.samples.setdefault(key, {}).setdefault(genus, []).append((lat, lon, ts))
        self.save()

    def update_progress(
        self,
        genus: str,
        genus_loc: str,
        species: str,
        species_loc: str,
        variant_loc: str,
        scan_type: str,
        credits: int,
        count_credits: bool = True,
    ) -> None:
        """Update scan progress for genus on current body based on ScanType."""
        key = self.body_key
        if key is None:
            return
        entry = self.progress.setdefault(key, {}).setdefault(genus, {
            'genus_loc': genus_loc,
            'species': species,
            'species_loc': species_loc,
            'variant_loc': variant_loc,
            'sample_count': 0,
            'completed': False,
            'credits': credits,
            'first_footfall': False,
        })
        if scan_type == 'Log':
            entry['sample_count'] = 1
        elif scan_type == 'Sample':
            entry['sample_count'] = 2
        elif scan_type == 'Analyse':
            entry['sample_count'] = 3
            entry['completed'] = True
            if count_credits:
                is_bonus = entry.get('first_footfall') and not self.system_population
                val = credits * 5 if is_bonus else credits
                self.session_credits += val
                self.unsold_credits += val
                self.session_log.append((species_loc, val, bool(is_bonus)))
        entry['genus_loc'] = genus_loc
        entry['species'] = species
        entry['species_loc'] = species_loc
        entry['variant_loc'] = variant_loc
        entry['credits'] = credits
        # First-footfall comes from the persisted body_scans value (set from the
        # body Scan's WasFootfalled flag, recovered across sessions by backfill).
        if self.body_scans.get(key, {}).get('first_footfall', False):
            entry['first_footfall'] = True
        self.save()

    def get_progress(self, genus: str) -> dict[str, Any] | None:
        key = self.body_key
        if key is None:
            return None
        return self.progress.get(key, {}).get(genus)

    def get_body_progress(self) -> dict[str, dict[str, Any]]:
        # Shallow copy under the lock: callers (build_display) iterate this off-lock
        # while the tailer thread may add genus keys, which would otherwise raise
        # "dictionary changed size during iteration".
        with self.lock:
            key = self.body_key
            if key is None:
                return {}
            return dict(self.progress.get(key, {}))

    def get_samples_for_genus(self, genus: str) -> list[tuple[float, float, str]]:
        with self.lock:
            key = self.body_key
            if key is None:
                return []
            return list(self.samples.get(key, {}).get(genus, []))

    def clear_current_scan(self) -> None:
        """Reset the actively tracked organism (genus/species/variant)."""
        with self.lock:
            self.current_genus = ''
            self.current_genus_loc = ''
            self.current_species = ''
            self.current_species_loc = ''
            self.current_variant_loc = ''

    def clear_current_body(self) -> None:
        with self.lock:
            self.body_name = ''
            self.body_id = None
            self.clear_current_scan()
            self.lat = None
            self.lon = None
            self.planet_radius = None
            self.local_temperature = None
            self.on_surface = False
            self.in_srv = False
            # Leaving the body abandons any deployed vehicle and ends our piloting of
            # it. But what each id *is* (its type/name/lander-ness) is stable for the
            # whole session, so keep that registry — it's reset on LoadGame/Shutdown —
            # so a Nomad redeployed on the next body is still labelled "Nomad".
            self.srv_deployed_ids = set()
            self.current_vehicle_id = None

    def register_vehicle(
        self, vehicle_id: int | None, srv_type: str | None = None,
        localised: str | None = None,
    ) -> None:
        """Record what we know about a vehicle by id: its SRVType, localised name,
        and whether it's a flying lander. Fed by LaunchSRV/RestockVehicle/DockSRV,
        which carry the type; Embark/LaunchFighter don't, so this is how the Nomad's
        id gets tagged before it ever flies."""
        if vehicle_id is None:
            return
        with self.lock:
            if srv_type:
                self.srv_types[vehicle_id] = srv_type
                if is_lander_type(srv_type):
                    self.lander_ids.add(vehicle_id)
            if localised:
                self.srv_localised[vehicle_id] = localised

    def mark_flyer(self, vehicle_id: int | None) -> None:
        """Behavioral fallback: a vehicle we're piloting that lifts off / touches
        down is a lander, whatever its type name. Keeps FLY/leave-behind correct for
        a future lander whose SRVType we don't recognise yet."""
        if vehicle_id is None:
            return
        with self.lock:
            self.lander_ids.add(vehicle_id)

    def stranded_vehicle_ids(self) -> set[int]:
        """Deployed vehicles that would be left behind if we departed now — everything
        currently out except the one we're piloting. Empty while flying the lone
        Nomad; {scarab} while flying the Nomad away from a parked Scarab."""
        with self.lock:
            return set(self.srv_deployed_ids) - {self.current_vehicle_id}

    def in_lander(self) -> bool:
        """True when the vehicle we're currently piloting is a flying lander (Nomad)."""
        with self.lock:
            return self.current_vehicle_id in self.lander_ids

    def stranded_label(self) -> str:
        """Header-chip text for what's currently strandable: the lander's localised
        name when only a lander is out ('NOMAD'), 'SRV' for a ground SRV, joined with
        '+' when both. Empty when nothing would be left behind."""
        with self.lock:
            stranded = set(self.srv_deployed_ids) - {self.current_vehicle_id}
            labels: list[str] = []
            for vid in stranded:
                if vid in self.lander_ids:
                    label = (self.srv_localised.get(vid) or 'Lander').upper()
                else:
                    label = 'SRV'
                if label not in labels:
                    labels.append(label)
            return ' + '.join(sorted(labels))

    def clear_system(self) -> None:
        with self.lock:
            self.system_stars = {}
            self.region_id = None
            self.system_first_discovered = False
            self.system_population = 0

    def store_body_scan(self, body_key: str, data: dict) -> None:
        serializable = {k: list(v) if isinstance(v, set) else v for k, v in data.items()}
        with self.lock:
            existing = self.body_scans.setdefault(body_key, {})
            # first_footfall is sticky-True: once a body is known to be unfootfalled
            # when first scanned, a later Scan (e.g. a re-scan after you've footfalled
            # it, which reports WasFootfalled=True) must not clear the bonus. Backfill
            # relies on this too, so its ordering vs the live replay never matters.
            if 'first_footfall' in serializable:
                serializable['first_footfall'] = (
                    bool(existing.get('first_footfall')) or bool(serializable['first_footfall'])
                )
            existing.update(serializable)
        self.save()

    def add_confirmed_species(self, body_key: str, species_loc: str) -> None:
        """Record a species confirmed present via a biological CodexEntry."""
        with self.lock:
            seen = self.confirmed.setdefault(body_key, set())
            if species_loc in seen:
                return
            seen.add(species_loc)
        self.save()

    def get_confirmed_species(self, body_key: str | None) -> set[str]:
        if body_key is None:
            return set()
        with self.lock:
            return set(self.confirmed.get(body_key, set()))

    def get_body_scan(self, body_key: str | None) -> dict:
        if body_key is None:
            return {}
        with self.lock:
            result = dict(self.body_scans.get(body_key, {}))
        if 'candidate_genera' in result and isinstance(result['candidate_genera'], list):
            result['candidate_genera'] = set(result['candidate_genera'])
        return result
