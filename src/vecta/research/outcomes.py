"""Downstream outcome labeling from QSIPrep / QSIRecon results.

Implements the assignment procedure declared in
`docs/paper1_outcome_labeling_manual.md` §7 for the CIDUR-shape
results layout:

    results_root/
    ├── qsiprep_single_run_output/sub-XXX/ses-YY/dwi/*_desc-preproc_dwi.nii.gz
    │                                              *_desc-preproc_dwi.bvec
    │                                              *_desc-brain_mask.nii.gz
    ├── qsirecon_single_run_output/sub-XXX/...
    └── qc/sub-XXX/subject_qc.json     ← subject-level PASS/FAIL per stage

Per-session outcome (`qsiprep_success`) is authoritative: it is derived
from actual derivative-file presence + structural sanity checks, not
from a log parse. Subject-level flags (qsirecon, connectome, node
strength) are taken from the CIDUR team's `subject_qc.json`.

This module deliberately does NOT parse raw QSIPrep logs. Logs live in
`results_root/logs/`; if they need to be consumed later (e.g. to
attribute a failure to a specific category), that is a separate v0.2
task requiring a stable log-format contract with the pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nibabel as nib

OUTCOME_PROTOCOL_VERSION = "0.1.0"
LABELING_METHOD_ID = "cidur_derivative_qc_v1"


# ── Required-derivative sanity ───────────────────────────────────────────


def _nifti_readable(path: Path, min_nonzero_voxels: int = 0) -> bool:
    try:
        img = nib.load(str(path))
        if min_nonzero_voxels > 0:
            data = img.get_fdata()
            if (data != 0).sum() < min_nonzero_voxels:
                return False
        return True
    except Exception:
        return False


def _bval_parseable(path: Path) -> int | None:
    """Return number of b-value entries, or None on parse failure."""
    try:
        entries = path.read_text().split()
        [float(x) for x in entries]
        return len(entries)
    except Exception:
        return None


def _bvec_parseable(path: Path) -> int | None:
    """Return number of directions (row length), or None on parse failure."""
    try:
        lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]
        if len(lines) != 3:
            return None
        rows = [[float(x) for x in ln.split()] for ln in lines]
        n = len(rows[0])
        if any(len(r) != n for r in rows):
            return None
        return n
    except Exception:
        return None


@dataclass
class SessionDerivativeState:
    preproc_dwi_present: bool = False
    preproc_dwi_readable: bool = False
    bval_present: bool = False
    bval_count: int | None = None
    bvec_present: bool = False
    bvec_count: int | None = None
    brain_mask_present: bool = False
    brain_mask_readable: bool = False
    dwiref_present: bool = False
    counts_match: bool | None = None      # NIfTI dim[4] == bval count == bvec count
    dwi_volume_count: int | None = None


def check_session_derivatives(
    prep_root: Path, subject: str, session: str
) -> SessionDerivativeState:
    """Structural sanity of the required-derivative inventory (labeling manual §3)."""
    ses_dir = prep_root / subject / session / "dwi"
    st = SessionDerivativeState()
    if not ses_dir.is_dir():
        return st

    dwi_files = list(ses_dir.glob("*_space-T1w_desc-preproc_dwi.nii.gz"))
    bval_files = list(ses_dir.glob("*_space-T1w_desc-preproc_dwi.bval"))
    bvec_files = list(ses_dir.glob("*_space-T1w_desc-preproc_dwi.bvec"))
    mask_files = list(ses_dir.glob("*_space-T1w_desc-brain_mask.nii.gz"))
    dwiref_files = list(ses_dir.glob("*_space-T1w_dwiref.nii.gz"))

    st.preproc_dwi_present = len(dwi_files) > 0
    st.bval_present = len(bval_files) > 0
    st.bvec_present = len(bvec_files) > 0
    st.brain_mask_present = len(mask_files) > 0
    st.dwiref_present = len(dwiref_files) > 0

    if st.preproc_dwi_present:
        st.preproc_dwi_readable = _nifti_readable(dwi_files[0])
        if st.preproc_dwi_readable:
            try:
                shape = nib.load(str(dwi_files[0])).header.get_data_shape()
                st.dwi_volume_count = int(shape[3]) if len(shape) >= 4 else 1
            except Exception:
                pass
    if st.bval_present:
        st.bval_count = _bval_parseable(bval_files[0])
    if st.bvec_present:
        st.bvec_count = _bvec_parseable(bvec_files[0])
    if st.brain_mask_present:
        st.brain_mask_readable = _nifti_readable(mask_files[0], min_nonzero_voxels=1000)

    if (st.dwi_volume_count is not None
        and st.bval_count is not None
        and st.bvec_count is not None):
        st.counts_match = (
            st.dwi_volume_count == st.bval_count == st.bvec_count
        )

    return st


# ── subject_qc.json parsing ──────────────────────────────────────────────


@dataclass
class SubjectQC:
    overall_status: str | None = None
    step_status: dict[str, str] = field(default_factory=dict)
    step_summary: dict[str, dict[str, Any]] = field(default_factory=dict)
    generated_at: str | None = None
    raw_path: Path | None = None


def read_subject_qc(qc_root: Path, subject: str) -> SubjectQC | None:
    p = qc_root / subject / "subject_qc.json"
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text())
    except Exception:
        return None
    qc = SubjectQC(
        overall_status=data.get("overall_status"),
        generated_at=data.get("generated_at"),
        raw_path=p,
    )
    for step in data.get("steps", []):
        sid = step.get("id")
        if not sid:
            continue
        qc.step_status[sid] = step.get("status")
        qc.step_summary[sid] = step.get("summary", {})
    return qc


# ── Outcome record ───────────────────────────────────────────────────────


@dataclass
class ResearchOutcome:
    """One session's downstream outcome record.

    Schema matches specification/v0.1/schemas/output/research_outcome.schema.json.
    Populates the outcomes catalog from
    docs/paper1_outcome_labeling_manual.md §6.
    """

    subject_id: str
    session_id: str
    outcome_id: str
    definition_version: str = OUTCOME_PROTOCOL_VERSION
    value: Any = None
    state: str = "observed"    # observed | unknown | not_applicable
    source_refs: list[str] = field(default_factory=list)
    labeling_method: str = LABELING_METHOD_ID
    pipeline_version: str | None = None
    reviewer_refs: list[str] = field(default_factory=list)
    adjudication_status: str = "not_required"
    computed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "outcome_id": self.outcome_id,
            "definition_version": self.definition_version,
            "value": self.value,
            "state": self.state,
            "source_refs": list(self.source_refs),
            "labeling_method": self.labeling_method,
            "pipeline_version": self.pipeline_version,
            "reviewer_refs": list(self.reviewer_refs),
            "adjudication_status": self.adjudication_status,
            "computed_at": self.computed_at,
        }


# ── Assignment procedure ────────────────────────────────────────────────


def _now():
    return datetime.now(timezone.utc).isoformat()


def label_session(
    subject: str,
    session: str,
    results_root: Path,
    pipeline_version: str | None = None,
) -> list[ResearchOutcome]:
    """Emit all outcome records for a single subject/session per §6 catalog.

    subject:      "sub-001"
    session:      "ses-1"
    results_root: /path/to/qsiprep results tree (contains
                  qsiprep_single_run_output/, qc/, qsirecon_single_run_output/)
    """
    prep_root = results_root / "qsiprep_single_run_output"
    qc_root = results_root / "qc"
    now = _now()

    st = check_session_derivatives(prep_root, subject, session)
    qc = read_subject_qc(qc_root, subject)   # subject-level

    # QSIPREP_SUCCESS (primary): all required derivatives present + readable + counts consistent
    qsiprep_ok = (
        st.preproc_dwi_present and st.preproc_dwi_readable
        and st.bval_present and st.bval_count is not None
        and st.bvec_present and st.bvec_count is not None
        and st.brain_mask_present and st.brain_mask_readable
        and st.counts_match is True
    )
    prep_src = f"{prep_root}/{subject}/{session}/dwi/"
    outcomes = [
        ResearchOutcome(
            subject_id=subject, session_id=session,
            outcome_id="VECTA.OUTCOME.QSIPREP_SUCCESS",
            value=qsiprep_ok, state="observed",
            source_refs=[prep_src],
            pipeline_version=pipeline_version,
            computed_at=now,
        ),
        ResearchOutcome(
            subject_id=subject, session_id=session,
            outcome_id="VECTA.OUTCOME.PREPROC_DWI_AVAILABLE",
            value=st.preproc_dwi_present and st.preproc_dwi_readable,
            state="observed",
            source_refs=[prep_src],
            pipeline_version=pipeline_version,
            computed_at=now,
        ),
    ]

    # Subject-level qsirecon / connectome / node-strength flags from
    # subject_qc.json step statuses. If not present, state=unknown.
    def _step(step_id: str, out_id: str) -> ResearchOutcome:
        if qc is None:
            return ResearchOutcome(
                subject_id=subject, session_id=session,
                outcome_id=out_id, value=None, state="unknown",
                source_refs=[], pipeline_version=pipeline_version,
                computed_at=now,
            )
        s = qc.step_status.get(step_id)
        # PASS → True; FAIL → False; SKIP → not_applicable; else unknown
        if s == "PASS":
            return ResearchOutcome(
                subject_id=subject, session_id=session,
                outcome_id=out_id, value=True, state="observed",
                source_refs=[str(qc.raw_path)],
                pipeline_version=pipeline_version, computed_at=now,
            )
        if s == "FAIL":
            return ResearchOutcome(
                subject_id=subject, session_id=session,
                outcome_id=out_id, value=False, state="observed",
                source_refs=[str(qc.raw_path)],
                pipeline_version=pipeline_version, computed_at=now,
            )
        if s == "SKIP":
            return ResearchOutcome(
                subject_id=subject, session_id=session,
                outcome_id=out_id, value=None, state="not_applicable",
                source_refs=[str(qc.raw_path)],
                pipeline_version=pipeline_version, computed_at=now,
            )
        return ResearchOutcome(
            subject_id=subject, session_id=session,
            outcome_id=out_id, value=None, state="unknown",
            source_refs=[str(qc.raw_path)] if qc else [],
            pipeline_version=pipeline_version, computed_at=now,
        )

    outcomes.append(_step("qsirecon", "VECTA.OUTCOME.QSIRECON_SUCCESS"))
    outcomes.append(_step("connectome", "VECTA.OUTCOME.CONNECTOME_AVAILABLE"))
    outcomes.append(_step("nodestrength", "VECTA.OUTCOME.NODESTRENGTH_AVAILABLE"))

    # QC_STATUS from subject_qc.overall_status
    if qc is not None and qc.overall_status:
        outcomes.append(ResearchOutcome(
            subject_id=subject, session_id=session,
            outcome_id="VECTA.OUTCOME.QC_STATUS",
            value=qc.overall_status.lower(),   # 'pass'/'fail'/'warn' per manual §8
            state="observed",
            source_refs=[str(qc.raw_path)],
            pipeline_version=pipeline_version,
            computed_at=now,
        ))
    else:
        outcomes.append(ResearchOutcome(
            subject_id=subject, session_id=session,
            outcome_id="VECTA.OUTCOME.QC_STATUS",
            value=None, state="unknown",
            source_refs=[],
            pipeline_version=pipeline_version,
            computed_at=now,
        ))

    return outcomes


def label_cohort(
    results_root: Path,
    pipeline_version: str | None = None,
) -> list[ResearchOutcome]:
    """Walk the qsiprep_single_run_output/ tree and label every session."""
    prep_root = results_root / "qsiprep_single_run_output"
    all_outcomes = []
    for subj_dir in sorted(prep_root.iterdir()):
        if not subj_dir.is_dir() or not subj_dir.name.startswith("sub-"):
            continue
        subject = subj_dir.name
        session_dirs = sorted(
            p for p in subj_dir.iterdir()
            if p.is_dir() and p.name.startswith("ses-")
        )
        if not session_dirs:
            continue
        for ses_dir in session_dirs:
            all_outcomes.extend(
                label_session(subject, ses_dir.name, results_root, pipeline_version)
            )
    return all_outcomes
