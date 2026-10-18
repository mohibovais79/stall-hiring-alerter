# Sample dataset

Realistic hiring-board exports for manual exploration and demos of the CLI.
These are not part of the pytest suite (which uses small inline fixtures per
story) — they exist to exercise the tool end-to-end against one coherent,
realistic board.

## Files

- `hiring_board.csv` — 45-row primary dataset covering every stage
  (Applied, Screen, Interview, Final, Offer), a mix of flagged/not-flagged
  candidates, and every rejection/normalisation scenario from S3 and S9:
  - missing date (C017), malformed date (C018)
  - future-dated entry (C019)
  - day-first slash date (C020, 05/10/2026 -> 5 Oct)
  - ISO timestamps with timezone offsets, including a DST-adjacent one
    (C021, C022)
  - stage with stray whitespace/case (" interview ", C023)
  - an alias not covered by default config, so it's rejected as unknown
    without `--config` (C024, "Phone Screen")
  - duplicate candidate_id, most recent date wins (C015)
  - unknown stage (C016, "Negotiation")
  - every inactive status: Hired, Rejected, Withdrawn, On hold (C025-C028)
  - non-ASCII name (C037) and a comma-in-quotes name (C038, "Smith, John")
  - several owners (jsmith, mgarcia, tlee, akumar, rpatel, swong, bchen,
    dkim, enelson) and stage/owner combinations sized to trip the default
    bottleneck thresholds (>=3 flagged or >=50%/30% share) in S8's summary
  - candidates intentionally left under-threshold (e.g. C002, C003, C006)
    so "not everything is flagged" is also represented
- `stall-alerter.toml` — example config: per-stage thresholds, the
  "Phone Screen" -> Screen alias, snooze window and bottleneck limits
  tuned for this dataset (bottleneck_min_pct 0.3, so more owners/stages
  are flagged as bottlenecks than with the built-in default of 0.5).
- `state.json` — chase-state fixture for S10: a candidate snoozed today
  (C007, inside the 3-day window), one outside the window (C030), and one
  whose snooze is cleared because they moved stage since being chased
  (C031: chased at Screen, now in Interview).
- `edge_bom_utf8.csv`, `edge_semicolon.csv`, `edge_tab.csv` — first 3 rows
  of the main dataset re-encoded/re-delimited for S13's file-handling checks.
- `edge_missing_columns.csv` — header missing `stage` and `owner`.
- `edge_header_only.csv` — valid header, zero data rows.
- `edge_headerless.csv` — a single data row with no header at all.
- `edge_corrupt_state.json` — invalid JSON, for exercising S10's
  "corrupt state file" error path.

## Example commands

```
uv run stall-alerter data/hiring_board.csv --today 2026-10-18 --threshold 5
uv run stall-alerter data/hiring_board.csv --config data/stall-alerter.toml \
    --state data/state.json --today 2026-10-18
uv run stall-alerter data/hiring_board.csv --today 2026-10-18 --threshold 5 \
    --explain C021
```

Note: on a Windows terminal using a legacy code page (cp1252), rendering the
non-ASCII name in C037 can raise `UnicodeEncodeError` on `print()`. Set
`PYTHONIOENCODING=utf-8` first, or redirect output to a file. This is a
pre-existing console-encoding limitation of `report.py`/`explain.py`, not a
data problem — flagged here for awareness, not fixed as part of this change
(no story currently covers terminal encoding).
