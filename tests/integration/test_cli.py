"""Smoke tests for the CLI: assess → aggregate → explain."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vecta.cli import main as cli_main


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specification" / "v0.1"
FIXTURE_ROOT = REPO_ROOT / "tests" / "synthetic"


def test_cli_assess_then_aggregate(tmp_path: Path):
    per_session = tmp_path / "assessments"
    for fname in (
        "dataset_001_valid",
        "dataset_004_missing_reverse_pe",
        "dataset_010_unknown_pe",
    ):
        rc = cli_main([
            "assess",
            "--dataset", str(FIXTURE_ROOT / fname),
            "--subject", "001",
            "--session", "01",
            "--spec", str(SPEC_ROOT),
            "--output", str(per_session / fname),
            "--formats", "json", "tsv",
        ])
        assert rc == 0
        assert (per_session / fname / "vecta.json").is_file()
        assert (per_session / fname / "vecta.tsv").is_file()

    cohort_dir = tmp_path / "cohort"
    rc = cli_main([
        "aggregate", str(per_session), "--output", str(cohort_dir),
    ])
    assert rc == 0
    for name in (
        "session_summary.tsv",
        "findings_long.tsv",
        "variables_long.tsv",
        "finding_prevalence.tsv",
        "missingness_matrix.tsv",
    ):
        assert (cohort_dir / name).is_file(), f"Missing {name}"

    # Prevalence table should distinguish the three denominators
    prev = (cohort_dir / "finding_prevalence.tsv").read_text().splitlines()
    header = prev[0].split("\t")
    assert "prevalence_over_assessed" in header
    assert "prevalence_over_applicable" in header
    assert "prevalence_over_evaluable" in header


def test_cli_validate_spec(capsys):
    rc = cli_main(["validate-spec", "--spec", str(SPEC_ROOT)])
    assert rc == 0
    err = capsys.readouterr().err
    assert "Specification 0.1.0 valid" in err


def test_cli_join_outcomes(tmp_path: Path):
    # Produce a cohort session_summary.tsv
    per_session = tmp_path / "assessments"
    for fname in ("dataset_001_valid", "dataset_004_missing_reverse_pe"):
        cli_main([
            "assess",
            "--dataset", str(FIXTURE_ROOT / fname),
            "--subject", "001", "--session", "01",
            "--spec", str(SPEC_ROOT),
            "--output", str(per_session / fname),
        ])
    cohort_dir = tmp_path / "cohort"
    cli_main(["aggregate", str(per_session), "--output", str(cohort_dir)])

    # Write a minimal outcomes_long.tsv
    outcomes_tsv = tmp_path / "outcomes_long.tsv"
    outcomes_tsv.write_text(
        "subject_id\tsession_id\toutcome_id\tvalue\tstate\n"
        "001\t01\tVECTA.OUTCOME.QSIPREP_SUCCESS\ttrue\tobserved\n"
        "001\t01\tVECTA.OUTCOME.PREPROC_DWI_AVAILABLE\ttrue\tobserved\n"
    )

    out = tmp_path / "joined"
    rc = cli_main([
        "join-outcomes",
        "--cohort", str(cohort_dir),
        "--outcomes", str(outcomes_tsv),
        "--output", str(out),
    ])
    assert rc == 0
    joined = out / "vecta_x_outcomes.tsv"
    assert joined.is_file()

    import csv
    rows = list(csv.DictReader(joined.open(), delimiter="\t"))
    # Both datasets have same subject/session — they should merge into matched rows
    assert any("VECTA.OUTCOME.QSIPREP_SUCCESS" in r for r in rows)
    # At least one row should have the outcome value
    outcome_vals = [r.get("VECTA.OUTCOME.QSIPREP_SUCCESS", "NA") for r in rows]
    assert "true" in outcome_vals


def test_cli_explain(tmp_path: Path, capsys):
    # Produce a vecta.json with a known finding
    out = tmp_path / "assess"
    cli_main([
        "assess",
        "--dataset", str(FIXTURE_ROOT / "dataset_004_missing_reverse_pe"),
        "--subject", "001", "--session", "01",
        "--spec", str(SPEC_ROOT),
        "--output", str(out),
    ])
    payload = json.loads((out / "vecta.json").read_text())
    finding_id = payload["findings"][0]["finding_id"]

    capsys.readouterr()  # clear
    rc = cli_main([
        "explain",
        "--assessment", str(out / "vecta.json"),
        "--finding-id", finding_id,
    ])
    assert rc == 0
    text = capsys.readouterr().out
    assert "VECTA-DWI-014" in text
    assert "Complementary phase-encoding" in text
    assert "distortion_correction_strategy_constrained" in text
