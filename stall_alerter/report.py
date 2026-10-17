"""Terminal report rendering."""
import pandas as pd

FLAGGED_COLUMNS = [
    "candidate_id", "name", "role", "stage",
    "days_in_stage", "days_overdue", "reason", "action",
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


def render(analysis):
    out = [
        f"Read {analysis.rows_read} rows: "
        f"{len(analysis.flagged)} flagged, {len(analysis.rejected)} rejected",
        "",
        "FLAGGED",
        _table(analysis.flagged, FLAGGED_COLUMNS),
        "REJECTED",
        _table(analysis.rejected, REJECTED_COLUMNS),
    ]
    return "\n".join(out)
