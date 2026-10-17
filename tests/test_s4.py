"""S4: Know who to chase first."""
from datetime import date

import pandas as pd

from stall_alerter.core import flag_stalled

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id, stage, entered):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, "recruiter1"]


def test_ac4_1_ordered_by_days_overdue():
    df = make_df([
        row("C1", "Interview", "2026-10-04"),  # 7 days, 2 over
        row("C2", "Interview", "2026-09-27"),  # 14 days, 9 over
        row("C3", "Interview", "2026-10-01"),  # 10 days, 5 over
    ])
    result = flag_stalled(df, today=TODAY, threshold=5)
    assert list(result["candidate_id"]) == ["C2", "C3", "C1"]


def test_ac4_2_tie_broken_by_later_stage():
    df = make_df([
        row("C1", "Screen", "2026-09-27"),  # 14 days, 9 over
        row("C2", "Offer", "2026-09-27"),   # 14 days, 9 over
    ])
    result = flag_stalled(df, today=TODAY, threshold=5)
    assert list(result["candidate_id"]) == ["C2", "C1"]


def test_ac4_3_tie_broken_by_candidate_id():
    df = make_df([
        row("C9", "Screen", "2026-09-27"),
        row("C3", "Screen", "2026-09-27"),
    ])
    result = flag_stalled(df, today=TODAY, threshold=5)
    assert list(result["candidate_id"]) == ["C3", "C9"]


def test_ac4_4_reason_line():
    df = make_df([row("C1", "Interview", "2026-10-02")])  # 9 days, 4 over
    result = flag_stalled(df, today=TODAY, threshold=5)
    assert result.iloc[0]["reason"] == "9 days in Interview, 4 over the 5-day limit"
