"""Extractors for the DICOM Source module.

Consume a DicomInventory produced by collectors/dicom.py and emit
VariableResult objects for the source-integrity variables declared in
specification/v0.1/variables/dicom_source.yaml.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..collectors.dicom import (
    DicomInventory,
    classify_series,
    series_by_class,
)
from ..enums import Confidence, ValueState
from ..models import VariableResult

EXTRACTOR_VERSION = "0.1.0"
FIELD_STRENGTH_TOLERANCE = 0.05  # tesla — tight because scanner reports are exact


def _now():
    return datetime.now(timezone.utc)


def _series_ev_refs(inventory: DicomInventory) -> list[str]:
    """All DICOM evidence records — coarse-grained refs for source counts."""
    return [ev.evidence_id for ev in inventory.evidence]


def extract_series_count(inventory: DicomInventory) -> VariableResult:
    """VECTA.DWI.DICOM.SERIES_COUNT."""
    return VariableResult(
        variable_id="VECTA.DWI.DICOM.SERIES_COUNT",
        definition_version="0.1.0",
        value=len(inventory.series),
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_series_ev_refs(inventory),
        extractor_id="dicom_series_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def derive_dwi_series_count(inventory: DicomInventory) -> VariableResult:
    """VECTA.DWI.DICOM.DWI_SERIES_COUNT."""
    dwi_series = series_by_class(inventory).get("dwi", [])
    return VariableResult(
        variable_id="VECTA.DWI.DICOM.DWI_SERIES_COUNT",
        definition_version="0.1.0",
        value=len(dwi_series),
        state=ValueState.DERIVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_series_ev_refs(inventory),
        extractor_id="dicom_dwi_series_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def extract_instance_count(inventory: DicomInventory) -> VariableResult:
    """VECTA.DWI.DICOM.INSTANCE_COUNT."""
    total = sum(len(s.instances) for s in inventory.series.values())
    return VariableResult(
        variable_id="VECTA.DWI.DICOM.INSTANCE_COUNT",
        definition_version="0.1.0",
        value=total,
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_series_ev_refs(inventory),
        extractor_id="dicom_instance_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def extract_duplicate_instance_count(inventory: DicomInventory) -> VariableResult:
    """VECTA.DWI.DICOM.DUPLICATE_INSTANCE_COUNT."""
    total = sum(s.duplicate_sop_instances for s in inventory.series.values())
    return VariableResult(
        variable_id="VECTA.DWI.DICOM.DUPLICATE_INSTANCE_COUNT",
        definition_version="0.1.0",
        value=total,
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_series_ev_refs(inventory),
        extractor_id="dicom_duplicate_instance_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def derive_dwi_geometry_consistent(inventory: DicomInventory) -> VariableResult:
    """VECTA.DWI.DICOM.SERIES_GEOMETRY_CONSISTENT."""
    dwi_series = series_by_class(inventory).get("dwi", [])
    if not dwi_series:
        return VariableResult(
            variable_id="VECTA.DWI.DICOM.SERIES_GEOMETRY_CONSISTENT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.NOT_APPLICABLE,
            confidence=Confidence.HIGH,
            evidence_refs=_series_ev_refs(inventory),
            extractor_id="dicom_dwi_geometry_consistent_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    all_consistent = all(s.geometry_consistent for s in dwi_series)
    return VariableResult(
        variable_id="VECTA.DWI.DICOM.SERIES_GEOMETRY_CONSISTENT",
        definition_version="0.1.0",
        value=all_consistent,
        state=ValueState.DERIVED,
        confidence=Confidence.HIGH,
        evidence_refs=_series_ev_refs(inventory),
        extractor_id="dicom_dwi_geometry_consistent_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def derive_field_strength_agrees_with_bids(
    inventory: DicomInventory, bids_field_strength: VariableResult
) -> VariableResult:
    """VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS.

    Transformation-fidelity check: DICOM vs BIDS agreement within tolerance.
    """
    dwi_series = series_by_class(inventory).get("dwi", [])
    if not dwi_series:
        return VariableResult(
            variable_id="VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS",
            definition_version="0.1.0",
            value=None,
            state=ValueState.NOT_APPLICABLE,
            confidence=Confidence.HIGH,
            evidence_refs=_series_ev_refs(inventory),
            extractor_id="dicom_bids_field_strength_agreement_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    dcm_val = dwi_series[0].magnetic_field_strength
    bids_val = bids_field_strength.value if bids_field_strength.state == "observed" else None
    if dcm_val is None or bids_val is None:
        return VariableResult(
            variable_id="VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            confidence=Confidence.HIGH,
            evidence_refs=_series_ev_refs(inventory),
            extractor_id="dicom_bids_field_strength_agreement_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    agrees = abs(float(dcm_val) - float(bids_val)) <= FIELD_STRENGTH_TOLERANCE
    return VariableResult(
        variable_id="VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS",
        definition_version="0.1.0",
        value=agrees,
        state=ValueState.DERIVED,
        confidence=Confidence.HIGH,
        evidence_refs=_series_ev_refs(inventory) + bids_field_strength.evidence_refs,
        extractor_id="dicom_bids_field_strength_agreement_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )
