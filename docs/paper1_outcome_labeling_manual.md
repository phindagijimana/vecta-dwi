# Paper 1 — Outcome labeling manual (draft)

**Status**: CONFIRMED — all seven open items resolved 2026-09-20.
Ready for `vecta-dwi-v0.1.0-paper1` freeze pending PI co-confirmation
of reviewer roles.

**Purpose**: Define the operational labeling procedure for every
downstream outcome Paper 1's statistical analyses depend on. Frozen
before the primary TBI validation analysis runs. Never changed after
inspecting outcome-stratified results; changes require a protocol
amendment.

**Scope**: outcomes are joined to Vecta assessments via the
`ResearchOutcome` schema at analysis time, not embedded in the
deterministic Vecta engine.

---

## 1. Primary outcome

**Definition**: A session's primary outcome is

  `qsiprep_success = true`

if all three of the following hold:

  (a) **QSIPrep exited zero** for the frozen configuration (Section 3).
  (b) **All required derivatives** (Section 4) are produced and pass
      structural sanity checks.
  (c) **No case-specific manual intervention** occurred; either the
      session ran under the frozen standard configuration or the only
      intervention was a `minor`-tier allowlisted action (Section 5).

Otherwise `qsiprep_success = false`.

**Binary**. Ordinal information (retry count, intervention level, QC
status) is captured as **secondary outcomes** — not folded into the
primary label.

**Deliberately excludes** infrastructure-only failures (scheduler
death, container error, quota limit) from the outcome. These become
`assessment_status.error` events, not data-quality failures.

## 2. Frozen QSIPrep configuration

**CONFIRMED** (2026-09-20). Verified from
`qsiprep_single_run_output/dataset_description.json`:

- **QSIPrep version**: `0.23.1.dev0+g634483f.d20240830`
  (development build pinned to commit `g634483f`, dated 2024-08-30)
- **Container**: Apptainer SIF; digest to be recorded from the
  `dwi_pipeline/` Snakemake submission logs (pending retrieval from
  HPC job records — does not block freeze).
- **Command-line invocation**: documented in
  `Documents/TrackTBI-Sub/dwi_pipeline/bids_app.sh`.
- **Reconstruction**: QSIPrep preprocessing only for Paper 1.
  QSIRecon / tractography / connectome are Paper 2 outcomes (Section 3).
- **FreeSurfer**: FastSurfer used (confirmed from `subject_qc.json`
  `recon.tool = fastsurfer`).
- **Distortion correction**: PEPOLAR (TOPUP) for sessions with reverse-PE
  fmap; explicit `--no-sdc` for GE sessions without fmap
  (`postprocess_vendor_dwi_fmap_rules.py` output flag). Both
  configurations are labeled under the same version; SDC availability
  is captured in `VECTA.DWI.ACQUISITION.REVERSE_PE_AVAILABLE`.

**Any change to this configuration is a new version.** Sessions run
under different configurations must be labeled with the configuration
they were actually run under; they cannot be pooled.

## 3. Required derivatives

**CONFIRMED** (2026-09-20). Filename patterns verified against actual
`qsiprep_single_run_output/sub-001/ses-1/dwi/` output. All patterns
use glob `*` for the `acq-` and `dir-` entities which vary by subject.

**Paper 1 required derivatives** (all under `sub-{id}/ses-{id}/dwi/`):

| Derivative glob | Structural sanity check |
|---|---|
| `*_space-T1w_desc-preproc_dwi.nii.gz` | NIfTI readable; 4D; dim[4] matches `.bval` count |
| `*_space-T1w_desc-preproc_dwi.bval` | Whitespace-parseable numeric list; length = NIfTI dim[4] |
| `*_space-T1w_desc-preproc_dwi.bvec` | Three rows of equal length; length = `.bval` |
| `*_space-T1w_desc-brain_mask.nii.gz` | NIfTI readable; 3D; ≥ 1000 non-zero voxels |
| `*_space-T1w_dwiref.nii.gz` | NIfTI readable; 3D |

