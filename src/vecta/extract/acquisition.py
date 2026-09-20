"""Acquisition variable extractors: voxel geometry, volume/gradient counts,
b-value shell structure, bvec plausibility.

Voxel size and volume count come from the NIfTI header (nibabel). b-values
and bvecs come from the sibling .bval / .bvec files.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import nibabel as nib

from ..collectors.bids import DwiEntity
from ..enums import Confidence, ValueState
from ..models import VariableResult

EXTRACTOR_VERSION = "0.1.0"
B0_THRESHOLD = 50.0        # b < this treated as a b0 volume
DEFAULT_SHELL_TOL = 50.0   # grouping tolerance in s/mm^2 (matches tolerance registry)
DEFAULT_VECTOR_NORM_TOL = 0.05


def _now():
    return datetime.now(timezone.utc)


# ─── Voxel size + volume count (NIfTI header) ───────────────────────────


def _load_nifti(entity: DwiEntity):
    if entity.nifti_path is None or not entity.nifti_path.is_file():
        return None
    try:
        return nib.load(str(entity.nifti_path))
    except Exception:
        return None


def _nifti_evidence_refs(entity: DwiEntity) -> list[str]:
    return [
        ev.evidence_id
        for ev in entity.evidence
        if ev.source_field == "nifti_header"
    ]


def extract_voxel_size(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.ACQ.VOXEL_SIZE — pixdim[1..3] from NIfTI header."""
    if entity.nifti_path is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.VOXEL_SIZE",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="mm",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_voxel_size_v1",
            extractor_version=EXTRACTOR_VERSION,
            warnings=["no NIfTI file present alongside this DWI sidecar"],
            computed_at=_now(),
        )
    img = _load_nifti(entity)
    if img is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.VOXEL_SIZE",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="mm",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_voxel_size_v1",
            extractor_version=EXTRACTOR_VERSION,
            warnings=["NIfTI header could not be read"],
            computed_at=_now(),
        )
    hdr = img.header
    zooms = hdr.get_zooms()[:3]
    vals = [float(z) for z in zooms]
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.VOXEL_SIZE",
        definition_version="0.1.0",
        value=vals,
        state=ValueState.OBSERVED,
        canonical_unit="mm",
        confidence=Confidence.HIGH,
        evidence_refs=_nifti_evidence_refs(entity),
        extractor_id="extract_voxel_size_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def extract_volume_count(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.ACQ.VOLUME_COUNT — NIfTI dim[4]."""
    if entity.nifti_path is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.VOLUME_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_volume_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    img = _load_nifti(entity)
    if img is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.VOLUME_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_volume_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    shape = img.header.get_data_shape()
    if len(shape) < 4:
        # 3D image — treat as one volume
        volumes = 1
    else:
        volumes = int(shape[3])
    if volumes < 1:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.VOLUME_COUNT",
            definition_version="0.1.0",
            value=volumes,
            state=ValueState.INVALID,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=_nifti_evidence_refs(entity),
            extractor_id="extract_volume_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.VOLUME_COUNT",
        definition_version="0.1.0",
        value=volumes,
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_nifti_evidence_refs(entity),
        extractor_id="extract_volume_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


# ─── bval / bvec ────────────────────────────────────────────────────────


def _parse_bval(path) -> list[float] | None:
    try:
        text = path.read_text().split()
        return [float(x) for x in text]
    except Exception:
        return None


def _parse_bvec(path) -> list[list[float]] | None:
    """Return list of 3D direction vectors (one per volume). BIDS bvec files
    are three whitespace-separated rows: x-row, y-row, z-row."""
    try:
        lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]
        if len(lines) != 3:
            return None
        rows = [[float(x) for x in ln.split()] for ln in lines]
        n = len(rows[0])
        if any(len(r) != n for r in rows):
            return None
        return [[rows[0][i], rows[1][i], rows[2][i]] for i in range(n)]
    except Exception:
        return None


def _bval_evidence_refs(entity: DwiEntity) -> list[str]:
    return [ev.evidence_id for ev in entity.evidence if ev.source_field == "bval"]


def _bvec_evidence_refs(entity: DwiEntity) -> list[str]:
    return [ev.evidence_id for ev in entity.evidence if ev.source_field == "bvec"]


