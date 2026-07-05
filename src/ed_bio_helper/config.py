"""Persisted user preferences (config.json).

Kept separate from state.json — which holds volatile per-body sampling data rebuilt
from the journal — so stable settings a user chooses once (currently the journal
directory) survive launches without being tangled up with sampling state. All I/O is
best-effort: a missing or corrupt file reads as "no saved prefs" and never raises.
"""

import json
import os
from pathlib import Path


def _config_path() -> Path:
    xdg = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))
    return Path(xdg) / 'ed-bio-helper' / 'config.json'


def load_config() -> dict:
    try:
        data = json.loads(_config_path().read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_config(config: dict) -> None:
    path = _config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2))
    except OSError:
        pass


def get_journal_dir() -> str | None:
    value = load_config().get('journal_dir')
    return value if isinstance(value, str) else None


def set_journal_dir(path: str) -> None:
    """Remember an explicitly chosen journal directory (no write if unchanged)."""
    config = load_config()
    if config.get('journal_dir') == path:
        return
    config['journal_dir'] = path
    save_config(config)
