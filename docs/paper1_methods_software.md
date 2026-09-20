# Paper 1 — Software and specification methods (draft)

Working draft of the software-methods sections of the Paper 1 manuscript.
Covers: the DBI construct as operationalized in software, the Vecta-DWI
specification structure, the engine architecture, the freeze release
methodology, and the technical validation strategy. Empirical results
(CIDUR internal, TBI transport) are excluded — they will be filled in
after the analyses run.

**Status**: prose-ready draft; citation stubs `[CITE_*]` marked for
insertion. All numeric claims about the software (variable counts,
schema counts, test counts) reflect `vecta-dwi` commit `7529290`.

---

## Data Birth Integrity as a machine-actionable construct

Reliability of diffusion-MRI processing pipelines depends on data
properties present or absent long before preprocessing runs. Existing
frameworks address complementary but distinct parts of the lifecycle:
the Brain Imaging Data Structure (BIDS) [CITE_BIDS] standardizes file
organization and metadata representation, image-quality control tools
such as MRIQC [CITE_MRIQC] and EDDY QC [CITE_EDDYQC] characterize
post-acquisition image properties, and preprocessing workflows such as
QSIPrep [CITE_QSIPREP] enforce implicit requirements on the inputs they
accept. None of these individually operationalize the question of
whether a dataset carries the acquisition- and representation-level
evidence a specified downstream analysis actually needs.

We define **Data Birth Integrity (DBI)** as the degree to which the
information, structure, provenance, acquisition characteristics, and
representation needed for a specified downstream scientific use are
present, internally consistent, traceable, and appropriately preserved
from acquisition and source data into the analysis-ready
representation. DBI is deliberately intended-use conditional: a dataset
can be sufficient for one analysis and insufficient for another. This
paper operationalizes DBI for diffusion-MRI preprocessing and
structural-connectomics readiness (`dwi_connectomics` profile).

DBI is distinct from BIDS conformance (BIDS is one evidence layer,
not a definition of readiness), from image quality (image-quality
metrics are complementary downstream evidence, not upstream integrity),
from diagnostic adequacy (out of scope for this study), and from
biological or model-performance validity (both are downstream
consequences whose relationship to DBI is testable but not assumed).

We formalize DBI as a versioned, machine-readable **specification**
executed by an open **engine** rather than as an informal checklist.
This distinction is central to Paper 1's methodological contribution:
the specification is a scientific contract that could in principle be
reimplemented independently, and the engine is a reproducible execution
of that contract. Both are frozen for the paper (release tag
`vecta-dwi-v0.1.0-paper1`) so results remain regeneratable.

## Lifecycle ontology

We adopt a nine-layer lifecycle ontology (L0–L9) describing where
evidence about a dataset originates. Paper 1 directly operationalizes
layers L1–L6.

| Layer | Content |
|-------|---------|
| L0 | Study design / intended use (out of scope for automated evaluation) |
| L1 | Acquisition (protocol, scanner, sequence parameters) |
| L2 | Source data (DICOM objects, series, and instances) |
| L3 | Metadata / provenance |
| L4 | Conversion and standardized representation (NIfTI/BIDS) |
| L5 | Signal / image quality |
| L6 | Processing readiness |
| L7 | Quantitative measurement reliability (Paper 2) |
| L8 | Model reliability / generalization (Paper 3) |
| L9 | Scientific inference |

Every Vecta variable carries a `lifecycle_layer` field so findings can
be classified by where the evidence originated, distinguishing (for
example) an acquisition-origin limitation from a
conversion-representation limitation.

## Specification structure

