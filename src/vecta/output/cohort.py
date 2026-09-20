"""Cohort aggregation across multiple Assessment payloads.

Emits the artifacts declared in Output Tech Spec §31-33 and Output
Dictionary §22-23:

  - session_summary  (one row per session)
  - findings_long    (one row per finding per session)
  - variables_long   (long-form state matrix)
  - finding_prevalence (numerators and 3 denominators per §32)
  - missingness_matrix

Denominators for finding prevalence are explicit and NOT interchangeable
(Output Tech Spec §32):
  - triggered / all assessed sessions
  - triggered / sessions where criterion was applicable
  - triggered / sessions where criterion was evaluable
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from . import tsv as tsv_module


@dataclass
class CohortSummary:
    """One structured cohort result. Serialize to TSV via `render_*`."""
    aggregation_version: str = "0.1.0"
    input_schema_version: str = "0.1.0"
    assessed_sessions: int = 0
    completed_sessions: int = 0
    session_summaries: list[dict[str, str]] = field(default_factory=list)
    findings_long: list[dict[str, str]] = field(default_factory=list)
    variables_long: list[dict[str, str]] = field(default_factory=list)
    finding_prevalence: list[dict[str, str]] = field(default_factory=list)
    missingness_matrix: list[dict[str, str]] = field(default_factory=list)


def _tsv(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["\t".join(columns)]
    for r in rows:
        lines.append("\t".join(r.get(c, "NA") for c in columns))
    return "\n".join(lines) + "\n"


def aggregate(payloads: list[dict[str, Any]]) -> CohortSummary:
    """Aggregate a list of per-session Assessment payloads into a
    structured cohort summary. Does not write files — the caller decides
    where to write them."""
    cohort = CohortSummary()
    cohort.assessed_sessions = len(payloads)
    cohort.completed_sessions = sum(
        1 for p in payloads
        if p.get("assessment_status", {}).get("state", "").startswith("completed")
    )

    # Per-session summaries (delegate row-projection to tsv module)
    for p in payloads:
        cohort.session_summaries.append(tsv_module.to_row(p))

    # Findings long: one row per finding per session
    for p in payloads:
        sid = p.get("session_id")
        subj = p.get("subject_id")
        for f in p.get("findings", []):
            cohort.findings_long.append({
                "session_id": sid,
                "subject_id": subj,
                "finding_id": f.get("finding_id"),
                "criterion_id": f.get("criterion_id"),
                "criterion_version": f.get("criterion_version"),
                "category": f.get("category"),
                "severity": f.get("severity"),
                "severity_status": f.get("severity_status"),
                "confidence": f.get("confidence"),
                "lifecycle_origin": f.get("lifecycle_origin"),
                "label": f.get("label"),
            })

    # Variables long: one row per variable per session
    for p in payloads:
        sid = p.get("session_id")
        subj = p.get("subject_id")
        for vid, v in p.get("variables", {}).items():
            cohort.variables_long.append({
                "session_id": sid,
                "subject_id": subj,
                "variable_id": vid,
                "value": tsv_module._fmt(v.get("value")),
                "state": v.get("state"),
                "confidence": v.get("confidence"),
            })

    # Finding prevalence — three explicit denominators per §32
    per_criterion_triggered: dict[str, int] = defaultdict(int)
    per_criterion_evaluated: dict[str, int] = defaultdict(int)
    per_criterion_applicable: dict[str, int] = defaultdict(int)
    for p in payloads:
        seen_this_session: set[str] = set()
        for c in p.get("criteria", []):
            cid = c["criterion_id"]
            if cid in seen_this_session:
                continue
            seen_this_session.add(cid)
            status = c.get("status")
            if status in ("satisfied", "finding"):
                per_criterion_evaluated[cid] += 1
                per_criterion_applicable[cid] += 1
            elif status == "unknown":
                per_criterion_applicable[cid] += 1   # applicable but unevaluable
            # not_applicable and error are excluded from both denominators
            if status == "finding":
                per_criterion_triggered[cid] += 1

    all_criterion_ids = (
        set(per_criterion_triggered)
        | set(per_criterion_evaluated)
        | set(per_criterion_applicable)
    )
    for cid in sorted(all_criterion_ids):
        tri = per_criterion_triggered[cid]
        applicable = per_criterion_applicable[cid]
        evaluated = per_criterion_evaluated[cid]
        assessed = cohort.assessed_sessions

        def _ratio(n, d):
            return f"{(n/d):.4f}" if d else "NA"

        cohort.finding_prevalence.append({
            "criterion_id": cid,
            "triggered": str(tri),
            "assessed_sessions": str(assessed),
            "applicable_sessions": str(applicable),
            "evaluable_sessions": str(evaluated),
            "prevalence_over_assessed": _ratio(tri, assessed),
            "prevalence_over_applicable": _ratio(tri, applicable),
            "prevalence_over_evaluable": _ratio(tri, evaluated),
        })

    # Missingness matrix: (session, variable, state, value_present)
    for p in payloads:
        sid = p.get("session_id")
        for vid, v in p.get("variables", {}).items():
            cohort.missingness_matrix.append({
                "session_id": sid,
                "variable_id": vid,
                "state": v.get("state"),
                "value_present": "1" if v.get("value") is not None else "0",
            })

    return cohort


def render_session_summary(cohort: CohortSummary) -> str:
    columns = [name for name, _ in tsv_module.COLUMNS]
    return _tsv(cohort.session_summaries, columns)


def render_findings_long(cohort: CohortSummary) -> str:
    columns = [
        "session_id", "subject_id", "finding_id", "criterion_id",
        "criterion_version", "category", "severity", "severity_status",
        "confidence", "lifecycle_origin", "label",
    ]
    return _tsv(cohort.findings_long, columns)


def render_variables_long(cohort: CohortSummary) -> str:
    columns = ["session_id", "subject_id", "variable_id", "value", "state", "confidence"]
    return _tsv(cohort.variables_long, columns)


def render_finding_prevalence(cohort: CohortSummary) -> str:
    columns = [
        "criterion_id", "triggered",
        "assessed_sessions", "applicable_sessions", "evaluable_sessions",
        "prevalence_over_assessed", "prevalence_over_applicable", "prevalence_over_evaluable",
    ]
    return _tsv(cohort.finding_prevalence, columns)


def render_missingness_matrix(cohort: CohortSummary) -> str:
    columns = ["session_id", "variable_id", "state", "value_present"]
    return _tsv(cohort.missingness_matrix, columns)
