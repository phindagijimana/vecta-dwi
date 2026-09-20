# dataset_020_dicom_valid

Synthetic BIDS session with a matching DICOM source export under
`source_dicom/`. Represents the case where Vecta can consume both
representations (Source module + BIDS module) and produce
transformation-fidelity findings.

Layout:

    dataset_020_dicom_valid/
    ├── source_dicom/               ← 10 minimal DICOM files
    │                                  DWI series (7 instances) + T1 (3)
    └── sub-001/ses-01/
        ├── dwi/                    ← BIDS DWI (AP + PA)
        └── anat/                   ← BIDS T1w

Expected: all Source and BIDS criteria satisfied. No findings.
