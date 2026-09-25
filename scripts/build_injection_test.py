"""
Controlled defect injection for VECTA-DWI criterion validation.

Takes sub-001 ses-1 (Siemens Skyra, ready, 67 directions, reverse-PE fmap) as
the baseline and creates per-defect BIDS subdatasets in cidur_injection_test/.
Each subdataset has exactly one injected defect; Vecta is then run on each to
confirm the expected criterion fires (and only that criterion).

Defects injected:
  def-021  Remove PhaseEncodingDirection from DWI sidecar  → VECTA-DWI-021
  def-014  Remove the reverse-PE EPI fieldmap               → VECTA-DWI-014
  def-030  Remove the DWI .bvec file                        → VECTA-DWI-030
  def-031  Corrupt bvec norms (scale to 0.5 instead of 1)  → VECTA-DWI-031
  baseline No defect (control — must remain ready)

Outputs at:
  ~/Documents/cidur_injection_test/
    baseline/
    def-021/
    def-014/
    def-030/
    def-031/
  ~/Documents/vecta_dwi_injection_test/   (Vecta assessment outputs)
"""

import json
import shutil
from pathlib import Path
import numpy as np

CIDUR_BIDS = Path("/mnt/nfs/home/URMC-SH/pndagiji/Documents/CIDUR_BIDS/data_bids")
INJECT_ROOT = Path("/mnt/nfs/home/URMC-SH/pndagiji/Documents/cidur_injection_test")
SOURCE_SUBJ = "sub-001"
SOURCE_SES = "ses-1"

SRC_DWI = CIDUR_BIDS / SOURCE_SUBJ / SOURCE_SES / "dwi"
SRC_FMAP = CIDUR_BIDS / SOURCE_SUBJ / SOURCE_SES / "fmap"
SRC_ANAT = CIDUR_BIDS / SOURCE_SUBJ / SOURCE_SES / "anat"

DATASET_DESC = {
    "Name": "CIDUR injection test (controlled defects for VECTA-DWI criterion validation)",
    "BIDSVersion": "1.10.1",
    "DatasetType": "raw",
    "GeneratedBy": [{"Name": "build_injection_test.py"}],
}

DWI_BASE = "sub-001_ses-1_acq-64dirax_dir-ap_dwi"
FMAP_BASE = "sub-001_ses-1_dir-pa_epi"
T1W_BASE  = "sub-001_ses-1_T1w"


def copy_session(dest_root: Path):
    """Copy baseline session files into dest_root/sub-001/ses-1/."""
    dwi_dir  = dest_root / "sub-001/ses-1/dwi"
    fmap_dir = dest_root / "sub-001/ses-1/fmap"
    anat_dir = dest_root / "sub-001/ses-1/anat"
    dwi_dir.mkdir(parents=True, exist_ok=True)
    fmap_dir.mkdir(parents=True, exist_ok=True)
    anat_dir.mkdir(parents=True, exist_ok=True)

    for ext in ("nii.gz", "bval", "bvec", "json"):
        shutil.copy2(SRC_DWI / f"{DWI_BASE}.{ext}", dwi_dir / f"{DWI_BASE}.{ext}")
    for ext in ("nii.gz", "json"):
        shutil.copy2(SRC_FMAP / f"{FMAP_BASE}.{ext}", fmap_dir / f"{FMAP_BASE}.{ext}")
    for ext in ("nii.gz", "json"):
        shutil.copy2(SRC_ANAT / f"{T1W_BASE}.{ext}", anat_dir / f"{T1W_BASE}.{ext}")

    with open(dest_root / "dataset_description.json", "w") as f:
        json.dump(DATASET_DESC, f, indent=2)


def inject_021(dest_root: Path):
    """Remove PhaseEncodingDirection from DWI sidecar → VECTA-DWI-021."""
    json_path = dest_root / "sub-001/ses-1/dwi" / f"{DWI_BASE}.json"
    with open(json_path) as f:
        sidecar = json.load(f)
    sidecar.pop("PhaseEncodingDirection", None)
    with open(json_path, "w") as f:
        json.dump(sidecar, f, indent=2)
    print(f"  [def-021] Removed PhaseEncodingDirection from {json_path.name}")


