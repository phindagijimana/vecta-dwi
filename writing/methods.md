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
requires. We operationalize DBI through a versioned specification
executed by a deterministic engine, with scientific meaning encoded in
the specification rather than in code, so that the assessment contract
is independently reviewable and reproducible independently of the
software implementation.

### Specification structure

The Vecta-DWI v0.1 specification consists of versioned variables,
criteria, intended-use profiles, evidence entries, and numeric
tolerances. Variables are machine-readable measurement contracts, each
carrying a stable identifier, lifecycle layer, allowed value states,
source mappings with exact DICOM tags [CITE DICOM standard] and BIDS
fields [CITE BIDS spec], canonical units, validity constraints, and an
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
are rated review_required.

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
output. Per-session outputs include vecta.json (canonical assessment),
a tabular TSV projection, and an HTML report. Cohort-level outputs
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
study. Sessions were converted to BIDS using dcm2niix [CITE] with
original DICOM archived alongside the BIDS representation. Prior to
Vecta assessment, a subset of sessions was excluded during BIDS
conversion due to acquisition-layer quality issues: four subjects
(sub-016, sub-018, sub-047, sub-065) had their entire DWI acquisition
flagged as corrupt and removed from the BIDS tree, and two additional
sessions for sub-002 (ses-1 and ses-2) were removed due to DWI
acquisition artifacts (corrupt multi-echo phase images). These
exclusions occurred at the BIDS conversion stage and are documented in
excluded_scans.csv; they are not part of the 62-session Vecta assessment
denominator. Vecta's assessment scope begins at the BIDS representation
layer and does not re-evaluate conversion-stage exclusion decisions.

The 62 sessions assessed by Vecta comprised 61 subjects (sub-009
contributed two longitudinal sessions). Scanning was performed across
three scanner models at two field strengths: Siemens Skyra (n = 16
sessions), Siemens MAGNETOM Vida Fit (n = 12), and GE SIGNA Premier
(n = 33) at 3.0 T, and one GE SIGNA Artist session at 1.5 T (sub-002
ses-3, acquired at a PET/MR scanner). All sessions used a single-shell
DWI protocol (b = 1000 s/mm²). Gradient table size varied by vendor:
67 directions for Siemens sessions, 53 for GE SIGNA Premier, and 51 for
the GE SIGNA Artist session.

## Assessment execution

Vecta-DWI v0.1 (commit 295e477) was applied to all 62 sessions using
the vecta assess command with the dwi_connectomics profile. Original
DICOM was available for all sessions and was provided via the --dicom
argument, enabling evaluation of DICOM source-integrity variables
(VECTA.DWI.DICOM.*). All per-session assessments were written to
session-level output directories outside the BIDS tree. Cohort
aggregates were produced using the vecta aggregate command.

## Outcome labeling

QSIPrep v0.23.1 processing outcomes were extracted from the QSIPrep
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