All five must pass for `VECTA.OUTCOME.QSIPREP_SUCCESS = true`. These
match the patterns used in `src/vecta/research/outcomes.py` §`check_session_derivatives()`.

**Paper 2 derivatives** (QSIRecon / tractography / connectome):
These are labeled as secondary outcomes for completeness but are
**out of scope for Paper 1's primary analysis**. Columns
`VECTA.OUTCOME.QSIRECON_SUCCESS`, `VECTA.OUTCOME.CONNECTOME_AVAILABLE`,
and `VECTA.OUTCOME.NODESTRENGTH_AVAILABLE` are emitted by the outcomes
module for use in Paper 2 and beyond.

## 4. Failure taxonomy

When `qsiprep_success = false`, one and only one failure category is
assigned per session. Categories are ordered by precedence (top wins):

| # | Category | When to assign |
|---|---|---|
| 1 | `infrastructure_or_hpc_failure` | Scheduler kill / OOM / disk full / container network error. QSIPrep did not run to natural termination. **Excluded from Paper 1 primary outcome regression.** |
| 2 | `software_error` | QSIPrep raised an unhandled exception traceable to a pipeline bug, not a data property. Requires manual adjudication. |
| 3 | `source_data_missing` | A required BIDS entity (dwi, T1w, reverse-PE fmap when configured) is absent at pipeline start. |
| 4 | `metadata_insufficient` | Pipeline start failed on missing / invalid essential metadata (PhaseEncodingDirection, TotalReadoutTime, gradient tables). |
| 5 | `conversion_failure` | dcm2niix / conversion artifact detected at pipeline start (e.g. extra unexpected outputs, geometry error). |
| 6 | `gradient_integrity_failure` | QSIPrep's gradient sanity check failed. |
| 7 | `distortion_correction_failure` | TOPUP / fieldmap-based correction failed to converge or produced degenerate output. |
| 8 | `registration_failure` | DWI→T1 or T1→template registration failed convergence check. |
| 9 | `anatomical_dependency_failure` | Missing or invalid T1 processing dependency (skull strip, segmentation). |
| 10 | `reconstruction_failure` | QSIRecon (if included) failed. |
| 11 | `manual_qc_failure` | Human QC reviewer marked the derivative unusable per Section 8. |
| 12 | `unknown_failure` | Adjudication could not assign a category. |

Assignment procedure: Section 7.

## 5. Manual intervention rubric

| Level | Definition | Examples |
|---|---|---|
| `none` | Session ran under frozen configuration, no case-specific action. | Pipeline ran to completion first attempt. |
| `minor` | Predefined action from an allowlist (Section 5.1). | Retry same config after transient scheduler kill (rerun only). |
| `major` | Case-specific parameter change, workflow change, or file repair. | Manual PhaseEncodingDirection assignment; gradient table reconstruction; series re-classification; distortion strategy override; manual BIDS sidecar edit. |
| `unrecoverable` | No configuration produces required derivatives. | Missing critical acquisition; corrupted DICOM series. Downstream label: `qsiprep_success = false`, category `manual_qc_failure` or `source_data_missing`. |

### 5.1 The `minor` allowlist (frozen)

**CONFIRMED** (2026-09-20) — four items.

Only these actions may be classified as `minor`. Anything else is
`major`.

1. **Rerun same configuration** after an infrastructure-only failure
   (Section 4 category 1) with no other change.
2. **Fresh Freesurfer/FastSurfer input** substitution when the initial
   FS output was infrastructure-corrupted, using a rerun of the same
   FS configuration (not a different FS version).
3. **Wall-time / memory bump** within the pre-registered range
   (defined per site at freeze) for sessions that ran to a partial
   result and would clearly complete with more resources.
