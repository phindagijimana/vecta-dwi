# Vecta-DWI: Framework Reference and Data Collection Guide

**Version**: 0.1.0  
**Intended audience**: Study coordinators, data managers, site investigators, and anyone involved in collecting, converting, or archiving DWI data for analysis with Vecta.

---

## Table of Contents

1. [What Vecta is trying to achieve](#1-what-vecta-is-trying-to-achieve)
2. [The theory: Data Birth Integrity (DBI)](#2-the-theory-data-birth-integrity-dbi)
3. [Lifecycle layers: where data can go wrong](#3-lifecycle-layers-where-data-can-go-wrong)
4. [Framework architecture](#4-framework-architecture)
5. [Variables: what Vecta measures](#5-variables-what-vecta-measures)
6. [Criteria: what Vecta checks](#6-criteria-what-vecta-checks)
7. [Assessment outputs: what Vecta produces](#7-assessment-outputs-what-vecta-produces)
8. [Data requirements for running Vecta](#8-data-requirements-for-running-vecta)
9. [TBI study: what to collect and why](#9-tbi-study-what-to-collect-and-why)
10. [Running Vecta](#10-running-vecta)
11. [What to do when a criterion fires](#11-what-to-do-when-a-criterion-fires)
12. [Full TrackTBI validation: data specification to fill paper 1 gaps](#12-full-tracktbi-validation-data-specification-to-fill-paper-1-gaps)

---

## 1. What Vecta is trying to achieve

Diffusion-weighted MRI (DWI) preprocessing pipelines — QSIPrep, FSL eddy, MRtrix3 — are complex. They depend on the data meeting specific requirements: gradient files must be present and valid, phase-encoding direction must be known, a reverse phase-encoding reference acquisition must be available for distortion correction. When any of these are missing or inconsistent, pipelines fail, skip processing steps silently, or complete with outputs of unknown validity.

The problem is that **none of the standard tools answer the question a researcher needs to answer before running a pipeline**: does this session have everything this pipeline needs to run correctly?

- **BIDS Validator** checks whether the data conforms to the BIDS standard. A session can pass BIDS validation and still be missing the fieldmap required for distortion correction. Conformance ≠ readiness.
- **MRIQC** assesses image quality (signal-to-noise, motion artifacts). It runs on the acquired images and tells you about image quality, not about whether the metadata and file structure are complete for preprocessing.
- **eddyqc / QSIPrep QC** evaluate the quality of preprocessing outputs. They require the pipeline to have run successfully first.

Vecta fills the gap **before preprocessing begins**, checking that the data has what it needs and reporting any shortfall with structured, evidence-traceable findings. It does not require any preprocessing to have been performed. It runs on the BIDS dataset as-is and reports readiness before computational resources are committed.

The secondary goal is **traceability**. In large multi-site studies, understanding why a session failed preprocessing months after data collection is difficult. Vecta creates a structured, versioned record of the data's state at assessment time — a protocol audit trail that persists independently of pipeline outputs.

---

## 2. The theory: Data Birth Integrity (DBI)

**Data Birth Integrity** is the degree to which the information, structure, acquisition characteristics, and representation needed for a specified downstream scientific use are present, internally consistent, traceable, and appropriately preserved from acquisition through the analysis-ready representation.

Three properties of this definition matter:

### DBI is intended-use conditional

The same session may be sufficient for one analysis and insufficient for another. A DWI session without a reverse-PE fieldmap may be perfectly adequate for tractography using a synthetic-fieldmap correction strategy, but insufficient for a pipeline that requires an EPI fieldmap specifically. Vecta's assessments are always made relative to a declared **intended-use profile** (e.g., `dwi_connectomics`) that specifies what the downstream workflow actually requires.

### DBI spans the full data lifecycle

A session's data integrity is not just about what the scanner acquired. It spans every transformation from acquisition to analysis-ready form:
- Was the reverse-PE fieldmap acquired at the scanner? (acquisition decision)
- Was the DICOM exported completely and without corruption? (source integrity)
- Did the converter correctly extract PhaseEncodingDirection from DICOM? (metadata transformation)
- Are the BIDS gradient files present and consistent with the NIfTI volume count? (representation integrity)

Problems at any of these layers can silently compromise the session. Vecta tracks which layer a problem originated at and reports this in every finding.

### DBI is not the same as image quality

Image quality (SNR, motion, distortion) is a separate downstream concern addressed by MRIQC, eddyqc, and visual inspection. A session can have excellent image quality but fail DBI (e.g., missing bvec file). Vecta does not assess image quality; it assesses structural prerequisites. The two are complementary and should both be checked.

---

## 3. Lifecycle layers: where data can go wrong

Vecta organizes every variable and criterion by the lifecycle layer at which the relevant event originates.

| Layer | ID | What it covers | Examples of problems |
|---|---|---|---|
| Acquisition | L1 | Physical scanner acquisition | Fieldmap not acquired; wrong phase-encoding direction programmed |
| Source | L2 | Raw DICOM files | Incomplete DICOM export; duplicate instances; geometry inconsistency across slices |
| Metadata | L3 | DICOM header values; converter-extracted metadata | PhaseEncodingDirection not written to DICOM; TotalReadoutTime absent |
| Representation | L4 | BIDS files (NIfTI, JSON, bval, bvec) | Missing bvec; bvec vectors with wrong scale; NIfTI present but bval absent |
| Conformance | L5 | BIDS specification compliance | BIDS Validator errors; required filename entities missing |

When Vecta fires a finding, it reports which layer the problem originated at. A finding at L1 (acquisition) means the data cannot be remediated after the fact — the scan was not acquired. A finding at L4 (representation) may be remediable by re-running the BIDS converter on the original DICOM.

---

## 4. Framework architecture

### Four components

**Variables** are measurement contracts. Each variable has a stable identifier, a declared lifecycle layer, allowed value states, source mappings (DICOM tag, BIDS field, derived formula), and an extraction algorithm reference. Variables define what Vecta measures and where it looks. Version 0.1 defines 22 variables across five domains.

**Criteria** are declarative rules that evaluate one or more variables and emit a structured finding if the condition is satisfied. Each criterion specifies its required variables, a condition tree, and a finding template (label, lifecycle origin, severity, potential downstream effects, recommended remediation). Eight criteria are active in v0.1.

**Intended-use profiles** declare what a specific downstream analysis requires. The `dwi_connectomics` profile specifies which criteria apply, which series are required (DWI + T1w), which are preferred (reverse-PE EPI), which metadata are essential (PhaseEncodingDirection, TotalReadoutTime), and the readiness decision rules (what constitutes ready vs. ready_with_limitations vs. not_ready).

**The criteria engine** evaluates each criterion against the extracted variable values, assembles findings into a structured Assessment object, validates against JSON Schema, and writes outputs in three formats: canonical JSON, tabular TSV, and HTML report. Cohort-level aggregation is a separate step.

### Value states

Every variable observation is assigned one of eight mutually exclusive states:

| State | Meaning |
|---|---|
| `observed` | Value determined from evidence |
| `derived` | Calculated from other variable values |
| `unknown` | Evidence insufficient to determine the value |
| `not_collected` | Not acquired by design |
| `not_applicable` | Variable does not apply to this session or profile |
| `invalid` | Value violates the variable's validity constraints |
| `extraction_failed` | Source present but parsing failed |
| `conflict` | Multiple sources disagree beyond tolerance |

The `unknown` state is never coerced to `false`. When a criterion requires a variable in an `unknown` state, the criterion returns `status: unknown` and **no finding is emitted** — this prevents both false-positive findings and false reassurance.

---

## 5. Variables: what Vecta measures

### Domain 1: Scanner context (4 variables)

These describe the physical scanner and its software version. They are extracted from DICOM headers and/or the BIDS JSON sidecar.

| Variable ID | Name | Source | Lifecycle |
|---|---|---|---|
| `VECTA.DWI.SCANNER.MANUFACTURER` | Scanner manufacturer | DICOM (0008,0070) / BIDS `Manufacturer` | L1 |
| `VECTA.DWI.SCANNER.MODEL` | Scanner model | DICOM (0008,1090) / BIDS `ManufacturersModelName` | L1 |
| `VECTA.DWI.SCANNER.FIELD_STRENGTH` | Magnetic field strength (Tesla) | DICOM (0018,0087) / BIDS `MagneticFieldStrength` | L1 |
| `VECTA.DWI.SCANNER.SOFTWARE_VERSION` | Scanner software version string | DICOM (0018,1020) / BIDS `SoftwareVersions` | L1 |

**Why these matter**: Scanner model and software version determine which metadata fields dcm2niix will successfully extract, whether TotalReadoutTime will be present, whether inline derived maps will be generated (Siemens), and how phase-encoding direction is encoded in DICOM. Different scanner models have different DICOM encoding conventions for the same physical acquisition parameters.

### Domain 2: Acquisition parameters (8 variables)

These describe the DWI acquisition geometry, gradient scheme, and the metadata required for distortion correction.

| Variable ID | Name | Source | Lifecycle | Notes |
|---|---|---|---|---|
| `VECTA.DWI.ACQ.VOXEL_SIZE` | Voxel dimensions (mm per axis) | NIfTI header pixdim / DICOM PixelSpacing+SliceThickness | L1 | Array of 3 floats |
| `VECTA.DWI.ACQ.VOLUME_COUNT` | Number of volumes in the NIfTI | NIfTI header dim[4] | L4 | Must match bval count |
| `VECTA.DWI.ACQ.BVAL_COUNT` | Number of b-value entries in .bval | .bval file | L4 | Must match volume count |
| `VECTA.DWI.ACQ.SHELL_COUNT` | Number of distinct non-zero b-value shells | Derived from .bval | L4 | 1 for single-shell; >1 for multi-shell |
| `VECTA.DWI.ACQ.BVEC_COUNT` | Number of gradient direction vectors in .bvec | .bvec file | L4 | Must match volume count |
| `VECTA.DWI.ACQ.BVEC_PLAUSIBILITY` | Whether all non-b0 gradient vectors have unit magnitude | Derived from .bvec | L4 | False = corrupt/vendor-rescaled bvec |
| `VECTA.DWI.ACQ.PE_DIRECTION` | Phase-encoding direction (BIDS convention: i/j/k with optional -) | BIDS `PhaseEncodingDirection` or `PhaseEncodingAxis` | L1 | Vendor-dependent field name |
| `VECTA.DWI.ACQ.TOTAL_READOUT_TIME_PRESENT` | Whether TotalReadoutTime is present in BIDS sidecar | BIDS `TotalReadoutTime` | L3 | Required for SDC calibration |
| `VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE` | Whether a complementary reverse-PE reference acquisition exists | BIDS inventory + fmap IntendedFor | L1 | Derived; checks PE axis compatibility |

**Key notes on PE_DIRECTION**: Different scanners write different BIDS field names. Siemens Skyra writes `PhaseEncodingAxis` (no polarity sign: `j`). Siemens MAGNETOM Vida Fit and GE write `PhaseEncodingDirection` (with polarity sign: `j-`). These are different BIDS fields with different semantics. Vecta checks both and handles the inconsistency at the variable level; downstream tools that check only one field will miss sessions from scanners that write the other.

**Key notes on REVERSE_PE_AVAILABLE**: This variable does more than check whether a file with `dir-PA` in the name exists. It checks that:
1. A reverse-PE acquisition is present in the fmap/ directory
2. The acquisition is an EPI type (not a GRE phasediff fieldmap, which looks similar but cannot serve as a reverse-PE reference)
3. The phase-encoding axis is compatible with the DWI (same axis, opposite polarity)
4. The fmap's `IntendedFor` field links it to the DWI acquisition

A GRE phasediff fieldmap will be present in the BIDS fmap/ directory but will NOT satisfy REVERSE_PE_AVAILABLE — this is a real edge case observed in the TrackTBI pilot.

### Domain 3: BIDS representation (4 variables)

These check the structural integrity of the BIDS dataset.

| Variable ID | Name | Source | Lifecycle |
|---|---|---|---|
| `VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT` | BIDS Validator error count | BIDS Validator output | L5 |
| `VECTA.DWI.BIDS.VALIDATOR_WARNING_COUNT` | BIDS Validator warning count | BIDS Validator output | L5 |
| `VECTA.DWI.BIDS.DWI_PRESENT` | Whether session contains at least one DWI acquisition | BIDS file inventory | L4 |
| `VECTA.DWI.BIDS.REQUIRED_SERIES_PRESENT` | Map of required series presence for the profile | BIDS file inventory + profile | L4 |

### Domain 4: DICOM source integrity (5 variables)

These require original DICOM to be provided. They check that the DICOM source was exported completely and that the BIDS conversion preserved key values faithfully.

| Variable ID | Name | Source | Lifecycle |
|---|---|---|---|
| `VECTA.DWI.DICOM.SERIES_COUNT` | Total DICOM series in export | DICOM inventory | L2 |
| `VECTA.DWI.DICOM.DWI_SERIES_COUNT` | DWI-classified DICOM series count | DICOM inventory | L2 |
| `VECTA.DWI.DICOM.INSTANCE_COUNT` | Total DICOM instance count | DICOM inventory | L2 |
| `VECTA.DWI.DICOM.SERIES_GEOMETRY_CONSISTENT` | Whether slice geometry is internally consistent within DWI series | DICOM headers | L2 |
| `VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS` | Whether DICOM and BIDS MagneticFieldStrength agree | DICOM vs. BIDS sidecar | L2/L4 |

**If DICOM is not available**: All five of these variables are set to `unknown` or `not_applicable`. The criteria that depend on them (VECTA-DWI-050 and VECTA-DWI-060) will return `status: unknown` and no finding is emitted. Assessment completeness will be lower (roughly 0.87 of the maximum rather than 1.0), but all BIDS-level criteria still run normally.

### Domain 5: Acquisition-derived (1 variable)

| Variable ID | Name | Derived from | Lifecycle |
|---|---|---|---|
| `VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE` | Reverse PE reference availability | BIDS inventory + PE_DIRECTION | L1 |

This variable is listed separately in the specification because it involves multi-source inference (BIDS file inventory, fmap IntendedFor, PE axis compatibility logic) rather than a simple field read.

---

## 6. Criteria: what Vecta checks

Eight criteria are active in v0.1. Each is evaluated per session relative to the `dwi_connectomics` intended-use profile. A criterion either fires (emitting a finding) or is satisfied (no finding). If a required variable is `unknown`, the criterion returns `status: unknown` and no finding is emitted in either direction.

### VECTA-DWI-001 — Phase-encoding direction unknown

| Field | Value |
|---|---|
| **Fires when** | `PE_DIRECTION` state is `unknown` |
| **Severity** | Major |
| **Lifecycle origin** | L3 — Metadata |
| **Readiness effect** | `review_required` (not automatically `ready_with_limitations`) |
| **Requires DICOM?** | No |

This fires when neither the BIDS `PhaseEncodingDirection` nor `PhaseEncodingAxis` field is present, and the value cannot be inferred from any other source. Without knowing the phase-encoding direction, REVERSE_PE_AVAILABLE cannot be determined, and distortion correction is not configurable. This is a review-required condition because the status is genuinely ambiguous — the data may be complete but metadata missing, or the acquisition may have been fundamentally incomplete.

**Remediation**: Recover PhaseEncodingDirection from original DICOM (tag 0018,1312) or from scanner protocol documentation, then regenerate the BIDS sidecar.

---

### VECTA-DWI-014 — Complementary phase-encoding reference unavailable

| Field | Value |
|---|---|
| **Fires when** | `REVERSE_PE_AVAILABLE = false` |
| **Severity** | Major |
| **Lifecycle origin** | L1 — Acquisition |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | No |

This is the most commonly triggered criterion in practice. It fires when no valid reverse-PE EPI acquisition is linkable to the DWI. The finding lifecycle origin is L1 (acquisition) because the root cause is a protocol-level decision made at the scanner — the reverse-PE fieldmap was never acquired. This cannot be remediated after the scan.

**In CIDUR**: Fired for all 34 GE sessions (100%) and no Siemens sessions (0%). GE protocol at this site did not acquire reverse-PE fieldmaps. BIDS Validator reported zero fieldmap-related errors for any of these sessions — the dataset was conformant but not ready for SDC-dependent preprocessing.

**In TrackTBI pilot**: Fired for all 10 sessions. One participant had a GRE phasediff fieldmap (which looked like a fieldmap but was not a reverse-PE EPI acquisition); Vecta correctly identified it as insufficient.

**Remediation**: At the acquisition stage, add a reverse-PE EPI acquisition to the DWI protocol (a short b=0 or low-b acquisition with opposite PE direction). At the analysis stage, consider whether a synthetic fieldmap correction strategy is acceptable for the intended analysis.

---

### VECTA-DWI-021 — Essential metadata absent

| Field | Value |
|---|---|
| **Fires when** | `PE_DIRECTION` is `unknown` OR `TOTAL_READOUT_TIME_PRESENT = false` |
| **Severity** | Major |
| **Lifecycle origin** | L3 — Metadata |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | No |

Fires when either the phase-encoding direction or TotalReadoutTime is missing from the BIDS sidecar. Both are required to configure susceptibility distortion correction. Note that this criterion can fire even when VECTA-DWI-001 does NOT fire: if PE direction is known (from PhaseEncodingAxis) but TotalReadoutTime is absent, only VECTA-DWI-021 fires.

**TotalReadoutTime availability is vendor and sequence-dependent**:
- Siemens Skyra, Vida Fit: typically present; extracted by dcm2niix from DICOM
- GE SIGNA Premier: typically present
- GE DISCOVERY MR750 (e.g., SleepyBrain dataset): absent — GE does not write the required DICOM tag for this scanner/software combination; dcm2niix cannot extract it
- Older Siemens software (syngo MR B17, B19): sometimes absent

**Remediation**: If TotalReadoutTime is absent, check whether `EffectiveEchoSpacing` is present (which allows equivalent calculation), or obtain the value from the scanner protocol sheet and add it to the BIDS sidecar manually.

---

### VECTA-DWI-030 — DWI gradient file missing or unparseable

| Field | Value |
|---|---|
| **Fires when** | `.bval` or `.bvec` file is absent or unparseable |
| **Severity** | Critical |
| **Lifecycle origin** | L4 — Representation |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | No |

Fires when either the .bval file (b-values) or .bvec file (gradient direction vectors) is missing from the BIDS DWI directory. Without both files, no gradient-aware preprocessing can run. QSIPrep, FSL eddy, and MRtrix3 all fail at the gradient-loading step.

**In MASiVar**: Fired for 5 sessions whose .bvec files and NIfTI images were genuinely absent from the OpenNeuro source repository — the data was never deposited. BIDS Validator did not report an error for these sessions (gradient files are treated as optional in BIDS validation).

**Remediation**: Re-run BIDS conversion (`dcm2niix -b y`) from the original DICOM. If DICOM is unavailable, the gradient files cannot be recovered and the session must be excluded from gradient-sensitive analyses.

---

### VECTA-DWI-031 — Gradient vectors have implausible norms

| Field | Value |
|---|---|
| **Fires when** | `BVEC_PLAUSIBILITY = false` (one or more non-b0 vectors deviate from unit magnitude) |
| **Severity** | Critical |
| **Lifecycle origin** | L4 — Representation |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | No |

Fires when gradient direction vectors in the .bvec file have norms significantly different from 1.0. A valid gradient table has unit-magnitude vectors (each pointing on the unit sphere). Some vendors or export pipelines scale the vectors by the b-value or by another factor; these look syntactically valid but encode incorrect diffusion directions that will silently corrupt tensor estimation and tractography.

Vecta intentionally does **not** normalize the vectors before checking. The point is to detect the condition before it reaches the pipeline, not to silently fix it.

**Remediation**: Re-export from DICOM using dcm2niix. If the vendor convention uses a non-unit scale, normalize each direction vector to unit magnitude and document the correction.

---

### VECTA-DWI-040 — No DWI acquisition present

| Field | Value |
|---|---|
| **Fires when** | `DWI_PRESENT = false` (no DWI files in BIDS session) |
| **Severity** | Critical |
| **Lifecycle origin** | L4 — Representation |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | No |

Fires when a BIDS session directory exists but contains no DWI acquisition at all. This is a cohort integrity check — if a session has no DWI, no DWI pipeline should be run on it. Without this check, pipelines may silently create empty output trees.

**Remediation**: Verify whether the DWI acquisition was actually performed at this visit. If it was, check whether it was accidentally excluded during BIDS conversion. If the DWI was not acquired, mark the session as DWI-absent and exclude from DWI-dependent analyses.

---

### VECTA-DWI-050 — DICOM geometry inconsistency

| Field | Value |
|---|---|
| **Fires when** | Slice geometry (position, orientation, spacing) is internally inconsistent across instances within the DWI DICOM series |
| **Severity** | Major |
| **Lifecycle origin** | L2 — Source |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | YES — will not evaluate without DICOM |

Fires when the DWI DICOM series has slices with inconsistent geometry — different spacing, different orientation, or duplicate slice positions. This typically indicates a partial or corrupted DICOM export, interleaved series from multiple acquisitions, or a scanner error. dcm2niix will typically fail or split the series when this occurs.

**In CIDUR**: Did not fire for any of 62 sessions — all DICOM exports were geometrically consistent. This is the expected result for a clean export from a functioning scanner.

**Remediation**: Re-export the DICOM from PACS/XNAT. If the export is incomplete, request a fresh export. If the corruption originated at the scanner, the scan may need to be repeated.

---

### VECTA-DWI-060 — DICOM/BIDS field-strength disagreement

| Field | Value |
|---|---|
| **Fires when** | `MagneticFieldStrength` in DICOM disagrees with BIDS sidecar JSON beyond tolerance |
| **Severity** | Moderate |
| **Lifecycle origin** | L4 — Representation |
| **Readiness effect** | `ready_with_limitations` |
| **Requires DICOM?** | YES — will not evaluate without DICOM |

Fires when the field strength recorded in the DICOM header does not match what dcm2niix wrote to the BIDS JSON sidecar. This indicates a metadata transformation error — the converter may have written a default value, misread the DICOM tag, or the wrong DICOM series was matched during conversion.

**In CIDUR**: Did not fire for any of 61 evaluable sessions.

**Remediation**: Reconcile the BIDS sidecar with the DICOM value. Regenerate the sidecar from the authoritative DICOM source.

---

## 7. Assessment outputs: what Vecta produces

### Per-session outputs

**`vecta.json`** — Canonical structured assessment document. Contains: assessment status and completeness ratio, all variable observations with values and states, all criterion results (satisfied/finding/unknown), all findings with full evidence chain, provenance (Vecta version, spec version, timestamp, input hashes). This is the authoritative record. All other outputs are derived from it.

**`vecta.tsv`** — Tabular projection of the key assessment fields. Suitable for loading into R, Python, or spreadsheet tools.

**`vecta.html`** — Human-readable report summarizing the assessment, findings, and variable observations.

### Cohort-level outputs (from `vecta aggregate`)

**`session_summary.tsv`** — One row per session: subject, session, readiness state, completeness, triggered criteria.

**`findings_long.tsv`** — Long-format table of all findings across all sessions.

**`variable_missingness.tsv`** — Matrix of variable states across sessions, showing which variables are unknown/missing cohort-wide.

**`finding_prevalence.tsv`** — Count and prevalence of each triggered criterion across the cohort.

### Readiness states

| State | Meaning |
|---|---|
| `ready` | No criteria triggered. Session meets all requirements under the declared profile. |
| `ready_with_limitations` | One or more non-blocking criteria triggered. Session has findable limitations but is not prevented from preprocessing. |
| `not_ready` | A blocking criterion triggered (none are currently blocking in `dwi_connectomics` v0.1). Session should not enter the pipeline without remediation. |
| `review_required` | A review criterion (VECTA-DWI-001) returned `unknown`. Cannot determine readiness; human review needed. |
| `not_assessed` | Assessment could not be completed (e.g., missing JSON sidecars). |

### Assessment completeness ratio

A value between 0 and 1 indicating what fraction of variables were successfully evaluated versus returning `unknown` or `extraction_failed`. A completeness of 1.0 means all 22 variables were successfully extracted. A lower value indicates that some variables could not be determined — typically because DICOM was not available (reduces to ~0.87) or because BIDS sidecars are incomplete.

---

## 8. Data requirements for running Vecta

### Required: BIDS dataset

Vecta's primary input is a BIDS-formatted dataset. The minimum required for a meaningful assessment is:

```
sub-<ID>/
  ses-<ID>/
    dwi/
      *_dwi.nii.gz       # DWI NIfTI image
      *_dwi.json         # BIDS sidecar JSON (PhaseEncodingDirection, TotalReadoutTime, etc.)
      *_dwi.bval         # b-value table
      *_dwi.bvec         # gradient direction vectors
    fmap/                # optional but strongly preferred
      *_dir-PA_epi.nii.gz   # reverse-PE EPI fieldmap
      *_dir-PA_epi.json     # with IntendedFor pointing to DWI
    anat/                # optional but required by dwi_connectomics profile
      *_T1w.nii.gz
```

**The JSON sidecar is critical.** It must contain:
- `PhaseEncodingDirection` or `PhaseEncodingAxis` (required for VECTA-DWI-001 and VECTA-DWI-014)
- `TotalReadoutTime` (required for VECTA-DWI-021 to not fire; absent for some scanners)
- `Manufacturer`, `ManufacturersModelName`, `MagneticFieldStrength`, `SoftwareVersions` (used for scanner context variables)

### Optional but strongly recommended: Original DICOM

Providing the original DICOM archive (alongside the BIDS dataset) enables the DICOM source-integrity module (VECTA-DWI-050 and VECTA-DWI-060) and increases assessment completeness to approximately 0.91–0.95.

Provide DICOM via the `--dicom` argument to `vecta assess`:
```bash
vecta assess --bids /path/to/bids --dicom /path/to/dicom_archive \
             --profile dwi_connectomics --output /path/to/output/
```

### Optional: QSIPrep output tree (for outcome labeling)

If QSIPrep has been run on the cohort, Vecta can label outcomes and join them to the assessment:
```bash
vecta label-outcomes --qsiprep /path/to/qsiprep_output/
vecta join-outcomes --assessments /path/to/vecta_output/ \
                    --outcomes /path/to/outcomes.tsv
```
This produces a joined table enabling comparison of Vecta readiness states against actual preprocessing outcomes.

---

## 9. TBI study: what to collect and why

The following is a specific checklist for collecting data at TBI study sites to maximize Vecta's assessment coverage and enable the full outcome analysis.

### At every scan visit

#### 1. Acquire the reverse-PE EPI fieldmap

**This is the single most important acquisition decision.** Without it, VECTA-DWI-014 will fire for every session, and susceptibility distortion correction cannot be applied.

A reverse-PE fieldmap is a short DWI-protocol-matched acquisition with the phase-encoding direction reversed:
- Same slice prescription as the main DWI
- b=0 (or very low b-value, e.g., b=5) is sufficient — no diffusion weighting needed
- Typical acquisition time: 15–45 seconds
- Filename in BIDS: `*_dir-PA_epi.nii.gz` (if main DWI is AP) + corresponding `.json` sidecar

**Key requirement**: The fieldmap JSON sidecar must have `IntendedFor` populated to point to the DWI NIfTI. `dcm2niix` does not do this automatically — a post-conversion step is needed (see Section 10).

#### 2. Acquire a T1w anatomical

Required by the `dwi_connectomics` profile. QSIPrep requires a T1w for DWI-anatomical co-registration. Without it, QSIPrep will not run regardless of DWI quality.

#### 3. Record the full DWI acquisition with correct BIDS naming

Standard DWI: `*_dir-AP_dwi.nii.gz` + `.json` + `.bval` + `.bvec`

All four files are required. A NIfTI without a bval or bvec cannot be preprocessed.

### At every site: DICOM archiving

**Retain original DICOM for all sessions.** Do not delete DICOM after BIDS conversion. Archive it alongside the BIDS dataset.

Why DICOM matters for Vecta:
- Enables VECTA-DWI-050 (geometry consistency check)
- Enables VECTA-DWI-060 (field-strength cross-validation with BIDS)
- Provides the authoritative source if bval/bvec files need to be regenerated (VECTA-DWI-030 remediation)
- Documents session ordering when study dates are de-identified

Organize DICOM so that each subject has a clear directory per visit, and each visit directory maps to a BIDS session. Record this mapping explicitly — if sessions are later excluded and BIDS session numbering changes, the DICOM-to-BIDS mapping must be preserved.

**DICOM de-identification**: If dates are blanked during de-identification (common practice), document the study UID for each visit alongside the BIDS session ID. Vecta's current DICOM session-matching uses alphabetical directory ordering when study dates are absent; if sessions are later renumbered, this heuristic may resolve to the wrong DICOM directory. A UID-based crosswalk prevents this.

### At site setup: verify TotalReadoutTime availability

Before the full study begins, run a single pilot session through Vecta and check whether `TotalReadoutTime` is present in the DWI JSON sidecar.

If it is absent:
- Check whether `EffectiveEchoSpacing` is present (allows equivalent calculation)
- If neither is present, contact the scanner physicist to determine whether the parameter can be enabled in the export protocol or obtained from the protocol documentation
- Document the TotalReadoutTime value for each scanner used and add it to the BIDS sidecars if it must be manually specified

This is especially important for:
- GE DISCOVERY MR750 (known to not export this field)
- Older Siemens syngo MR versions (B17, B19)
- Philips scanners (frequently absent)

### Multi-site consistency checklist

For each site in the TBI study, verify the following before enrolling participants:

| Check | What to verify | Vecta criterion affected |
|---|---|---|
| Reverse-PE fieldmap in protocol | `*_dir-PA_epi` is acquired at every DWI visit | VECTA-DWI-014 |
| PE direction documented | BIDS sidecar has `PhaseEncodingDirection` or `PhaseEncodingAxis` | VECTA-DWI-001, 021 |
| TotalReadoutTime available | BIDS sidecar has `TotalReadoutTime` | VECTA-DWI-021 |
| bval and bvec generated | Conversion produces `.bval` and `.bvec` | VECTA-DWI-030 |
| bvec vectors unit-scaled | Gradient norms ≈ 1.0 | VECTA-DWI-031 |
| DICOM archived | Full session DICOM retained alongside BIDS | VECTA-DWI-050, 060 |
| fmap IntendedFor populated | Post-conversion step adds `IntendedFor` to fieldmap JSON | VECTA-DWI-014 |
| T1w acquired | Anatomical present in BIDS | QSIPrep requirement |

Run this checklist using Vecta on a pilot session from each site before enrolling participants. A completeness ratio below 0.90 on the pilot session indicates a data collection or conversion configuration problem.

### What the CIDUR and TrackTBI data tell us to expect

From the CIDUR cohort (University of Rochester, Siemens + GE scanners):
- Siemens sessions (Skyra, Vida Fit): All had reverse-PE fieldmaps → `ready`
- GE sessions (SIGNA Premier, SIGNA Artist): None had reverse-PE fieldmaps → `ready_with_limitations` with VECTA-DWI-014
- All 62 sessions had valid bval/bvec, correct geometry, no field-strength conflicts

From the TrackTBI pilot (Baylor College of Medicine, MGH; Siemens TrioTim and Skyra):
- All 10 sessions triggered VECTA-DWI-014 (no reverse-PE EPI fieldmap)
- One session had a GRE phasediff fieldmap — looked like a fieldmap but did not satisfy the reverse-PE requirement
- DICOM was not available → VECTA-DWI-050 and VECTA-DWI-060 not evaluated (completeness ≈ 0.88)

**For the full TBI study**: Verify the reverse-PE fieldmap acquisition status at each site early. Siemens sites that have already had Skyra or Vida Fit protocols at CIDUR will likely have fieldmaps. Sites with GE scanners or older Siemens software may not. Protocol harmonization across sites — specifically, adding a reverse-PE EPI acquisition — is the single most impactful protocol change that can be made before the study begins.

---

## 10. Running Vecta

### Installation

```bash
pip install git+https://github.com/phindagijimana/vecta-dwi.git
```

### Assess a single session

```bash
vecta assess \
  --bids /path/to/bids_root \
  --subject sub-001 \
  --session ses-1 \
  --profile dwi_connectomics \
  --output /path/to/output/sub-001_ses-1/ \
  --dicom /path/to/dicom_archive/EP007361/visit_1/   # optional
```

### Assess an entire cohort

```bash
# Assess all sessions
for sub in sub-001 sub-002 sub-003 ...; do
  for ses in ses-1 ses-2; do
    vecta assess \
      --bids /path/to/bids_root \
      --subject $sub --session $ses \
      --profile dwi_connectomics \
      --output /path/to/output/${sub}_${ses}/ \
      --dicom /path/to/dicom_archive/ 2>/dev/null
  done
done

# Aggregate results across the cohort
vecta aggregate \
  --assessments /path/to/output/ \
  --output /path/to/cohort_summary/
```

### Populate fieldmap IntendedFor (post-conversion step)

After BIDS conversion, run this step to ensure fieldmap JSON sidecars have `IntendedFor` pointing to the DWI:

```bash
python fill_fmap_intended_for.py --root /path/to/bids_root
```

This is required for VECTA-DWI-014 to correctly link the fieldmap to the DWI. Without it, a fieldmap may be present in BIDS but invisible to Vecta's reverse-PE detection logic.

### Label QSIPrep outcomes and join to assessments

```bash
vecta label-outcomes \
  --qsiprep /path/to/qsiprep_output/ \
  --output /path/to/outcomes.tsv

vecta join-outcomes \
  --assessments /path/to/cohort_summary/session_summary.tsv \
  --outcomes /path/to/outcomes.tsv \
  --output /path/to/joined.tsv
```

---

## 11. What to do when a criterion fires

### Reading a finding

Every finding contains:
- **Label**: Short description of what was found
- **Severity**: `informational` / `minor` / `major` / `critical`
- **Lifecycle origin**: Which layer the problem originated at (L1–L5)
- **Potential effects**: What downstream consequences are plausible
- **Recommended actions**: Specific remediation steps with action class (review, re-export, repair, exclude)

### Severity guide

| Severity | Meaning | Typical action |
|---|---|---|
| `informational` | Noted observation, no readiness impact | Document; no action required |
| `minor` | Small deviation from ideal; unlikely to affect results | Review; document in analysis notes |
| `major` | Missing or incorrect data property with plausible effect on preprocessing | Review; attempt remediation; document limitation if unremediable |
| `critical` | Missing or invalid data property that will prevent preprocessing or invalidate results | Remediate before running pipeline; exclude if unremediable |

### Remediable vs. not remediable

| Finding | Remediable? | How |
|---|---|---|
| VECTA-DWI-014 (no reverse-PE fieldmap) | Not after scanning | Add fieldmap acquisition to protocol for future visits; consider synthetic SDC for existing sessions |
| VECTA-DWI-021 (TotalReadoutTime absent) | Sometimes | Extract from DICOM `EffectiveEchoSpacing`; add manually to sidecar if value known from protocol |
| VECTA-DWI-030 (missing bval/bvec) | If DICOM retained | Re-run dcm2niix on original DICOM |
| VECTA-DWI-031 (non-unit bvec norms) | If DICOM retained | Re-run dcm2niix; or normalize vectors if vendor scaling is known |
| VECTA-DWI-050 (DICOM geometry) | If DICOM retained | Re-export from PACS; contact scanner physicist if scan-time error |
| VECTA-DWI-060 (field-strength mismatch) | Yes | Regenerate BIDS sidecar from authoritative DICOM |
| VECTA-DWI-001 (PE direction unknown) | If DICOM retained | Recover from DICOM tag 0018,1312; add to sidecar |
| VECTA-DWI-040 (no DWI) | If acquisition was done | Check BIDS conversion; re-run if DWI was excluded accidentally |

### Distinguishing ready_with_limitations from not_ready

In the current `dwi_connectomics` v0.1 profile, **no criterion makes a session `not_ready`**. All triggered criteria produce `ready_with_limitations`. This reflects the evidence base: even without a reverse-PE fieldmap, QSIPrep will often complete using a fallback correction path (synthetic SDC or no SDC), and the output may still be scientifically valid depending on the analysis.

`ready_with_limitations` means: the session can enter preprocessing, but the analysis notes must document the limitation, and the results should be interpreted with awareness of it. For VECTA-DWI-014, this means: results from sessions without SDC should be characterized as such in any publication.

`review_required` (from VECTA-DWI-001) means: the session cannot be automatically classified. A human must review the PE direction situation and decide whether preprocessing should proceed.

---

## 12. Full TrackTBI validation: data specification to fill paper 1 gaps

This section documents exactly what data must be collected, retained, and processed from the full TrackTBI cohort to close the scientific gaps in the paper. Each subsection identifies a specific gap, the data required to address it, and the exact Vecta commands and output files that generate the evidence.

**Available data for the full TrackTBI cohort**: BIDS-converted DWI sessions and QSIPrep output tree. Original DICOM is not available. Assessment completeness will be approximately 0.87 (same as the TrackTBI pilot), since VECTA-DWI-050 and VECTA-DWI-060 require DICOM and will return `unknown` for all sessions.

### Gap map: what the paper currently lacks and what fills it

| Gap | Root cause | What fills it |
|---|---|---|
| n=1 failure event in primary cohort | CIDUR had only 1 QSIPrep failure | Full TrackTBI: ~600 sessions across multiple sites, more failure events expected |
| Only VECTA-DWI-014 active in primary cohort | CIDUR conversion was clean; same protocol at all Siemens sites | Multi-site TBI: different scanners, software versions, and conversion pipelines will activate other criteria |
| No confidence intervals on sensitivity | Sample size too small for CI | Full TrackTBI: sufficient N for binomial CI on sensitivity/specificity |
| VECTA-DWI-021 outcome validation | SleepyBrain/MASiVar have no labeled outcomes | TBI sites with absent TotalReadoutTime (GE or older Siemens) + QSIPrep outcomes |
| VECTA-DWI-050/060 outcome validation | CIDUR DICOM was clean; no criterion fired | **Not fillable with current TBI data** — requires DICOM; all sessions will return `unknown` for these criteria |
| Single-site primary cohort | CIDUR = one site | Full TBI = multiple independent sites, scanners, operators |
| TrackTBI pilot = 5 subjects only | Subset analyzed | Full cohort run with Vecta + outcome labeling |

---

### Data element 1: BIDS-converted DWI for all sessions

**What**: Full BIDS dataset for all ~600 TrackTBI sessions.

**Files required per session**:
```
sub-<ID>/ses-<timepoint>/
  dwi/
    *_dwi.nii.gz          # REQUIRED
    *_dwi.json            # REQUIRED — must have PE direction + TotalReadoutTime if available
    *_dwi.bval            # REQUIRED
    *_dwi.bvec            # REQUIRED
  fmap/
    *_dir-PA_epi.nii.gz   # STRONGLY PREFERRED — absence activates VECTA-DWI-014
    *_dir-PA_epi.json     # REQUIRED if fieldmap present — must have IntendedFor
  anat/
    *_T1w.nii.gz          # REQUIRED by dwi_connectomics profile
```

**Time points**: Both the 2-week and 6-month sessions for every participant. The 2-week sessions already have QSIPrep outcomes in the pilot. The 6-month sessions do not yet; running QSIPrep on both time points doubles the outcome sample.

**Gaps this fills**:
- Provides the denominator (N) for powered sensitivity/specificity estimation
- 2-week + 6-month doubles the session count relative to using one time point only
- Multi-site DWI will activate criteria that never fired in CIDUR (different scanners → different metadata completeness)

**Vecta command**:
```bash
# Run for each subject/session
vecta assess \
  --bids /path/to/tracktbi_bids \
  --subject sub-<ID> --session ses-<timepoint> \
  --profile dwi_connectomics \
  --output /path/to/tracktbi_vecta_run/sub-<ID>_ses-<timepoint>/

# Then aggregate
vecta aggregate \
  --assessments /path/to/tracktbi_vecta_run/ \
  --output /path/to/tracktbi_cohort_summary/
```

**Output files needed**:
- `tracktbi_cohort_summary/session_summary.tsv` — readiness state per session
- `tracktbi_cohort_summary/finding_prevalence.tsv` — which criteria fired and how often

---

### Data element 2: QSIPrep output tree for all sessions

**What**: The complete QSIPrep v0.23.1 (or equivalent pinned version) output directory for every session.

**Why version pinning matters**: The outcome label (`QSIPREP_SUCCESS`) is defined as: preprocessed DWI NIfTI present at `<qsiprep_output>/sub-<ID>/ses-<X>/dwi/*_desc-preproc_dwi.nii.gz`. Different QSIPrep versions may handle edge cases differently (e.g., fallback SDC behavior). All sessions in a single cohort analysis should be processed with the same QSIPrep version to avoid version-driven variability in the outcome label.

**Files required per session for outcome labeling** (only one file is actually checked):
```
<qsiprep_output>/
  sub-<ID>/
    ses-<timepoint>/
      dwi/
        *_desc-preproc_dwi.nii.gz    # PRESENT = success; ABSENT = failure
```

**Run QSIPrep for both time points**. The pilot only has 2-week outcomes. 6-month outcomes double the sample.

**Gaps this fills**:
- Provides the outcome event count needed for CI estimation on sensitivity
- 6-month sessions add ~300 additional outcome events
- Across multiple sites, some sessions will fail QSIPrep for gradient-related reasons, providing outcome data for VECTA-DWI-030/031

**Vecta outcome labeling commands**:
```bash
# After QSIPrep completes, label outcomes
vecta label-outcomes \
  --qsiprep /path/to/tracktbi_qsiprep_output/ \
  --output /path/to/tracktbi_outcomes.tsv

# Join to Vecta assessments
vecta join-outcomes \
  --assessments /path/to/tracktbi_cohort_summary/session_summary.tsv \
  --outcomes /path/to/tracktbi_outcomes.tsv \
  --output /path/to/tracktbi_joined.tsv
```

**Output file needed**: `tracktbi_joined.tsv` — one row per session with: subject, session, site, scanner, Vecta readiness state, triggered criteria, QSIPrep success flag.

---

### Data element 3: Post-conversion BIDS validation output

**What**: BIDS Validator output (JSON format) for the full TrackTBI BIDS dataset.

**Why**: The ablation comparison (Levels 0–3) in the paper requires knowing how many sessions have BIDS Validator errors vs. Vecta findings. For the full TBI cohort, this generates Table 5 (Level 0–3 sensitivity) with sufficient N for statistics.

**Command**:
```bash
bids-validator /path/to/tracktbi_bids --json > /path/to/tracktbi_bids_validator.json
```

**What Vecta reads from this**: The `VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT` and `VALIDATOR_WARNING_COUNT` variables are extracted from this file during assessment. It must be run with the same BIDS Validator version as was used in the paper (currently pinned; check `specification/v0.1/` for the pinned version).

---

### Complete run pipeline: end-to-end commands for the full TBI analysis

Once all data elements above are assembled, run the following pipeline in order. Each step depends on the previous.

**Step 1: Run BIDS Validator (once per cohort)**
```bash
bids-validator /path/to/tracktbi_bids --json \
  > /path/to/tracktbi_analysis/bids_validator_output.json
```

**Step 2: Run Vecta assessment on all sessions**
```bash
# Requires: BIDS dataset only (no DICOM available)
# VECTA-DWI-050 and VECTA-DWI-060 will return unknown; completeness ~0.87
# Output: per-session vecta.json files

python3 scripts/run_vecta_cohort.py \
  --bids /path/to/tracktbi_bids \
  --profile dwi_connectomics \
  --output-root /path/to/tracktbi_analysis/vecta_run/
```

**Step 3: Aggregate Vecta results**
```bash
vecta aggregate \
  --assessments /path/to/tracktbi_analysis/vecta_run/ \
  --output /path/to/tracktbi_analysis/cohort_summary/
```

**Step 4: Label QSIPrep outcomes**
```bash
vecta label-outcomes \
  --qsiprep /path/to/tracktbi_qsiprep/ \
  --output /path/to/tracktbi_analysis/qsiprep_outcomes.tsv
```

**Step 5: Join assessments to outcomes**
```bash
vecta join-outcomes \
  --assessments /path/to/tracktbi_analysis/cohort_summary/session_summary.tsv \
  --outcomes /path/to/tracktbi_analysis/qsiprep_outcomes.tsv \
  --output /path/to/tracktbi_analysis/joined_assessments_outcomes.tsv
```

**Step 6: Run ablation comparison script**
```bash
python3 scripts/compute_ablation_table.py \
  --joined /path/to/tracktbi_analysis/joined_assessments_outcomes.tsv \
  --output /path/to/tracktbi_analysis/ablation_table.tsv
```

The following files from `tracktbi_analysis/` feed directly into paper figures and tables:

| File | Paper use |
|---|---|
| `cohort_summary/session_summary.tsv` | Readiness distribution table; criterion prevalence table |
| `cohort_summary/finding_prevalence.tsv` | Criterion × site heatmap; update Table 5 |
| `cohort_summary/variable_missingness.tsv` | Assessment completeness by site/scanner |
| `joined_assessments_outcomes.tsv` | Contingency table (Table 2 equivalent for TBI); sensitivity/specificity with CI |
| `ablation_table.tsv` | Extended ablation comparison (Levels 0–3) with full-cohort N |

---

### Minimum viable dataset: what you need at a minimum for paper 1

The available TBI data (BIDS + QSIPrep outcomes) covers the two highest-priority elements. Priority ordering within what is available:

| Priority | Data element | Why it's highest priority |
|---|---|---|
| 1 | BIDS DWI + bval/bvec + JSON sidecars for all ~600 sessions | Vecta cannot run without these |
| 2 | QSIPrep outcomes for all sessions | Without outcomes, no criterion-to-outcome validation |
| 3 | Both time points (2-week + 6-month) | Doubles N; 6-month failure events expected |
| 4 | BIDS Validator output | Required for Level 0 ablation comparison |

Note: DICOM is not available for this cohort. VECTA-DWI-050 and VECTA-DWI-060 will return `unknown` for all sessions; assessment completeness will be approximately 0.87 rather than the 0.91 achieved in CIDUR. The DICOM-dependent gap (VECTA-DWI-050/060 outcome validation) cannot be filled with the current TBI data and will remain an open item for future work.

**Even 200 sessions with QSIPrep outcomes from the full TBI cohort would be sufficient to compute confidence intervals and formally test the VECTA-DWI-014 association.** The n=1 failure problem is solved as soon as the cohort contains more than one session where QSIPrep failed — which is expected at multi-site scale.

---

### What to expect each criterion to do in the full TBI cohort

Based on the CIDUR and TrackTBI pilot findings, this is the expected criterion behavior across a multi-site TBI dataset. Where a criterion is expected to fire, the table identifies what outcome data is needed to complete its validation.

| Criterion | Expected behavior in full TBI | Outcome data needed |
|---|---|---|
| VECTA-DWI-001 (PE unknown) | May fire at sites with older scanners (syngo B17/B19) or Philips scanners where PE direction is not reliably exported | QSIPrep success/failure for these sessions |
| VECTA-DWI-014 (no reverse PE) | Will fire at all sites where the reverse-PE fieldmap was not acquired. In the 5-subject pilot, 100% of sessions triggered. The full TBI protocol at each site must be checked. | QSIPrep outcome + SDC fallback path confirmation |
| VECTA-DWI-021 (essential metadata) | Will fire at GE sites without TotalReadoutTime export, and at Siemens sites with older software. The site protocol registry determines which sites are expected to trigger this. | QSIPrep outcome for sessions where TotalReadoutTime is absent |
| VECTA-DWI-030 (gradient missing) | Low expected rate but non-zero across 600+ sessions; most likely at sites with manual BIDS conversion or DICOM export gaps. | QSIPrep failure expected for all triggered sessions |
| VECTA-DWI-031 (bvec implausible) | Low expected rate; may appear at Philips sites (known for non-unit gradient vector scaling) or from BIDS conversion pipeline bugs. | QSIPrep outcome; direct bvec norm inspection |
| VECTA-DWI-040 (no DWI) | Should be rare if BIDS conversion is supervised; may appear if a session's DWI was corrupted and excluded. | QSIPrep produces no DWI output (confirms finding) |
| VECTA-DWI-050 (DICOM geometry) | **Will return `unknown` — DICOM not available.** Cannot be evaluated without DICOM. | Not evaluable with current TBI data |
| VECTA-DWI-060 (field-strength mismatch) | **Will return `unknown` — DICOM not available.** Cannot be evaluated without DICOM. | Not evaluable with current TBI data |

---

*Vecta-DWI specification version 0.1.0. For the latest version, see the [GitHub repository](https://github.com/phindagijimana/vecta-dwi).*
