# Stall Hiring Alerter

A command-line tool that reads a recruiting pipeline CSV export and flags
candidates who have been stuck in the same stage too long. It ranks them by
how overdue they are, suggests a next action, drafts a follow-up message for
human review, and highlights where stalls cluster (by owner or by stage) so
you can fix the process, not just chase individuals.

Full usage guide: [docs/usage.md](docs/usage.md).
Project spec (source of truth for behaviour): [stories.md](stories.md).

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

## Setup

```powershell
uv sync
```

This creates `.venv` and installs the dependencies (pandas at runtime,
pytest for tests). The `stall-alerter` command then runs via `uv run`.

Verify the install:

```powershell
uv run pytest -q
```

## Quick start

```powershell
uv run stall-alerter data/hiring_board.csv --today 2026-10-18 --threshold 5
```

`data/hiring_board.csv` is a sample dataset shipped with the repo covering
every stage, every rejection reason, and every normalisation case (see
`data/README.md`). `--today` pins the reference date so output is
reproducible; omit it to use the current date.

## Input file

The CSV must have these columns (exact names, case-sensitive):

```
candidate_id, name, role, stage, stage_entered_date, owner
```

`stage` must be one of `Applied, Screen, Interview, Final, Offer` (case and
whitespace are normalised automatically; other names need a config alias).
An optional `status` column (`Hired`, `Rejected`, `Withdrawn`, `On hold`)
excludes a candidate from flagging.

## Common commands

Flag with per-stage thresholds from a config file:

```powershell
uv run stall-alerter data/hiring_board.csv --config data/stall-alerter.toml --today 2026-10-18
```

Track who's already been chased, so they're not flagged again immediately:

```powershell
uv run stall-alerter data/hiring_board.csv --mark-chased C007 --state data/state.json --today 2026-10-18
uv run stall-alerter data/hiring_board.csv --state data/state.json --today 2026-10-18
```

Explain exactly how one candidate was (or wasn't) flagged:

```powershell
uv run stall-alerter data/hiring_board.csv --today 2026-10-18 --threshold 5 --explain C021
```

Every normal run also writes a dated markdown snapshot to
`reports/<today>.md` (configurable with `--report-dir`).

See [docs/usage.md](docs/usage.md) for the full CLI reference, config file
format, report layout, data-problem handling, and troubleshooting
(including a known Windows console encoding caveat with non-ASCII names).

## Running tests

```powershell
uv run pytest -v
```

Tests live in `tests/`, one file per user story (`test_s1.py`–`test_s14.py`).
Story IDs and acceptance criteria are defined in `stories.md`.

## Project layout

```
stall_alerter/   CLI and core logic (one module per concern: io, normalize,
                 config, state, drafts, summary, report, markdown_report, explain)
tests/           pytest suite, one file per story
data/            sample dataset and config/state fixtures for manual runs
docs/            usage guide
stories.md       user stories and acceptance criteria (the spec)
change.log       dated log of every story and spec change
```