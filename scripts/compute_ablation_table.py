#!/usr/bin/env python3
"""
compute_ablation_table.py

Produces the 4-level ablation comparison table for Paper 1:

  Level 0 — BIDS Validator only
             Flag session if BIDS_VALIDATOR_ERROR_COUNT > 0
  Level 1 — Basic metadata check
             Flag session if PhaseEncodingDirection unknown OR
             TotalReadoutTime absent
  Level 2 — Vecta Core (all criteria, BIDS-only)
             Flag session if any finding present (readiness != ready)
  Level 3 — Vecta + source integrity (with DICOM)
             Flag session if any finding present, including DICOM criteria

For each level compute against QSIPrep outcome:
  TP  — flagged AND QSIPrep failed
  FP  — flagged AND QSIPrep succeeded
  TN  — not flagged AND QSIPrep succeeded
  FN  — not flagged AND QSIPrep failed
  Sensitivity = TP / (TP + FN)
  Specificity = TN / (TN + FP)
  PPV         = TP / (TP + FP)
  NPV         = TN / (TN + FN)

Sessions with no QSIPrep outcome are excluded from the 2×2 table.

Usage:
    python scripts/compute_ablation_table.py \
        --vecta  ~/Documents/vecta_dwi_cidur_run/per_session \
        --outcomes ~/Documents/vecta_dwi_cidur_run/outcomes/outcomes_long.tsv \
        --output ~/Documents/vecta_dwi_cidur_run/ablation_table.tsv
"""

from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path


def load_outcomes(outcomes_tsv: Path) -> dict[tuple[str, str], bool | None]:
    """Return {(subject_id, session_id): qsiprep_success}."""
    outcomes: dict[tuple[str, str], bool | None] = {}
    with outcomes_tsv.open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["outcome_id"] != "VECTA.OUTCOME.QSIPREP_SUCCESS":
                continue
            sub = row["subject_id"].removeprefix("sub-")
            ses = row["session_id"].removeprefix("ses-")
            val = row["value"]
            outcomes[(sub, ses)] = (val.lower() == "true") if val else None
    return outcomes


def load_sessions(per_session_dir: Path) -> list[dict]:
    sessions = []
    for d in sorted(per_session_dir.iterdir()):
        p = d / "vecta.json"
        if not p.exists():
            continue
        j = json.loads(p.read_text())
        variables = j.get("variables", {})

        sub = j.get("subject_id", "")
        ses = j.get("session_id", "")
        # Normalise to bare label (strip sub-/ses- prefixes if present)
        sub = sub.removeprefix("sub-")
        ses = ses.removeprefix("ses-")

        bids_errors = variables.get("VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT", {}).get("value")
        pe_state = variables.get("VECTA.DWI.ACQ.PE_DIRECTION", {}).get("state", "unknown")
        trt_val = variables.get("VECTA.DWI.ACQ.TOTAL_READOUT_TIME_PRESENT", {}).get("value")
        readiness = j.get("readiness", {}).get("state", "")
        findings = j.get("findings", [])
        dicom_domains = j.get("assessment_status", {}).get("domains_attempted", [])
        has_dicom = "dicom_source" in dicom_domains

        sessions.append({
            "subject_id": sub,
            "session_id": ses,
            "bids_errors": int(bids_errors) if bids_errors is not None else 0,
            "pe_unknown": pe_state == "unknown",
            "trt_absent": trt_val is False,
            "readiness": readiness,
            "finding_count": len(findings),
            "has_dicom": has_dicom,
            "dicom_finding": any(
                f.get("criterion_id") in ("VECTA-DWI-050", "VECTA-DWI-060")
                for f in findings
            ),
        })
    return sessions


def flag_level(session: dict, level: int) -> bool:
    if level == 0:
        return session["bids_errors"] > 0
    if level == 1:
        return session["pe_unknown"] or session["trt_absent"]
    if level == 2:
        return session["readiness"] not in ("ready", "not_assessed", "")
    if level == 3:
        return session["finding_count"] > 0
    raise ValueError(level)


def compute_2x2(sessions, outcomes, level):
    tp = fp = tn = fn = excluded = 0
    for s in sessions:
        key = (s["subject_id"], s["session_id"])
        qsp = outcomes.get(key)
        if qsp is None:
            excluded += 1
            continue
        flagged = flag_level(s, level)
        failed = not qsp
        if flagged and failed:
            tp += 1
        elif flagged and not failed:
            fp += 1
        elif not flagged and not failed:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    ppv = tp / (tp + fp) if (tp + fp) else float("nan")
    npv = tn / (tn + fn) if (tn + fn) else float("nan")
    return {
        "level": level,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "excluded": excluded, "total": total,
        "sensitivity": round(sensitivity, 3),
        "specificity": round(specificity, 3),
        "ppv": round(ppv, 3),
        "npv": round(npv, 3),
    }


LEVEL_LABELS = {
    0: "BIDS Validator errors > 0",
    1: "PE direction unknown OR TotalReadoutTime absent",
    2: "Vecta Core — any finding (readiness != ready)",
    3: "Vecta + DICOM — any finding including source-integrity",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vecta", required=True, type=Path, help="per_session dir")
    ap.add_argument("--outcomes", required=True, type=Path, help="outcomes_long.tsv")
    ap.add_argument("--output", required=True, type=Path, help="output TSV path")
    args = ap.parse_args()

    sessions = load_sessions(args.vecta)
    outcomes = load_outcomes(args.outcomes)
    has_dicom_sessions = sum(1 for s in sessions if s["has_dicom"])

    print(f"Loaded {len(sessions)} sessions ({has_dicom_sessions} with DICOM)")
    print(f"Outcomes available for: {sum(1 for v in outcomes.values() if v is not None)} sessions\n")

    rows = []
    for level in range(4):
        if level == 3 and has_dicom_sessions == 0:
            print(f"Level 3 skipped — no DICOM sessions")
            continue
        r = compute_2x2(sessions, outcomes, level)
        r["label"] = LEVEL_LABELS[level]
        rows.append(r)
        print(f"Level {level}: {LEVEL_LABELS[level]}")
        print(f"  TP={r['tp']} FP={r['fp']} TN={r['tn']} FN={r['fn']} excluded={r['excluded']}")
        print(f"  Sensitivity={r['sensitivity']} Specificity={r['specificity']} "
              f"PPV={r['ppv']} NPV={r['npv']}\n")

    fields = ["level", "label", "tp", "fp", "tn", "fn", "excluded", "total",
              "sensitivity", "specificity", "ppv", "npv"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Written → {args.output}")


if __name__ == "__main__":
    main()
