# Vecta-DWI specification changelog

## v0.1.0 — 2026-09-19 (draft)

Initial specification skeleton.

### Added
- Release manifest.
- Shared enum registry (value states, criterion status, assessment status, confidence, severity, readiness, evidence basis, review status, privacy status).
- Default tolerance placeholders (voxel size, TE, b-shell grouping, vector norm) — values are illustrative only, not yet justified.
- 10 foundational variable stubs across `scanner`, `acquisition`, `bids` domains.
- `dwi_connectomics` intended-use profile.
- Evidence registry with `EV-DWI-PE-001`.
- `VECTA-DWI-014` (missing reverse PE) fully worked; `VECTA-DWI-001` and `VECTA-DWI-021` stubbed.

### Open
- Extraction algorithms for all variables are not yet defined (`extraction: TODO`).
- No JSON Schemas under `schemas/` yet.
- No protocol reference examples under `protocols/examples/` yet.
- Tolerance values are placeholders — must be justified before freeze (see Spec Blueprint §12).

### Not yet in this release
- Python engine.
- Golden test fixtures.
- Synthetic dataset expected outputs.
