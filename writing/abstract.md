# Abstract

Diffusion-weighted MRI (DWI) preprocessing pipelines depend on specific
acquisition parameters, gradient files, and fieldmap acquisitions being
present, internally consistent, and preserved from the scanner through
Brain Imaging Data Structure (BIDS) conversion. When these requirements
are unmet, pipelines fail silently or produce outputs of uncertain
validity, yet no systematic framework exists to assess DWI processing
readiness before preprocessing begins. We developed Vecta-DWI, a
declarative framework for Data Birth Integrity (DBI) assessment of DWI
datasets. DBI is defined as the degree to which the information,
structure, and acquisition characteristics needed for a specified
downstream use are present, traceable, and preserved from acquisition
into the analysis-ready representation. Vecta-DWI operationalizes DBI
through a versioned specification of 22 variables and 8 criteria
evaluated relative to a declared intended-use profile, without requiring
any preprocessing to have been performed. We applied Vecta-DWI to 62
BIDS-converted DWI sessions from the CIDUR cohort, acquired across three
scanner models at two field strengths and two vendors, augmented with
original DICOM source data. Assessment completed for all 62 sessions
(mean completeness ratio 0.911). Twenty-eight sessions (45.2%) received a
readiness state of ready and 34 (54.8%) received ready_with_limitations;
no session was rated not_ready. A single criterion, VECTA-DWI-014
(complementary phase-encoding reference unavailable), was triggered in
all 34 GE sessions (54.8%) and in no Siemens session, reflecting a
known, site-level protocol difference in reverse phase-encoding practice.
Among sessions processed by QSIPrep v0.23.1, all 26 ready sessions
produced valid preprocessed outputs (positive predictive value 100%).
Thirty-three of 34 ready_with_limitations sessions were successfully
processed; the single QSIPrep failure occurred in a session pre-flagged
by VECTA-DWI-014 and was confirmed to fail on the same condition. These
results indicate that structural metadata and gradient file integrity
checks, evaluated before preprocessing, correctly stratify DWI sessions
by processing outcome. Vecta-DWI is open-source and provides
criterion-level attribution for every finding, enabling targeted
remediation without manual chart review.
