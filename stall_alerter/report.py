"""Terminal report rendering."""
import pandas as pd

FLAGGED_COLUMNS = [
    "candidate_id", "name", "role", "stage",
    "days_in_stage", "days_overdue", "reason", "action",
    "draft_source", "draft_status", "draft_text",
]
REJECTED_COLUMNS = ["candidate_id", "name", "stage", "reason"]


def _table(df, columns):
    cols = [c for c in columns if c in df.columns]
    if df.empty:
        return "  (none)\n"
    widths = {c: max(len(c), *(len(str(v)) for v in df[c])) for c in cols}
    lines = ["  " + "  ".join(c.ljust(widths[c]) for c in cols)]
    for _, row in df.iterrows():
        lines.append("  " + "  ".join(str(row[c]).ljust(widths[c]) for c in cols))
    return "\n".join(lines) + "\n"


def _summary_lines(analysis):
    s = analysis.summary
    if s is None or s.total == 0:
        return ["  No flagged candidates.\n"]
    lines = []
    for title, groups in (("By owner", s.owners), ("By stage", s.stages)):
        lines.append(f"  {title}:")
        for g in groups:
            mark = "  BOTTLENECK" if g.bottleneck else ""
            lines.append(f"    {g.name}: {g.count} ({g.share:.0%}){mark}")
    return lines + [""]


def render(analysis):
    inactive = analysis.inactive if analysis.inactive is not None else []
    out = [
        f"Read {analysis.rows_read} rows: "
        f"{len(analysis.flagged)} flagged, {len(analysis.rejected)} rejected, "
        f"{len(inactive)} inactive",
        "",
        "SUMMARY",
        *_summary_lines(analysis),
        "FLAGGED",
        _table(analysis.flagged, FLAGGED_COLUMNS),
        "REJECTED",
        _table(analysis.rejected, REJECTED_COLUMNS),
    ]
    return "\n".join(out)
