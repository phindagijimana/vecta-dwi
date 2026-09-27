# Discussion

In this study, we describe Vecta-DWI, an implementation of the Data
Birth Integrity (DBI) framework for DWI preprocessing readiness, and
validate it empirically across five datasets spanning 1,275 sessions and
three scanner vendors. The results serve two purposes: they demonstrate
that Vecta-DWI is a practical and generalizable tool, and they provide
evidence that the DBI design approach itself — assessing readiness
declaratively against an intended-use profile, handling unknown states
safely, and version-pinning the assessment contract — produces a
framework whose outputs correctly stratify sessions by preprocessing
outcome at scale. We
applied the framework to 71 CIDUR sessions spanning three readiness
states and confirmed QSIPrep 1.0.1.dev0 outcomes for 69 sessions. Three
QSIPrep failures were observed across three readiness states; all three
occurred in sessions Vecta had flagged as non-ready. The failure rate
was 0% for ready sessions (0/26), 2.4% for ready_with_limitations
sessions (1/41), and 100% for review_required sessions (2/2) — a
monotonically ordered risk stratification. However, the three failures
are mechanistically heterogeneous. The two review_required failures
(sub-036 and sub-069) have a confirmed direct cause: QSIPrep crashed
because PhaseEncodingDirection was absent, triggering a NaN string
operation at the DWI parameter-extraction step before the SDC
workflow was instantiated. This is the condition VECTA-DWI-021
precisely characterizes. The single ready_with_limitations failure
(sub-076) is less clear: QSIPrep passed parameter extraction,
completed anatomical preprocessing, and entered the eddy step, where
the available log (truncated at 844 lines) does not capture the crash.
Sub-076 has a valid signed PhaseEncodingDirection and its fieldmap
absence is shared by 40 other GE sessions that succeeded. The most
likely cause is a data-specific eddy failure — possibly related to
the unusually low b0 count (3) or slightly non-standard gradient count
(50 b1000 directions vs 51–53 in other GE sessions) — rather than the
fieldmap-absence condition VECTA-DWI-014 characterizes.

These findings demonstrate that structural metadata and gradient file
integrity checks, performed without any preprocessing, are sufficient to
correctly stratify DWI sessions by downstream processing outcome in this
cohort. A comparison with a naive EPI fieldmap presence check — the
simplest possible baseline for VECTA-DWI-014 — showed identical
binary classification across all 62 CIDUR sessions. This equivalence
is expected in a cohort with no edge cases (no sessions with EPI
fieldmaps whose IntendedFor does not reference DWI, and no sessions
with non-EPI fieldmap types misidentified as reverse-PE capable). The
1,275-session TrackTBI external validation cohort provided one such
edge case: a session with a GRE phasediff fieldmap (TBI011204) that a
naive any-fmap check would misclassify as SDC-capable,
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

The perfect vendor stratification observed in the TrackTBI external
validation — Siemens sessions uniformly receiving ready_with_limitations
(VECTA-DWI-014) and GE and Philips sessions uniformly receiving
review_required (VECTA-DWI-021 + VECTA-DWI-001) — reveals a systematic
difference in DICOM-to-BIDS metadata generation across the scanners
represented in this dataset. BIDS conversion provenance (conversion tool,
version, and per-session parameters) was not available to the authors for
the TrackTBI dataset; the attribution of PhaseEncodingDirection absence to
vendor versus specific scanner model, software version, or conversion tool
behavior cannot be confirmed from the data available. Within this cohort,
Siemens sidecar files carried a signed PhaseEncodingDirection field and GE
and Philips sidecar files did not, a pattern that held without exception
across all 1,275 sessions. Regardless of attribution, this is not a
session-specific artifact but a cohort-level data integrity pattern that
Vecta surfaces systematically. The implications for multi-site studies using
GE or Philips scanners are significant: VECTA-DWI-021 will flag sessions
without PhaseEncodingDirection, and without this field QSIPrep cannot
proceed with susceptibility distortion correction. Researchers planning
multi-site DWI studies with mixed-vendor acquisitions should audit
PhaseEncodingDirection completeness before initiating preprocessing, and
site-level remediation (re-exporting from DICOM with an updated dcm2niix
version, or manually populating the field from acquisition parameters) may
be required at scale.

