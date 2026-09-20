"""Test the ResearchOutcome extractor against a mock QSIPrep results tree."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import nibabel as nib
import pytest

from vecta.research.outcomes import (
    check_session_derivatives,
    label_session,
    read_subject_qc,
)


def _write_dwi_bundle(dwi_dir: Path, base: str, n_vols: int = 7):
    dwi_dir.mkdir(parents=True, exist_ok=True)
    data = np.ones((3, 3, 3, n_vols), dtype=np.int16)
    img = nib.Nifti1Image(data, np.diag([2.0, 2.0, 2.0, 1.0]))
    nib.save(img, str(dwi_dir / f"{base}.nii.gz"))
    (dwi_dir / f"{base}.bval").write_text(" ".join(["1000"] * n_vols) + "\n")
    (dwi_dir / f"{base}.bvec").write_text(
        " ".join(["1"] * n_vols) + "\n"
        + " ".join(["0"] * n_vols) + "\n"
        + " ".join(["0"] * n_vols) + "\n"
    )


def _write_mask(dwi_dir: Path, base: str):
    # Brain mask with ≥1000 non-zero voxels (labeling manual §3)
    data = np.ones((15, 15, 15), dtype=np.int16)
    img = nib.Nifti1Image(data, np.diag([1.0, 1.0, 1.0, 1.0]))
    nib.save(img, str(dwi_dir / f"{base}.nii.gz"))


def _write_dwiref(dwi_dir: Path, base: str):
    data = np.ones((3, 3, 3), dtype=np.int16)
    img = nib.Nifti1Image(data, np.diag([2.0, 2.0, 2.0, 1.0]))
    nib.save(img, str(dwi_dir / f"{base}.nii.gz"))


def _build_mock_results(root: Path, success_subject: str, failure_subject: str, qc_root_status="PASS"):
    """Create qsiprep_single_run_output + qc/ shape for two subjects."""
    prep = root / "qsiprep_single_run_output"
    for subj, complete in ((success_subject, True), (failure_subject, False)):
        dwi_dir = prep / subj / "ses-1" / "dwi"
        base = f"{subj}_ses-1_dir-ap_space-T1w_desc-preproc_dwi"
        mask = f"{subj}_ses-1_dir-ap_space-T1w_desc-brain_mask"
        dwiref = f"{subj}_ses-1_dir-ap_space-T1w_dwiref"
        if complete:
            _write_dwi_bundle(dwi_dir, base)
            _write_mask(dwi_dir, mask)
            _write_dwiref(dwi_dir, dwiref)
        else:
            # Half-complete: NIfTI present but no bval/bvec, no mask
            dwi_dir.mkdir(parents=True, exist_ok=True)
            data = np.ones((3, 3, 3, 7), dtype=np.int16)
            nib.save(nib.Nifti1Image(data, np.diag([2.0, 2.0, 2.0, 1.0])),
                     str(dwi_dir / f"{base}.nii.gz"))

    # subject_qc.json for success subject only
    qc_dir = root / "qc" / success_subject
    qc_dir.mkdir(parents=True, exist_ok=True)
    (qc_dir / "subject_qc.json").write_text(json.dumps({
        "pipeline": "DKT Connectome",
        "subject": success_subject,
        "overall_status": qc_root_status,
        "generated_at": "2026-09-19T00:00:00Z",
        "steps": [
            {"id": "qsiprep", "status": "PASS", "summary": {}},
            {"id": "qsirecon", "status": "PASS", "summary": {}},
            {"id": "connectome", "status": "PASS", "summary": {"nodes": 78}},
            {"id": "nodestrength", "status": "PASS", "summary": {}},
        ],
    }, indent=2))


def test_success_session_outcomes(tmp_path):
    _build_mock_results(tmp_path, "sub-001", "sub-002")
    outcomes = label_session("sub-001", "ses-1", tmp_path, pipeline_version="mock-v1")
    by_id = {o.outcome_id: o for o in outcomes}
    assert by_id["VECTA.OUTCOME.QSIPREP_SUCCESS"].value is True
    assert by_id["VECTA.OUTCOME.QSIPREP_SUCCESS"].state == "observed"
    assert by_id["VECTA.OUTCOME.PREPROC_DWI_AVAILABLE"].value is True
    assert by_id["VECTA.OUTCOME.QSIRECON_SUCCESS"].value is True
    assert by_id["VECTA.OUTCOME.CONNECTOME_AVAILABLE"].value is True
    assert by_id["VECTA.OUTCOME.NODESTRENGTH_AVAILABLE"].value is True
    assert by_id["VECTA.OUTCOME.QC_STATUS"].value == "pass"


def test_failure_session_outcomes(tmp_path):
    """Failure subject has NIfTI but no bval/bvec/mask; no subject_qc.json."""
    _build_mock_results(tmp_path, "sub-001", "sub-002")
    outcomes = label_session("sub-002", "ses-1", tmp_path, pipeline_version="mock-v1")
    by_id = {o.outcome_id: o for o in outcomes}
    assert by_id["VECTA.OUTCOME.QSIPREP_SUCCESS"].value is False
    assert by_id["VECTA.OUTCOME.PREPROC_DWI_AVAILABLE"].value is True   # NIfTI is present + readable
    # Subject-level flags unknown (no subject_qc.json)
    assert by_id["VECTA.OUTCOME.QSIRECON_SUCCESS"].value is None
    assert by_id["VECTA.OUTCOME.QSIRECON_SUCCESS"].state == "unknown"
    assert by_id["VECTA.OUTCOME.QC_STATUS"].value is None
    assert by_id["VECTA.OUTCOME.QC_STATUS"].state == "unknown"


def test_derivative_counts_mismatch(tmp_path):
    """NIfTI has 7 volumes but bval has 8 → counts_match=False → QSIPREP_SUCCESS=False."""
    prep = tmp_path / "qsiprep_single_run_output"
    dwi_dir = prep / "sub-003" / "ses-1" / "dwi"
    base = "sub-003_ses-1_dir-ap_space-T1w_desc-preproc_dwi"
    _write_dwi_bundle(dwi_dir, base, n_vols=7)
    # Overwrite bval with 8 entries
    (dwi_dir / f"{base}.bval").write_text(" ".join(["1000"] * 8) + "\n")
    _write_mask(dwi_dir, f"sub-003_ses-1_dir-ap_space-T1w_desc-brain_mask")

    st = check_session_derivatives(prep, "sub-003", "ses-1")
    assert st.counts_match is False
    outcomes = label_session("sub-003", "ses-1", tmp_path)
    by_id = {o.outcome_id: o for o in outcomes}
    assert by_id["VECTA.OUTCOME.QSIPREP_SUCCESS"].value is False


def test_step_skip_becomes_not_applicable(tmp_path):
    """A 'SKIP' step (e.g. disconnectome skipped for non-lesion subject)
    maps to state=not_applicable, not False."""
    _build_mock_results(tmp_path, "sub-001", "sub-002")
    # Rewrite the subject_qc.json to mark connectome as SKIP
    qc = tmp_path / "qc" / "sub-001" / "subject_qc.json"
    data = json.loads(qc.read_text())
    for step in data["steps"]:
        if step["id"] == "connectome":
            step["status"] = "SKIP"
    qc.write_text(json.dumps(data, indent=2))

    outcomes = label_session("sub-001", "ses-1", tmp_path)
    by_id = {o.outcome_id: o for o in outcomes}
    assert by_id["VECTA.OUTCOME.CONNECTOME_AVAILABLE"].value is None
    assert by_id["VECTA.OUTCOME.CONNECTOME_AVAILABLE"].state == "not_applicable"


def test_outcomes_validate_against_schema(tmp_path):
    """Every emitted outcome record must validate against research_outcome.schema.json."""
    import json
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    from jsonschema import Draft202012Validator

    REPO = Path(__file__).resolve().parents[2]
    SCHEMA_ROOT = REPO / "specification" / "v0.1" / "schemas"
    schema = json.loads((SCHEMA_ROOT / "output" / "research_outcome.schema.json").read_text())

    registry = Registry()
    for f in SCHEMA_ROOT.rglob("*.schema.json"):
        doc = json.loads(f.read_text())
        if doc.get("$id"):
            registry = registry.with_resource(doc["$id"], Resource(contents=doc, specification=DRAFT202012))
        registry = registry.with_resource("file://" + str(f.resolve()),
                                          Resource(contents=doc, specification=DRAFT202012))
    validator = Draft202012Validator(schema, registry=registry)

    _build_mock_results(tmp_path, "sub-001", "sub-002")
    all_outcomes = label_session("sub-001", "ses-1", tmp_path)
    all_outcomes += label_session("sub-002", "ses-1", tmp_path)
    for o in all_outcomes:
        payload = o.to_dict()
        errors = list(validator.iter_errors(payload))
        assert not errors, f"Outcome {o.outcome_id} failed schema: {errors}"
