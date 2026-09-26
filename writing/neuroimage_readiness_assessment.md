# Readiness Assessment: Vecta-DWI Manuscript
_Against NeuroImage main journal standards — honest pre-submission review_

---

## Current journal tier

**As submitted today: NeuroImage: Reports / Neuroinformatics tier.**

Not yet at NeuroImage main journal. The TrackTBI scale (N=1,071 confirmed
outcomes, 627 failures) is genuinely large for a DWI QC paper and pushes the
work above JOSS or Frontiers in Neuroinformatics. The blocking gap is the
absence of a comparison to MRIQC, which any NeuroImage reviewer will ask for
immediately. Once that comparison is added and the DBI construct is better
justified, the paper is competitive for NeuroImage main.

---

## Scientific soundness

### Strengths

- **TrackTBI validation is real.** 1,071 confirmed outcomes, 627 failures,
  sensitivity 0.989 [0.977, 0.995] — these are tight CIs on a large enough
  N that the estimate is stable. Perfect vendor stratification across 1,275
  sessions with zero cross-tier misclassifications is a striking finding that
  survives scrutiny.
- **Two mechanistically distinct failure modes** (PhaseEncodingDirection
  absence causing pre-SDC crash, vs. fieldmap absence causing no-SDC fallback)
  are correctly identified and empirically confirmed with sub-036 / sub-069
  vs. sub-076. The QSIPrep crash traceback (`get_acq_parameters_df` on NaN
  PED) is documented precisely.
- **Pre/post-intervention analysis** is methodologically sound. The curation
  protocol (filename label–based) operated on independent evidence from
  Vecta's sidecar-metadata assessment. The two flagged sessions being
  independently caught by both pathways is a valid concordance result.
- **Open-source, versioned specification.** The YAML-based declarative spec is
  independently reviewable. JSON Schema contracts, golden regression tests, and
  determinism-by-design are appropriate for a methods tool.

### Weaknesses

**W1 (critical): CIDUR N=3 failures.** The sensitivity=1.000 [0.439, 1.000]
for CIDUR is correct but statistically empty — the CI covers 56% of the unit
interval. The paper correctly labels CIDUR as "in-sample development context"
and "mechanistically illustrative," but reviewers will read the Level 0-3
detection comparison (Table 4) and see that the paper's mechanistic claim rests
on 3 events. The TrackTBI analysis is where the science actually lives; the
manuscript framing needs to reflect this more completely — CIDUR should be
described as illustrating *why* the criteria were designed as they were, not as
a validation dataset.

**W2 (critical): No MRIQC comparison.** The introduction correctly says MRIQC
"characterizes image quality after acquisition rather than structural
prerequisites before preprocessing." That's true — but reviewers will ask
for empirical evidence on the same dataset. A single table showing what MRIQC
reports (DWI image quality metrics) for the review_required and failed sessions
vs. what Vecta reports would suffice. The point — that MRIQC cannot detect
absent PhaseEncodingDirection or absent fieldmap acquisitions before
preprocessing — can be made in ~1 paragraph with supporting data.

**W3 (moderate): Outcome measure is pipeline success, not data quality.** The
outcome is QSIPrep boolean success/failure. This is a reasonable proxy but
not ground truth. Two sessions can both succeed QSIPrep while producing outputs
of very different scientific quality (e.g., one with SDC, one without). The
paper uses "QSIPrep failure" as the outcome, which correctly operationalizes
"cannot run" but does not address "ran but produced inferior output." The
connectome section was meant to address this but provides no useful signal
(tractography yield equivalence at 10M streamlines is expected for
ready_with_limitations sessions and doesn't distinguish scientific quality
from run-or-not-run).

**W4 (moderate): False negative classification is post-hoc.** The 5 false
negatives categorized as "fieldmap_error" (non-EPI GRE phasediff with
corrupt metadata) were classified by examining QSIPrep logs after outcome
was known. No pre-specified classification criteria exist. This is honest
but reviewers may see "outside Vecta's current criterion scope" as motivated
framing. Need either: (a) pre-specified error taxonomy defined in Methods,
or (b) explicit acknowledgment that the post-hoc classification is
exploratory.

**W5 (moderate): DBI construct lacks empirical validation.** The four formal
properties of DBI (intended-use conditionality, null safety, determinism,
version-pinning) are design choices, not empirically demonstrated properties.
A reviewer will ask: "Do these properties actually matter in practice? Can you
show a case where null-safety prevented a false negative, or where
version-pinning caught a specification drift?" The pre/post-intervention
analysis partially answers the intended-use conditionality point; the others
need concrete examples or the construct section needs to be framed as a
design rationale rather than a validated framework.

