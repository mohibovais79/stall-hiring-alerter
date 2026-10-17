"""S13: Survive scale and bad files."""
import time
from datetime import date

import pandas as pd

from stall_alerter.cli import main
from stall_alerter.core import analyze
from stall_alerter.io import load_csv

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = date(2026, 10, 11)


def row(candidate_id, stage="Interview", entered="2026-10-01", owner="rec1",
        name="Ada Lovelace"):
    return [candidate_id, name, "Engineer", stage, entered, owner]


def test_ac13_1_fifty_thousand_rows():
    n = 50_000
    df = pd.DataFrame({
        "candidate_id": [f"C{i}" for i in range(n)],
        "name": "Ada Lovelace",
        "role": "Engineer",
        "stage": "Interview",
        "stage_entered_date": "2026-10-01",
        "owner": "rec1",
    })
    start = time.monotonic()
    result = analyze(df, today=TODAY, threshold=5)
    elapsed = time.monotonic() - start
    assert len(result.flagged) == n
    assert elapsed < 15, f"50k rows took {elapsed:.1f}s"


def test_ac13_2_bom_semicolon_tab_extra_columns(tmp_path):
    base = ",".join(COLUMNS) + "\n" + ",".join(row("C1")) + "\n"
    bom = tmp_path / "bom.csv"
    bom.write_bytes(b"\xef\xbb\xbf" + base.encode("utf-8"))
    assert load_csv(bom).iloc[0]["candidate_id"] == "C1"

    semi = tmp_path / "semi.csv"
    semi.write_text(base.replace(",", ";"))
    assert load_csv(semi).iloc[0]["candidate_id"] == "C1"

    tab = tmp_path / "tab.csv"
    tab.write_text(base.replace(",", "\t"))
    assert load_csv(tab).iloc[0]["candidate_id"] == "C1"

    extra = tmp_path / "extra.csv"
    extra.write_text(
        ",".join(COLUMNS + ["ats_id", "notes"]) + "\n"
        + ",".join(row("C1") + ["ATS-1", "some note"]) + "\n")
    df = load_csv(extra)
    assert df.iloc[0]["candidate_id"] == "C1"
    result = analyze(df, today=TODAY, threshold=5)
    assert len(result.flagged) == 1


def test_ac13_3_missing_columns_listed(tmp_path):
    path = tmp_path / "bad.csv"
    make = pd.DataFrame([["C1", "Ada", "Engineer", "2026-10-01"]],
                        columns=["candidate_id", "name", "role",
                                 "stage_entered_date"])
    make.to_csv(path, index=False)
    try:
        load_csv(path)
        assert False, "expected an error"
    except ValueError as e:
        assert "stage" in str(e) and "owner" in str(e)


def test_ac13_4_header_only_and_headerless(tmp_path, capsys):
    header_only = tmp_path / "empty.csv"
    header_only.write_text(",".join(COLUMNS) + "\n")
    rc = main([str(header_only), "--today", "2026-10-11"])
    out = capsys.readouterr().out
    assert rc == 0 and "no data rows" in out.lower()

    headerless = tmp_path / "headerless.csv"
    headerless.write_text(",".join(row("C1")) + "\n")
    rc = main([str(headerless), "--today", "2026-10-11"])
    captured = capsys.readouterr()
    assert rc != 0 and "missing" in captured.err.lower()
    assert "Traceback" not in captured.err


def test_ac13_5_long_and_nonascii_passthrough():
    long_name = "Zoë Алексей 日本語 " + "x" * 5000
    df = pd.DataFrame([row("C1", name=long_name)], columns=COLUMNS)
    result = analyze(df, today=TODAY, threshold=5)
    assert result.flagged.iloc[0]["name"] == long_name
