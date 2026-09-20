# dataset_010_unknown_pe

Synthetic BIDS session with one DWI acquisition and NO
`PhaseEncodingDirection` or `TotalReadoutTime` in the sidecar. Represents
the prohibited case (Output Tech Spec §55): Vecta must NOT emit
`REVERSE_PE_AVAILABLE = false` in this state.

Expected outcome:
- `VECTA.DWI.ACQ.PE_DIRECTION.state` = `unknown`
- `VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE.state` = `unknown` (value must be null)
- `VECTA-DWI-014.status` = `unknown` (NO finding emitted)
- `VECTA-DWI-001.status` = `finding` (PE direction unknown triggers this)
- readiness = `review_required` (VECTA-DWI-001 is in the profile's `review_criteria`)
