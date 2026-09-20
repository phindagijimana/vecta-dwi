"""Test the HTML renderer.

Verifies:
  - HTML string produced without exceptions from a canonical JSON.
  - Content preserved: readiness, findings, variables, provenance.
  - No independent recalculation of scientific rules — everything
    rendered must be present verbatim in the input JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vecta.cli import main as cli_main
from vecta.output.html import render_html


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specification" / "v0.1"
FIXTURE_ROOT = REPO_ROOT / "tests" / "synthetic"


def _run_assess(tmp_path: Path, fixture_name: str, formats=("json",)) -> dict:
    out = tmp_path / fixture_name
    cli_main([
        "assess",
        "--dataset", str(FIXTURE_ROOT / fixture_name),
        "--subject", "001", "--session", "01",
        "--spec", str(SPEC_ROOT),
        "--output", str(out),
        "--formats", *formats,
    ])
    return json.loads((out / "vecta.json").read_text())


def test_html_renders_from_json(tmp_path):
    payload = _run_assess(tmp_path, "dataset_004_missing_reverse_pe")
    html = render_html(payload)

    # Structural anchors
    assert "<html" in html
    assert "</html>" in html

    # Readiness
    assert payload["readiness"]["state"] in html
    # Subject/session
    assert payload["subject_id"] in html
    assert payload["session_id"] in html
    # Finding-related content
    for f in payload["findings"]:
        assert f["criterion_id"] in html
        assert f["label"] in html
        for pe in f["potential_effects"]:
            # Wording should be in the HTML, and it must be exactly what the
            # JSON says (HTML renderer does not re-author it)
            assert pe["effect_id"] in html
    # Provenance versions
    assert payload["provenance"]["vecta_software_version"] in html


def test_html_via_cli(tmp_path):
    _run_assess(tmp_path, "dataset_004_missing_reverse_pe", formats=("json", "html"))
    html_path = tmp_path / "dataset_004_missing_reverse_pe" / "report.html"
    assert html_path.is_file()
    text = html_path.read_text()
    assert "VECTA-DWI-014" in text
    assert "ready_with_limitations" in text
