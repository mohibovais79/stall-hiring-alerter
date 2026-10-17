"""Input normalisation for messy CSV exports.

Date rules (documented per AC9.1):
- YYYY-MM-DD and ISO timestamps (with or without timezone offsets) parse as
  ISO. Timestamps are converted to a UTC calendar date before day counting.
- Dates containing "/" are always read day-first (DD/MM/YYYY), including
  ambiguous ones like 05/06/2026 (-> 5 June 2026).
"""
import pandas as pd

from .constants import INACTIVE_STATUSES, STAGE_ORDER

_MISSING = {"", "nan", "nat", "none", "null"}


def parse_stage_entered(raw):
    """Return (date, note) or (None, None) when missing/malformed."""
    text = str(raw).strip()
    if text.lower() in _MISSING:
        return None, None
    if "/" in text:
        ts = pd.to_datetime(text, dayfirst=True, errors="coerce")
        note = f"date '{text}' parsed as day-first"
    else:
        ts = pd.to_datetime(text, errors="coerce", utc=True)
        note = (f"timestamp '{text}' converted to UTC"
                if "T" in text or ":" in text else None)
    if pd.isna(ts):
        return None, None
    return ts.date(), note


def normalize_stage(raw, aliases=None):
    """Return (canonical_stage, note); (None, None) when unknown."""
    text = str(raw).strip()
    canonical = {s.lower(): s for s in STAGE_ORDER}
    key = text.lower()
    if key in canonical:
        note = (f"stage '{raw}' normalised to '{canonical[key]}'"
                if text != canonical[key] else None)
        return canonical[key], note
    alias_map = {str(k).strip().lower(): v for k, v in (aliases or {}).items()}
    if key in alias_map and alias_map[key] in STAGE_ORDER:
        return alias_map[key], f"stage '{raw}' mapped via alias to '{alias_map[key]}'"
    return None, None


def is_inactive(raw_status):
    return str(raw_status or "").strip().lower() in INACTIVE_STATUSES
