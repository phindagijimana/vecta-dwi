# dataset_003_bval_volume_mismatch

NIfTI has 7 volumes but the .bval file has 8 entries. bvec has 7.
Represents corrupted / partially-converted export.

Expected: VOLUME_COUNT=7, BVAL_COUNT=8. BVEC_PLAUSIBILITY becomes
extraction_failed because bval and bvec lengths disagree.
