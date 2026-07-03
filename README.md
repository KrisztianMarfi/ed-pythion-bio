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
variable.

### Options

| Flag | Description |
|------|-------------|
| `--journal-dir DIR` | Override the journal directory (default: Proton Steam prefix). |
| `--replay FILE` | Replay a saved journal file instead of watching live (for testing). |
| `--speed N` | Replay speed multiplier (default: `1.0` = real time; `5` = 5× faster). |
| `--stats-file FILE` | On launch, write a bio-payout-by-star report here (default: `./stats.txt`; pass `""` to disable). |
| `--show-corrections` | Print the local ruleset corrections learned from your samples, then exit. |

### Replay / testing

A sample journal fixture is included so you can sanity-check the TUI without
being in-game:

```sh
ed-bio-helper --replay tests/fixtures/sample_journal.log --speed 5
```

## State & data

Per-body sample locations and scan progress are persisted to:

```
~/.local/share/ed-bio-helper/state.json
```

This survives app restarts mid-expedition. Session credit totals reset on each
app start.

## Credits

This project builds on data from Silarn's excellent EDMC plugins (both MIT
licensed):

- Genus minimum-distance thresholds from
  [EDMC-ExploData](https://github.com/Silarn/EDMC-ExploData).
- Species credit values from
  [EDMC-BioScan](https://github.com/Silarn/EDMC-BioScan).

## License

MIT
