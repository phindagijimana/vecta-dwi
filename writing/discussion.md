# Discussion

In this study, we describe Vecta-DWI, a declarative framework for
assessing Data Birth Integrity of DWI datasets before preprocessing. We
applied the framework to 62 BIDS-converted sessions from the CIDUR
cohort and compared the resulting readiness states against QSIPrep
processing outcomes, and conducted an initial transportability pilot in
five participants from the TrackTBI dataset acquired at independent
institutions with a different protocol. A single criterion, VECTA-DWI-014 (complementary
phase-encoding reference unavailable), was triggered in all 34 GE
sessions and in no Siemens session, stratifying the cohort into a
ready tier and a ready_with_limitations tier. Among sessions processed
by QSIPrep, all 26 ready sessions produced valid preprocessed outputs,
and 33 of 34 ready_with_limitations sessions were successfully processed.
The single QSIPrep failure in the ready_with_limitations group had been
pre-flagged by VECTA-DWI-014 and was confirmed to fail on the same
condition — absence of a fieldmap for distortion correction.

These findings demonstrate that structural metadata and gradient file
integrity checks, performed without any preprocessing, are sufficient to
correctly stratify DWI sessions by downstream processing outcome in this
cohort. A comparison with a naive EPI fieldmap presence check — the
simplest possible baseline for VECTA-DWI-014 — showed identical
binary classification across all 62 CIDUR sessions. This equivalence
is expected in a cohort with no edge cases (no sessions with EPI
fieldmaps whose IntendedFor does not reference DWI, and no sessions
with non-EPI fieldmap types misidentified as reverse-PE capable). The
TrackTBI pilot provided one such edge case: a session with a GRE
phasediff fieldmap that a naive any-fmap check would misclassify,
while Vecta correctly identifies the absence of a reverse-PE EPI
acquisition. Beyond binary classification, Vecta uniquely provides
severity designation, lifecycle attribution, evidence basis, potential
downstream effects, and structured remediation steps — attributes that
a file-presence check cannot encode. Critically, BIDS Validator reported
zero fieldmap-related errors or warnings for any of the 34 sessions with
VECTA-DWI-014 findings: all passed BIDS validation, because the BIDS
specification does not require fieldmap acquisitions. This gap between
conformance and readiness is the central motivation for a dedicated
readiness assessment layer.

The criterion-level attribution provided by Vecta adds information
beyond a binary pass/fail by identifying the specific evidence layer
at which the problem originated and the recommended remediation. In the
case of VECTA-DWI-014, the finding identified that the limitation was a
site-level protocol decision rather than a data artifact, enabling
researchers to accurately characterize their distortion-correction
options rather than investigate potential data transfer or conversion
errors. Connectome output metrics were consistent with the non-blocking
designation: total streamline count was equivalent between ready (mean
7,811,000) and ready_with_limitations (mean 7,811,300) groups, and all
59 subjects with connectome data passed downstream QC. An observed
difference in mean tract-weighted FA (0.456 ready versus 0.475
ready_with_limitations) is attributable to the in-plane resolution
difference between vendor protocols (2 mm isotropic Siemens versus
1 mm in-plane GE) rather than to SDC status, and should not be
interpreted as evidence that distortion correction degrades FA. These
findings support the interpretation that VECTA-DWI-014 correctly
characterizes a methodological limitation without overstating its impact
on usable output in this cohort.

Two individual cases illustrate additional uses of the framework. The
first demonstrates a cross-layer inference capability that neither BIDS
Validator nor a fieldmap presence check can provide. For sub-009
(ses-1 and ses-2), both sessions were rated ready by Vecta — the DWI
data were intact in BIDS with 67-direction Siemens acquisitions and
reverse-PE fieldmaps present — yet neither appeared in the QSIPrep
output tree. A naive tool classifies the DWI data as ready and stops;
Vecta's structured, session-level assessment enables the next step:
cross-referencing the ready rating against the absence of pipeline
output surfaces the discrepancy and localizes the block to a layer
outside Vecta's current scope. Investigation confirmed that a T1w
motion artifact documented for ses-2 at BIDS conversion led to
subject-level exclusion from QSIPrep — an anatomical quality decision
at a layer Vecta does not currently evaluate. Without session-level
readiness attribution, distinguishing this scenario (DWI intact,
processing excluded for anatomical reasons) from a silent DWI data
problem would require manual inspection of per-session output
directories across the entire cohort. For sub-044 (ses-2), QSIPrep produced only
anatomical derivatives without DWI outputs, but subject-level QC
metrics reported passing status because they reflected ses-1, for which
full DWI preprocessing succeeded. The session-level granularity of
Vecta's assessment, combined with the explicit lifecycle attribution of
its findings, would allow a researcher to distinguish this type of
processing gap from a data integrity issue without manual review of each
session's output directory.

