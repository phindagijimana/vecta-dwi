#!/usr/bin/env bash
# Write and submit SLURM jobs to run QSIPrep on all 5 controlled-defect
# injection datasets.  Output at ~/Documents/cidur_injection_qsiprep_test/.
#
# Predicted outcomes (from Table 9 in results.md):
#   baseline  → SUCCESS (all criteria pass, clean session)
#   def-021   → FAILURE at topup SDC (PhaseEncodingDirection absent)
#   def-014   → SUCCESS with no-SDC fallback (no reverse-PE fmap)
#   def-030   → FAILURE at gradient loading (bvec file deleted)
#   def-031   → FAILURE or eddy WARNING (non-unit bvec norms ≈0.5)
#
# Usage:
#   bash scripts/run_injection_qsiprep.sh

set -euo pipefail

INJECT_ROOT=/mnt/nfs/home/URMC-SH/pndagiji/Documents/cidur_injection_test
OUT_ROOT=/mnt/nfs/home/URMC-SH/pndagiji/Documents/cidur_injection_qsiprep_test
QSIPREP_SIF=/mnt/nfs/home/URMC-SH/pndagiji/Documents/others/containers/qsiprep.sif
FS_LICENSE=${FS_LICENSE:-/mnt/nfs/home/urmc-sh.rochester.edu/pndagiji/Documents/others/data_mining/freesurfer/license.txt}
LOG_DIR=$OUT_ROOT/logs

mkdir -p "$LOG_DIR"

declare -A DEFECTS=(
  [baseline]="001"
  [def-021]="001"
  [def-014]="001"
  [def-030]="001"
  [def-031]="001"
)

declare -A PRED=(
  [baseline]="SUCCESS"
  [def-021]="FAILURE: topup SDC (no PhaseEncodingDirection)"
  [def-014]="SUCCESS: no-SDC fallback"
  [def-030]="FAILURE: gradient loading (no bvec)"
  [def-031]="FAILURE or WARNING: eddy (non-unit bvec norms)"
)

echo "=== Writing SLURM jobs for injection QSIPrep test ==="
echo "  INJECT_ROOT = $INJECT_ROOT"
echo "  OUT_ROOT    = $OUT_ROOT"
echo ""

for defect in baseline def-021 def-014 def-030 def-031; do
  subj="${DEFECTS[$defect]}"
  bids_dir="$INJECT_ROOT/$defect"
  out_dir="$OUT_ROOT/$defect/output"
  work_dir="$OUT_ROOT/$defect/work"
  slurm_file="$OUT_ROOT/${defect}.slurm"

  mkdir -p "$out_dir" "$work_dir"

  cat > "$slurm_file" <<SLURM
#!/bin/bash
#SBATCH --job-name=qsiprep_${defect}
#SBATCH --output=${LOG_DIR}/${defect}_%j.out
#SBATCH --error=${LOG_DIR}/${defect}_%j.err
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --partition=interactive

echo "=== QSIPrep injection test: $defect ==="
echo "  QSIPrep SIF : $QSIPREP_SIF"
echo "  BIDS input  : $bids_dir"
echo "  Output      : $out_dir"
echo "  Prediction  : ${PRED[$defect]}"
echo ""

singularity run --cleanenv \\
  -B $bids_dir:/bids:ro \\
  -B $out_dir:/output \\
  -B $work_dir:/work \\
  -B $FS_LICENSE:/opt/freesurfer/license.txt:ro \\
  $QSIPREP_SIF /bids /output participant \\
  --participant-label $subj \\
  --output-resolution 2 \\
  --hmc-model eddy \\
  -w /work \\
  --nthreads 8 --omp-nthreads 8 \\
  2>&1 | tee ${LOG_DIR}/${defect}_qsiprep.log

EXIT_CODE=\$?
echo ""
echo "Exit code: \$EXIT_CODE"
echo "Predicted: ${PRED[$defect]}"
if [ \$EXIT_CODE -eq 0 ]; then
  echo "OBSERVED: SUCCESS"
else
  echo "OBSERVED: FAILURE (exit \$EXIT_CODE)"
fi
SLURM

  echo "  Wrote $slurm_file"
done

echo ""
echo "=== Submit all jobs ==="
for defect in baseline def-021 def-014 def-030 def-031; do
  job_id=$(sbatch "$OUT_ROOT/${defect}.slurm" | awk '{print $NF}')
  echo "  Submitted $defect  → job $job_id"
done

echo ""
echo "Monitor: squeue -u \$USER"
echo "Logs:    $LOG_DIR/"
