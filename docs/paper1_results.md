# Paper 1 — Results (draft)

Working draft of the empirical results sections of the Paper 1 manuscript.
Covers the CIDUR internal-validation cohort only. TBI transport results
will be added as a separate section once that run completes.
Numeric claims reference `data/cidur_vecta_run/` outputs at commit `79c542b`.

---

## Study cohort and assessment completeness

The CIDUR dataset comprised 62 DWI sessions from 61 subjects (one subject,
sub-009, contributed two longitudinal sessions). Scanning was performed
across three scanner models at two field strengths: Siemens Skyra (n = 16
sessions), Siemens MAGNETOM Vida Fit (n = 12), and GE SIGNA Premier
(n = 33) at 3.0 T, and one GE SIGNA Artist session at 1.5 T (sub-002
ses-3; acquired at a PET/MR scanner). All sessions used a single-shell
protocol (b = 1000 s/mm²). Gradient table size varied by vendor: 67
directions for Siemens sessions, 53 for GE SIGNA Premier, and 51 for
the GE SIGNA Artist session.

Vecta-DWI assessed all 62 sessions to completion (assessment status
`completed` for all). Mean assessment completeness ratio was 0.911
(range 0.826–0.913 across sessions), with the lower value attributable
to the GE SIGNA Artist session where the absence of DWI DICOM series
prevented evaluation of VECTA-DWI-050 and VECTA-DWI-060. Assessment
runtimes varied 17–670 seconds per session; sessions with larger DICOM
archives (>5,000 instances) took proportionally longer due to header
parsing.

## Readiness distribution

Of 62 assessed sessions, 28 (45.2%) received a readiness state of
`ready` and 34 (54.8%) received `ready_with_limitations`. No session
received `not_ready`. The `ready` group consisted entirely of Siemens
sessions; the `ready_with_limitations` group consisted entirely of GE
sessions. This vendor-stratified split reflects a known, protocol-level
difference in reverse phase-encoding practice between the two scanner
platforms at this site (see Finding prevalence, below).

## Finding prevalence and criterion-level attribution

**Table 1** summarizes criterion evaluation results across the 62
assessed sessions.

| Criterion | Description | Triggered | Evaluated | Prevalence |
|---|---|---|---|---|
| VECTA-DWI-001 | Missing b=0 reference volume | 0 | 62 | 0% |
| VECTA-DWI-014 | Reverse PE acquisition unavailable | 34 | 62 | 54.8% |
| VECTA-DWI-021 | Field strength mismatch across sources | 0 | 62 | 0% |
| VECTA-DWI-030 | DWI volume count below protocol minimum | 0 | 62 | 0% |
| VECTA-DWI-040 | No DWI acquisition present (cohort integrity) | 0 | 62 | 0% |
| VECTA-DWI-050 | DICOM geometry inconsistency within session | 0 | 61 | 0% |
| VECTA-DWI-060 | DICOM/BIDS field-strength disagreement | 0 | 61 | 0% |

VECTA-DWI-014 was the sole triggered criterion, accounting for all 34
`ready_with_limitations` findings. It triggered for every GE session
(34/34, 100%) and for no Siemens session (0/28, 0%). All GE sessions
lacked a reverse-phase-encoding fieldmap acquisition — a known site-level
protocol difference confirmed in the BIDS conversion manifest and
corroborated by the absence of any `fmap/` entries targeting DWI runs for
GE subjects. This criterion fires at severity `major` and downgrades
readiness from `ready` to `ready_with_limitations` without blocking
assessment.

The DICOM Source module (VECTA-DWI-050 and VECTA-DWI-060) was evaluated
for 61 of 62 sessions; the single GE SIGNA Artist session contained no
DWI DICOM series (only localizer and planning series), so those criteria
were scored `not_applicable` for that session. Among the 61 evaluable
sessions, no DICOM geometry inconsistency and no DICOM/BIDS field-strength
disagreement was detected. All DICOM slice geometry, spacing, and
field-of-view parameters were internally consistent within each session's
DWI acquisition, and all DICOM-reported field strengths matched the
corresponding BIDS `FieldStrength` values.

## Vecta readiness state versus QSIPrep processing outcome

QSIPrep v0.23.1 (QSIPREP_VERSION_CIDUR) outcomes were available for
60 of the 62 Vecta-assessed sessions. The two sessions without QSIPrep
outcomes were sub-009 ses-1 and ses-2, both rated `ready` by Vecta —
these subjects appear to have been excluded from the pipeline run for
reasons not recorded in the QSIPrep output tree.

**Table 2** presents the joint distribution of Vecta readiness state
and QSIPrep success.

| Vecta readiness | QSIPREP_SUCCESS = True | QSIPREP_SUCCESS = False | No QSIPrep outcome | Total |
|---|---|---|---|---|
| ready | 26 | 0 | 2 | 28 |
| ready_with_limitations | 33 | 1 | 0 | 34 |
| **Total** | **59** | **1** | **2** | **62** |

Among the 26 `ready` sessions that were processed, all 26 produced valid
preprocessed DWI outputs (positive predictive value: 26/26, 100%). Among
the 34 `ready_with_limitations` sessions, 33 produced valid preprocessed
outputs and 1 did not (sub-076 ses-1; 97.1% processing success rate).
The single QSIPrep failure occurred in a session that Vecta had
pre-flagged with VECTA-DWI-014: a GE SIGNA Premier acquisition acquired
without a reverse-PE fieldmap for which distortion correction was not
applicable. QSIPrep confirmed this in its runtime log (`explicit no_sdc
→ NO SDC (legacy no-fieldmap GE runs)`) and produced no
`*_desc-preproc_dwi.nii.gz` output for that session. No `ready`
session failed QSIPrep processing.

## Notable individual cases

**sub-009 (ses-1 and ses-2).** Both sessions were assessed as `ready`
(Siemens Skyra, 3.0 T, 67 directions, reverse-PE fieldmap present). Neither
session appears in the QSIPrep output tree, indicating the subject was
not submitted to the pipeline despite meeting all readiness criteria.
This case illustrates a prospective application of Vecta: sessions
rated `ready` that were never processed represent a recoverable resource
in the study dataset and can be identified systematically without manual
chart review.

**sub-076 ses-1.** The only QSIPrep failure in the cohort. Vecta rated
this session `ready_with_limitations` on account of VECTA-DWI-014. The
session was a GE legacy acquisition without distortion-correction support;
QSIPrep produced anatomical derivatives but no preprocessed DWI output.
The Vecta finding correctly characterized the condition that caused
downstream failure.

**sub-044 ses-2.** QSIPrep produced only anatomical outputs for ses-2
of this subject (no DWI directory). However, the subject-level QC record
(`subject_qc.json`) reports QSIRecon, connectome, and node-strength as
PASS — these subject-level statuses reflect ses-1, for which full DWI
preprocessing succeeded. The inconsistency arises from the subject-level
granularity of the QC file, not from a Vecta misclassification; ses-2
was not assessed by Vecta (only ses-1 appeared in the session inventory).

---

*Draft as of 2026-09-21. TBI transport validation results to be appended
once that pipeline run completes. All numeric claims verified against
`data/cidur_vecta_run/` at commit `79c542b`.*
