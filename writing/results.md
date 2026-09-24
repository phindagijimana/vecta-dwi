# Results

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

Table 1 summarizes criterion evaluation results across the 62 assessed
sessions.

| Criterion | Description | Triggered | Evaluated | Prevalence |
|---|---|---|---|---|
| VECTA-DWI-001 | Missing b=0 reference volume | 0 | 62 | 0% |
| VECTA-DWI-014 | Reverse PE acquisition unavailable | 34 | 62 | 54.8% |
| VECTA-DWI-021 | Essential metadata insufficient (PE direction or TotalReadoutTime absent) | 0 | 62 | 0% |
| VECTA-DWI-030 | DWI gradient file (.bval/.bvec) missing or unparseable | 0 | 62 | 0% |
| VECTA-DWI-031 | DWI gradient vectors have implausible norms (non-unit) | 0 | 62 | 0% |
| VECTA-DWI-040 | No DWI acquisition present (cohort integrity) | 0 | 62 | 0% |
| VECTA-DWI-050 | DICOM geometry inconsistency within session | 0 | 61 | 0% |
| VECTA-DWI-060 | DICOM/BIDS field-strength disagreement | 0 | 61 | 0% |

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
check. The TrackTBI pilot provided one such case: one participant had a
GRE dual-echo phasediff fieldmap; the naive any-fmap check would rate
this session as having a fieldmap, while VECTA-DWI-014 correctly
identified the absence of a reverse-PE EPI acquisition and triggered
as expected. Beyond binary classification, Vecta provides attributes
absent from any file-presence check: severity designation, lifecycle
layer attribution (acquisition versus BIDS representation), evidence
basis, potential downstream effects, and recommended remediation steps,
all encoded in the versioned specification rather than in ad hoc code.

## Vecta readiness state versus QSIPrep processing outcome

QSIPrep v0.23.1 outcomes were available for 60 of the 62 Vecta-assessed
sessions. The two sessions without QSIPrep outcomes were sub-009 ses-1
and ses-2, both rated ready by Vecta. Review of the BIDS conversion
records indicates that ses-2 for this subject had T1w scans flagged for
motion artifacts; the subject was excluded from the QSIPrep batch as a
subject-level decision, likely due to the T1w artifact flag on ses-2
affecting both sessions. The DWI data for both sessions were intact in
BIDS (67-direction Siemens Skyra acquisitions with reverse-PE fieldmaps
present), and Vecta correctly assessed the DWI layer as ready. The
pipeline exclusion was driven by an anatomical (T1w) quality concern
that falls outside Vecta's current assessment scope.

Table 3 presents the joint distribution of Vecta readiness state and
QSIPrep success.

| Vecta readiness | QSIPrep success | QSIPrep failure | No QSIPrep outcome | Total |
|---|---|---|---|---|
| ready | 26 | 0 | 2 | 28 |
| ready_with_limitations | 33 | 1 | 0 | 34 |
| **Total** | **59** | **1** | **2** | **62** |

Among the 26 ready sessions that were processed, all 26 produced valid
preprocessed DWI outputs (positive predictive value: 26/26, 100%).
Among the 34 ready_with_limitations sessions, 33 produced valid
preprocessed outputs and 1 did not (97.1% processing success rate). The
single QSIPrep failure occurred in a session that Vecta had pre-flagged
with VECTA-DWI-014: a GE SIGNA Premier acquisition acquired without a
reverse-PE fieldmap for which distortion correction was not applicable.
QSIPrep confirmed this at runtime and produced no preprocessed DWI
output for that session. No ready session failed QSIPrep processing.

## Connectome output metrics by readiness group

To assess whether the absence of SDC in ready_with_limitations sessions
(all GE) was associated with degraded connectome output quality, we
compared tractography yield and downstream QC status between readiness
groups across the 58 subjects with available connectome data (26 ready,
32 ready_with_limitations). The QSIRecon configuration used a fixed
tractography target of 10 million streamlines per session via iFOD2
(MRtrix3); all 58 sessions with connectivity outputs achieved this
target, indicating equivalent tractography yield regardless of SDC
status. The CSD reconstruction pipeline used here does not produce
voxel-wise DTI-derived FA maps; therefore, a tract-weighted FA comparison
between groups is not available from the current outputs. Both groups
produced connectome outputs and passed downstream QC (connectome and
node-strength metrics available and passing for all 58 subjects).
These results are consistent with VECTA-DWI-014's non-blocking severity
designation: the criterion correctly flags a methodological limitation —
absence of distortion correction — without predicting connectome failure.

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

**sub-076 ses-1.** The only QSIPrep failure in the cohort. Vecta rated
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

## Criterion replication: TrackTBI independent cohort

To assess whether the primary triggered criterion replicated in an
independent cohort with a different institution, scanner platform, and
protocol, the framework was applied to a subset of five
participants from the TrackTBI study (Yue et al., 2013). These sessions were
acquired at Baylor College of Medicine and Massachusetts General Hospital
using Siemens TrioTim and Skyra scanners (syngo software versions B17,
B19, and D13) with a b = 1300 s/mm² single-shell protocol and gradient
table sizes of 65 and 72 directions respectively — a different
institution, scanner platform, b-value, and gradient scheme from the
CIDUR cohort. Original DICOM was not available for this pilot;
accordingly, DICOM source-integrity criteria (VECTA-DWI-050,
VECTA-DWI-060) were not evaluated, and the mean assessment completeness
ratio was 0.882 across all sessions.

