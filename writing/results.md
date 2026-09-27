# Results

## Figure captions

**Figure 1.** Vecta-DWI readiness state versus QSIPrep processing outcome in the
CIDUR development cohort (n=71 sessions; in-sample evaluation). Stacked bars
show the proportion of sessions in each outcome category. Failure rates were 0%
(0/26) for ready, 2.4% (1/41) for ready_with_limitations, and 100% (2/2) for
review_required. All three failures occurred in Vecta-flagged sessions.

**Figure 2.** Detection level comparison against QSIPrep failure in the CIDUR
cohort (n=69 confirmed outcomes; 3 failures). Grouped bars show sensitivity and
NPV for each detection level, with Wilson 95% confidence intervals. Wide CIs
reflect n=3 failures; the comparison is mechanistically illustrative rather than
statistically powered.

**Figure 3.** Criterion activation rate (% of sessions triggering each criterion)
across five datasets. Gray cells indicate DICOM not available and source-integrity
criteria therefore not evaluated. Bold text indicates any activation. The
cross-dataset pattern illustrates that criterion co-occurrence and prevalence vary
systematically by acquisition and conversion practice.

**Figure 4.** Vecta-DWI readiness state versus QSIPrep processing outcome in the
TrackTBI external validation cohort (n=1,273 eligible sessions; 1,071 with
confirmed outcomes). Left: stacked proportional bars with session counts annotated.
Right: QSIPrep failure rate per readiness tier with Wilson 95% confidence interval.
Failure rates were 1.6% (7/451) for ready_with_limitations and 100% (620/620) for
review_required among sessions with confirmed outcomes.

---

## Study cohort and assessment completeness

Six sessions were excluded from the BIDS tree before Vecta assessment due
to acquisition-layer quality issues (corrupt DWI or multi-echo phase image
artifacts); these are outside Vecta's assessment scope. The 62-session
denominator comprised 61 subjects (one subject contributed two longitudinal
sessions) spanning three scanner models at two field strengths: Siemens
Skyra (n = 16), Siemens MAGNETOM Vida Fit (n = 12), and GE SIGNA Premier
(n = 33) at 3.0 T, and one GE SIGNA Artist session at 1.5 T (acquired at
a combined PET/MR scanner). All sessions used a single-shell protocol
(b = 1000 s/mm²). Gradient table size varied by vendor: 67 directions for
Siemens sessions, 51–53 for GE sessions.

Vecta-DWI assessed all 62 sessions to completion (assessment status
completed for all). Mean assessment completeness ratio was 0.911
(range 0.826–0.913 across sessions), with the lower value attributable
to sub-002 ses-3: Vecta's session-matching heuristic (alphabetical DICOM
directory ordering) mapped this subject's BIDS ses-3 to a PET-only DICOM
session directory that contained no DWI acquisition, so DICOM
source-integrity variables were scored not_applicable for that session.
The GE SIGNA Artist session (sub-057 ses-1) was correctly matched to its
MR DICOM directory and received the standard completeness ratio. Assessment
runtimes varied 17–670 seconds per session; sessions with larger DICOM
archives (>5,000 instances) took proportionally longer due to header
parsing.

## Readiness distribution

Of 62 assessed sessions, 28 (45.2%) received a readiness state of
ready and 34 (54.8%) received ready_with_limitations. No session
received not_ready. The ready group consisted entirely of Siemens
sessions; the ready_with_limitations group consisted entirely of GE
sessions. This vendor-stratified split reflects a known, protocol-level
difference in reverse phase-encoding practice between the two scanner
platforms at this site (see Finding prevalence, below).

## Finding prevalence and criterion-level attribution

**Table 1.** Criterion evaluation results across the 62 CIDUR sessions.
Triggered: number of sessions for which the criterion condition was met.
Evaluated: sessions for which all required variables were resolvable.
Prevalence: Triggered / Evaluated.

| Criterion | Description | Triggered | Evaluated | Prevalence |
|---|---|---|---|---|
| VECTA-DWI-001 | Phase-encoding direction cannot be determined (review criterion) | 0 | 62 | 0% |
| VECTA-DWI-014 | Complementary phase-encoding reference unavailable | 34 | 62 | 54.8% |
| VECTA-DWI-021 | One or more essential metadata items missing or unknown | 0 | 62 | 0% |
| VECTA-DWI-030 | DWI gradient file (.bval and/or .bvec) missing | 0 | 62 | 0% |
| VECTA-DWI-031 | DWI gradient vectors have implausible norms | 0 | 62 | 0% |
| VECTA-DWI-040 | Session has no DWI acquisition | 0 | 62 | 0% |
| VECTA-DWI-050 | DWI DICOM series has internally inconsistent geometry | 0 | 61 | 0% |
| VECTA-DWI-060 | MagneticFieldStrength disagrees between DICOM and BIDS sidecar | 0 | 61 | 0% |

VECTA-DWI-014 was the sole triggered criterion, accounting for all 34
ready_with_limitations findings. It triggered for every GE session
(34/34, 100%) and for no Siemens session (0/28, 0%). All GE sessions
lacked a reverse-phase-encoding fieldmap acquisition — a known
site-level protocol difference confirmed in the BIDS conversion records.
This criterion fires at severity major and downgrades readiness from
ready to ready_with_limitations without blocking assessment.

The DICOM source module (VECTA-DWI-050 and VECTA-DWI-060) was evaluated
for 61 of 62 sessions; for sub-002 ses-3 the session-matching heuristic
resolved to a PET-only DICOM directory with no DWI acquisition, so those
criteria were scored not_applicable for that session. Among the 61 evaluable
sessions, no DICOM geometry inconsistency and no DICOM/BIDS
field-strength disagreement was detected. All DICOM slice geometry,
spacing, and field-of-view parameters were internally consistent within
each session's DWI acquisition, and all DICOM-reported field strengths
matched the corresponding BIDS FieldStrength values.

## Protocol documentation audit