4. **Explicit `--no-sdc` flag** applied to GE sessions without a
   reverse-PE fieldmap (legacy no-fieldmap protocol). This is a
   pre-registered configuration variant, not a session-specific
   override: all GE sessions without fmap run under `--no-sdc` by
   rule in `postprocess_vendor_dwi_fmap_rules.py`. The absence of
   susceptibility distortion correction is captured by
   `VECTA-DWI-014` (REVIEW_REQUIRED) and recorded in
   `VECTA.DWI.ACQUISITION.REVERSE_PE_AVAILABLE = false`.
   Also includes: **no PhaseEncodingDirection in sidecar** handled
   by filename inference (all MATCH per `dwi_phase_encoding_traceability.csv`).

**Not allowed as `minor`**: any change to acquisition-metadata
handling beyond the pre-registered rules above; any change to
`--recon-spec`; any manual file edit or reassociation not listed here.

## 6. Secondary outcomes

Independently labeled. Not derived from `qsiprep_success`:

| Outcome ID | Type | Definition |
|---|---|---|
| `VECTA.OUTCOME.QSIPREP_SUCCESS` | bool | The primary outcome. |
| `VECTA.OUTCOME.QSIPREP_FAILURE_CATEGORY` | enum | Section 4 category, or null if success. |
| `VECTA.OUTCOME.RETRY_COUNT` | int | Number of distinct QSIPrep attempts, including allowlisted retries. |
| `VECTA.OUTCOME.MANUAL_INTERVENTION_LEVEL` | enum | Section 5 level. |
| `VECTA.OUTCOME.MANUAL_INTERVENTION_TIME` | float / null | Engineer time in minutes, if reliably measurable. |
| `VECTA.OUTCOME.QC_STATUS` | enum | `pass` / `review` / `fail` per Section 8. |
| `VECTA.OUTCOME.WALL_TIME` | float | Pipeline wall time in hours. |
| `VECTA.OUTCOME.CPU_HOURS` | float | Compute burden. |
| `VECTA.OUTCOME.FAILED_COMPUTE_HOURS` | float | Compute spent on failed attempts. |
| `VECTA.OUTCOME.PREPROC_DWI_AVAILABLE` | bool | Preprocessed DWI file exists and passes sanity check. |
| `VECTA.OUTCOME.TRACTOGRAPHY_AVAILABLE` | bool | If QSIRecon in pipeline. |
| `VECTA.OUTCOME.CONNECTOME_AVAILABLE` | bool | If QSIRecon in pipeline. |

## 7. Assignment procedure

Per session:

1. **Read the QSIPrep run log**. Extract exit code, wall time, CPU
   time, retry count.
2. **Check required derivative inventory** (Section 3). Run structural
   sanity checks.
3. **If all derivatives present + sanity checks pass + intervention =
   none or minor** → `qsiprep_success = true`. Failure category = null.
4. **Otherwise** → `qsiprep_success = false`. Assign failure category
   by walking the taxonomy (Section 4) in precedence order and
   selecting the first category that matches the observed log +
   derivative state.
5. **Label `MANUAL_INTERVENTION_LEVEL`** independently from success:
   even sessions with `qsiprep_success = true` may have `minor`
   intervention.
6. **Record log excerpts** supporting the category assignment (5–20
   lines from the QSIPrep log) in the outcome record.

## 8. QC status labeling

Independent of QSIPrep exit status. A reviewer inspects each
successful session's preprocessed DWI + brain mask against the
pre-registered visual rubric:

- `pass` — no visible artifacts affecting downstream analysis.
- `review` — borderline; requires second reviewer.
- `fail` — visible artifact (severe motion, distortion residual,
  registration failure) that would invalidate downstream analysis.

Visual rubric details (screenshot templates, decision tree) to be
appended as Section 12 before freeze.

## 9. Reviewer roles and adjudication

**CONFIRMED** (2026-09-20).

