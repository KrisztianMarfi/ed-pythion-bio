"""Startup self-update check (pip + GitHub source tarball).

On live startup (throttled to once a day) this asks the GitHub API for the newest
release tag and, if it is newer than the installed version, offers to run
``pip install --upgrade <that tag's source tarball>``. No git is required on the
user's machine — pip fetches the auto-generated ``.tar.gz`` over plain HTTPS.

Everything here is best-effort. It silently no-ops for editable/dev installs (so a
``pip install -e .`` checkout is never clobbered), when the package metadata is
missing, when the network is down, or when stdio is not a TTY. Disable entirely
with ``ED_BIO_HELPER_NO_UPDATE=1``; override the throttle (seconds) with
``ED_BIO_HELPER_UPDATE_INTERVAL``.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from importlib import metadata
from pathlib import Path

_PACKAGE = 'ed-bio-helper'
_REPO = 'KrisztianMarfi/ed-pythion-bio'
_TAGS_URL = f'https://api.github.com/repos/{_REPO}/tags?per_page=100'
_TARBALL_URL = 'https://github.com/{repo}/archive/refs/tags/{tag}.tar.gz'

_DEFAULT_INTERVAL = 24 * 60 * 60  # once per day
_HTTP_TIMEOUT = 10  # seconds; keep startup snappy on a slow network
_PIP_TIMEOUT = 300


def _stamp_path() -> Path:
    xdg = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))
    return Path(xdg) / 'ed-bio-helper' / '.last_update_check'


def _interval() -> float:
    raw = os.environ.get('ED_BIO_HELPER_UPDATE_INTERVAL')
    if raw:
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
    return _DEFAULT_INTERVAL


def _due(stamp: Path, interval: float) -> bool:
    """True if we've never checked, or the throttle window has elapsed."""
    try:
        return time.time() - stamp.stat().st_mtime >= interval
    except FileNotFoundError:
        return True
    except OSError:
        return False


def _touch(stamp: Path) -> None:
    """Record 'checked now' so a failed fetch or a declined prompt doesn't re-nag."""
    try:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        os.utime(stamp, None)
    except OSError:
        pass


def _parse_version(tag: str) -> tuple[int, ...]:
    """Turn a tag like 'v1.2.3' into (1, 2, 3) for ordering. Empty on garbage."""
    parts: list[int] = []
    for chunk in tag.lstrip('vV').strip().split('.'):
        digits = ''
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def _installed_version() -> str | None:
    """The version pip recorded for this package, or None if it can't be read."""
    try:
        return metadata.version(_PACKAGE)
    except metadata.PackageNotFoundError:
        return None


def _is_editable_install() -> bool:
    """True for a `pip install -e .` dev checkout, which we must not auto-upgrade."""
    try:
        raw = metadata.distribution(_PACKAGE).read_text('direct_url.json')
    except Exception:
        return False
    if not raw:
        return False
    try:
        info = json.loads(raw)
    except ValueError:
        return False
    return bool(info.get('dir_info', {}).get('editable'))


def _fetch_json(url: str) -> object | None:
    """GET a JSON document, returning the parsed body or None on any failure.

    Sends a User-Agent — the GitHub API rejects requests without one.
    """
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': f'{_PACKAGE}-updater',
            'Accept': 'application/vnd.github+json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None


def _latest_release() -> tuple[str, tuple[int, ...]] | None:
    """Highest-version tag on the GitHub repo as (tag_name, version), or None.

    The tags API isn't guaranteed to be version-sorted, so pick the max ourselves.
    Using tags (not `releases/latest`) means simply pushing a tag is enough — no
    formal GitHub Release required.
    """
    data = _fetch_json(_TAGS_URL)
    if not isinstance(data, list):
        return None
    best: tuple[str, tuple[int, ...]] | None = None
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        if not isinstance(name, str):
            continue
        version = _parse_version(name)
        if version and (best is None or version > best[1]):
            best = (name, version)
    return best


def _pip_upgrade(tag: str) -> bool:
    """Run pip against the tag's source tarball. Streams pip's output to the user."""
    url = _TARBALL_URL.format(repo=_REPO, tag=tag)
    try:
        proc = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', url],
            timeout=_PIP_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _restart() -> None:
    """Re-exec so the freshly installed code runs, preserving the original arguments."""
    os.execvp(sys.executable, [sys.executable, '-m', 'ed_bio_helper', *sys.argv[1:]])


def _prompt_and_update(tag: str, installed: str) -> None:
    print(f'\n  A new version of ed-bio-helper is available: {tag} (you have {installed}).')
    try:
        answer = input('  Update now? [Y/n] ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if answer not in ('', 'y', 'yes'):
        return
    print('  Updating via pip...\n')
    if not _pip_upgrade(tag):
        manual = _TARBALL_URL.format(repo=_REPO, tag=tag)
        print(f'\n  Update failed. Upgrade manually with:\n    pip install --upgrade {manual}\n')
        return
    print('\n  Updated. Restarting...\n')
    _restart()


def check_for_update() -> None:
    """Throttled startup check for a newer release tarball. Best-effort; never raises."""
    if os.environ.get('ED_BIO_HELPER_NO_UPDATE'):
        return
    # Can't prompt without an interactive terminal; stay quiet under pipes/CI.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return

    installed = _installed_version()
    if installed is None:
        return  # no recorded metadata — can't compare, so do nothing
    if _is_editable_install():
        return  # dev checkout; the developer manages their own updates

    stamp = _stamp_path()
    if not _due(stamp, _interval()):
        return
    # Stamp before the network call so a fetch failure or a declined prompt waits out
    # the throttle window instead of retrying (and re-prompting) on every launch.
    _touch(stamp)

    latest = _latest_release()
    if latest is None:
        return
    tag, latest_version = latest
    if latest_version <= _parse_version(installed):
        return

    _prompt_and_update(tag, installed)
