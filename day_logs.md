# Daily Log: Stall Alerter (Option C)

## Timeline
- 17 October 2026: started (late in the day), worked on planning, specs and code
- 18 October 2026: no work
- 19 October 2026: review, documentation and videos

I did not use the full five days. I started late on the 17th, took no time on
the 18th, and finished on the 19th, so this log has two entries and nothing is
filled in for days I did not work.

## Day 1: 17 October 2026
**Goal:** Plan the project, define the stories, and build the tool.

**What I did:** I wrote the plan first (intent.md and the first directive.md),
then wrote user stories with acceptance criteria in stories.md, and only then
wrote the code from those stories. This is the first habit I set out to change:
normally I take an idea, prompt an agent, and start building. This time the
user stories came first and the features were designed from them.

**How I worked with the AI:** I used the AI to help draft the plan, the
stories and the directive, and to help build the code. I treated stories.md as
the source of truth and aimed to work test-first with AI, which is the second
habit I set out to change: moving away from auto-mode agent coding where I
review a black box at the end.

**Decisions I made:**
- Validation runs before status classification, so a row with a corrupt date is
  rejected even if its status says Hired, Rejected, Withdrawn or On hold. It is
  not counted as inactive. Reason: an untrustworthy row should surface as a
  data problem, not quietly inflate the inactive count.
- The follow-up list is ranked by days overdue, with later stages winning ties.
- The stories were extended beyond the core list-and-rank behaviour to include
  an LLM-drafted follow-up with a human-review gate and deterministic fallback,
  bottleneck detection, messy-data handling, follow-up memory, explainability,
  configuration, and scale handling.

## Day 2: 19 October 2026
**Goal:** Review the work and prepare the submission.

**What I did:** I reviewed the work, wrote up the documentation, and recorded
the Loom walkthrough and the demo video. The documentation covers the final
directive.md, change.log, the README and the note on what I unlearned.

**Note on timeline:** Everything above happened over two working days, 17 and
19 October. I did not use the days in between, and I am reporting it as it
was rather than spreading the work across five entries.