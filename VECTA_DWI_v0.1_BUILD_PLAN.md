# Vecta-DWI v0.1 — Build Plan

**Status:** planning draft — no code yet
**Session:** 2026-09-19
**Reference protocol docs:** `../vecta_paper/` (6 .docx files, treat as frozen inputs)
**Prior artifact:** `../dbi/` (DBI v1.0.5, frozen 2026-04-10; do not modify)

---

## 1. What this repo is

This repo is the **implementation** of the Vecta-DWI v0.1 specification described in `vecta_paper/`. It is the software artifact whose immutable release will be tagged `vecta-dwi-v0.1.0-paper1` and cited by Paper 1.

It is **not**:
- A rewrite or version bump of `dbi/`. DBI v1.0.5 is a different scientific object (series-level scalar composite; multi-modality) and remains frozen in the sibling `../dbi/` directory.
- A general-purpose imaging QC tool. Scope is DWI processing / structural-connectomics readiness (`dwi_connectomics` profile).
- A place for scientific meaning to live in Python constants. All variables, criteria, profiles, protocols, tolerances, and evidence live in versioned specification files under `specification/v0.1/`. Python (when added) is an execution engine.

## 2. Architectural decisions (closed)

| # | Decision | Rationale |
|---|----------|-----------|
| A1 | **Fresh package**, not an evolution of `dbi/` | Paper 1's freeze-before-external-validation discipline requires DBI v1 outputs to remain reproducible under their original code path. Vecta's evidence/finding/readiness data shape is also fundamentally different from DBI's scalar composite. |
| A2 | **Session** is the primary unit of analysis (subject / session / profile execution), not series | Matches Vecta-DWI docs and matches the way DWI preprocessing outcomes (QSIPrep success, connectome availability) are naturally scoped. |
| A3 | **No scalar score in v0.1** | Explicit in Output Dictionary §12/§34 and Spec Blueprint §2. Provisional severity and empirical effect remain separate. Numeric penalties from DBI v1 are not carried over. |
| A4 | **Multi-file specification** under `specification/v0.1/` | Matches Spec Blueprint §4. Domain reviewers can read variable / criterion / profile / evidence YAML without touching Python. |
| A5 | **Modular software architecture** (collectors / normalizers / derivations / rules / builders / serializers), to be added in later sessions | Matches Spec Blueprint §22 and Output Tech Spec §67. This session does not add any Python. |
| A6 | **8-state value vocabulary** (observed, derived, unknown, not_collected, not_applicable, invalid, extraction_failed, conflict) | Matches Output Tech Spec Table 3. Replaces DBI v1's boolean `na`. |
| A7 | **Local-only git for now** | GitHub remote deferred until the first vertical slice runs. |

## 3. Repository layout

```
vecta-dwi/
├── .gitignore
├── VECTA_DWI_v0.1_BUILD_PLAN.md          ← this file
│
├── specification/
│   └── v0.1/
│       ├── manifest.yaml                  ← release identity (populated)
│       ├── CHANGELOG.md                   ← populated
│       ├── variables/
│       │   ├── scanner.yaml               ← populated (4 vars, first slice)
│       │   ├── acquisition.yaml           ← populated (9 vars, first slice)
│       │   └── bids.yaml                  ← populated (3 vars, first slice)
│       ├── criteria/
│       │   └── dwi_connectomics.yaml      ← populated (VECTA-DWI-014 detailed; 001, 021 stubs)
│       ├── profiles/
│       │   └── dwi_connectomics.yaml      ← populated
│       ├── protocols/
│       │   └── examples/                  ← placeholder (needs CIDUR + TBI protocol refs)
│       ├── evidence/
│       │   └── evidence_registry.yaml     ← populated (EV-DWI-PE-001)
│       ├── tolerances/
│       │   └── default_tolerances.yaml    ← populated (placeholder values, need justification)
│       ├── schemas/                       ← placeholder (JSON Schemas to be authored)
│       └── registries/
│           └── enums.yaml                 ← populated
│
└── tests/
    ├── unit/          ← placeholder
    ├── integration/   ← placeholder
    ├── synthetic/     ← placeholder (14 synthetic datasets listed in Spec Blueprint §27)
    └── golden/        ← placeholder
```

Not created this session: `src/vecta/` Python package, `pyproject.toml`, JSON schemas under `specification/v0.1/schemas/`. These are next-session work.

## 4. First vertical slice — 10 foundational variables

Per Spec Blueprint §43-44. IDs follow the `VECTA.DWI.<DOMAIN>.<NAME>` convention (Output Tech Spec Table 2).