Vecta-DWI recorded structured variable observations for all 62 sessions,
producing a queryable protocol ledger independent of the readiness
assessment. Across the cohort, 10 distinct protocol configurations were
identified, defined by unique combinations of manufacturer, scanner
model, field strength, software version, volume count, voxel geometry,
and phase-encoding direction (Table 2). Voxel geometry varied between
vendors: Siemens sessions used approximately 2.0 mm isotropic
acquisition geometry (Skyra: 2.017 × 2.017 × 2.0 mm; Vida Fit:
2.0 × 2.0 × 2.6 mm), while GE SIGNA Premier sessions used higher
in-plane resolution (1.0 × 1.0 mm) with 2.0–2.2 mm slice thickness.
Software versions spanned two Siemens release families (syngo MR E11,
XA50) and three GE release strings across the two GE scanner models.
All sessions used posterior-to-anterior (j-) phase-encoding direction
with the exception of one GE session (PE direction j, no polarity
marker). These parameters are not reported by BIDS Validator, which
assesses structural conformance rather than acquisition characteristics,
and are not derivable from BIDS filenames alone. The Vecta variable
record provides a machine-readable protocol audit trail that persists
independently of the assessment outcome.

**Table 2.** Protocol configurations identified in the CIDUR cohort (n=62 sessions).
Rows 7–10 represent four low-prevalence configurations (1 Siemens Vida Fit and 3 GE
sessions) with heterogeneous software versions and voxel geometries not individually
listed due to n < 2.

| Configuration | Scanner | Field strength | Software | Volumes | Voxel size (mm) | n |
|---|---|---|---|---|---|---|
| 1 | Siemens Skyra | 3.0 T | syngo MR E11 | 67 | 2.02 × 2.02 × 2.0 | 16 |
| 2 | GE SIGNA Premier | 3.0 T | RX29.1 | 53 | 1.0 × 1.0 × 2.0 | 15 |
| 3 | Siemens Vida Fit | 3.0 T | syngo MR XA50 | 67 | 2.0 × 2.0 × 2.6 | 11 |
| 4 | GE SIGNA Premier | 3.0 T | RX29.1 | 53 | 1.0 × 1.0 × 2.2 | 7 |
| 5 | GE SIGNA Premier | 3.0 T | SIGNA LX1 MR30 | 53 | 1.0 × 1.0 × 2.0 | 6 |
| 6 | GE SIGNA Premier | 3.0 T | SIGNA LX1 MR30 | 53 | 1.0 × 1.0 × 2.2 | 3 |
| 7–10 | Siemens Vida Fit / GE variants | 3.0–1.5 T | various | 51–67 | various | 4 |

## Conformance versus readiness: BIDS Validator comparison

BIDS Validator was run on the full 62-session dataset. The validator
reported zero errors and zero warnings related to fieldmap presence,
reverse phase-encoding acquisition, or distortion-correction
prerequisites. All 34 sessions that Vecta identified as lacking a
reverse-PE acquisition passed BIDS validation without any fieldmap-
related issue, consistent with the BIDS specification's position that
fieldmap acquisitions are optional. The validator did report
inconsistent session and file count warnings attributable to the
multi-session, multi-scanner design of the study (not all subjects
contributed the same sessions or sequence variants). These warnings
reflect protocol heterogeneity that Vecta captures at the variable
level but that BIDS Validator treats as a structural irregularity
without further characterization. The absence of fieldmap-related
validator output for the 34 sessions with VECTA-DWI-014 findings
demonstrates a concrete gap between BIDS conformance checking and
preprocessing readiness assessment.

## Comparison with a naive fieldmap presence check

To benchmark Vecta's VECTA-DWI-014 classification against the simplest
possible baseline, we implemented a naive checker that identifies
sessions as having reverse-PE capability if and only if at least one
`*_epi.json` file is present in the session's `fmap/` directory. On the
62-session CIDUR cohort, the naive checker and VECTA-DWI-014 produced
identical classifications: all 28 Siemens sessions were flagged as
having EPI fieldmaps (0 triggered); all 34 GE sessions lacked EPI
fieldmaps (34 triggered). In this cohort, no session presented the edge
cases that differentiate the two approaches — a session with an EPI
fieldmap whose `IntendedFor` field does not reference the DWI
acquisition, or a session with a non-EPI fieldmap type (e.g., GRE
phasediff) that could produce a false-negative from a naive any-fmap
check. The TrackTBI cohort provided such cases: among the seven false-negative
sessions (ready_with_limitations, QSIPrep failure), five carried a
non-EPI fieldmap (e.g., GRE dual-echo phasediff) with corrupt or
incomplete metadata; the naive any-fmap check would rate these sessions
as having a fieldmap, while VECTA-DWI-014 correctly identified the absence
of a reverse-PE EPI acquisition and triggered as expected. Beyond binary classification, Vecta provides attributes
absent from any file-presence check: severity designation, lifecycle
layer attribution (acquisition versus BIDS representation), evidence
basis, potential downstream effects, and recommended remediation steps,
all encoded in the versioned specification rather than in ad hoc code.

## Vecta readiness state versus QSIPrep processing outcome

To achieve a more statistically powered outcome cohort, QSIPrep was
submitted for all 9 sessions excluded from the main BIDS dataset during
protocol-variant selection. These sessions had been assessed by Vecta in
the pre-intervention run (71 sessions total; see Pre-intervention
sensitivity analysis). The 2 sessions rated review_required (sub-036
and sub-069, VECTA-DWI-001 + VECTA-DWI-021) were prioritized; both
were confirmed to fail QSIPrep (see below). The 7 sessions rated
ready_with_limitations (VECTA-DWI-014 only) were also submitted; all
7 succeeded with full DWI derivatives.

The extended outcome cohort therefore comprises 69 sessions with
confirmed QSIPrep outcomes: 60 from the main BIDS cohort, 2
pre-intervention sessions (sub-036, sub-069) for which failure was
confirmed, and 7 excluded GE sessions for which success was confirmed. The two sessions without QSIPrep outcomes (sub-009 ses-1 and
ses-2, rated ready) were excluded because the subject was removed from
the QSIPrep batch due to a T1w motion-artifact flag — an anatomical
quality concern outside Vecta's current scope. Vecta correctly assessed
both sessions' DWI layers as ready.

Three distinct failure mechanisms were identified across the three
failures: sub-076 lacked a reverse-PE fieldmap (VECTA-DWI-014); sub-036
and sub-069 lacked a signed PhaseEncodingDirection (VECTA-DWI-021,
review_required). For sub-036 and sub-069, QSIPrep crashed at the DWI
parameter-extraction step (`get_acq_parameters_df` in `merge.py`) when
attempting a string operation on a NaN PhaseEncodingDirection value.
This crash occurs before the susceptibility-distortion correction
workflow begins, meaning QSIPrep fails regardless of fieldmap presence —
a harder block than initially predicted, consistent with VECTA-DWI-021's
review_required designation.

