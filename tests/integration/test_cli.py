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
