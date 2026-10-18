# User Stories: Stall Alerter

## Input contract
CSV with columns: candidate_id, name, role, stage, stage_entered_date (YYYY-MM-DD),
owner. "Today" is a parameter (defaults to the current date) so tests are deterministic.

Stages, in order: Applied, Screen, Interview, Final, Offer.

---

## S1: See who is stalled
As a recruiter, I want to see candidates who have not moved stage for N days,
so I know who is stuck.

Acceptance criteria
- AC1.1: A candidate whose days in stage is greater than the threshold is flagged.
- AC1.2: A candidate whose days in stage equals the threshold is not flagged.
- AC1.3: Days in stage is computed from stage_entered_date and the "today" parameter.
- AC1.4: An empty CSV returns an empty result without error.

## S2: Set thresholds per stage
As a recruiter, I want a different threshold per stage, because an Offer
waiting 5 days is a bigger problem than an Applied candidate waiting 5 days.

Acceptance criteria
- AC2.1: A global default threshold applies when no stage override exists.
- AC2.2: A per-stage override takes precedence over the default.
- AC2.3: A stage with no override and no default is an error that names the stage.

## S3: Trust the data
As a recruiter, I want bad rows reported rather than silently skipped, so I
never miss a candidate because of a typo.

Acceptance criteria
- AC3.1: A row with a missing or malformed date is excluded from flagging and
  listed in a "rejected rows" section with the reason.
- AC3.2: A row with an unknown stage is listed in rejected rows with the reason.
- AC3.3: A future-dated stage_entered_date is rejected with the reason.
- AC3.4: Duplicate candidate_id rows are reported, and the most recent
  stage_entered_date is used.
- AC3.5: Output always states how many rows were read, flagged, and rejected.

## S4: Know who to chase first
As a recruiter, I want the list ranked, so I work top to bottom.

Acceptance criteria
- AC4.1: Candidates are ordered by days overdue (days in stage minus threshold),
  highest first.
- AC4.2: Ties are broken by later stage first (Offer before Screen).
- AC4.3: Remaining ties are broken by candidate_id so output is stable.
- AC4.4: Each row includes a one-line reason, e.g. "9 days in Interview,
  4 over the 5-day limit".

## S5: Know what to do
As a recruiter, I want a suggested next action per flagged candidate, so I
don't have to think about it.

Acceptance criteria
- AC5.1: The action comes from a rule table keyed by stage.
- AC5.2: Every valid stage has an action; a missing mapping fails loudly.
- AC5.3: The action text is included in each output row.

## S6: Run it easily
As a recruiter, I want one command that produces a readable report.

Acceptance criteria
- AC6.1: One CLI command takes a CSV path and optional threshold options.
- AC6.2: Output is a readable table in the terminal, with an option to write CSV.
- AC6.3: A missing file or missing required columns gives a clear error message,
  not a stack trace.


## S7: Draft the follow-up
As a recruiter, I want a drafted follow-up message for each flagged candidate,
so I can chase quickly, but I stay in control of what gets sent.

Acceptance criteria
- AC7.1: Each flagged candidate gets a draft addressed to the right person for
  their stage (candidate for Applied/Screen, owner for Interview/Final/Offer).
- AC7.2: The draft includes the candidate's name, role and stage, and only
  facts present in the CSV row (no invented details).
- AC7.3: Drafts are generated through an LLM client interface, so tests can
  inject a fake client with no network calls.
- AC7.4: If the LLM call fails or returns invalid output, the tool falls back
  to a deterministic template and marks the draft as "template".
- AC7.5: Every draft starts with status "needs review"; nothing is ever marked
  sent or approved by the tool itself.
- AC7.6: A draft longer than the limit (for example 80 words) is rejected and
  replaced by the fallback template.
- AC7.7: The report shows each draft next to its row, labelled "AI" or "template".


## S8: Spot bottlenecks
As a hiring manager, I want to see where stalls cluster, so I can fix the
process and not just chase individuals.

Acceptance criteria
- AC8.1: The report shows a summary above the list: flagged count per owner
  and per stage.
- AC8.2: An owner or stage is marked a bottleneck when it holds at least X
  flagged candidates or at least Y% of all flagged candidates (both configurable).
- AC8.3: Summary ordering is by flagged count, highest first, with ties broken
  alphabetically.
- AC8.4: With no flagged candidates, the summary says so and shows no bottlenecks.
- AC8.5: Rejected rows (S3) are excluded from the counts.

