#!/usr/bin/env bash
# Build a minimal BIDS tree for sub-036 and sub-069 (pre-intervention excluded sessions)
# and write SLURM job scripts to run QSIPrep for VECTA-DWI-021 validation.
#
# Both sessions: PhaseEncodingAxis="j" only (no signed PhaseEncodingDirection).
# Vecta pre-intervention run already confirmed: review_required + VECTA-DWI-001 + VECTA-DWI-021.
#
# sub-069: has reverse-PE EPI fieldmap → QSIPrep will attempt SDC via topup
#          → PREDICTED FAILURE because PhaseEncodingDirection absent
# sub-036: no fieldmap → QSIPrep will use no-SDC fallback
#          → PREDICTED SUCCESS (but SDC permanently unavailable = VECTA-DWI-021 confirmed)
#
# Usage:
#   bash scripts/setup_pre_intervention_qsiprep_test.sh
#   sbatch $TEST_DIR/run_sub069_sdc.slurm    # confirm SDC failure
#   sbatch $TEST_DIR/run_sub036_nosdc.slurm  # confirm no-SDC fallback

set -euo pipefail

FOR_REVIEW=/mnt/nfs/home/URMC-SH/pndagiji/Documents/CIDUR_BIDS/for_review/special_cases_vendor
MAIN_BIDS=/mnt/nfs/home/URMC-SH/pndagiji/Documents/CIDUR_BIDS/data_bids
QSIPREP_SIF=/mnt/nfs/home/URMC-SH/pndagiji/Documents/others/containers/qsiprep.sif
FS_LICENSE=${FS_LICENSE:-/mnt/nfs/home/urmc-sh.rochester.edu/pndagiji/Documents/others/data_mining/freesurfer/license.txt}
TEST_DIR=${TEST_DIR:-/mnt/nfs/home/URMC-SH/pndagiji/Documents/cidur_pre_intervention_qsiprep_test}
BIDS_DIR=$TEST_DIR/bids
OUT_DIR=$TEST_DIR/output
WORK_DIR=$TEST_DIR/work

echo "=== Building minimal BIDS tree ==="
mkdir -p \
  "$BIDS_DIR/sub-036/ses-1/dwi" \
  "$BIDS_DIR/sub-036/ses-1/anat" \
  "$BIDS_DIR/sub-069/ses-1/dwi" \
  "$BIDS_DIR/sub-069/ses-1/anat" \
  "$BIDS_DIR/sub-069/ses-1/fmap" \
  "$OUT_DIR" "$WORK_DIR" "$TEST_DIR/logs"

printf '{"Name":"CIDUR pre-intervention QSIPrep test","BIDSVersion":"1.10.1","DatasetType":"raw"}\n' \
  > "$BIDS_DIR/dataset_description.json"

# sub-036: 64-dir Siemens Skyra, PhaseEncodingAxis only, no fieldmap
for ext in nii.gz bval bvec json; do
  cp "$FOR_REVIEW/sub-036/ses-1/dwi/sub-036_ses-1_acq-64dirax_dwi.$ext" \
     "$BIDS_DIR/sub-036/ses-1/dwi/"
done
cp "$MAIN_BIDS/sub-036/ses-1/anat/sub-036_ses-1_T1w.nii.gz" "$BIDS_DIR/sub-036/ses-1/anat/"
cp "$MAIN_BIDS/sub-036/ses-1/anat/sub-036_ses-1_T1w.json"   "$BIDS_DIR/sub-036/ses-1/anat/"

# sub-069: 24-dir Siemens Skyra, PhaseEncodingAxis only, HAS reverse-PE fmap
for ext in nii.gz bval bvec json; do
  cp "$FOR_REVIEW/sub-069/ses-1/dwi/sub-069_ses-1_acq-24dirax_dir-ap_dwi.$ext" \
     "$BIDS_DIR/sub-069/ses-1/dwi/"
done
for f in "$FOR_REVIEW/sub-069/ses-1/fmap/"*; do
  cp "$f" "$BIDS_DIR/sub-069/ses-1/fmap/"