def inject_014(dest_root: Path):
    """Remove reverse-PE EPI fieldmap → VECTA-DWI-014."""
    for ext in ("nii.gz", "json"):
        fp = dest_root / "sub-001/ses-1/fmap" / f"{FMAP_BASE}.{ext}"
        if fp.exists():
            fp.unlink()
    print(f"  [def-014] Removed fmap/{FMAP_BASE}.*")


def inject_030(dest_root: Path):
    """Remove the DWI .bvec file → VECTA-DWI-030."""
    bvec = dest_root / "sub-001/ses-1/dwi" / f"{DWI_BASE}.bvec"
    if bvec.exists():
        bvec.unlink()
    print(f"  [def-030] Removed {bvec.name}")


def inject_031(dest_root: Path):
    """Scale bvec norms to 0.5 (non-unit) → VECTA-DWI-031."""
    bvec_path = dest_root / "sub-001/ses-1/dwi" / f"{DWI_BASE}.bvec"
    vecs = np.loadtxt(bvec_path)  # shape (3, N)
    # Set every non-zero column to have norm 0.5
    norms = np.linalg.norm(vecs, axis=0)
    nonzero = norms > 0.01
    vecs[:, nonzero] = vecs[:, nonzero] / norms[nonzero] * 0.5
    np.savetxt(bvec_path, vecs, fmt="%.6f")
    print(f"  [def-031] Scaled non-zero bvec norms to 0.5 in {bvec_path.name}")


DEFECTS = {
    "baseline": None,
    "def-021":  inject_021,
    "def-014":  inject_014,
    "def-030":  inject_030,
    "def-031":  inject_031,
}

EXPECTED_FINDINGS = {
    "baseline": "ready (no criteria triggered)",
    "def-021":  "review_required (VECTA-DWI-001 + VECTA-DWI-021)",
    "def-014":  "ready_with_limitations (VECTA-DWI-014)",
    "def-030":  "not_ready (VECTA-DWI-030 — blocking criterion)",
    "def-031":  "ready_with_limitations (VECTA-DWI-031)",
}

QSIPREP_PREDICTION = {
    "baseline": "SUCCESS (all criteria pass)",
    "def-021":  "FAILURE at SDC calibration (no signed PhaseEncodingDirection)",
    "def-014":  "SUCCESS with no-SDC fallback (VECTA-DWI-014 non-blocking)",
    "def-030":  "FAILURE at gradient loading (no bvec file)",
    "def-031":  "FAILURE or WARNING at eddy (implausible gradient norms)",
}


def main():
    if INJECT_ROOT.exists():
        print(f"Removing existing injection root: {INJECT_ROOT}")
        shutil.rmtree(INJECT_ROOT)
    INJECT_ROOT.mkdir(parents=True)

    print(f"Building controlled defect datasets at {INJECT_ROOT}")
    print(f"Source: {SOURCE_SUBJ} {SOURCE_SES} from {CIDUR_BIDS.name}")
    print()

    for defect_id, inject_fn in DEFECTS.items():
        dest = INJECT_ROOT / defect_id
        print(f"--- {defect_id} ---")
        copy_session(dest)
        if inject_fn is not None:
            inject_fn(dest)
        print(f"  Expected Vecta:   {EXPECTED_FINDINGS[defect_id]}")
        print(f"  Expected QSIPrep: {QSIPREP_PREDICTION[defect_id]}")
        print()

    print("=== Summary manifest ===")
    for defect_id in DEFECTS:
        print(f"  {defect_id:12s}  {EXPECTED_FINDINGS[defect_id]}")

    # Write a manifest for reference
    manifest = {
        defect_id: {
            "expected_vecta": EXPECTED_FINDINGS[defect_id],
            "expected_qsiprep": QSIPREP_PREDICTION[defect_id],
        }
        for defect_id in DEFECTS
    }
    manifest_path = INJECT_ROOT / "injection_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written to {manifest_path}")
    print()
    print("Next steps:")
    print(f"  1. Run Vecta on each subdataset:")
    for defect_id in DEFECTS:
        print(f"       vecta assess {INJECT_ROOT}/{defect_id} --profile dwi_connectomics \\")
        print(f"         -o ~/Documents/vecta_dwi_injection_test/{defect_id}")
    print(f"  2. Run QSIPrep SLURM jobs:")
    print(f"       bash scripts/run_injection_qsiprep.sh")


if __name__ == "__main__":
    main()
