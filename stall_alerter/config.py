"""TOML config file loading and validation.

Documented defaults (used when the file is missing):
- default_threshold: 5 days
- stage_order: Applied, Screen, Interview, Final, Offer
- stage_thresholds: none (default applies everywhere)
- aliases: none
- action_rules: DEFAULT_ACTIONS
- snooze_window_days: 3
- bottleneck_min_count: 3, bottleneck_min_pct: 0.5
- word_limit: 80
"""
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .constants import DEFAULT_ACTIONS, STAGE_ORDER

KNOWN_KEYS = {
    "default_threshold", "stage_thresholds", "stage_order", "aliases",
    "action_rules", "snooze_window_days", "bottleneck_min_count",
    "bottleneck_min_pct", "word_limit",
}


class ConfigError(Exception):
    pass


@dataclass
class Config:
    stage_order: list = field(default_factory=lambda: list(STAGE_ORDER))
    default_threshold: int | None = 5
    stage_thresholds: dict = field(default_factory=dict)
    aliases: dict = field(default_factory=dict)
    action_rules: dict = field(default_factory=lambda: dict(DEFAULT_ACTIONS))
    snooze_window_days: int = 3
    bottleneck_min_count: int = 3
    bottleneck_min_pct: float = 0.5
    word_limit: int = 80


def _nonneg_int(key, value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ConfigError(f"{key}: must be a non-negative integer, got {value!r}")


def load_config(path):
    """Return (Config, warnings). A missing file yields the defaults."""
    cfg = Config()
    warnings = []
    p = Path(path)
    if not p.exists():
        return cfg, warnings
    data = tomllib.loads(p.read_text(encoding="utf-8"))

    for key in data:
        if key not in KNOWN_KEYS:
            warnings.append(f"unknown config key '{key}'")

    if "stage_order" in data:
        order = data["stage_order"]
        if (not isinstance(order, list) or not order
                or not all(isinstance(s, str) for s in order)):
            raise ConfigError(
                "stage_order: must be a non-empty list of stage names")
        cfg.stage_order = order

    if "default_threshold" in data:
        _nonneg_int("default_threshold", data["default_threshold"])
        cfg.default_threshold = data["default_threshold"]

    for stage, value in (data.get("stage_thresholds") or {}).items():
        if stage not in cfg.stage_order:
            raise ConfigError(f"stage_thresholds: unknown stage '{stage}'")
        _nonneg_int(f"stage_thresholds.{stage}", value)
    cfg.stage_thresholds = dict(data.get("stage_thresholds") or {})

    for alias, target in (data.get("aliases") or {}).items():
        if target not in cfg.stage_order:
            raise ConfigError(f"aliases: '{alias}' -> unknown stage '{target}'")
    cfg.aliases = dict(data.get("aliases") or {})

    cfg.action_rules.update(data.get("action_rules") or {})
    missing = [s for s in cfg.stage_order if s not in cfg.action_rules]
    if missing:
        raise ConfigError(f"action_rules: no action for stage '{missing[0]}'")

    for key in ("snooze_window_days", "bottleneck_min_count", "word_limit"):
        if key in data:
            _nonneg_int(key, data[key])
            setattr(cfg, key, data[key])
    if "bottleneck_min_pct" in data:
        pct = data["bottleneck_min_pct"]
        if not isinstance(pct, (int, float)) or not 0 <= pct <= 1:
            raise ConfigError(
                f"bottleneck_min_pct: must be between 0 and 1, got {pct!r}")
        cfg.bottleneck_min_pct = pct

    return cfg, warnings
