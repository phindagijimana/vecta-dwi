# dataset_002_missing_bvec

DWI has .nii.gz + .bval but NO .bvec. Represents export/conversion
problem: gradient directions unavailable.

Expected: BVEC_COUNT.state=unknown, BVEC_PLAUSIBILITY.state=unknown,
readiness=ready_with_limitations (VECTA-DWI-014 satisfied because we
know PE=j- and can determine reverse-PE absence from complete inventory).
