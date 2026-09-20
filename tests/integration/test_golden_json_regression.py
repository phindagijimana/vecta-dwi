"""Golden JSON regression tests.

For each fixture with a corresponding tests/golden/<name>.expected.json,
normalize volatile fields in the emitted vecta.json (UUIDs, timestamps,
file hashes, source paths that depend on the working directory) and
diff against the golden. Any structural change to output requires an
explicit golden update.

This is the deterministic-reproducibility guarantee from Spec Blueprint
§27-28 and Output Tech Spec §52.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from vecta.cli import main as cli_main


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = REPO_ROOT / "specification" / "v0.1"
FIXTURE_ROOT = REPO_ROOT / "tests" / "synthetic"
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"

ISO8601_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
HASH_RE = re.compile(r"sha256:[0-9a-f]{64}")


def _normalize(node, fixture_root: Path):
    """Replace volatile values in a nested payload with stable placeholders."""
    if isinstance(node, dict):
        return {k: _normalize(v, fixture_root) for k, v in node.items()}
    if isinstance(node, list):
        return [_normalize(v, fixture_root) for v in node]
    if isinstance(node, str):
        s = node
        s = ISO8601_RE.sub("<TIMESTAMP>", s)
        s = UUID_RE.sub("<UUID>", s)
        s = HASH_RE.sub("<HASH>", s)
        # Strip absolute fixture path (workdir-dependent)
        s = s.replace(str(fixture_root.resolve()), "<FIXTURE_ROOT>")
        return s
    return node


def _emit(fixture_name: str, tmp_path: Path) -> dict:
    out = tmp_path / fixture_name
    cli_main([
        "assess",
        "--dataset", str(FIXTURE_ROOT / fixture_name),
        "--subject", "001", "--session", "01",
        "--spec", str(SPEC_ROOT),
        "--output", str(out),
    ])
    return json.loads((out / "vecta.json").read_text())


# ── Regenerate mode ────────────────────────────────────────────────────
#
# Run `VECTA_REGEN_GOLDEN=1 pytest tests/integration/test_golden_json_regression.py`
# to overwrite the goldens after an intentional behavior change.

import os
REGEN = os.environ.get("VECTA_REGEN_GOLDEN") == "1"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "dataset_001_valid",
        "dataset_004_missing_reverse_pe",
        "dataset_010_unknown_pe",
        "dataset_002_missing_bvec",
        "dataset_005_missing_readout",
    ],
)
def test_golden_json(fixture_name, tmp_path):
    payload = _emit(fixture_name, tmp_path)
    fixture_dir = FIXTURE_ROOT / fixture_name
    normalized = _normalize(payload, fixture_dir)

    golden_path = GOLDEN_DIR / f"{fixture_name}.expected.json"
    if REGEN or not golden_path.is_file():
        GOLDEN_DIR.mkdir(exist_ok=True)
        golden_path.write_text(json.dumps(normalized, indent=2, sort_keys=True))
        if not REGEN:
            pytest.skip(f"Golden not present; wrote initial: {golden_path.name}")
        return

    expected = json.loads(golden_path.read_text())
    if normalized != expected:
        # Diff at the top-level keys to make failures readable
        diffs = []
        for k in sorted(set(normalized) | set(expected)):
            if normalized.get(k) != expected.get(k):
                diffs.append(k)
        pytest.fail(
            f"Golden mismatch for {fixture_name}. Differing top-level keys: {diffs}\n"
            f"To regenerate: VECTA_REGEN_GOLDEN=1 pytest -k {fixture_name}"
        )
