"""Re-run Vecta assessment for all CIDUR DWI sessions with DICOM Source module.

Reads subject_mapping.csv to map BIDS sub-IDs → EP_IDs, finds the
per-session DICOM root, and re-runs vecta assess --dicom for every
session that was previously assessed. Writes outputs to
data/cidur_vecta_run/per_session/ (overwriting the BIDS-only assessments).
Then re-runs aggregate + label-outcomes + join-outcomes.

Usage:
    python3.11 scripts/run_cidur_dicom.py
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from vecta.collectors import bids as bids_collector
from vecta.collectors import dicom as dicom_collector
from vecta.output.assemble import (
    assess_session,
    check_referential_integrity,
    to_dict,
    validate_against_schema,
)
from vecta.output import cohort as cohort_module
from vecta.research.outcomes import label_cohort, QSIPREP_VERSION_CIDUR
from vecta.spec.loader import load as load_spec

# ── Paths ────────────────────────────────────────────────────────────────
SPEC_ROOT    = REPO / "specification" / "v0.1"
SCHEMA_ROOT  = SPEC_ROOT / "schemas"
BIDS_ROOT    = Path("/mnt/nfs/home/URMC-SH/pndagiji/Documents/CIDUR_BIDS/data_bids")
DICOM_ROOT   = Path("/mnt/nfs/home/urmc-sh.rochester.edu/pndagiji/Documents/CIDUR_data")
MAPPING_CSV  = Path("/mnt/nfs/home/URMC-SH/pndagiji/Documents/CIDUR_BIDS/subject_mapping.csv")
QSIPREP_ROOT = Path("/mnt/nfs/Gugger_Lab/NIR/dwi_CIDUR/results")
OUT_ROOT     = REPO / "data" / "cidur_vecta_run"
PER_SESSION  = OUT_ROOT / "per_session"
COHORT_DIR   = OUT_ROOT / "cohort"
OUTCOMES_DIR = OUT_ROOT / "outcomes"


def load_mapping() -> dict[str, str]:
    """Return {bids_numeric_id: ep_id}, e.g. {'001': 'EP007361'}."""
    m = {}
    with open(MAPPING_CSV) as f:
        for row in csv.DictReader(f):
            bids_id = row["BIDS_ID"]          # sub-001
            ep_id   = row["EP_ID"]             # EP007361
            numeric = bids_id.replace("sub-", "")
            m[numeric] = ep_id
    return m


def find_dicom_session_dir(ep_id: str, session_number: int) -> Path | None:
    """Return the DICOM session root for a given EP_ID and BIDS session number.

    Session directory layout:
        DICOM_ROOT/EP_ID/EP_ID/{EP_ID}_MR_1/     ← ses-1
                                {EP_ID}_MR_2/     ← ses-2
                                {EP_ID}_PETMR_1/  ← ses-3 (if MR_1+MR_2 exist)
    We sort all session directories alphabetically and pick index (session_number-1).
    """
    inner = DICOM_ROOT / ep_id / ep_id
    if not inner.is_dir():
        return None
    dirs = sorted(
        d for d in inner.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    idx = session_number - 1
    if idx < 0 or idx >= len(dirs):
        return None
    return dirs[idx]


def run_session(
    subject_id: str,
    session_id: str,
    spec,
    mapping: dict[str, str],
) -> dict | None:
    ep_id = mapping.get(subject_id)
    if ep_id is None:
        log.warning("No EP_ID for sub-%s — skipping DICOM", subject_id)
        return None

    try:
        ses_num = int(session_id)
    except ValueError:
        log.warning("Cannot parse session_id=%s — skipping DICOM", session_id)
        return None

    dicom_ses_dir = find_dicom_session_dir(ep_id, ses_num)
    if dicom_ses_dir is None:
        log.warning("sub-%s ses-%s: DICOM dir not found (ep=%s)", subject_id, session_id, ep_id)
        return None

    log.info("sub-%s ses-%s  DICOM=%s", subject_id, session_id, dicom_ses_dir.name)
    t0 = time.time()

    try:
        session = bids_collector.collect(
            BIDS_ROOT, subject_id=subject_id, session_id=session_id
        )
        dcm_inv = dicom_collector.collect(dicom_ses_dir)
        assessment = assess_session(session, spec, dicom_inventory=dcm_inv)
        payload = to_dict(assessment)
        validate_against_schema(payload, SCHEMA_ROOT)
        check_referential_integrity(payload)
    except Exception as exc:
        log.error("sub-%s ses-%s FAILED: %s", subject_id, session_id, exc)
        return None

    elapsed = time.time() - t0
    log.info(
        "  → readiness=%s  findings=%d  DICOM series=%d  (%.1fs)",
        payload["readiness"]["state"],
        len(payload["findings"]),
        len(dcm_inv.series),
        elapsed,
    )
    return payload


def main():
    log.info("Loading spec …")
    spec = load_spec(SPEC_ROOT, profile_id="dwi_connectomics")

    log.info("Loading subject mapping …")
    mapping = load_mapping()

    # Read the session list from existing session_summary.tsv
    summary_path = COHORT_DIR / "session_summary.tsv"
    sessions = []
    with open(summary_path) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            sessions.append((row["subject_id"], row["session_id"]))
    log.info("Sessions to process: %d", len(sessions))

    PER_SESSION.mkdir(parents=True, exist_ok=True)

    payloads = []
    failed = []
    for i, (subj, ses) in enumerate(sessions, 1):
        log.info("[%d/%d] sub-%s ses-%s", i, len(sessions), subj, ses)
        out_dir = PER_SESSION / f"sub-{subj}_ses-{ses}"
        out_dir.mkdir(exist_ok=True)

        payload = run_session(subj, ses, spec, mapping)
        if payload is None:
            # Fall back to existing BIDS-only assessment
            existing = out_dir / "vecta.json"
            if existing.is_file():
                payload = json.loads(existing.read_text())
                log.info("  → using existing BIDS-only assessment")
            else:
                failed.append((subj, ses))
                continue

        (out_dir / "vecta.json").write_text(json.dumps(payload, indent=2))
        payloads.append(payload)

    # ── Re-aggregate ──────────────────────────────────────────────────
    log.info("Aggregating %d sessions …", len(payloads))
    COHORT_DIR.mkdir(exist_ok=True)
    result = cohort_module.aggregate(payloads)
    (COHORT_DIR / "session_summary.tsv").write_text(cohort_module.render_session_summary(result))
    (COHORT_DIR / "findings_long.tsv").write_text(cohort_module.render_findings_long(result))
    (COHORT_DIR / "variables_long.tsv").write_text(cohort_module.render_variables_long(result))
    (COHORT_DIR / "finding_prevalence.tsv").write_text(cohort_module.render_finding_prevalence(result))
    (COHORT_DIR / "missingness_matrix.tsv").write_text(cohort_module.render_missingness_matrix(result))
    log.info("Cohort artifacts written to %s", COHORT_DIR)

    # ── Re-label outcomes ─────────────────────────────────────────────
    log.info("Labeling outcomes …")
    outcomes = label_cohort(QSIPREP_ROOT, pipeline_version=QSIPREP_VERSION_CIDUR)
    OUTCOMES_DIR.mkdir(exist_ok=True)
    lines = ["subject_id\tsession_id\toutcome_id\tvalue\tstate"]
    for o in outcomes:
        val = "" if o.value is None else str(o.value)
        lines.append(f"{o.subject_id}\t{o.session_id}\t{o.outcome_id}\t{val}\t{o.state}")
    outcomes_tsv = OUTCOMES_DIR / "outcomes_long.tsv"
    outcomes_tsv.write_text("\n".join(lines) + "\n")

    # ── Re-join ───────────────────────────────────────────────────────
    log.info("Joining Vecta × outcomes …")
    import csv as csv_mod
    outcome_ids: list[str] = []
    outcomes_wide: dict[tuple, dict] = {}
    with outcomes_tsv.open() as fh:
        for row in csv_mod.DictReader(fh, delimiter="\t"):
            # outcomes use "sub-001"/"ses-1"; session_summary uses "001"/"1"
            subj = row["subject_id"].removeprefix("sub-")
            ses  = row["session_id"].removeprefix("ses-")
            key = (subj, ses)
            oid = row["outcome_id"]
            outcomes_wide.setdefault(key, {})[oid] = row.get("value", "")
            if oid not in outcome_ids:
                outcome_ids.append(oid)

    with (COHORT_DIR / "session_summary.tsv").open() as fh:
        summary_rows = list(csv_mod.DictReader(fh, delimiter="\t"))
        summary_fields = list(summary_rows[0].keys()) if summary_rows else []

    joined_fields = summary_fields + outcome_ids
    joined_rows = []
    for s in summary_rows:
        key = (s.get("subject_id", ""), s.get("session_id", ""))
        o = outcomes_wide.get(key, {})
        row = dict(s)
        for oid in outcome_ids:
            row[oid] = o.get(oid, "NA")
        joined_rows.append(row)

    join_path = OUT_ROOT / "vecta_x_outcomes.tsv"
    with join_path.open("w", newline="") as fh:
        writer = csv_mod.DictWriter(fh, fieldnames=joined_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(joined_rows)

    log.info("vecta_x_outcomes.tsv written")

    if failed:
        log.warning("Failed sessions (%d): %s", len(failed), failed)

    log.info("Done. %d/%d sessions processed with DICOM.", len(payloads), len(sessions))


if __name__ == "__main__":
    main()
