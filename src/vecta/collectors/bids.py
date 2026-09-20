"""BIDS collector — locates DWI entities and reads their JSON sidecars.

Deliberately minimal: no dependency on a BIDS-parsing library. Handles the
subset of BIDS needed for the VECTA-DWI-014 vertical slice. A full
implementation should later switch to pybids or an equivalent.

Assumes single-subject / single-session datasets shaped like:

    <root>/sub-XXX/ses-YY/dwi/sub-XXX_ses-YY_dir-<D>_dwi.json
                                                     _dwi.nii.gz
                                                     _dwi.bval
                                                     _dwi.bvec
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..enums import PrivacyStatus, SourceType
from ..models import EvidenceRecord

COLLECTOR_ID = "bids_collector"
COLLECTOR_VERSION = "0.1.0"


@dataclass
class DwiEntity:
    """One DWI acquisition discovered in a BIDS dataset."""

    json_path: Path
    sidecar: dict           # parsed JSON contents
    dir_entity: str | None  # e.g. "AP" from _dir-AP_dwi.json
    bval_path: Path | None = None
    bvec_path: Path | None = None
    nifti_path: Path | None = None
    evidence: list[EvidenceRecord] = field(default_factory=list)


@dataclass
class BidsSession:
    root: Path
    subject_id: str
    session_id: str
    dwi_entities: list[DwiEntity] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


def _parse_dir_entity(json_path: Path) -> str | None:
    """Pull the `dir-<X>` entity out of a BIDS-style filename, if any."""
    for token in json_path.stem.split("_"):
        if token.startswith("dir-"):
            return token[len("dir-"):]
    return None


def _make_evidence(
    evidence_id: str,
    source_type: SourceType,
    path: Path,
    source_field: str | None,
    raw_value,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        source_type=source_type,
        source_locator=str(path),
        source_field=source_field,
        raw_value=raw_value,
        source_hash=_hash_file(path) if path.is_file() else None,
        collector_id=COLLECTOR_ID,
        collector_version=COLLECTOR_VERSION,
        privacy_status=PrivacyStatus.SAFE,
        timestamp=datetime.now(timezone.utc),
    )


def collect(root: Path, subject_id: str, session_id: str) -> BidsSession:
    """Discover all DWI JSON sidecars and companion files for one session."""
    root = Path(root)
    ses_dir = root / f"sub-{subject_id}" / f"ses-{session_id}" / "dwi"

    session = BidsSession(root=root, subject_id=subject_id, session_id=session_id)

    if not ses_dir.is_dir():
        return session   # no dwi entities; caller decides how to handle

    ev_counter = 0
    def next_ev_id() -> str:
        nonlocal ev_counter
        ev_counter += 1
        return f"ev-{ev_counter:05d}"

    for json_path in sorted(ses_dir.glob("*_dwi.json")):
        sidecar = json.loads(json_path.read_text())
        entity = DwiEntity(
            json_path=json_path,
            sidecar=sidecar,
            dir_entity=_parse_dir_entity(json_path),
        )
        # Record evidence for each sidecar field we care about
        for field_name in (
            "PhaseEncodingDirection",
            "TotalReadoutTime",
            "Manufacturer",
            "ManufacturersModelName",
            "MagneticFieldStrength",
            "SoftwareVersions",
            "RepetitionTime",
            "EchoTime",
        ):
            if field_name in sidecar:
                ev = _make_evidence(
                    evidence_id=next_ev_id(),
                    source_type=SourceType.BIDS_JSON,
                    path=json_path,
                    source_field=field_name,
                    raw_value=sidecar[field_name],
                )
                entity.evidence.append(ev)
                session.evidence.append(ev)

        # Companion files
        base = json_path.with_suffix("")   # strip .json
        for suffix, attr, source_type in [
            (".nii.gz", "nifti_path", SourceType.NIFTI_HEADER),
            (".bval", "bval_path", SourceType.BVAL),
            (".bvec", "bvec_path", SourceType.BVEC),
        ]:
            candidate = base.with_suffix(suffix) if suffix != ".nii.gz" else Path(str(base) + ".nii.gz")
            if candidate.is_file():
                setattr(entity, attr, candidate)
                ev = _make_evidence(
                    evidence_id=next_ev_id(),
                    source_type=source_type,
                    path=candidate,
                    source_field={
                        SourceType.NIFTI_HEADER: "nifti_header",
                        SourceType.BVAL: "bval",
                        SourceType.BVEC: "bvec",
                    }[source_type],
                    raw_value=None,
                )
                entity.evidence.append(ev)
                session.evidence.append(ev)

        session.dwi_entities.append(entity)

    return session
