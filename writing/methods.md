# Methods

## The Vecta-DWI framework

### Data Birth Integrity construct

We define Data Birth Integrity (DBI) as the degree to which the
information, structure, acquisition characteristics, and representation
needed for a specified downstream scientific use are present, internally
consistent, traceable, and appropriately preserved from acquisition
through the analysis-ready representation. DBI is intended-use
conditional: the same session may be sufficient for one analysis and
insufficient for another depending on what the downstream workflow
requires.

Four formal properties constitute the design requirements of any
DBI-conformant implementation. First, **intended-use conditionality**:
assessment is always evaluated relative to a declared profile that
encodes downstream requirements; readiness states are profile-relative,
not absolute. Second, **null safety**: the value state `unknown` is
never coerced to false or absent; a criterion requiring a variable in
an `unknown` state returns `unknown` status and emits no finding,
preventing both false-positive findings and false reassurance. Third,
**determinism**: for a fixed specification version and fixed inputs,
the engine produces an identical output; findings are reproducible
without re-running any preprocessing. Fourth, **specification-version
pinning**: variables, criteria, and profiles carry explicit version
identifiers so that assessment runs can be compared unambiguously and
specification changes are traceable. These properties are design
guarantees, not empirical claims; their practical consequences are
illustrated by the CIDUR pre-intervention analysis (null safety
preventing false reassurance when PhaseEncodingDirection is absent)
and the specification-version statement that fixes all reported results
to v0.1.0.

We operationalize DBI through a versioned specification executed by a
deterministic engine, with scientific meaning encoded in the
specification rather than in code, so that the assessment contract is
independently reviewable and reproducible independently of the software
implementation.

### Specification structure

The Vecta-DWI v0.1 specification consists of versioned variables,
criteria, intended-use profiles, evidence entries, and numeric
tolerances. Variables are machine-readable measurement contracts, each
carrying a stable identifier, lifecycle layer, allowed value states,
source mappings with exact DICOM tags (NEMA, 2024) and BIDS
fields (Gorgolewski et al., 2016), canonical units, validity constraints, and an
extraction algorithm reference. Version 0.1 defines 22 variables across
five domains: scanner context (manufacturer, model, field strength,
software version), acquisition parameters (voxel size, volume count,
b-value and gradient file counts, shell structure, bvec plausibility,
phase-encoding direction, total readout time), BIDS representation
(validator error and warning counts, required series presence, DWI
presence), DICOM source integrity (series count, instance count,
duplicate detection, geometry consistency, DICOM-to-BIDS field strength
agreement), and acquisition-derived variables (reverse phase-encoding
availability).

Criteria are declarative rules that evaluate one or more variables under
a profile and emit a structured finding when the condition is satisfied.
Version 0.1 defines eight active criteria (Table 1). Each criterion
specifies its required variables, a declarative condition tree (composed
of all, any, and not operators over equals and not_equals predicates),
and a finding template capturing label, category, lifecycle origin,
severity, evidence basis, potential downstream effects, and recommended
remediation actions. Severity is a provisional categorical label
(informational, minor, major, critical) carrying an explicit evidence
basis chain; it is distinct from confidence, which describes certainty
that the observation is correct.

The dwi_connectomics intended-use profile declares the required and
preferred evidence for structural connectomics preprocessing. It
specifies which criteria apply to sessions assessed under this profile
and the readiness decision rules: sessions with no triggered findings are
rated ready; sessions with triggered non-blocking findings are rated
ready_with_limitations; sessions where a blocking criterion fires are
rated not_ready; sessions where a review criterion returns unknown status
are rated review_required. The `dwi_connectomics` profile is the only
profile specified in Vecta-DWI v0.1; extension to other intended-use
profiles (resting-state fMRI, multi-shell acquisition, quantitative MRI)
is architecturally supported but requires separate specification
development and empirical validation outside the scope of this paper.
All variable extraction algorithms assume dcm2niix (Li et al., 2016)
field naming conventions in BIDS sidecar JSON files; datasets converted
using other tools may produce non-standard field names that Vecta's
extractor does not recognize, yielding `extraction_failed` states
rather than evaluated values for affected variables.

