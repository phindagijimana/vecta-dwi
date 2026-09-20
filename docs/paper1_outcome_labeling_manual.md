# Paper 1 — Outcome labeling manual (draft)

**Status**: DRAFT — encodes the D7 and D8 recommendations from the
2026-09-19 decision review. Not yet confirmed. Must be reviewed and
adjusted by the DWI pipeline expert + data engineer + biostatistician
before `vecta-dwi-v0.1.0-paper1` freeze.

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

To be pinned at freeze time. Configuration hash is stored in the
`Provenance` object of every `ResearchOutcome` record. Configuration
includes at minimum:

- QSIPrep version (specific x.y.z, not `latest`).
- Container digest (Apptainer / Singularity SIF sha256).
- Command-line invocation template (arguments + argument order).
- Reconstruction workflow selection (`--recon-spec`).
- Freesurfer input handling (with / without pre-existing FS output).
- Output resource limits (CPU, memory, wall time).

**Any change to this configuration is a new version.** Sessions run
under different configurations must be labeled with the configuration
they were actually run under; they cannot be pooled.

## 3. Required derivatives

The following files must exist and pass structural sanity checks for
`qsiprep_success = true`:

| Derivative | Structural sanity check |
|---|---|
| `sub-*_ses-*_dir-*_space-T1w_desc-preproc_dwi.nii.gz` | NIfTI is readable; 4D; volume count matches paired `.bval` line count |
| `sub-*_ses-*_dir-*_space-T1w_desc-preproc_dwi.bval` | Whitespace-parseable numeric list; length matches NIfTI dim[4] |
| `sub-*_ses-*_dir-*_space-T1w_desc-preproc_dwi.bvec` | Three whitespace-parseable rows of equal length; length matches `.bval` |
| `sub-*_ses-*_dir-*_space-T1w_desc-brain_mask.nii.gz` | NIfTI is readable; 3D; ≥ 1000 non-zero voxels |
| `sub-*_ses-*_desc-preproc_dwiref.nii.gz` | NIfTI is readable; 3D |

**Exact filename patterns to be finalized against the frozen QSIPrep
version's output layout.**

If reconstruction is included in the Paper 1 pipeline (QSIRecon),
additional required derivatives are listed as **secondary**:

| Derivative | Secondary outcome |
|---|---|
| Connectome matrix (per selected atlas) | `qsirecon_connectome_available = true` |
| Tractogram | `qsirecon_tractogram_available = true` |

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

Only these actions may be classified as `minor`. Anything else is
`major`.

1. **Rerun same configuration** after an infrastructure-only failure
   (Section 4 category 1) with no other change.
2. **Fresh Freesurfer input** substitution when the initial FS output
   was infrastructure-corrupted, using a rerun of the same FS
   configuration (not a different FS version).
3. **Wall-time / memory bump** within the pre-registered range
   (defined per site at freeze) for sessions that ran to a partial
   result and would clearly complete with more resources.

**Not allowed as `minor`**: any change to acquisition-metadata
handling; any change to `--recon-spec`; any change to distortion-
correction strategy; any manual file edit or reassociation.

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

| Role | Responsibility |
|---|---|
| Automated labeler | Runs QSIPrep log parser + derivative sanity checks. Emits candidate label for every session. |
| Primary reviewer (DWI expert) | Confirms or overrides automated label. Assigns intervention level. Records QC status. |
| Secondary reviewer (independent DWI expert) | Reviews all sessions labeled `review` or `fail`, and a 10% random sample of `pass`. |
| Adjudicator (senior DWI expert) | Resolves disagreements between primary and secondary reviewers. |

**Reviewer identity** recorded by role, not name / initials, in the
outcome record. Reviewer training + inter-rater reliability protocol
(Section 10) must be complete before any session is labeled for
Paper 1 analysis.

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

Before Paper 1 outcome labeling begins:

1. Primary and secondary reviewers **independently label a training
   set of 20 sessions** spanning `pass` / `review` / `fail` / all
   failure categories.
2. Compute Cohen's kappa on: `qsiprep_success` (binary), failure
   category (categorical), intervention level (ordinal),
   `QC_STATUS` (ordinal).
3. **Kappa ≥ 0.80** on all four dimensions before proceeding.
4. If kappa < 0.80 on any dimension, adjust rubric, retrain, repeat
   on a fresh 20-session sample. Document iterations.
5. Report the final kappa values in the manuscript.

## 12. Visual QC rubric

**TODO before freeze**. Placeholder outline:

- Preprocessed DWI: check for residual motion artifacts (interleaved
  slice mismatch, ghosting), distortion residuals along PE axis
  (frontal / temporal signal dropout, spatial warping), registration
  quality (DWI ↔ T1 boundary alignment).
- Brain mask: check for exclusion of non-brain tissue, inclusion of
  full cortex.
- Rate each on `pass` / `review` / `fail`.
- Reference screenshots for each rating to be produced from CIDUR
  pilot review.

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

## Immediate items requiring user confirmation

Before this document is frozen:

- [ ] Confirm QSIPrep version + container digest (Section 2).
- [ ] Freeze the required-derivative filename patterns against that
  QSIPrep version (Section 3).
- [ ] Confirm the `minor` allowlist (Section 5.1) — three items only,
  or expand?
- [ ] Confirm reviewer roles + who fills each (Section 9).
- [ ] Confirm kappa threshold (Section 11 uses ≥ 0.80).
- [ ] Author the visual QC rubric with reference screenshots
  (Section 12) — requires a CIDUR pilot subset first.
- [ ] Confirm which QSIRecon derivatives are Paper 1 outcomes vs
  Paper 2 outcomes (Section 3).

---

*Draft as of 2026-09-19. Encodes D7 + D8 recommendations. Must not be
frozen until above confirmation items are resolved. This document is
independent of the Vecta engine — it lives in `docs/` rather than
`specification/v0.1/` because outcome labeling is a research procedure
consumed by Vecta at analysis time, not an engine input.*
