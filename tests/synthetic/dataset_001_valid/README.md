# dataset_001_valid

Synthetic BIDS session with two DWI acquisitions in complementary
phase-encoding directions. Represents the reference case where no
Vecta-DWI-014 finding should be triggered.

- `sub-001_ses-01_dir-AP_dwi.json`: PhaseEncodingDirection = `j-`
- `sub-001_ses-01_dir-PA_dwi.json`: PhaseEncodingDirection = `j`

Expected outcome: `VECTA-DWI-014` status = `satisfied`, readiness = `ready`.