The Vecta-DWI v0.1 specification lives under
`specification/v0.1/` and consists of nine components, each versioned
independently and referenced by a top-level `manifest.yaml`:

  - **`variables/`** — machine-readable variable contracts (16 in the
    v0.1 release, across five domains: scanner, acquisition, DICOM
    source, BIDS, provenance).
  - **`criteria/`** — declarative rules that evaluate one or more
    variables under a profile and emit a finding when triggered.
  - **`profiles/`** — intended-use declarations
    (`dwi_connectomics.yaml`) specifying required and preferred
    evidence, essential metadata, and which criteria apply.
  - **`protocols/`** — study/site protocol references (deferred to
    Paper 1 freeze; templates present).
  - **`evidence/`** — a registry of scientific justifications, cited
    independently by any criterion that uses them. Distinguishes six
    evidence classes: formal standard, pipeline requirement, peer-
    reviewed literature, expert consensus, empirical internal,
    empirical external.
  - **`tolerances/`** — numeric comparison tolerances (voxel size, TE,
    b-shell grouping, vector norm), each carrying a justification
    basis.
  - **`schemas/`** — JSON Schema Draft 2020-12 contracts, split into
    `input/` (validate the spec YAMLs themselves) and `output/`
    (validate the canonical `vecta.json`). 14 schemas in v0.1, all
    verified against Draft 2020-12 meta-schema.
  - **`registries/`** — shared enumerations (value states, criterion
    status, severity, confidence, readiness state, action classes,
    finding categories).
  - **`CHANGELOG.md`** — every scientific or technical change with its
    versioning consequence.

Each variable object declares a stable ID (`VECTA.DWI.<DOMAIN>.<NAME>`),
definition version, lifecycle layer, allowed value states, source
mappings (with exact DICOM tags and BIDS fields where applicable),
canonical units, validity constraints, extraction algorithm identifier,
missing-state semantics, and applicable tolerance references. Each
criterion declares its required variables, the profile(s) it applies
to, a declarative condition tree, and a finding template capturing
severity, severity basis, confidence, potential effects, and
recommended actions.

## Value state vocabulary

Every observation is emitted in one of eight distinct states, none of
which are collapsed at any layer of the pipeline:

  - `observed` — value determined from evidence.
  - `derived` — value calculated from other observed/derived values.
  - `unknown` — evidence insufficient to determine value.
  - `not_collected` — known-by-design not to have been acquired.
  - `not_applicable` — variable does not apply to this profile.
  - `invalid` — source value exists but violates validity rules.
  - `extraction_failed` — source may contain the value but parsing failed.
  - `conflict` — multiple sources disagree beyond tolerance.

This vocabulary is enforced by JSON Schema and by the referential
integrity checker before any output is written. In particular,
`unknown` is never coerced to `false`. This is a structural rather
than incidental property of the specification: because criteria
distinguish state-based predicates from value-based predicates, a
criterion evaluated over an `unknown` variable returns
`criterion_status: unknown` and emits no finding, rather than a false
negative or a spurious triggered finding.

## Software architecture

The Vecta-DWI engine is deliberately generic and interprets the
specification rather than embedding scientific meaning in code. The
package layout is:

```
src/vecta/
├── enums.py            # runtime mirror of registries/enums.yaml
├── models.py           # Pydantic v2 models mirroring output schemas
├── spec/loader.py      # loads + validates the spec at start-up
├── collectors/
│   ├── bids.py         # BIDS entity discovery + sidecar/companion reads
│   └── dicom.py        # DICOM tree scan, group by SeriesInstanceUID
├── extract/
│   ├── scanner.py      # manufacturer/model/field/software
│   ├── acquisition.py  # voxel/volume/bval/shell/bvec extractors
│   ├── bids.py         # validator counts + required-series presence
│   ├── pe.py           # PE direction + TotalReadoutTime presence
│   └── dicom_source.py # source-integrity + transformation-fidelity
├── derive/
│   └── reverse_pe.py   # reverse-PE availability derivation
├── criteria/engine.py  # declarative condition evaluator + finding assembly
├── output/
│   ├── assemble.py     # full Assessment assembly + schema validation
│   ├── tsv.py          # versioned per-session TSV projection
│   ├── cohort.py       # cohort aggregation with three explicit denominators
│   └── html.py         # Jinja2 renderer, canonical-JSON only
└── cli.py              # vecta assess | aggregate | validate-spec | explain | version
```

