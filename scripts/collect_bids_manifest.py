#!/usr/bin/env python3
"""
collect_bids_manifest.py — Run on the remote machine where full BIDS data lives.

Produces a small TSV (~1 row per session, ~2 KB per session) that documents:
  - Which DWI sidecar fields are present/absent  (PED, TRT, EchoSpacing)
  - Which fieldmap types are present per session (epi, phasediff, magnitude1/2, TB1)
  - Whether each fieldmap set is complete       (both files AND required metadata)
  - QSIPrep failure reason (parsed from the HTML report / log files)

Nothing large is collected — only text metadata.
Transfer back with:
    rsync -avz remote:/path/to/bids_manifest/ ~/Documents/vecta_dwi_tbi_full/bids_manifest/

Usage:
    python collect_bids_manifest.py \
        --bids   /path/to/BIDS_root \
        --qsiprep /path/to/qsiprep_output \
        --output  /path/to/bids_manifest \
        [--subjects sub-001 sub-002 ...]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def read_json_safe(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def field_status(sidecar: dict, field: str) -> str:
    """present | absent | empty"""
    val = sidecar.get(field)
    if val is None:
        return "absent"
    if val == "" or val == [] or val == {}:
        return "empty"
    return "present"


def parse_qsiprep_failure_reason(subject: str, session: str, qsiprep_dir: Path) -> str:
    """
    Parse QSIPrep HTML report or log files for a failure reason.
    Returns one of:
        success | missing_ped | missing_fmap | missing_t1w |
        t1w_quality | topup_failed | freesurfer_failed |
        bids_error | unknown_failure | not_run
    """
    if qsiprep_dir is None:
        return "not_run"

    sub_dir = qsiprep_dir / subject
    if not sub_dir.exists():
        return "not_run"

    ses_dir = sub_dir / session / "dwi" if session else sub_dir / "dwi"
    preproc = list(sub_dir.rglob("*desc-preproc_dwi.nii.gz"))
    if preproc:
        return "success"

    # Check HTML report for failure keywords
    html_reports = list(sub_dir.parent.glob(f"{subject}.html")) + \
                   list(sub_dir.parent.glob(f"{subject}_{session}.html"))

    log_files = list(sub_dir.rglob("*.log")) + \
                list((qsiprep_dir / "logs").glob(f"*{subject}*")) \
                if (qsiprep_dir / "logs").exists() else []

    text = ""
    for f in html_reports + log_files:
        try:
            text += f.read_text(errors="ignore").lower()
        except Exception:
            pass

    if not text:
        return "unknown_failure"

    # Pattern matching — ordered by specificity
    patterns = [
        ("missing_ped",
         r"phaseencodingdirection.*not.*found|"
         r"missing.*phaseencoding|"
         r"no phase.encoding.*direction|"
         r"unable.*determine.*phase"),
        ("missing_fmap",
         r"no fieldmap.*found|"
         r"fieldmap.*not.*found|"
         r"missing.*magnitude|"
         r"missing.*phasediff|"
         r"no.*fmap|"
         r"distortion.correction.*skipped"),
        ("topup_failed",
         r"topup.*error|"
         r"topup.*failed|"
         r"blip.*up.*down.*error"),
        ("missing_t1w",
         r"no t1w.*found|"
         r"t1w.*not.*found|"
         r"missing.*t1w"),
        ("t1w_quality",
         r"t1w.*quality|"
         r"recon.all.*failed|"
         r"freesurfer.*failed|"
         r"registration.*failed"),
        ("bids_error",
         r"bids.*validation.*error|"
         r"bids.*error"),
    ]

    for reason, pattern in patterns:
        if re.search(pattern, text):
            return reason

    return "unknown_failure"


# ── fieldmap inventory ────────────────────────────────────────────────────────

def inventory_fmaps(fmap_dir: Path, dwi_entities: list[str]) -> dict:
    """
    Returns a dict of fieldmap inventory for one session.
    Checks file presence AND key metadata completeness.
    """
    result = {
        # EPI (reverse-PE) fieldmap
        "fmap_epi_present": False,
        "fmap_epi_has_ped": False,
        "fmap_epi_has_trt": False,
        "fmap_epi_intended_for_dwi": False,

        # Phasediff (GRE) fieldmap
        "fmap_phasediff_present": False,
        "fmap_phasediff_has_echotime1": False,
        "fmap_phasediff_has_echotime2": False,
        "fmap_phasediff_has_intended_for": False,
        "fmap_phasediff_nifti_present": False,
        "fmap_magnitude1_present": False,
        "fmap_magnitude2_present": False,
        "fmap_phasediff_set_complete": False,  # all 3 files present + metadata

        # Counts
        "fmap_n_epi": 0,
        "fmap_n_phasediff": 0,
        "fmap_n_magnitude": 0,
    }

    if not fmap_dir.is_dir():
        return result

    # EPI fieldmaps
    epi_jsons = sorted(fmap_dir.glob("*_epi.json"))
    result["fmap_n_epi"] = len(epi_jsons)
    result["fmap_epi_present"] = len(epi_jsons) > 0

    for epi_json in epi_jsons:
        sc = read_json_safe(epi_json)
        if sc.get("PhaseEncodingDirection"):
            result["fmap_epi_has_ped"] = True
        if sc.get("TotalReadoutTime"):
            result["fmap_epi_has_trt"] = True
        intended = sc.get("IntendedFor", [])
        if isinstance(intended, str):
            intended = [intended]
        if any("dwi" in entry.lower() for entry in intended) or not intended:
            result["fmap_epi_intended_for_dwi"] = True

    # Phasediff fieldmap
    phasediff_jsons = sorted(fmap_dir.glob("*_phasediff.json"))
    magnitude1_files = sorted(fmap_dir.glob("*_magnitude1.nii*"))
    magnitude2_files = sorted(fmap_dir.glob("*_magnitude2.nii*"))
    phasediff_niftis = sorted(fmap_dir.glob("*_phasediff.nii*"))

    result["fmap_n_phasediff"] = len(phasediff_jsons)
    result["fmap_phasediff_present"] = len(phasediff_jsons) > 0
    result["fmap_magnitude1_present"] = len(magnitude1_files) > 0
    result["fmap_magnitude2_present"] = len(magnitude2_files) > 0
    result["fmap_phasediff_nifti_present"] = len(phasediff_niftis) > 0
    result["fmap_n_magnitude"] = len(magnitude1_files) + len(magnitude2_files)

    for pd_json in phasediff_jsons:
        sc = read_json_safe(pd_json)
        if sc.get("EchoTime1"):
            result["fmap_phasediff_has_echotime1"] = True
        if sc.get("EchoTime2"):
            result["fmap_phasediff_has_echotime2"] = True
        intended = sc.get("IntendedFor", [])
        if intended:
            result["fmap_phasediff_has_intended_for"] = True

    # A complete phasediff set = magnitude1 + magnitude2 + phasediff.nii + phasediff.json
    # with EchoTime1 + EchoTime2
    result["fmap_phasediff_set_complete"] = (
        result["fmap_phasediff_present"]
        and result["fmap_phasediff_nifti_present"]
        and result["fmap_magnitude1_present"]
        and result["fmap_magnitude2_present"]
        and result["fmap_phasediff_has_echotime1"]
        and result["fmap_phasediff_has_echotime2"]
    )

    return result


# ── DWI sidecar inventory ─────────────────────────────────────────────────────

def inventory_dwi_sidecars(dwi_dir: Path) -> dict:
    """Summarise key field presence across all DWI sidecars in a session."""
    result = {
        "dwi_n_entities": 0,
        "dwi_all_have_ped": True,
        "dwi_all_have_trt": True,
        "dwi_any_missing_ped": False,
        "dwi_any_missing_trt": False,
        "dwi_any_missing_bvec": False,
        "dwi_any_missing_bval": False,
        "dwi_manufacturer": "",
        "dwi_field_strength": "",
        "dwi_pe_directions_observed": "",
    }

    if not dwi_dir.is_dir():
        return result

    jsons = sorted(dwi_dir.glob("*_dwi.json"))
    result["dwi_n_entities"] = len(jsons)
    if not jsons:
        return result

    ped_values = set()
    manufacturers = set()
    field_strengths = set()

    for j in jsons:
        sc = read_json_safe(j)
        ped = sc.get("PhaseEncodingDirection")
        trt = sc.get("TotalReadoutTime")

        if not ped:
            result["dwi_any_missing_ped"] = True
            result["dwi_all_have_ped"] = False
        else:
            ped_values.add(ped)

        if not trt:
            result["dwi_any_missing_trt"] = True
            result["dwi_all_have_trt"] = False

        mfr = sc.get("Manufacturer") or sc.get("ManufacturerModelName", "")
        if mfr:
            manufacturers.add(mfr)
        fs = sc.get("MagneticFieldStrength")
        if fs:
            field_strengths.add(str(fs))

        # Check companion files
        base = j.with_suffix("")
        bvec = Path(str(base) + ".bvec")
        bval = Path(str(base) + ".bval")
        if not bvec.exists():
            result["dwi_any_missing_bvec"] = True
        if not bval.exists():
            result["dwi_any_missing_bval"] = True

    result["dwi_pe_directions_observed"] = "|".join(sorted(ped_values))
    result["dwi_manufacturer"] = "|".join(sorted(manufacturers))
    result["dwi_field_strength"] = "|".join(sorted(field_strengths))

    return result


# ── main ──────────────────────────────────────────────────────────────────────

def collect_session(
    bids_root: Path,
    subject: str,
    session: str,
    qsiprep_dir: Path | None,
) -> dict:
    sub_label = subject.replace("sub-", "")
    ses_label = session.replace("ses-", "")

    row = {
        "subject_id": sub_label,
        "session_id": ses_label,
    }

    dwi_dir = bids_root / subject / session / "dwi"
    fmap_dir = bids_root / subject / session / "fmap"

    row.update(inventory_dwi_sidecars(dwi_dir))
    row.update(inventory_fmaps(fmap_dir, []))

    # QSIPrep failure reason
    qp_reason = "not_run"
    if qsiprep_dir and qsiprep_dir.exists():
        qp_reason = parse_qsiprep_failure_reason(subject, session, qsiprep_dir)
    row["qsiprep_outcome"] = qp_reason
    row["qsiprep_success"] = qp_reason == "success"

    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bids",    required=True,  type=Path)
    ap.add_argument("--qsiprep", required=False, type=Path, default=None)
    ap.add_argument("--output",  required=True,  type=Path)
    ap.add_argument("--subjects", nargs="*", default=None,
                    help="Limit to these subject labels (with or without sub- prefix)")
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # Discover subjects/sessions
    bids_root = args.bids
    subjects = []
    if args.subjects:
        subjects = [s if s.startswith("sub-") else f"sub-{s}" for s in args.subjects]
    else:
        subjects = sorted([
            d.name for d in bids_root.iterdir()
            if d.is_dir() and d.name.startswith("sub-")
        ])

    rows = []
    for sub in subjects:
        sub_dir = bids_root / sub
        sessions = sorted([
            d.name for d in sub_dir.iterdir()
            if d.is_dir() and d.name.startswith("ses-")
        ]) if sub_dir.exists() else []

        if not sessions:
            # sessionless BIDS
            rows.append(collect_session(bids_root, sub, "", args.qsiprep))
        else:
            for ses in sessions:
                rows.append(collect_session(bids_root, sub, ses, args.qsiprep))

    if not rows:
        print("No sessions found.", file=sys.stderr)
        sys.exit(1)

    outfile = args.output / "bids_manifest.tsv"
    with open(outfile, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} sessions → {outfile}")

    # Print quick summary
    n_missing_ped   = sum(1 for r in rows if r["dwi_any_missing_ped"])
    n_missing_trt   = sum(1 for r in rows if r["dwi_any_missing_trt"])
    n_missing_bvec  = sum(1 for r in rows if r["dwi_any_missing_bvec"])
    n_no_epi_fmap   = sum(1 for r in rows if not r["fmap_epi_present"])
    n_pd_incomplete = sum(1 for r in rows
                          if r["fmap_phasediff_present"] and not r["fmap_phasediff_set_complete"])
    n_qp_fail       = sum(1 for r in rows if r["qsiprep_outcome"] not in ("success", "not_run"))

    print(f"\nQuick summary ({len(rows)} sessions):")
    print(f"  Missing PhaseEncodingDirection : {n_missing_ped}")
    print(f"  Missing TotalReadoutTime       : {n_missing_trt}")
    print(f"  Missing bvec file              : {n_missing_bvec}")
    print(f"  No EPI fieldmap                : {n_no_epi_fmap}")
    print(f"  Phasediff present but incomplete: {n_pd_incomplete}")
    print(f"  QSIPrep failures               : {n_qp_fail}")


if __name__ == "__main__":
    main()