| Role | Assignment | Responsibility |
|---|---|---|
| Automated labeler | `src/vecta/research/outcomes.py` | Derivative sanity checks; emits candidate label for every session. |
| Primary reviewer (DWI expert) | P.N. (extensive DWI experience, CIDUR data curator) | Confirms or overrides automated label. Assigns intervention level. Records QC status. Final authority on ambiguous cases pending adjudicator. |
| Secondary reviewer (independent) | PI (to be confirmed) | Reviews all sessions labeled `review` or `fail`, and a 10% random sample of `pass` sessions for reliability. |
| Adjudicator | PI | Resolves disagreements between primary and secondary. |

**Reviewer identity** is recorded by role (not name) in outcome records
to preserve protocol blinding. Training + inter-rater reliability
protocol (Section 11) must be complete before any session is labeled
for Paper 1 analysis.

## 10. Unknown / ambiguous handling

- **Log parsing failed**: `qsiprep_success = null`, no category. Route
  to primary reviewer.
- **Derivative file present but sanity check fails**:
  `qsiprep_success = false`, category `software_error` if the log is
  clean, otherwise the log-derived category.
- **QC reviewer unavailable**: `QC_STATUS = null`. Session excluded
  from QC-dependent secondary analyses but included in primary.
- **Configuration mismatch** (session run under a non-frozen
  configuration variant): `qsiprep_success = null`, sensitivity
  analysis only.

## 11. Inter-rater reliability protocol

**CONFIRMED** (2026-09-20). κ ≥ 0.80 threshold retained.

**Background**: Cohen's kappa (κ) measures how well two reviewers
agree on categorical labels, corrected for chance. κ = 1.0 is perfect
agreement; κ = 0.80 corresponds to "almost perfect" agreement on the
Landis & Koch scale and is the standard threshold in neuroimaging QC
publications. With 58/58 CIDUR sessions already PASS in the automated
QC system, achieving κ ≥ 0.80 is expected to be straightforward; the
exercise is methodologically required to make the labels defensible to
reviewers.

Before Paper 1 outcome labeling begins:

1. Primary and secondary reviewers **independently label a training
   set of 20 sessions** (10 randomly sampled from CIDUR PASS sessions
   + any available REVIEW/FAIL cases). Each reviewer uses the visual
   QC rubric (Section 12) without seeing the other's labels.
2. Compute Cohen's kappa on: `QSIPREP_SUCCESS` (binary) and
   `QC_STATUS` (ordinal: pass/review/fail). Failure-category and
   intervention-level kappas computed if any failure/major-intervention
   cases are present in the training set.
3. **κ ≥ 0.80** on both primary dimensions before proceeding.
4. If κ < 0.80, adjust rubric, retrain, repeat on a fresh 20-session
   sample. Document iterations.
5. Report the final kappa values in the manuscript.

## 12. Visual QC rubric

**Confirmed criteria** (2026-09-20). Reference screenshots from a
CIDUR pilot subset (10 sessions) to be added before freeze by the
primary reviewer.

Each session's QSIPrep HTML report (`qsiprep_single_run_output/sub-{id}.html`)
contains the following figures reviewed in order:

### 12.1 Preprocessed DWI quality (primary)

| Item | Pass | Review | Fail |
|---|---|---|---|
| **Motion** (eddy CNR map + confounds TSV) | CNR map visually uniform; no large blank slice bands | Scattered motion spikes in ≤10% of volumes; CNR patchy but continuous | Interleaved-slice dropout (checkerboard), CNR map with > 1 blank band, or > 20% volumes flagged |
| **Distortion residual** (along PE axis, AP direction) | No signal dropout in frontal lobes / temporal poles; sulci resolve normally | Mild anterior signal loss not obscuring cortex | Severe frontal dropout or spatial warping visible at brain boundary |
| **DWI↔T1 registration** (overlay figure in report) | Brain boundaries align; white matter visible through both | Minor misalignment (< 3 mm) at boundary | Gross misalignment or DWI outside T1 brain mask |

