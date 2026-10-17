"""Command line interface."""
import argparse
import sys
from datetime import date

import pandas as pd

from .config import ConfigError, load_config
from .core import analyze
from .explain import explain
from .io import load_csv
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
    parser.add_argument("--config", metavar="PATH",
                        default="stall-alerter.toml",
                        help="config file (default: %(default)s; missing = defaults)")
    parser.add_argument("--threshold", type=int, default=None,
                        help="default stall threshold in days (overrides config)")
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
    parser.add_argument("--snooze-window", type=int, default=None,
                        help="days a chased candidate stays snoozed")
    parser.add_argument("--mark-chased", metavar="CANDIDATE_ID",
                        help="record a candidate as chased today and exit")
    parser.add_argument("--explain", metavar="CANDIDATE_ID",
                        help="explain one candidate's result and exit")
    args = parser.parse_args(argv)

    try:
        cfg, cfg_warnings = load_config(args.config)
        for warning in cfg_warnings:
            print(f"warning: {warning}", file=sys.stderr)
        today = date.fromisoformat(args.today) if args.today else date.today()
        df = load_csv(args.csv)
        if df.empty:
            print(f"No data rows in {args.csv}.")

        if args.mark_chased:
            rows = df[df["candidate_id"].astype(str) == args.mark_chased]
            if rows.empty:
                raise ValueError(
                    f"candidate not found: {args.mark_chased}")
            stage, _ = normalize_stage(
                rows.iloc[0]["stage"], cfg.aliases, cfg.stage_order)
            mark_chased(args.state, args.mark_chased, stage, today)
            print(f"Marked {args.mark_chased} as chased on {today}.")
            return 0

        # Precedence: CLI option > config file > built-in defaults.
        analysis = analyze(
            df, today=today,
            threshold=(args.threshold if args.threshold is not None
                       else cfg.default_threshold),
            stage_thresholds={**cfg.stage_thresholds,
                              **_parse_stage_thresholds(args.stage_threshold)},
            action_rules=cfg.action_rules, aliases=cfg.aliases,
            stage_order=cfg.stage_order, word_limit=cfg.word_limit,
            state=load_state(args.state),
            snooze_window_days=(args.snooze_window
                                if args.snooze_window is not None
                                else cfg.snooze_window_days),
            bottleneck_min_count=cfg.bottleneck_min_count,
            bottleneck_min_pct=cfg.bottleneck_min_pct,
        )
    except FileNotFoundError:
        print(f"error: file not found: {args.csv}", file=sys.stderr)
        return 2
    except (ValueError, KeyError, StateError, ConfigError,
            pd.errors.ParserError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.explain:
        try:
            print(explain(analysis, args.explain))
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        return 0

    print(render(analysis))
    if args.output:
        analysis.flagged.to_csv(args.output, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
