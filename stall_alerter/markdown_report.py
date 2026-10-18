"""Markdown report written to reports/YYYY-MM-DD.md (S14)."""
from pathlib import Path

import pandas as pd

FLAGGED_COLUMNS = [
    "candidate_id", "name", "role", "stage", "days_in_stage",
    "days_overdue", "reason", "action", "draft_source", "draft_status",
    "draft_text",
]
REJECTED_COLUMNS = ["candidate_id", "name", "stage", "reason"]
SNOOZED_COLUMNS = ["candidate_id", "name", "stage", "reason"]


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(df, columns):
    if df is None or df.empty:
        return "_None._\n"
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_cell(row[c]) for c in columns) + " |")
    return "\n".join(lines) + "\n"


def _summary(analysis):
    s = analysis.summary
    if s is None or s.total == 0:
        return "No flagged candidates.\n"
    lines = []
    for title, groups in (("By owner", s.owners), ("By stage", s.stages)):
        lines.append(f"**{title}**\n")
        for g in groups:
            mark = " BOTTLENECK" if g.bottleneck else ""
            lines.append(f"- {g.name}: {g.count} ({g.share:.0%}){mark}")
        lines.append("")
    return "\n".join(lines)


def render_markdown(analysis, today):
    inactive = len(analysis.inactive) if analysis.inactive is not None else 0
    return "\n".join([
        f"# Stall report {today.isoformat()}",
        "",
        f"Read {analysis.rows_read} rows: {len(analysis.flagged)} flagged, "
        f"{len(analysis.rejected)} rejected, {inactive} inactive.",
        "",
        "## Summary",
        "",
        _summary(analysis),
        "## Flagged",
        "",
        _table(analysis.flagged, FLAGGED_COLUMNS),
        "## Rejected",
        "",
        _table(analysis.rejected, REJECTED_COLUMNS),
        "## Snoozed",
        "",
        _table(analysis.snoozed if analysis.snoozed is not None
               else pd.DataFrame(), SNOOZED_COLUMNS),
    ])


def write_report(analysis, today, report_dir):
    """Write the report to <report_dir>/<today>.md and return its path."""
    directory = Path(report_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{today.isoformat()}.md"
    path.write_text(render_markdown(analysis, today), encoding="utf-8")
    return path
