# Introduction

Diffusion-weighted MRI (DWI) is widely used in research applications
ranging from structural connectomics to white matter tract analysis.
Specialized preprocessing pipelines such as QSIPrep (Cieslak et al.,
2021), MRtrix3 (Tournier et al., 2019), and FSL's eddy (Andersson &
Sotiropoulos, 2016) have standardized the transformation from raw DWI
acquisitions to analysis-ready outputs, but these pipelines depend on
specific data properties being present and correctly preserved from the
scanner through the Brain Imaging Data Structure (BIDS; Gorgolewski et
al., 2016) conversion step. Susceptibility distortion correction, for example,
requires a reverse phase-encoding reference acquisition, a
PhaseEncodingDirection field in the BIDS sidecar, and a TotalReadoutTime
value; without these, distortion correction is not applicable and may
proceed silently without correction. When these requirements are unmet,
preprocessing pipelines may fail with uninformative error messages, skip
processing steps without reporting them, or complete without error while
producing outputs of reduced validity. Discovering such data
insufficiencies only after preprocessing has been attempted wastes
computational resources and introduces delays that are particularly
costly in large multi-site studies.

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
already require the pipeline to have run successfully. None of these
tools answer the question that confronts researchers preparing a DWI
dataset for analysis: does this session have what this pipeline needs
to run correctly?

We define Data Birth Integrity (DBI) as the degree to which the
information, structure, provenance, acquisition characteristics, and
representation needed for a specified downstream scientific use are
present, internally consistent, traceable, and appropriately preserved
from acquisition and source data into the analysis-ready representation.
DBI is deliberately intended-use conditional: a dataset can be
sufficient for one analysis and insufficient for another. This framing
extends and operationalizes adjacent frameworks — including broad
AI-readiness criteria (Clark et al., 2024), machine-actionable provenance
(Levinson et al., 2024), and the FAIR stewardship principles (Wilkinson
et al., 2016) — to
the specific task of determining whether a DWI session can enter a
designated preprocessing workflow. DBI assessment operates at the
lifecycle layer of evidence acquisition and representation, preceding
and complementing downstream QC tools that characterize what the
pipeline produced.

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

We applied Vecta-DWI to 62 BIDS-converted DWI sessions from the CIDUR
cohort at the University of Rochester Medical Center, acquired across
three scanner models from two vendors at two field strengths and
augmented with original DICOM source data. We compared Vecta readiness
states and criterion-level findings against QSIPrep v0.23.1 processing
outcomes, testing whether structural metadata integrity checks performed
before preprocessing correctly stratify sessions by downstream processing
success. We report the assessment completeness, finding prevalence,
readiness distribution, and positive predictive value for each readiness
tier, and describe individual cases where the criterion-level attribution
provided information not recoverable from aggregate pipeline success
rates. To facilitate validation and adoption, the Vecta-DWI
specification, engine, synthetic test fixtures, and analysis scripts are
publicly available (github.com/phindagijimana/vecta-dwi).
