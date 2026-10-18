"""S6: Run it easily."""
import pandas as pd
import pytest

from stall_alerter.cli import main

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]


@pytest.fixture(autouse=True)
def _isolate_reports(tmp_path, monkeypatch):
    # S14 writes reports/ relative to the working directory; keep tests out of the repo.
    monkeypatch.chdir(tmp_path)


def write_csv(tmp_path, rows, name="board.csv"):
    path = tmp_path / name
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)
    return str(path)


def row(candidate_id="C1", stage="Interview", entered="2026-10-01"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, "recruiter1"]


def test_ac6_1_cli_takes_csv_and_threshold_options(tmp_path, capsys):
    csv = write_csv(tmp_path, [row("C1", "Offer", "2026-10-07")])
    rc = main([csv, "--today", "2026-10-11", "--threshold", "5",
               "--stage-threshold", "Offer=3"])
    assert rc == 0
    assert "C1" in capsys.readouterr().out


def test_ac6_2_readable_table_and_csv_output(tmp_path, capsys):
    csv = write_csv(tmp_path, [row("C1", "Interview", "2026-10-01")])
    out_csv = str(tmp_path / "out.csv")
    rc = main([csv, "--today", "2026-10-11", "--threshold", "5",
               "--output", out_csv])
    assert rc == 0
    stdout = capsys.readouterr().out
    assert "candidate_id" in stdout and "days" in stdout
    written = pd.read_csv(out_csv)
    assert list(written["candidate_id"]) == ["C1"]


def test_ac6_3_missing_file_clear_error(capsys):
    rc = main(["nonexistent.csv", "--today", "2026-10-11"])
    captured = capsys.readouterr()
    assert rc != 0
    assert "not found" in captured.err.lower()
    assert "Traceback" not in captured.err


def test_ac6_3_missing_columns_clear_error(tmp_path, capsys):
    path = tmp_path / "bad.csv"
    pd.DataFrame([["C1", "Ada", "2026-10-01"]],
                 columns=["candidate_id", "name", "stage_entered_date"],
                 ).to_csv(path, index=False)
    rc = main([str(path), "--today", "2026-10-11"])
    captured = capsys.readouterr()
    assert rc != 0
    assert "stage" in captured.err
    assert "Traceback" not in captured.err