**W6 (minor): No prospective validation.** The paper claims Vecta "enables
targeted remediation." The two pre-intervention sessions (sub-036, sub-069)
were submitted post-assessment and confirmed to fail — this is valuable. But
there is no example of: "Vecta flagged session X, we remediated it, it then
succeeded." The closest available case is the 2 manually-patched TrackTBI
sessions (excluded from performance metrics), which would serve this purpose
but are excluded precisely because they were patched.

**W7 (minor): TrackTBI BIDS conversion provenance unknown.** For a paper
specifically about data birth integrity from acquisition through BIDS
conversion, not knowing the conversion tool, version, or parameters for the
external validation dataset is a structural irony reviewers will notice.
The paper acknowledges this in Methods; it needs to also appear as a named
limitation in Discussion with specific interpretive consequences (e.g., the
vendor stratification finding may reflect this cohort's specific dcm2niix
version or site settings rather than a universal vendor behavior).

---

## Experimental soundness

### Strengths

- Five independent datasets spanning 5 vendors, 15+ scanner models, 3 imaging
  protocols, and 3 institutions — the breadth is appropriate.
- BIDS Validator comparison is concretely executed: 0 fieldmap-related errors
  for any of the 34 VECTA-DWI-014 sessions. This is a real finding, not a
  hypothetical.
- The MASiVar VECTA-DWI-030 case (bvec files absent from S3 source confirmed
  by S3 inspection) is an independent external validation of criterion face
  validity.
- Technical validation layers (meta-schema, spec validation, golden regression
  suite, 28 integration tests) are appropriate for a methods tool.

### Weaknesses

**E1 (critical): CIDUR and TrackTBI are tested against one pipeline only
(QSIPrep).** The paper's readiness criteria are framed as pipeline-agnostic
("DWI preprocessing readiness") but validated only against QSIPrep. Reviewers
will ask: do these criteria predict failure in MRtrix3 pipelines, fMRIPrep,
or dMRIprep? The `dwi_connectomics` profile is named correctly (it's a
profile, not a universal claim) but the abstract and introduction language is
broader than the validation supports. Either restrict claims to QSIPrep or
show that VECTA-DWI-001 (PE direction unknown) also causes failure in at
least one other pipeline.

**E2 (moderate): OpenNeuro datasets have no QSIPrep outcome data.** The three
OpenNeuro datasets demonstrate criterion activation patterns but cannot be used
to validate predictive performance. This is stated, but the MASiVar prequal
output analysis (prequal derivatives with 0 NIfTI for bvec-absent sessions) is
presented as partial validation when it actually conflates two confounds: the
bvec absence (VECTA-DWI-030) and the TotalReadoutTime absence (VECTA-DWI-021,
all MASiVar). The sentence "the prequal derivative pattern therefore reflects a
sub-cohort-level preprocessing incompatibility rather than an outcome specific
to the VECTA-DWI-030 finding" is honest but means the MASiVar prequal data
cannot be used as evidence for VECTA-DWI-030 criterion validity.

**E3 (minor): Connectome section adds no informative result.** "All 58 subjects
achieved the tractography target and passed downstream QC" is the expected
result for QSIPrep-successful sessions. It does not address the scientific
question of whether SDC status affects tract reliability or connectivity
estimates. For NeuroImage, either extend this to show tract-level or
connectivity-level differences by SDC status, or remove the section entirely
and replace with a paragraph on the scope boundary: Vecta assesses what the
pipeline *needs*, not what the pipeline *produces*.

---

## Statistical soundness

### Strengths

- Wilson score CIs throughout — correct for proportions, avoids normal
  approximation failure at extremes.
- Explicit numerator/denominator for every metric — full reproducibility.
- Proportional imputation sensitivity analysis for never_attempted exclusion
  is well-designed; results within 0.002 of observed values are reassuring.
- Conservative direction disclosure for the never_attempted asymmetry is
  appropriate and correct.

### Weaknesses

**S1 (critical): No formal comparison between detection levels.** Table 4
presents point estimates and CIs for 4 detection levels but no test of whether
Level 2 sensitivity is significantly greater than Level 1. With N=3 failures
the CIs overlap substantially (Level 1: [0.208, 0.939]; Level 2: [0.439, 1.000])
and no conclusion about superiority can be supported statistically. This is
fine if the comparison is framed as mechanistically illustrative (which the
caption does), but the Results text says "Only a framework that independently
evaluates both conditions achieves full sensitivity" — this causal claim goes
beyond what 3 events support. Reframe as: "In this n=3 sample, the two
failure modes required independent criteria; statistical power to claim
superiority is not available from this cohort alone."

