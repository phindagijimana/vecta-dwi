#!/usr/bin/env bash
# Batch Vecta assessment for three OpenNeuro datasets.
# Runs vecta assess for all subject/session pairs, then aggregates each cohort.
# Usage: bash scripts/run_openneuro_batch.sh [ds000201|ds003416|ds004712|all]

set -euo pipefail

SPEC=/mnt/nfs/home/urmc-sh.rochester.edu/pndagiji/Documents/vecta/vecta-dwi/specification/v0.1
OPENNEURO=/mnt/nfs/home/urmc-sh.rochester.edu/pndagiji/Documents/vecta/vecta-dwi/data/openneuro
OUT_ROOT=~/Documents/vecta_dwi_openneuro

DATASETS_TO_RUN="${1:-all}"

run_dataset() {
    local dsid="$1"      # e.g. ds000201
    local dsdir="$2"     # full path to BIDS root
    local outdir="$3"    # output root
    local profile="${4:-dwi_connectomics}"

    echo "=== $dsid: scanning sessions ==="
    local n_ok=0 n_fail=0

    # Enumerate sub-*/ses-* pairs that have a dwi/ directory
    while IFS= read -r ses_path; do
        sub_dir=$(dirname "$ses_path")
        sub_label=$(basename "$sub_dir" | sed 's/^sub-//')
        ses_label=$(basename "$ses_path" | sed 's/^ses-//')
        out_session="$outdir/per_session/sub-${sub_label}_ses-${ses_label}"

        if [[ -f "$out_session/vecta.json" ]]; then
            echo "  SKIP sub-${sub_label} ses-${ses_label} (already done)"
            ((n_ok++)) || true
            continue
        fi

        mkdir -p "$out_session"
        if vecta assess \
            --dataset "$dsdir" \
            --subject "$sub_label" \
            --session "$ses_label" \
            --spec "$SPEC" \
            --profile "$profile" \
            --output "$out_session" \
            --formats json 2>>"$outdir/errors.log"; then
            ((n_ok++)) || true
        else
            echo "  FAIL sub-${sub_label} ses-${ses_label}"
            ((n_fail++)) || true
        fi
    done < <(find "$dsdir" -mindepth 3 -maxdepth 3 -name 'dwi' -type d \
              -not -path '*/derivatives/*' \
              | sed 's|/dwi$||' \
              | sort)

    echo "=== $dsid done: ok=$n_ok fail=$n_fail ==="

    # Aggregate
    echo "=== $dsid: aggregating ==="
    vecta aggregate \
        "$outdir/per_session" \
        --output "$outdir/cohort" 2>>"$outdir/errors.log" \
        && echo "=== $dsid: aggregate done ===" \
        || echo "=== $dsid: aggregate FAILED ==="
}

mkdir -p "$OUT_ROOT"

if [[ "$DATASETS_TO_RUN" == "ds000201" || "$DATASETS_TO_RUN" == "all" ]]; then
    mkdir -p "$OUT_ROOT/ds000201/per_session"
    run_dataset "ds000201" "$OPENNEURO/ds000201_sleepybrain" "$OUT_ROOT/ds000201"
fi

if [[ "$DATASETS_TO_RUN" == "ds003416" || "$DATASETS_TO_RUN" == "all" ]]; then
    mkdir -p "$OUT_ROOT/ds003416/per_session"
    run_dataset "ds003416" "$OPENNEURO/ds003416_masivar" "$OUT_ROOT/ds003416"
fi

if [[ "$DATASETS_TO_RUN" == "ds004712" || "$DATASETS_TO_RUN" == "all" ]]; then
    mkdir -p "$OUT_ROOT/ds004712/per_session"
    run_dataset "ds004712" "$OPENNEURO/ds004712_onharmony" "$OUT_ROOT/ds004712"
fi

echo "All requested datasets complete."
