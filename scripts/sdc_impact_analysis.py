"""
Connectome consequences of SDC absence: Siemens (SDC) vs GE (no SDC).

Reads per-subject node-strength CSVs and the Vecta outcomes table, then
tests whether susceptibility-sensitive brain regions show disproportionately
lower node strength in GE (no-SDC) sessions compared to Siemens (SDC) sessions.

Important confounders acknowledged in the analysis:
- Voxel size: GE 1×1×2 mm vs Siemens 2×2×2 mm (affects streamline counts)
- Gradient directions: GE 51-53 vs Siemens 67
- Scanner model differences

The primary metric is therefore an intra-subject ratio:
  susceptibility_index = mean(susceptible region strengths) / mean(non-susceptible region strengths)
This ratio is independent of absolute streamline count and controls for
within-subject tractography yield, scanner, and resolution differences.

Outputs:
  data/cidur_qsiprep/sdc_impact/sdc_global_strength.tsv
  data/cidur_qsiprep/sdc_impact/sdc_region_strength.tsv
  data/cidur_qsiprep/sdc_impact/sdc_susceptibility_index.tsv
  data/cidur_qsiprep/sdc_impact/sdc_impact_stats.txt
"""

from pathlib import Path
import csv
import json
from collections import defaultdict
from scipy import stats
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
OUTCOMES_TSV = REPO_ROOT / "data/cidur_vecta_run/vecta_x_outcomes.tsv"
STRENGTH_DIR = Path("/mnt/nfs/Gugger_Lab/NIR/dwi_CIDUR/results/node_strength/strength/per_subject")
OUT_DIR = REPO_ROOT / "data/cidur_qsiprep/sdc_impact"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Region sets
# ---------------------------------------------------------------------------
# Regions near air-tissue interfaces with high susceptibility distortion
SUSCEPTIBLE_REGIONS = {
    "L.entorhinal", "R.entorhinal",
    "L.parahippocampal", "R.parahippocampal",
    "L.lateralorbitofrontal", "R.lateralorbitofrontal",
    "L.medialorbitofrontal", "R.medialorbitofrontal",
    "L.fusiform", "R.fusiform",
    "L.inferiortemporal", "R.inferiortemporal",
    "L.temporalpole", "R.temporalpole",      # may not be in DKT atlas
    "L.parsorbitalis", "R.parsorbitalis",     # inferior frontal / orbital
}

# Regions distant from air-tissue interfaces, minimal susceptibility effect
NON_SUSCEPTIBLE_REGIONS = {
    "L.postcentral", "R.postcentral",
    "L.precentral", "R.precentral",
    "L.paracentral", "R.paracentral",
    "L.superiorparietal", "R.superiorparietal",
    "L.precuneus", "R.precuneus",
    "L.cuneus", "R.cuneus",
    "L.superiorfrontal", "R.superiorfrontal",
}


# ---------------------------------------------------------------------------
# Load outcomes
# ---------------------------------------------------------------------------
def load_outcomes():
    """Return dict: subject_id -> {manufacturer, readiness_state, connectome_available}."""
    outcomes = {}
    with open(OUTCOMES_TSV) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            subj = row["subject_id"].zfill(3)
            conn = row.get("VECTA.OUTCOME.CONNECTOME_AVAILABLE", "").strip()
            outcomes[subj] = {
                "manufacturer": row["manufacturer"],
                "readiness_state": row["readiness_state"],
                "connectome_available": conn == "True",
                "qsiprep_success": row.get("VECTA.OUTCOME.QSIPREP_SUCCESS", "").strip() == "True",
                "model": row.get("model", ""),
            }
    return outcomes