### Value state vocabulary

Every variable observation is assigned one of eight mutually exclusive
states: observed (value determined from evidence), derived (calculated
from other values), unknown (evidence insufficient), not_collected
(not acquired by design), not_applicable (variable does not apply to
this profile), invalid (value violates validity constraints),
extraction_failed (source present but parsing failed), and conflict
(multiple sources disagree beyond tolerance). The unknown state is never
coerced to false. When a criterion requires a variable in an unknown
state, the criterion returns status unknown and no finding is emitted,
preventing both false-positive findings and false reassurance.

### Engine and output

The criteria engine evaluates each criterion's declarative condition
tree against the set of extracted variable results and assembles typed
CriterionResult and Finding objects. The output assembler composes these
into a top-level Assessment object, serializes it to a canonical JSON
document, validates the JSON against 14 JSON Schema Draft 2020-12
contracts, and performs referential integrity checks before writing any
output. Per-session outputs include a canonical JSON assessment document,
a tabular projection, and an HTML report. Cohort-level outputs
include a session summary, a long-format findings table, a variable
missingness matrix, and a finding prevalence table. Tabular and HTML
outputs are derived views of the canonical JSON and cannot contain
information absent from the canonical output.

### Technical validation

The engine was validated in three layers before empirical analysis.
Meta-schema validation confirmed that every JSON Schema is a valid
Draft 2020-12 schema. Specification validation loads and validates every
variable, criterion, and profile YAML against the corresponding input
schema at engine start, aborting execution before any dataset is
processed if inconsistencies are detected. A set of five synthetic BIDS
fixtures with frozen expected outputs serves as a golden output
regression suite; any change to output structure requires an explicit
golden update. Additional integration tests cover seven synthetic
scenarios including the reference case, missing reverse phase-encoding,
unknown phase-encoding direction, missing gradient files, bval/volume
count mismatch, missing readout metadata, and DICOM-to-BIDS field
strength conflict. All 28 tests pass on the frozen release.

---

## CIDUR cohort

The CIDUR cohort at the University of Rochester Medical Center comprises
DWI acquisitions from participants enrolled in a longitudinal imaging
study. Sessions were converted to BIDS using dcm2niix (Li et al., 2016)
with original DICOM archived alongside the BIDS representation. Six
sessions were excluded from the BIDS tree before Vecta assessment due to
acquisition-layer quality issues (corrupt DWI or multi-echo phase image
artifacts) documented in the conversion log; these are outside Vecta's
assessment scope. The resulting Vecta denominator comprised 62 sessions
across 61 subjects, spanning three scanner models at two field strengths:
Siemens Skyra (n = 16), Siemens MAGNETOM Vida Fit (n = 12), and GE SIGNA
Premier (n = 33) at 3.0 T, and one GE SIGNA Artist session at 1.5 T
(acquired at a combined PET/MR scanner). All sessions used a single-shell
DWI protocol (b = 1000 s/mm²). Gradient table size varied by vendor:
67 directions for Siemens sessions, 51–53 for GE sessions.

## Assessment execution

All Vecta assessments in this paper used specification version v0.1.0
(profile dwi_connectomics v0.1.0). Vecta-DWI v0.1 was applied to all 62
sessions using the vecta assess command with the dwi_connectomics profile. Original
DICOM was available for all sessions and was provided via the --dicom
argument, enabling evaluation of DICOM source-integrity variables
(VECTA.DWI.DICOM.*). All per-session assessments were written to
session-level output directories outside the BIDS tree. Cohort
aggregates were produced using the vecta aggregate command.

## Outcome labeling

QSIPrep 1.0.1.dev0+gee9aa2e.d20250115 processing outcomes were extracted from the QSIPrep
output tree using the vecta label-outcomes command. A session was
classified as QSIPrep success (QSIPREP_SUCCESS = True) if a
*_desc-preproc_dwi.nii.gz file was present in the session-level DWI
output directory; otherwise the session was classified as failure
(QSIPREP_SUCCESS = False). Vecta assessment states and QSIPrep outcomes
were joined on (subject_id, session_id) using the vecta join-outcomes
command. Two sessions (sub-009 ses-1 and ses-2) had no QSIPrep output
and were recorded as no outcome available. The reason for their absence
from the QSIPrep output tree was investigated separately and is
described in the Results.