| # | Variable ID | Lifecycle layer | Source | State |
|---|-------------|-----------------|--------|-------|
| 1 | `VECTA.DWI.SCANNER.MANUFACTURER` | L1 | DICOM `(0008,0070)` / BIDS `Manufacturer` | stubbed |
| 2 | `VECTA.DWI.SCANNER.MODEL` | L1 | DICOM `(0008,1090)` / BIDS `ManufacturersModelName` | stubbed |
| 3 | `VECTA.DWI.SCANNER.FIELD_STRENGTH` | L1 | DICOM `(0018,0087)` / BIDS `MagneticFieldStrength` | stubbed |
| 4 | `VECTA.DWI.SCANNER.SOFTWARE_VERSION` | L1 | DICOM `(0018,1020)` / BIDS `SoftwareVersions` | stubbed |
| 5 | `VECTA.DWI.ACQ.VOXEL_SIZE` | L1 | NIfTI header pixdim / BIDS `dwi.json` | stubbed |
| 6 | `VECTA.DWI.ACQ.VOLUME_COUNT` | L4 | NIfTI header dim[4] | stubbed |
| 7 | `VECTA.DWI.ACQ.BVAL_COUNT` + `SHELL_COUNT` (derived) | L4 | `.bval` file | stubbed |
| 8 | `VECTA.DWI.ACQ.BVEC_COUNT` + `BVEC_PLAUSIBILITY` | L4 | `.bvec` file | stubbed |
| 9 | `VECTA.DWI.ACQ.PE_DIRECTION` | L1 | DICOM InPlanePhaseEncodingDirection + vendor / BIDS `PhaseEncodingDirection` | stubbed |
| 10 | `VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE` | L1 (derived) | Requires #9 + inventory | stubbed |

Plus these three carried in `bids.yaml`, treated as part of the same slice per Paper 1 §14:
- `VECTA.DWI.ACQ.TOTAL_READOUT_TIME_PRESENT`
- `VECTA.DWI.BIDS.VALIDATOR_ERROR_COUNT` / `VALIDATOR_WARNING_COUNT`
- `VECTA.DWI.BIDS.REQUIRED_SERIES_PRESENT`

Each stub carries: stable ID, definition version 0.1.0, lifecycle layer, allowed states, source mapping, dependencies, missing-state semantics, and `TODO`s where extraction algorithms and evidence refs will be filled in.

## 5. Worked example: `VECTA-DWI-014` (missing reverse PE)

Fully specified in `specification/v0.1/criteria/dwi_connectomics.yaml`. The full end-to-end chain:

```
DICOM/BIDS collector
   └─→ VECTA.DWI.ACQ.PE_DIRECTION      (observed | unknown)
   └─→ [inventory of other acquisitions]
         └─→ VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE  (true | false | unknown)
              └─→ VECTA-DWI-014
                    condition: REVERSE_PE_AVAILABLE == false
                    → Finding {
                        category: acquisition_integrity
                        severity: major (status=provisional)
                        confidence: high
                        potential_effects: [distortion_correction_strategy_constrained, ...]
                        evidence_refs: [EV-DWI-PE-001]
                      }
                    → ReadinessSummary.processing_readiness: contributes to ready_with_limitations
                    → vecta.json.findings[]
                    → vecta.tsv column `reverse_pe_available` = false, `major_finding_count` += 1
                    → report.html "Priority findings" section
                    → tests/golden/dataset_004_missing_reverse_pe.expected.json
```

Distinct expected behavior when PE direction is unknown (Output Tech Spec §55):
- `REVERSE_PE_AVAILABLE.state = unknown`, value = null
- `VECTA-DWI-014.status = unknown`, no finding emitted
- ReadinessSummary may become `review_required` per profile rule
- **Prohibited**: emitting `reverse_pe_available = false`

## 6. Reuse from `dbi/` (when Python starts)

DBI v1 has real value as a source of validated logic even though the output shape differs. Lift these — don't reinvent:

| DBI v1 asset | Where it goes in Vecta-DWI |
|--------------|---------------------------|
| Series classification regexes (`dbi_v1_config.yaml` → `classification_rules`) | Vecta collector for identifying DWI vs T1 vs fmap series from DICOM |
| `scanner_cluster` derivation (DBI spec §2) | Vecta variable, used as stratification covariate (not a component) |
| Universal DICOM tag map (`tags_universal`, `tags_spatial`) | `specification/v0.1/variables/*.yaml` source_field entries |
| Community-standards naming references (BIDS, ENIGMA, ADNI citations in `automation_conventions`) | `specification/v0.1/evidence/evidence_registry.yaml` — as evidence entries, not as scoring components |
| `derived_scan_naming` markers (ADC/FA/TRACE etc.) | Vecta collector logic for excluding derived series from raw DWI evidence |
| Modality-aware `na` design principle | Formalized as Vecta's `not_applicable` state |
| DBI v1 open clarifications §9 (de-ID, localizer, protocol regex) | Carried forward to Section 8 below — still open |

Deliberately not lifted:
- The scalar composite `DBI_series = Σ w_c · score_c / Σ w_c` and its component scores M/P/G/S/N. Vecta v0.1 does not emit a scalar score.
- Weight tables in `dbi_v1_config.yaml → weights`.
- Multi-modality scoring for BOLD/T1/T2/FLAIR/ASL/SWI. Vecta-DWI is DWI-only in v0.1.

