"""S11: Explain any result."""
from datetime import date

import pandas as pd
import pytest

from stall_alerter.cli import main
from stall_alerter.core import analyze
from stall_alerter.explain import explain

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def make_df(rows, columns=COLUMNS):
    return pd.DataFrame(rows, columns=columns)


def row(candidate_id, stage="Interview", entered="2026-10-01", owner="rec1"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, owner]


def test_ac11_1_explain_flagged(tmp_path, capsys):
    csv = tmp_path / "board.csv"
    make_df([row("C1", "Offer", "2026-10-02")]).to_csv(csv, index=False)
    rc = main([str(csv), "--today", "2026-10-11", "--threshold", "5",
               "--stage-threshold", "Offer=3", "--explain", "C1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Days in stage: 9" in out
    assert "Threshold: 3 (stage override)" in out
    assert "Days overdue: 6" in out
    assert "Rank: 1" in out


def test_ac11_2_rule_and_normalisations():
    df = make_df([row("C1", stage=" interview ", entered="2026-10-01")])
    result = analyze(df, today=TODAY, threshold=5)
    out = explain(result, "C1")
    assert "Chase the owner for interview feedback" in out
    assert "rule for stage 'Interview'" in out
    assert "interview" in out.lower()  # normalisation note recorded


def test_ac11_3_non_flagged_reasons():
    cols = COLUMNS + ["status"]
    df = make_df([
        row("C1", entered="2026-10-10") + ["Active"],   # under threshold
        row("C2", entered="2026-10-01") + ["Hired"],    # inactive
        row("C3", entered="2026-10-01") + ["Active"],   # snoozed
        row("C4", stage="Chit-chat") + ["Active"],      # rejected
    ], columns=cols)
    state = {"C3": {"last_chased": "2026-10-09", "stage": "Interview"}}
    result = analyze(df, today=TODAY, threshold=5, state=state)
    assert "under threshold" in explain(result, "C1").lower()
    assert "inactive" in explain(result, "C2").lower()
    assert "snoozed" in explain(result, "C3").lower()
    assert "chased 2 days ago" in explain(result, "C3")
    assert "rejected" in explain(result, "C4").lower()


def test_ac11_4_unknown_id_errors(tmp_path, capsys):
    df = make_df([row("C1")])
    result = analyze(df, today=TODAY, threshold=5)
    with pytest.raises((KeyError, ValueError), match="NOPE"):
        explain(result, "NOPE")

    csv = tmp_path / "board.csv"
    df.to_csv(csv, index=False)
    rc = main([str(csv), "--today", "2026-10-11", "--explain", "NOPE"])
    captured = capsys.readouterr()
    assert rc != 0 and "NOPE" in captured.err


def test_ac11_5_same_numbers_as_ranking():
    df = make_df([row("C1"), row("C2", entered="2026-09-25")])
    result = analyze(df, today=TODAY, threshold=5)
    top = result.flagged.iloc[0]
    out = explain(result, top["candidate_id"])
    assert f"Days in stage: {top['days_in_stage']}" in out
    assert f"Days overdue: {top['days_overdue']}" in out
    assert "Rank: 1" in out