The detection approach comparison (Table 4) illustrates the cost of
under-specification and demonstrates a critical distinction between
metadata-layer and acquisition-layer failure modes. Level 0 (BIDS
Validator errors) flags no sessions; all three failures pass structural
conformance validation. Level 1 (PhaseEncodingDirection absent) captures
two of the three failures — those caused by the metadata-absence mode
(VECTA-DWI-021) — but has a systematic blind spot for the
acquisition-absence mode: the VECTA-DWI-014 failure (sub-076) carried
a valid signed PhaseEncodingDirection and TotalReadoutTime and was
invisible to any metadata-completeness check. Level 2 (Vecta Core)
captures all three failures because VECTA-DWI-014 and VECTA-DWI-021
are independent criteria evaluating complementary evidence layers.
Sensitivity is 0.000 (Level 0), 0.667 [0.208, 0.939] (Level 1),
and 1.000 [0.439, 1.000] (Level 2); NPV is 0.957, 0.985, and 1.000
respectively. These values rest on n=3 confirmed failures across n=69
confirmed sessions; the sensitivity and NPV confidence intervals are
correspondingly wide and should be interpreted as illustrative of
criterion behavior rather than precise population estimates. The
positive predictive value of 0.070 at Level 2 warrants careful
interpretation: VECTA-DWI-014 makes a structural claim about data
properties — specifically, that no reverse phase-encoding reference
is available for susceptibility distortion correction — not a claim that
the pipeline will abort. The 40 GE sessions classified as false positives
did not receive SDC; QSIPrep completed via a fallback path, but the
absence of distortion correction is a methodological limitation of those
outputs, not a false alarm. Level 3 is identical to Level 2 because no
DICOM source-integrity criteria triggered in this cohort.

Controlled defect injection confirmed VECTA-DWI-021 detection and
revealed that PhaseEncodingDirection absence produces two distinct
QSIPrep failure modes depending on session context. The real-world
sessions (sub-036, sub-069) crashed immediately at `get_acq_parameters_df()`
with an `AttributeError`. The injection session produced a silent failure:
QSIPrep reported "finished successfully!" with exit code 0 but produced
only anatomical derivatives — the DWI session was excluded from the
workflow during grouping without any error message. The silent-skip
mode is operationally more dangerous than a crash, because no failure
signal reaches the researcher. Vecta-DWI-021 correctly identifies
the underlying condition in both cases.

The criterion-level attribution provided by Vecta adds information
beyond a binary pass/fail by identifying the specific evidence layer
at which the problem originated and the recommended remediation — an
approach consistent with quality assurance frameworks that have
demonstrated measurable impact on downstream DWI metrics
(Roalf et al., 2016). In the
case of VECTA-DWI-014, the finding identified that the limitation was a
site-level protocol decision rather than a data artifact, enabling
researchers to accurately characterize their distortion-correction
options rather than investigate potential data transfer or conversion
errors. Connectome output metrics were consistent with the non-blocking
designation: all 58 subjects with available connectome data achieved
the fixed 10-million-streamline tractography target and passed
downstream QC regardless of SDC status, confirming that VECTA-DWI-014
correctly characterizes the absent distortion correction as a
methodological limitation rather than a connectome yield predictor.

**Recommended integration into neuroimaging workflows.** Vecta-DWI is
designed to be run at BIDS conversion time, before any preprocessing
batch is submitted. The intended workflow is: (1) convert DICOM to BIDS;
(2) run `vecta assess` with the appropriate intended-use profile and,
where available, the original DICOM directory; (3) review the cohort
aggregate — sessions rated review_required should be inspected for
PhaseEncodingDirection and TotalReadoutTime completeness before batching;
sessions rated ready_with_limitations can proceed to preprocessing with
documentation of the specific limitation (e.g., no SDC will be applied)
and downstream interpretation adjusted accordingly; sessions rated ready
can proceed without qualification. This assessment adds minutes per
session and requires no preprocessing to have run; it surfaces fixable
metadata gaps at the point where remediation is still practical — before
computational resources have been committed and before downstream
analyses depend on potentially incomplete outputs. For the PhaseEncoding
Direction absence pattern observed in all GE and Philips sessions of the
TrackTBI cohort, the assessment output provides a specific remediation
path: re-export from DICOM with a dcm2niix version that populates the
signed direction field, or manually populate from acquisition parameters
documented in the scanning protocol.

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

