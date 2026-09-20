# Paper 1 — Prior-art comparison table (draft)

Per the Detailed Literature Reference Guide §25 and §17 (novelty
threat matrix), the Introduction should not be finalized until Vecta
is compared feature-by-feature against the closest neighboring
frameworks. This document is that comparison.

**Status**: prose-ready draft; each column reflects the framework as
described in its primary reference. All bibliographic entries resolve
from `docs/references.yaml`. Rows that mark Vecta as unique should be
re-checked after the systematic prior-art search (Guide §18) is run,
since new work in this area is fast-moving.

**Purpose of this table**: not to argue that Vecta is universally
superior, but to make explicit where Vecta overlaps with each neighbor
so that the novelty claim is bounded and defensible.

---

## Framework legend

| Short name | Reference | Category |
|---|---|---|
| **Vecta-DWI v0.1** | This paper | Data Birth Integrity for DWI (intended-use conditional) |
| Bridge2AI | `[[bridge2ai_readiness]]` | Biomedical AI-readiness criteria |
| FAIRSCAPE | `[[fairscape]]` | Machine-actionable AI-readiness with provenance |
| FAIR | `[[fair_wilkinson_2016]]` | Universal stewardship principles |
| BIDS Validator | `[[bids_specification; bids_validator]]` | Neuroimaging standards conformance |
| MRIQC | `[[mriqc_esteban_2017]]` | Automated MRI image-quality prediction |
| EDDY QC | `[[eddy_qc_bastiani_2019]]` | DWI QC from preprocessing outputs |
| DTIPrep | DWI-QC prior-art family | Automated DWI quality control |
| DataLad | `[[datalad_halchenko_2021]]` | Distributed data + code + provenance mgmt |
| Datasheets/Data Cards | `[[datasheets_gebru_2021; data_cards_pushkarna_2022]]` | Manual dataset documentation |

---

## Feature-by-feature comparison

Legend for cells: **✓** = strong yes; **~** = partial / adjacent; **✗** = not addressed; **N/A** = out of scope for that framework.

### 1. Scope and intended use

| Feature | Vecta-DWI | Bridge2AI | FAIRSCAPE | FAIR | BIDS Val. | MRIQC | EDDY QC | DTIPrep | DataLad | Datasheets |
|---|---|---|---|---|---|---|---|---|---|---|
| Intended-use conditional (readiness relative to a declared analysis) | ✓ | ~ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ |
| Modality-specific (DWI) | ✓ | ✗ | ✗ | ✗ | ~ | ~ | ✓ | ✓ | ✗ | ✗ |
| Cross-modality by design | future | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Universal principles (independent of any workflow) | ✗ | ~ | ~ | ✓ | ✗ | ✗ | ✗ | ✗ | ~ | ~ |

### 2. Unit of analysis and evidence sources

| Feature | Vecta-DWI | Bridge2AI | FAIRSCAPE | FAIR | BIDS Val. | MRIQC | EDDY QC | DTIPrep | DataLad | Datasheets |
|---|---|---|---|---|---|---|---|---|---|---|
| Subject/session as primary unit | ✓ | N/A | N/A | N/A | ~ | ✓ (image) | ✓ | ✓ | N/A | ~ (dataset) |
| Consumes original DICOM source | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ~ | ✗ |
| Consumes BIDS representation | ✓ | ✗ | ~ | ✗ | ✓ | ✓ | ✓ | ~ | ✓ | ✗ |
| Consumes preprocessing logs / QC outputs | ~ (planned) | ✗ | ~ | ✗ | ✗ | ~ | ✓ | ~ | ✗ | ✗ |
| Explicit source→representation fidelity check (DICOM vs BIDS) | ✓ (`VECTA-DWI-060`) | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |

### 3. Output shape and interpretation