# ---------------------------------------------------------------------------
# Load node strength for one subject
# ---------------------------------------------------------------------------
def load_strength(subject_id):
    """Return dict: region_name -> float strength."""
    path = STRENGTH_DIR / f"sub-{subject_id}_strength.csv"
    if not path.exists():
        return None
    strengths = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            strengths[row["name"]] = float(row["strength"])
    return strengths


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------
def main():
    outcomes = load_outcomes()

    # Split cohort
    siemens_subjects = []
    ge_subjects = []
    for subj, info in outcomes.items():
        if not info["connectome_available"]:
            continue
        if info["manufacturer"] == "Siemens":
            siemens_subjects.append(subj)
        elif info["manufacturer"] == "GE":
            ge_subjects.append(subj)

    print(f"Siemens (SDC) subjects with connectome: {len(siemens_subjects)}")
    print(f"GE (no-SDC) subjects with connectome: {len(ge_subjects)}")

    # Build per-subject data
    records = []
    all_regions = None
    for group, subjects in [("Siemens_SDC", siemens_subjects), ("GE_noSDC", ge_subjects)]:
        for subj in subjects:
            strengths = load_strength(subj)
            if strengths is None:
                print(f"  WARNING: no strength file for sub-{subj}")
                continue
            if all_regions is None:
                all_regions = sorted(strengths.keys())

            # Global mean node strength
            global_mean = np.mean(list(strengths.values()))

            # Susceptible vs non-susceptible means (only regions present in data)
            susc_values = [strengths[r] for r in SUSCEPTIBLE_REGIONS if r in strengths]
            nonsusc_values = [strengths[r] for r in NON_SUSCEPTIBLE_REGIONS if r in strengths]

            susc_mean = np.mean(susc_values) if susc_values else float("nan")
            nonsusc_mean = np.mean(nonsusc_values) if nonsusc_values else float("nan")
            susc_index = susc_mean / nonsusc_mean if nonsusc_mean > 0 else float("nan")

            records.append({
                "subject_id": subj,
                "group": group,
                "manufacturer": outcomes[subj]["manufacturer"],
                "model": outcomes[subj]["model"],
                "global_mean_strength": global_mean,
                "susceptible_mean_strength": susc_mean,
                "nonsusceptible_mean_strength": nonsusc_mean,
                "susceptibility_index": susc_index,
                "n_susceptible_regions": len(susc_values),
                "n_nonsusceptible_regions": len(nonsusc_values),
                **{r: strengths.get(r, float("nan")) for r in (SUSCEPTIBLE_REGIONS | NON_SUSCEPTIBLE_REGIONS)},
            })

    # ---------------------------------------------------------------------------
    # Save per-subject susceptibility index table
    # ---------------------------------------------------------------------------
    index_path = OUT_DIR / "sdc_susceptibility_index.tsv"
    index_fields = ["subject_id", "group", "manufacturer", "model",
                    "global_mean_strength", "susceptible_mean_strength",
                    "nonsusceptible_mean_strength", "susceptibility_index",
                    "n_susceptible_regions", "n_nonsusceptible_regions"]
    with open(index_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=index_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {index_path}")

    # ---------------------------------------------------------------------------
    # Save global strength table
    # ---------------------------------------------------------------------------
    global_path = OUT_DIR / "sdc_global_strength.tsv"
    global_fields = ["subject_id", "group", "manufacturer", "model", "global_mean_strength"]
    with open(global_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=global_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {global_path}")

    # ---------------------------------------------------------------------------
    # Save per-region table
    # ---------------------------------------------------------------------------
    region_path = OUT_DIR / "sdc_region_strength.tsv"
    region_fields = ["subject_id", "group", "manufacturer"] + sorted(
        SUSCEPTIBLE_REGIONS | NON_SUSCEPTIBLE_REGIONS
    )
    with open(region_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=region_fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {region_path}")

    # ---------------------------------------------------------------------------
    # Statistical tests
    # ---------------------------------------------------------------------------
    siemens_rec = [r for r in records if r["group"] == "Siemens_SDC"]
    ge_rec = [r for r in records if r["group"] == "GE_noSDC"]

    def extract(recs, key):
        return np.array([r[key] for r in recs if not np.isnan(r[key])])

    stats_lines = []
    stats_lines.append("SDC IMPACT ANALYSIS — STATISTICAL RESULTS")
    stats_lines.append("=" * 60)
    stats_lines.append(f"Siemens (with SDC): n = {len(siemens_rec)}")
    stats_lines.append(f"GE (without SDC):   n = {len(ge_rec)}")
    stats_lines.append("")
    stats_lines.append("NOTE: Confounders present — these groups differ in:")
    stats_lines.append("  - Voxel size: GE=1×1×2mm, Siemens=2×2×2mm")
    stats_lines.append("  - Gradient directions: GE=51-53, Siemens=67")
    stats_lines.append("  Primary metric (susceptibility index) controls for")
    stats_lines.append("  absolute streamline count by using an intra-subject ratio.")
    stats_lines.append("")

    for label, key in [
        ("Global mean node strength", "global_mean_strength"),
        ("Susceptible region mean strength", "susceptible_mean_strength"),
        ("Non-susceptible region mean strength", "nonsusceptible_mean_strength"),
        ("Susceptibility index (susc/nonsusc ratio)", "susceptibility_index"),
    ]:
        s_vals = extract(siemens_rec, key)
        g_vals = extract(ge_rec, key)
        u_stat, p_val = stats.mannwhitneyu(s_vals, g_vals, alternative="two-sided")
        stats_lines.append(f"{label}:")
        stats_lines.append(f"  Siemens: median={np.median(s_vals):.1f}, IQR=[{np.percentile(s_vals,25):.1f},{np.percentile(s_vals,75):.1f}]")
        stats_lines.append(f"  GE:      median={np.median(g_vals):.1f}, IQR=[{np.percentile(g_vals,25):.1f},{np.percentile(g_vals,75):.1f}]")
        stats_lines.append(f"  Mann-Whitney U={u_stat:.0f}, p={p_val:.4f}")
        stats_lines.append("")

    # Per-region tests for susceptible regions
    stats_lines.append("PER-REGION TESTS (susceptibility-sensitive regions):")
    stats_lines.append("-" * 60)
    region_results = []
    for region in sorted(SUSCEPTIBLE_REGIONS):
        s_vals = extract(siemens_rec, region)
        g_vals = extract(ge_rec, region)
        if len(s_vals) < 3 or len(g_vals) < 3:
            continue
        u_stat, p_val = stats.mannwhitneyu(s_vals, g_vals, alternative="two-sided")
        region_results.append((region, np.median(s_vals), np.median(g_vals), u_stat, p_val))

    # FDR correction (Benjamini-Hochberg)
    if region_results:
        p_vals = np.array([r[4] for r in region_results])
        n = len(p_vals)
        sorted_idx = np.argsort(p_vals)
        p_adj = np.zeros(n)
        for rank, idx in enumerate(sorted_idx):
            p_adj[idx] = p_vals[idx] * n / (rank + 1)
        p_adj = np.minimum(p_adj, 1.0)
        # Enforce monotonicity
        for i in range(n - 2, -1, -1):
            p_adj[sorted_idx[i]] = min(p_adj[sorted_idx[i]], p_adj[sorted_idx[i + 1]])

        for i, (region, s_med, g_med, u, p_raw) in enumerate(region_results):
            stats_lines.append(f"{region}:")
            stats_lines.append(f"  Siemens median={s_med:.0f}, GE median={g_med:.0f}")
            stats_lines.append(f"  U={u:.0f}, p={p_raw:.4f}, p_adj(BH)={p_adj[i]:.4f}")

    stats_lines.append("")
    stats_lines.append("PER-REGION TESTS (non-susceptible control regions):")
    stats_lines.append("-" * 60)
    for region in sorted(NON_SUSCEPTIBLE_REGIONS):
        s_vals = extract(siemens_rec, region)
        g_vals = extract(ge_rec, region)
        if len(s_vals) < 3 or len(g_vals) < 3:
            continue
        u_stat, p_val = stats.mannwhitneyu(s_vals, g_vals, alternative="two-sided")
        stats_lines.append(f"{region}: U={u_stat:.0f}, p={p_val:.4f} (Siemens med={np.median(s_vals):.0f}, GE med={np.median(g_vals):.0f})")

    # Save stats
    stats_path = OUT_DIR / "sdc_impact_stats.txt"
    with open(stats_path, "w") as f:
        f.write("\n".join(stats_lines))
    print(f"Wrote {stats_path}")

    # Print to stdout
    print()
    for line in stats_lines:
        print(line)

    # ---------------------------------------------------------------------------
    # Summary JSON for paper
    # ---------------------------------------------------------------------------
    s_idx_siemens = extract(siemens_rec, "susceptibility_index")
    s_idx_ge = extract(ge_rec, "susceptibility_index")
    u_stat, p_val = stats.mannwhitneyu(s_idx_siemens, s_idx_ge, alternative="two-sided")

    summary = {
        "n_siemens": len(siemens_rec),
        "n_ge": len(ge_rec),
        "susceptibility_index_siemens_median": float(np.median(s_idx_siemens)),
        "susceptibility_index_siemens_iqr": [float(np.percentile(s_idx_siemens, 25)), float(np.percentile(s_idx_siemens, 75))],
        "susceptibility_index_ge_median": float(np.median(s_idx_ge)),
        "susceptibility_index_ge_iqr": [float(np.percentile(s_idx_ge, 25)), float(np.percentile(s_idx_ge, 75))],
        "mann_whitney_U": float(u_stat),
        "p_value": float(p_val),
        "confounders": ["voxel_size", "gradient_directions", "scanner_model"],
    }
    summary_path = OUT_DIR / "sdc_impact_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