The pre-intervention analysis provides a prospective validity check that is
mechanistically distinct from the primary outcome comparison. The curation
protocol that produced the 62-session denominator operated on BIDS filename
entities only, with no access to sidecar JSON content. Vecta's assessment
of the reconstructed 71-session pre-intervention dataset flagged both
subsequently excluded sessions as review_required using sidecar-level evidence
— the absence of the signed PhaseEncodingDirection field — independently of
and prior to any filename-label decision. The root cause (dcm2niix populating
only the unsigned PhaseEncodingAxis field on two Siemens Skyra acquisitions)
is invisible to BIDS Validator and undetectable from BIDS filenames alone.
Vecta's finding directly predicts the downstream preprocessing consequence:
without a signed PhaseEncodingDirection, QSIPrep crashes at the DWI
parameter-extraction step (`get_acq_parameters_df` in `merge.py`) —
confirmed empirically in the CIDUR pre-intervention runs for sub-036 and
sub-069, and via controlled defect injection (def-021). This convergence
of three independent pathways — Vecta sidecar finding, curation exclusion
via filename detection, and confirmed QSIPrep failure — supports the face
validity of VECTA-DWI-021
and demonstrates that sidecar-level metadata assessment detects preprocessing
prerequisites that neither conformance checking nor filename inspection can
resolve. The readiness regression in sub-002 ses-3, where the curation step
unintentionally dissolved a complementary-PE relationship visible only in
sidecar metadata, additionally illustrates that filename-entity-based curation
can introduce DBI limitations that are not surfaced by the curation process
itself but are detectable by Vecta at the metadata layer.

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
single protocol-level difference. The TrackTBI cohort (649 subjects, 1,275 sessions; Siemens 584,
GE 363, Philips 328) provides independent outcome-based external
validation across three vendors and multiple sites. Vecta produced
perfect vendor stratification: all Siemens sessions received
ready_with_limitations (VECTA-DWI-014; no reverse-PE EPI), while all GE
and Philips sessions received review_required (VECTA-DWI-021 +
VECTA-DWI-001; absent PhaseEncodingDirection). This vendor-level
separation reflects a systematic, cohort-level difference in DICOM-to-BIDS
metadata generation; because BIDS conversion provenance was not available
for TrackTBI, the pattern is reported as an empirical observation rather
than attributed to a specific conversion tool or vendor behavior. From
1,071 sessions with confirmed QSIPrep outcomes (627 confirmed failures),
sensitivity was 0.989 (95% CI [0.977, 0.995]) and NPV was 0.984
(95% CI [0.968, 0.992]). The three OpenNeuro datasets
provide broader external evidence: SleepyBrain and MASiVar demonstrate
criterion behavior in datasets with sparse or absent TotalReadoutTime
metadata, while MASiVar is a multi-shell protocol (b = 1000 and
2000 s/mm²), demonstrating that the framework operates correctly on
multi-shell acquisitions.
A second limitation is that Vecta-DWI v0.1 evaluates structural metadata
and gradient file integrity but does not include image quality assessment.
Sessions rated ready may still have image quality problems — motion
artifacts, thermal noise, signal dropout — that are not detectable from
BIDS metadata alone. Image quality assessment tools such as MRIQC
(Esteban et al., 2017) and eddyqc (Bastiani et al., 2019) address a
complementary downstream evidence layer: MRIQC derives image quality
metrics (SNR, framewise displacement, B0 uniformity) from the acquired
image data, while Vecta evaluates metadata integrity before the image
is ever passed to a pipeline. As described in Results, MRIQC DWI image
quality metrics do not report PhaseEncodingDirection completeness,
fieldmap availability, or gradient file integrity — the conditions Vecta
specifically evaluates. A session can pass MRIQC (image quality
acceptable) and fail Vecta (metadata absent), or fail MRIQC (motion
artifact) and pass Vecta (metadata intact). These tools are orthogonal
and designed to be used in sequence: Vecta at BIDS conversion time to
confirm structural readiness, MRIQC after preprocessing to characterize
image quality. An image quality domain is planned for Vecta-DWI v0.2. A third limitation is that
DICOM-source module variables (VECTA-DWI-050, VECTA-DWI-060) require
original DICOM to be available alongside the BIDS dataset. Sites that
retain only the BIDS representation will receive lower assessment
completeness scores for the source-integrity criteria, which will return
unknown rather than evaluated. A fourth limitation is that the
sensitivity and NPV estimates from the primary cohort rest on n=3
confirmed failures across 69 sessions; confidence intervals are
correspondingly wide. Additionally, the CIDUR cohort served as the primary
development context for the criteria — the PhaseEncodingDirection absence
issue (VECTA-DWI-021) was known from curation records before criterion
specification was finalized — making this an in-sample evaluation. The
performance estimates therefore reflect criterion behavior on familiar
data rather than out-of-sample generalization. The TrackTBI cohort
(649 subjects, 1,275 sessions, three vendors) provides this independent
external validation: sensitivity 0.989 (95% CI [0.977, 0.995]) and
NPV 0.984 (95% CI [0.968, 0.992]) were estimated from 1,071 sessions
with confirmed outcomes across a cohort developed independently of the
Vecta criterion specification. The MASiVar prequal-v1.0.0 derivatives show that all five VECTA-DWI-030
sessions produce no preprocessed NIfTI output; however, this pattern
reflects a sub-cohort-level preprocessing incompatibility affecting all
sessions from those scanner groups, not an outcome specific to the
gradient file deficiency. The primary validation for VECTA-DWI-030
therefore rests on S3 source confirmation of absent bvec files. The
observed associations between Vecta findings and preprocessing outcomes
should be interpreted as exploratory evidence supporting criterion face
validity rather than calibrated predictive performance.
Broader analysis variability in neuroimaging — where the same dataset
analyzed by different teams produces substantially different conclusions
(Botvinik-Nezer et al., 2020) — further motivates prospective readiness
certification as a prerequisite to analysis.
A fifth limitation is that Vecta's assessment scope begins at the BIDS
representation layer and does not evaluate the correctness or
completeness of the DICOM-to-BIDS conversion. The CIDUR dataset
represents standard institutional BIDS conversion conditions: dcm2niix
produces inline derived image series (ADC, diffusion tensor maps) that
require exclusion, co-acquired protocol variants that require selection,
and fieldmap IntendedFor fields that require a post-conversion population
step. Vecta assesses the BIDS representation as presented and correctly
reflects the state of the tree; it cannot determine from the BIDS layer
alone whether upstream data selection decisions were applied or what
criteria governed them. The pre-intervention analysis in this paper
directly addresses this boundary: Vecta correctly detects the
metadata-integrity failures that remained visible in the sidecar, while
protocol-selection exclusions (non-standard gradient direction count)
are recognized as outside DBI scope. Extending Vecta to include
conversion-boundary traceability — derived map detection, multi-series
disambiguation, and session-to-DICOM mapping validation — is a priority
for future versions and would make the assessment scope contiguous from
DICOM through BIDS.
A sixth limitation is that outcome-based validation was conducted
against one pipeline only (QSIPrep 1.0.1.dev0). The readiness criteria
are designed around requirements common to BIDS-App DWI pipelines —
PhaseEncodingDirection for SDC, TotalReadoutTime for SDC calibration,
gradient files for DWI modeling — but the claim that Vecta findings
predict failure has been empirically tested only against QSIPrep.
The two blocking failure modes identified in CIDUR (absent PED causing
QSIPrep crash, absent fieldmap causing no-SDC fallback) are not
QSIPrep-specific: any pipeline that reads PhaseEncodingDirection from
the BIDS sidecar (fMRIPrep, dMRIprep, Tractoflow) will encounter the
same NaN-handling issue, and the fieldmap-absence condition is a BIDS-
level acquisition property, not a QSIPrep behavior. Confirming that
these criteria predict failure in at least one additional pipeline
(fMRIPrep or MRtrix3-based workflow) is a priority for v0.2 validation.

