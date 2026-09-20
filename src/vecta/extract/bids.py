"""Extractors for BIDS-representation-level variables.

The BIDS Validator itself is a Node.js tool; wiring it up is deferred. For
v0.1 we report `unknown` unless a caller has pre-run the validator and
placed its JSON output next to the dataset (`.bids-validator-output.json`
convention adopted here — no formal BIDS spec).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..collectors.bids import BidsSession
from ..enums import Confidence, ValueState
from ..models import VariableResult


def derive_dwi_present(session: BidsSession) -> VariableResult:
    """VECTA.DWI.BIDS.DWI_PRESENT — boolean flag for declarative predicates."""
    present = len(session.dwi_entities) > 0
    return VariableResult(
        variable_id="VECTA.DWI.BIDS.DWI_PRESENT",
        definition_version="0.1.0",
        value=present,
        state=ValueState.DERIVED,
        confidence=Confidence.HIGH,
        evidence_refs=[],
        extractor_id="derive_dwi_present_v1",
        extractor_version="0.1.0",
        computed_at=_now(),
    )

EXTRACTOR_VERSION = "0.1.0"


def _now():
    return datetime.now(timezone.utc)


def _validator_output(root: Path) -> dict | None:
    """Read a validator output JSON if present, normalizing legacy /
    v1 (flat) and v2 (issues-wrapped) shapes to a common form.

    Returns a dict with keys `errors` (list) and `warnings` (list),
    or None if no file is present or parsing fails.

    Supported shapes:
      - Flat:  {"errors": [...], "warnings": [...]}
      - Wrapped: {"issues": {"errors": [...], "warnings": [...]}, ...}
        (bids-validator v2 / deno CLI)

    Some tooling prepends stderr warnings to the JSON output; we scan
    each line for the first `{` and try to parse from there.
    """
    candidate = root / ".bids-validator-output.json"
    if not candidate.is_file():
        return None
    text = candidate.read_text()
    payload = None
    for start_line in text.splitlines():
        stripped = start_line.strip()
        if stripped.startswith("{"):
            try:
                payload = json.loads(stripped)
                break
            except Exception:
                continue
    if payload is None:
        try:
            payload = json.loads(text)
        except Exception:
            return None
    if "issues" in payload and isinstance(payload["issues"], dict):
        issues = payload["issues"]
        return {
            "errors": issues.get("errors", []),
            "warnings": issues.get("warnings", []),
        }
    return payload


def extract_validator_error_count(session: BidsSession) -> VariableResult:
    """VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT."""
    data = _validator_output(session.root)
    if data is None:
        return VariableResult(
            variable_id="VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_bids_validator_errors_v1",
            extractor_version=EXTRACTOR_VERSION,
            warnings=["no .bids-validator-output.json found; run bids-validator externally to populate"],
            computed_at=_now(),
        )
    errs = data.get("errors")
    if isinstance(errs, list):
        count = len(errs)
    elif isinstance(errs, int):
        count = errs
    else:
        return VariableResult(
            variable_id="VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_bids_validator_errors_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT",
        definition_version="0.1.0",
        value=count,
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=[],
        extractor_id="extract_bids_validator_errors_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def extract_validator_warning_count(session: BidsSession) -> VariableResult:
    """VECTA.DWI.BIDS.VALIDATOR_WARNING_COUNT."""
    data = _validator_output(session.root)
    if data is None:
        return VariableResult(
            variable_id="VECTA.DWI.BIDS.VALIDATOR_WARNING_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_bids_validator_warnings_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    warns = data.get("warnings")
    if isinstance(warns, list):
        count = len(warns)
    elif isinstance(warns, int):
        count = warns
    else:
        return VariableResult(
            variable_id="VECTA.DWI.BIDS.VALIDATOR_WARNING_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_bids_validator_warnings_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.BIDS.VALIDATOR_WARNING_COUNT",
        definition_version="0.1.0",
        value=count,
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=[],
        extractor_id="extract_bids_validator_warnings_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def derive_required_series_present(session: BidsSession, profile: dict) -> VariableResult:
    """VECTA.DWI.BIDS.REQUIRED_SERIES_PRESENT — structured object per §9.1.

    For the dwi_connectomics profile, required = {dwi, anatomical_t1}. We
    check by presence of a canonical BIDS entity directory under the
    subject/session tree.
    """
    root = session.root
    subj = f"sub-{session.subject_id}"
    ses = f"ses-{session.session_id}"

    def _has_dir(entity_dir: str) -> bool:
        path = root / subj / ses / entity_dir
        return path.is_dir() and any(path.iterdir())

    def _has_t1w() -> bool:
        anat_dir = root / subj / ses / "anat"
        if not anat_dir.is_dir():
            return False
        return any("_T1w" in p.name for p in anat_dir.iterdir())

    required = profile.get("requires", {})
    present = {}
    for entity, spec in required.items():
        if not spec.get("required", False):
            continue
        if entity == "dwi":
            present["dwi"] = _has_dir("dwi")
        elif entity == "anatomical_t1":
            present["anatomical_t1"] = _has_t1w()
        else:
            present[entity] = False  # unknown entity treated as absent

    missing = [k for k, v in present.items() if not v]
    return VariableResult(
        variable_id="VECTA.DWI.BIDS.REQUIRED_SERIES_PRESENT",
        definition_version="0.1.0",
        value={"present": present, "missing": missing},
        state=ValueState.DERIVED,
        confidence=Confidence.HIGH,
        evidence_refs=[],
        extractor_id="derive_required_series_present_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )
