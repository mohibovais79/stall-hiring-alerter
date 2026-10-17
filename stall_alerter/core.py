"""Stall detection."""
import pandas as pd


def flag_stalled(df, today, threshold):
    """Return the rows whose days in stage exceed the threshold."""
    entered = pd.to_datetime(df["stage_entered_date"])
    days = (pd.Timestamp(today) - entered).dt.days
    return df[days > threshold]
