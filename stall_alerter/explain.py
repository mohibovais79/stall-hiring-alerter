"""Per-candidate explanation built from the analysis trace."""


def explain(analysis, candidate_id):
    """Explain how one candidate was classified and ranked."""
    trace = analysis.traces.get(str(candidate_id))
    if trace is None:
        raise ValueError(f"unknown candidate_id: {candidate_id}")
    rec = trace.get("record") or {}
    lines = [
        f"Candidate {candidate_id}: {rec.get('name', '?')} — {rec.get('role', '?')}",
        f"Stage: {rec.get('stage', '?')}",
    ]
    if "days_in_stage" in rec:
        lines += [
            f"Days in stage: {rec['days_in_stage']}",
            f"Threshold: {rec['threshold']} ({rec['threshold_source']})",
            f"Days overdue: {rec['days_overdue']}",
        ]
    if trace["outcome"] == "flagged":
        lines.append(f"Rank: {trace['rank']}")
        lines.append(
            f"Action: {rec.get('action')} (rule for stage '{rec.get('stage')}')")
        lines.append("Outcome: flagged")
    else:
        reason = trace.get("reason")
        suffix = f" — {reason}" if reason else ""
        lines.append(f"Outcome: not flagged ({trace['outcome']}{suffix})")
    notes = rec.get("normalizations") or []
    if notes:
        lines.append("Normalisations: " + "; ".join(notes))
    for reason in trace.get("rejected_rows", []):
        lines.append(f"Also rejected: {reason}")
    return "\n".join(lines)
