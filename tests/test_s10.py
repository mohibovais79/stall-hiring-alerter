"""S10: Remember follow-ups."""
import json
from datetime import date

import pandas as pd
import pytest

from stall_alerter.cli import main
from stall_alerter.core import analyze
from stall_alerter.state import StateError, load_state, mark_chased

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id, stage="Interview", entered="2026-10-01", owner="rec1"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, owner]


def test_ac10_1_state_records_last_chased(tmp_path):
    path = tmp_path / "state.json"
    mark_chased(path, "C1", "Interview", TODAY)
    state = load_state(path)
    assert state["C1"]["last_chased"] == "2026-10-11"
    assert state["C1"]["stage"] == "Interview"


def test_ac10_2_snoozed_within_window():
    df = make_df([row("C1"), row("C2")])
    state = {"C1": {"last_chased": "2026-10-09", "stage": "Interview"}}
    result = analyze(df, today=TODAY, threshold=5, state=state,
                     snooze_window_days=3)
    assert list(result.flagged["candidate_id"]) == ["C2"]
    assert list(result.snoozed["candidate_id"]) == ["C1"]
    assert "chased 2 days ago" in result.snoozed.iloc[0]["reason"]


def test_ac10_2_window_boundary():
    df = make_df([row("C1")])
    state = {"C1": {"last_chased": "2026-10-08", "stage": "Interview"}}
    result = analyze(df, today=TODAY, threshold=5, state=state,
                     snooze_window_days=3)
    assert list(result.flagged["candidate_id"]) == ["C1"]
    assert len(result.snoozed) == 0


def test_ac10_3_stage_move_clears_snooze():
    df = make_df([row("C1", stage="Interview")])
    state = {"C1": {"last_chased": "2026-10-09", "stage": "Screen"}}
    result = analyze(df, today=TODAY, threshold=5, state=state,
                     snooze_window_days=3)
    assert list(result.flagged["candidate_id"]) == ["C1"]
    assert len(result.snoozed) == 0


def test_ac10_4_report_never_writes_state(tmp_path, capsys):
    csv = tmp_path / "board.csv"
    make_df([row("C1")]).to_csv(csv, index=False)
    state_path = tmp_path / "state.json"
    rc = main([str(csv), "--today", "2026-10-11", "--state", str(state_path)])
    assert rc == 0
    assert not state_path.exists()

    rc = main([str(csv), "--today", "2026-10-11", "--state", str(state_path),
               "--mark-chased", "C1"])
    assert rc == 0
    assert state_path.exists()
    assert load_state(state_path)["C1"]["last_chased"] == "2026-10-11"


def test_ac10_5_missing_and_corrupt_state(tmp_path):
    missing = tmp_path / "nope.json"
    assert load_state(missing) == {}
    df = make_df([row("C1")])
    result = analyze(df, today=TODAY, threshold=5, state=load_state(missing))
    assert len(result.flagged) == 1

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_bytes(b"{not json")
    with pytest.raises(StateError, match="corrupt"):
        load_state(corrupt)
    with pytest.raises(StateError):
        mark_chased(corrupt, "C1", "Interview", TODAY)
    assert corrupt.read_bytes() == b"{not json"


def test_ac10_6_atomic_write(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"C0": {"last_chased": "2026-10-01",
                                       "stage": "Screen"}}))
    import stall_alerter.state as state_mod

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(state_mod.os, "replace", boom)
    with pytest.raises(OSError):
        mark_chased(path, "C1", "Interview", TODAY)
    assert json.loads(path.read_text()) == {
        "C0": {"last_chased": "2026-10-01", "stage": "Screen"}}
    assert list(tmp_path.glob("*.tmp")) == []
