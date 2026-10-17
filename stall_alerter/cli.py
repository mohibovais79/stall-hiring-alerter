"""Command line interface."""
import argparse
import sys
from datetime import date

import pandas as pd

from .core import COLUMNS, analyze
from .report import render


def _parse_stage_thresholds(entries):
    overrides = {}
    for entry in entries or []:
        stage, _, value = entry.partition("=")
        overrides[stage.strip()] = int(value)
    return overrides


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="stall-alerter",
        description="Flag candidates who have not moved stage.",
    )
    parser.add_argument("csv", help="path to the hiring board CSV export")
    parser.add_argument("--threshold", type=int, default=5,
                        help="default stall threshold in days (default: 5)")
    parser.add_argument("--stage-threshold", action="append", default=[],
                        metavar="STAGE=DAYS",
                        help="per-stage threshold override, repeatable")
    parser.add_argument("--output", metavar="PATH",
                        help="also write the flagged list to this CSV")
    parser.add_argument("--today", metavar="YYYY-MM-DD",
                        help="override 'today' (default: current date)")
    args = parser.parse_args(argv)

    try:
        today = date.fromisoformat(args.today) if args.today else date.today()
        df = pd.read_csv(args.csv)
        missing = [c for c in COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"missing required column(s): {', '.join(missing)}")
        analysis = analyze(
            df, today=today, threshold=args.threshold,
            stage_thresholds=_parse_stage_thresholds(args.stage_threshold),
        )
    except FileNotFoundError:
        print(f"error: file not found: {args.csv}", file=sys.stderr)
        return 2
    except (ValueError, KeyError, pd.errors.ParserError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(render(analysis))
    if args.output:
        analysis.flagged.to_csv(args.output, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
