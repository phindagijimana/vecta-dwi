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

---

## v0.1.0 — 2026-09-19 (draft, first Python vertical slice)

First executable end-to-end path. Runs `VECTA-DWI-014` against synthetic
BIDS input and emits schema-validated `vecta.json`.

### Added
- Python package `vecta` under `src/vecta/`:
  - `enums.py` — runtime mirror of `registries/enums.yaml`.
  - `models.py` — Pydantic v2 models mirroring the output schemas.
  - `spec/loader.py` — reads and validates variable/criterion/profile YAMLs
    against input schemas at engine start; performs referential integrity
    checks before any data is assessed (Spec Blueprint §23).
  - `collectors/bids.py` — minimal BIDS collector; discovers DWI entities
    and reads sidecar JSONs; emits `EvidenceRecord` per source field.
  - `extract/pe.py` — extractors for `PE_DIRECTION` and
    `TOTAL_READOUT_TIME_PRESENT`.
  - `derive/reverse_pe.py` — reverse-PE availability derivation per
    `reverse_pe_availability_v1` formula.
  - `criteria/engine.py` — declarative condition evaluator
    (all/any/not + equals/not_equals/state predicates); Finding assembly
    from criterion finding-templates.
  - `output/assemble.py` — full assessment assembler + JSON Schema
    validation + referential integrity check (Output Tech Spec §46).
- `pyproject.toml` — hatchling build; deps: pydantic, PyYAML, jsonschema,
  referencing.
- Three synthetic BIDS fixtures under `tests/synthetic/`:
  - `dataset_001_valid` — DWI AP + PA → `VECTA-DWI-014` satisfied, ready.
  - `dataset_004_missing_reverse_pe` — DWI AP only, complete inventory →
    `VECTA-DWI-014` finding, ready_with_limitations.
  - `dataset_010_unknown_pe` — DWI with no `PhaseEncodingDirection` →
    `VECTA-DWI-014` status=unknown (no finding — Output Tech Spec §55
    prohibited case regression); `VECTA-DWI-001` and `VECTA-DWI-021` fire;
    readiness=review_required.
- `tests/integration/test_first_vertical_slice.py` — parametrized
  end-to-end test: pipeline → schema validation → referential integrity
  → per-fixture behavior assertions, plus explicit prohibited-behavior
  regression on `dataset_010`.

### Verified
- 4 integration tests pass under Python 3.11.
- Emitted `vecta.json` validates against `vecta_output.schema.json` for
  all three fixtures.
- Referential integrity check passes.

### Fixed (bugs found by the test)
- `to_dict`: blanket `exclude_none=True` was dropping schema-required
  `VariableResult.value` and `DerivedMetric.value` when null (state=unknown).
  Now reinserts them explicitly.
- Runtime `__version__` changed from PEP 440 `0.1.0.dev0` to SemVer
  `0.1.0-dev0` so it matches the schema's SemVer pattern. Package
  version in `pyproject.toml` stays PEP 440 for packaging tooling.
- Input `variable.schema.json` conditional (fixed in previous commit)
  now confirmed correct against real YAML loading.

### Not yet built
- DICOM collector (`collectors/dicom.py`).
- Extractors for scanner/voxel/volume/bval/bvec variables.
- CLI (`cli.py`).
- HTML report renderer.
- TSV projection.
- Cohort aggregator.
- Golden JSON fixtures with normalized-placeholder diffing (currently
  using structured expected.yaml assertions instead).
