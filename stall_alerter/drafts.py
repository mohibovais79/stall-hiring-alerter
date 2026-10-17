"""Follow-up draft generation via an injectable LLM client."""
from dataclasses import dataclass
from typing import Protocol

WORD_LIMIT = 80
CANDIDATE_STAGES = {"Applied", "Screen"}


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


@dataclass
class Draft:
    text: str
    source: str  # "AI" or "template"
    addressed_to: str
    status: str = "needs review"


def recipient_for(row):
    """Candidate for early stages, owner for late stages."""
    return row["name"] if row["stage"] in CANDIDATE_STAGES else row["owner"]


def template_text(row, to):
    return (
        f"Hi {to}, {row['name']} has been in {row['stage']} for "
        f"{row['days_in_stage']} days for the {row['role']} role "
        f"({row['days_overdue']} over the {row['threshold']}-day limit). "
        "Please follow up."
    )


def _prompt(row, to):
    return (
        f"Write a short follow-up message (under 80 words) to {to} about "
        f"{row['name']}, a {row['role']} candidate who has been in "
        f"{row['stage']} for {row['days_in_stage']} days. "
        "Use only these facts."
    )


def draft_for(row, client=None, word_limit=WORD_LIMIT):
    """One draft for one flagged row; falls back to the template."""
    to = recipient_for(row)
    if client is not None:
        try:
            text = client.complete(_prompt(row, to))
        except Exception:
            text = None
        if text and text.strip() and len(text.split()) <= word_limit:
            return Draft(text=text.strip(), source="AI", addressed_to=to)
    return Draft(text=template_text(row, to), source="template", addressed_to=to)