## 7. What remains before v0.1 can freeze

Concrete work packages, in rough dependency order:

1. **Domain expert review** of the 10 foundational variables + `VECTA-DWI-014` (Study Design §14, Paper 1 §30). Multidisciplinary panel: DWI scientist, MR physicist, technologist, data engineer, biostatistician, BIDS/reproducibility expert.
2. **Close open decisions** (Section 8).
3. **JSON Schemas** for output objects under `specification/v0.1/schemas/`: `vecta_output`, `evidence`, `variable_result`, `derived_metric`, `criterion_result`, `finding`, `readiness`, `provenance`, `assessment_status`, `cohort_summary`, `research_outcome` (Output Tech Spec §42).
4. **Python engine** — first vertical slice per Output Tech Spec §66: shared enums + `EvidenceRecord` + `VariableResult` + serialize PE direction and reverse-PE availability + `CriterionResult` + `Finding` + `VECTA-DWI-014` output + minimal `ReadinessSummary` + one assembled valid `vecta.json` + schema validation + one-row TSV + simple HTML + golden fixtures.
5. **CIDUR pilot** — 10-20 stratified sessions, manual review (Study Design §14, Paper 1 §29).
6. **Outcome labeling manual** and manual-intervention rubric (independent of the Vecta software; Paper 1 §26-28).
7. **QSIPrep/QSIRecon log inventory** on CIDUR to determine what outcome data actually exists.
8. **50-100 session pilot** (Spec Blueprint §29 stage 2).
9. **Full CIDUR analysis** → **specification review** → **freeze `vecta-dwi-v0.1.0-paper1`**.
10. **TBI common-variable mapping** without inspecting outcome-driven results (Study Design §34).
11. **Frozen TBI validation**.

## 8. Open decisions — must close before freeze

Items marked (DBI) carry over from DBI v1 clarifications §9; items marked (V) are new to Vecta.

| ID | Decision | Blocks |
|----|----------|--------|
| D1 (DBI+V) | **De-identification path** — compute on pre-BIDS DICOM (Option A) or de-identified DICOM (Option B)? | Collector design; privacy serializer |
| D2 (DBI+V) | **Localizer inclusion** — include in cohort summaries or exclude? | Cohort aggregation contract |
| D3 (DBI) | **Prospective protocol token** — replace `PROTO_[A-Z0-9_]+` example with real CIDUR/TBI token(s) | Protocol reference files |
| D4 (V) | **Tolerance values** — voxel size, TE, b-shell grouping, vector norm — currently placeholders in `tolerances/default_tolerances.yaml` | Criterion evaluation |
| D5 (V) | **CIDUR inventory** — subject/session counts, DICOM availability, existing QSIPrep/QSIRecon runs and logs | Whether CIDUR is full development cohort or source-lifecycle substudy (Study Design §5) |
| D6 (V) | **TBI cohort finalization** — verified N, site structure, common Core evidence availability | TBI validation projection (Paper 1 §36) |
| D7 (V) | **Primary outcome operational definition** — what exactly constitutes "successful predefined preprocessing without major manual intervention" | Analysis projection, `ResearchOutcome` labeling manual (Paper 1 §24, §26) |
| D8 (V) | **Manual intervention rubric** — frozen none/minor/major/unrecoverable definitions with worked examples | Outcome labeling (Paper 1 §28) |
| D9 (V) | **CIDUR + per-TBI-site protocol reference files** | `specification/v0.1/protocols/examples/*.yaml` |
| D10 (V) | **IRB/DUA/data-owner permission confirmations** — CIDUR secondary methodological use; TBI multisite methodological validation; identifier publication policy | Paper 1 §51, before any full-cohort run |
| D11 (V) | **Site identifier publication policy** — publish site names or code them? | Manuscript and cohort summary export |

## 9. Immediate next-session tasks

1. Draft JSON Schemas for `evidence`, `variable_result`, `finding`, `criterion_result`, `readiness`, and top-level `vecta_output`. YAML variable/criterion files should validate against a variable/criterion schema.
2. Circulate this build plan + the specification stubs for domain expert review (Section 7 item 1).
3. Begin closing D1, D2, D5 (highest-leverage decisions).
4. Draft the outcome labeling manual (D7, D8) as its own standalone document under `specification/v0.1/` or as a companion doc — this is independent of the Vecta software and can proceed in parallel.

## 10. Follow-up housekeeping (parent repo)

`vecta-dwi/` is a nested git repo inside `../` (the existing `vecta/` repo). The parent repo will show `vecta-dwi/` as untracked. Two clean options, either fine:

- Add `vecta-dwi/` to the parent's `.gitignore` (silent from parent perspective).
- Register `vecta-dwi/` as a submodule of the parent (explicit link, still independent history).

Not decided this session — leave for a later housekeeping pass.
