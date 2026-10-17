"""S8: Spot bottlenecks."""
from datetime import date

import pandas as pd

from stall_alerter.core import analyze
from stall_alerter.report import render

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id, stage, owner, entered="2026-10-01"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, owner]


def test_ac8_1_counts_per_owner_and_stage():
    df = make_df([
        row("C1", "Interview", "rec1"),
        row("C2", "Interview", "rec1"),
        row("C3", "Offer", "rec2"),
    ])
    result = analyze(df, today=TODAY, threshold=5)
    owners = {g.name: g.count for g in result.summary.owners}
    stages = {g.name: g.count for g in result.summary.stages}
    assert owners == {"rec1": 2, "rec2": 1}
    assert stages == {"Interview": 2, "Offer": 1}


def test_ac8_2_bottleneck_by_count_or_pct():
    df = make_df([
        row("C1", "Interview", "rec1"),
        row("C2", "Interview", "rec1"),
        row("C3", "Offer", "rec2"),
    ])
    by_count = analyze(df, today=TODAY, threshold=5,
                       bottleneck_min_count=2, bottleneck_min_pct=1.0)
    flag = {g.name: g.bottleneck for g in by_count.summary.owners}
    assert flag == {"rec1": True, "rec2": False}

    by_pct = analyze(df, today=TODAY, threshold=5,
                     bottleneck_min_count=99, bottleneck_min_pct=0.4)
    flag = {g.name: g.bottleneck for g in by_pct.summary.owners}
    assert flag == {"rec1": True, "rec2": False}


def test_ac8_3_ordering():
    df = make_df([
        row("C1", "Interview", "b-rec"),
        row("C2", "Interview", "a-rec"),
        row("C3", "Interview", "a-rec"),
        row("C4", "Offer", "b-rec"),
    ])
    result = analyze(df, today=TODAY, threshold=5)
    names = [g.name for g in result.summary.owners]
    assert names == ["a-rec", "b-rec"]
    # a-rec has 2 (first), b-rec has 2 -> tie broken alphabetically
    df2 = make_df([
        row("C1", "Interview", "b-rec"),
        row("C2", "Interview", "a-rec"),
    ])
    result2 = analyze(df2, today=TODAY, threshold=5)
    assert [g.name for g in result2.summary.owners] == ["a-rec", "b-rec"]


def test_ac8_4_no_flagged():
    df = make_df([row("C1", "Interview", "rec1", entered="2026-10-10")])
    result = analyze(df, today=TODAY, threshold=5)
    assert result.summary.total == 0
    assert not any(g.bottleneck for g in result.summary.owners)
    assert "no flagged" in render(result).lower()


def test_ac8_5_rejected_excluded():
    df = make_df([
        row("C1", "Interview", "rec1"),
        row("C2", "Chit-chat", "rec2"),       # rejected: unknown stage
        row("C3", "Interview", "rec2", entered="2026-10-10"),  # under threshold
    ])
    result = analyze(df, today=TODAY, threshold=5)
    owners = {g.name: g.count for g in result.summary.owners}
    assert owners == {"rec1": 1}
