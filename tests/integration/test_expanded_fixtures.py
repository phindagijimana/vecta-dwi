"""Behavior tests for the expanded synthetic fixture suite (Commit E).

Runs the pipeline for each new fixture and checks the structured
expected.yaml assertions. For dataset_011 also supplies the DICOM
inventory since it exercises the transformation-fidelity criterion.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from vecta.collectors import bids as bids_collector
from vecta.collectors import dicom as dicom_collector
from vecta.output.assemble import (
    assess_session,
    check_referential_integrity,
    to_dict,
    validate_against_schema,
)
from vecta.spec.loader import load as load_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specification" / "v0.1"
SCHEMA_ROOT = SPEC_ROOT / "schemas"
FIXTURE_ROOT = REPO_ROOT / "tests" / "synthetic"


@pytest.fixture(scope="module")
def spec():
    return load_spec(SPEC_ROOT)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "dataset_002_missing_bvec",
        "dataset_003_bval_volume_mismatch",
        "dataset_005_missing_readout",
        "dataset_011_dicom_bids_conflict",
        "dataset_030_fmap_reverse_pe",
        "dataset_040_missing_gradient_files",
        "dataset_060_no_dwi_directory",
    ],
)
def test_expanded_fixture(spec, fixture_name):
    fixture_dir = FIXTURE_ROOT / fixture_name
    expected = yaml.safe_load((fixture_dir / "expected.yaml").read_text())

    session = bids_collector.collect(fixture_dir, subject_id="001", session_id="01")
    dcm_inv = None
    dcm_dir = fixture_dir / "source_dicom"
    if dcm_dir.is_dir():
        dcm_inv = dicom_collector.collect(dcm_dir)

    assessment = assess_session(session, spec, dicom_inventory=dcm_inv)
    payload = to_dict(assessment)

    validate_against_schema(payload, SCHEMA_ROOT)
    check_referential_integrity(payload)

    assert payload["assessment_status"]["state"] == expected["assessment_status_state"]
    assert payload["readiness"]["state"] == expected["readiness_state"]

    for vid, expect in expected.get("variables", {}).items():
        assert vid in payload["variables"], f"Missing variable {vid}"
        v = payload["variables"][vid]
        assert v["value"] == expect["value"], f"{vid}.value: got {v['value']} expected {expect['value']}"
        assert v["state"] == expect["state"], f"{vid}.state: got {v['state']} expected {expect['state']}"

    criteria_by_id = {c["criterion_id"]: c for c in payload["criteria"]}
    for cid, want in expected.get("criteria", {}).items():
        assert cid in criteria_by_id, f"Criterion {cid} not evaluated"
        assert criteria_by_id[cid]["status"] == want, (
            f"{cid} status: got {criteria_by_id[cid]['status']} expected {want}"
        )

    findings_by_crit = {f["criterion_id"]: f for f in payload["findings"]}
    for cid, should_be_present in expected.get("findings_present", {}).items():
        assert (cid in findings_by_crit) == should_be_present, (
            f"Finding for {cid}: got present={cid in findings_by_crit} expected {should_be_present}"
        )