def extract_bval_count(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.ACQ.BVAL_COUNT."""
    if entity.bval_path is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.BVAL_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_bval_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    bvals = _parse_bval(entity.bval_path)
    if bvals is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.BVAL_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=_bval_evidence_refs(entity),
            extractor_id="extract_bval_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.BVAL_COUNT",
        definition_version="0.1.0",
        value=len(bvals),
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_bval_evidence_refs(entity),
        extractor_id="extract_bval_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def derive_shell_count(entity: DwiEntity, tolerance: float = DEFAULT_SHELL_TOL) -> VariableResult:
    """VECTA.DWI.ACQ.SHELL_COUNT — distinct non-b0 b-value shells within tolerance."""
    if entity.bval_path is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.SHELL_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="derive_shell_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    bvals = _parse_bval(entity.bval_path)
    if bvals is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.SHELL_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=_bval_evidence_refs(entity),
            extractor_id="derive_shell_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    nonzero = sorted(b for b in bvals if b > B0_THRESHOLD)
    # Greedy shell grouping: start a new shell whenever the next value is >
    # tolerance away from the current shell's mean.
    shells: list[list[float]] = []
    for b in nonzero:
        if not shells or abs(b - (sum(shells[-1]) / len(shells[-1]))) > tolerance:
            shells.append([b])
        else:
            shells[-1].append(b)
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.SHELL_COUNT",
        definition_version="0.1.0",
        value=len(shells),
        state=ValueState.DERIVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_bval_evidence_refs(entity),
        extractor_id="derive_shell_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def extract_bvec_count(entity: DwiEntity) -> VariableResult:
    """VECTA.DWI.ACQ.BVEC_COUNT."""
    if entity.bvec_path is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.BVEC_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="extract_bvec_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    bvecs = _parse_bvec(entity.bvec_path)
    if bvecs is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.BVEC_COUNT",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            canonical_unit="count",
            confidence=Confidence.HIGH,
            evidence_refs=_bvec_evidence_refs(entity),
            extractor_id="extract_bvec_count_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.BVEC_COUNT",
        definition_version="0.1.0",
        value=len(bvecs),
        state=ValueState.OBSERVED,
        canonical_unit="count",
        confidence=Confidence.HIGH,
        evidence_refs=_bvec_evidence_refs(entity),
        extractor_id="extract_bvec_count_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )


def derive_bvec_plausibility(
    entity: DwiEntity, tolerance: float = DEFAULT_VECTOR_NORM_TOL
) -> VariableResult:
    """VECTA.DWI.ACQ.BVEC_PLAUSIBILITY — every non-b0 vector has |v| within
    tolerance of 1.0."""
    if entity.bvec_path is None or entity.bval_path is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.BVEC_PLAUSIBILITY",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            confidence=Confidence.HIGH,
            evidence_refs=[],
            extractor_id="derive_bvec_plausibility_v1",
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    bvals = _parse_bval(entity.bval_path)
    bvecs = _parse_bvec(entity.bvec_path)
    if bvals is None or bvecs is None or len(bvals) != len(bvecs):
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.BVEC_PLAUSIBILITY",
            definition_version="0.1.0",
            value=None,
            state=ValueState.EXTRACTION_FAILED,
            confidence=Confidence.HIGH,
            evidence_refs=_bvec_evidence_refs(entity) + _bval_evidence_refs(entity),
            extractor_id="derive_bvec_plausibility_v1",
            extractor_version=EXTRACTOR_VERSION,
            warnings=["bval and bvec length mismatch or unparseable"],
            computed_at=_now(),
        )
    all_ok = True
    for b, v in zip(bvals, bvecs):
        if b <= B0_THRESHOLD:
            continue
        norm = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
        if abs(norm - 1.0) > tolerance:
            all_ok = False
            break
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.BVEC_PLAUSIBILITY",
        definition_version="0.1.0",
        value=all_ok,
        state=ValueState.DERIVED,
        confidence=Confidence.HIGH,
        evidence_refs=_bvec_evidence_refs(entity) + _bval_evidence_refs(entity),
        extractor_id="derive_bvec_plausibility_v1",
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )
