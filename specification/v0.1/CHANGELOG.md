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

---

## v0.1.0 — 2026-09-19 (draft, outcome extractor + first Vecta × outcome join)

Enables the CIDUR internal validation loop described in Study Design §12
("Internal validation should test both software correctness and
scientific association") on the actual Gugger Lab pipeline outputs.

### Added
- `src/vecta/research/outcomes.py` — outcome extractor for the CIDUR-
  shape QSIPrep results tree:
  - `check_session_derivatives()` — structural sanity of the
    required-derivative inventory per outcome-labeling manual §3.
  - `read_subject_qc()` — parse `subject_qc.json` (CIDUR team's
    ready-made PASS/FAIL structure).
  - `label_session()` / `label_cohort()` — emit the six primary +
    secondary outcome records per outcome-labeling manual §6.
  - Deliberately does NOT parse raw QSIPrep logs; log-based failure
    attribution is a v0.2 task requiring a stable log-format contract.
- `specification/v0.1/schemas/output/research_outcome.schema.json` —
  formal contract for the outcome record, keeping outcome labeling
  cleanly separate from the deterministic assessment (Output Tech
  Spec §35).
- `cli.py`: `vecta label-outcomes` subcommand.
- `tests/integration/test_outcomes.py` — 5 tests covering success,
  failure, count mismatch, SKIP → not_applicable mapping, and
  schema-validation of every emitted outcome.

### First live CIDUR × QSIPrep join
- Labeled all 62 CIDUR sessions from `/mnt/nfs/Gugger_Lab/NIR/dwi_CIDUR/results`.
- Joined against the earlier Vecta run → 60/62 sessions matched.
- Full report at `~/Documents/vecta_dwi_cidur_run/JOIN_REPORT.md`.
- Headline (engineering, not scientific):
  - **26/26 Vecta-`ready` sessions produced QSIPrep derivatives (100%).**
  - **33/34 Vecta-`ready_with_limitations` sessions produced derivatives (97%).**
  - The one failure (`sub-076/ses-1`) is a GE SIGNA Premier session
    where Vecta had flagged missing reverse-PE — the exact
    upstream-to-downstream pattern Paper 1 is designed to characterize.
- The 2 outcome-only sessions (`sub-002/ses-1`, `sub-044/ses-2`)
  exposed a v0.2 gap: Vecta should emit a cohort-integrity finding
  when an expected session has no DWI at all.

### Verified
- All 27 integration tests pass (was 22).

---

## v0.1.0 — 2026-09-19 (draft, D2/D4 encoded + VECTA-DWI-030 added)

Encoding the D2 (localizer exclusion) and D4 (tolerance justification)
recommendations from the recent decision review, and adding
`VECTA-DWI-030` to close the gap surfaced by CIDUR's manual
"DWI missing .bval/.bvec" exclusions.

### Added
- `VECTA-DWI-030` — critical/provisional criterion firing when a DWI
  entity is present but the `.bval` and/or `.bvec` companion file is
  absent. Distinct from the plausibility check
  (`BVEC_PLAUSIBILITY`, which assumes both files exist).
- `EV-DWI-GRAD-001` — pipeline-requirement evidence entry supporting
  the above (BIDS DWI companion-file requirement + gradient-aware
  preprocessing requirement).
- `tests/synthetic/dataset_040_missing_gradient_files/` — DWI NIfTI +
  sidecar, no .bval or .bvec. Verifies the new criterion + severity.
- `dwi_connectomics` profile: `exclusions.classes: [localizer]` — D2
  decision encoded. Localizer series remain in per-session evidence
  but are excluded from cohort denominators / profile readiness math.
- `input/profile.schema.json`: new optional `exclusions` object with
  `classes: [string]`.

### Changed
- `tolerances/default_tolerances.yaml`: all four v0.1 tolerances
  promoted from `provisional` to `expert_consensus` or
  `pipeline_requirement` with justified sources (D4 decision).
- `dataset_040_missing_gradient_files` also triggers `VECTA-DWI-014`
  (missing reverse-PE) — inventory of PE-known DWI entities is
  complete with one entity, so the derivation returns
  `reverse_pe_available=false`.

### Verified against CIDUR
- The 3 CIDUR "DWI missing .bval/.bvec" cases were caught upstream by
  the conversion team (all 3 are fMRI mis-routed as DWI, routed to
  `for_review/corrupt_scans/`, never appearing in `data_bids/`). So
  `VECTA-DWI-030` correctly does not fire against the current CIDUR
  BIDS export. The criterion remains valuable for less-careful
  conversion pipelines that emit malformed DWI to BIDS.

### Verified
- All 22 integration tests pass (was 21). Goldens regenerated for the
  5 fixtures to reflect `VECTA-DWI-030` in the criteria list.

---

## v0.1.0 — 2026-09-19 (draft, CIDUR integration + first live run)

Prompted by inspecting `~/Documents/CIDUR_BIDS/data_bids` (76 subjects,
82 sessions, 62 DWI sessions across Siemens Skyra/Vida Fit + GE SIGNA
Premier/Artist).

### Added
- `collectors/bids.py`: `FmapEpiEntity` dataclass; collector now also
  discovers `fmap/*_epi.json` and reads `IntendedFor`.
- `derive/reverse_pe.py`: after checking sibling DWI entities, also
  consult fmap EPI entities whose `IntendedFor` list points at the
  target DWI (or which lack an `IntendedFor` entirely, per BIDS-Legacy
  semantics). Without this, `VECTA-DWI-014` gave wrong results on
  CIDUR-style layouts where the reverse-PE reference lives under
  `fmap/` rather than as a sibling DWI acquisition.
- `extract/bids.py::_validator_output`: handles both the flat
  `{errors, warnings}` shape and the v2 `{issues: {errors, warnings}}`
  shape. Also skips prepended stderr lines (some
  `bids-validator` invocations leak node warnings into stdout ahead
  of the JSON body — observed in
  `CIDUR_BIDS/validation_report_data_bids.json`).
- `tests/synthetic/dataset_030_fmap_reverse_pe/`: DWI has no sibling
  DWI reverse; reverse-PE reference lives in fmap with IntendedFor.
  Verifies the new code path.
- `specification/v0.1/protocols/examples/CIDUR_URMC_64dir_v1.yaml`:
  Siemens-dominant 64-direction protocol reference authored from
  actual CIDUR sidecars.
- `specification/v0.1/protocols/examples/CIDUR_URMC_50dir_v1.yaml`:
  GE-dominant 50-direction protocol reference authored from actual
  CIDUR sidecars.

### First live CIDUR run
- All 62 CIDUR DWI sessions assessed successfully (0 failures).
- Output written to `~/Documents/vecta_dwi_cidur_run/` (outside the
  repo, per PHI caution).
- `REPORT.md` in that directory summarizes results.
- Headline finding: **34/62 sessions (55%) triggered `VECTA-DWI-014`**
  — the 50-direction acquisition variant (GE SIGNA Premier + MAGNETOM
  Vida Fit + one SIGNA Artist) lacks a matching PA reverse-PE fmap
  across the cohort, while the 64-direction Siemens Skyra protocol
  includes reverse-PE consistently.
- This is a real, protocol-level DBI finding of exactly the type Paper
  1 is designed to detect and report.

### Verified
- 21 integration tests pass under Python 3.11 (was 20).

### Not committed to repo
- Any per-session CIDUR results (in `~/Documents/vecta_dwi_cidur_run/`).
- The `.bids-validator-output.json` staging file. The source CIDUR
  tree was not modified.

---

## v0.1.0 — 2026-09-19 (draft, literature integration)

Aligning the manuscript draft with `vecta_paper/Vecta_Paper1_Detailed_Literature_Reference_Guide.docx`.

### Added
- `docs/references.yaml` — structured single-source bibliography keyed
  by short ID, containing all Tier A anchors (FAIR, Bridge2AI,
  FAIRSCAPE, BIDS, QSIPrep, EDDY QC, MRIQC, Fortin multisite DTI,
  Nichols COBIDAS, fMRIPrep), Tier B standards + processing + QC +
  provenance, and Tier C dataset-documentation / ML-validation
  references. All with DOIs where available.
- `docs/paper1_prior_art_comparison.md` — feature-by-feature comparison
  of Vecta vs Bridge2AI vs FAIRSCAPE vs FAIR vs BIDS Validator vs
  MRIQC vs EDDY QC vs DTIPrep vs DataLad vs Datasheets/Data Cards.
  Table split into 6 dimensions (scope, unit + evidence, output shape,
  missingness, spec + software engineering, validation methodology).
  Explicit "defensible / not defensible" summary. Fulfills Guide §25
  action item.

### Changed
- `docs/paper1_methods_software.md` rewritten:
  - Introduction paragraph reframed per Guide §17 novelty threat
    matrix — names Bridge2AI + FAIRSCAPE as "closest conceptual and
    implementation neighbors" rather than implying first-of-kind.
  - Deliberate non-claims section extended to include
    "not first-of-kind AI-readiness framework", "does not replace QC",
    "BIDS-valid data are not scientifically invalid", "TBI transport
    does not prove universal generalization".
  - New "Comparator analyses" section describing the 4-way ablation
    (BIDS-only / basic metadata / Vecta / QC) per Guide §25.
  - All `[CITE_*]` stubs replaced with `[[key]]` references resolving
    to `docs/references.yaml`.
  - Added missing Tier A anchors: FAIR, Bridge2AI, FAIRSCAPE, Fortin,
    Nichols/COBIDAS, fMRIPrep, Poldrack 2024 BIDS evolution,
    Karakuzu qMRI-BIDS.

### Still requires user
- Run the 12 systematic prior-art search queries (Guide §18) to
  identify any framework the comparison table misses.
- Read + annotate the 15-paper core set (Guide §21).
- Cross-check the DTIPrep row against the actual DTIPrep publication.

---

## v0.1.0 — 2026-09-19 (draft, expanded fixtures + golden regression)

### Added
- Four new synthetic BIDS fixtures covering additional Spec Blueprint
  §27 coverage cases:
  - `dataset_002_missing_bvec` — DWI has NIfTI + bval but no bvec.
    Verifies `BVEC_COUNT.state=unknown`, plausibility=unknown.
  - `dataset_003_bval_volume_mismatch` — NIfTI has 7 volumes but bval
    has 8 entries. Verifies `BVEC_PLAUSIBILITY.state=extraction_failed`
    from bval/bvec length disagreement.
  - `dataset_005_missing_readout` — PE present but TotalReadoutTime
    absent. Triggers `VECTA-DWI-021` (essential metadata insufficient).
  - `dataset_011_dicom_bids_conflict` — BIDS declares 3.0T,
    source DICOM reports 1.5T. Triggers `VECTA-DWI-060`
    (representation_integrity / transformation-fidelity).
- `tests/integration/test_expanded_fixtures.py` — behavior tests for
  the four new fixtures, parametrized.
- `tests/integration/test_golden_json_regression.py` — golden JSON
  regression tests with normalized-placeholder diffing. Volatile
  fields (UUIDs, ISO timestamps, sha256 hashes, absolute source paths)
  are normalized to placeholders before diffing. Any structural
  behavior change requires an explicit golden update via
  `VECTA_REGEN_GOLDEN=1 pytest`.
- `tests/golden/*.expected.json` — 5 golden reference outputs locked in.

### Verified
- All 20 integration tests pass under Python 3.11.
- Golden regression catches unintentional output changes; goldens
  can be regenerated deterministically after intentional changes.