## S9: Handle messy real-world data
As a recruiter, I want the tool to cope with the exports I actually get, so I
don't have to clean the CSV by hand first.

Acceptance criteria
- AC9.1: Dates are accepted in YYYY-MM-DD, DD/MM/YYYY and ISO timestamps with
  timezone offsets; ambiguous formats follow a documented rule.
- AC9.2: Timestamps are converted to a single timezone before computing days,
  and a DST boundary does not change the day count wrongly.
- AC9.3: Stage names are matched case-insensitively and trimmed of whitespace.
- AC9.4: Stage aliases (for example "Phone Screen" for Screen) map to the
  canonical stage via a configurable alias table.
- AC9.5: An optional status column is supported; candidates with status Hired,
  Rejected, Withdrawn or On hold are never flagged and are counted in the
  summary as "inactive".
- AC9.6: Every normalisation applied to a row is recorded so it can be reported.

## S10: Remember follow-ups
As a recruiter, I don't want to be told to chase someone I already chased
yesterday.

Acceptance criteria
- AC10.1: A state file records the last-chased date per candidate_id.
- AC10.2: A candidate chased within the snooze window (configurable) is not
  ranked, and appears in a "snoozed" section with the reason, e.g. "chased
  2 days ago".
- AC10.3: A candidate who moves to a new stage has their snooze cleared.
- AC10.4: The tool never marks anyone as chased by itself; the user does it
  with an explicit command.
- AC10.5: A missing state file is treated as empty; a corrupt one gives a clear
  error and the tool does not overwrite it.
- AC10.6: State writes are atomic, so an interrupted run cannot corrupt the file.

## S11: Explain any result
As a recruiter, I want to see exactly how a candidate was ranked, so I can
trust the list.

Acceptance criteria
- AC11.1: `--explain <candidate_id>` prints days in stage, threshold used and
  where it came from (default or stage override), days overdue and rank position.
- AC11.2: It also prints the rule that produced the suggested action, and any
  normalisations applied to that row (S9).
- AC11.3: For a candidate who is not flagged, it says why (under threshold,
  inactive, snoozed, or rejected).
- AC11.4: An unknown candidate_id gives a clear error.
- AC11.5: The explanation is generated from the same function as the ranking,
  not a separate calculation, so the two cannot disagree.

## S12: Configure instead of hardcode
As a team lead, I want thresholds, stage order, aliases and action rules in a
config file, so I can adapt the tool without touching code.

Acceptance criteria
- AC12.1: Default threshold, per-stage thresholds, stage order, alias table,
  action rules, snooze window and bottleneck limits all load from one config file.
- AC12.2: A missing config file falls back to documented defaults.
- AC12.3: Validation errors name the field and the problem, e.g. a negative
  threshold, a stage with no action, or an alias pointing to an unknown stage.
- AC12.4: CLI options override config values, and config overrides defaults.
- AC12.5: Unknown keys in the config produce a warning, not a silent ignore.

## S13: Survive scale and bad files
As a recruiter, I want it to cope with large and awkward exports.

Acceptance criteria
- AC13.1: A file with 50,000 rows is processed within a time limit set after
  measuring a baseline, and the number is recorded in the log.
- AC13.2: A UTF-8 BOM, a semicolon or tab delimiter, and extra unknown columns
  are handled without error.
- AC13.3: Missing required columns give an error that lists exactly which ones
  are missing.
- AC13.4: A file with a header and no rows, and a file with no header, each
  give a clear message.
- AC13.5: Extremely long text fields and non-ASCII names pass through to the
  report unchanged.

---

## S14: Keep a dated markdown report
As a recruiter, I want each run saved as a markdown file named by date, so I
can review and share past runs without re-running the tool.

Acceptance criteria
- AC14.1: Every normal run writes a markdown report to reports/YYYY-MM-DD.md,
  using the --today date (or the current date). --mark-chased and --explain
  runs do not write a report.
- AC14.2: The --report-dir PATH option changes the output directory.
- AC14.3: The report has a title with the date, a count line (rows read,
  flagged, rejected, inactive), and sections for summary, flagged, rejected
  and snoozed.
- AC14.4: Flagged rows appear in the same rank order as the terminal report.
- AC14.5: Pipe characters in cell text are escaped so tables do not break,
  and the file is written as UTF-8.
- AC14.6: A run with no flagged candidates still writes a report that says so.
- AC14.7: Terminal output is unchanged by S14.

---

## Build order
S1, S2, S4, S3, S5, S6-s13, S14. Each story goes through the full cycle in directive.md
before the next one starts.