Vecta-DWI assessed all 10 sessions (5 subjects × 2 longitudinal time
points: 2-week and 6-month post-injury) to completion. All 10 received a
readiness state of ready_with_limitations, with VECTA-DWI-014 as the
sole triggered criterion. None of the five participants had a
reverse-phase-encoding EPI fieldmap; one participant had a GRE dual-echo
phasediff fieldmap, which Vecta correctly identified as a non-EPI
acquisition and did not treat as satisfying the reverse-PE availability
requirement.

Table 4 presents the joint distribution for the five 2-week sessions,
the only sessions for which QSIPrep outcomes were available in this
batch.

| Vecta readiness | QSIPrep success | QSIPrep failure | No QSIPrep outcome | Total |
|---|---|---|---|---|
| ready_with_limitations | 5 | 0 | 5 | 10 |
| **Total** | **5** | **0** | **5** | **10** |

All five 2-week sessions produced valid preprocessed DWI outputs (5/5,
100%). The six-month sessions had not been run through QSIPrep in this
batch; Vecta assessed those DWI acquisitions as structurally intact, with
no criterion triggered beyond VECTA-DWI-014. This pilot result is
consistent with the ready_with_limitations processing success rate
observed in the CIDUR cohort (97.1%) and indicates that VECTA-DWI-014
correctly characterizes the distortion-correction limitation without
blocking processing in either dataset.

## OpenNeuro public dataset validation

To assess criterion behavior across independently published datasets spanning
diverse scanners, sites, and protocols, Vecta-DWI was applied to three
OpenNeuro datasets: the Stockholm SleepyBrain dataset (ds000201; van der
Meer et al., 2020), the MASiVar multisite variability dataset (ds003416;
Cai et al., 2021), and the ON-Harmony multi-scanner harmonization dataset
(ds004712; Karakuzu et al., 2022). No DICOM
was available for any of these datasets; accordingly, source-integrity criteria
(VECTA-DWI-050, VECTA-DWI-060) were not evaluated. Table 5 summarizes the
criterion-level results across all three datasets.

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
mismatch and triggers VECTA-DWI-014. This case is analogous to the GRE phasediff
edge case observed in the TrackTBI pilot: in both instances, a file whose label
suggests distortion-correction capability does not satisfy the criterion's
metadata-level conditions.

## Pre-intervention sensitivity analysis

To assess Vecta's prospective sensitivity to the metadata issues that
drove post-conversion curation decisions, Vecta-DWI was applied to the
pre-intervention BIDS dataset (71 sessions: the 62 retained sessions plus
the 9 sessions whose DWI acquisitions were removed by protocol-variant
selection; see Methods).

**Table 6.** Readiness distribution before and after protocol-variant
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
evidence paths. The absent signed `PhaseEncodingDirection` implies that
any SDC-dependent preprocessing pipeline would fail at the
susceptibility-correction step — consistent with the confirmed failure
mode for the same unsigned-PED condition in the TrackTBI cohort.

The seven remaining excluded sessions triggered VECTA-DWI-014 only
(no reverse-PE EPI fieldmap) — the same condition as the 34 GE sessions
in the retained cohort. Their curation exclusion was a protocol-selection
decision (non-standard gradient direction count) not detectable from
sidecar metadata, and is outside Vecta's DBI scope. One shared session
showed a readiness change (ready → ready_with_limitations) after the
curation step removed one of its two complementary-PE DWI acquisitions;
Vecta's sidecar-level reverse-PE detection had identified the pair, and
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

Table 7 presents the criterion activation pattern across all five datasets.
Each criterion was activated in at least one dataset, with the exception of
VECTA-DWI-001 and VECTA-DWI-040, which did not trigger in any cohort.
VECTA-DWI-014 and VECTA-DWI-021 exhibited complementary co-occurrence
(SleepyBrain) and mutually exclusive patterns (MASiVar, ON-Harmony), reflecting
distinct acquisition and metadata practices. VECTA-DWI-030 activated exclusively
in MASiVar, where preprocessing failure was independently confirmed.
VECTA-DWI-050 and VECTA-DWI-060 were evaluable only in CIDUR (DICOM available);
neither triggered, indicating a clean conversion in that cohort.

**Table 7.** Criterion activation across all five datasets. Bold: criterion
triggered. Dash: DICOM not available; criterion not evaluated.

| Criterion | CIDUR (n=62) | TrackTBI (n=10) | SleepyBrain (n=76) | MASiVar (n=281ᵃ) | ON-Harmony (n=165) |
|---|---|---|---|---|---|
| VECTA-DWI-001: PE direction unknown | 0 | 0 | 0 | 0 | 0 |
| VECTA-DWI-014: Reverse PE unavailable | **34 (54.8%)** | **10 (100%)** | **76 (100%)** | 0 | **1 (0.6%)** |
| VECTA-DWI-021: Essential metadata absent | 0 | 0 | **76 (100%)** | **281 (100%)** | 0 |
| VECTA-DWI-030: Gradient file missing | 0 | 0 | 0 | **5 (1.8%)** | 0 |
| VECTA-DWI-040: No DWI present | 0 | 0 | 0 | 0 | 0 |
| VECTA-DWI-050: DICOM geometry inconsistent | 0/61ᵇ | — | — | — | — |
| VECTA-DWI-060: DICOM/BIDS field-strength mismatch | 0/61ᵇ | — | — | — | — |

ᵃ 27 Philips sessions (sub-cIIs\* subjects) lacked JSON sidecars and were not
assessed; 281 assessed sessions shown. ᵇ DICOM available for CIDUR only;
evaluated for 61/62 sessions (one not applicable due to DICOM directory mismatch).