Every extractor returns a typed `VariableResult` with explicit state,
evidence references, extractor version, and computation timestamp. The
criteria engine consumes these results and emits typed
`CriterionResult` and `Finding` objects. The output assembler
composes all objects into a top-level `Assessment`, serializes it to
canonical JSON, validates the JSON against
`schemas/output/vecta_output.schema.json`, and runs referential
integrity checks (every evidence reference resolves; every finding's
criterion exists; readiness references only valid finding IDs; software
errors never appear as data-integrity findings).

TSV, HTML, and cohort projections are derived views of the canonical
JSON; they cannot contain scientific information absent from or
irreproducible from the canonical output.

## Explicit scientific separations

The specification and engine maintain five deliberate separations that
distinguish Vecta from a scalar-scoring quality-control tool. Each
separation is enforced by the schema, the engine, or both:

  1. **Severity** (provisional interpretation for a stated intended use)
     is a categorical label carrying an `evidence_basis` chain. It is
     not a probability.
  2. **Confidence** describes certainty that the observation itself is
     correct, independent of severity. A finding can be severity=major
     and confidence=low, and vice versa.
  3. **Evidence basis** distinguishes standard-derived, pipeline-derived,
     literature-supported, expert-supported, empirically-internal, and
     empirically-external justifications.
  4. **Empirical status** records whether a criterion's link to
     downstream consequences has been empirically evaluated. In v0.1
     all criteria are `not_tested`; Paper 1's TBI validation will
     populate this field for the criteria that transport.
  5. **Predictive risk** (calibrated probability of a downstream
     outcome) is not emitted in v0.1. If introduced later, it would
     require an explicit calibration reference and applicable
     population.

We deliberately do not emit an aggregate 0–1 or 0–100 Vecta score in
v0.1. This departs from earlier approaches (e.g., a scalar
composite over metadata / naming / gradient / spatial / naming-
compliance components that we and others have previously explored). An
aggregate score requires a defensible calibration strategy tied to a
specified outcome; without that, the number is uninterpretable. Paper 1
therefore reports variables, findings, and profile-relative readiness,
not a Vecta score.

## Cohort A: CIDUR development

The CIDUR cohort at URMC provides original DICOM alongside standardized
BIDS representation and QSIPrep/QSIRecon processing outcomes. This
combination lets us evaluate the full L1→L6 lifecycle within one
cohort, including transformation-fidelity checks that require both the
source DICOM and the derived BIDS representation. CIDUR is used as the
development cohort: variables, criteria, and tolerances may be revised
before freeze based on internal evidence.

## Freeze: `vecta-dwi-v0.1.0-paper1`

Before the primary TBI validation analysis, the software, the
specification, the JSON schemas, the intended-use profile, the
protocol/tolerance definitions, the outcome-labeling protocol, and the
analysis projection are frozen in a single immutable git tag,
`vecta-dwi-v0.1.0-paper1`. Any subsequent change requires either a
patch-level release (documentation or non-behavior-changing bug fix
with regression test) or a new version. Changes that affect a
criterion's scientific behavior are reserved for `v0.2.0`, informed
by Paper 1 results and not folded back into `v0.1`. This freeze
boundary is the single most important methodological property of the
study design: it converts the CIDUR-to-TBI evaluation from a
tune-and-report exercise into an independent transportability test.

## Cohort B: multisite TBI validation

