"""S7: Draft the follow-up."""
from datetime import date

import pandas as pd

from stall_alerter.core import analyze
from stall_alerter.report import render

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


class FakeLLM:
    def __init__(self, response="Draft text from the model"):
        self.response = response
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        return self.response


class FailingLLM:
    def complete(self, prompt):
        raise RuntimeError("API down")


def make_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def row(candidate_id, name, role, stage, entered, owner):
    return [candidate_id, name, role, stage, entered, owner]


def test_ac7_1_addressed_to_right_person():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
        row("C2", "Grace Hopper", "Engineer", "Screen", "2026-10-01", "rec-owner"),
    ])
    result = analyze(df, today=TODAY, threshold=5)
    to = dict(zip(result.flagged["candidate_id"], result.flagged["draft_to"]))
    assert to["C1"] == "rec-owner"
    assert to["C2"] == "Grace Hopper"


def test_ac7_2_draft_contains_csv_facts():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
    ])
    result = analyze(df, today=TODAY, threshold=5)
    text = result.flagged.iloc[0]["draft_text"]
    assert "Ada Lovelace" in text and "Engineer" in text and "Interview" in text


def test_ac7_3_llm_via_injected_client():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
    ])
    llm = FakeLLM(response="Personalised nudge from the model")
    result = analyze(df, today=TODAY, threshold=5, llm=llm)
    flagged = result.flagged.iloc[0]
    assert flagged["draft_text"] == "Personalised nudge from the model"
    assert flagged["draft_source"] == "AI"
    assert len(llm.prompts) == 1 and "Ada Lovelace" in llm.prompts[0]


def test_ac7_4_failure_and_invalid_fall_back():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
        row("C2", "Grace Hopper", "Engineer", "Interview", "2026-10-01", "rec-owner"),
    ])
    failing = analyze(df, today=TODAY, threshold=5, llm=FailingLLM())
    assert list(failing.flagged["draft_source"]) == ["template", "template"]

    empty = analyze(df, today=TODAY, threshold=5, llm=FakeLLM(response="   "))
    assert list(empty.flagged["draft_source"]) == ["template", "template"]


def test_ac7_5_status_needs_review():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
    ])
    for llm in (None, FakeLLM()):
        result = analyze(df, today=TODAY, threshold=5, llm=llm)
        assert result.flagged.iloc[0]["draft_status"] == "needs review"


def test_ac7_6_overlong_draft_replaced():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
    ])
    long_text = " ".join(["word"] * 81)
    result = analyze(df, today=TODAY, threshold=5, llm=FakeLLM(response=long_text))
    flagged = result.flagged.iloc[0]
    assert flagged["draft_source"] == "template"
    assert flagged["draft_text"] != long_text


def test_ac7_7_report_labels_draft():
    df = make_df([
        row("C1", "Ada Lovelace", "Engineer", "Interview", "2026-10-01", "rec-owner"),
    ])
    result = analyze(df, today=TODAY, threshold=5, llm=FakeLLM())
    output = render(result)
    assert "Draft text from the model" in output
    assert "AI" in output
