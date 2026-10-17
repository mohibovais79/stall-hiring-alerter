"""S12: Configure instead of hardcode."""
import pytest
import pandas as pd

from stall_alerter.cli import main
from stall_alerter.config import ConfigError, load_config
from stall_alerter.constants import DEFAULT_ACTIONS, STAGE_ORDER
from stall_alerter.core import analyze

COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]

FULL_TOML = """
default_threshold = 7
snooze_window_days = 4
bottleneck_min_count = 2
bottleneck_min_pct = 0.25
word_limit = 60
stage_order = ["Applied", "Screen", "Interview", "Final", "Offer"]

[stage_thresholds]
Offer = 2

[aliases]
"Phone Screen" = "Screen"

[action_rules]
Applied = "nudge candidate"
Screen = "nudge candidate"
Interview = "custom interview rule"
Final = "chase final"
Offer = "chase offer"
"""


def make_df(rows, columns=COLUMNS):
    return pd.DataFrame(rows, columns=columns)


def row(candidate_id, stage="Interview", entered="2026-10-07", owner="rec1"):
    return [candidate_id, "Ada Lovelace", "Engineer", stage, entered, owner]


def test_ac12_1_all_settings_from_one_file(tmp_path):
    path = tmp_path / "c.toml"
    path.write_text(FULL_TOML)
    cfg, warnings = load_config(path)
    assert cfg.default_threshold == 7
    assert cfg.snooze_window_days == 4
    assert cfg.bottleneck_min_count == 2
    assert cfg.bottleneck_min_pct == 0.25
    assert cfg.word_limit == 60
    assert cfg.stage_order == STAGE_ORDER
    assert cfg.stage_thresholds == {"Offer": 2}
    assert cfg.aliases == {"Phone Screen": "Screen"}
    assert cfg.action_rules["Interview"] == "custom interview rule"

    df = make_df([row("C1", stage="Phone Screen", entered="2026-10-01")])
    result = analyze(df, today=__import__("datetime").date(2026, 10, 11),
                     threshold=cfg.default_threshold,
                     stage_thresholds=cfg.stage_thresholds,
                     aliases=cfg.aliases, action_rules=cfg.action_rules,
                     stage_order=cfg.stage_order)
    flagged = result.flagged.iloc[0]
    assert flagged["stage"] == "Screen"
    assert flagged["action"] == "nudge candidate"


def test_ac12_2_missing_file_defaults(tmp_path):
    cfg, warnings = load_config(tmp_path / "missing.toml")
    assert cfg.default_threshold == 5
    assert cfg.stage_order == STAGE_ORDER
    assert cfg.action_rules == DEFAULT_ACTIONS
    assert warnings == []


def test_ac12_3_validation_names_field(tmp_path):
    bad = tmp_path / "bad1.toml"
    bad.write_text("default_threshold = -1\n")
    with pytest.raises(ConfigError, match="default_threshold"):
        load_config(bad)

    bad.write_text('[aliases]\n"Phone Screen" = "Nope"\n')
    with pytest.raises(ConfigError, match="unknown stage 'Nope'"):
        load_config(bad)

    bad.write_text(
        'stage_order = ["Applied", "Screen", "Interview", "Final", "Offer", '
        '"Onboarding"]\n')
    with pytest.raises(ConfigError, match="Onboarding"):
        load_config(bad)


def test_ac12_4_cli_beats_config_beats_default(tmp_path, capsys):
    csv = tmp_path / "board.csv"
    make_df([row("C1")]).to_csv(csv, index=False)  # 4 days in Interview
    cfg = tmp_path / "c.toml"
    cfg.write_text("default_threshold = 10\n")

    rc = main([str(csv), "--config", str(cfg), "--today", "2026-10-11"])
    assert rc == 0
    assert "C1" not in capsys.readouterr().out.split("FLAGGED")[1].split("REJECTED")[0]

    rc = main([str(csv), "--config", str(cfg), "--today", "2026-10-11",
               "--threshold", "2"])
    assert rc == 0
    assert "C1" in capsys.readouterr().out


def test_ac12_5_unknown_keys_warn(tmp_path):
    path = tmp_path / "c.toml"
    path.write_text('mystery_key = 1\ndefault_threshold = 5\n')
    cfg, warnings = load_config(path)
    assert any("mystery_key" in w for w in warnings)
    assert cfg.default_threshold == 5
