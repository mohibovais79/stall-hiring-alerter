"""S9: Handle messy real-world data."""
from datetime import date

import pandas as pd

from stall_alerter.core import analyze

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)
ALIASES = {"Phone Screen": "Screen"}


def make_df(rows, columns=COLUMNS):
    return pd.DataFrame(rows, columns=columns)


def row(candidate_id, stage, entered, owner="rec1", status=None):
    base = [candidate_id, "Ada Lovelace", "Engineer", stage, entered, owner]
    return base + [status] if status is not None else base


def test_ac9_1_multiple_date_formats():
    df = make_df([
        row("C1", "Interview", "2026-10-01"),
        row("C2", "Interview", "01/10/2026"),
        row("C3", "Interview", "2026-10-01T10:00:00+00:00"),
    ])
    result = analyze(df, today=TODAY, threshold=5)
    assert sorted(result.flagged["candidate_id"]) == ["C1", "C2", "C3"]
    assert list(result.flagged["days_in_stage"]) == [10, 10, 10]


def test_ac9_2_timestamps_normalised_to_utc():
    df = make_df([
        # 23:30 +02:00 is 21:30 UTC on Oct 10 -> 1 day in stage on Oct 11
        row("C1", "Interview", "2026-10-10T23:30:00+02:00"),
        # 00:30 CEST Oct 25 (DST ends that day) is 22:30 UTC Oct 24 -> 1 day
        row("C2", "Interview", "2026-10-25T00:30:00+02:00"),
    ])
    result = analyze(df, today=date(2026, 10, 25), threshold=0)
    days = dict(zip(result.flagged["candidate_id"], result.flagged["days_in_stage"]))
    assert days == {"C1": 15, "C2": 1}


def test_ac9_3_stage_case_and_whitespace():
    df = make_df([row("C1", " interview ", "2026-10-01")])
    result = analyze(df, today=TODAY, threshold=5)
    assert list(result.flagged["stage"]) == ["Interview"]


def test_ac9_4_stage_alias():
    df = make_df([row("C1", "Phone Screen", "2026-10-01")])
    with_alias = analyze(df, today=TODAY, threshold=5, aliases=ALIASES)
    assert list(with_alias.flagged["stage"]) == ["Screen"]
    without = analyze(df, today=TODAY, threshold=5)
    assert len(without.flagged) == 0
    assert "unknown stage" in without.rejected.iloc[0]["reason"]


def test_ac9_5_inactive_status():
    cols = COLUMNS + ["status"]
    df = make_df([
        row("C1", "Interview", "2026-10-01", status="Hired"),
        row("C2", "Interview", "2026-10-01", status="On hold"),
        row("C3", "Interview", "2026-10-01", status="Active"),
    ], columns=cols)
    result = analyze(df, today=TODAY, threshold=5)
    assert list(result.flagged["candidate_id"]) == ["C3"]
    assert len(result.inactive) == 2


def test_ac9_6_normalisations_recorded():
    df = make_df([
        row("C1", " phone screen ", "01/10/2026"),
    ])
    result = analyze(df, today=TODAY, threshold=5, aliases=ALIASES)
    notes = result.flagged.iloc[0]["normalizations"]
    assert any("phone screen" in n.lower() for n in notes)
    assert any("day-first" in n.lower() or "date" in n.lower() for n in notes)