## Detection approach comparison

To benchmark Vecta's criterion-level classification against simpler detection
approaches, four detection levels were evaluated against QSIPrep processing
outcomes on the 69 sessions with confirmed QSIPrep outcomes (sub-009 ses-1 and
ses-2 were excluded as no QSIPrep outcome was available; the extended outcome
cohort is described in Results). The
four levels were operationalized as follows:

- **Level 0 (BIDS Validator only):** A session was flagged if its
  BIDS_VALIDATOR_ERROR_COUNT variable was greater than zero.
- **Level 1 (Basic metadata completeness):** A session was flagged if its
  PhaseEncodingDirection state was unknown or TotalReadoutTime was absent.
- **Level 2 (Vecta Core):** A session was flagged if its readiness state was
  anything other than ready — that is, any Vecta criterion triggered under the
  dwi_connectomics profile.
- **Level 3 (Vecta with DICOM source integrity):** A session was flagged if
  any finding was present, including DICOM source-integrity criteria
  (VECTA-DWI-050, VECTA-DWI-060). This level requires original DICOM.

For each level, sessions were classified as flagged or not-flagged and
cross-tabulated against QSIPrep success. Standard 2×2 performance metrics were
computed: sensitivity (TP / (TP + FN)), specificity (TN / (TN + FP)), positive
predictive value (PPV; TP / (TP + FP)), and negative predictive value (NPV;
TN / (TN + FN)), where a positive is a flagged session and a case is a QSIPrep
failure. PPV is undefined when no sessions are flagged. Ninety-five percent
confidence intervals for all proportions were computed using the Wilson score
method (Brown et al., 2001). Computations were executed using Python 3.9 (NumPy 1.26.4) via
scripts/compute_ablation_table.py against the per-session vecta.json outputs
and the outcomes_long.tsv file produced by vecta join-outcomes.

## TrackTBI external validation cohort

External validation was conducted using BIDS-converted DWI sessions from
the Transforming Research and Clinical Knowledge in Traumatic Brain Injury
(TrackTBI) study ([TODO: replace Yue et al. 2013 with full cohort citation —
Yue et al. 2020 NEJM or FITBIR repository citation]), accessed via the Federal
Interagency Traumatic Brain Injury Research (FITBIR) repository. The cohort comprised
649 subjects contributing 1,275 sessions across two longitudinal time
points: 634 sessions at 2-week post-injury (2WK) and 641 sessions at
6-month post-injury (6MO).

Sessions were acquired across multiple sites on scanners from three
vendors: Siemens (584 sessions), GE (363 sessions), and Philips
(328 sessions). Siemens scanner software versions spanned three
generations: syngo MR B17 (304 sessions), syngo MR D13 (159 sessions),
and syngo MR E11 (98 sessions). Multiple scanner models were represented
across vendors and sites.

Original DICOM was not available for any TrackTBI session; accordingly,
assessment was conducted on BIDS representations only. DICOM
source-integrity criteria (VECTA-DWI-050, VECTA-DWI-060) were therefore
not evaluated for any session. DICOM-to-BIDS conversion provenance
(conversion tool, version, and per-session parameters) was not available
to the authors for the TrackTBI dataset; the systematic absence of
PhaseEncodingDirection in GE and Philips sidecars may reflect specific
scanner model, software version, or conversion tool behavior present in
this cohort rather than a universal vendor property.

QSIPrep preprocessing was conducted on the URMC HPC cluster across
multiple processing batches (g1, g2, g3) using QSIPrep
1.0.1.dev0+gee9aa2e.d20250115 (Singularity image qsiprep_1.0.0.sif,
which reports version 1.0.1.dev0 at runtime).
Outcomes were extracted from the QSIPrep output tree using the same
procedure as the CIDUR cohort: a session was classified as QSIPrep
success if a *_desc-preproc_dwi.nii.gz file was present in the
session-level DWI output directory; otherwise it was classified as
failure.

