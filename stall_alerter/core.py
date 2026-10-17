"""Stall detection and ranking."""
import pandas as pd

STAGE_ORDER = ["Applied", "Screen", "Interview", "Final", "Offer"]


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
