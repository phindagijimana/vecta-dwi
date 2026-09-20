"""Extractors for scanner-context variables.

All four read from the BIDS DWI sidecar for the first vertical slice.
When the DICOM collector lands (Commit B), a fallback path to
DICOM Manufacturer/Model/MagneticFieldStrength/SoftwareVersions tags
will be added, along with conflict detection.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..collectors.bids import DwiEntity
from ..enums import Confidence, ValueState
from ..models import VariableResult

EXTRACTOR_VERSION = "0.1.0"


def _now():
    return datetime.now(timezone.utc)


def _string_field(entity: DwiEntity, bids_field: str) -> tuple[str | None, list[str]]:
    """Return (normalized string value or None, evidence_refs)."""
    raw = entity.sidecar.get(bids_field)
    if raw is None:
        return None, []
    ev_refs = [
        ev.evidence_id for ev in entity.evidence if ev.source_field == bids_field
    ]
    if isinstance(raw, str):
        return raw.strip() or None, ev_refs
    return str(raw), ev_refs


def extract_manufacturer(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.SCANNER.MANUFACTURER."""
    value, refs = _string_field(entity, "Manufacturer")
    state = ValueState.OBSERVED if value is not None else ValueState.UNKNOWN
    return VariableResult(
        variable_id="VECTA.DWI.SCANNER.MANUFACTURER",
        definition_version="0.1.0",
        value=value,
        state=state,
        confidence=Confidence.HIGH,
        evidence_refs=refs,
        extractor_id="extract_manufacturer_v1",
        extractor_version=EXTRACTOR_VERSION,
        normalization_rule="strip_whitespace",
        computed_at=_now(),
    )


def extract_model(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.SCANNER.MODEL."""
    value, refs = _string_field(entity, "ManufacturersModelName")
    state = ValueState.OBSERVED if value is not None else ValueState.UNKNOWN
    return VariableResult(
        variable_id="VECTA.DWI.SCANNER.MODEL",
        definition_version="0.1.0",
        value=value,
        state=state,
        confidence=Confidence.HIGH,
        evidence_refs=refs,
        extractor_id="extract_model_v1",
        extractor_version=EXTRACTOR_VERSION,
        normalization_rule="strip_whitespace",
        computed_at=_now(),
    )


def extract_field_strength(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.SCANNER.FIELD_STRENGTH."""
    raw = entity.sidecar.get("MagneticFieldStrength")
    ev_refs = [
        ev.evidence_id
        for ev in entity.evidence
        if ev.source_field == "MagneticFieldStrength"
    ]
    if raw is None:
        return VariableResult(
            variable_id="VECTA.DWI.SCANNER.FIELD_STRENGTH",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="tesla",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_field_strength_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return VariableResult(
            variable_id="VECTA.DWI.SCANNER.FIELD_STRENGTH",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="tesla",
            confidence=Confidence.HIGH,
            evidence_refs=ev_refs,
            extractor_id="extract_field_strength_v1",
            extractor_version=EXTRACTOR_VERSION,
            warnings=[f"could not parse MagneticFieldStrength={raw!r} as float"],
            computed_at=_now(),
        )
    if value <= 0.0 or value >= 12.0:
        return VariableResult(
            variable_id="VECTA.DWI.SCANNER.FIELD_STRENGTH",
            definition_version="0.1.0",
            value=value,
            state=ValueState.INVALID,
            canonical_unit="tesla",
            confidence=Confidence.HIGH,
            evidence_refs=ev_refs,
            extractor_id="extract_field_strength_v1",
            extractor_version=EXTRACTOR_VERSION,
            warnings=[f"field strength {value}T outside plausible MR range (0, 12)"],
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.SCANNER.FIELD_STRENGTH",
        definition_version="0.1.0",
        value=value,
        state=ValueState.OBSERVED,
        canonical_unit="tesla",
        confidence=Confidence.HIGH,
        evidence_refs=ev_refs,
        extractor_id="extract_field_strength_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def extract_software_version(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.SCANNER.SOFTWARE_VERSION."""
    value, refs = _string_field(entity, "SoftwareVersions")
    state = ValueState.OBSERVED if value is not None else ValueState.UNKNOWN
    return VariableResult(
        variable_id="VECTA.DWI.SCANNER.SOFTWARE_VERSION",
        definition_version="0.1.0",
        value=value,
        state=state,
        confidence=Confidence.HIGH,
        evidence_refs=refs,
        extractor_id="extract_software_version_v1",
        extractor_version=EXTRACTOR_VERSION,
        normalization_rule="strip_whitespace",
        computed_at=_now(),
    )
