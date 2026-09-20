"""Extractors for the phase-encoding-related first vertical slice.

Each extractor returns a VariableResult that mirrors what the
specification/v0.1/variables/*.yaml files declare — same states, same
allowed values, same evidence linkage.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..collectors.bids import BidsSession, DwiEntity
from ..enums import Confidence, ValueState
from ..models import VariableResult

EXTRACTOR_VERSION = "0.1.0"


def _now():
    return datetime.now(timezone.utc)


def extract_pe_direction(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.ACQ.PE_DIRECTION — from BIDS PhaseEncodingDirection."""
    pe = entity.sidecar.get("PhaseEncodingDirection")
    ev_refs = [
        ev.evidence_id
        for ev in entity.evidence
        if ev.source_field == "PhaseEncodingDirection"
    ]
    if pe is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.PE_DIRECTION",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_pe_direction_v1",
            extractor_version=EXTRACTOR_VERSION,
            normalization_rule="bids_pe_direction_v1",
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.PE_DIRECTION",
        definition_version="0.1.0",
        value=pe,
        state=ValueState.OBSERVED,
        confidence=Confidence.HIGH,
        evidence_refs=ev_refs,
        extractor_id="extract_pe_direction_v1",
        extractor_version=EXTRACTOR_VERSION,
        normalization_rule="bids_pe_direction_v1",
        computed_at=_now(),
    )


def extract_total_readout_time_present(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.ACQ.TOTAL_READOUT_TIME_PRESENT — presence-only in v0.1."""
    present = "TotalReadoutTime" in entity.sidecar
    ev_refs = [
        ev.evidence_id
        for ev in entity.evidence
        if ev.source_field == "TotalReadoutTime"
    ]
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.TOTAL_READOUT_TIME_PRESENT",
        definition_version="0.1.0",
        value=present,
        state=ValueState.OBSERVED,
        confidence=Confidence.HIGH,
        evidence_refs=ev_refs,
        extractor_id="extract_total_readout_time_present_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )
