# CIDUR BIDS Conversion Issues Manifest

**Status**: paper-ready draft — for Paper 1 §Results / §Discussion  
**Scope**: All real-world conversion problems encountered during CIDUR DICOM → BIDS  
**Date compiled**: 2026-09-20  
**Data**: 76 subjects, 82 assessed sessions, 62 DWI sessions (per `vecta aggregate`)  
**Source artifacts**: `CIDUR_BIDS/` tree — CSVs, `for_review/`, validation reports, traceability files

---

## 1. Overview

CIDUR data were acquired on two vendor platforms (Siemens Skyra / Vida Fit; GE SIGNA Premier / Artist)
at URMC over approximately three years. Converting the full cohort to BIDS-compliant format required
resolution of seven distinct issue classes, enumerated below. The issues are ordered by Vecta lifecycle
layer (L1 → L5) and cross-referenced to the criteria they motivate or are captured by.

**Summary counts (from `excluded_scans.csv`, `special_case_*.csv`, traceability files)**:

| Issue class | Affected sessions (est.) | Vecta criterion impacted |
|---|---|---|
| Missing PhaseEncodingDirection (inference required) | 18/62 DWI (29%) | VECTA-DWI-001 |
| Missing reverse-PE EPI (GE protocol) | ~20 sessions | VECTA-DWI-014 |
| Run-vs-session ambiguity | 2 subjects multi-session confusion | cohort integrity |
| Non-standard DWI naming → direction-count inference | ~15 sessions | VECTA-DWI-030 (proximate) |
| Scanner-emitted derived DWI series (FA, ADC, TraceW) | 499 files excluded | L2_SOURCE integrity |
| dcm2niix unexpected extra output | 5 subjects | L3_METADATA |
| Scanner malfunction / corrupt volumes | 2 subjects | L2_SOURCE, VECTA-DWI-050 |
| fmap IntendedFor absent, manually populated | 17 fmaps | VECTA-DWI-014 |
| Session scope confusion (fMRI vs structural/DWI) | 2 subjects | VECTA-DWI-040 |

---

## 2. Issue Class 1 — Missing Phase Encoding Direction (PED)

**What happened**: BIDS requires `PhaseEncodingDirection` in the DWI JSON sidecar for susceptibility
distortion correction workflows. Siemens scanners emit `PhaseEncodingAxis` (an unsigned axis: `j` or
`i`) rather than the signed BIDS form (`j` = A→P, `j-` = P→A). GE scanners sometimes emit the signed
form directly, sometimes omit it entirely.

**Evidence**: `dwi_phase_encoding_traceability.csv` (39 sessions, 39 DWI files):
- 21/39 (54%) used `PhaseEncodingDirection` (already signed — mainly GE or late Siemens firmware)
- 18/39 (46%) had only `PhaseEncodingAxis` — required manual inference from acquisition name

**Manual inference rule applied** (`PHASE_ENCODING_TRACEABILITY.md §3`):  
When `PhaseEncodingDirection` was absent, direction was inferred from the BIDS filename entity:
- `dir-ap` in filename → `PhaseEncodingDirection: "j-"` (Anterior → Posterior)
- `dir-pa` in filename → `PhaseEncodingDirection: "j"` (Posterior → Anterior)

All 39 audited files reached `Axis_Match_Status = MATCH` (DICOM metadata cross-checked). However,
the axis-only case requires filename conventions to be authoritative — a convention that is:
- Not enforced by dcm2niix
- Not validated by the BIDS validator (it only checks format, not semantic correctness)
- Dependent on a site-specific naming convention established during protocol design

**Vecta impact**:
- VECTA-DWI-001 (PE direction unknown): 0 sessions triggered in final BIDS tree — because the manual
  inference succeeded. Without the traceability audit, these sessions would have appeared to have valid
  PE direction but with unverifiable provenance.
- `VECTA.DWI.SCANNER.MANUFACTURER` captures Siemens vs GE distinctions, making vendor-specific PED
  behavior a reportable variable.
- The `VECTA.DWI.ACQUISITION.PE_DIRECTION` variable documents the state as `observed` — it does not
  distinguish direct DICOM extraction from filename inference. This is a known L3 provenance gap.

**Paper 1 framing**: This is the canonical example of the "L1 → L4 traceability gap" introduced by
vendor-specific metadata conventions. A directly observed (L2) PED value has higher integrity than one
inferred (L3/L4) from filename conventions. Vecta's 8-state vocabulary does not yet distinguish these
sub-states; a future version could introduce `inferred` or `transcribed` states.

---

## 3. Issue Class 2 — Missing Reverse-PE EPI (No Fieldmap Available)

**What happened**: The 64-direction Siemens Skyra protocol included a paired reverse-PE EPI in `fmap/`
(`dir-pa_epi`). The GE 50-direction protocol (`acq-multidirax`) did not include a paired EPI at all.

**GE sessions without any reverse-PE**: GE subjects acquired on SIGNA Premier or Artist ran a 50-dir
protocol without a paired PA acquisition. The fmap directory for these subjects either does not exist
or contains only a GRE fieldmap (magnitude/phasediff), which is excluded by BIDS-for-QSIPrep rules.

**Affected subset identified by**: comparing `converted_scans.csv` (Modality=fmap: 17 fmaps total,
all associated with Siemens subjects) against GE DWI subjects with no fmap entry.

**Vecta impact**: VECTA-DWI-014 (`complementary_pe_reference_unavailable`) fires for these sessions.
In the CIDUR Vecta run, 1 subject (sub-076, ses-1, GE SIGNA Premier) was flagged. Additional subjects
whose sessions had only a 50-dir GE acquisition would similarly fire VECTA-DWI-014.

**fmap IntendedFor gap**: For the 17 Siemens subjects that did have a reverse-PE fmap,
`IntendedFor` had to be manually populated via `fill_fmap_intended_for.py`. The BIDS validator's
`INCONSISTENT_SUBJECTS` warning (554 files across the cohort) partially reflects this asymmetry —
some subjects have fmap files others do not.

**Paper 1 framing**: This directly validates the original motivation for VECTA-DWI-014 and
demonstrates the "intended-use conditional" nature of DBI. A session is perfectly valid for many
analyses but scores `review_required` for structural connectomics because distortion correction is
constrained. The GE/Siemens difference is not a data quality failure — it is a protocol design
decision that constrains downstream options.

---

## 4. Issue Class 3 — Run vs Session Ambiguity

**What happened**: CIDUR includes subjects with multiple scanning dates. Two naming conventions were
used ambiguously:
- Some repeated scans (within a single study visit) were labeled as additional sessions (`ses-2`,
  `ses-3`) when they should have been labeled as runs within the same session.
- The reverse was also observed: what appeared to be a new visit was cataloged as a second run of
  the same session, requiring manual reclassification.

**Evidence from artifacts**:
- `session_key_potentially_affected.csv` (78 rows): all 78 subjects had at least one blank StudyDate
  in their DICOM header (the `has_blank_study_date: True` field). With no StudyDate, automated
  session assignment is impossible without cross-referencing StudyInstanceUID or StudyTime.
- Subjects have 0 unique study dates (blank only) — session assignment relied entirely on
  StudyInstanceUID and manual chart review.
- Sub-018 ses-1: removed from BIDS because it was a functional MRI session, not structural/DWI
  (see `special_case_actions.csv`). This session had valid DWI files that were removed.
- Sub-036 ses-2: similarly removed as an fMRI session.

**Vecta impact**: VECTA-DWI-040 (session_has_no_dwi) would have fired for the functional sessions
had they been left in the BIDS tree. The manual removal prevented this but the issue illustrates that
"session has no DWI" can arise from both missing acquisition and from scope errors in BIDS curation.

**Paper 1 framing**: BIDS's session/run distinction is semantically underspecified for longitudinal
neuroimaging studies. A single scanner visit with two DWI acquisitions (e.g., an aborted and a
re-acquired scan) could legitimately be labeled either as two runs or two sessions — and the choice
has downstream consequences for QSIPrep (which processes sessions independently). Vecta cannot resolve
this ambiguity but can flag session-level cohort integrity conditions. The blank StudyDate issue is
a separate L2_SOURCE provenance concern.

---

## 5. Issue Class 4 — Inconsistent DWI Protocol Naming and Direction-Count Inference

**What happened**: Across vendors and even within Siemens, the DWI series description was inconsistent:

| Series description found | Direction count | Vendor | Notes |
|---|---|---|---|
| `AX DTI AP-64 DIRECTIONS` | 64 | Siemens Skyra | Standard protocol |
| `AX DTI PA-64 DIRECTIONS` | 64 (reverse-PE EPI) | Siemens Skyra | Treated as fmap |
| `Ax DTI 50directions` | 50 | GE SIGNA Premier | No PA counterpart |
| `Ax DTI 50 DIRECTIONS` | 50 | GE Artist | No PA counterpart |
| `AX DTI LONG` | ~50 | GE SIGNA Premier | sub-002 ses-1 |
| `Ax DTI` | ? | GE | sub-002 ses-1, no standard naming |

