"""S3: Trust the data."""
from datetime import date

import pandas as pd

from stall_alerter.core import analyze

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id="C1", stage="Interview", entered="2026-10-01"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, "recruiter1"]


def test_ac3_1_missing_or_malformed_date_rejected():
    df = make_df([
        row("C1", entered=""),
        row("C2", entered="garbage"),
    ])
    result = analyze(df, today=TODAY, threshold=5)
    assert len(result.flagged) == 0
    assert sorted(result.rejected["candidate_id"]) == ["C1", "C2"]
    assert all("date" in r for r in result.rejected["reason"])


def test_ac3_2_unknown_stage_rejected():
    df = make_df([row("C1", stage="Chit-chat")])
    result = analyze(df, today=TODAY, threshold=5)
    assert len(result.flagged) == 0
    assert "Chit-chat" in result.rejected.iloc[0]["reason"]


def test_ac3_3_future_date_rejected():
    df = make_df([row("C1", entered="2026-10-20")])
    result = analyze(df, today=TODAY, threshold=5)
    assert len(result.flagged) == 0
    assert "future" in result.rejected.iloc[0]["reason"]


def test_ac3_4_duplicate_uses_most_recent():
    df = make_df([
        row("C1", entered="2026-09-27"),  # 14 days ago
        row("C1", entered="2026-10-05"),  # 6 days ago
    ])
    result = analyze(df, today=TODAY, threshold=5)
    assert list(result.flagged["candidate_id"]) == ["C1"]
    assert result.flagged.iloc[0]["days_in_stage"] == 6
    dupes = result.rejected[result.rejected["reason"].str.contains("duplicate")]
    assert len(dupes) == 1
    assert dupes.iloc[0]["candidate_id"] == "C1"


def test_ac3_5_counts_reported():
    df = make_df([
        row("C1", entered="2026-10-01"),   # stalled
        row("C2", entered="2026-10-10"),   # under threshold
        row("C3", entered="garbage"),      # rejected
        row("C1", entered="2026-10-05"),   # duplicate -> rejected
    ])
    result = analyze(df, today=TODAY, threshold=5)
    assert result.rows_read == 4
    assert len(result.flagged) == 1
    assert len(result.rejected) == 2
