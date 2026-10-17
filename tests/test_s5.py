"""S5: Know what to do."""
from datetime import date

import pandas as pd
import pytest

from stall_alerter.core import analyze

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)

ACTIONS = {
    "Applied": "applied-action",
    "Screen": "screen-action",
    "Interview": "CUSTOM interview action",
    "Final": "final-action",
    "Offer": "offer-action",
}


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id="C1", stage="Interview", entered="2026-10-01"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, "recruiter1"]


def test_ac5_1_action_from_stage_rule_table():
    df = make_df([row("C1", stage="Interview")])
    result = analyze(df, today=TODAY, threshold=5, action_rules=ACTIONS)
    assert result.flagged.iloc[0]["action"] == "CUSTOM interview action"


def test_ac5_2_missing_stage_mapping_fails():
    df = make_df([row("C1", stage="Interview")])
    rules = {k: v for k, v in ACTIONS.items() if k != "Interview"}
    with pytest.raises(ValueError, match="Interview"):
        analyze(df, today=TODAY, threshold=5, action_rules=rules)


def test_ac5_3_action_in_output_row():
    df = make_df([row("C1", stage="Offer")])
    result = analyze(df, today=TODAY, threshold=5)
    action = result.flagged.iloc[0]["action"]
    assert isinstance(action, str) and len(action) > 0
