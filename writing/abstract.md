# Abstract

DWI preprocessing pipelines require acquisition parameters, gradient
files, and fieldmap acquisitions to be present, internally consistent,
and preserved through BIDS conversion; when unmet, pipelines fail
silently or produce outputs of uncertain validity, yet no generalizable,
declarative, version-controlled framework exists to assess preprocessing
readiness at the metadata layer before pipelines run. We developed
Vecta-DWI, a Data Birth Integrity (DBI) framework that evaluates 22
variables and 8 criteria against a declared intended-use profile without
preprocessing. Criteria were developed using the CIDUR in-sample
development cohort (62 sessions; two vendors); all three QSIPrep
failures across 69 sessions with confirmed outcomes occurred in
Vecta-flagged sessions, spanning two mechanistically distinct modes —
PhaseEncodingDirection absence and reverse-PE acquisition absence —
each undetectable by naive metadata checks. External validation on
1,275 TrackTBI sessions (649 subjects; Siemens, GE, Philips) produced
perfect vendor stratification: all Siemens sessions received
ready_with_limitations; all GE and Philips sessions received
review_required. Against 1,071 sessions with confirmed QSIPrep outcomes,
failure rates were 1.6% (7/451) for ready_with_limitations and 100%
(620/620) for review_required, yielding sensitivity 0.989 [0.977, 0.995],
NPV 0.984 [0.968, 0.992], PPV 1.000, and specificity 1.000. Seven false
negatives had non-EPI fieldmaps with corrupt metadata outside Vecta's
current criterion scope. Three publicly available datasets (549 sessions;
522 assessed) confirmed criterion stability across protocols and vendors.
Vecta-DWI identifies failure modes invisible to conformance-based
validation, provides criterion-level attribution for targeted remediation,
and is open-source, demonstrating that the DBI design approach —
declarative, intended-use-conditional, null-safe readiness assessment —
is practically instantiable and generalizes across vendors and acquisition
platforms.
