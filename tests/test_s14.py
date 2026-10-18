"""S14: Keep a dated markdown report."""
from datetime import date

import pandas as pd

from stall_alerter.cli import main

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
TODAY = "2026-10-18"


def write_csv(tmp_path, rows, name="board.csv"):
    path = tmp_path / name
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)
    return str(path)


def row(candidate_id="C1", name="Ada Lovelace", stage="Interview",
        entered="2026-10-01", owner="rec1"):
    return [candidate_id, name, "Engineer", stage, entered, owner]


def test_ac14_1_default_location_and_dated_name(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    csv = write_csv(tmp_path, [row("C1")])
    rc = main([csv, "--today", TODAY, "--threshold", "5"])
    assert rc == 0
    report = tmp_path / "reports" / "2026-10-18.md"
    assert report.exists()


def test_ac14_1_explain_run_writes_no_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    csv = write_csv(tmp_path, [row("C1")])
    main([csv, "--today", TODAY, "--threshold", "5", "--explain", "C1"])
    assert not (tmp_path / "reports").exists()


def test_ac14_2_report_dir_option(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    csv = write_csv(tmp_path, [row("C1")])
    custom = tmp_path / "custom"
    rc = main([csv, "--today", TODAY, "--threshold", "5",
               "--report-dir", str(custom)])
    assert rc == 0
    assert (custom / "2026-10-18.md").exists()
    assert not (tmp_path / "reports").exists()


def test_ac14_3_report_has_title_counts_and_sections(tmp_path, capsys):
    csv = write_csv(tmp_path, [
        row("C1", entered="2026-10-01"),   # 17 days, flagged
        row("C2", entered="garbage"),      # rejected
    ])
    rdir = tmp_path / "out"
    main([csv, "--today", TODAY, "--threshold", "5", "--report-dir", str(rdir)])
    text = (rdir / "2026-10-18.md").read_text(encoding="utf-8")
    assert text.startswith("# ")
    assert "2026-10-18" in text
    assert "1 flagged" in text and "1 rejected" in text and "0 inactive" in text
    for heading in ("## Summary", "## Flagged", "## Rejected", "## Snoozed"):
        assert heading in text


def test_ac14_4_flagged_rows_in_rank_order(tmp_path, capsys):
    csv = write_csv(tmp_path, [
        row("C2", entered="2026-10-07"),   # 11 days, 6 over
        row("C1", entered="2026-09-27"),   # 21 days, 16 over
    ])
    rdir = tmp_path / "out"
    main([csv, "--today", TODAY, "--threshold", "5", "--report-dir", str(rdir)])
    text = (rdir / "2026-10-18.md").read_text(encoding="utf-8")
    assert text.index("| C1 |") < text.index("| C2 |")


def test_ac14_5_pipes_escaped_and_utf8(tmp_path, capsys):
    csv = write_csv(tmp_path, [
        row("C1", name="Smith | Jones Zoë 田中", entered="2026-10-01"),
    ])
    rdir = tmp_path / "out"
    main([csv, "--today", TODAY, "--threshold", "5", "--report-dir", str(rdir)])
    text = (rdir / "2026-10-18.md").read_text(encoding="utf-8")
    assert "Smith \\| Jones Zoë 田中" in text


def test_ac14_6_empty_run_still_writes_report(tmp_path, capsys):
    csv = write_csv(tmp_path, [row("C1", entered="2026-10-16")])  # 2 days
    rdir = tmp_path / "out"
    main([csv, "--today", TODAY, "--threshold", "5", "--report-dir", str(rdir)])
    text = (rdir / "2026-10-18.md").read_text(encoding="utf-8")
    assert "No flagged candidates" in text


def test_ac14_1_report_written_even_if_terminal_print_fails(tmp_path, monkeypatch):
    import stall_alerter.cli as cli

    def broken_render(analysis):
        raise UnicodeEncodeError("charmap", "x", 0, 1, "cannot encode")

    monkeypatch.setattr(cli, "render", broken_render)
    csv = write_csv(tmp_path, [row("C1", entered="2026-10-01")])
    rdir = tmp_path / "out"
    try:
        main([csv, "--today", TODAY, "--threshold", "5", "--report-dir", str(rdir)])
    except UnicodeEncodeError:
        pass
    assert (rdir / "2026-10-18.md").exists()


def test_ac14_7_terminal_output_unchanged(tmp_path, capsys):
    csv = write_csv(tmp_path, [row("C1", entered="2026-10-01")])
    rc = main([csv, "--today", TODAY, "--threshold", "5",
               "--report-dir", str(tmp_path / "out")])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.startswith("Read 1 rows: 1 flagged")
    assert "SUMMARY" in out and "FLAGGED" in out and "REJECTED" in out