Series with `dir_count=None` (no numeric count in name) or unexpected counts (12, 24, 30, 64) were
moved to `for_review/special_cases_vendor/` via `postprocess_vendor_dwi_fmap_rules.py`:
- GE, 30 directions: 6 subjects → review (not enough directions for standard connectomics)
- GE, 12 directions: 1 subject → review
- Siemens, 24 directions: 2 subjects → review (sub-042, sub-069 — non-standard Siemens protocol)
- Siemens, 64 directions, no phase label: 1 subject → review (sub-036)
- Siemens fmap, phase=pa: 13 fmaps → review (protocol variant without explicit IntendedFor)

The direction count was inferred from the series description string — not from the bval file — because
at the time of conversion the NIfTI and bval/bvec had not yet been generated. This is a
bootstrapping problem: the BIDS filename needs to encode the direction count (`acq-64dirax`) before
bvals exist to confirm it.

**Vecta impact**:
- `VECTA.DWI.ACQUISITION.SHELL_COUNT` (derived from bval file post-conversion) can confirm or
  contradict the acquisition label inferred during naming.
- `VECTA.DWI.ACQUISITION.BVAL_COUNT` and `VOLUME_COUNT` directly measure what was acquired.
- VECTA-DWI-030 fires when bval/bvec are missing outright — but not when the count is simply
  different from expected. A future criterion could check protocol conformance explicitly.

**Paper 1 framing**: This is a concrete example of L3 metadata dependency on L1 acquisition naming
conventions. The absence of a mandatory "DWI direction count" field in DICOM forces sites to encode
this in free-text series descriptions, creating fragile parsing chains. Vecta directly addresses this
by extracting `SHELL_COUNT` from the bval file (ground truth) rather than from the series name.

---

## 6. Issue Class 5 — Scanner-Emitted Derived DWI Series

**What happened**: Siemens and GE scanners automatically emit post-processed DWI derivatives alongside
the raw diffusion-weighted volumes. These appear in DICOM as separate series with their own
SeriesDescription values:
- `AX DTI AP-64 DIRECTIONS_FA` (fractional anisotropy map)
- `AX DTI AP-64 DIRECTIONS_ADC` (apparent diffusion coefficient map)
- `AX DTI AP-64 DIRECTIONS_TRACEW` (trace-weighted image)
- `FA_b1000`, `Trace_b1000` (GE equivalents)

**Scale**: 499 of 1,181 excluded files (42%) were excluded under the reason
`"Derived/processed data - not raw"`. This is the single largest exclusion category.

**Detection method**: Automated rule applied during `postprocess_vendor_dwi_fmap_rules.py` based on
series description substring matching (`_FA`, `_ADC`, `_TRACEW`, `FA_b`, `Trace_b`).

**Vecta impact**:
- VECTA-DWI-050 (DWI DICOM geometry inconsistent): scanner-derived series can have different geometry
  (e.g., FA maps are often 2D, ADC maps may differ in slice count) — including them would trigger
  false geometry inconsistency alerts.
- The `DicomInventory.classify_series()` method in `src/vecta/collectors/dicom.py` uses similar
  substring rules to flag these as `derived` class, separate from primary `dwi` series.

**Paper 1 framing**: Scanner-derived derivatives are a well-known L2_SOURCE integrity risk. If
accidentally included in BIDS diffusion data, downstream pipelines (dcm2niix, QSIPrep) may produce
corrupted or incorrect outputs. Vecta's DICOM Source module addresses this through geometry consistency
checking (VECTA-DWI-050) and series-count auditing, but requires DICOM access — which is the
optional module activated with `--dicom`.

---

## 7. Issue Class 6 — dcm2niix Unexpected Extra Output

**What happened**: For five subjects, dcm2niix emitted unexpected auxiliary files alongside the
primary NIfTI output:

| Subject | Session | Unexpected files | Cause |
|---|---|---|---|
| sub-002 | ses-1 | `*_e2_phMag.json`, `*_e2_phMag.nii.gz` | GE multi-echo phase magnitude |
| sub-002 | ses-3 | `*FLAIRa.nii.gz`, `*FLAIRa.json` | Alternative FLAIR reconstruction |
| sub-009 | ses-2 | `*T1wb*.nii.gz` ×5 | T1 with multiple ROI overlays |
| sub-019 | ses-1 | `*T1wa.nii.gz`, `*T1wa.json` | Alternative T1 reconstruction |
| sub-065 | ses-2 | `*_e2_phMag.nii.gz`, `*_e2_phMag.json` | GE multi-echo phase magnitude |

