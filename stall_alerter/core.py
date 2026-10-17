"""Stall detection."""
import pandas as pd


def flag_stalled(df, today, threshold=None, stage_thresholds=None):
    """Return the rows whose days in stage exceed their stage's threshold."""
    stage_thresholds = stage_thresholds or {}
    if threshold is None:
        missing = sorted(set(df["stage"]) - set(stage_thresholds))
        if missing:
            raise ValueError(f"no threshold for stage(s): {', '.join(missing)}")
    limits = df["stage"].map(lambda s: stage_thresholds.get(s, threshold))
    entered = pd.to_datetime(df["stage_entered_date"])
    days = (pd.Timestamp(today) - entered).dt.days
    return df[days > limits]