Sessions were excluded from performance metric computation in two
circumstances: (1) never_attempted sessions (n = 202) for which no
QSIPrep run was recorded, arising from HPC resource constraints (quota
incidents cancelling submitted jobs) and missing anatomical prerequisites
(absent or malformed T1w) unrelated to Vecta readiness findings; and
(2) two sessions (sub-TBI031004 ses-2WK, sub-TBI101003 ses-2WK) for
which QSIPrep was run on post-assessment sidecars with manually patched
PhaseEncodingDirection as part of a controlled remediation test — these
runs do not reflect standard pipeline behavior on the original sidecar.
The remaining 1,071 sessions with confirmed QSIPrep outcomes formed the
basis for all sensitivity, specificity, PPV, and NPV calculations; this
is the complete available sample from FITBIR and was not a pre-specified
target. Had the two excluded remediation-test sessions been run on their
original unmodified BIDS sidecars, both would be expected to fail
(VECTA-DWI-021 predicts QSIPrep crash at PhaseEncodingDirection
extraction) and including them would not change any performance metric.

False negatives — sessions rated ready_with_limitations that failed
QSIPrep — were categorized by examining QSIPrep workflow logs. A session
was classified as `fieldmap_error` if the log contained evidence that
QSIPrep attempted to use a non-EPI fieldmap acquisition (e.g., GRE
phasediff) and encountered absent or corrupt required metadata fields
(EchoTime1, EchoTime2, or Units). A session was classified as
`unidentified` if the log did not contain a diagnostic message
attributable to the DWI acquisition layer.

Vecta-DWI v0.1 was applied to all 1,275 sessions using the same
vecta assess command with the dwi_connectomics profile used for the CIDUR
cohort. Cohort aggregates were produced using the vecta aggregate command.

## OpenNeuro public dataset validation

To assess criterion behavior across independently published datasets,
Vecta-DWI v0.1 was applied to the DWI-only components of three OpenNeuro
datasets: Stockholm SleepyBrain (ds000201; van der Meer et al., 2020), a
sleep-deprivation study with 76 subjects on a GE DISCOVERY MR750 at 3.0 T
(b = 800 s/mm², 50 directions); MASiVar (ds003416; Cai et al., 2021), a
multisite, multi-scanner DWI variability dataset spanning Siemens, GE, and
Philips platforms with multi-shell protocols (b = 1000 and 2000 s/mm²)
across 308 sessions from 132 subjects; and ON-Harmony (ds004712; Karakuzu
et al., 2022), a longitudinal multi-scanner harmonization dataset covering
165 sessions from 20 subjects across Siemens, Philips, and GE platforms at
multiple sites. No DICOM was
available for any dataset; assessment was conducted on BIDS representations
only. Data were downloaded from the OpenNeuro S3 mirror
(s3://openneuro.org/) using the DWI-only subset (`sub-*/*/dwi/*`).
Cohort aggregates for each dataset were produced using the vecta aggregate
command.

## Pre-intervention sensitivity analysis

To assess Vecta's prospective sensitivity to the metadata issues that drove
post-conversion curation decisions, a pre-intervention BIDS dataset was
reconstructed by restoring the nine sessions removed from the CIDUR BIDS
tree by the protocol-variant selection step. These nine sessions were
excluded from the curated tree because their gradient direction counts or
BIDS filename direction entities did not match the site's expected protocol;
their sidecar JSON files, gradient tables, and NIfTI images were intact and
available in the curation hold directory. The reconstruction was strictly
additive: no files present in the 62-session post-intervention BIDS tree
were modified. Vecta-DWI v0.1 was applied to the resulting 71-session
pre-intervention dataset using the same vecta assess command and
dwi_connectomics profile as the primary analysis. Readiness distributions
were compared between pre-intervention (n = 71) and post-intervention (n = 62)
datasets. Because the protocol-variant selection script operated solely on
BIDS filename entities with no access to sidecar JSON content, Vecta's
sidecar-level assessment was conducted on entirely independent evidence from
the curation decisions, enabling a comparison of the two detection pathways.