**S2 (moderate): TrackTBI sensitivity 0.989 reflects a specific exclusion
decision.** The 2 post-remediation test sessions (excluded) and the 202
never_attempted sessions each involve analytical choices. The paper handles
both transparently, but a reviewer could note that sensitivity depends
critically on the exclusion of those 2 patched sessions. If those 2 sessions
had been QSIPrep failures on the unmodified sidecar (which is the predicted
outcome given the conditions), they would be correctly classified and
sensitivity would remain 0.989. The paper should explicitly state this: "had
the 2 excluded remediation-test sessions been classified using their original
unmodified sidecars, they would be expected to fail (consistent with
VECTA-DWI-021), and their inclusion would not change the sensitivity estimate."

**S3 (minor): No power calculation or sample size rationale.** NeuroImage
does not require formal power calculations for observational studies, but a
sentence explaining that N=1,071 confirmed outcomes was the complete available
sample from FITBIR (not a chosen N) removes the question.

**S4 (minor): PPV must be contextualized.** CIDUR PPV = 0.070 [0.024, 0.186]
will alarm any reader who sees it in isolation. The paper explains that
ready_with_limitations sessions are *expected* to be flagged and mostly succeed
(false positives are informative, not erroneous classifications). This needs a
single explicit sentence in the Performance section: "PPV is low because
ready_with_limitations (the majority of flagged sessions) represents sessions
Vecta correctly identified as lacking distortion-correction capability, not
misclassified sessions — these sessions ran QSIPrep via the no-SDC fallback
path."

---

## Academic writing

### Strengths

- Abstract is precise, within word limit, reports CIs, avoids overclaiming.
- Introduction positions existing tools accurately without misrepresentation.
- The "phantom criterion" framing (VECTA-DWI-040, validated via synthetic
  fixture only) is handled honestly.
- Table captions are informative and contain the footnotes necessary for
  standalone interpretation.

### Weaknesses

**AW1 (critical): "Data Birth Integrity" will face reviewer pushback.** Coining
a new construct term requires either: (a) demonstrating that no existing term
covers it, or (b) showing empirical results that validate the construct itself
rather than just the tool. The current introduction says DBI "extends and
operationalizes adjacent frameworks" but does not explain why "preprocessing
readiness assessment" or "pipeline-readiness QC" is insufficient. The four
formal properties are described as *distinguishing* DBI but a reviewer will
note that determinism and version-pinning are just good software engineering
practices, not properties that define a new scientific construct. Options:
  - Drop the DBI construct name; call it "DWI preprocessing readiness
    assessment" throughout and keep the four properties as design principles.
  - Or write a 200-word paragraph in the Introduction explicitly defending
    why a new construct term is scientifically necessary, with reference to
    prior literature that the properties address gaps in.

**AW2 (moderate): The 6-item contribution list in the Introduction is too
long and some items overlap.** Items (3) and (4) are both validation; items
(5) and (6) are both secondary evidence. Consolidate to 4 items: framework
description, CIDUR mechanism study, TrackTBI primary validation, and
cross-dataset stability.

**AW3 (moderate): "no framework exists" in the abstract is overclaimed.**
The claim "no framework exists to assess processing readiness before
preprocessing begins" will be challenged. Site-specific pre-flight scripts,
informal checkers, and MRIQC's structural metadata output all partially
address this. Reframe: "no generalizable, declarative, version-controlled
framework exists" or "no tool provides structured, criterion-level attribution
traceable to pipeline requirements."

**AW4 (moderate): Discussion lacks a concrete workflow recommendation.**
The Discussion does not tell a reader how to actually use Vecta in a study.
A paragraph such as: "We recommend running vecta assess at BIDS conversion
time, before any preprocessing is submitted. Review_required sessions should
be inspected for PhaseEncodingDirection and TotalReadoutTime before batching;
ready_with_limitations sessions can be processed with the understanding that
SDC will not be applied..." would make the paper actionable and is expected
in a methods paper.

**AW5 (minor): The Methods section is very dense.** The specification
structure subsection lists 22 variables and 5 domains in a single long
paragraph. Consider a small table (variable domain / count / example variable
/ extraction source) rather than prose enumeration. NeuroImage methods papers
routinely use brief schema tables for this purpose.

**AW6 (minor): Tense consistency.** Methods use present tense for the
framework description but past tense for cohort-level procedures. This is
standard but inconsistent in a few places — "Criteria are declarative rules"
(present, spec description) vs. "Sessions were excluded" (past, cohort-level).
Pick one convention per subsection and apply consistently.

