"""Stall detection and ranking."""
from dataclasses import dataclass, field

import pandas as pd

from .drafts import draft_for

STAGE_ORDER = ["Applied", "Screen", "Interview", "Final", "Offer"]
COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]

DEFAULT_ACTIONS = {
    "Applied": "Send a status update to the candidate",
    "Screen": "Send a status update to the candidate",
    "Interview": "Chase the owner for interview feedback",
    "Final": "Chase the owner for a decision",
    "Offer": "Chase the owner on the offer",
}


@dataclass
class Analysis:
    flagged: pd.DataFrame
    rejected: pd.DataFrame
    rows_read: int


def analyze(df, today, threshold=None, stage_thresholds=None,
            action_rules=None, llm=None):
    """Validate rows, then flag and rank the stalled candidates."""
    rejected = []
    valid = []
    for row in df.to_dict("records"):
        entered = pd.to_datetime(row.get("stage_entered_date"), errors="coerce")
        if pd.isna(entered):
            rejected.append({**row, "reason": "missing or malformed date"})
            continue
        if row.get("stage") not in STAGE_ORDER:
            rejected.append({**row, "reason": f"unknown stage {row.get('stage')!r}"})
            continue
        if entered.date() > today:
            rejected.append({**row, "reason": "stage_entered_date in the future"})
            continue
        valid.append({**row, "stage_entered_date": entered})

    # Duplicates: keep the row with the most recent stage_entered_date.
    valid.sort(key=lambda r: (r["candidate_id"], r["stage_entered_date"]))
    seen = {}
    for row in valid:
        cid = row["candidate_id"]
        if cid in seen:
            rejected.append({**seen[cid], "reason": "duplicate candidate_id"})
        seen[cid] = row
    kept = pd.DataFrame(list(seen.values()), columns=list(COLUMNS))

    rejected_df = pd.DataFrame(rejected)
    flagged = flag_stalled(kept, today, threshold, stage_thresholds)

    rules = action_rules if action_rules is not None else DEFAULT_ACTIONS
    missing = sorted(set(flagged["stage"]) - set(rules))
    if missing:
        raise ValueError(f"no action rule for stage(s): {', '.join(missing)}")
    flagged["action"] = flagged["stage"].map(rules)

    drafts = [draft_for(r, client=llm) for r in flagged.to_dict("records")]
    flagged["draft_text"] = [d.text for d in drafts]
    flagged["draft_source"] = [d.source for d in drafts]
    flagged["draft_to"] = [d.addressed_to for d in drafts]
    flagged["draft_status"] = [d.status for d in drafts]

    return Analysis(flagged=flagged, rejected=rejected_df, rows_read=len(df))


def flag_stalled(df, today, threshold=None, stage_thresholds=None):
    """Return stalled rows ranked by days overdue, with a reason per row."""
    stage_thresholds = stage_thresholds or {}
    if threshold is None:
        missing = sorted(set(df["stage"]) - set(stage_thresholds))
        if missing:
            raise ValueError(f"no threshold for stage(s): {', '.join(missing)}")

    df = df.copy()
    df["threshold"] = df["stage"].map(lambda s: stage_thresholds.get(s, threshold))
    entered = pd.to_datetime(df["stage_entered_date"])
    df["days_in_stage"] = (pd.Timestamp(today) - entered).dt.days

    out = df[df["days_in_stage"] > df["threshold"]].copy()
    out["days_overdue"] = out["days_in_stage"] - out["threshold"]
    out["reason"] = [
        f"{d} days in {s}, {o} over the {t}-day limit"
        for d, s, o, t in zip(
            out["days_in_stage"], out["stage"],
            out["days_overdue"], out["threshold"],
        )
    ]
    stage_rank = out["stage"].map({s: i for i, s in enumerate(STAGE_ORDER)})
    out = out.assign(_stage_rank=stage_rank).sort_values(
        ["days_overdue", "_stage_rank", "candidate_id"],
        ascending=[False, False, True],
    )
    return out.drop(columns="_stage_rank").reset_index(drop=True)
