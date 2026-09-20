"""End-to-end test with DICOM Source module.

Runs the pipeline with both a BIDS session AND a DICOM inventory, and
verifies the source-integrity + transformation-fidelity criteria evaluate
correctly.
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


def test_dicom_source_module_end_to_end(spec):
    fixture_dir = FIXTURE_ROOT / "dataset_020_dicom_valid"
    expected = yaml.safe_load((fixture_dir / "expected.yaml").read_text())

    session = bids_collector.collect(fixture_dir, subject_id="001", session_id="01")
    inventory = dicom_collector.collect(fixture_dir / "source_dicom")

    assessment = assess_session(session, spec, dicom_inventory=inventory)
    payload = to_dict(assessment)

    validate_against_schema(payload, SCHEMA_ROOT)
    check_referential_integrity(payload)

    # Source-module variables emit only when a DICOM inventory is supplied
    for vid in expected["variables"]:
        assert vid in payload["variables"], f"Missing {vid}"
        got = payload["variables"][vid]
        want = expected["variables"][vid]
        assert got["value"] == want["value"], f"{vid}.value got {got['value']} want {want['value']}"
        assert got["state"] == want["state"], f"{vid}.state got {got['state']} want {want['state']}"

    crit_by_id = {c["criterion_id"]: c for c in payload["criteria"]}
    for cid, want in expected["criteria"].items():
        assert cid in crit_by_id, f"Criterion {cid} not evaluated"
        assert crit_by_id[cid]["status"] == want, f"{cid} status got {crit_by_id[cid]['status']} want {want}"

    findings_by_crit = {f["criterion_id"]: f for f in payload["findings"]}
    for cid, should_be_present in expected["findings_present"].items():
        assert (cid in findings_by_crit) == should_be_present


def test_source_criteria_unknown_when_no_dicom(spec):
    """When assess_session is called without a DICOM inventory, source
    variables are not extracted and source criteria return `unknown`."""
    fixture_dir = FIXTURE_ROOT / "dataset_001_valid"
    session = bids_collector.collect(fixture_dir, subject_id="001", session_id="01")
    assessment = assess_session(session, spec)   # no dicom_inventory
    payload = to_dict(assessment)

    crit_by_id = {c["criterion_id"]: c for c in payload["criteria"]}
    assert crit_by_id["VECTA-DWI-050"]["status"] == "unknown"
    assert crit_by_id["VECTA-DWI-060"]["status"] == "unknown"

    # And no source variables are in the payload
    assert "VECTA.DWI.DICOM.SERIES_COUNT" not in payload["variables"]