| Feature | Vecta-DWI | Bridge2AI | FAIRSCAPE | FAIR | BIDS Val. | MRIQC | EDDY QC | DTIPrep | DataLad | Datasheets |
|---|---|---|---|---|---|---|---|---|---|---|
| Structured findings with evidence chain | ✓ | ~ | ✓ | ✗ | ~ (errors/warnings) | ~ (metrics) | ~ (metrics) | ~ | ~ (provenance) | ✗ |
| Categorical severity separate from confidence separate from empirical effect | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| No scalar composite score (deliberately) | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ (score is central) | ✗ | ~ | ✓ | ✓ |
| Provisional vs empirically calibrated distinction | ✓ | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ |
| Human-readable, evidence-linked explanation for every finding | ✓ | ~ | ~ | ✗ | ~ | ~ | ~ | ~ | ~ | ✓ (manual) |

### 4. Missingness semantics

| Feature | Vecta-DWI | Bridge2AI | FAIRSCAPE | FAIR | BIDS Val. | MRIQC | EDDY QC | DTIPrep | DataLad | Datasheets |
|---|---|---|---|---|---|---|---|---|---|---|
| 8-state value vocabulary (observed / derived / unknown / not_collected / not_applicable / invalid / extraction_failed / conflict) | ✓ | ✗ | ✗ | ✗ | ~ (errors vs warnings) | ✗ | ✗ | ✗ | ✗ | ✗ |
| `unknown` guaranteed never coerced to `false` (enforced by schema + engine) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Assessment completeness reported alongside every result | ✓ | ~ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (manual) |

### 5. Specification and software engineering

| Feature | Vecta-DWI | Bridge2AI | FAIRSCAPE | FAIR | BIDS Val. | MRIQC | EDDY QC | DTIPrep | DataLad | Datasheets |
|---|---|---|---|---|---|---|---|---|---|---|
| Scientific meaning in versioned specification, not code | ✓ | ~ | ~ | N/A (principles) | ~ (JSON schemas) | ✗ (in code) | ✗ (in code) | ✗ (in code) | ✗ (in code) | N/A (template) |
| JSON Schema validation of both specification and output | ✓ | ~ | ✓ | ✗ | ✓ (specification) | ✗ | ✗ | ✗ | ✗ | ✗ |
| Referential integrity check across output objects | ✓ | ✗ | ~ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Golden output regression tests | ✓ | ✗ | ✗ | ✗ | ✓ | ~ | ~ | ✗ | ✗ | ✗ |
| Deterministic same-input → same-output guarantee | ✓ | ~ | ~ | N/A | ✓ | ~ (ML) | ~ | ~ | ✓ | N/A |
| Explicit software vs data-integrity finding separation | ✓ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ |

### 6. Validation methodology

| Feature | Vecta-DWI | Bridge2AI | FAIRSCAPE | FAIR | BIDS Val. | MRIQC | EDDY QC | DTIPrep | DataLad | Datasheets |
|---|---|---|---|---|---|---|---|---|---|---|
| Freeze-before-external-validation discipline | ✓ (v0.1.0-paper1 tag) | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ |
| Independent multisite transport cohort planned | ✓ | ~ | ~ | ✗ | ~ | ✓ | ✓ | ~ | ✗ | ✗ |
| Reports what does NOT transport as a first-class result | ✓ (planned) | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ |
| Post-freeze changes reserved for next major version | ✓ | ✗ | ✗ | ✗ | ~ | ✓ | ✓ | ~ | ✓ | ✗ |

### 7. Relationship to other frameworks (Vecta's stance)

