# dataset_011_dicom_bids_conflict

BIDS sidecar declares MagneticFieldStrength=3.0T; DICOM source
reports 1.5T. Represents a real transformation-fidelity failure —
the value survived conversion incorrectly (or was manually set).

Expected: VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS=false,
VECTA-DWI-060=finding (representation_integrity), readiness=
ready_with_limitations.