done
cp "$MAIN_BIDS/sub-069/ses-1/anat/sub-069_ses-1_T1w.nii.gz" "$BIDS_DIR/sub-069/ses-1/anat/"
cp "$MAIN_BIDS/sub-069/ses-1/anat/sub-069_ses-1_T1w.json"   "$BIDS_DIR/sub-069/ses-1/anat/"

echo "BIDS tree built:"
find "$BIDS_DIR" -type f | sort

# ---------------------------------------------------------------------------
# SLURM job: sub-069 with SDC enabled (expected FAILURE)
# ---------------------------------------------------------------------------
cat > "$TEST_DIR/run_sub069_sdc.slurm" <<SLURM
#!/bin/bash
#SBATCH --job-name=vecta_069_sdc
#SBATCH --output=$TEST_DIR/logs/sub069_sdc_%j.out
#SBATCH --error=$TEST_DIR/logs/sub069_sdc_%j.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --partition=interactive

echo "=== sub-069: QSIPrep with SDC (VECTA-DWI-021 validation) ==="
echo "Vecta finding: review_required + VECTA-DWI-001 + VECTA-DWI-021"
echo "Has reverse-PE fmap but PhaseEncodingDirection absent"
echo "Expected: FAILURE at topup SDC step"

mkdir -p $OUT_DIR/sub069_sdc $WORK_DIR/sub069_sdc

singularity run --cleanenv \\
  -B $BIDS_DIR:/bids:ro \\
  -B $OUT_DIR/sub069_sdc:/output \\
  -B $WORK_DIR/sub069_sdc:/work \\
  -B $FS_LICENSE:/opt/freesurfer/license.txt:ro \\
  $QSIPREP_SIF /bids /output participant \\
  --participant-label 069 \\
  --output-resolution 2 \\
  --hmc-model eddy \\
  -w /work \\
  --nthreads 8 --omp-nthreads 8 \\
  2>&1 | tee $TEST_DIR/logs/sub069_sdc_qsiprep.log

echo "Exit code: \$?"
SLURM

# ---------------------------------------------------------------------------
# SLURM job: sub-036 no fieldmap (expected no-SDC fallback)
# ---------------------------------------------------------------------------
cat > "$TEST_DIR/run_sub036_nosdc.slurm" <<SLURM
#!/bin/bash
#SBATCH --job-name=vecta_036_nosdc
#SBATCH --output=$TEST_DIR/logs/sub036_nosdc_%j.out
#SBATCH --error=$TEST_DIR/logs/sub036_nosdc_%j.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --partition=interactive

echo "=== sub-036: QSIPrep without fieldmap (VECTA-DWI-021 validation) ==="
echo "Vecta finding: review_required + VECTA-DWI-001 + VECTA-DWI-021"
echo "No fieldmap present; PhaseEncodingDirection absent"
echo "Expected: SUCCESS with no-SDC fallback (SDC permanently unavailable)"

mkdir -p $OUT_DIR/sub036_nosdc $WORK_DIR/sub036_nosdc

singularity run --cleanenv \\
  -B $BIDS_DIR:/bids:ro \\
  -B $OUT_DIR/sub036_nosdc:/output \\
  -B $WORK_DIR/sub036_nosdc:/work \\
  -B $FS_LICENSE:/opt/freesurfer/license.txt:ro \\
  $QSIPREP_SIF /bids /output participant \\
  --participant-label 036 \\
  --output-resolution 2 \\
  --hmc-model eddy \\
  -w /work \\
  --nthreads 8 --omp-nthreads 8 \\
  2>&1 | tee $TEST_DIR/logs/sub036_nosdc_qsiprep.log

echo "Exit code: \$?"
SLURM

chmod +x "$TEST_DIR/run_sub069_sdc.slurm" "$TEST_DIR/run_sub036_nosdc.slurm"

echo ""
echo "=== Ready ==="
echo "To submit:"
echo "  sbatch $TEST_DIR/run_sub069_sdc.slurm    # predict FAIL (SDC)"
echo "  sbatch $TEST_DIR/run_sub036_nosdc.slurm  # predict SUCCESS (no-SDC)"
echo ""
echo "Verify these paths first:"
echo "  QSIPREP_SIF = $QSIPREP_SIF"
echo "  FS_LICENSE  = $FS_LICENSE"