The multisite TBI cohort (approximately 600 subjects across multiple
sites, two timepoints per subject; final N to be verified before
analysis) provides heterogeneous scanner, protocol, and site
distributions but does not (initially) include original DICOM. The
frozen specification is applied to TBI using only the Core module
variables evaluable from BIDS-standardized evidence. DICOM-only
variables (Source module) remain `unknown` for TBI sessions and are
never coerced to `false`. The primary transport analysis is therefore
scoped to the frozen Core subset evaluable in both cohorts; Source
module results remain a CIDUR-only lifecycle contribution.

## Technical validation

The engine is validated in three layers before empirical analysis:

  1. **Meta-schema validation** confirms every JSON Schema is a
     valid Draft 2020-12 schema.
  2. **Specification validation** loads each variable, criterion, and
     profile YAML at engine start and validates it against the
     corresponding input schema. Referential integrity is checked:
     every criterion in the profile must exist; every variable a
     criterion requires must exist; every evidence reference must
     resolve. Invalid specifications abort execution before any
     dataset is touched.
  3. **Golden output regression**: 5 synthetic fixtures with frozen
     expected outputs, diffed after normalizing volatile fields
     (UUIDs, timestamps, file hashes, absolute paths). Any structural
     change to output requires an explicit golden update.

Additional behavior tests exercise the full pipeline on 7 synthetic
BIDS fixtures (some with matching DICOM), covering the reference case,
missing complementary phase encoding, unknown PE direction (the
Output Tech Spec §55 prohibited case, verified via an explicit
regression), missing gradient files, bval/volume count mismatch,
missing readout metadata, and DICOM/BIDS field-strength conflict. All
20 integration tests pass on the frozen release.

## Reproducibility

The Paper 1 reproducibility package includes:

  - The frozen software tag `vecta-dwi-v0.1.0-paper1`.
  - A container / environment lock (pending — to be produced at freeze
    time).
  - All specification YAMLs, JSON schemas, and evidence registry.
  - The complete synthetic fixture set with golden expected outputs.
  - The versioned per-session TSV projection map and cohort
    aggregation definitions.
  - The analysis projection joining Vecta variables to independently
    labeled downstream outcomes.

Raw CIDUR and TBI data are not redistributable and are not included.
The specification, engine, synthetic fixtures, and golden outputs are
sufficient to independently reproduce every element of the Vecta
assessment pipeline, and to reproduce every aggregate table and figure
in the paper given a valid dataset in place.

## Deliberate non-claims

Consistent with the intended-use scoping of the DBI construct, the
paper does not claim:

  - that Vecta certifies clinical or diagnostic adequacy;
  - that a `ready` readiness state guarantees valid biological
    measurement or downstream analytic correctness;
  - that a triggered finding causally predicts pipeline failure —
    observed effects reported in Results should be interpreted as
    associations subject to the study's site, scanner, and protocol
    confounding structure;
  - that BIDS conformance is equivalent to processing readiness;
  - that processing success (Paper 1) implies measurement validity
    (Paper 2).

## Citation stubs to insert

  - `[CITE_BIDS]` — Gorgolewski et al., 2016 (BIDS)
  - `[CITE_MRIQC]` — Esteban et al., 2017 (MRIQC)
  - `[CITE_EDDYQC]` — Bastiani et al., 2019 (EDDY QC)
  - `[CITE_QSIPREP]` — Cieslak et al., 2021 (QSIPrep)
  - `[CITE_DCM2NIIX]` — Li et al., 2016 (dcm2niix)
  - `[CITE_FSL_TOPUP]` — Andersson et al., 2003 (topup)
  - `[CITE_BIDSVALIDATOR]` — bids-validator
  - `[CITE_ENIGMA_DTI]` — Thompson et al., 2020 (ENIGMA-DTI)
  - `[CITE_ADNI]` — Jack et al., 2008 (ADNI MRI procedures)
  - `[CITE_DATALAD]` — Halchenko et al., 2021 (DataLad)

---

*Draft as of 2026-09-19. Empirical results (CIDUR internal, TBI
transport, ablation vs BIDS/QC baselines) are excluded and will be
inserted after the analyses run.*
