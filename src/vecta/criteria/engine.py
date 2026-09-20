"""Criteria evaluation engine.

Evaluates the declarative condition tree declared in a criterion spec
against a mapping of variable_id → VariableResult. Returns a
CriterionResult and, if triggered, a Finding assembled from the criterion
finding-template.

Supports the subset of predicates used by the first vertical slice:
  operator: equals, not_equals
  state:    matches VariableResult.state

Combinator: all | any | not (per input/criterion.schema.json).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..enums import (
    ActionClass,
    Confidence,
    CriterionStatus,
    EmpiricalRelation,
    EvidenceBasis,
    FindingCategory,
    Severity,
    SeverityStatus,
    ValueState,
)
from ..models import (
    CriterionResult,
    EmpiricalStatus,
    Finding,
    PotentialEffect,
    RecommendedAction,
    SeverityBasis,
    SeverityRecord,
    VariableResult,
)

ENGINE_VERSION = "0.1.0"


class _EvalUnknown(Exception):
    """Raised when a predicate cannot be evaluated because a required
    variable is in an unknown-like state (unknown / not_collected /
    extraction_failed). The criterion result becomes `unknown`, not
    `finding` and not `satisfied`."""


class _NotApplicable(Exception):
    """Raised when a required variable is not_applicable to this session."""


def _evaluate_predicate(pred: dict[str, Any], vars_: dict[str, VariableResult]) -> bool:
    vid = pred["variable"]
    if vid not in vars_:
        raise _EvalUnknown(f"variable {vid} not computed")
    var = vars_[vid]

    # State-based predicate short-circuit
    if "state" in pred:
        return var.state == pred["state"]

    # Value-based predicates require an observed/derived state
    if var.state in (ValueState.UNKNOWN.value, "unknown", "not_collected", "extraction_failed"):
        raise _EvalUnknown(f"{vid} state={var.state}, cannot evaluate value predicate")
    if var.state in (ValueState.NOT_APPLICABLE.value, "not_applicable"):
        raise _NotApplicable(f"{vid} is not_applicable")

    op = pred.get("operator")
    expected = pred.get("value")
    if op == "equals":
        return var.value == expected
    if op == "not_equals":
        return var.value != expected
    raise ValueError(f"Unsupported operator: {op}")


def _evaluate_condition(cond: dict[str, Any], vars_: dict[str, VariableResult]) -> bool:
    if "all" in cond:
        return all(_evaluate_predicate(p, vars_) for p in cond["all"])
    if "any" in cond:
        # Short-circuit any; but an unknown short-circuits to unknown unless
        # some predicate is confidently True.
        unknown_seen = False
        for p in cond["any"]:
            try:
                if _evaluate_predicate(p, vars_):
                    return True
            except _EvalUnknown:
                unknown_seen = True
        if unknown_seen:
            raise _EvalUnknown("any: some predicates unknown, none satisfied")
        return False
    if "not" in cond:
        return not _evaluate_predicate(cond["not"], vars_)
    raise ValueError(f"Malformed condition: {cond}")


def _build_finding(
    criterion: dict[str, Any],
    finding_id: str,
    vars_: dict[str, VariableResult],
    spec_version: str,
) -> Finding:
    tmpl = criterion["finding"]
    sev = tmpl["severity"]

    input_snapshot = {
        vid: vars_[vid].value for vid in criterion.get("requires", []) if vid in vars_
    }

    return Finding(
        finding_id=finding_id,
        criterion_id=criterion["criterion_id"],
        criterion_version=criterion["version"],
        label=tmpl["label"],
        category=FindingCategory(tmpl["category"]),
        lifecycle_origin=criterion["lifecycle_origin"],
        observed_condition=tmpl.get("observed_condition", input_snapshot),
        reference_condition=tmpl.get("reference_condition"),
        affected_profile=criterion["applies_to"][0],
        severity=Severity(sev["level"]),
        severity_status=SeverityStatus(sev["status"]),
        severity_basis=[EvidenceBasis(b["evidence_type"]) for b in sev["basis"]],
        confidence=Confidence(
            tmpl.get("confidence", {}).get("default", "high")
        ),
        confidence_basis=tmpl.get("confidence", {}).get("components"),
        evidence_refs=criterion["evidence_refs"],
        variable_refs=list(criterion.get("requires", [])),
        potential_effects=[
            PotentialEffect(
                effect_id=pe["effect_id"],
                relation=EmpiricalRelation(pe["relation"]),
                evidence_refs=pe.get("evidence_refs", []),
                wording=pe["wording"],
                causal_claim=pe.get("causal_claim", False),
            )
            for pe in tmpl.get("potential_effects", [])
        ],
        recommended_actions=[
            RecommendedAction(
                action_id=a["action_id"],
                action_class=ActionClass(a["action_class"]),
                text=a["text"],
                automated=a.get("automated", False),
                changes_source_data=a.get("changes_source_data", False),
                requires_human_approval=a.get("requires_human_approval", True),
            )
            for a in tmpl.get("recommended_actions", [])
        ],
        empirical_status=EmpiricalStatus(
            **tmpl.get("empirical_status", {"state": "not_tested"})
        ),
        spec_version=spec_version,
    )


def evaluate(
    criterion: dict[str, Any],
    vars_: dict[str, VariableResult],
    profile_id: str,
    finding_id_generator,
    spec_version: str,
) -> tuple[CriterionResult, list[Finding]]:
    """Evaluate one criterion; return the result and (0 or 1) findings."""
    now = datetime.now(timezone.utc)
    findings: list[Finding] = []

    input_snapshot = {}
    for vid in criterion.get("requires", []):
        if vid in vars_:
            input_snapshot[vid] = {"value": vars_[vid].value, "state": vars_[vid].state}

    try:
        triggered = _evaluate_condition(criterion["condition"], vars_)
    except _EvalUnknown:
        result = CriterionResult(
            criterion_id=criterion["criterion_id"],
            criterion_version=criterion["version"],
            status=CriterionStatus.UNKNOWN,
            profile_id=profile_id,
            input_snapshot=input_snapshot,
            evaluation_engine_version=ENGINE_VERSION,
            evaluated_at=now,
        )
        return result, findings
    except _NotApplicable:
        result = CriterionResult(
            criterion_id=criterion["criterion_id"],
            criterion_version=criterion["version"],
            status=CriterionStatus.NOT_APPLICABLE,
            profile_id=profile_id,
            input_snapshot=input_snapshot,
            evaluation_engine_version=ENGINE_VERSION,
            evaluated_at=now,
        )
        return result, findings

    if triggered:
        fid = finding_id_generator()
        finding = _build_finding(criterion, fid, vars_, spec_version)
        findings.append(finding)
        status = CriterionStatus.FINDING
        finding_refs = [fid]
    else:
        status = CriterionStatus.SATISFIED
        finding_refs = []

    result = CriterionResult(
        criterion_id=criterion["criterion_id"],
        criterion_version=criterion["version"],
        status=status,
        profile_id=profile_id,
        input_snapshot=input_snapshot,
        finding_refs=finding_refs,
        evaluation_engine_version=ENGINE_VERSION,
        evaluated_at=now,
    )
    return result, findings
