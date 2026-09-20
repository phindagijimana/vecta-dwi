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
- CLI (`cli.py`).
- HTML report renderer.
- TSV projection.
- Cohort aggregator.
- Golden JSON fixtures with normalized-placeholder diffing (currently
  using structured expected.yaml assertions instead).

---

## v0.1.0 — 2026-09-19 (draft, first slice completed)

Completed the first vertical slice by wiring up all 10+ foundational
variables and fleshing out the previously-stub criteria.

### Added
- `extract/scanner.py` — Manufacturer, ManufacturersModelName,
  MagneticFieldStrength (with plausibility bounds → invalid state),
  SoftwareVersions.
- `extract/acquisition.py` — voxel size (NIfTI zooms), volume count
  (NIfTI dim[4]), bval count, shell count derivation (b0 threshold +
  greedy grouping under `b_shell_grouping` tolerance), bvec count,
  bvec plausibility derivation (per-vector norm within `vector_norm`
  tolerance).
- `extract/bids.py` — BIDS Validator error/warning counts (reads
  optional external `.bids-validator-output.json`), required-series
  presence per profile (structured object with `present` map +
  `missing` list, per Spec Blueprint §9.1).
- BIDS collector now emits evidence records for `.nii.gz`, `.bval`,
  `.bvec` companion files and additional sidecar fields (Manufacturer,
  ModelName, FieldStrength, SoftwareVersions, RepetitionTime, EchoTime).

### Filled out
- `EV-DWI-PE-002` — PhaseEncodingDirection required for
  distortion-correction configuration (QSIPrep/FSL topup).
- `EV-DWI-META-001` — PE + TotalReadoutTime essential for topup.
- `VECTA-DWI-001` — full finding template with observed/reference
  condition, potential effects, recommended actions, empirical status.
- `VECTA-DWI-021` — full finding template.

### Verified
- All 4 existing integration tests still pass under Python 3.11 with
  the expanded variable set.
- All new variables validate against the output schema.
- Fixture datasets now include real NIfTI/bval/bvec companion files.

### Dependencies
- Added: `nibabel>=5.0`, `pydicom>=2.4`, `numpy>=1.24`.

---

## v0.1.0 — 2026-09-19 (draft, DICOM Source module)

Added the DICOM Source module — the distinctive CIDUR-cohort capability
that separates Vecta from BIDS-only readiness tools.

### Added
- `collectors/dicom.py` — walks a DICOM tree, groups instances by
  SeriesInstanceUID, reads headers only (fast), tracks duplicate
  SOPInstanceUIDs and intra-series geometry consistency. Also carries
  the substring-based classifier (dwi/t1/fmap/etc.) lifted in spirit
  from `dbi/` v1.0.5's `classification_rules`.
- `extract/dicom_source.py` — extractors for
  `VECTA.DWI.DICOM.{SERIES_COUNT, DWI_SERIES_COUNT, INSTANCE_COUNT,
  DUPLICATE_INSTANCE_COUNT, SERIES_GEOMETRY_CONSISTENT,
  FIELD_STRENGTH_AGREES_WITH_BIDS}`.
- `specification/v0.1/variables/dicom_source.yaml` — 6 source-integrity
  variables (L2_SOURCE + one L4 transformation-fidelity).
- Two new criteria in `dwi_connectomics.yaml`:
  - `VECTA-DWI-050` — DWI DICOM geometry inconsistent (source_integrity).
  - `VECTA-DWI-060` — DICOM/BIDS field-strength disagreement
    (representation_integrity, i.e. transformation-fidelity check per
    Study Design §7).
- Evidence entries `EV-DWI-DCM-GEO-001` and `EV-DWI-DCM-FIDELITY-001`.
- `assess_session()` now takes an optional `dicom_inventory` argument;
  Source variables are emitted only when supplied. Source criteria
  return `unknown` when the inventory is absent (never `false`).
- New fixture `dataset_020_dicom_valid` with 10 synthetic DICOM files
  (DWI + T1 series, minimal but valid headers) alongside a matching
  BIDS layout.
- `tests/integration/test_source_module.py` — 2 tests covering (a) full
  BIDS+DICOM end-to-end and (b) source-criteria-unknown-without-DICOM
  behavior.

### Changed
- Existing BIDS-only fixtures now have `assessment_status.state =
  completed_with_unknowns` because the added Source criteria are
  unevaluable without DICOM. Readiness state is unchanged (Source
  criteria are not in the profile's review or blocking lists).

### Verified
- All 6 integration tests pass under Python 3.11.
- DICOM evidence carries `privacy_status: restricted` — never exported
  by the (still-to-be-built) privacy serializer.

---

## v0.1.0 — 2026-09-19 (draft, cohort/TSV/CLI)

### Added
- `output/tsv.py` — versioned per-session TSV projection
  (`vecta_session_tsv_v1`, 28 columns). NULL/unknown values rendered as
  `NA` so `false` and `unknown` remain distinct (Output Tech Spec §29).
- `output/cohort.py` — cohort aggregation producing five artifacts:
  `session_summary.tsv`, `findings_long.tsv`, `variables_long.tsv`,
  `finding_prevalence.tsv`, `missingness_matrix.tsv`.
- Finding prevalence table exposes **three explicit denominators**
  (assessed / applicable / evaluable) as required by Output Tech Spec
  §32 — these are NOT interchangeable when unknown rates vary.
- `cli.py` — `vecta assess | aggregate | validate-spec | explain |
  version` sub-commands. `vecta` entry point installed via project
  scripts.
- `tests/integration/test_cli.py` — 3 CLI smoke tests
  (assess→aggregate, validate-spec, explain).

### Verified
- All 9 integration tests pass under Python 3.11.
- `vecta assess` runs against all three BIDS fixtures + emits validated
  vecta.json + one-row TSV per session.
- `vecta aggregate` produces prevalence table showing VECTA-DWI-014
  triggered in 1/3 assessed, 1/3 applicable, and 1/2 evaluable
  sessions — the evaluable-count difference exposes the unknown-PE
  case as expected.
- `vecta explain` prints human-readable finding explanation without
  reimplementing any scientific logic.

---

## v0.1.0 — 2026-09-19 (draft, HTML report renderer)

### Added
- `output/html.py` — Jinja2-based HTML report renderer.
- CLI: `--formats html` writes `report.html` alongside `vecta.json`.
- `tests/integration/test_html_report.py` — 2 tests verifying
  content preservation (readiness, findings, effects, provenance) and
  end-to-end CLI HTML output.

### Contract (per Output Tech Spec §30 + §69)
- Renders from canonical JSON only. Every value shown in the report
  is present verbatim in the input `vecta.json`; no scientific rule
  is re-implemented.
- Severity/confidence/effect wording is pulled from the finding's
  own fields. Potential effects are shown with their relation status
  (plausible / empirically_associated / externally_replicated).
- Readiness is displayed with the disclaimer that it does not
  guarantee clinical or scientific validity.
- No PHI serialized by default (relies on the privacy filter to have
  dropped restricted evidence before reaching the renderer).

### Verified
- All 11 integration tests pass under Python 3.11.

### Dependencies
- Added: `jinja2>=3.0`.
