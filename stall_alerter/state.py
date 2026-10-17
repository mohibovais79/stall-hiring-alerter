"""Chase-state file: who was chased, when, and at which stage."""
import json
import os
from datetime import date
from pathlib import Path


class StateError(Exception):
    pass


def load_state(path):
    """Return the state dict; a missing file means empty state."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise StateError(f"corrupt state file {p}: {e}") from e
    if not isinstance(data, dict):
        raise StateError(f"corrupt state file {p}: expected a JSON object")
    return data


def mark_chased(path, candidate_id, stage, today):
    """Record that candidate_id was chased on `today` at `stage`."""
    p = Path(path)
    state = load_state(p)  # raises on corrupt state; never overwrites it
    state[candidate_id] = {"last_chased": today.isoformat(), "stage": stage}
    tmp = p.with_name(p.name + ".tmp")
    try:
        tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, p)
    finally:
        if tmp.exists():
            tmp.unlink()


def snooze_reason(row, state, today, window_days):
    """Return 'chased N days ago' when the row is inside the snooze window."""
    entry = state.get(str(row["candidate_id"]))
    if not entry:
        return None
    if entry.get("stage") != row["stage"]:
        return None  # moved to a new stage: snooze cleared
    try:
        last = date.fromisoformat(str(entry["last_chased"]))
    except (KeyError, ValueError):
        return None
    days = (today - last).days
    if 0 <= days < window_days:
        return f"chased {days} day{'s' if days != 1 else ''} ago"
    return None
