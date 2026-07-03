import argparse
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from rich.live import Live

from .biology import genus_min_distance
from .corrections import Corrections
from .geo import haversine
from .history import compute_unsold_earnings
from .journal import bootstrap_context, journal_tailer, replay_journal
from .state import AppState
from .stats import write_stats
from .status import status_poller
from .tui import build_display


_BELL_SOUND = '/usr/share/sounds/freedesktop/stereo/bell.oga'
_WARN_SOUND = '/usr/share/sounds/freedesktop/stereo/dialog-warning.oga'
_INFO_SOUND = '/usr/share/sounds/freedesktop/stereo/dialog-information.oga'
# Re-sound the SRV-strand warning this often (s) while the danger persists, so it
# nags through the whole FSD spool-up rather than being a single easy-to-miss blip.
_SRV_WARN_INTERVAL = 2.0


def _beep(sound: str = _BELL_SOUND) -> None:
    """Non-blocking audio cue via paplay; silently no-ops if unavailable."""
    try:
        subprocess.Popen(
            ['paplay', sound],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        sys.stdout.write('\a')
        sys.stdout.flush()


def _is_sampling_ready(state: AppState) -> bool:
    """True when the current position is clear of the active genus' minimum sample
    distance — i.e. a fresh sample could be taken here.

    Works on foot, in the SRV, AND while flying the ship near the body, so the audio
    cue fires the moment you cross the threshold while scouting a landing spot from
    the air. Not gated on on_surface: it relies on having a live position (lat/lon/
    radius from Status.json) and an active genus, both of which clear_current_body
    wipes when you leave the body — so it stays quiet out in supercruise/space.
    """
    with state.lock:
        genus = state.current_genus
        lat = state.lat
        lon = state.lon
        radius = state.planet_radius
    if not genus or lat is None or lon is None or not radius:
        return False
    min_dist = genus_min_distance(genus)
    if min_dist is None:
        return False
    samples = state.get_samples_for_genus(genus)
    if not samples:
        return True  # no prior samples — anywhere is fine
    nearest = min(haversine(lat, lon, s[0], s[1], radius) for s in samples)
    return nearest >= min_dist


def _srv_strand_risk(state: AppState) -> bool:
    """True when the FSD is charging while a vehicle would be left behind — i.e.
    you're about to jump away from a deployed SRV/Nomad you're not piloting. Uses the
    stranded set (everything out except the vehicle you're in), so a Nomad you're
    flying doesn't self-trigger, but a Scarab parked below it does."""
    with state.lock:
        return state.fsd_charging and bool(state.stranded_vehicle_ids())


def _consume_srv_liftoff_warning(state: AppState) -> bool:
    """Take the pending 'lifted off with SRV out' flag (one gentle beep per liftoff)."""
    with state.lock:
        pending = state.srv_liftoff_warn_pending
        state.srv_liftoff_warn_pending = False
        return pending

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


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='ed-bio-helper',
        description='Elite Dangerous Odyssey exobiology sampling assistant',
    )
    parser.add_argument(
        '--journal-dir',
        metavar='DIR',
        help='Override the journal directory (default: Proton Steam prefix)',
    )
    parser.add_argument(
        '--replay',
        metavar='FILE',
        help='Replay a journal file for testing (does not watch live)',
    )
    parser.add_argument(
        '--speed',
        type=float,
        default=1.0,
        metavar='N',
        help='Replay speed multiplier (default: 1.0)',
    )
    parser.add_argument(
        '--show-corrections',
        action='store_true',
        help='Print the local ruleset corrections learned from your samples, then exit',
    )
    parser.add_argument(
        '--stats-file',
        metavar='FILE',
        default='stats.txt',
        help='On launch, write a bio-payout-by-star report here (default: ./stats.txt). '
             'Pass "" to disable.',
    )
    args = parser.parse_args()

    if args.show_corrections:
        print(Corrections().format_report())
        return

    journal_dir = _resolve_journal_dir(args.journal_dir)

    if args.replay:
        replay_path = Path(args.replay).expanduser()
        if not replay_path.is_file():
            print(f'error: replay file not found: {replay_path}', file=sys.stderr)
            sys.exit(1)
        _run_replay(replay_path, args.speed)
    else:
        if not journal_dir.is_dir():
            print(
                f'error: journal directory not found: {journal_dir}\n'
                'Use --journal-dir to override.',
                file=sys.stderr,
            )
            sys.exit(1)
        if args.stats_file:
            write_stats(journal_dir, Path(args.stats_file).expanduser())
        _run_live(journal_dir)


def _run_live(journal_dir: Path) -> None:
    state = AppState()
    state.unsold_credits = compute_unsold_earnings(journal_dir)
    state.corrections = Corrections()
    state.corrections.apply_saved()
    bootstrap_context(journal_dir, state)
    stop = threading.Event()

    j_thread = threading.Thread(
        target=journal_tailer,
        args=(journal_dir, state, stop),
        daemon=True,
        name='journal-tailer',
    )
    s_thread = threading.Thread(
        target=status_poller,
        args=(journal_dir, state, stop),
        daemon=True,
        name='status-poller',
    )

    j_thread.start()
    s_thread.start()

    try:
        prev_ready = False
        last_srv_warn = 0.0
        with Live(build_display(state), refresh_per_second=4, screen=True) as live:
            while True:
                ready = _is_sampling_ready(state)
                if ready and not prev_ready:
                    _beep()
                prev_ready = ready
                if _srv_strand_risk(state) and time.monotonic() - last_srv_warn >= _SRV_WARN_INTERVAL:
                    _beep(_WARN_SOUND)
                    last_srv_warn = time.monotonic()
                if _consume_srv_liftoff_warning(state):
                    _beep(_INFO_SOUND)
                live.update(build_display(state))
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()


def _run_replay(replay_path: Path, speed: float) -> None:
    state = AppState()
    state.corrections = Corrections()
    state.corrections.apply_saved()
    stop = threading.Event()

    # Status poller still tries the journal dir for Status.json; in replay
    # mode there may not be one, so it silently no-ops.
    journal_dir = replay_path.parent
    s_thread = threading.Thread(
        target=status_poller,
        args=(journal_dir, state, stop),
        daemon=True,
        name='status-poller',
    )
    s_thread.start()

    replay_done = threading.Event()

    def _do_replay() -> None:
        replay_journal(replay_path, state, speed=speed)
        replay_done.set()

    r_thread = threading.Thread(target=_do_replay, daemon=True, name='replay')
    r_thread.start()

    try:
        prev_ready = False
        last_srv_warn = 0.0
        with Live(build_display(state), refresh_per_second=4, screen=True) as live:
            while not replay_done.is_set():
                ready = _is_sampling_ready(state)
                if ready and not prev_ready:
                    _beep()
                prev_ready = ready
                if _srv_strand_risk(state) and time.monotonic() - last_srv_warn >= _SRV_WARN_INTERVAL:
                    _beep(_WARN_SOUND)
                    last_srv_warn = time.monotonic()
                if _consume_srv_liftoff_warning(state):
                    _beep(_INFO_SOUND)
                live.update(build_display(state))
                time.sleep(0.25)
            # Show the final state for a moment
            live.update(build_display(state))
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()


if __name__ == '__main__':
    main()