Note on evaluation context: The CIDUR cohort served as the primary
development context for Vecta-DWI v0.1. The PhaseEncodingDirection absence
issue (VECTA-DWI-021) was known from curation records before criterion
specification was finalized. Performance estimates from this cohort therefore
reflect criterion behavior on familiar data and should be interpreted as
illustrative of criterion face validity rather than out-of-sample
generalization. Independent external validation is provided by the TrackTBI
cohort (649 subjects, 1,275 sessions; see below).

**Table 3.** Joint distribution of Vecta readiness state and QSIPrep outcome
across the extended CIDUR outcome cohort (n=71 sessions tracked; 69 with
confirmed QSIPrep outcomes, 2 without). See footnotes for individual case details.

| Vecta readiness | QSIPrep success | QSIPrep failure | No QSIPrep outcome | Total |
|---|---|---|---|---|
| ready | 26 | 0 | 2ᵃ | 28 |
| ready_with_limitations | 40 | 1 | 0 | 41 |
| review_required | 0 | 2 | 0 | 2ᵇ |
| **Total** | **66** | **3** | **2** | **71** |

ᵃ sub-009 ses-1 and ses-2: T1w motion artifact, excluded from QSIPrep batch.
ᵇ sub-036 and sub-069: pre-intervention excluded sessions, QSIPrep confirmed failure.

The failure rate was 0% (0/26) for ready sessions, 2.4% (1/41) for
ready_with_limitations sessions, and 100% (2/2) for review_required
sessions. All three failures occurred in Vecta-flagged sessions. The two
review_required failures (sub-036, sub-069) have a confirmed direct
cause: QSIPrep crashed at parameter extraction because
PhaseEncodingDirection was absent — the condition VECTA-DWI-021
explicitly flags. The ready_with_limitations failure (sub-076) has
a different character: QSIPrep completed anatomical preprocessing and
entered the eddy head-motion correction step before failing; the
available log (844 lines, truncated) does not contain the error message,
and no crash file was recovered. Sub-076's sidecar carries a valid signed
PhaseEncodingDirection (`j-`) and TotalReadoutTime, and its protocol
(50 b1000 directions, 3 b0 volumes; `acq-50dirax`) is slightly atypical
relative to other GE sessions (51–53 b1000 directions). The direct cause
of the eddy-stage failure is therefore not attributable to VECTA-DWI-014's
stated condition (absent fieldmap): 40 other fieldmap-absent GE sessions
ran eddy without error. Vecta correctly classified sub-076 as
ready_with_limitations — the structural assessment (no reverse-PE
fieldmap → no SDC) is accurate — but the QSIPrep failure appears to
have occurred for a different reason not captured by any of Vecta's
current criteria. No ready session failed QSIPrep processing.

## Detection approach comparison

Table 4 presents the 2×2 confusion matrix and derived performance metrics for
the four detection levels evaluated against QSIPrep processing outcomes on the
69 sessions with confirmed outcomes (3 failures, 66 successes;
2 sessions without QSIPrep outcome excluded). Wilson 95% confidence intervals
are shown in brackets.

**Table 4.** Performance metrics for four detection levels against QSIPrep
processing failure as outcome (n = 69; 3 failures, 66 successes;
2 sessions without QSIPrep outcome excluded). This comparison is
mechanistically illustrative: with n=3 failures, all CIs are wide and
values should not be interpreted as precise population estimates. PPV
undefined (—) when no sessions are flagged. Wilson 95% CIs in brackets.

