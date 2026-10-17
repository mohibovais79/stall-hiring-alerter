"""Stall detection and ranking."""
from dataclasses import dataclass, field

import pandas as pd

from .constants import COLUMNS, DEFAULT_ACTIONS, STAGE_ORDER  # noqa: F401
from .drafts import draft_for
from .normalize import is_inactive, normalize_stage, parse_stage_entered
from .state import snooze_reason
from .summary import summarize


@dataclass
class Analysis:
    flagged: pd.DataFrame
    rejected: pd.DataFrame
    rows_read: int
    inactive: pd.DataFrame = None
    snoozed: pd.DataFrame = None
    summary: object = None
    traces: dict = field(default_factory=dict)


def analyze(df, today, threshold=None, stage_thresholds=None,
            action_rules=None, llm=None, aliases=None, state=None,
            stage_order=STAGE_ORDER, snooze_window_days=3, word_limit=80,
            bottleneck_min_count=3, bottleneck_min_pct=0.5):
    """Validate and normalise rows, then flag and rank stalled candidates."""
    rejected = []
    inactive = []
    valid = []
    for row in df.to_dict("records"):
        notes = []
        stage, note = normalize_stage(row.get("stage"), aliases, stage_order)
        if note:
            notes.append(note)
        entered, note = parse_stage_entered(row.get("stage_entered_date"))
        if note:
            notes.append(note)
        row["normalizations"] = notes
        if stage is None:
            rejected.append({**row, "reason": f"unknown stage {row.get('stage')!r}"})
        elif entered is None:
            rejected.append({**row, "reason": "missing or malformed date"})
        elif entered > today:
            rejected.append({**row, "reason": "stage_entered_date in the future"})
        elif is_inactive(row.get("status")):
            inactive.append(row)
        else:
            valid.append({**row, "stage": stage, "stage_entered_date": entered})

    # Duplicates: keep the row with the most recent stage_entered_date.
    valid.sort(key=lambda r: (r["candidate_id"], r["stage_entered_date"]))
    seen = {}
    for row in valid:
        cid = row["candidate_id"]
        if cid in seen:
            rejected.append({**seen[cid], "reason": "duplicate candidate_id"})
        seen[cid] = row
    kept = pd.DataFrame(list(seen.values()), columns=list(COLUMNS) + ["normalizations", "status"])

    rejected_df = pd.DataFrame(rejected)
    enriched = _enrich(kept, today, threshold, stage_thresholds)
    flagged = _rank(enriched, stage_order)

    snoozed = []
    if state:
        kept_rows = []
        for rec in flagged.to_dict("records"):
            reason = snooze_reason(rec, state, today, snooze_window_days)
            if reason:
                snoozed.append({**rec, "reason": reason})
            else:
                kept_rows.append(rec)
        flagged = pd.DataFrame(kept_rows, columns=flagged.columns)

    rules = action_rules if action_rules is not None else DEFAULT_ACTIONS
    missing = sorted(set(flagged["stage"]) - set(rules))
    if missing:
        raise ValueError(f"no action rule for stage(s): {', '.join(missing)}")
    flagged["action"] = flagged["stage"].map(rules)

    drafts = [draft_for(r, client=llm, word_limit=word_limit)
              for r in flagged.to_dict("records")]
    flagged["draft_text"] = [d.text for d in drafts]
    flagged["draft_source"] = [d.source for d in drafts]
    flagged["draft_to"] = [d.addressed_to for d in drafts]
    flagged["draft_status"] = [d.status for d in drafts]

    # Per-candidate trace for --explain: built from the same enriched rows
    # the ranking used, so the two can never disagree (AC11.5).
    traces = {}
    for rec in enriched.to_dict("records"):
        reason = (f"{rec['days_in_stage']} days in {rec['stage']}, "
                  f"under the {rec['threshold']}-day limit")
        traces[str(rec["candidate_id"])] = {
            "record": rec, "outcome": "under threshold", "reason": reason}
    for i, rec in enumerate(flagged.to_dict("records")):
        traces[str(rec["candidate_id"])] = {
            "record": rec, "outcome": "flagged", "rank": i + 1}
    for rec in snoozed:
        traces[str(rec["candidate_id"])] = {
            "record": rec, "outcome": "snoozed", "reason": rec["reason"]}
    for row in inactive:
        traces[str(row["candidate_id"])] = {
            "record": row, "outcome": "inactive",
            "reason": f"status '{row.get('status')}'"}
    for row in rejected:
        cid = str(row["candidate_id"])
        if cid in traces:
            traces[cid].setdefault("rejected_rows", []).append(row["reason"])
        else:
            traces[cid] = {"record": row, "outcome": "rejected",
                           "reason": row["reason"]}

    return Analysis(
        flagged=flagged, rejected=rejected_df, rows_read=len(df),
        inactive=pd.DataFrame(inactive), snoozed=pd.DataFrame(snoozed),
        summary=summarize(flagged, bottleneck_min_count, bottleneck_min_pct),
        traces=traces,
    )


def flag_stalled(df, today, threshold=None, stage_thresholds=None,
                 stage_order=STAGE_ORDER):
    """Return stalled rows ranked by days overdue, with a reason per row."""
    return _rank(_enrich(df, today, threshold, stage_thresholds), stage_order)


def _enrich(df, today, threshold=None, stage_thresholds=None):
    """Add days_in_stage, threshold (+source) and days_overdue columns."""
    stage_thresholds = stage_thresholds or {}
    if threshold is None:
        missing = sorted(set(df["stage"]) - set(stage_thresholds))
        if missing:
            raise ValueError(f"no threshold for stage(s): {', '.join(missing)}")

    df = df.copy()
    df["threshold"] = df["stage"].map(lambda s: stage_thresholds.get(s, threshold))
    df["threshold_source"] = df["stage"].map(
        lambda s: "stage override" if s in stage_thresholds else "default")
    entered = pd.to_datetime(df["stage_entered_date"])
    df["days_in_stage"] = (pd.Timestamp(today) - entered).dt.days
    df["days_overdue"] = df["days_in_stage"] - df["threshold"]
    return df


def _rank(enriched, stage_order=STAGE_ORDER):
    """Filter to stalled rows and rank them."""
    out = enriched[enriched["days_in_stage"] > enriched["threshold"]].copy()
    out["reason"] = [
        f"{d} days in {s}, {o} over the {t}-day limit"
        for d, s, o, t in zip(
            out["days_in_stage"], out["stage"],
            out["days_overdue"], out["threshold"],
        )
    ]
    stage_rank = out["stage"].map({s: i for i, s in enumerate(stage_order)})
    out = out.assign(_stage_rank=stage_rank).sort_values(
        ["days_overdue", "_stage_rank", "candidate_id"],
        ascending=[False, False, True],
    ).drop(columns="_stage_rank").reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    return out
