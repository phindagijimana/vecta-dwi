# dataset_005_missing_readout

PhaseEncodingDirection present but TotalReadoutTime missing.
This should trigger VECTA-DWI-021 (essential metadata insufficient).

Expected: TOTAL_READOUT_TIME_PRESENT=false, VECTA-DWI-021=finding,
readiness=ready_with_limitations.
