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
- No protocol reference examples under `protocols/examples/` yet.
- Tolerance values are placeholders — must be justified before freeze (see Spec Blueprint §12).

### Not yet in this release
- Python engine.
- Golden test fixtures.
- Synthetic dataset expected outputs.

---

## v0.1.0 — 2026-09-19 (draft, schema pass)

Added JSON Schema layer under `schemas/`.

### Added
- `schemas/_defs.schema.json` — shared enums (mirrored from `registries/enums.yaml`), ID patterns, and reusable object types (`SeverityRecord`, `ConfidenceRecord`, `PotentialEffect`, `RecommendedAction`, `EmpiricalStatus`, `ErrorRecord`, `WarningRecord`) per Output Tech Spec §14-18, §25.
- Input schemas (validate authored YAML spec files):
  - `schemas/input/variable.schema.json`
  - `schemas/input/criterion.schema.json`
  - `schemas/input/profile.schema.json`
- Output schemas (validate emitted `vecta.json`):
  - `schemas/output/evidence.schema.json`
  - `schemas/output/conflict.schema.json`
  - `schemas/output/variable_result.schema.json`
  - `schemas/output/derived_metric.schema.json`
  - `schemas/output/criterion_result.schema.json`
  - `schemas/output/finding.schema.json`
  - `schemas/output/readiness.schema.json`
  - `schemas/output/assessment_status.schema.json`
  - `schemas/output/provenance.schema.json`
  - `schemas/output/vecta_output.schema.json` (top-level)

### Verified
- All 14 schemas parse and pass Draft 2020-12 meta-schema validation.
- All 5 authored YAML spec files (scanner, acquisition, bids variables; dwi_connectomics criteria; dwi_connectomics profile) validate against their input schemas.

### Fixed
- `input/variable.schema.json`: the derived-variable conditional (`derived: true` implies `formula_id` required) was firing vacuously when `derived` was absent. Now gated by `required: ["derived"]` inside the `if` clause.

### Deferred
- `input/protocol.schema.json` — no protocol reference example files yet.
- `output/adjudication.schema.json` — no human adjudication in first vertical slice.
- `output/cohort_summary.schema.json` — cohort aggregation is later phase.
- `output/research_outcome.schema.json` — outcome labeling manual not yet drafted (D7, D8).
