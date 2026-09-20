"""Pydantic v2 models mirroring specification/v0.1/schemas/output/*.

These are the runtime typed representation of the canonical vecta.json.
The JSON Schema is the cross-language public contract; this module is the
Python implementation convenience.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    ActionClass,
    AssessmentState,
    Confidence,
    CriterionStatus,
    EmpiricalRelation,
    EvidenceBasis,
    FindingCategory,
    PrivacyStatus,
    ReadinessState,
    Severity,
    SeverityStatus,
    SourceType,
    ValueState,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


# ─── Building blocks ──────────────────────────────────────────────────────


class SeverityBasis(_StrictModel):
    evidence_type: EvidenceBasis
    evidence_ref: str


class SeverityRecord(_StrictModel):
    level: Severity
    status: SeverityStatus
    basis: list[SeverityBasis] = Field(min_length=1)
    profile_id: Optional[str] = None
    calibration_ref: Optional[str] = None


class ConfidenceRecord(_StrictModel):
    level: Confidence
    components: Optional[dict[str, Confidence]] = None
    method_id: Optional[str] = None


class PotentialEffect(_StrictModel):
    effect_id: str
    relation: EmpiricalRelation
    evidence_refs: list[str] = Field(default_factory=list)
    wording: str
    causal_claim: bool = False


class RecommendedAction(_StrictModel):
    action_id: str
    action_class: ActionClass
    text: str
    automated: bool
    changes_source_data: bool = False
    requires_human_approval: bool


class EmpiricalStatus(_StrictModel):
    state: str  # not_tested | exploratory_association | ...
    study_ref: Optional[str] = None
    outcome_ref: Optional[str] = None
    effect_ref: Optional[str] = None
    evidence_version: Optional[str] = None


class ErrorRecord(_StrictModel):
    error_code: str
    error_class: str
    message: str
    recoverable: bool
    context: Optional[dict[str, Any]] = None


class WarningRecord(_StrictModel):
    code: str
    message: str
    context: Optional[dict[str, Any]] = None


# ─── Top-level output objects ─────────────────────────────────────────────


class EvidenceRecord(_StrictModel):
    evidence_id: str
    source_type: SourceType
    source_locator: Optional[str] = None
    source_field: Optional[str] = None
    raw_value: Any = None
    raw_unit: Optional[str] = None
    source_hash: Optional[str] = None
    collector_id: str
    collector_version: str
    privacy_status: PrivacyStatus
    timestamp: datetime
    metadata: Optional[dict[str, Any]] = None


class ConflictRecord(_StrictModel):
    conflict_id: str
    source_values: list[dict[str, Any]]
    tolerance_ref: Optional[str] = None
    resolution: str
    canonical_evidence_ref: Optional[str] = None
    note: Optional[str] = None


class VariableResult(_StrictModel):
    variable_id: str
    definition_version: str
    value: Any = None
    state: ValueState
    canonical_unit: Optional[str] = None
    confidence: Confidence
    evidence_refs: list[str] = Field(default_factory=list)
    extractor_id: str
    extractor_version: str
    normalization_rule: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    computed_at: datetime


class DerivedMetric(_StrictModel):
    metric_id: str
    definition_version: str
    value: Any = None
    state: ValueState
    canonical_unit: Optional[str] = None
    dependency_refs: list[str] = Field(default_factory=list)
    formula_id: str
    formula_version: str
    reference_id: Optional[str] = None
    confidence: Confidence
    evidence_refs: list[str] = Field(default_factory=list)
    details: Optional[dict[str, Any]] = None


class CriterionResult(_StrictModel):
    criterion_id: str
    criterion_version: str
    status: CriterionStatus
    profile_id: str
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    reference_snapshot: Optional[dict[str, Any]] = None
    finding_refs: list[str] = Field(default_factory=list)
    evaluation_engine_version: str
    evaluated_at: datetime
    error: Optional[ErrorRecord] = None


class Finding(_StrictModel):
    finding_id: str
    criterion_id: str
    criterion_version: str
    label: str
    category: FindingCategory
    lifecycle_origin: str
    observed_condition: dict[str, Any]
    reference_condition: Optional[dict[str, Any]] = None
    affected_profile: str
    severity: Severity
    severity_status: SeverityStatus
    severity_basis: list[EvidenceBasis] = Field(min_length=1)
    confidence: Confidence
    confidence_basis: Optional[dict[str, Any]] = None
    evidence_refs: list[str] = Field(min_length=1)
    variable_refs: list[str] = Field(default_factory=list)
    metric_refs: list[str] = Field(default_factory=list)
    potential_effects: list[PotentialEffect] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    empirical_status: EmpiricalStatus
    explanation_template_id: Optional[str] = None
    spec_version: str


class DimensionState(_StrictModel):
    state: ReadinessState
    contributing_findings: list[str] = Field(default_factory=list)


class AssessmentCompleteness(_StrictModel):
    applicable_variables: int
    observed_or_derived: int
    unknown: int = 0
    not_collected: int = 0
    invalid: int = 0
    extraction_failed: int = 0
    evaluable_criteria: int = 0
    unknown_criteria: int = 0
    ratio: float
    calculation_id: str


class ReadinessDimensions(_StrictModel):
    source_integrity: Optional[DimensionState] = None
    metadata_sufficiency: Optional[DimensionState] = None
    representation_integrity: Optional[DimensionState] = None
    protocol_conformance: Optional[DimensionState] = None
    processing_readiness: Optional[DimensionState] = None
    assessment_completeness: Optional[AssessmentCompleteness] = None


class ReadinessSummary(_StrictModel):
    profile_id: str
    profile_version: str
    state: ReadinessState
    dimensions: ReadinessDimensions
    blocking_finding_refs: list[str] = Field(default_factory=list)
    review_finding_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    rule_version: str


class AssessmentStatus(_StrictModel):
    state: AssessmentState
    started_at: datetime
    completed_at: Optional[datetime] = None
    domains_attempted: list[str] = Field(default_factory=list)
    domains_completed: list[str] = Field(default_factory=list)
    errors: list[ErrorRecord] = Field(default_factory=list)
    warnings: list[WarningRecord] = Field(default_factory=list)


class Provenance(_StrictModel):
    vecta_software_version: str
    specification_version: str
    schema_version: str
    profile_version: str
    protocol_reference: Optional[str] = None
    protocol_version: Optional[str] = None
    configuration_hash: Optional[str] = None
    dataset_snapshot: Optional[str] = None
    source_hash_manifest: Optional[str] = None
    converter_version: Optional[str] = None
    bids_validator_version: Optional[str] = None
    container_digest: Optional[str] = None
    runtime_environment: Optional[dict[str, Any]] = None
    executed_at: datetime
    software_commit: Optional[str] = None
    spec_snapshot_hash: Optional[str] = None


class ProfileRef(_StrictModel):
    id: str
    version: str


class ProtocolReferenceRef(_StrictModel):
    id: str
    version: str


class Assessment(_StrictModel):
    schema_version: str
    assessment_id: str
    subject_id: str
    session_id: str
    profile: ProfileRef
    protocol_reference: Optional[ProtocolReferenceRef] = None
    assessment_status: AssessmentStatus
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    variables: dict[str, VariableResult] = Field(default_factory=dict)
    derived_metrics: dict[str, DerivedMetric] = Field(default_factory=dict)
    criteria: list[CriterionResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    readiness: ReadinessSummary
    summary: Optional[dict[str, Any]] = None
    provenance: Provenance
    extensions: Optional[dict[str, Any]] = None