Sub-002 (ses-1) and sub-065 (ses-2) dcm2niix emitted phase-magnitude maps from a multi-echo GE
sequence. These are not interpretable as standard BIDS DWI files and were moved to `for_review/`.

**Vecta impact**: dcm2niix's output proliferation is an L3_METADATA issue — the converted file
set does not match what the BIDS specification expects for a given modality. If these extra files are
left in place, the BIDS validator emits `INCONSISTENT_SUBJECTS` warnings (files present for some
subjects but not others). Vecta's `extract_validator_error_count` and `extract_validator_warning_count`
capture the net effect in the final BIDS tree.

**Paper 1 framing**: Converter behavior (dcm2niix version, parameter settings) is a source of L3
variability that Vecta currently does not version-stamp in its evidence. The `provenance` block records
Vecta software and spec versions but not the converter version used during BIDS generation. This is
flagged as a known limitation.

---

## 8. Issue Class 7 — Scanner Malfunction / Corrupt Volumes

**What happened**: Two subjects had corrupt DWI DICOM files:
- **sub-016 ses-3**: dcm2niix produced a 1D output of 315 slices (expected a 4D volume). Scanner
  malfunction recorded as exclusion reason: `"CORRUPT - Scanner malfunction: 315 slices in 1D (expected 4D volume)"`.
- **sub-047 ses-?**: 4,689 slices in 1D — acquisition aborted mid-scan or scanner fault.

Both were moved to `for_review/corrupt_scans/` and are not in the final BIDS tree.

**Additional for_review/corrupt_scans subjects**: sub-002, sub-009, sub-018, sub-019, sub-047, sub-065
are present in `corrupt_scans/` (6 subjects total across 7 sessions, including the two malfunction
cases and cases where dcm2niix extra-output was co-occurring).

**Vecta impact**: VECTA-DWI-050 (DWI DICOM geometry inconsistent) would have fired for these sessions
if their DICOM had been processed. Sub-047 (distorted DWI) is explicitly noted in `excluded_scans.csv`
with reason `"sub-047 rule: exclude distorted DWI"`. VECTA-DWI-040 (no DWI in session) would not
fire because these are absent from BIDS entirely.

**Paper 1 framing**: Scanner malfunction represents an L1_ACQUISITION failure — data integrity was
lost at source, not during conversion. Vecta's Source module (with DICOM access) can detect geometric
inconsistency signs earlier in the pipeline, but once a corrupt DICOM is excluded from BIDS, Vecta
assesses the BIDS state (no DWI present) rather than the DICOM root cause.

---

## 9. Issue Class 8 — fmap IntendedFor Manually Populated

**What happened**: dcm2niix does not populate `IntendedFor` in fmap JSON sidecars. BIDS requires
`IntendedFor` for the fmap to be associated with a DWI acquisition by QSIPrep. For all 17 Siemens
subjects with a reverse-PE EPI, `IntendedFor` was added post-conversion using
`fill_fmap_intended_for.py` with the following mapping logic:
- The PA EPI filename's `acq-` entity was matched to the corresponding AP DWI acquisition.
- `IntendedFor` was set to `ses-{N}/dwi/{subject}_{session}_{acq}_dwi.nii.gz`

**fmap_intendedfor.csv** records all 17 entries with `Targets_Exist: True` (verified that the target
DWI file exists in the BIDS tree).

**Vecta impact**: The original Vecta engine only checked sibling DWI entities for reverse-PE. This was
fixed in Commit H (fmap IntendedFor support) after discovering that all CIDUR reverse-PE references
live in `fmap/` with `IntendedFor`, not as sibling DWI acquisitions. Without this fix, 100% of
CIDUR sessions with valid reverse-PE would have fired VECTA-DWI-014 (false positive).

**Paper 1 framing**: This was the most consequential bug discovered during CIDUR validation. It
demonstrates that the "fmap as reverse-PE reference" pattern — common in practice — was not covered
by the initial Vecta specification. The fix required extending both the BIDS collector and the
reverse-PE derivation logic. This is documented as a specification-level correction (not just
implementation) and motivates the need for real-data validation before freezing v0.1.

---

## 10. BIDS Validator Output Summary

**File**: `validation_report_data_bids.json` (bids-validator v1, run on final `data_bids/` tree)

**Errors**: 0  
**Warnings**: 3 types

