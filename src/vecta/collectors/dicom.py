"""DICOM collector — reads original DICOM series from a CIDUR-style export.

Walks a directory tree, groups files by SeriesInstanceUID, and produces
per-series inventory records. Header-only reads (stop_before_pixels=True)
keep this fast enough to run on login nodes before preprocessing (Spec
Blueprint §36 performance guidance).

Layout supported:
  <root>/<any-nesting>/<file>.dcm
  <root>/<any-nesting>/<file>          # DICOM files often lack .dcm extension

The collector does NOT interpret series identity beyond DICOM's own
SeriesInstanceUID; series classification (dwi vs t1 vs fmap) happens in
a dedicated classifier reused from the dbi/ v1 rules.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pydicom
from pydicom.errors import InvalidDicomError

from ..enums import PrivacyStatus, SourceType
from ..models import EvidenceRecord

COLLECTOR_ID = "dicom_collector"
COLLECTOR_VERSION = "0.1.0"


@dataclass
class DicomInstance:
    path: Path
    sop_instance_uid: str | None
    instance_number: int | None


@dataclass
class DicomSeries:
    series_uid: str
    series_number: int | None
    series_description: str | None
    modality: str | None
    manufacturer: str | None
    manufacturer_model_name: str | None
    magnetic_field_strength: float | None
    software_versions: str | None
    protocol_name: str | None
    study_uid: str | None
    instances: list[DicomInstance] = field(default_factory=list)
    # Geometry (recorded from first readable instance)
    pixel_spacing: list[float] | None = None
    slice_thickness: float | None = None
    spacing_between_slices: float | None = None
    rows: int | None = None
    columns: int | None = None
    # Diffusion (from first readable instance if present)
    in_plane_pe_direction: str | None = None
    # Header-agreement flags recorded during collection
    geometry_consistent: bool = True
    duplicate_sop_instances: int = 0


@dataclass
class DicomInventory:
    root: Path
    series: dict[str, DicomSeries] = field(default_factory=dict)
    unreadable_files: list[Path] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)


# ─── Header extraction helpers ────────────────────────────────────────────


def _get(ds, keyword, default=None):
    """Safe DICOM attribute access."""
    try:
        val = getattr(ds, keyword)
    except (AttributeError, KeyError):
        return default
    if val is None or (isinstance(val, str) and not val.strip()):
        return default
    return val


def _to_float(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _iter_dicom_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        # Skip obvious non-DICOM
        if p.name.startswith("."):
            continue
        yield p


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()


# ─── Collection ───────────────────────────────────────────────────────────


def collect(root: Path) -> DicomInventory:
    """Scan `root` for DICOM files, group by SeriesInstanceUID, and record
    per-series inventory + evidence. Header-only read; pixel data is not
    loaded."""
    root = Path(root)
    inventory = DicomInventory(root=root)

    if not root.is_dir():
        return inventory

    series_dupe_tracker: dict[str, set[str]] = defaultdict(set)
    geom_ref: dict[str, tuple[Any, Any, Any]] = {}

    ev_counter = 0
    def next_ev_id() -> str:
        nonlocal ev_counter
        ev_counter += 1
        return f"ev-dcm-{ev_counter:05d}"

    for path in _iter_dicom_files(root):
        try:
            ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=False)
        except (InvalidDicomError, Exception):
            inventory.unreadable_files.append(path)
            continue

        series_uid = _get(ds, "SeriesInstanceUID")
        if series_uid is None:
            inventory.unreadable_files.append(path)
            continue

        if series_uid not in inventory.series:
            inventory.series[series_uid] = DicomSeries(
                series_uid=series_uid,
                series_number=_get(ds, "SeriesNumber"),
                series_description=_get(ds, "SeriesDescription"),
                modality=_get(ds, "Modality"),
                manufacturer=_get(ds, "Manufacturer"),
                manufacturer_model_name=_get(ds, "ManufacturerModelName"),
                magnetic_field_strength=_to_float(_get(ds, "MagneticFieldStrength")),
                software_versions=str(_get(ds, "SoftwareVersions") or "") or None,
                protocol_name=_get(ds, "ProtocolName"),
                study_uid=_get(ds, "StudyInstanceUID"),
                pixel_spacing=[
                    float(x) for x in (_get(ds, "PixelSpacing") or [])
                ] or None,
                slice_thickness=_to_float(_get(ds, "SliceThickness")),
                spacing_between_slices=_to_float(_get(ds, "SpacingBetweenSlices")),
                rows=_get(ds, "Rows"),
                columns=_get(ds, "Columns"),
                in_plane_pe_direction=_get(ds, "InPlanePhaseEncodingDirection"),
            )
            geom_ref[series_uid] = (
                inventory.series[series_uid].pixel_spacing,
                inventory.series[series_uid].slice_thickness,
                (inventory.series[series_uid].rows, inventory.series[series_uid].columns),
            )
            # One evidence record per series, marking the first-file source
            ev = EvidenceRecord(
                evidence_id=next_ev_id(),
                source_type=SourceType.DICOM_HEADER,
                source_locator=str(path),
                source_field="SeriesInstanceUID",
                raw_value=series_uid,
                source_hash=None,   # per-file hash on many DICOMs is expensive; skip in v0.1
                collector_id=COLLECTOR_ID,
                collector_version=COLLECTOR_VERSION,
                privacy_status=PrivacyStatus.RESTRICTED,   # DICOM headers may carry PHI-adjacent info
                timestamp=datetime.now(timezone.utc),
            )
            inventory.evidence.append(ev)

        s = inventory.series[series_uid]

        # Instance-level tracking
        sop_uid = _get(ds, "SOPInstanceUID")
        instance_number = _get(ds, "InstanceNumber")
        if sop_uid is not None:
            if sop_uid in series_dupe_tracker[series_uid]:
                s.duplicate_sop_instances += 1
            else:
                series_dupe_tracker[series_uid].add(sop_uid)
        s.instances.append(DicomInstance(path=path, sop_instance_uid=sop_uid, instance_number=instance_number))

        # Geometry consistency check within the series
        current_geom = (
            [float(x) for x in (_get(ds, "PixelSpacing") or [])] or None,
            _to_float(_get(ds, "SliceThickness")),
            (_get(ds, "Rows"), _get(ds, "Columns")),
        )
        ref = geom_ref[series_uid]
        if (
            (current_geom[0] is not None and ref[0] is not None and current_geom[0] != ref[0])
            or (current_geom[1] is not None and ref[1] is not None and current_geom[1] != ref[1])
            or (current_geom[2] != ref[2])
        ):
            s.geometry_consistent = False

    return inventory


# ─── Classification (lifted from dbi/ v1 substring rules) ────────────────

# Ordered — first match wins. Kept simple and stable for v0.1; a future
# revision should replace substring rules with the community-standards
# regexes from dbi/ v1 config (evidence-linked in evidence_registry.yaml).
CLASS_RULES = [
    ("fmap", ("field_map", "field map", "gre_field", "FMRI_field")),
    ("dwi", ("DTI", "DWI", "DIFFUSION", "dwi", "dti", "DIFF")),
    ("bold", ("fMRI", "fmri", "BOLD", "RESTING", "rsfMRI", "TASK", "EPI")),
    ("asl", ("ASL", "PCASL", "PASL")),
    ("swi", ("SWI", "SWAN")),
    ("flair", ("FLAIR", "flair")),
    ("perf", ("perf", "DSC", "DCE", "perfusion", "CBF")),
    ("t1_anat", ("MPRAGE", "MP-RAGE", "MP_RAGE", "MP RAGE", "SPGR", "FSPGR", "BRAVO", "IR FSPGR", "IR_FSPGR")),
    ("t2_anat", ("T2", "BLADE")),
    ("localizer", ("localizer", "Localizer", "LOC", "scout", "Scout")),
]


def classify_series(series: DicomSeries) -> str:
    """Return one of {dwi, bold, asl, fmap, swi, flair, perf, t1_anat,
    t2_anat, localizer, other}. Substring match on the series description
    + protocol name, first rule to match wins."""
    haystack = " ".join(
        s for s in (series.series_description, series.protocol_name) if s
    )
    for cls, tokens in CLASS_RULES:
        for tok in tokens:
            if tok in haystack:
                return cls
    return "other"


def series_by_class(inventory: DicomInventory) -> dict[str, list[DicomSeries]]:
    """Group DicomInventory.series by classify_series() result."""
    by_class: dict[str, list[DicomSeries]] = defaultdict(list)
    for s in inventory.series.values():
        by_class[classify_series(s)].append(s)
    return dict(by_class)