| Framework | Vecta's stance |
|---|---|
| FAIR `[[fair_wilkinson_2016]]` | FAIR principles are broader in scope and universal; Vecta is intended-use-conditional and modality-specific. Vecta datasets should ideally be FAIR but FAIR-ness alone does not establish processing readiness. |
| Bridge2AI `[[bridge2ai_readiness]]` | Closest broad conceptual neighbor. Vecta is narrower (DWI processing readiness) and deeper (source-to-representation lifecycle with pipeline-anchored evidence). Not a Bridge2AI competitor; a modality-focused instantiation of overlapping principles. |
| FAIRSCAPE `[[fairscape]]` | Closest machine-actionable neighbor. Both use structured provenance/metadata to enable programmatic assessment. Vecta adds a domain-specific criterion engine tied to a specific downstream workflow (QSIPrep) and its documented pipeline requirements. |
| BIDS Validator `[[bids_specification; bids_validator]]` | Complementary. BIDS conformance is one Vecta evidence layer among many. Vecta explicitly demonstrates BIDS-valid cases with material readiness limitations for the intended use, and BIDS-invalid cases where the limitation would not affect intended processing. |
| MRIQC `[[mriqc_esteban_2017]]` | Different lifecycle layer. MRIQC characterizes image-quality outcomes; Vecta characterizes acquisition/source/metadata/representation inputs. Vecta ablations report incremental information beyond MRIQC-style downstream QC. |
| EDDY QC `[[eddy_qc_bastiani_2019]]` | Downstream-QC comparator. Vecta ablations against EDDY QC test whether upstream integrity evidence adds complementary information. Null results (Vecta subsumed by EDDY QC for a specific outcome) are informative. |
| DTIPrep and other DWI-QC prior art | Nearest single-modality overlap. Systematic prior-art search (Guide §18) is required before novelty is finalized. Where overlap exists (gradient checks, metadata checks), Vecta should map it explicitly. |
| DataLad `[[datalad_halchenko_2021]]` | Provenance/reproducibility infrastructure. Vecta's evidence chain is a scientific-content analog to DataLad's data-object provenance. Complementary; DataLad can be used to distribute the Vecta reproducibility package. |
| Datasheets/Data Cards `[[datasheets_gebru_2021; data_cards_pushkarna_2022]]` | Manual documentation frameworks. Vecta operationalizes parts of dataset-documentation intent (motivation, composition, limitations) as executable, evidence-backed automated assessment. |

---

## What this comparison lets Paper 1 claim — and what it does not

### Defensible with this comparison

- The intersection of **source-to-representation traceability** (currently emphasized by DataLad/FAIRSCAPE without a DWI-specific criterion layer), **intended-use conditional readiness** (currently emphasized by Bridge2AI without a modality-specific criterion engine), and **empirical linkage to downstream processing outcomes** (currently emphasized by EDDY QC/MRIQC without an upstream integrity layer) is where Vecta operates.
- Every neighboring framework addresses at least one of these three dimensions; no single neighbor addresses all three integrated for DWI processing readiness with a freeze-before-external-validation methodology.
- Vecta's 8-state value vocabulary and its structural refusal to coerce `unknown` to `false` is a stronger enforcement of missingness discipline than any neighbor.
- The specification-as-data / engine-as-execution separation follows precedents but is unusually strict for a neuroimaging QC-adjacent tool.

### NOT defensible

- Claiming Vecta is the **first** framework to assess biomedical data integrity, AI-readiness, or upstream data properties (Bridge2AI, FAIRSCAPE, MRIQC, EDDY QC all exist).
- Claiming Vecta **replaces** BIDS Validator, MRIQC, or EDDY QC.
- Claiming that DWI-specific automated QC is novel (DTIPrep and related tools address this).
- Claiming that machine-actionable provenance is novel (FAIRSCAPE, DataLad, NIDM address this).
- Claiming universal AI-readiness (Vecta v0.1 is DWI-only).

---

## Follow-up before Introduction finalization (Guide §25)

- [ ] Run the 12 systematic search queries in Guide §18 to identify any framework this table misses.
- [ ] Update this table whenever the search identifies a new closest-prior-art candidate.
- [ ] For each **~** cell above, confirm the partial-support claim against the reference's primary publication.
- [ ] Cross-check DTIPrep row against the actual DTIPrep publication; the current row is based on general familiarity rather than a re-read.
- [ ] After freeze, expand Vecta's row where CIDUR internal analysis actually demonstrates a claimed feature.
