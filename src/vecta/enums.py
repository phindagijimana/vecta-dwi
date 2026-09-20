"""Runtime mirror of specification/v0.1/registries/enums.yaml.

Kept as a Python module rather than loaded from YAML at import time because
runtime code needs static enum values for exhaustive matching and IDE help.
The YAML remains the human-authored source of truth; a future test should
verify the two are consistent.
"""

from enum import Enum


class ValueState(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    UNKNOWN = "unknown"
    NOT_COLLECTED = "not_collected"
    NOT_APPLICABLE = "not_applicable"
    INVALID = "invalid"
    EXTRACTION_FAILED = "extraction_failed"
    CONFLICT = "conflict"


class CriterionStatus(str, Enum):
    SATISFIED = "satisfied"
    FINDING = "finding"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


class AssessmentState(str, Enum):
    COMPLETED = "completed"
    COMPLETED_WITH_UNKNOWNS = "completed_with_unknowns"
    PARTIAL = "partial"
    FAILED = "failed"
    SPECIFICATION_ERROR = "specification_error"


class Confidence(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MODERATE = "moderate"
    INFORMATIONAL = "informational"


class SeverityStatus(str, Enum):
    PROVISIONAL = "provisional"
    CALIBRATED = "calibrated"


class ReadinessState(str, Enum):
    READY = "ready"
    READY_WITH_LIMITATIONS = "ready_with_limitations"
    REVIEW_REQUIRED = "review_required"
    NOT_READY = "not_ready"
    NOT_ASSESSED = "not_assessed"


class EvidenceBasis(str, Enum):
    FORMAL_STANDARD = "formal_standard"
    PIPELINE_REQUIREMENT = "pipeline_requirement"
    PEER_REVIEWED_LITERATURE = "peer_reviewed_literature"
    EXPERT_CONSENSUS = "expert_consensus"
    EMPIRICAL_INTERNAL = "empirical_internal"
    EMPIRICAL_EXTERNAL = "empirical_external"


class PrivacyStatus(str, Enum):
    SAFE = "safe"
    RESTRICTED = "restricted"


class ActionClass(str, Enum):
    REVIEW = "review"
    DOCUMENT = "document"
    RE_EXPORT = "re_export"
    REPAIR_REPRESENTATION = "repair_representation"
    ALTERNATIVE_PROCESSING = "alternative_processing"
    EXCLUDE = "exclude"
    PROSPECTIVE_CHANGE = "prospective_change"


class EmpiricalRelation(str, Enum):
    PLAUSIBLE = "plausible"
    EMPIRICALLY_ASSOCIATED = "empirically_associated"
    EXTERNALLY_REPLICATED = "externally_replicated"


class FindingCategory(str, Enum):
    ACQUISITION_INTEGRITY = "acquisition_integrity"
    SOURCE_INTEGRITY = "source_integrity"
    METADATA_INTEGRITY = "metadata_integrity"
    CONVERSION_INTEGRITY = "conversion_integrity"
    REPRESENTATION_INTEGRITY = "representation_integrity"
    PROTOCOL_CONFORMANCE = "protocol_conformance"
    COHORT_INTEGRITY = "cohort_integrity"
    PROVENANCE_INTEGRITY = "provenance_integrity"
    EVIDENCE_INSUFFICIENCY = "evidence_insufficiency"


class SourceType(str, Enum):
    DICOM_HEADER = "dicom_header"
    DICOM_DATASET = "dicom_dataset"
    BIDS_JSON = "bids_json"
    BIDS_FILENAME = "bids_filename"
    BIDS_VALIDATOR = "bids_validator"
    NIFTI_HEADER = "nifti_header"
    BVAL = "bval"
    BVEC = "bvec"
    PROTOCOL_REFERENCE = "protocol_reference"
    PIPELINE_LOG = "pipeline_log"
    CONVERTER_LOG = "converter_log"
    COHORT_MANIFEST = "cohort_manifest"