### 12.2 Brain mask quality (secondary)

| Item | Pass | Review | Fail |
|---|---|---|---|
| **Coverage** | Full cortex included; no hemisphere cut-off | Minor exclusion of occipital / temporal poles | Hemisphere or large cortical region excluded |
| **Non-brain exclusion** | No eyes, sinuses, or large non-brain regions included | Small orbital inclusion | Large non-brain regions included |

### 12.3 No-SDC sessions (GE, VECTA-DWI-014)

Sessions run with `--no-sdc` are rated on the same rubric. Mild
frontal dropout consistent with uncorrected susceptibility distortion
is expected and does **not** automatically downgrade to `fail` —
rate the actual image quality, not the absence of correction. The
`REVIEW_REQUIRED` Vecta readiness state captures the SDC constraint
independently of QC status.

### 12.4 Rating procedure

1. Open QSIPrep HTML report for the session.
2. Rate Preprocessed DWI (12.1) and Brain mask (12.2) independently.
3. Overall `QC_STATUS` = worst of the two:
   - Any `fail` → `fail`
   - Any `review`, no `fail` → `review`
   - All `pass` → `pass`
4. Record free-text note for any `review` or `fail` rating.
5. Reference screenshots (one per rating tier per item) to be added
   from the CIDUR pilot review session before freeze.

## 13. Frozen artifacts

At `vecta-dwi-v0.1.0-paper1` freeze, this manual is versioned and
tagged. Every field in the `ResearchOutcome` schema references this
document version. Later revisions do not retroactively change
Paper 1 labeling.

## 14. Explicit anti-patterns

**Never do these** during Paper 1 outcome labeling:

1. Inspect Vecta findings before labeling outcomes. Outcome labeling
   must be independent from the predictor set (Paper 1 §26).
2. Change the frozen configuration mid-labeling to make a session
   succeed. Re-labeling with a different configuration is a new
   version.
3. Fold retry / intervention information into the primary success
   label after the fact. `MANUAL_INTERVENTION_LEVEL` is a separate
   secondary outcome.
4. Assign a failure category based on QSIPrep exit code alone. Walk
   the taxonomy in precedence order.
5. Change kappa targets after seeing initial reliability results.

---

## Confirmation log

All seven pre-freeze items resolved 2026-09-20:

| Item | Resolution |
|---|---|
| QSIPrep version | `0.23.1.dev0+g634483f.d20240830` — confirmed from `dataset_description.json` |
| Filename patterns | Confirmed from actual `qsiprep_single_run_output/sub-001/ses-1/dwi/` output (Section 3) |
| `minor` allowlist | Four items confirmed; added `--no-sdc` / no-PED-inference as pre-registered variant (Section 5.1) |
| Reviewer roles | Primary: P.N. (DWI expert); Secondary/Adjudicator: PI (to co-confirm) (Section 9) |
| Kappa threshold | κ ≥ 0.80 confirmed; background explanation added to Section 11 |
| Visual QC rubric | Criteria derived from QSIPrep output structure + CIDUR data characteristics (Section 12); reference screenshots deferred to pilot review session |
| Paper 1 vs Paper 2 scope | Paper 1 = `QSIPREP_SUCCESS` + `PREPROC_DWI_AVAILABLE` only; QSIRecon/connectome/nodestrength = Paper 2 |

**One item pending before full freeze**: PI co-confirmation of reviewer roles (Section 9).

---

*Confirmed 2026-09-20. Encodes D7 + D8 recommendations. This document
is independent of the Vecta engine — it lives in `docs/` rather than
`specification/v0.1/` because outcome labeling is a research procedure
consumed at analysis time, not an engine input. All changes after
`vecta-dwi-v0.1.0-paper1` freeze require a protocol amendment.*
