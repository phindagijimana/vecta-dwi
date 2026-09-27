# Introduction

Diffusion-weighted MRI (DWI) is widely used in research applications
ranging from structural connectomics to white matter tract analysis.
Specialized preprocessing pipelines such as QSIPrep (Cieslak et al.,
2021), MRtrix3 (Tournier et al., 2019), and FSL's eddy (Andersson &
Sotiropoulos, 2016), typically distributed as BIDS Apps (Gorgolewski et
al., 2017), have standardized the transformation from raw DWI acquisitions
to analysis-ready outputs, but these pipelines depend on
specific data properties being present and correctly preserved from the
scanner through the Brain Imaging Data Structure (BIDS; Gorgolewski et
al., 2016) conversion step. Susceptibility distortion correction via reversed phase-encoding
(Andersson et al., 2003), for example, requires a reverse
phase-encoding reference acquisition, a PhaseEncodingDirection field in
the BIDS sidecar, and a TotalReadoutTime value; without these, distortion
correction is not applicable and may proceed silently without correction. When these requirements are unmet,
preprocessing pipelines may fail with uninformative error messages, skip
processing steps without reporting them, or complete without error while
producing outputs of reduced validity. Discovering such data
insufficiencies only after preprocessing has been attempted wastes
computational resources and introduces delays that are particularly
costly in large multi-site studies.

The scale of this problem is substantial. Variability in analytic
choices and data handling contributes to low reproducibility in
neuroimaging findings (Botvinik-Nezer et al., 2020; Nichols et al.,
2017), and inconsistent acquisition and conversion practices are a
primary source of that variability in DWI studies. Roalf et al. (2016)
demonstrated that scanner and site differences produce systematic
variation in DWI-derived metrics that can rival or exceed effect sizes
of interest, underscoring the importance of detecting acquisition
irregularities before they propagate through analysis. Large open
repositories such as OpenNeuro (Markiewicz et al., 2021) have made
multi-site, multi-scanner DWI datasets widely accessible but have also
revealed the heterogeneity of acquisition and conversion practices
across sites. Metadata fields required by modern pipelines are
frequently absent, inconsistently populated, or silently dropped during
DICOM-to-BIDS conversion, and these deficiencies are not reliably
surfaced by existing validation tools.

Several existing tools address complementary aspects of DWI data
management without fully addressing this problem. The BIDS Validator
(bids-standard/bids-validator) checks whether a dataset conforms to the
BIDS specification, identifying structural errors and missing required
fields, but conformance to the standard does not guarantee readiness for
any particular downstream pipeline. MRIQC (Esteban et al., 2017) provides
automated assessment of image quality metrics derived from the acquired
images, but characterizes image quality after acquisition rather than
structural prerequisites before preprocessing. eddyqc (Bastiani et al.,
2019) and QSIPrep's
built-in quality measures assess processing quality from outputs that
already require the pipeline to have run successfully. None of these tools answer the question that confronts researchers
preparing a DWI dataset for analysis: does this session have what this
pipeline needs to run correctly? Critically, MRIQC's DWI image quality
metrics — SNR, framewise displacement, B0 field uniformity, b-value
summary statistics — are derived from the acquired image data and do not
include PhaseEncodingDirection completeness, TotalReadoutTime presence,
fieldmap availability relative to DWI sessions, or gradient file
integrity. A session lacking a signed PhaseEncodingDirection will
receive normal MRIQC image quality scores, because the absence of that
sidecar field does not degrade the image; yet that absence will cause
QSIPrep to crash before the preprocessing workflow is instantiated.
The gap is not that existing tools are inadequate — they answer
different questions — but that no tool occupies the metadata-integrity
layer between BIDS conversion and pipeline execution.

We define Data Birth Integrity (DBI) as the degree to which the
information, structure, provenance, acquisition characteristics, and
representation needed for a specified downstream scientific use are
present, internally consistent, traceable, and appropriately preserved
from acquisition and source data into the analysis-ready representation.
DBI is deliberately intended-use conditional: a dataset can be
sufficient for one analysis and insufficient for another. DBI is a
theoretical framework, not a tool: it specifies what a preprocessing
readiness assessment must guarantee, in the same way that the FAIR data
stewardship principles (Wilkinson et al., 2016) specify what data must
be to support reuse, but do not prescribe a specific implementation.
Vecta-DWI is an instantiation of DBI for DWI preprocessing readiness;
the empirical work in this paper validates Vecta-DWI. The DBI framework
provides the theoretical grounding for Vecta's four design properties
and explains why they are required rather than merely convenient. This
framing extends and operationalizes adjacent frameworks — including
AI-readiness criteria for biomedical data (Clark et al., 2024) and
machine-actionable provenance (Levinson et al., 2024) — to the specific
task of determining whether a DWI session can enter a designated
preprocessing workflow. DBI assessment operates at the lifecycle layer
of evidence acquisition and representation, preceding and complementing
downstream QC tools that characterize what the pipeline produced.

We describe Vecta-DWI, an open-source framework that operationalizes DBI
for DWI processing readiness. Vecta-DWI embodies a versioned
specification of variables, criteria, and intended-use profiles, executed
by a deterministic engine that produces structured, evidence-traceable
findings without requiring any preprocessing to have been performed.
Twenty-two variables spanning five evidence domains — scanner context,
acquisition parameters, gradient files, BIDS representation, and DICOM
source integrity — are evaluated against eight declarative criteria under
a dwi_connectomics intended-use profile. Each finding carries a severity
rating, an evidence chain anchored to pipeline requirements and published
standards, and a recommended remediation action, enabling targeted
investigation rather than manual review of entire datasets.

Criteria were developed using the Clinical Imaging Data for UR Researchers
(CIDUR) cohort (62 sessions; three scanner models, two vendors, two field
strengths) from the University of Rochester Medical Center as an in-sample
development context, augmented
with original DICOM source data. Primary external validation was
conducted on a 1,275-session cohort (TrackTBI; 649 subjects, three
vendors: Siemens, GE, Philips) to assess generalizability across
acquisition platforms and institutions. We compared Vecta readiness
states and criterion-level findings against QSIPrep
1.0.1.dev0+gee9aa2e.d20250115 processing outcomes, testing whether
structural metadata integrity checks performed before preprocessing
correctly stratify sessions by downstream processing success. We report
the assessment completeness, finding prevalence, readiness distribution,
and predictive performance for each readiness tier, and describe
individual cases where criterion-level attribution provided information
not recoverable from aggregate pipeline outcomes. Specifically, this work: (1) introduces the DBI framework and its
four formal design properties, and describes the Vecta-DWI v0.1
specification, engine, and open-source implementation; (2) uses the
CIDUR development cohort (69 confirmed outcomes, two vendors) to
characterize two mechanistically distinct failure modes missed by
metadata-completeness and conformance-based tools; (3) provides primary
external validation in 1,275 TrackTBI sessions (649 subjects, three
vendors) and criterion stability across three independent OpenNeuro
datasets (549 sessions), yielding sensitivity 0.989 [0.977, 0.995]
and NPV 0.984 [0.968, 0.992]; and (4) presents case studies
demonstrating criterion-level attribution, pre-intervention detection,
and cross-layer inference that BIDS Validator, MRIQC, and file-presence
checks cannot provide. To facilitate validation and adoption,
the Vecta-DWI specification, engine, synthetic test fixtures, and
analysis scripts are publicly available
(github.com/phindagijimana/vecta-dwi).