In the Stockholm SleepyBrain dataset, both VECTA-DWI-014 and VECTA-DWI-021
co-triggered for all 76 sessions — a pattern not observed in CIDUR. The
CIDUR GE sessions also lack a reverse-PE EPI acquisition, yet VECTA-DWI-021
did not trigger there because the CIDUR scanners export TotalReadoutTime in
their sidecar JSON files. The difference illustrates that criterion fire
patterns are informative about acquisition and conversion practices across
sites: the same physical limitation (no SDC) can co-occur with different
metadata completeness states, and both have implications for pipeline
configurability. In MASiVar, VECTA-DWI-030 (gradient file missing or
unparseable) triggered in five sessions, the first real-world triggering of
this criterion observed in this study. S3 source inspection confirmed that
the corresponding .bvec files and NIfTI images were never deposited, indicating
a data completeness gap at the source rather than a conversion artifact; these
five sessions would fail any downstream pipeline at gradient loading. In
ON-Harmony, the single VECTA-DWI-014 finding was driven not by absent
bidirectional acquisitions but by a phase-encoding axis inconsistency:
the dir-AP and dir-PA DWI files were acquired on different axes (j- and i
respectively) and cannot serve as complementary reverse-PE references despite
their filename labels. A filename-label-only check would misclassify this
session as SDC-capable. These findings across three independent datasets
collectively demonstrate that criterion fire patterns vary systematically
across sites, protocol choices, and conversion practices, and that metadata-aware
evaluation captures readiness-relevant distinctions that file-presence or
label-based checks cannot.

This study has several notable limitations. A primary limitation is that
the primary validation cohort comprises a single site with two vendors
but limited protocol diversity: all sessions used single-shell DWI at
b = 1000 s/mm², and the vendor-stratified readiness split reflects a
single protocol-level difference. An initial transportability pilot
using five participants from the TrackTBI dataset — acquired at different
institutions with Siemens TrioTim and Skyra scanners at b = 1300 s/mm²
— produced results consistent with the CIDUR findings: VECTA-DWI-014
triggered in all sessions and all 2-week sessions processed successfully
by QSIPrep. The three OpenNeuro datasets provide broader external evidence:
SleepyBrain and MASiVar demonstrate criterion behavior in datasets with
sparse or absent TotalReadoutTime metadata, while MASiVar is a multi-shell
protocol (b = 1000 and 2000 s/mm²), demonstrating that the framework
operates correctly on multi-shell acquisitions. The full TrackTBI cohort
(approximately 600 sessions across multiple sites) will constitute the
formal outcome-based external validation.
A second limitation is that Vecta-DWI v0.1 evaluates structural metadata
and gradient file integrity but does not include image quality assessment.
Sessions rated ready may still have image quality problems — motion
artifacts, thermal noise, signal dropout — that are not detectable from
BIDS metadata alone. Image quality assessment, as provided by tools such
as MRIQC [CITE] or eddyqc [CITE], addresses a complementary and
downstream evidence layer; we regard these tools as orthogonal to
Vecta's scope rather than competitors. A third limitation is that
DICOM-source module variables (VECTA-DWI-050, VECTA-DWI-060) require
original DICOM to be available alongside the BIDS dataset. Sites that
retain only the BIDS representation will receive lower assessment
completeness scores for the source-integrity criteria, which will return
unknown rather than evaluated. A fourth limitation is that the
probability that a finding causes downstream failure has not been
calibrated in this cohort; the observed associations between findings
and outcomes should be interpreted as exploratory rather than
predictive.

Future work will address several of these limitations. The initial TBI
pilot is consistent with criterion transportability; the full TrackTBI
cohort will provide sufficient power to formally test whether the
VECTA-DWI-014 finding-to-outcome association replicates across a
multi-site, multi-scanner, multi-protocol dataset, and to evaluate
criteria that did not trigger in CIDUR.
An image quality domain incorporating MRIQC-derived metrics is planned
for Vecta-DWI v0.2, enabling joint assessment of metadata integrity and
image quality in a single framework. Extension to multi-shell protocols
will require updating the shell-count derivation formula to use a more
robust b-value clustering approach suitable for acquisitions with
multiple closely spaced shells. Extension to other DWI-relevant
preprocessing pipelines and ultimately to other MRI modalities —
functional MRI, arterial spin labeling, quantitative MRI — is supported
by the modality-agnostic design of the criteria engine and output
schema, but will require new specification components (variables,
criteria, and profiles) developed and validated for each modality
independently. We envision Vecta as a pre-processing readiness layer
that, if integrated into neuroimaging workflows, could surface data
integrity issues at the point where remediation is still possible —
before computational resources have been committed and before
downstream analyses have been performed on data of uncertain integrity.
