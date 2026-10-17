"""Shared constants."""

STAGE_ORDER = ["Applied", "Screen", "Interview", "Final", "Offer"]
COLUMNS = ["candidate_id", "name", "role", "stage", "stage_entered_date", "owner"]
INACTIVE_STATUSES = {"hired", "rejected", "withdrawn", "on hold"}

DEFAULT_ACTIONS = {
    "Applied": "Send a status update to the candidate",
    "Screen": "Send a status update to the candidate",
    "Interview": "Chase the owner for interview feedback",
    "Final": "Chase the owner for a decision",
    "Offer": "Chase the owner on the offer",
}
