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
any preprocessing to have been performed. We applied Vecta-DWI to a 71-session CIDUR cohort spanning three scanner
models at two field strengths and two vendors, with original DICOM source
data available. Assessment completed for all sessions (mean completeness
ratio 0.911). In the 62-session primary BIDS cohort, 28 sessions (45.2%)
received ready and 34 (54.8%) received ready_with_limitations; 2
sessions in the pre-intervention excluded stratum received
review_required. QSIPrep v0.23.1 outcomes were confirmed for 69
sessions spanning all three readiness states. Failure rates were 0%
(0/26) for ready sessions, 2.4% (1/41) for ready_with_limitations
sessions, and 100% (2/2) for review_required sessions. All three QSIPrep failures occurred in Vecta-flagged sessions.
The two review_required failures (VECTA-DWI-021) have a confirmed
direct cause: QSIPrep crashed because PhaseEncodingDirection was absent,
preventing parameter extraction before the SDC workflow was instantiated.
The single ready_with_limitations failure (VECTA-DWI-014) occurred at
the eddy step; the direct cause was not recovered from available logs
and is not attributable to fieldmap absence alone (40 other fieldmap-absent
sessions succeeded). Across all three failures, Vecta achieved
sensitivity 1.000 (95% CI [0.439, 1.000]) and NPV 1.000
(95% CI [0.871, 1.000]). A naive metadata-completeness check
(PhaseEncodingDirection absent) matched two of three failures but
could not detect the eddy-stage failure, which carries valid
PhaseEncodingDirection metadata. In an independent criterion replication cohort (five
TrackTBI participants, b = 1300 s/mm², independent institutions and
scanner platform), the sole triggered criterion matched CIDUR findings,
with all five 2-week sessions successfully preprocessed. Application to
three publicly available datasets (549 additional sessions) demonstrated
criterion stability across protocols and vendors: VECTA-DWI-021
triggered in all sessions lacking TotalReadoutTime; VECTA-DWI-030
identified five MASiVar sessions with absent gradient files confirmed
at the source repository. These results demonstrate that a
multi-criterion readiness framework spanning acquisition and metadata
evidence layers identifies failure modes invisible to conformance-based
validation and to single-criterion metadata checks. Vecta-DWI is
open-source and provides criterion-level attribution for every finding,
enabling targeted remediation without manual chart review.
