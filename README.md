# Vecta-DWI

**Data Birth Integrity assessment for diffusion-weighted MRI datasets**

Vecta-DWI evaluates whether a BIDS-converted DWI session contains the acquisition parameters, gradient files, and metadata required for a specified downstream workflow — before preprocessing begins. It does not preprocess data; it certifies readiness and attributes every finding to the specific variable and criterion that triggered it.

The framework is built on a versioned specification (variables → criteria → profiles) evaluated by a deterministic engine. Scientific meaning lives in the YAML specification, not in code, making the assessment contract independently reviewable.

---

## Install

```bash
pip install git+https://github.com/phindagijimana/vecta-dwi.git
```

Requires Python ≥ 3.10. For development:

```bash
git clone https://github.com/phindagijimana/vecta-dwi.git
pip install -e vecta-dwi/
```

---

## Quick start

### Assess one session

```bash
vecta assess \
    --dataset /path/to/BIDS_root \
    --subject 001 \
    --session 1 \
    --spec specification/v0.1 \
    --profile dwi_connectomics \
    --output /path/to/output/sub-001_ses-1
```

With original DICOM (enables source-integrity variables):

```bash
vecta assess \
    --dataset /path/to/BIDS_root \
    --subject 001 --session 1 \
    --dicom /path/to/DICOM/EP007361/EP007361/EP007361_MR_1 \
    --spec specification/v0.1 \
    --profile dwi_connectomics \
    --output /path/to/output/sub-001_ses-1
```

Per-session output:
- `vecta.json` — canonical assessment (all variables, criteria, findings, readiness)
- `vecta.tsv` — tabular projection of key fields

### Assess a full cohort (batch)

```bash
# Assess all sessions, then aggregate
for sub in BIDS_root/sub-*/; do
  for ses in $sub/ses-*/; do
    vecta assess \
      --dataset BIDS_root \
      --subject "$(basename $sub | sed 's/sub-//')" \
      --session "$(basename $ses | sed 's/ses-//')" \
      --spec specification/v0.1 \
      --profile dwi_connectomics \
      --output output/per_session/$(basename $sub)_$(basename $ses)
  done
done

vecta aggregate output/per_session --output output/cohort
```

See `scripts/run_openneuro_batch.sh` for a complete batch script with skip-already-done logic.

### Aggregate cohort outputs

```bash
vecta aggregate /path/to/per_session_dir --output /path/to/cohort_dir
```

Cohort outputs:
- `session_summary.tsv` — one row per session (readiness state, finding counts, key variable values)
- `findings_long.tsv` — one row per finding
- `variables_long.tsv` — one row per variable per session
- `missingness_matrix.tsv` — variable × session completeness
- `finding_prevalence.tsv` — criterion trigger rates

### Label QSIPrep outcomes

```bash
vecta label-outcomes \
    --results-root /path/to/qsiprep_output_tree \
    --output /path/to/outcomes \
    --pipeline-version 0.23.1
```

### Join Vecta findings with outcomes

```bash
vecta join-outcomes \
    --cohort /path/to/cohort_dir \
    --outcomes /path/to/outcomes/outcomes_long.tsv \
    --output /path/to/joined
```

Produces `vecta_x_outcomes.tsv` — the primary analysis table linking readiness state to pipeline outcome for each session.

---

## What Vecta assesses

Version 0.1 defines **22 variables** across five domains and **8 active criteria**.

### Variables by domain

| Domain | Variables |
|--------|-----------|
| `scanner` | Manufacturer, model, field strength, software version |
| `acquisition` | Voxel size, volume count, bval count, bvec count, shell count, bvec plausibility, phase-encoding direction, TotalReadoutTime present, reverse PE availability |
| `bids` | BIDS validator error count, warning count, DWI present, required series present |
| `dicom_source` | Series count, DWI series count, instance count, duplicate SOPInstanceUID count, series geometry consistent, DICOM/BIDS field-strength agreement |

DICOM domain variables are only populated when `--dicom` is passed to `vecta assess`.

### Criteria and what they catch

| Criterion | What it catches |
|-----------|-----------------|
| **VECTA-DWI-001** | PhaseEncodingDirection cannot be determined from any source |
| **VECTA-DWI-014** | No complementary PE reference available (no reverse-PE DWI entity and no EPI fieldmap with matching IntendedFor) |
| **VECTA-DWI-021** | PhaseEncodingDirection unknown **or** TotalReadoutTime absent |
| **VECTA-DWI-030** | bval or bvec file missing entirely |
| **VECTA-DWI-031** | bvec gradient vectors have non-unit norms (corrupt or vendor-rescaled) |
| **VECTA-DWI-040** | Session exists in BIDS tree but has no DWI acquisition at all |
| **VECTA-DWI-050** | DWI DICOM series has internally inconsistent geometry (requires `--dicom`) |
| **VECTA-DWI-060** | MagneticFieldStrength disagrees between DICOM header and BIDS sidecar (requires `--dicom`) |

### Readiness states

| State | Meaning |
|-------|---------|
| `ready` | No criteria triggered |
| `ready_with_limitations` | One or more non-blocking criteria triggered |
| `not_ready` | A blocking criterion triggered |
| `review_required` | A review criterion returned unknown status |

### Naming and consistency checks

Vecta reads JSON sidecar values directly — not filename labels. This means it catches semantic inconsistencies that filename-level checks miss. For example, a session with `dir-AP` and `dir-PA` files where both have the same phase-encoding axis (e.g., `j-` and `i`) will correctly trigger VECTA-DWI-014 because the axis complement check fails, even though the filename labels look complementary.

---

## Specification structure

