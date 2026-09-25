# Abstract

DWI preprocessing pipelines require acquisition parameters, gradient
files, and fieldmap acquisitions to be present, internally consistent,
and preserved through BIDS conversion. When unmet, pipelines fail
silently or produce outputs of uncertain validity, yet no framework
exists to assess processing readiness before preprocessing begins. We
developed Vecta-DWI, a declarative framework for Data Birth Integrity
(DBI) assessment. DBI is the degree to which information, structure, and
acquisition characteristics needed for a specified downstream use are
present, traceable, and preserved into the analysis-ready
representation. Vecta-DWI operationalizes DBI through 22 variables and
8 criteria evaluated against a declared intended-use profile, without
requiring preprocessing. Applied to a 71-session CIDUR cohort (three scanner models, two
vendors, two field strengths; completeness ratio 0.911), 28 of 62
sessions received ready (45.2%), 34 ready_with_limitations (54.8%),
and 2 review_required. QSIPrep v0.23.1 outcomes were confirmed for 69
sessions. Failure rates were 0% (0/26), 2.4% (1/41), and 100% (2/2)
for ready, ready_with_limitations, and review_required, respectively;
all three failures occurred in Vecta-flagged sessions (sensitivity
1.000, 95% CI [0.439, 1.000]; NPV 1.000, 95% CI [0.871, 1.000]). A naive metadata check matched two of
three failures but missed the eddy-stage failure. In an independent
replication cohort (five TrackTBI participants, independent scanner
platform), the sole triggered criterion matched CIDUR findings; all
five sessions preprocessed successfully. Three publicly available
datasets (549 sessions; 522 assessed) showed criterion stability across
protocols and vendors; controlled injection confirmed detection
sensitivity. Vecta-DWI identifies failure modes invisible to conformance-based
validation and single-criterion checks, is open-source, and provides
criterion-level attribution for targeted remediation.
