# dataset_040_missing_gradient_files

DWI NIfTI + sidecar present; .bval and .bvec BOTH absent.
Corresponds to CIDUR excluded_scans.csv 'DWI missing .bval/.bvec'
cases.

Expected: VECTA-DWI-030=finding (critical), readiness=ready_with_limitations.
(Not not_ready — readiness_rules only mark 001 as review, no criterion
is currently blocking in v0.1.)
