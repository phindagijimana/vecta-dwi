# Discussion

In this study, we describe Vecta-DWI, a declarative framework for
assessing Data Birth Integrity of DWI datasets before preprocessing. We
applied the framework to 62 BIDS-converted sessions from the CIDUR
cohort and compared the resulting readiness states against QSIPrep
processing outcomes. A single criterion, VECTA-DWI-014 (complementary
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
cohort. The criterion-level attribution provided by Vecta adds
information beyond a binary assessment of pipeline success by identifying
the specific evidence layer at which the problem originated and the
recommended remediation. In the case of VECTA-DWI-014, the finding
identified that the limitation was a site-level protocol decision rather
than a data artifact, enabling researchers to accurately characterize
their distortion-correction options rather than investigate potential
data transfer or conversion errors. This type of actionable, attributed
assessment is not provided by BIDS validation, which would not flag the
absence of a fieldmap as an error for a session that does not declare
one as required, nor by downstream QC tools such as eddyqc, which
require the pipeline to have already processed the session.

Two individual cases illustrate additional uses of the framework. For
sub-009 (ses-1 and ses-2), both sessions were rated ready by Vecta —
the DWI data were intact in BIDS with 67-direction Siemens acquisitions
and reverse-PE fieldmaps present — yet neither appeared in the QSIPrep
output tree. Cross-referencing the Vecta ready rating against the
missing pipeline output identified this discrepancy and exposed the
reason: a T1w motion artifact documented for ses-2 at BIDS conversion
led to subject-level exclusion from the QSIPrep batch, an anatomical
decision outside Vecta's current DWI-focused scope. Vecta correctly
characterized the DWI data as ready; the processing gap was attributable
to a separate evidence layer (anatomical image quality) that Vecta does
not currently evaluate. For sub-044 (ses-2), QSIPrep produced only
anatomical derivatives without DWI outputs, but subject-level QC
metrics reported passing status because they reflected ses-1, for which
full DWI preprocessing succeeded. The session-level granularity of
Vecta's assessment, combined with the explicit lifecycle attribution of
its findings, would allow a researcher to distinguish this type of
processing gap from a data integrity issue without manual review of each
session's output directory.

This study has several notable limitations. A primary limitation is that
the internal validation cohort comprises a single site with two vendors
but limited protocol diversity: all sessions used single-shell DWI at
b = 1000 s/mm², and the vendor-stratified readiness split reflects a
single protocol-level difference. Generalizability to multi-shell
acquisitions, non-standard b-values, or sites with different fieldmap
practices has not been demonstrated. The CIDUR cohort also does not
include independent external validation data; the TBI transport cohort
(approximately 600 sessions across multiple sites) will provide the
first external transportability test and is the subject of ongoing work.
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

Future work will address several of these limitations. The TBI transport
analysis will test whether criteria developed on the CIDUR cohort
transport to an independent multisite dataset, treating non-transporting
criteria as first-class results rather than failures to be suppressed.
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
