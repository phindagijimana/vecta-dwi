"""Assemble a full Assessment and validate it against the output schema."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from .. import SCHEMA_VERSION, SPEC_VERSION, __version__ as VECTA_VERSION
from ..collectors.bids import BidsSession
from ..criteria.engine import evaluate as evaluate_criterion
from ..derive.reverse_pe import derive_reverse_pe_availability
from ..enums import (
    AssessmentState,
    CriterionStatus,
    ReadinessState,
    ValueState,
)
from ..extract.pe import (
    extract_pe_direction,
    extract_total_readout_time_present,
)
from ..models import (
    Assessment,
    AssessmentCompleteness,
    AssessmentStatus,
    DimensionState,
    Finding,
    ProfileRef,
    Provenance,
    ReadinessDimensions,
    ReadinessSummary,
    VariableResult,
)
from ..spec.loader import LoadedSpec


class OutputValidationError(Exception):
    pass


def assess_session(session: BidsSession, spec: LoadedSpec) -> Assessment:
    """Run the full first-vertical-slice pipeline for one BIDS session."""

    started = datetime.now(timezone.utc)
    profile_id = spec.profile["profile_id"]
    profile_version = spec.profile["version"]

    # Empty session (no dwi entities) → not_assessed
    if not session.dwi_entities:
        return _empty_assessment(session, spec, started, "no_dwi_entities_found")

    # For v0.1 we treat the first-listed non-reverse-PE-like entity as target.
    # A future revision should let the profile declare target selection rules.
    target = session.dwi_entities[0]

    # ── Extract ─────────────────────────────────────────────────────────
    variables: dict[str, VariableResult] = {}
    for extractor in (extract_pe_direction, extract_total_readout_time_present):
        vr = extractor(target)
        variables[vr.variable_id] = vr

    # ── Derive ──────────────────────────────────────────────────────────
    rev = derive_reverse_pe_availability(session, target)
    variables[rev.variable_id] = rev

    # ── Evaluate criteria ──────────────────────────────────────────────
    _finding_counter = [0]
    def next_finding_id() -> str:
        _finding_counter[0] += 1
        return f"finding-{_finding_counter[0]:04d}"

    criteria_results = []
    findings: list[Finding] = []

    for cid in spec.profile.get("criteria", []):
        criterion = spec.criteria[cid]
        # Only evaluate criteria whose required variables were extracted.
        # Others (e.g. stubs relying on VECTA-DWI-021's second variable
        # when we did extract it, that's fine; but future extensions might
        # hit missing variables — the engine will raise _EvalUnknown and
        # return status=unknown).
        result, f = evaluate_criterion(
            criterion=criterion,
            vars_=variables,
            profile_id=profile_id,
            finding_id_generator=next_finding_id,
            spec_version=spec.version,
        )
        criteria_results.append(result)
        findings.extend(f)

    # ── Readiness ─────────────────────────────────────────────────────
    readiness = _build_readiness(spec, criteria_results, findings, variables)

    completed = datetime.now(timezone.utc)

    unknown_criteria = sum(1 for c in criteria_results if c.status == CriterionStatus.UNKNOWN.value)
    state = (
        AssessmentState.COMPLETED_WITH_UNKNOWNS
        if unknown_criteria > 0
        else AssessmentState.COMPLETED
    )

    assessment = Assessment(
        schema_version=SCHEMA_VERSION,
        assessment_id=f"va-{uuid.uuid4()}",
        subject_id=session.subject_id,
        session_id=session.session_id,
        profile=ProfileRef(id=profile_id, version=profile_version),
        assessment_status=AssessmentStatus(
            state=state,
            started_at=started,
            completed_at=completed,
            domains_attempted=["scanner", "acquisition", "bids"],
            domains_completed=["acquisition"],  # first slice only touches acquisition-layer variables
        ),
        evidence=list(session.evidence),
        variables=variables,
        criteria=criteria_results,
        findings=findings,
        readiness=readiness,
        provenance=Provenance(
            vecta_software_version=VECTA_VERSION,
            specification_version=SPEC_VERSION,
            schema_version=SCHEMA_VERSION,
            profile_version=profile_version,
            executed_at=completed,
        ),
    )
    return assessment


def _empty_assessment(
    session: BidsSession, spec: LoadedSpec, started: datetime, reason: str
) -> Assessment:
    profile_id = spec.profile["profile_id"]
    profile_version = spec.profile["version"]
    now = datetime.now(timezone.utc)
    readiness = ReadinessSummary(
        profile_id=profile_id,
        profile_version=profile_version,
        state=ReadinessState.NOT_ASSESSED,
        dimensions=ReadinessDimensions(
            assessment_completeness=AssessmentCompleteness(
                applicable_variables=0,
                observed_or_derived=0,
                ratio=0.0,
                calculation_id="assessment_completeness_v1",
            )
        ),
        rule_version=spec.profile["readiness_rules"]["rule_version"],
        limitations=[reason],
    )
    return Assessment(
        schema_version=SCHEMA_VERSION,
        assessment_id=f"va-{uuid.uuid4()}",
        subject_id=session.subject_id,
        session_id=session.session_id,
        profile=ProfileRef(id=profile_id, version=profile_version),
        assessment_status=AssessmentStatus(
            state=AssessmentState.FAILED,
            started_at=started,
            completed_at=now,
            domains_attempted=[],
            domains_completed=[],
        ),
        readiness=readiness,
        provenance=Provenance(
            vecta_software_version=VECTA_VERSION,
            specification_version=SPEC_VERSION,
            schema_version=SCHEMA_VERSION,
            profile_version=profile_version,
            executed_at=now,
        ),
    )


def _build_readiness(
    spec: LoadedSpec,
    criteria_results,
    findings: list[Finding],
    variables: dict[str, VariableResult],
) -> ReadinessSummary:
    profile_id = spec.profile["profile_id"]
    profile_version = spec.profile["version"]
    rules = spec.profile["readiness_rules"]
    blocking_ids = set(rules.get("blocking_criteria", []))
    review_ids = set(rules.get("review_criteria", []))

    findings_by_criterion = {}
    for f in findings:
        findings_by_criterion.setdefault(f.criterion_id, []).append(f.finding_id)

    blocking_findings = [
        fid for cid, fids in findings_by_criterion.items() if cid in blocking_ids for fid in fids
    ]
    review_findings = [
        fid for cid, fids in findings_by_criterion.items() if cid in review_ids for fid in fids
    ]

    # Also treat unknown criteria that live in review_criteria as review-required
    for cr in criteria_results:
        if cr.status == CriterionStatus.UNKNOWN.value and cr.criterion_id in review_ids:
            # Add a synthetic review flag via limitations, no finding is emitted
            pass

    if blocking_findings:
        state = ReadinessState.NOT_READY
    elif review_findings or any(
        cr.status == CriterionStatus.UNKNOWN.value and cr.criterion_id in review_ids
        for cr in criteria_results
    ):
        state = ReadinessState.REVIEW_REQUIRED
    elif findings:
        state = ReadinessState.READY_WITH_LIMITATIONS
    else:
        state = ReadinessState.READY

    applicable = len(variables)
    observed_or_derived = sum(
        1 for v in variables.values()
        if v.state in (ValueState.OBSERVED.value, ValueState.DERIVED.value)
    )
    unknown = sum(1 for v in variables.values() if v.state == ValueState.UNKNOWN.value)

    evaluable = sum(
        1 for cr in criteria_results
        if cr.status in (CriterionStatus.SATISFIED.value, CriterionStatus.FINDING.value)
    )
    unknown_criteria = sum(
        1 for cr in criteria_results if cr.status == CriterionStatus.UNKNOWN.value
    )

    completeness_ratio = observed_or_derived / applicable if applicable else 0.0

    return ReadinessSummary(
        profile_id=profile_id,
        profile_version=profile_version,
        state=state,
        dimensions=ReadinessDimensions(
            processing_readiness=DimensionState(
                state=state,
                contributing_findings=blocking_findings + review_findings,
            ),
            assessment_completeness=AssessmentCompleteness(
                applicable_variables=applicable,
                observed_or_derived=observed_or_derived,
                unknown=unknown,
                evaluable_criteria=evaluable,
                unknown_criteria=unknown_criteria,
                ratio=round(completeness_ratio, 4),
                calculation_id="assessment_completeness_v1",
            ),
        ),
        blocking_finding_refs=blocking_findings,
        review_finding_refs=review_findings,
        rule_version=rules["rule_version"],
    )


# ── Serialization + validation ─────────────────────────────────────────


def _build_output_registry(schema_root: Path) -> Registry:
    reg = Registry()
    for f in schema_root.rglob("*.schema.json"):
        doc = json.loads(f.read_text())
        if doc.get("$id"):
            reg = reg.with_resource(doc["$id"], Resource(contents=doc, specification=DRAFT202012))
        reg = reg.with_resource(
            "file://" + str(f.resolve()),
            Resource(contents=doc, specification=DRAFT202012),
        )
    return reg


def to_dict(assessment: Assessment) -> dict[str, Any]:
    """Pydantic → JSON-safe dict, enums as values, datetimes as ISO strings.

    exclude_none=True drops unset optional fields so the strict output schema
    (which types those fields as `object` when present, not `null`) validates.
    Two exceptions: VariableResult.value and DerivedMetric.value are schema-
    required properties whose semantic value is legitimately null when
    state=unknown/not_applicable/etc., so we reinsert them after the drop.
    """
    d = json.loads(assessment.model_dump_json(exclude_none=True))
    for v in d.get("variables", {}).values():
        v.setdefault("value", None)
    for m in d.get("derived_metrics", {}).values():
        m.setdefault("value", None)
    return d


def validate_against_schema(payload: dict[str, Any], schema_root: Path) -> None:
    """Raise OutputValidationError if payload does not conform to vecta_output.schema.json."""
    top = json.loads((schema_root / "output/vecta_output.schema.json").read_text())
    registry = _build_output_registry(schema_root)
    validator = Draft202012Validator(top, registry=registry)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if errors:
        lines = ["Output validation failed:"]
        for e in errors[:20]:
            loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
            lines.append(f"  at {loc}: {e.message}")
        if len(errors) > 20:
            lines.append(f"  ...and {len(errors) - 20} more")
        raise OutputValidationError("\n".join(lines))


def check_referential_integrity(payload: dict[str, Any]) -> None:
    """Every ID reference in the payload must resolve. Source: Output Tech Spec §46."""
    evidence_ids = {e["evidence_id"] for e in payload.get("evidence", [])}
    variable_ids = set(payload.get("variables", {}).keys())
    finding_ids = {f["finding_id"] for f in payload.get("findings", [])}
    criterion_ids_in_findings = {f["criterion_id"] for f in payload.get("findings", [])}

    problems = []

    # Evidence refs from variables + findings
    for vid, v in payload.get("variables", {}).items():
        for eref in v.get("evidence_refs", []):
            if eref not in evidence_ids:
                problems.append(f"variable {vid} references missing evidence {eref}")
    for f in payload.get("findings", []):
        for eref in f.get("evidence_refs", []):
            if eref not in evidence_ids:
                # It's legitimate for findings to reference evidence registry
                # IDs (EV-*) that are not per-session evidence records; skip
                # those.
                if not eref.startswith(("EV-", "ev-registry-")):
                    problems.append(f"finding {f['finding_id']} references missing evidence {eref}")
        for vref in f.get("variable_refs", []):
            if vref not in variable_ids:
                problems.append(f"finding {f['finding_id']} references missing variable {vref}")

    # Criterion → finding refs
    for cr in payload.get("criteria", []):
        for fref in cr.get("finding_refs", []):
            if fref not in finding_ids:
                problems.append(f"criterion {cr['criterion_id']} references missing finding {fref}")

    # Readiness → finding refs
    for fref in payload.get("readiness", {}).get("blocking_finding_refs", []) + payload.get("readiness", {}).get("review_finding_refs", []):
        if fref not in finding_ids:
            problems.append(f"readiness references missing finding {fref}")

    if problems:
        raise OutputValidationError("Referential integrity failed:\n  " + "\n  ".join(problems))
