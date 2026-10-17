"""CSV loading: encoding, delimiter sniffing, column validation."""
import pandas as pd

from .constants import COLUMNS

_DELIMITERS = (",", ";", "\t")


def _sniff_delimiter(sample):
    header = next((l for l in sample.splitlines() if l.strip()), "")
    counts = {d: header.count(d) for d in _DELIMITERS}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def load_csv(path):
    """Read a hiring-board CSV into a DataFrame with required columns."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(8192)
    if not sample.strip():
        raise ValueError("empty file: no header row")
    df = pd.read_csv(path, encoding="utf-8-sig",
                     sep=_sniff_delimiter(sample))
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")
    return df