| Warning key | Code | Affected files | Cause |
|---|---|---|---|
| `INCONSISTENT_SUBJECTS` | 38 | 554+ files | Multi-protocol cohort (GE vs Siemens differ in fmap/DWI file sets) |
| `INCONSISTENT_PARAMETERS` | 39 | 200+ files | Protocol variation within acquisiton type (slice counts, resolution) |
| `MISSING_SESSION` | 97 | 148+ files | Not all subjects have all sessions (expected in longitudinal cohort) |

All three warning types are **expected and acceptable** for a multi-site, longitudinal, multi-vendor
cohort. The zero-error result indicates structural BIDS compliance.

**`INCONSISTENT_SUBJECTS` detail**: The 50-direction GE sessions have no fmap (no PA EPI); Siemens
sessions do. This creates systematic "missing file" warnings where the validator expects all subjects
to have the same files. This warning does not indicate a data problem — it reflects an intentional
protocol difference between vendors.

**`INCONSISTENT_PARAMETERS` detail**: DWI volumes show different slice counts (68 vs 70 vs 76) and
different TR values (4.2s vs 4.3s vs 4.7s). These correspond to the same 64-direction Siemens
protocol run at slightly different parameter settings across scanner firmware updates or as
site-protocol evolved over the study period. The voxel sizes are consistent (2.0mm isotropic).

---

## 11. Mapping to Vecta Criteria and Proposed New Criteria

The following table maps each issue class to its Vecta capture status:

| Issue | Vecta criterion | Status | Captured? |
|---|---|---|---|
| Missing PED (unsigned axis only) | VECTA-DWI-001 | Fires when PED absent from JSON | Partial: doesn't distinguish direct vs inferred |
| Missing reverse-PE EPI | VECTA-DWI-014 | Fires when no reverse-PE found | Yes |
| Run/session ambiguity | VECTA-DWI-040 | Fires when DWI absent | Partial: flags result, not cause |
| Direction-count mismatch | (none) | Not covered in v0.1 | **Gap → proposed VECTA-DWI-070** |
| Scanner-derived series | VECTA-DWI-050 | Fires on geometry inconsistency | Partial: requires DICOM access |
| dcm2niix extra output | (none) | Validator warning count only | Partial |
| Scanner malfunction | VECTA-DWI-050 | Fires on geometry inconsistency | Partial: requires DICOM access |
| fmap IntendedFor absent | VECTA-DWI-014 | Engine updated (Commit H) | Yes, after fix |
| fMRI session in DWI cohort | VECTA-DWI-040 | Fires: no DWI in session | Yes |

**Proposed VECTA-DWI-070 (for v0.2)**: Protocol-conformance mismatch. Fires when the inferred
direction count from the acquisition label (`acq-Ndir`) does not match the actual volume count
extracted from the NIfTI (`VECTA.DWI.ACQUISITION.VOLUME_COUNT`). This would have caught the
24-direction and 30-direction variants that were excluded during conversion.

---

## 12. What Is Usable for Paper 1

Each of the eight issue classes above provides concrete evidence for Paper 1's claims:

1. **L1 → L3 traceability gap** (Issues 1, 4): Vendor-specific conventions force inference where
   direct extraction is impossible. Vecta's 8-state vocabulary captures the outcome but not the
   method — a known limitation that motivates future `inferred` states.

2. **Intended-use conditional readiness** (Issue 2): GE vs Siemens protocol differences manifest
   as different readiness states for the same downstream use. This directly validates the profile-
   relative design of DBI.

3. **L2 source integrity** (Issues 5, 7): Scanner-emitted derivatives and malfunction-corrupted
   volumes cannot be detected from BIDS alone; DICOM source access is required. This is the
   primary argument for Vecta's optional Source module (VECTA-DWI-050, VECTA-DWI-060).

4. **Converter as integrity actor** (Issues 3, 6, 8): dcm2niix's behavior (extra output, missing
   IntendedFor) creates L3 integrity concerns that propagate forward. The converter version should
   be recorded in Vecta provenance — currently a gap.

5. **Validator warnings as incomplete evidence** (Issue 10): Zero BIDS errors is necessary but not
   sufficient for processing readiness. The three warning types are cohort-structural, not DWI-
   quality failures. Vecta's criterion-level assessment goes beyond the validator's binary pass/fail.

6. **Real-data-driven spec correction** (Issue 8 — fmap IntendedFor): The most important finding.
   Running Vecta on CIDUR data before freezing v0.1 caught a systematic false positive that would
   have classified 100% of Siemens reverse-PE sessions as REVIEW_REQUIRED. This validates the
   "validate spec on real data before tagging" methodology recommended in the build plan.
