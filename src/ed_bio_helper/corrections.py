"""Data-driven calibration of the local species rulesets.

Every confirmed spawn (ScanOrganic / biological CodexEntry) is ground truth: the
game is deterministic, so an observation isn't a noisy sample — it's a fact. We
use only the *safe* kind of fact here: false negatives, where the predictor
failed to list a species that genuinely appeared. If the sole reason a species
fell out of an otherwise-matching ruleset is a numeric bound (gravity /
temperature / pressure / distance), we widen that bound to include the observed
value. That can only add a case that really occurs; it never removes a valid
prediction, so it can't degrade accuracy elsewhere.

Categorical mismatches (wrong atmosphere / body type / region / star) are logged
as 'unexplained' for upstream reporting (Canonn / BioScan) but never auto-applied
— generalising a new niche from a single observation is exactly the overfitting
we want to avoid.

Widenings are persisted to ``ruleset_corrections.json`` (XDG data dir) and
re-applied to the in-memory catalog at startup; the vendored ``predict.py`` data
is never edited on disk.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from . import predict


def _path() -> Path:
    xdg = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))
    p = Path(xdg) / 'ed-bio-helper' / 'ruleset_corrections.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# Scan fields worth keeping in the human-readable log (skip bulky star/atm dicts).
_LOG_PARAMS = (
    'planet_class', 'atmosphere_type', 'surface_gravity',
    'surface_temperature', 'surface_pressure', 'volcanism', 'region_id',
)


def _trim_params(params: dict) -> dict:
    return {k: params.get(k) for k in _LOG_PARAMS if params.get(k) not in (None, '')}


class Corrections:
    """Tracks predictor misses and widens local rulesets to fit confirmed spawns."""

    def __init__(self, path: Path | None = None) -> None:
        self.lock = threading.RLock()
        self.bounds: dict[str, dict[str, float]] = {}   # "genus|species|idx" -> {bound: value}
        self.log: list[dict] = []                       # applied widenings, for the report
        self.unexplained: list[dict] = []               # categorical misses (not auto-fixed)
        self.processed: set[str] = set()                # "body_key|species_key" already seen
        self._path = path or _path()
        self._load()

    # -- persistence ---------------------------------------------------------

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return
        self.bounds = data.get('bounds', {})
        self.log = data.get('log', [])
        self.unexplained = data.get('unexplained', [])
        self.processed = set(data.get('processed', []))

    def _save(self) -> None:
        with self.lock:
            data = {
                'bounds': self.bounds,
                'log': self.log,
                'unexplained': self.unexplained,
                'processed': sorted(self.processed),
            }
        try:
            self._path.write_text(json.dumps(data, indent=2))
        except OSError:
            pass

    # -- catalog wiring ------------------------------------------------------

    def apply_saved(self) -> int:
        """Re-apply persisted widenings to the in-memory catalog. Returns # applied."""
        n = 0
        with self.lock:
            items = list(self.bounds.items())
        for key, widenings in items:
            try:
                genus_key, species_key, idx_s = key.split('|')
            except ValueError:
                continue
            if predict.apply_widening(genus_key, species_key, int(idx_s), widenings):
                n += 1
        return n

    @property
    def applied_count(self) -> int:
        with self.lock:
            return len(self.bounds)

    # -- the learning step ---------------------------------------------------

    def observe(self, genus_key: str, species_key: str, body_key: str,
                body_name: str, ts: str, **params) -> str:
        """Diagnose one confirmed spawn and widen the local ruleset if it's a fixable miss.

        Idempotent per (body, species). Returns a short status:
        'skip' | 'predicted' | 'applied' | 'unexplained' | 'unknown'.
        """
        tag = f'{body_key}|{species_key}'
        with self.lock:
            if tag in self.processed:
                return 'skip'

        result = predict.diagnose_observation(genus_key, species_key, **params)
        status = result.get('status')
        sp_name = predict.species_name(genus_key, species_key) or species_key

        with self.lock:
            self.processed.add(tag)

            if status == 'widen':
                idx = result['ruleset_index']
                bkey = f'{genus_key}|{species_key}|{idx}'
                cur = self.bounds.setdefault(bkey, {})
                before: dict[str, float | None] = {}
                for k, v in result['widenings'].items():
                    before[k] = predict.ruleset_bound(genus_key, species_key, idx, k)
                    # Keep the widest bound seen so far for this ruleset.
                    cur[k] = max(v, cur.get(k, v)) if k.startswith('max_') else min(v, cur.get(k, v))
                predict.apply_widening(genus_key, species_key, idx, cur)
                self.log.append({
                    'ts': ts, 'body': body_name, 'species': sp_name, 'ruleset': idx,
                    'widened': {k: [before[k], cur[k]] for k in result['widenings']},
                    'params': _trim_params(params),
                })
                ret = 'applied'
            elif status == 'unexplained':
                self.unexplained.append({
                    'ts': ts, 'body': body_name, 'species': sp_name,
                    'params': _trim_params(params),
                })
                ret = 'unexplained'
            else:
                ret = status or 'unknown'  # 'predicted' or 'unknown_species'

        self._save()
        return ret

    # -- reporting -----------------------------------------------------------

    def format_report(self) -> str:
        with self.lock:
            applied = list(self.log)
            unexplained = list(self.unexplained)
            n_bounds = len(self.bounds)

        out: list[str] = []
        out.append('Local ruleset corrections')
        out.append('=========================')
        out.append(f'Bound widenings active: {n_bounds}   '
                   f'(from {len(applied)} confirmed miss(es))')
        out.append('')
        if applied:
            out.append('Widened bounds (species the predictor missed, now included):')
            for e in applied:
                changes = ', '.join(
                    f'{k} {_fmt_bound(before)}→{_fmt_bound(after)}'
                    for k, (before, after) in e['widened'].items()
                )
                out.append(f"  • {e['species']}  @ {e['body']}")
                out.append(f"      ruleset #{e['ruleset']}: {changes}")
        else:
            out.append('No bound widenings yet — every sampled species was predicted. 👍')
        out.append('')
        if unexplained:
            out.append('Unexplained misses (categorical mismatch — NOT auto-applied;')
            out.append('worth reporting upstream to Canonn / BioScan):')
            for e in unexplained:
                params = ', '.join(f'{k}={v}' for k, v in e['params'].items())
                out.append(f"  • {e['species']}  @ {e['body']}  [{params}]")
        return '\n'.join(out)


def _fmt_bound(v) -> str:
    if v is None:
        return '∅'
    if isinstance(v, float):
        return f'{v:g}'
    return str(v)