A seventh limitation, revealed by the TrackTBI external validation, is
that Vecta does not currently evaluate the metadata integrity of
non-EPI fieldmap acquisitions. The 7 false negatives in the TrackTBI
cohort — sessions rated ready_with_limitations (VECTA-DWI-014) that
failed QSIPrep — had a failure cause of fieldmap_error: corrupt metadata
on GRE phasediff fieldmap acquisitions. VECTA-DWI-014 correctly
identifies the absence of a reverse-PE EPI reference; however, it does
not inspect the metadata completeness of non-EPI fieldmaps that are
present. A session carrying a GRE phasediff fieldmap with corrupt or
incomplete metadata will be rated ready_with_limitations (correctly
noting the absence of reverse-PE EPI), but may still fail QSIPrep if
the pipeline attempts to use the non-EPI fieldmap and encounters the
metadata deficiency. This represents a criterion scope gap: a new
criterion evaluating phasediff fieldmap metadata completeness —
verifying required fields such as EchoTime1, EchoTime2, and Units —
would close this gap and reduce these false negatives.

Future work will address several of these limitations. The TrackTBI
external validation encompassed 649 subjects, 1,275 sessions across
three vendors; sensitivity 0.989 and NPV 0.984 were estimated from 1,071
sessions with confirmed QSIPrep outcomes, confirming that Vecta criteria
replicate across independent institutions and scanner platforms. The
7 false negatives in that cohort point to the next criterion development
priority: a phasediff fieldmap metadata completeness check (verifying
EchoTime1, EchoTime2, and Units fields) to close the non-EPI fieldmap
metadata scope gap identified above.
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
that, if integrated into neuroimaging workflows consistent with best
practices for neuroimaging data management (Nichols et al., 2017),
could surface data integrity issues at the point where remediation is
still possible — before computational resources have been committed and
before downstream analyses have been performed on data of uncertain
integrity.
