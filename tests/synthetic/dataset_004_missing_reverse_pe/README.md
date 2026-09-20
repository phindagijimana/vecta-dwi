# dataset_004_missing_reverse_pe

Synthetic BIDS session with a single DWI acquisition in one PE direction,
no complementary reference acquisition.

- `sub-001_ses-01_dir-AP_dwi.json`: PhaseEncodingDirection = `j-`

Inventory is complete (all acquisitions have known PE), so reverse-PE
availability can be confidently established as `false`.

Expected outcome: `VECTA-DWI-014` status = `finding`, one major finding
emitted, readiness = `ready_with_limitations`.
