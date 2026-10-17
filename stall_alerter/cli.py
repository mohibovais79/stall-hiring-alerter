"""Command line interface."""
import argparse
import sys
from datetime import date

import pandas as pd

from .core import COLUMNS, analyze
from .normalize import normalize_stage
from .report import render
from .state import StateError, load_state, mark_chased


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
    parser.add_argument("--state", metavar="PATH",
                        default=".stall-alerter-state.json",
                        help="chase-state file (default: %(default)s)")
    parser.add_argument("--snooze-window", type=int, default=3,
                        help="days a chased candidate stays snoozed")
    parser.add_argument("--mark-chased", metavar="CANDIDATE_ID",
                        help="record a candidate as chased today and exit")
    args = parser.parse_args(argv)

    try:
        today = date.fromisoformat(args.today) if args.today else date.today()
        df = pd.read_csv(args.csv)
        missing = [c for c in COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"missing required column(s): {', '.join(missing)}")

        if args.mark_chased:
            rows = df[df["candidate_id"].astype(str) == args.mark_chased]
            if rows.empty:
                raise ValueError(
                    f"candidate not found: {args.mark_chased}")
            stage, _ = normalize_stage(rows.iloc[0]["stage"])
            mark_chased(args.state, args.mark_chased, stage, today)
            print(f"Marked {args.mark_chased} as chased on {today}.")
            return 0

        analysis = analyze(
            df, today=today, threshold=args.threshold,
            stage_thresholds=_parse_stage_thresholds(args.stage_threshold),
            state=load_state(args.state),
            snooze_window_days=args.snooze_window,
        )
    except FileNotFoundError:
        print(f"error: file not found: {args.csv}", file=sys.stderr)
        return 2
    except (ValueError, KeyError, StateError, pd.errors.ParserError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(render(analysis))
    if args.output:
        analysis.flagged.to_csv(args.output, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