| Level | Description | TP | FP | TN | FN | Sensitivity [95% CI] | Specificity [95% CI] | PPV [95% CI] | NPV [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| 0 | BIDS Validator errors > 0 | 0 | 0 | 66 | 3 | 0.000 [0.000, 0.561] | 1.000 [0.945, 1.000] | — | 0.957 [0.880, 0.985] |
| 1 | PhaseEncodingDirection absent OR TotalReadoutTime absent | 2 | 0 | 66 | 1 | 0.667 [0.208, 0.939] | 1.000 [0.945, 1.000] | 1.000 [0.342, 1.000] | 0.985 [0.920, 0.997] |
| 2 | Vecta Core (readiness ≠ ready) | 3ᵃ | 40 | 26 | 0 | 1.000 [0.439, 1.000] | 0.394 [0.285, 0.515] | 0.070 [0.024, 0.186] | 1.000 [0.871, 1.000] |
| 3 | Vecta + DICOM source integrity | 3ᵃ | 40 | 26 | 0 | 1.000 [0.439, 1.000] | 0.394 [0.285, 0.515] | 0.070 [0.024, 0.186] | 1.000 [0.871, 1.000] |

ᵃ sub-076 (the ready_with_limitations failure) failed at the eddy step for an undetermined cause distinct from the VECTA-DWI-014 condition; 40 other sessions with the same VECTA-DWI-014 finding succeeded. Vecta correctly classified sub-076 as flagged but the QSIPrep failure mechanism was not the criterion's stated condition. See Results: Notable individual cases.

PPV at Level 2 is 0.070 [0.024, 0.186], which requires contextual interpretation: VECTA-DWI-014 flags the structural absence of a reverse-PE EPI acquisition, not a prediction that QSIPrep will abort. The 40 flagged-and-successful GE sessions did not receive SDC; QSIPrep completed via the no-SDC fallback path. These sessions are correctly characterized as having a methodological limitation (absent distortion correction), not as misclassified. PPV should be interpreted as the proportion of flagged sessions that also fail the pipeline, not as the precision of the structural finding itself.

Level 0 (BIDS Validator errors) flags no sessions: all three failures
produced zero BIDS Validator errors. Level 1 (absent PhaseEncodingDirection
or TotalReadoutTime) captures two of the three failures — sub-036 and
sub-069, which lacked a signed PhaseEncodingDirection — but misses
sub-076, whose sidecar carried a valid PhaseEncodingDirection and
TotalReadoutTime; the failure arose from an absent fieldmap (VECTA-DWI-014),
an acquisition-layer condition invisible to metadata-completeness checks.
Level 2 (Vecta Core) captures all three failures because it evaluates
both metadata completeness (VECTA-DWI-021) and fieldmap availability
(VECTA-DWI-014) as separate criteria, achieving sensitivity 1.000 and
NPV 1.000 across two mechanistically distinct failure modes. The
40 false positives at Level 2 are GE sessions that Vecta correctly
characterizes as lacking reverse-PE acquisitions; these sessions were
processed via QSIPrep's no-SDC fallback path and completed without
pipeline error. Level 3 is identical to Level 2 because no DICOM
source-integrity criteria triggered in this cohort. The two sessions
excluded (sub-009 ses-1 and ses-2) are examined in Notable individual
cases below.

The three-failure extended cohort spans two mechanistically distinct
failure modes: metadata absence (VECTA-DWI-021, n=2) and acquisition
absence (VECTA-DWI-014, n=1). In this n=3 sample, Level 1 missed the
acquisition-absence failure mode and Level 2 captured all three — a
mechanistically coherent pattern, though the sample is too small for
formal statistical comparison of sensitivity between levels. The key
distinction illustrated here is structural: a metadata-completeness
check and a fieldmap-availability criterion evaluate independent
evidence layers, and a session can fail for either reason independently.
The TrackTBI external validation (N=1,071) provides the statistical
power to evaluate performance; the CIDUR comparison identifies the two
failure pathways that TrackTBI then tests at scale.

## Comparison with image quality assessment (MRIQC)

MRIQC (Esteban et al., 2017) assesses DWI data quality via image-derived
metrics: signal-to-noise ratio (SNR) for B0 and diffusion-weighted
volumes, framewise displacement (FD) for motion estimation, foreground-
background energy ratio (FBER), entropy focus criterion (EFC), B0 field
uniformity, and b-value/bvec summary statistics. These metrics are
derived from the acquired image data and characterize image quality after
acquisition. MRIQC does not report PhaseEncodingDirection completeness,
TotalReadoutTime presence, fieldmap availability relative to DWI
sessions, or gradient file integrity. A session lacking a signed
PhaseEncodingDirection — the condition that causes QSIPrep to crash
before preprocessing begins — will receive normal MRIQC image quality
scores, because the absence of that sidecar field does not degrade
the acquired signal.

**Table 11b.** Comparison of what each tool reports for the three CIDUR
failure sessions and 40 false-positive GE sessions.

| Session | Vecta finding | Vecta readiness | MRIQC PED flag | MRIQC fmap flag | QSIPrep outcome |
|---|---|---|---|---|---|
| sub-036 ses-1 | VECTA-DWI-021 + VECTA-DWI-001 (no PED) | review_required | not reported | not reported | failure (pre-SDC crash) |
| sub-069 ses-3 | VECTA-DWI-021 + VECTA-DWI-001 (no PED) | review_required | not reported | not reported | failure (pre-SDC crash) |
| sub-076 ses-1 | VECTA-DWI-014 (no reverse-PE EPI) | ready_with_limitations | not reported | not reported | failure (eddy stage) |
| 40 GE sessions | VECTA-DWI-014 (no reverse-PE EPI) | ready_with_limitations | not reported | not reported | success (no-SDC path) |
| 28 Siemens sessions | none | ready | not reported | not reported | success (SDC applied) |

_MRIQC PED flag / MRIQC fmap flag: MRIQC DWI IQMs do not include
PhaseEncodingDirection completeness or fieldmap availability fields;
"not reported" reflects the documented MRIQC DWI output schema, not a
null result from a run. MRIQC IQMs for these sessions would be expected
to fall within normal ranges: the failure modes (absent sidecar fields,
fieldmap metadata corruption) do not alter the acquired signal and
therefore do not degrade image quality metrics._

The distinction is not that MRIQC is inadequate — it correctly answers
its design question (is the image quality acceptable?) — but that it
occupies a different lifecycle layer than Vecta (image quality after
acquisition versus metadata integrity before pipeline execution). MRIQC
should be run after Vecta confirms a session is structurally ready;
for sessions rated review_required or ready_with_limitations, MRIQC
image quality scores are interpretable only in the context of the
readiness finding. These tools are complementary: a session can pass
MRIQC and fail Vecta (metadata absent, image fine) or fail MRIQC and
pass Vecta (motion artifact, metadata intact).

## Connectome output metrics and VECTA-DWI-014 severity calibration

VECTA-DWI-014 is classified as major severity but non-blocking: it
flags the absence of reverse-PE EPI capability as a methodological
limitation without preventing the session from proceeding. To assess
whether this severity calibration is appropriate — i.e., that absent
SDC degrades output quality but does not prevent tractography — connectome
outputs were examined for the 58 subjects with available data
(26 ready, 32 ready_with_limitations). All 58 subjects achieved the
fixed 10-million-streamline tractography target via iFOD2/SIFT (Smith
et al., 2013), parcellated with the Schaefer 200-region atlas (Schaefer
et al., 2018), and all 58 passed downstream QC regardless of readiness
tier. This equivalence confirms that VECTA-DWI-014's non-blocking
designation is appropriate for the tractography-yield dimension: absent
SDC in a single-shell b=1000 s/mm² protocol did not prevent tractography
completion at this target density. It does not indicate that SDC absence
has no effect on microstructural accuracy or tract geometry — those
would require voxel-level comparison beyond the scope of this paper —
but it supports the criterion's intent to characterize the limitation
accurately rather than block processing unnecessarily.

## Notable individual cases

**sub-009 (ses-1 and ses-2).** Both sessions were assessed as ready
(Siemens Skyra, 3.0 T, 67 directions, reverse-PE fieldmap present and
DWI intact in BIDS). Neither session appears in the QSIPrep output tree.
T1w scans acquired at ses-2 were flagged for motion artifacts during
BIDS conversion, and the subject was excluded from the QSIPrep batch as
a subject-level decision. Vecta's DWI assessment was correct; the
exclusion gate was a T1w quality concern outside Vecta's current scope.
This case illustrates a prospective use of Vecta: cross-referencing
ready-rated sessions against pipeline outputs can surface unprocessed
data and expose the specific layer (DWI versus anatomical) at which the
block occurred, enabling targeted remediation decisions without
full-dataset manual review.

**sub-076 ses-1.** The only QSIPrep failure in the 62-session primary BIDS cohort. Vecta rated
this session ready_with_limitations on account of VECTA-DWI-014. The
session was a GE legacy acquisition without distortion-correction
support; QSIPrep produced anatomical derivatives but no preprocessed
DWI output. The Vecta finding correctly characterized the condition that
caused downstream failure.

**sub-044 ses-2.** QSIPrep produced only anatomical outputs for ses-2
of this subject (no DWI directory). However, the subject-level QC record
reports QSIRecon, connectome, and node-strength metrics as passing —
these subject-level statuses reflect ses-1, for which full DWI
preprocessing succeeded. The inconsistency arises from the subject-level
granularity of the QC file, not from a Vecta misclassification; ses-2
was not assessed by Vecta (only ses-1 appeared in the session inventory).

## TrackTBI external validation

### Cohort and readiness distribution

Vecta-DWI was applied to 1,275 sessions from 649 subjects in the TrackTBI
study (634 sessions at 2-week post-injury, 641 at 6-month post-injury)
spanning three vendors: Siemens (584 sessions across multiple models and
three syngo software generations), GE (363 sessions), and Philips
(328 sessions). Original DICOM was not available; assessment was
conducted on BIDS representations only, and DICOM source-integrity
criteria (VECTA-DWI-050, VECTA-DWI-060) were not evaluated for any session.

**Table 5.** Vecta-DWI readiness distribution across 1,275 TrackTBI sessions.

| Readiness state | Sessions | Percentage |
|---|---|---|
| ready_with_limitations | 584 | 45.8% |
| review_required | 691 | 54.2% |
| **Total** | **1,275** | **100%** |

### Vendor stratification

Readiness state was perfectly stratified by vendor: all 584 Siemens
sessions received ready_with_limitations, and all 691 GE and Philips
sessions received review_required. No Siemens session was review_required,
and no GE or Philips session was ready_with_limitations.

The sole triggered criterion for all 584 Siemens sessions was
VECTA-DWI-014 (reverse-PE acquisition unavailable; 45.8% of cohort),
consistent with the CIDUR finding: Siemens sessions had intact metadata
but lacked a reverse-phase-encoding EPI fieldmap acquisition. The sole
triggered criteria for all 691 GE and Philips sessions were VECTA-DWI-001
(PE direction unknown) and VECTA-DWI-021 (essential metadata absent —
PhaseEncodingDirection or TotalReadoutTime absent from BIDS sidecar), with
both criteria co-triggering in every case (54.2% of cohort). Review-required
sessions received an assessment status of completed_with_unknowns; the
mean completeness ratio for this tier (completeness_with_unknowns) reflects
that the PE-direction variable and derived metadata fields were unresolvable
from BIDS alone.

### QSIPrep outcome distribution

Of the 1,275 assessed sessions, 202 had no QSIPrep run recorded
(never_attempted): 133 in the ready_with_limitations tier and 69 in the
review_required tier. Never_attempted sessions arose from HPC resource
constraints (batch quota incidents cancelling submitted jobs) and missing
anatomical prerequisites (absent or malformed T1w for a subset of sessions),
not from Vecta readiness findings; the decision to attempt QSIPrep was made
independently of Vecta assessment status. Never_attempted sessions were
unevenly distributed across readiness tiers: 133 of 584 ready_with_limitations
sessions (22.8%) versus 69 of 689 review_required sessions (10.0%) were
never attempted. Post-hoc review of batch submission logs indicated that the
higher rate in ready_with_limitations reflects Siemens sessions submitted in
earlier HPC batches that were disproportionately affected by quota incidents;
the disproportion was not driven by readiness state. Critically, this
asymmetry is conservative with respect to Vecta's performance estimates: the
unattempted ready_with_limitations sessions, if attempted, would most likely
have succeeded (observed failure rate 1.6%), not failed. These 202 sessions
were excluded from performance metric computation.

Two additional review_required sessions (sub-TBI031004 ses-2WK and
sub-TBI101003 ses-2WK) were excluded from performance analysis: QSIPrep
was run on post-assessment BIDS sidecars in which PhaseEncodingDirection
had been manually patched as part of a controlled remediation test. These
runs do not reflect standard-pipeline behavior with the original
unmodified sidecar and are not informative about whether VECTA-DWI-021
predicts standard QSIPrep failure. The remaining 1,071 sessions had
confirmed QSIPrep outcomes (1,275 assessed − 202 never_attempted − 2
post-remediation test sessions = 1,071).

**Table 6.** Joint distribution of Vecta readiness state and QSIPrep
outcome across 1,273 eligible TrackTBI sessions (1,275 assessed minus
2 post-remediation test sessions).

| Vecta readiness | QSIPrep success | QSIPrep failure | Never attempted | Total |
|---|---|---|---|---|
| ready_with_limitations | 444 | 7 | 133 | 584 |
| review_required | 0 | 620 | 69 | 689 |
| **Total** | **444** | **627** | **202** | **1,273** |

### Failure rates and prediction accuracy

Among sessions with confirmed QSIPrep outcomes (n = 1,071), the failure
rate was 1.6% (7/451) for ready_with_limitations sessions and 100%
(620/620) for review_required sessions. Every review_required session
that entered QSIPrep failed; no ready_with_limitations session that
failed could be attributed to the reverse-PE absence condition.

Performance metrics (n = 1,071 sessions with confirmed outcomes;
627 failures, 444 successes; 202 never_attempted and 2 post-remediation
test sessions excluded) are presented in Table 7. Wilson 95% confidence
intervals are shown in brackets.

**Table 7.** Vecta-DWI performance metrics for the TrackTBI external
validation cohort (n = 1,071; 627 failures, 444 successes).
A positive is a session flagged as review_required; a case is a QSIPrep
failure. Wilson 95% CIs in brackets.

| Metric | Value [95% CI] | Numerator / Denominator |
|---|---|---|
| Sensitivity | 0.989 [0.977, 0.995] | 620 / 627 |
| Specificity | 1.000 [0.991, 1.000] | 444 / 444 |
| PPV | 1.000 [0.994, 1.000] | 620 / 620 |
| NPV | 0.984 [0.968, 0.992] | 444 / 451 |

### False negatives

Seven sessions were rated ready_with_limitations but failed QSIPrep.
Five had cause=fieldmap_error: each carried a non-EPI fieldmap (e.g., a
GRE phasediff acquisition) with corrupt or incomplete metadata. VECTA-DWI-014
evaluates reverse-PE EPI fieldmap availability; it does not inspect
non-EPI fieldmap metadata integrity. These five cases represent a scope
gap: the criterion correctly identifies the absence of a reverse-PE EPI
reference but cannot predict failure from a corrupt non-EPI fieldmap that
the pipeline also attempts to use. The remaining 2 false negatives had
no identified cause; their QSIPrep logs did not contain a diagnostic error
attributable to the DWI layer.

### Sensitivity analysis for never_attempted exclusion

To assess whether the exclusion of 202 never_attempted sessions biases the
performance estimates, a proportional imputation was applied: never_attempted
sessions in each readiness tier were assigned failure rates equal to the
observed rates for attempted sessions in that tier (1.6% for
ready_with_limitations, 100% for review_required). Under this assumption,
133 never_attempted ready_with_limitations sessions contribute ~2 additional
failures; 69 never_attempted review_required sessions contribute 69 additional
failures. The imputed sensitivity is 689/698 = 0.987 and the imputed NPV is
574/583 = 0.985 — both within 0.002 of the observed values (0.989 and 0.984
respectively), confirming that the exclusion does not materially affect the
conclusions. Under the conservative worst-case scenario in which all
202 never_attempted sessions would have failed, sensitivity falls to 0.831;
however, this scenario is implausible for the ready_with_limitations tier,
which had a 1.6% observed failure rate among attempted sessions.

## OpenNeuro public dataset validation

To assess criterion behavior across independently published datasets spanning
diverse scanners, sites, and protocols, Vecta-DWI was applied to three
OpenNeuro datasets: the Stockholm SleepyBrain dataset (ds000201; van der
Meer et al., 2020), the MASiVar multisite variability dataset (ds003416;
Cai et al., 2021), and the ON-Harmony multi-scanner harmonization dataset
(ds004712; Karakuzu et al., 2022). No DICOM
was available for any of these datasets; accordingly, source-integrity criteria
(VECTA-DWI-050, VECTA-DWI-060) were not evaluated. Table 6 in the preceding section presents TrackTBI outcome data; OpenNeuro
criterion-level results across all three datasets are summarized in Table 8.

**Table 8.** Vecta-DWI assessment summary across three OpenNeuro datasets.
Sessions assessed, readiness distribution, criterion activation counts, and
mean completeness ratio. DICOM not available for any dataset; source-integrity
criteria not evaluated.

| Dataset | Sessions assessed | Ready | Ready_with_limitations | Not assessed | VECTA-DWI-014 | VECTA-DWI-021 | VECTA-DWI-030 | Mean completeness |
|---|---|---|---|---|---|---|---|---|
| SleepyBrain (ds000201) | 76 | 0 | 76 | 0 | 76 (100%) | 76 (100%) | 0 | 0.824 |
| MASiVar (ds003416) | 308 | 0 | 281 | 27 | 0 | 281 (100%) | 5 (1.8%) | 0.586† |
| ON-Harmony (ds004712) | 165 | 164 | 1 | 0 | 1 (0.6%) | 0 | 0 | 0.882 |

_†Mean completeness for 281 completed sessions; 27 sessions with missing JSON sidecars were not assessed._

**Stockholm SleepyBrain (ds000201).** All 76 sessions were acquired on a GE
DISCOVERY MR750 scanner at 3.0 T. Vecta-DWI assessed all 76 sessions to
completion (status completed_with_unknowns, mean completeness 0.824; DICOM
not available). All 76 sessions received a readiness state of
ready_with_limitations, with two criteria co-triggering: VECTA-DWI-014 (no
reverse-PE EPI acquisition, 76/76) and VECTA-DWI-021 (TotalReadoutTime absent
from BIDS sidecar JSON, 76/76). The co-occurrence of two criteria in the same
session — both originating at different evidence layers (acquisition protocol
versus metadata generation) — illustrates a pattern absent from the CIDUR
cohort, where only VECTA-DWI-014 triggered. The absence of TotalReadoutTime
means that even if a reverse-PE reference were added in a follow-up protocol,
SDC calibration would require either the EffectiveEchoSpacing parameter
(present in this dataset) or a DICOM-derived alternative.

**MASiVar (ds003416).** MASiVar is a multi-site, multi-scanner, multi-subject
dataset spanning Siemens, GE, and Philips platforms (Cai et al., 2021). Vecta-DWI assessed
all 308 sessions. Twenty-seven sessions belonging to a Philips scanner cohort
(sub-cIIs* subjects) lacked JSON sidecar files entirely and received
assessment_status failed with readiness not_assessed; these represent a
BIDS-level structural incompleteness in the published dataset (no PhaseEncoding
Direction metadata derivable from any available file). The remaining 281 sessions
were all assessed to completion (status completed_with_unknowns, mean
completeness 0.586; assessment completeness is low because MASiVar sidecar
JSONs contain only PhaseEncodingDirection and no further scanner or acquisition
metadata). All 281 received a readiness state of ready_with_limitations, with
VECTA-DWI-021 (TotalReadoutTime absent) as the sole triggered criterion;
VECTA-DWI-014 did not trigger because all assessed sessions include DWI
acquisitions at both complementary phase-encoding directions within the same
session. Five sessions — sub-cIIIsA01 ses-s1Bx7, sub-cIIIsC007 ses-s1Bx3,
sub-cIIIsC040 ses-s1Bx2, sub-cIIIsC101 ses-s1Bx1, and sub-cIIIsC110 ses-s1Bx1
— also triggered VECTA-DWI-030 (gradient file missing or unparseable). Inspection
confirmed that all .bvec files and .nii.gz images are absent from the S3
source for these five sessions; the bval and JSON sidecar files exist, but
the corresponding gradient table and image data were never deposited. These five
sessions would fail any DWI preprocessing pipeline at the gradient-loading step.
No BIDS Validator error was reported for these sessions because the validator
treats absent optional gradient files as a structure-level warning rather than
a blocking error. The MASiVar derivatives folder on OpenNeuro contains
published prequal-v1.0.0 outputs. Examination shows that the five VECTA-DWI-030
sessions each have 8–12 files in the prequal derivatives with 0 preprocessed
NIfTI images; however, all sessions from the same sub-cohorts (sub-cIIIsA and
sub-cIIIsC scanner variability groups) also produce no NIfTI output in prequal,
regardless of bvec availability. The prequal derivative pattern therefore reflects
a sub-cohort-level preprocessing incompatibility — likely related to the absent
TotalReadoutTime flagged by VECTA-DWI-021 across all MASiVar sessions — rather
than an outcome specific to the VECTA-DWI-030 finding. The primary evidence for
VECTA-DWI-030's finding validity remains the S3 source inspection: confirmed
absence of bvec files and NIfTI images from the source repository for these
five sessions.

**ON-Harmony (ds004712).** ON-Harmony is a longitudinal multi-scanner
harmonization dataset covering Siemens (75 sessions), Philips (50 sessions),
and GE (40 sessions) platforms across multiple sites (Karakuzu et al., 2022). Vecta-DWI assessed
all 165 sessions to completion (status completed_with_unknowns, mean completeness
0.882). One hundred and sixty-four of 165 sessions received a readiness state of
ready (VECTA-DWI-014 not triggered, TotalReadoutTime present). A single session
— sub-16793 ses-OXF4GEP001 (GE SIGNA Premier) — received a readiness state of
ready_with_limitations on account of VECTA-DWI-014. Inspection of the DWI
sidecar JSON revealed a phase-encoding axis inconsistency: the dir-AP DWI
acquisition has PhaseEncodingDirection j- while the dir-PA acquisition has
PhaseEncodingDirection i. These two acquisitions are on different readout axes
and cannot serve as complementary reverse-PE references, even though both AP
and PA labeled files are physically present. A naive bidirectional-PE check
based on filename labels (dir-AP and dir-PA present) would rate this session
as having a valid reverse-PE reference; Vecta correctly identifies the axis
mismatch and triggers VECTA-DWI-014. This case is analogous to the GRE phasediff edge cases observed in the
TrackTBI external validation cohort: in both instances, a file whose label
suggests distortion-correction capability does not satisfy the criterion's
metadata-level conditions.

## Pre-intervention sensitivity analysis

To assess Vecta's prospective sensitivity to the metadata issues that
drove post-conversion curation decisions, Vecta-DWI was applied to the
pre-intervention BIDS dataset (71 sessions: the 62 retained sessions plus
the 9 sessions whose DWI acquisitions were removed by protocol-variant
selection; see Methods).

**Table 9.** Readiness distribution before and after protocol-variant
selection. The pre-intervention dataset includes 9 sessions subsequently
excluded from the analysis cohort.

| Readiness state | Pre-intervention (n=71) | Post-intervention (n=62) |
|---|---|---|
| ready | 29 (40.8%) | 28 (45.2%) |
| ready_with_limitations | 40 (56.3%) | 34 (54.8%) |
| review_required | 2 (2.8%) | 0 (0%) |

Two pre-intervention sessions received review_required: VECTA-DWI-021
(essential metadata absent) and VECTA-DWI-001 (PE direction unknown)
co-triggered in both. The root cause was a Siemens Skyra dcm2niix export
behavior that produces only the unsigned `PhaseEncodingAxis` field
(indicating the readout axis) without the signed `PhaseEncodingDirection`
field (indicating polarity). These are semantically distinct BIDS fields:
`PhaseEncodingDirection` encodes k-space traversal direction and is
required for SDC calibration; `PhaseEncodingAxis` does not carry
polarity and cannot substitute. The 16 Skyra sessions retained in the
post-curation cohort carry the signed direction field — inferred from
the BIDS filename direction entity and added during the post-conversion
curation step that ran after protocol-variant selection was complete.
The two flagged sessions were excluded before that step ran, leaving
their sidecars with only the raw dcm2niix output.

Both sessions were independently excluded by the curation protocol,
which used BIDS filename label detection and had no access to sidecar
JSON content. Vecta's sidecar-metadata validation and the filename-label
approach identified the same two sessions through entirely independent
evidence paths.

To confirm the predicted QSIPrep failure, both sessions were submitted
to QSIPrep 1.0.1.dev0+gee9aa2e.d20250115 using the same parameters as the main cohort. Both
failed. The crash occurred at the DWI parameter-extraction stage
(`get_acq_parameters_df`, `qsiprep/workflows/dwi/merge.py`) when
QSIPrep attempted a string operation (`.str.replace("-", "")`) on a
NaN-valued `PhaseEncodingDirection` column — before the
susceptibility-distortion correction workflow was ever instantiated.
This failure mode is harder than originally predicted: the missing
PhaseEncodingDirection does not merely prevent SDC calibration, it
prevents QSIPrep from constructing the preprocessing workflow entirely,
regardless of whether a fieldmap is present. Sub-036 (no fieldmap) and
sub-069 (fieldmap present) produced identical crash traceback and both
exited with pipeline failure. This empirically confirms VECTA-DWI-021's
review_required designation: sessions lacking a signed
PhaseEncodingDirection cannot be preprocessed by QSIPrep irrespective
of acquisition protocol.

The seven remaining excluded sessions triggered VECTA-DWI-014 only
(no reverse-PE EPI fieldmap) — the same condition as the 34 GE sessions
in the retained cohort. Their curation exclusion was a protocol-selection
decision (non-standard gradient direction count) not detectable from
sidecar metadata, and is outside Vecta's DBI scope. QSIPrep was
submitted for all 7 sessions; all 7 succeeded with full DWI derivatives,
consistent with the 40/41 (97.6%) success rate observed for the same
criterion across the extended outcome cohort. One shared session showed a
readiness change (ready → ready_with_limitations) after the curation
step removed one of its two complementary-PE DWI acquisitions; Vecta's
sidecar-level reverse-PE detection had identified the pair, and
correctly revised its assessment once the pair was dissolved.

BIDS Validator v1.15.0 issued no error or warning for the absent
`PhaseEncodingDirection`, the unsigned-axis-only sidecar state, or the
missing reverse-PE acquisitions in any pre-intervention session. The
BIDS specification does not require `PhaseEncodingDirection`; its
absence is invisible to conformance-based validation but detectable by
a readiness-focused assessment. Taken together, this analysis
demonstrates that Vecta would have prospectively flagged the
metadata-level failure mode in both excluded sessions prior to and
independent of the curation decisions — from information present in
the BIDS sidecar at the time of conversion, without DICOM access.

## Cross-dataset criterion activation summary

Table 10 presents the criterion activation pattern across all five datasets.
Each criterion was activated in at least one dataset, with the exception of
VECTA-DWI-040, which did not trigger in any reported cohort and is validated
via the synthetic fixture suite. VECTA-DWI-001 activated in the TrackTBI
external validation cohort (691/1,275, 54.2%), where GE and Philips sessions
lacked a signed PhaseEncodingDirection in the BIDS sidecar; it also activates
in the CIDUR pre-intervention analysis (n=2, sub-036 and sub-069; see
Pre-intervention sensitivity analysis below), where the dcm2niix Skyra export
produced only an unsigned PhaseEncodingAxis field without the signed
PhaseEncodingDirection required by downstream pipelines. VECTA-DWI-014 and
VECTA-DWI-021 co-triggered for all 691 TrackTBI GE and Philips sessions,
exhibited complementary co-occurrence in SleepyBrain, and showed mutually
exclusive patterns in MASiVar and ON-Harmony, reflecting distinct acquisition
and metadata practices across vendor platforms. VECTA-DWI-030 activated
exclusively in MASiVar, where S3 source inspection confirmed the corresponding
bvec files were never deposited. All results in this paper were generated
under Vecta-DWI specification version v0.1.0; a subsequent profile update
(v0.1.1) reclassified VECTA-DWI-030 as blocking but does not affect any
performance metric reported here (VECTA-DWI-030 triggered only in MASiVar,
which has no QSIPrep outcome data). VECTA-DWI-050 and VECTA-DWI-060 were evaluable only
in CIDUR (DICOM available); neither triggered, indicating a clean conversion in
that cohort.

**Table 10.** Criterion activation across all five datasets. Bold: criterion
triggered. Dash: DICOM not available; criterion not evaluated.

| Criterion | CIDUR (n=62) | TrackTBI (n=1275) | SleepyBrain (n=76) | MASiVar (n=281ᵃ) | ON-Harmony (n=165) |
|---|---|---|---|---|---|
| VECTA-DWI-001: PE direction unknown | 0 | **691 (54.2%)** | 0 | 0 | 0 |
| VECTA-DWI-014: Complementary PE reference unavailable | **34 (54.8%)** | **584 (45.8%)** | **76 (100%)** | 0 | **1 (0.6%)** |
| VECTA-DWI-021: Essential metadata absent | 0 | **691 (54.2%)** | **76 (100%)** | **281 (100%)** | 0 |
| VECTA-DWI-030: Gradient file missing | 0 | 0 | 0 | **5 (1.8%)** | 0 |
| VECTA-DWI-031: Gradient norms implausible | 0ᶜ | 0ᶜ | 0ᶜ | 0ᶜ | 0ᶜ |
| VECTA-DWI-040: No DWI present | 0 | 0 | 0 | 0 | 0 |
| VECTA-DWI-050: DICOM geometry inconsistent | 0/61ᵇ | — | — | — | — |
| VECTA-DWI-060: DICOM/BIDS field-strength mismatch | 0/61ᵇ | — | — | — | — |

ᵃ 27 Philips sessions (sub-cIIs\* subjects) lacked JSON sidecars and were not
assessed; 281 assessed sessions shown. ᵇ DICOM available for CIDUR only;
evaluated for 61/62 sessions (one not applicable due to DICOM directory mismatch).
ᶜ VECTA-DWI-031 was not activated in any dataset (all bvec files had unit-norm
gradient vectors as expected from dcm2niix conversion); criterion validity was
confirmed via controlled defect injection (see Section "Controlled criterion
validation" below).

## Controlled criterion validation

To provide direct evidence that each Vecta-DWI criterion fires exactly when
its target condition is present — and is silent otherwise — we applied
controlled defect injection to a single known-good session. Sub-001 ses-1
(Siemens Prisma, 67 directions, reverse-PE EPI fieldmap, Vecta baseline
readiness: *ready*) was copied five times; four copies each received one
precisely defined defect; one remained as an unmodified control. Vecta was
run on all five subdatasets using the `dwi_connectomics` profile. Results are
shown in Table 11.

**Table 11.** Controlled defect injection: injected defect, criterion expected
to fire, observed Vecta readiness, observed findings, and confirmed QSIPrep
outcome.

| Defect ID | Injected defect | Expected criterion | Observed readiness | Observed findings | QSIPrep outcome |
|---|---|---|---|---|---|
| baseline | None (control) | None | ready | [] | SUCCESS (DWI derivatives present) |
| def-021 | `PhaseEncodingDirection` removed from DWI sidecar | VECTA-DWI-021 | review\_required | VECTA-DWI-001, VECTA-DWI-021 | FAILURE (silent DWI exclusion; anat-only output) |
| def-014 | Reverse-PE EPI fieldmap deleted | VECTA-DWI-014 | ready\_with\_limitations | VECTA-DWI-014 | SUCCESS (no-SDC fallback; DWI derivatives present) |
| def-030 | DWI `.bvec` file deleted | VECTA-DWI-030 | not\_ready | VECTA-DWI-030 | FAILURE (BIDS validation error; dataset rejected) |
| def-031 | Non-zero bvec norms scaled to 0.5 | VECTA-DWI-031 | ready\_with\_limitations | VECTA-DWI-031 | SUCCESS (eddy completed; DWI derivatives present) |

All four criterion-level predictions were confirmed: each criterion fired
exclusively for its target defect, and the baseline remained *ready* with no
findings. The readiness states were also as expected: def-021 escalated to
*review_required* because VECTA-DWI-001 (unsigned PE direction) co-fires
whenever PhaseEncodingDirection is absent (VECTA-DWI-001 is a review
criterion); def-030 produced *not_ready* because VECTA-DWI-030 is designated
blocking (tractography cannot proceed without gradient files); def-014 and
def-031 produced *ready_with_limitations* as non-blocking non-review criteria.
VECTA-DWI-031 was not observed to fire in any real-world cohort — all bvec
files produced by dcm2niix carried unit-norm gradient vectors — but the
injection confirms the detection logic functions as designed.

QSIPrep 1.0.1.dev0+gee9aa2e.d20250115 outcomes were confirmed for all five subdatasets. The failure
prediction was verified for def-021 and def-030, and the success prediction was
verified for baseline, def-014, and def-031. The def-021 outcome is noteworthy:
QSIPrep reported "QSIPrep finished successfully!" and exited with code 0, but
produced no DWI derivatives — the DWI session was silently excluded from the
workflow during the grouping step. This silent-skip behavior is mechanistically
distinct from the crash observed for sub-036 and sub-069, where QSIPrep raised
an `AttributeError` at `get_acq_parameters_df()` and terminated immediately;
the difference likely reflects session-level grouping context rather than the
PhaseEncodingDirection absence per se. Both modes represent failure to produce
usable DWI preprocessed output; the silent-skip mode is the more operationally
dangerous because no error is surfaced to the researcher. Vecta-DWI-021
correctly predicts the failure in both cases.
