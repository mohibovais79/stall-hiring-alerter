# Intent

## What I'm building
A stall alerter. It reads a CSV export of a hiring board, finds
candidates who have not moved stage in a set number of days, and outputs a
ranked follow-up list: who to contact first, and what to do about it.

## Who uses it
A recruiter or hiring manager who opens it on a Monday morning and needs a
ten-minute action list, not a dashboard.

## What good looks like
- Runs from one command on any CSV with the expected columns.
- The stall threshold is configurable, globally and per stage.
- Ranking is explainable: every row says in one line why it sits where it does.
- Bad input (missing or malformed dates, unknown stages, duplicates) is
  reported to the user, never silently dropped.
- Stall logic and ranking are deterministic and covered by tests, including
  edge cases, not just the happy path.

## How I normally work, and what I'm changing
I am a full stack AI engineer. My default workflow is to take an idea, drop a
prompt on a coding agent, and let it build, often in auto mode. It is fast, but
I end up reviewing a black box at the end, and the thing I optimise for is what
I want to code rather than what the user needs. This assessment is where I
deliberately change that.

## Habits I plan to drop

### 1. Prompt-first building
- Before: take an idea, prompt an agent, start building.
- Now: write user stories with acceptance criteria first. Every feature is
  designed from a story, not from what I feel like coding. The user's need is
  the starting point, not the implementation.
- Evidence: stories.md is committed before any code, and each commit references
  a story ID.

### 2. Black-box agent coding
- Before: agent in auto mode, little visibility into what it wrote or why,
  review only at the end if at all.
- Now: test-driven development with AI. I write the acceptance criteria in
  plain language, review and approve every test before any implementation is
  generated, watch it fail, then have the AI write the minimum code to pass it.
  One story at a time.
- Why: it keeps the spec in my hands and makes bad AI code fail loudly instead
  of looking plausible. The known risk is the AI writing tests that mirror its
  own implementation and pass for the wrong reason, so I check for that
  explicitly and log every case I catch.
- Evidence: git history shows test commits before implementation commits, and
  the daily logs record each wrong test or wrong implementation the AI
  produced and how I caught it.

## Process for every feature
1. Pick one user story.
2. Write or confirm its acceptance criteria myself.
3. Have the AI propose tests from the criteria; I review and approve them.
4. Run them and confirm they fail for the right reason.
5. Have the AI write the minimum code to pass.
6. Review the diff, run the full suite, commit, and log what happened.

## How I will know I changed
Each daily log states what I delegated to the AI, what I verified myself, what
the AI got wrong, and what I changed in directive.md as a result. The final
note on what I unlearned points to commits and log entries rather than claims.

## Honest expectations
I expect this to feel slower at first, and I expect to catch the AI writing
weak tests. If the process breaks down on any day, I will say so in that day's
log rather than smoothing it over.