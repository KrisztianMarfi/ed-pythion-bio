# ed-bio-helper

A small Linux console TUI companion for **Elite Dangerous: Odyssey** exobiology.

**This has been created with the help of Claude. If you are against AI or  
   AI assisted coding, please ignore it.** 

It tails the game's journal and `Status.json` in real time, predicts which
organisms a body can host and what they're worth, and gives you live
sampling-distance guidance while you're on foot — all in a terminal next to the
game.

**No overlay. No game injection. Pure file watching.**

---

## Features

- **Live sampling guidance** — minimum sample distance for the current genus and
  the live great-circle distance from your nearest existing same-genus sample,
  with a clear `READY` / `WALK` / `FIRST` status indicator.
- **Species prediction** — predicts the organisms a body can host from its type,
  atmosphere, temperature, star, and region, plus the credit value of each.
- **Payout tracking** — predicted value for the organism being scanned and a
  running session total of confirmed Analyse payouts (first-footfall ×5 handled
  automatically).
- **Per-body progress** — a list of organisms with scan progress
  (`1/3`, `2/3`, `3/3` → `ANALYSED`).
- **Audio cues** — a beep when you cross the genus minimum-distance threshold, a
  gentle heads-up when you lift off leaving a vehicle behind, and a repeating
  warning if you start charging the FSD with an SRV/Nomad stranded on the surface.
- **Stats report** — a bio-payout-by-star text report written on launch.
- **Self-calibrating** — learns and widens its prediction rulesets from the
  spawns you actually confirm.
- **Self-updating** — an Oh-My-Zsh-style check on startup that offers to
  `pip install --upgrade` a newer release.

## Requirements

- Python 3.10+
- [`rich`](https://github.com/Textualize/rich) (installed automatically)

## Install

```sh
pip install -e .
```

Or with [uv](https://github.com/astral-sh/uv):

```sh
uv pip install -e .
```

## Usage

```sh
ed-bio-helper
```

The default journal directory is the Proton/Steam compatdata path:

```
~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/
```

Override it with `--journal-dir PATH` or the `ED_JOURNAL_DIR` environment
variable. A path passed with `--journal-dir` is **remembered** for next time, so
you only need to pass it once. Resolution order is: `--journal-dir` (saved) →
`ED_JOURNAL_DIR` (transient, not saved) → last saved path → the built-in default.

### Options

| Flag | Description |
|------|-------------|
| `--journal-dir DIR` | Override the journal directory (default: Proton Steam prefix). |
| `--replay FILE` | Replay a saved journal file instead of watching live (for testing). |
| `--speed N` | Replay speed multiplier (default: `1.0` = real time; `5` = 5× faster). |
| `--stats-file FILE` | On launch, write a bio-payout-by-star report here (default: `./stats.txt`; pass `""` to disable). |
| `--show-corrections` | Print the local ruleset corrections learned from your samples, then exit. |
| `--no-update` | Skip the startup check for a newer tagged release (for this run). |

### Replay / testing

A sample journal fixture is included so you can sanity-check the TUI without
being in-game:

```sh
ed-bio-helper --replay tests/fixtures/sample_journal.log --speed 5
```

## Windows

The app is pure Python and runs on Windows too, but it's primarily developed and
tested on Linux, so treat Windows as best-effort. Two things differ:

- **Journal directory.** The Proton/Steam default doesn't apply — point it at the
  native Elite Dangerous journal location. With `--journal-dir` this is
  remembered, so you only pass it once:

  ```powershell
  ed-bio-helper --journal-dir "$env:USERPROFILE\Saved Games\Frontier Developments\Elite Dangerous"
  ```

  Or set it for the session instead:

  ```powershell
  $env:ED_JOURNAL_DIR = "$env:USERPROFILE\Saved Games\Frontier Developments\Elite Dangerous"
  ```

- **Audio cues** rely on the Linux `paplay` command; on Windows they fall back to
  the terminal bell (`\a`).

Install is the same, and the startup update check works too — it uses pip, so no
git is required. Use a terminal with decent ANSI support — Windows Terminal is
recommended over the legacy console.

## Updating

On startup the app checks GitHub (at most once a day) for a newer release. When
one exists it asks before doing anything:

```
  A new version of ed-bio-helper is available: v1.2.0 (you have 1.1.0).
  Update now? [Y/n]
```

Answer `Y` (the default) and it runs `pip install --upgrade` against that
release's source tarball, then restarts itself; answer `n` and it just starts.
No git is needed — pip fetches the tarball over HTTPS.

The check is best-effort and stays out of your way: it silently does nothing when
you're offline, not on a terminal, or running a `pip install -e .` **editable dev
checkout** (so your working copy is never touched). If the upgrade fails it prints
the manual `pip install --upgrade …` command instead.

Controls:

| | |
|------|-------------|
| `--no-update` | Skip the check for this run. |
| `ED_BIO_HELPER_NO_UPDATE=1` | Disable the check entirely. |
| `ED_BIO_HELPER_UPDATE_INTERVAL=SECONDS` | Change the throttle window (default: `86400`). |

The last-checked timestamp lives at `~/.local/share/ed-bio-helper/.last_update_check`.

## State & data

Per-body sample locations and scan progress are persisted to:

```
~/.local/share/ed-bio-helper/state.json
```

This survives app restarts mid-expedition. Session credit totals reset on each
app start.

Stable preferences (currently your chosen journal directory) are stored
separately in:

```
~/.local/share/ed-bio-helper/config.json
```

Delete this file to forget a remembered `--journal-dir`.

## Credits

This project builds on data from Silarn's excellent EDMC plugins (both MIT
licensed):

- Genus minimum-distance thresholds from
  [EDMC-ExploData](https://github.com/Silarn/EDMC-ExploData).
- Species credit values from
  [EDMC-BioScan](https://github.com/Silarn/EDMC-BioScan).

## License

MIT
