"""S1: See who is stalled."""
from datetime import date

import pandas as pd

from stall_alerter.core import flag_stalled

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id="C1", stage="Interview", entered="2026-10-01"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, "recruiter1"]


def test_ac1_1_flags_candidate_over_threshold():
    df = make_df([row(entered="2026-10-01")])
    result = flag_stalled(df, today=date(2026, 10, 11), threshold=5)
    assert list(result["candidate_id"]) == ["C1"]


def test_ac1_2_not_flagged_at_threshold():
    df = make_df([row(entered="2026-10-06")])
    result = flag_stalled(df, today=date(2026, 10, 11), threshold=5)
    assert len(result) == 0


def test_ac1_3_days_computed_from_today_param():
    df = make_df([row(entered="2026-10-06")])
    before = flag_stalled(df, today=date(2026, 10, 11), threshold=5)
    after = flag_stalled(df, today=date(2026, 10, 12), threshold=5)
    assert len(before) == 0
    assert len(after) == 1


def test_ac1_4_empty_csv_returns_empty():
    df = make_df([])
    result = flag_stalled(df, today=date(2026, 10, 11), threshold=5)
    assert len(result) == 0