---

## Software soundness

The software is genuinely well-engineered for v0.1:

- Declarative YAML specification separates scientific meaning from code — this
  is the right architecture for a tool that claims independent reviewability.
- JSON Schema Draft 2020-12 contracts at both input and output — appropriate
  rigor.
- Golden regression suite prevents silent output drift.
- `pip install git+...` works; open-source.

**Gaps for a methods paper:**

**SW1:** The version is v0.1. NeuroImage reviewers will ask about sustainability
and maintenance. A one-sentence statement about versioning policy suffices:
"Specification versions and engine versions are independently tracked; changes
to the specification require a version increment and a changelog entry. The
v0.1.0 specification is frozen for all results in this paper."

**SW2:** The tool is validated only on Siemens, GE, and Philips DWI data in
BIDS. The dcm2niix conversion is the dominant DICOM-to-BIDS tool; the paper
should note that the variable extraction algorithms assume dcm2niix field
naming conventions and may not generalize to other converters without
specification updates.

**SW3:** The `dwi_connectomics` profile is the only profile. Reviewers will ask
whether the framework supports other intended uses (resting-state fMRI, task
fMRI). A brief statement: "The framework is designed to support multiple
profiles; the `dwi_connectomics` profile is the only profile specified in
v0.1. Extension to other imaging modalities is planned but not validated."

---

## Priority ranking: what to do before NeuroImage submission

### Must-do (paper will be rejected without these)

1. **MRIQC comparison** (W2, E1 above) — run MRIQC on CIDUR and/or TrackTBI
   sessions; add Table N showing MRIQC DWI QC metrics for failed vs.
   successful sessions, with a paragraph demonstrating that MRIQC does not
   report fieldmap absence or PhaseEncodingDirection absence as actionable
   findings. One page of results, one paragraph in Discussion.

2. **Reframe DBI or justify it rigorously** (AW1) — either drop the construct
   name and use "preprocessing readiness assessment" throughout, or write a
   dedicated paragraph defending why a new construct term is scientifically
   necessary. The current treatment is too thin to survive peer review.

3. **Reframe CIDUR detection-level comparison as illustrative, not
   statistical** (S1, W1) — remove the causal language ("only a framework
   that independently evaluates both conditions achieves full sensitivity")
   or qualify it explicitly. The 3-event sample cannot support this claim.

### Should-do (substantially raises acceptance probability)

4. **Add pipeline-generalizability caveat** (E1) — one paragraph: "Criteria
   were validated against QSIPrep outcomes; the same blocking conditions
   (absent PhaseEncodingDirection, absent TotalReadoutTime) have been
   independently confirmed to cause failure in [X]." Even an informal
   cross-check against one other pipeline (e.g., fMRIPrep DWI path or
   MRtrix3) would strengthen this.

5. **Pre-specify false negative taxonomy** (W4) — define "fieldmap_error"
   category in Methods (not only in Results), with its operational definition
   (non-EPI fieldmap with absent or corrupt required metadata fields).

6. **Add concrete workflow guidance to Discussion** (AW4) — one paragraph on
   how to integrate vecta assess into a study workflow.

7. **Add a sentence on the 2 excluded remediation-test sessions** (S2) —
   state explicitly that including them as failures would not change
   sensitivity.

### Nice-to-have (reviewer requests, can address in revision)

8. SW2 note on dcm2niix assumption
9. SW3 note on single profile in v0.1
10. Consolidate Introduction contribution list from 6 to 4 items (AW2)
11. Replace Methods prose enumeration of 22 variables with a schema table (AW5)
12. Word "no framework exists" → qualified claim in abstract (AW3)
13. PPV contextualization sentence (S4)
14. Sample size rationale sentence (S3)
15. Connectome section: extend or remove (E3)

---

## Honest bottom line

The paper's evidence is real. The TrackTBI result — perfect specificity at
scale, sensitivity 0.989, tight CIs — is a strong finding that earns its
place in NeuroImage. The software is sound. The five-dataset breadth is
appropriate. The open-science posture is good.

The paper fails NeuroImage not because the science is weak but because two
things are missing: an empirical contrast with MRIQC (without which a reviewer
cannot evaluate the contribution claim), and a justification for the DBI
construct term that is strong enough to survive expert review. Both are
addressable. Neither requires new data collection.

Estimated time to address must-do items: 2–4 weeks (MRIQC run + analysis + 2
pages of text; DBI reframe is a writing task).

Estimated time to address should-do items: 1–2 additional weeks.

After must-do + should-do: **submit to NeuroImage main journal.**
