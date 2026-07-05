"""Oh-My-Zsh-style self-update check.

On live startup (throttled to once a day) this fetches the upstream git tags and,
if a newer release tag exists than the one currently checked out, prompts the user
to `git pull`. Detection is tag-only: releases are cut by tagging, so we compare the
highest known tag against the tag reachable from HEAD.

Everything here is best-effort. If the install is not a git checkout, git is
missing, the network is down, or stdio is not a TTY, the check silently no-ops so
the app always starts. Disable entirely with ``ED_BIO_HELPER_NO_UPDATE=1``; override
the throttle (seconds) with ``ED_BIO_HELPER_UPDATE_INTERVAL``.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

_DEFAULT_INTERVAL = 24 * 60 * 60  # once per day
_FETCH_TIMEOUT = 10  # seconds; keep startup snappy on a slow network
_PULL_TIMEOUT = 60


def _run_git(args: list[str], cwd: Path, timeout: float) -> str | None:
    """Run a git command, returning its stdout (stripped) or None on any failure.

    An empty string is a successful command with no output (e.g. `fetch`), which is
    distinct from None — so callers test `is None` for failure, not truthiness.
    """
    try:
        proc = subprocess.run(
            ['git', *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _repo_root() -> Path | None:
    """The git checkout containing this package, or None if not installed from git."""
    top = _run_git(['rev-parse', '--show-toplevel'], cwd=Path(__file__).resolve().parent, timeout=5)
    return Path(top) if top else None


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


def _highest_tag(root: Path, extra_args: list[str] | None = None) -> str | None:
    """Highest-version tag (by `-v:refname`) among those matched, or None if none.

    `extra_args` narrows the set, e.g. `--merged HEAD` for tags reachable from HEAD.
    Version-sort — not `git describe`, which orders by topology and would pick an
    older tag when several sit on one commit.
    """
    out = _run_git(['tag', '--sort=-v:refname', *(extra_args or [])], cwd=root, timeout=5)
    if not out:
        return None
    return out.splitlines()[0].strip()


def _latest_tag(root: Path) -> str | None:
    """Highest tag known to the checkout (includes tags just fetched from origin)."""
    return _highest_tag(root)


def _current_tag(root: Path) -> str | None:
    """Highest tag reachable from HEAD — the release we're actually running.

    None on a checkout with no tags in its history yet, in which case any upstream
    tag counts as an available update.
    """
    return _highest_tag(root, ['--merged', 'HEAD'])


def _restart() -> None:
    """Re-exec so the freshly pulled code runs, preserving the original arguments."""
    os.execvp(sys.executable, [sys.executable, '-m', 'ed_bio_helper', *sys.argv[1:]])


def _prompt_and_update(root: Path, current: str | None, latest: str) -> None:
    have = current or 'an untagged build'
    print(f'\n  A new version of ed-bio-helper is available: {latest} (you have {have}).')
    try:
        answer = input('  Update now? [Y/n] ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if answer not in ('', 'y', 'yes'):
        return
    print('  Updating via git pull...')
    if _run_git(['pull', '--ff-only'], cwd=root, timeout=_PULL_TIMEOUT) is None:
        print(
            '  Update failed — local changes or diverged history. '
            f'Pull manually with: git -C {root} pull\n'
        )
        return
    print('  Updated. Restarting...\n')
    _restart()


def check_for_update() -> None:
    """Throttled startup check for a newer tagged release. Best-effort; never raises."""
    if os.environ.get('ED_BIO_HELPER_NO_UPDATE'):
        return
    # Can't prompt without an interactive terminal; stay quiet under pipes/CI.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return

    stamp = _stamp_path()
    if not _due(stamp, _interval()):
        return

    root = _repo_root()
    if root is None:
        return  # installed some other way; nothing to pull

    # Stamp before the network call so a fetch failure or a declined prompt waits out
    # the throttle window instead of retrying (and re-prompting) on every launch.
    _touch(stamp)

    if _run_git(['fetch', '--tags', '--quiet', 'origin'], cwd=root, timeout=_FETCH_TIMEOUT) is None:
        return

    latest = _latest_tag(root)
    if not latest:
        return
    current = _current_tag(root)
    if current and _parse_version(latest) <= _parse_version(current):
        return

    _prompt_and_update(root, current, latest)