```
specification/v0.1/
├── variables/          # 22 variable definitions (acquisition, bids, dicom_source, scanner)
├── criteria/           # 8 criteria for dwi_connectomics profile
├── profiles/           # dwi_connectomics intended-use profile
├── schemas/            # JSON Schema Draft 2020-12 contracts (14 schemas)
├── protocols/examples/ # CIDUR URMC reference protocol YAMLs
├── evidence/           # Evidence registry (EV-DWI-* entries)
├── tolerances/         # Numeric tolerances (e.g. bvec norm tolerance)
└── CHANGELOG.md
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/run_openneuro_batch.sh` | Batch-assess a full OpenNeuro BIDS dataset and aggregate |
| `scripts/run_cidur_dicom.py` | Re-run CIDUR cohort with DICOM source module; auto-aggregates and joins outcomes |
| `scripts/collect_bids_manifest.py` | Inventory DWI sidecar fields, fieldmap types, and QSIPrep failure categories — produces small TSVs safe to transfer from a compute cluster |
| `scripts/compute_ablation_table.py` | Compute detection-level comparison table (BIDS Validator / naive PE check / Vecta Core) against labelled pipeline outcomes |
| `scripts/sdc_impact_analysis.py` | Regional connectome comparison between SDC and no-SDC sessions (susceptibility-sensitive region analysis) |
| `scripts/build_injection_test.py` | Build five per-defect BIDS subdatasets for controlled criterion validation (injects VECTA-DWI-014, -021, -030, -031 defects into a known-good session) |
| `scripts/run_injection_qsiprep.sh` | Submit SLURM jobs running QSIPrep on the five injection subdatasets; confirms each Vecta finding predicts the correct pipeline outcome |
| `scripts/setup_pre_intervention_qsiprep_test.sh` | Build minimal BIDS trees for pre-intervention excluded sessions (sub-036, sub-069) and generate SLURM jobs to confirm VECTA-DWI-021 failure prediction |

### Remote machine workflow

When full BIDS and DICOM data are on a compute cluster:

```bash
# On the remote machine:
git clone https://github.com/phindagijimana/vecta-dwi.git
pip install -e vecta-dwi/

# Run Vecta on all sessions (no imaging data leaves the machine)
# Run collect_bids_manifest.py for fieldmap inventory
python vecta-dwi/scripts/collect_bids_manifest.py \
    --bids /path/to/BIDS \
    --qsiprep /path/to/qsiprep_output \
    --output ~/bids_manifest

# Transfer back only small outputs (~50 KB per session)
rsync -avz ~/vecta_run/per_session/ local:~/vecta_run/ \
    --include="*/" --include="vecta.json" --include="*.tsv" --exclude="*"
rsync -avz ~/bids_manifest/ local:~/bids_manifest/
```

---

## PHI and data privacy

**Nothing in this repository contains participant data.**

- `data/` is entirely gitignored. It contains subject IDs, EP-IDs, and all run outputs — never committed.
- `subject_mapping.csv` (EP_ID ↔ BIDS crosswalk) lives only on the authorized machine; never committed.
- DICOM evidence carries `privacy_status: restricted` and is never exported outside an authorized environment.
- Sub-IDs that appear in `writing/` (e.g., `sub-016`) are de-identified BIDS pseudonyms used in the manuscript.

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

28 tests covering meta-schema validation, specification validation, five synthetic BIDS fixtures with frozen golden outputs, and seven integration scenarios (reference case, missing reverse PE, unknown PE direction, missing gradient files, bval/volume mismatch, missing readout metadata, DICOM/BIDS field-strength conflict).

---

## Project layout

```
src/vecta/           Python package (collectors, criteria engine, output assembler, CLI)
specification/v0.1/  Versioned YAML specification + JSON schemas
tests/               Synthetic fixtures, golden outputs, integration tests
scripts/             Batch and remote-machine utility scripts
writing/             Manuscript drafts (methods, results, discussion, abstract)
docs/                Analysis manuals and outcome-labeling documentation
data/                (gitignored) Local run outputs, subject mappings, BIDS trees
```

---

## Validation

Vecta-DWI v0.1 has been evaluated on:

- **CIDUR clinical cohort** (69 sessions, 3 scanner models, 2 vendors, 2 field strengths): QSIPrep v0.23.1 outcomes confirmed for all 69 sessions. All 3 failures occurred in Vecta-flagged sessions; no ready session failed. Sensitivity 1.000 (95% CI [0.439, 1.000]), NPV 1.000 (95% CI [0.871, 1.000]). A naive PhaseEncodingDirection-absent check matched 2 of 3 failures and could not detect the acquisition-layer failure mode.
- **TrackTBI pilot** (10 sessions, independent institutions, Siemens TrioTim/Skyra, b=1300 s/mm²): criterion findings consistent with CIDUR; all 5 processed sessions succeeded.
- **Three OpenNeuro datasets** (506 additional sessions): SleepyBrain (ds000201), MASiVar (ds003416), ON-Harmony (ds004712) — criterion fire patterns consistent across protocols and vendors.
- **Controlled defect injection**: all 5 per-criterion injections (VECTA-DWI-014, -021, -030, -031, baseline) produced the predicted Vecta readiness state and the predicted QSIPrep outcome, including a silent DWI skip (no error, exit 0, anat-only output) under VECTA-DWI-021.

---

## Reference guide

`vecta.md` contains a detailed framework reference and data collection guide for study coordinators, data managers, and site investigators — including what to collect at the scanner, criterion remediation steps, and the data specification for external validation cohorts.

---

## Citation

Manuscript in preparation. Specification version: 0.1.0.
