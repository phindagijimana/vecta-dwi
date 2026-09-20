"""End-to-end test of the first vertical slice.

For each synthetic BIDS fixture:
  1. Load the specification (fails fast if any YAML is malformed).
  2. Collect the BIDS session.
  3. Assemble the Assessment via the pipeline.
  4. Serialize to JSON and validate against the top-level output schema.
  5. Check referential integrity of every ID in the output.
  6. Compare against the expected.yaml assertions.

The expected.yaml files are intentionally structural (states, values,
finding presence) rather than byte-exact JSON matches, so that volatile
fields (timestamps, UUIDs, file hashes) don't break tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from vecta.collectors import bids as bids_collector
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
    ["dataset_001_valid", "dataset_004_missing_reverse_pe", "dataset_010_unknown_pe"],
)
def test_first_slice_fixture(spec, fixture_name):
    fixture_dir = FIXTURE_ROOT / fixture_name
    expected = yaml.safe_load((fixture_dir / "expected.yaml").read_text())

    session = bids_collector.collect(fixture_dir, subject_id="001", session_id="01")
    assessment = assess_session(session, spec)

    payload = to_dict(assessment)

    # 1. Schema validation
    validate_against_schema(payload, SCHEMA_ROOT)

    # 2. Referential integrity
    check_referential_integrity(payload)

    # 3. Behavior assertions
    assert payload["assessment_status"]["state"] == expected["assessment_status_state"]
    assert payload["readiness"]["state"] == expected["readiness_state"]

    for vid, expect in expected.get("variables", {}).items():
        assert vid in payload["variables"], f"Missing variable {vid}"
        v = payload["variables"][vid]
        assert v["value"] == expect["value"], f"{vid} value: got {v['value']} expected {expect['value']}"
        assert v["state"] == expect["state"], f"{vid} state: got {v['state']} expected {expect['state']}"

    criteria_by_id = {c["criterion_id"]: c for c in payload["criteria"]}
    for cid, expected_status in expected.get("criteria", {}).items():
        assert cid in criteria_by_id, f"Criterion {cid} not evaluated"
        assert criteria_by_id[cid]["status"] == expected_status, (
            f"{cid} status: got {criteria_by_id[cid]['status']} expected {expected_status}"
        )

    findings_by_crit = {f["criterion_id"]: f for f in payload["findings"]}
    for cid, should_be_present in expected.get("findings_present", {}).items():
        present = cid in findings_by_crit
        assert present == should_be_present, (
            f"Finding for {cid}: got present={present} expected={should_be_present}"
        )

    for cid, detail in expected.get("finding_details", {}).items():
        assert cid in findings_by_crit, f"Expected finding for {cid} not emitted"
        f = findings_by_crit[cid]
        assert f["severity"] == detail["severity"]
        assert f["severity_status"] == detail["severity_status"]
        assert f["category"] == detail["category"]
        # Every potential_effect must have causal_claim=false (invariant from spec).
        assert all(pe["causal_claim"] is False for pe in f["potential_effects"])


def test_dataset_010_prohibited_behavior(spec):
    """Regression against the Output Tech Spec §55 prohibited case:
    when PE is unknown, REVERSE_PE_AVAILABLE must NOT be reported as false."""
    fixture = FIXTURE_ROOT / "dataset_010_unknown_pe"
    session = bids_collector.collect(fixture, subject_id="001", session_id="01")
    assessment = assess_session(session, spec)
    payload = to_dict(assessment)
    rev = payload["variables"]["VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE"]
    assert rev["value"] is None, "PROHIBITED: reverse_pe_available must not be false when PE is unknown"
    assert rev["state"] == "unknown"
