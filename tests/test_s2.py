"""S2: Set thresholds per stage."""
from datetime import date

import pandas as pd
import pytest

from stall_alerter.core import flag_stalled

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id, stage, entered="2026-10-01"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, "recruiter1"]


def test_ac2_1_default_applies_without_override():
    df = make_df([row("C1", "Interview", entered="2026-10-04")])  # 7 days in stage
    result = flag_stalled(df, today=TODAY, threshold=5)
    assert list(result["candidate_id"]) == ["C1"]


def test_ac2_2_override_beats_default():
    df = make_df([
        row("C1", "Offer", entered="2026-10-07"),      # 4 days, override 3 -> flag
        row("C2", "Interview", entered="2026-10-04"),  # 7 days, override 10 -> no
    ])
    result = flag_stalled(
        df, today=TODAY, threshold=5,
        stage_thresholds={"Offer": 3, "Interview": 10},
    )
    assert list(result["candidate_id"]) == ["C1"]


def test_ac2_3_missing_threshold_errors_naming_stage():
    df = make_df([row("C1", "Offer")])
    with pytest.raises(ValueError, match="Offer"):
        flag_stalled(df, today=TODAY, threshold=None,
                     stage_thresholds={"Interview": 10})
