# Stall Alerter: Usage Guide

The Stall Alerter reads a hiring-board CSV export and reports candidates who
have been in the same pipeline stage for too long. For each stalled candidate
it gives a rank, a reason, a suggested next action, and a draft follow-up
message that a human reviews before anything is sent.

This guide covers setup, the input file, every command-line option, the config
file, chase tracking, the report layout, and troubleshooting.

---

## 1. Requirements and setup

- Python 3.13 or newer, managed by [uv](https://docs.astral.sh/uv/).
- Dependencies: pandas (runtime), pytest (development). Both are declared in
  `pyproject.toml`.

From the repository root:

```powershell
uv sync
```

This creates `.venv` and installs the dependencies. The console command
`stall-alerter` is then available through `uv run`.

Check the install with the test suite:

```powershell
uv run pytest -q
```

---

## 2. Quick start

```powershell
uv run stall-alerter data/hiring_board.csv --today 2026-10-18 --threshold 5
```

- `data/hiring_board.csv` is the sample board shipped with the repo.
- `--today` fixes the reference date. Leave it out to use the current date.
  Pinning it makes runs reproducible.
- `--threshold 5` flags anyone who has been in a stage for more than 5 days.

---

## 3. Input file

The CSV must contain these columns (header names are exact, case-sensitive):

| Column | Meaning |
|---|---|
| `candidate_id` | Unique ID. Duplicates are allowed; see section 9. |
| `name` | Candidate name, passed through unchanged. |
| `role` | Role title, passed through unchanged. |
| `stage` | Pipeline stage: `Applied`, `Screen`, `Interview`, `Final`, `Offer`. |
| `stage_entered_date` | Date the candidate entered the current stage. |
| `owner` | Recruiter or hiring manager responsible. |

Optional column:

| Column | Meaning |
|---|---|
| `status` | `Hired`, `Rejected`, `Withdrawn` or `On hold` excludes the candidate from flagging. Other values such as `Active` are treated as active. |

Any other columns (for example `source_ats`) are ignored, not rejected.

### 3.1 Accepted date formats

| Format | Example | Notes |
|---|---|---|
| ISO date | `2026-10-01` | Preferred. |
| Day-first with slashes | `05/10/2026` | Read as 5 October 2026. Every slash date is day-first, so `05/06/2026` means 5 June. |
| ISO timestamp with offset | `2026-10-01T09:00:00+05:30` | Converted to UTC before the day is counted. |

Empty values and unparseable text such as `not-a-date` are rejected with a
reason. Dates later than `--today` are rejected as "in the future".

### 3.2 Stage names

Stage names are matched case-insensitively and with surrounding whitespace
removed, so ` interview ` is read as `Interview`. Other names must be listed
in the config file as aliases (section 6). Unknown stages are rejected.

### 3.3 Encodings and delimiters

The loader handles:

- UTF-8 files with or without a byte-order mark (BOM).
- Comma, semicolon or tab delimiters, detected from the header line.
- Extra columns.

---

## 4. Command-line reference

```
stall-alerter CSV [options]
```

| Option | Default | Description |
|---|---|---|
| `csv` | (required) | Path to the hiring-board CSV. |
| `--config PATH` | `stall-alerter.toml` | TOML config file. A missing file means built-in defaults. |
| `--threshold N` | config value, else `5` | Default days-in-stage limit. Overrides the config file. |
| `--stage-threshold STAGE=N` | none | Per-stage limit. Repeat the option for several stages. Overrides the config file. |
| `--output PATH` | none | Also write the flagged candidates to this CSV. |
| `--today YYYY-MM-DD` | current date | Reference date for "days in stage". |
| `--state PATH` | `.stall-alerter-state.json` | Chase-state file used for snoozing. |
| `--snooze-window N` | config value, else `3` | Days a chased candidate stays snoozed. |
| `--mark-chased CANDIDATE_ID` | none | Record the candidate as chased today, then exit. |
| `--explain CANDIDATE_ID` | none | Print one candidate's trace, then exit. |

Precedence: **command-line option > config file > built-in default.**

Exit codes: `0` on success. `2` on any error (missing file, missing columns,
bad config, corrupt state, unknown candidate, and similar).

---

## 5. Reading the report

A normal run prints four sections.

**Header line.** For example `Read 45 rows: 22 flagged, 6 rejected, 4 inactive`.
Every input row is accounted for.

**SUMMARY.** Flagged counts grouped by owner, then by stage, highest first.
Groups marked `BOTTLENECK` meet the bottleneck limits in section 6.
If nothing is flagged, the section says so and shows no bottlenecks.

**FLAGGED.** One row per stalled candidate, ranked from most overdue.

| Column | Meaning |
|---|---|
| `candidate_id`, `name`, `role`, `stage` | Identity and position. |
| `days_in_stage` | Days between `stage_entered_date` and `--today`. |
| `days_overdue` | `days_in_stage` minus the threshold for that stage. |
| `reason` | One-line explanation, for example `17 days in Applied, 12 over the 5-day limit`. |
| `action` | Suggested next step for the stage. |
| `draft_source` | `AI` or `template`. |
| `draft_status` | Always `needs review` on creation. The tool never marks a draft sent or approved. |
| `draft_text` | Draft follow-up message. Review before sending. |

Ranking: most days overdue first. Ties go to the later stage, then to
`candidate_id` in ascending order.

**REJECTED.** Rows that could not be used, each with a reason: unknown stage,
missing or malformed date, future date, or duplicate `candidate_id`.
Rejected rows are excluded from flagging and from the summary counts.

**SNOOZED.** Candidates who were chased recently (section 7) and so are
hidden from the flagged list, with a reason such as `chased 1 day ago`.

Inactive candidates (status `Hired`, `Rejected`, `Withdrawn` or `On hold`)
are counted in the header but not listed. Use `--explain` to see one.

---

## 6. Config file

Copy the sample and edit it:

```powershell
Copy-Item data/stall-alerter.toml stall-alerter.toml
```

The default config file name is `stall-alerter.toml` in the current working
directory. Pass `--config PATH` to use another file.

Annotated example:

```toml
# Days in stage before a candidate is flagged, for stages without an override.
default_threshold = 5

# Per-stage overrides. Keys must be stage names from stage_order.
[stage_thresholds]
Applied = 7
Screen = 5
Interview = 5
Final = 4
Offer = 3

# Map non-standard stage names to canonical ones. The target must be a known stage.
[aliases]
"Phone Screen" = "Screen"

# Suggested action for each stage. Every stage in stage_order needs an entry.
[action_rules]
Applied = "Send a status update to the candidate"
Screen = "Send a status update to the candidate"
Interview = "Chase the owner for interview feedback"
Final = "Chase the owner for a decision"
Offer = "Chase the owner on the offer"

# Pipeline order. Used for tie-breaking and validation.
# stage_order = ["Applied", "Screen", "Interview", "Final", "Offer"]

snooze_window_days = 3       # days a chased candidate stays hidden
bottleneck_min_count = 3     # flag an owner or stage with at least this many flagged candidates...
bottleneck_min_pct = 0.3     # ...or at least this share of all flagged candidates (0 to 1)
word_limit = 80              # maximum words in a draft before falling back to the template
```

### 6.1 Validation

The config is checked on load. Errors name the field and the problem, and the
run stops with exit code 2. Examples:

- `default_threshold: must be a non-negative integer, got -1`
- `stage_thresholds: unknown stage 'Phonescreen'`
- `aliases: 'Phone Screen' -> unknown stage 'Screenn'`
- `action_rules: no action for stage 'Offer'`
- `bottleneck_min_pct: must be between 0 and 1, got 1.5`

Unknown top-level keys produce a warning and are otherwise ignored:

```
warning: unknown config key 'defualt_threshold'
```

### 6.2 Threshold rules

- A candidate is flagged when `days_in_stage` is strictly greater than the
  threshold. Exactly 5 days with a threshold of 5 is not flagged.
- A stage override beats the default. Without a default, every stage in use
  needs an override, or the run fails with an error that names the stage.

---

## 7. Tracking chased candidates

The tool never marks anyone as chased by itself. You record it explicitly:

```powershell
uv run stall-alerter data/hiring_board.csv --mark-chased C007 --state data/state.json --today 2026-10-18
```

Then, on later runs with the same state file, C007 appears under SNOOZED for
the snooze window. The snooze is cleared automatically when the candidate
changes stage.

The state file is JSON, keyed by candidate ID:

```json
{
  "C007": { "last_chased": "2026-10-17", "stage": "Interview" }
}
```

- A missing state file is treated as empty.
- A corrupt state file stops the run with a clear error, and the tool does
  not overwrite it.
- Writes are atomic, so an interrupted run cannot leave a half-written file.

---

## 8. Explaining a result

```powershell
uv run stall-alerter data/hiring_board.csv --today 2026-10-18 --threshold 5 --explain C021
```

Example output:

```
Candidate C021: Elena Volkov — Data Analyst
Stage: Interview
Days in stage: 17
Threshold: 5 (default)
Days overdue: 12
Rank: 5
Action: Chase the owner for interview feedback (rule for stage 'Interview')
Outcome: flagged
Normalisations: timestamp '2026-10-01T09:00:00+05:30' converted to UTC
```

The outcome line says why a candidate was or was not flagged: `flagged`,
`under threshold`, `inactive`, `snoozed` or `rejected`. The explanation comes
from the same calculation as the ranking, so the two cannot disagree.


---

## 9. Data problems the tool reports

| Problem | Behaviour |
|---|---|
| Missing or malformed date | Rejected: "missing or malformed date". |
| Future date | Rejected: "stage_entered_date in the future". |
| Unknown stage | Rejected: "unknown stage '...'". Add an alias if the name is a known variant. |
| Duplicate `candidate_id` | The row with the most recent `stage_entered_date` is kept. The others are listed as rejected: "duplicate candidate_id". |
| Inactive status | Not flagged. Counted in the header as inactive. |
| Missing required columns | Error naming every missing column. |
| Header only, no data rows | Message: "No data rows", exit code 0. |
| No header row | Error about missing columns, no traceback. |

---

## 10. Troubleshooting

**`error: file not found: ...`**
Check the path. Relative paths are resolved from the current directory.

**`error: missing required column(s): stage, owner`**
The export lacks those headers. Rename the columns to the exact names in
section 3.

**`UnicodeEncodeError` when printing names**
Your console uses a legacy code page (often cp1252 in Windows PowerShell or
cmd). Either run:

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

or redirect the output to a file.

**`--stage-threshold` seems to have no effect**
Stage names are case-sensitive in this option. `--stage-threshold offer=3` is
silently ignored. Use `--stage-threshold Offer=3`.

**`error: invalid literal for int() with base 10: 'abc'`**
The value after `=` in `--stage-threshold` must be a whole number, for
example `Offer=3`. The message does not name the option, so check the value.

**`error: candidate not found: ID`** (with `--mark-chased`) or
**`error: unknown candidate_id: ID`** (with `--explain`)
The ID does not exist in the CSV. Check spelling and case.

**`error: corrupt state file ...`**
The JSON state file cannot be parsed. Fix it by hand or move it aside. The tool
will not overwrite it for you.

**Unexpected snooze**
Check the state file's `last_chased` date against `--today`, and make sure
you are using the intended `--state` path.

**Results differ from the spreadsheet**
Check the reference date (`--today`), the threshold in use (see the `Threshold`
line from `--explain`), and whether a stage override applies.

---

## 11. Running the tests

```powershell
uv run pytest -v
```

Tests live in `tests/`, one file per story (`test_s1.py` to `test_s13.py`).
The story and acceptance-criteria IDs are in `stories.md`.

---

## 12. Known limitations

- Dates with slashes are always read day-first. ISO dates are unaffected.
- Stage names in `--stage-threshold` are case-sensitive. A lowercase name is
  silently ignored. A config key that is not a known stage causes an error.
- Invalid `--stage-threshold` values produce a generic error message.
- Terminal rendering of non-ASCII text depends on the console code page
  (section 10).
- Drafts come from a deterministic template. The CLI does not configure an
  LLM client, so every draft is labelled `template`.
- The sample dataset in `data/` is for demonstration. It is not part of the
  test suite.

