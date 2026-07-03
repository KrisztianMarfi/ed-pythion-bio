import json
import threading
import time
from pathlib import Path

from .state import AppState

_ON_FOOT_FLAG2_BIT = 1 << 0   # Flags2 bit 0
_FSD_CHARGING_BIT = 1 << 17    # Flags bit 17 — FSD spooling up (strand danger point)


def _read_status(path: Path) -> dict | None:
    try:
        text = path.read_text()
        return json.loads(text)
    except (OSError, json.JSONDecodeError):
        try:
            time.sleep(0.02)
            text = path.read_text()
            return json.loads(text)
        except (OSError, json.JSONDecodeError):
            return None


def status_poller(journal_dir: Path, state: AppState, stop: threading.Event) -> None:
    """Poll Status.json every ~250 ms and update state."""
    status_file = journal_dir / 'Status.json'
    while not stop.is_set():
        data = _read_status(status_file)
        if data:
            flags2 = data.get('Flags2', 0)
            flags = data.get('Flags', 0)
            on_foot = bool(flags2 & _ON_FOOT_FLAG2_BIT)
            fsd_charging = bool(flags & _FSD_CHARGING_BIT)
            lat = data.get('Latitude')
            lon = data.get('Longitude')
            radius = data.get('PlanetRadius')
            heading = data.get('Heading')
            # Odyssey reports local ambient temperature (K) only while on a surface
            # (on foot / in SRV); absent in ship/space, where get() yields None.
            temperature = data.get('Temperature')
            with state.lock:
                state.on_foot = on_foot
                state.fsd_charging = fsd_charging
                if lat is not None:
                    state.lat = lat
                if lon is not None:
                    state.lon = lon
                if radius is not None:
                    state.planet_radius = radius
                # Heading is -1 when not applicable (e.g. airborne); treat as unknown.
                state.heading = heading if (heading is not None and heading >= 0) else None
                state.local_temperature = temperature
        stop.wait(0.25)
