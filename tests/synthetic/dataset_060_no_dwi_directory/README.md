# dataset_060_no_dwi_directory

Synthetic BIDS session with an anatomical directory but no `dwi/` subdirectory.
Models CIDUR sub-002/ses-1 and sub-044/ses-2 where DWI was excluded at conversion.

Expected: VECTA-DWI-040 fires (session_has_no_dwi), readiness → ready_with_limitations.
