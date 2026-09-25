# Learning Vecta-DWI: Engineering, Theory, and Code

**Author**: Claude (Anthropic) working with Phinda Ndagijimana  
**Project**: Vecta-DWI v0.1 — Data Birth Integrity assessment for diffusion-weighted MRI  
**Purpose**: Document every task, concept, and engineering decision in a form the researcher can study

---

## Table of Contents

1. [The Problem and the Solution](#1-the-problem-and-the-solution)
2. [Theory: Data Birth Integrity (DBI)](#2-theory-data-birth-integrity-dbi)
3. [DWI and BIDS Background](#3-dwi-and-bids-background)
4. [Python Project Setup — pyproject.toml and src layout](#4-python-project-setup)
5. [Specification Design — YAML Variables, Criteria, Profiles](#5-specification-design)
6. [JSON Schema — Contracts for Inputs and Outputs](#6-json-schema)
7. [Enums — Python mirrors of YAML registries](#7-enums)
8. [Pydantic v2 — Typed Data Models](#8-pydantic-v2)
9. [Spec Loader — Reading YAML and Validating Against Schema](#9-spec-loader)
10. [BIDS Collector — Walking the Directory Tree](#10-bids-collector)
11. [PE Extractor — Phase Encoding Direction Logic](#11-pe-extractor)
12. [Acquisition Extractor — bval/bvec and Gradient Analysis](#12-acquisition-extractor)
13. [Reverse-PE Deriver — Checking fmap IntendedFor](#13-reverse-pe-deriver)
14. [DICOM Collector — Source Integrity](#14-dicom-collector)
15. [Criteria Engine — Evaluating Conditions Against Variables](#15-criteria-engine)
16. [Output Assembler — Building the vecta.json](#16-output-assembler)
17. [TSV Projector and Cohort Aggregator](#17-tsv-projector-and-cohort-aggregator)
18. [HTML Report Renderer — Jinja2 Templates](#18-html-report-renderer)
19. [CLI Design — argparse and Subcommands](#19-cli-design)
20. [Testing — pytest, Synthetic Fixtures, Golden Outputs](#20-testing)
21. [Research Module — QSIPrep Outcome Labeling and Join](#21-research-module)
22. [SLURM and Singularity — HPC Job Submission](#22-slurm-and-singularity)
23. [Controlled Defect Injection — Validating Criteria](#23-controlled-defect-injection)
24. [Statistical Methods — Wilson CIs, Sensitivity, NPV](#24-statistical-methods)
25. [Key Bugs Found and What They Taught](#25-key-bugs-found-and-what-they-taught)
26. [Manuscript Integration — Writing in the Loop](#26-manuscript-integration)
27. [Concept Glossary](#27-concept-glossary)

---

## 1. The Problem and the Solution

### 1.1 Why does preprocessing fail?

Diffusion-weighted MRI (DWI) preprocessing pipelines like QSIPrep, FSL eddy, and MRtrix3 have specific requirements. They need:

- A gradient table (`.bvec` file) with unit-norm vectors pointing in the right directions
- A b-value file (`.bval`) matching the number of volumes
- A signed phase-encoding direction (`PhaseEncodingDirection: "j-"` or `"j"`) in the JSON sidecar
- A total readout time (`TotalReadoutTime`) for distortion correction
- A reverse phase-encoding reference acquisition (EPI fieldmap) for susceptibility distortion correction (SDC)

If any of these are missing, the pipeline either **crashes with an error** or **silently produces degraded output** — sometimes without any error message.

The problem is: there was no tool that checked for these requirements *before* running the pipeline. Researchers discovered the problem only after wasting hours of compute time.

### 1.2 What Vecta does

Vecta-DWI evaluates a BIDS-converted DWI session against a declared *intended-use profile* and returns a **readiness state** with **criterion-level attribution** — before any preprocessing. It answers: "Is this data ready for this specific pipeline?"

Critically, it does *not* preprocess data. It only reads metadata.

### 1.3 The architecture in one sentence

A versioned YAML specification (variables + criteria + profiles) is loaded, evaluated against extracted metadata, and assembled into a structured JSON output with a binary readiness verdict per criterion.

---

## 2. Theory: Data Birth Integrity (DBI)

### 2.1 Definition

**Data Birth Integrity (DBI)** is defined as:

> The degree to which the information, structure, and acquisition characteristics needed for a specified downstream use are present, traceable, and preserved from acquisition into the analysis-ready representation.

Three words matter here: *present* (the field exists), *traceable* (we can confirm where it came from), *preserved* (it hasn't been corrupted or dropped in conversion).

### 2.2 Four properties of DBI

The framework was built around four formal properties:

| Property | What it means |
|----------|---------------|
| **Intended-use conditionality** | Readiness is only meaningful relative to a declared downstream use. A session that is ready for tractography may not be ready for tensor fitting. |
| **Null safety** | An absent variable is not the same as a variable with value zero. Missing metadata is treated as `unknown`, not as a safe default. |
| **Determinism** | Given the same inputs and specification version, Vecta always produces the same output. No randomness, no environment-dependent behavior. |
| **Version-pinning** | Every output records the exact specification version that produced it. Assessment results from different spec versions are not comparable without re-running. |

### 2.3 Lifecycle layers

DWI data passes through several layers before it reaches the analysis-ready form:

```
Scanner acquisition
    ↓
DICOM files (raw from scanner)
    ↓
dcm2niix conversion (DICOM → NIfTI + JSON sidecar + bval/bvec)
    ↓
BIDS dataset (organized directory structure)
    ↓
QSIPrep preprocessing
    ↓
Connectivity analysis (tractography, connectome)
```

Vecta currently evaluates layers 3 and 4 (BIDS + optional DICOM). Problems at any earlier layer propagate forward invisibly.

### 2.4 Readiness states

Vecta produces one of four states per session:

| State | Meaning |
|-------|---------|
| `ready` | No criteria triggered |
| `ready_with_limitations` | Non-blocking criteria triggered (pipeline will run but with limitations) |
| `review_required` | A review criterion returned `unknown` — human judgment needed |
| `not_ready` | A blocking criterion triggered — pipeline cannot run |

---

## 3. DWI and BIDS Background

### 3.1 What is DWI?

Diffusion-weighted MRI measures water diffusion in brain tissue. The signal in each voxel depends on how water diffuses along a specific direction (gradient direction). By acquiring many volumes with different gradient directions, we can reconstruct the diffusion tensor or fiber orientation distribution.

Key parameters:
- **b-value** (`b=1000 s/mm²`): diffusion weighting strength. b=0 is a reference (no diffusion weighting).
- **gradient direction** (in `.bvec`): a unit vector `[x, y, z]` specifying which direction was diffusion-weighted.
- **PhaseEncodingDirection**: the axis along which the EPI readout happens. EPI distortion occurs along this axis.

### 3.2 What is BIDS?

Brain Imaging Data Structure (BIDS) is a standard way to organize neuroimaging data. Key conventions:

```
BIDS_root/
  sub-001/
    ses-1/
      dwi/
        sub-001_ses-1_acq-64dirax_dir-ap_dwi.nii.gz   ← image data
        sub-001_ses-1_acq-64dirax_dir-ap_dwi.bval      ← b-values
        sub-001_ses-1_acq-64dirax_dir-ap_dwi.bvec      ← gradient vectors
        sub-001_ses-1_acq-64dirax_dir-ap_dwi.json      ← sidecar metadata
      fmap/
        sub-001_ses-1_dir-pa_epi.nii.gz                ← reverse-PE fieldmap
        sub-001_ses-1_dir-pa_epi.json
```

The **sidecar JSON** is critical. It contains metadata that dcm2niix extracted from the DICOM header, including:
- `PhaseEncodingDirection`: `"j-"` (posterior-to-anterior), `"j"` (anterior-to-posterior)
- `TotalReadoutTime`: the EPI readout duration in seconds (needed for topup/eddy)
- `Manufacturer`, `ManufacturersModelName`, `MagneticFieldStrength`

The difference between `PhaseEncodingDirection` (signed, e.g. `"j-"`) and `PhaseEncodingAxis` (unsigned, e.g. `"j"`) is critical:
- QSIPrep requires the **signed** form
- Some scanner/conversion combinations (e.g. Siemens Skyra with some dcm2niix versions) produce only the unsigned axis
- Vecta's VECTA-DWI-021 criterion detects this gap

### 3.3 What is susceptibility distortion correction (SDC)?

EPI sequences (used in DWI) suffer from geometric distortion along the phase-encoding direction because of magnetic field inhomogeneities. SDC corrects this by acquiring a second volume with the phase-encoding direction reversed (reverse-PE). The pair of AP/PA images lets TOPUP estimate the field map and warp the image back to the correct shape.

This is why a missing reverse-PE acquisition (VECTA-DWI-014) is a limitation rather than a blocker: QSIPrep can still run without SDC, just with less geometric accuracy.

### 3.4 BIDS filename entities

BIDS filenames encode metadata as key-value pairs separated by underscores:

```
sub-001_ses-1_acq-64dirax_dir-ap_dwi.nii.gz
 ↑sub  ↑ses    ↑acq         ↑dir   ↑suffix
```

- `sub`: subject ID
- `ses`: session ID
- `acq`: acquisition label (arbitrary, often encodes protocol details)
- `dir`: phase-encoding direction label (`ap`, `pa`, `lr`, `rl`)
- `run`: run number if multiple runs exist

**Key insight**: filename labels like `dir-ap` and `dir-pa` are *intended* to indicate complementary phase-encoding directions, but they are not validated — a session could have `dir-AP` and `dir-PA` files that both have `j-` in their sidecar (same actual direction). Vecta reads the sidecar values, not the filename labels.

---

## 4. Python Project Setup

### 4.1 pyproject.toml — modern Python packaging

Before `pyproject.toml` became standard, Python packages used `setup.py` or `setup.cfg`. The modern approach uses `pyproject.toml` with PEP 517/518 build backends.

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "vecta-dwi"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "jsonschema>=4.18",
    "pydicom>=2.4",
    "nibabel>=5.0",
    "pandas>=2.0",
    "scipy>=1.11",
    "numpy>=1.24",
    "jinja2>=3.1",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov"]

[project.scripts]
vecta = "vecta.cli:main"
```

**What `[project.scripts]` does**: it installs a command-line entry point. After `pip install`, typing `vecta` in the terminal calls `vecta.cli:main`. The format is `command = "module:function"`.

**What `[project.optional-dependencies]` does**: `pip install -e ".[dev]"` installs the package plus the dev dependencies (pytest). The `[dev]` part is the extras group name.

### 4.2 The src layout

```
vecta-dwi/
  src/
    vecta/          ← the actual package
  tests/            ← tests (not inside the package)
  pyproject.toml
```

**Why src layout?** Without it, `import vecta` in tests would find the local `vecta/` directory even if the package isn't installed, hiding missing `__init__.py` or import errors. With `src/`, Python's import system doesn't see the package unless it's installed (even in editable mode with `pip install -e .`), forcing you to install before running tests.

### 4.3 Package structure

```
src/vecta/
  __init__.py
  enums.py          ← Python enums (mirrors of YAML registry)
  models.py         ← Pydantic data models
  cli.py            ← argparse CLI
  spec/
    loader.py       ← loads YAML spec, validates against JSON Schema
  collectors/
    bids.py         ← walks BIDS directory tree
    dicom.py        ← reads DICOM headers
  extract/
    acquisition.py  ← bval/bvec parsing, gradient analysis
    bids.py         ← BIDS validator result parsing
    pe.py           ← phase-encoding direction extraction
    scanner.py      ← scanner metadata extraction
    dicom_source.py ← DICOM-layer variable extraction
  derive/
    reverse_pe.py   ← determines if reverse-PE reference exists
  criteria/
    engine.py       ← evaluates criteria against variable results
  output/
    assemble.py     ← builds vecta.json output
    tsv.py          ← projects key fields to TSV
    cohort.py       ← aggregates per-session outputs
    html.py         ← Jinja2 HTML report renderer
  research/
    outcomes.py     ← QSIPrep outcome labeling and joining
```

**Design principle**: each module has one responsibility. The `collectors/` module finds files; the `extract/` module reads values from those files; the `criteria/` module evaluates logic; the `output/` module serializes results. These layers are independent — you can test the criteria engine without a real BIDS dataset.

---

## 5. Specification Design

### 5.1 The three-layer hierarchy

The specification has three layers, all written in YAML:

```
Variables → Criteria → Profiles
```

- **Variables**: what to measure (22 variables across 5 domains)
- **Criteria**: what conditions to check (8 criteria, each referencing variables)
- **Profiles**: which criteria are active for a given intended use (one profile per downstream workflow)

### 5.2 A variable definition

```yaml
# specification/v0.1/variables/acquisition.yaml

- id: phase_encoding_direction
  name: PhaseEncodingDirection
  domain: acquisition
  source: bids_sidecar
  field: PhaseEncodingDirection
  value_type: string
  allowed_values: ["i", "i-", "j", "j-", "k", "k-"]
  required: false
  description: >
    Signed phase-encoding direction from the DWI sidecar JSON.
    Must be a signed form (e.g. "j-") not just an axis (e.g. "j").
  evidence_ids: [EV-DWI-021]
```

**What this defines**: a named measurement that the extraction layer should attempt to read from the BIDS sidecar. It includes the source (`bids_sidecar`), the exact field name (`PhaseEncodingDirection`), the allowed values, and a link to an evidence entry.

### 5.3 A criterion definition

```yaml
# specification/v0.1/criteria/dwi_connectomics.yaml

- id: VECTA-DWI-021
  name: PhaseEncodingDirection absent or unsigned
  version: "0.1.0"
  severity: critical
  severity_status: calibrated
  category: metadata_integrity
  lifecycle_layer: bids_sidecar
  designation: review
  variables:
    required: [phase_encoding_direction, total_readout_time]
  condition:
    any_of:
      - variable: phase_encoding_direction
        state: [unknown, not_collected]
      - variable: total_readout_time
        state: [unknown, not_collected]
  finding:
    title: "PhaseEncodingDirection absent or unsigned"
    description: >
      QSIPrep requires a signed PhaseEncodingDirection to extract
      acquisition parameters. If absent or unsigned (PhaseEncodingAxis
      only), QSIPrep crashes at get_acq_parameters_df() before the SDC
      workflow begins.
    severity: critical
    potential_effects:
      - QSIPrep crashes immediately at DWI parameter extraction
      - OR QSIPrep silently excludes the DWI session from the workflow
    remediation:
      - Re-run dcm2niix with a version that exports signed direction
      - Manually add PhaseEncodingDirection to the sidecar JSON
  evidence_ids: [EV-DWI-021]
```

**Key design decision**: the `condition` block uses a declarative logic (`any_of`, `all_of`, `none_of`) rather than Python code. This means the criterion is independently readable — a reviewer who doesn't know Python can understand what triggers it.

**`designation: review`** means this criterion puts the session into `review_required` rather than `not_ready` or `ready_with_limitations`. The three designation types are:
- `blocking` → `not_ready`
- `review` → `review_required`
- (neither) → `ready_with_limitations`

### 5.4 A profile definition

```yaml
# specification/v0.1/profiles/dwi_connectomics.yaml

id: dwi_connectomics
name: DWI Connectomics
version: "0.1.0"
description: >
  Profile for DWI-based structural connectivity analysis via QSIPrep
  and QSIRecon tractography.

criteria:
  - VECTA-DWI-001
  - VECTA-DWI-014
  - VECTA-DWI-021
  - VECTA-DWI-030
  - VECTA-DWI-031
  - VECTA-DWI-040
  - VECTA-DWI-050
  - VECTA-DWI-060

blocking_criteria:
  - VECTA-DWI-040
  - VECTA-DWI-030

review_criteria:
  - VECTA-DWI-001
```

**The critical design bug we found**: the criteria engine only iterates `spec.profile["criteria"]`. If a criterion exists in the YAML spec but is NOT listed in the profile's `criteria` list, it is **never evaluated**. VECTA-DWI-031 was missing from this list, causing it to silently never fire despite being correctly defined. The fix was to add `VECTA-DWI-031` to the profile `criteria` list.

### 5.5 Why YAML over Python?

The scientific meaning lives in YAML, not in code. This has important consequences:

1. **Independent reviewability**: a domain expert can review what Vecta checks without reading Python
2. **Version-pinning**: the spec version is recorded in every output; a criterion can be updated independently of the code
3. **Separation of concerns**: changing what Vecta checks (YAML) is separate from how it checks it (Python)

---

## 6. JSON Schema

### 6.1 What JSON Schema is

JSON Schema is a specification for describing the structure of JSON (or YAML) documents. It lets you validate that a document matches an expected shape before using it.

We used **JSON Schema Draft 2020-12** (the most recent stable version). Key features used:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://vecta-dwi/schemas/v0.1/variable.schema.json",
  "type": "object",
  "required": ["id", "name", "domain", "source", "value_type"],
  "properties": {
    "id": { "type": "string", "pattern": "^[a-z_]+$" },
    "domain": { "$ref": "_defs.schema.json#/$defs/Domain" },
    "value_type": {
      "type": "string",
      "enum": ["string", "number", "boolean", "integer"]
    }
  },
  "additionalProperties": false
}
```

**`additionalProperties: false`**: any key in the YAML not listed in `properties` causes a validation error. This is strict mode — it prevents typos from silently passing.

**`$ref`**: references another schema or a `$defs` section. This avoids duplicating shared type definitions.

### 6.2 The `_defs.schema.json` shared definitions file

```json
{
  "$defs": {
    "Domain": {
      "type": "string",
      "enum": ["acquisition", "bids", "scanner", "dicom_source", "derived"]
    },
    "ValueState": {
      "type": "string",
      "enum": ["observed", "derived", "unknown", "not_collected", 
               "not_applicable", "invalid", "extraction_failed", "conflict"]
    }
  }
}
```

This file defines shared types that multiple schemas reference with `$ref`. It's a DRY (Don't Repeat Yourself) pattern applied to schema authoring.

### 6.3 Input vs output schemas

We authored two sets of schemas:
- **Input schemas** (`schemas/input/`): validate the YAML spec files (variable definitions, criterion definitions, profile definitions)
- **Output schemas** (`schemas/output/`): validate the `vecta.json` output format

Having both means the spec author (who writes YAML) and the output consumer (who reads `vecta.json`) both have a contract. If either side violates the contract, validation fails immediately.

### 6.4 How jsonschema is used in Python

```python
import json
import jsonschema

with open("specification/v0.1/schemas/input/variable.schema.json") as f:
    schema = json.load(f)

with open("specification/v0.1/variables/acquisition.yaml") as f:
    data = yaml.safe_load(f)  # YAML loads as dict

for variable_def in data:
    jsonschema.validate(variable_def, schema)  # raises ValidationError if invalid
```

**The `jsonschema` library** implements the JSON Schema specification. `validate()` raises `jsonschema.ValidationError` with a human-readable message if the document fails to match the schema.

---

## 7. Enums

### 7.1 Why Python enums mirror the YAML registry

The specification defines allowed values in `specification/v0.1/registries/enums.yaml`. Python code needs these values for type checking and exhaustive matching. Rather than loading the YAML at import time (slow, fragile), we maintained a Python enum file that mirrors the YAML.

```python
# src/vecta/enums.py
from enum import Enum

class ValueState(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    UNKNOWN = "unknown"
    NOT_COLLECTED = "not_collected"
    NOT_APPLICABLE = "not_applicable"
    INVALID = "invalid"
    EXTRACTION_FAILED = "extraction_failed"
    CONFLICT = "conflict"

class ReadinessState(str, Enum):
    READY = "ready"
    READY_WITH_LIMITATIONS = "ready_with_limitations"
    REVIEW_REQUIRED = "review_required"
    NOT_READY = "not_ready"
    NOT_ASSESSED = "not_assessed"
```

**`str, Enum`**: inheriting from both `str` and `Enum` means enum members serialize directly to their string value (`json.dumps(ValueState.OBSERVED)` gives `"observed"`). Without `str`, JSON serialization would fail.

### 7.2 Exhaustive matching with enums

```python
def readiness_from_criteria(triggered: list, blocking: set, review: set) -> ReadinessState:
    for cid in triggered:
        if cid in blocking:
            return ReadinessState.NOT_READY
    for cid in triggered:
        if cid in review:
            return ReadinessState.REVIEW_REQUIRED
    if triggered:
        return ReadinessState.READY_WITH_LIMITATIONS
    return ReadinessState.READY
```

Using the enum rather than raw strings means a typo like `ReadinessState.RAEDY` raises `AttributeError` at import time — caught immediately, not at runtime.

---

## 8. Pydantic v2

### 8.1 What Pydantic is

Pydantic is a Python library for data validation using type annotations. You declare a data class, and Pydantic automatically validates and coerces input data.

**Pydantic v2** (released 2023) is a major rewrite from v1 — faster, stricter, different API. The key differences:

| v1 | v2 |
|----|----|
| `from pydantic import BaseModel` | same |
| `@validator` decorator | `@field_validator` or `@model_validator` |
| `class Config: arbitrary_types_allowed = True` | `model_config = ConfigDict(arbitrary_types_allowed=True)` |
| `.dict()` method | `.model_dump()` method |
| `.json()` method | `.model_dump_json()` method |

### 8.2 A model definition

```python
# src/vecta/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from .enums import ValueState, CriterionStatus, ReadinessState

class VariableResult(BaseModel):
    variable_id: str
    value: Optional[Any] = None
    state: ValueState
    source: Optional[str] = None
    confidence: Optional[str] = None
    notes: Optional[str] = None

class CriterionResult(BaseModel):
    criterion_id: str
    status: CriterionStatus
    triggered: bool
    evidence: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class VectaOutput(BaseModel):
    schema_version: str
    spec_version: str
    subject: str
    session: str
    profile: str
    assessment_state: str
    readiness: ReadinessState
    variables: List[VariableResult]
    criteria: List[CriterionResult]
    findings: List[dict] = Field(default_factory=list)
```

**`Field(default_factory=list)`**: mutable defaults (like lists) cannot be plain default values in Python classes because they're shared across instances. `default_factory=list` creates a new empty list for each instance.

**`Optional[Any]`**: `Optional[X]` is equivalent to `Union[X, None]` — the field can be `None`. `Any` means any type is accepted for the `value` field (because variables can hold strings, numbers, booleans, etc.).

### 8.3 Serialization

```python
output = VectaOutput(...)
# Write to JSON file
with open("vecta.json", "w") as f:
    f.write(output.model_dump_json(indent=2))

# Convert to dict (for further manipulation)
d = output.model_dump()
```

Pydantic's `model_dump_json()` handles enum serialization automatically (enums serialize to their `.value`).

---

## 9. Spec Loader

### 9.1 The loader's job

The spec loader reads the YAML files, validates each document against its JSON Schema, and returns a structured object that the rest of the system can use.

```python
# src/vecta/spec/loader.py
import yaml
import json
import jsonschema
from pathlib import Path

class VectaSpec:
    def __init__(self, spec_dir: Path, profile_name: str):
        self.spec_dir = spec_dir
        self.profile_name = profile_name
        self._load_schemas()
        self.variables = self._load_variables()
        self.criteria = self._load_criteria()
        self.profile = self._load_profile()

    def _load_schemas(self):
        schema_dir = self.spec_dir / "schemas"
        self._var_schema = self._read_schema(schema_dir / "input/variable.schema.json")
        self._crit_schema = self._read_schema(schema_dir / "input/criterion.schema.json")
        self._profile_schema = self._read_schema(schema_dir / "input/profile.schema.json")

    def _load_variables(self) -> dict:
        var_dir = self.spec_dir / "variables"
        variables = {}
        for yaml_file in var_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                defs = yaml.safe_load(f)
            for v in defs:
                jsonschema.validate(v, self._var_schema)
                variables[v["id"]] = v
        return variables
```

**`Path.glob("*.yaml")`**: returns all `.yaml` files in a directory. `Path` objects (from `pathlib`) are preferred over string paths — they support `/` for joining, `.stem` for the filename without extension, etc.

**Why validate on load**: catching a malformed spec file immediately at startup (rather than later when a criterion tries to use it) gives a clear error message pointing to the YAML file.

### 9.2 Profile loading and the criteria filter

```python
def _load_profile(self) -> dict:
    profile_file = self.spec_dir / "profiles" / f"{self.profile_name}.yaml"
    with open(profile_file) as f:
        profile = yaml.safe_load(f)
    jsonschema.validate(profile, self._profile_schema)
    return profile
```

The `profile["criteria"]` list is the **filter** — only criteria in this list are evaluated. This is the source of the VECTA-DWI-031 bug: the criterion was defined in the YAML but not listed in the profile.

---

## 10. BIDS Collector

### 10.1 Walking the directory tree

```python
# src/vecta/collectors/bids.py
from pathlib import Path
from typing import Optional
import json

class BIDSCollector:
    def __init__(self, bids_root: Path, subject: str, session: Optional[str] = None):
        self.bids_root = Path(bids_root)
        self.subject = subject
        self.session = session
        self._session_dir = self._resolve_session_dir()

    def _resolve_session_dir(self) -> Path:
        if self.session:
            return self.bids_root / f"sub-{self.subject}" / f"ses-{self.session}"
        return self.bids_root / f"sub-{self.subject}"

    def collect_dwi_sidecars(self) -> list[dict]:
        dwi_dir = self._session_dir / "dwi"
        if not dwi_dir.exists():
            return []
        sidecars = []
        for json_file in sorted(dwi_dir.glob("*_dwi.json")):
            with open(json_file) as f:
                sidecar = json.load(f)
            sidecar["_filename"] = json_file.name
            sidecars.append(sidecar)
        return sidecars

    def collect_fmap_sidecars(self) -> list[dict]:
        fmap_dir = self._session_dir / "fmap"
        if not fmap_dir.exists():
            return []
        ...
```

**`sorted()`**: filesystem order is not guaranteed to be consistent across operating systems. Sorting ensures deterministic behavior (property 3 of DBI).

**Adding `_filename`**: the sidecar is a plain dict; by adding `_filename` to the dict, downstream code knows which file it came from without needing to pass the filename separately.

---

## 11. PE Extractor

### 11.1 The signed vs unsigned problem

```python
# src/vecta/extract/pe.py
from ..enums import ValueState

SIGNED_DIRECTIONS = {"i", "i-", "j", "j-", "k", "k-"}
UNSIGNED_AXES = {"i", "j", "k"}  # no minus sign

def extract_phase_encoding_direction(sidecar: dict) -> tuple[ValueState, str | None]:
    ped = sidecar.get("PhaseEncodingDirection")
    pea = sidecar.get("PhaseEncodingAxis")

    if ped is not None:
        if ped in SIGNED_DIRECTIONS:
            return ValueState.OBSERVED, ped
        else:
            return ValueState.INVALID, ped

    if pea is not None:
        # PhaseEncodingAxis is unsigned — not sufficient for SDC
        return ValueState.UNKNOWN, None   # ← VECTA-DWI-021 will fire

    return ValueState.NOT_COLLECTED, None
```

**The distinction**: `PhaseEncodingDirection: "j-"` means posterior-to-anterior (signed). `PhaseEncodingAxis: "j"` means the j-axis (unsigned — could be either direction). QSIPrep needs the signed form to determine which way to warp the image for distortion correction. When only the axis is present, the direction is genuinely unknown.

**`ValueState.UNKNOWN` vs `ValueState.NOT_COLLECTED`**: `UNKNOWN` means we found evidence but can't determine the value (e.g. we found `PhaseEncodingAxis` but not `PhaseEncodingDirection`). `NOT_COLLECTED` means the field wasn't attempted or wasn't in the sidecar at all.

---

## 12. Acquisition Extractor

### 12.1 Parsing bval files

A `.bval` file is a space- or newline-separated list of b-values, one per volume:

```
0 0 0 1000 1000 1000 1000 ...
```

```python
def _parse_bval(bval_path: Path) -> list[float]:
    with open(bval_path) as f:
        content = f.read()
    # b-values can be space or newline separated, possibly across multiple lines
    return [float(x) for x in content.split()]
```

### 12.2 Parsing bvec files (FSL format)

A `.bvec` file has **3 rows** and N columns, where N is the number of volumes:

```
0.0  0.707  0.0   ...    ← x-components of each gradient direction
0.0  0.0    0.707 ...    ← y-components
1.0  0.707  0.707 ...    ← z-components
```

```python
def _parse_bvec(bvec_path: Path) -> list[list[float]]:
    """Returns list of N [x, y, z] vectors (one per volume)."""
    with open(bvec_path) as f:
        lines = f.readlines()
    rows = [[float(v) for v in line.split()] for line in lines if line.strip()]
    if len(rows) != 3:
        raise ValueError(f"Expected 3 rows in bvec, got {len(rows)}")
    n_vols = len(rows[0])
    # Transpose: rows[0][i] = x component of volume i
    return [[rows[0][i], rows[1][i], rows[2][i]] for i in range(n_vols)]
```

### 12.3 Gradient vector norm plausibility check (VECTA-DWI-031)

For non-b0 volumes, the gradient vector should be a unit vector (norm = 1.0). Non-unit norms indicate the bvec was corrupted or vendor-rescaled.

```python
DEFAULT_VECTOR_NORM_TOL = 0.05  # |norm - 1.0| > 0.05 is implausible
B0_THRESHOLD = 50.0             # b-values below this are treated as b=0

def derive_bvec_plausibility(bvals: list[float], bvecs: list[list[float]]) -> dict:
    import numpy as np

    implausible = []
    for i, (bval, vec) in enumerate(zip(bvals, bvecs)):
        if bval <= B0_THRESHOLD:
            continue  # b=0 volumes have zero gradient; norm is undefined
        norm = np.linalg.norm(vec)
        if abs(norm - 1.0) > DEFAULT_VECTOR_NORM_TOL:
            implausible.append({"volume": i, "bval": bval, "norm": round(norm, 4)})

    return {
        "plausible": len(implausible) == 0,
        "implausible_count": len(implausible),
        "implausible_volumes": implausible
    }
```

**`numpy.linalg.norm(vec)`**: computes the Euclidean norm `sqrt(x² + y² + z²)` of a vector. For a unit vector, this should equal 1.0.

**Why not just check `norm == 1.0`?**: floating-point arithmetic means `0.707² + 0.707² + 0.0²` may not equal exactly 1.0. The tolerance `0.05` allows for rounding while still catching genuine corruption.

---

## 13. Reverse-PE Deriver

### 13.1 The problem

A session has a reverse-PE reference if:
1. There's another DWI file with the opposite phase-encoding direction (e.g. one has `j-`, the other has `j`), OR
2. There's an EPI fieldmap in `fmap/` whose `IntendedFor` field references the DWI file

The first check is simple. The second requires reading the fmap sidecar and checking its `IntendedFor` list.

### 13.2 The IntendedFor check

```python
# src/vecta/derive/reverse_pe.py

def has_reverse_pe_reference(
    dwi_sidecars: list[dict],
    fmap_sidecars: list[dict],
    subject: str,
    session: str
) -> tuple[bool, str]:
    """
    Returns (has_reference, source_description).
    source_description is for evidence attribution.
    """
    # Check 1: complementary DWI entities
    ped_values = set()
    for s in dwi_sidecars:
        ped = s.get("PhaseEncodingDirection")
        if ped:
            ped_values.add(ped)

    complements = {("j", "j-"), ("j-", "j"), ("i", "i-"), ("i-", "i"),
                   ("k", "k-"), ("k-", "k")}
    for a, b in complements:
        if a in ped_values and b in ped_values:
            return True, "complementary_dwi_entities"

    # Check 2: EPI fieldmap with IntendedFor referencing this DWI
    for fmap in fmap_sidecars:
        # EPI fieldmaps have PhaseEncodingDirection — phasediff/magnitude do not
        if "PhaseEncodingDirection" not in fmap:
            continue
        fmap_ped = fmap.get("PhaseEncodingDirection", "")
        intended_for = fmap.get("IntendedFor", [])
        if isinstance(intended_for, str):
            intended_for = [intended_for]

        # IntendedFor uses paths like "ses-1/dwi/sub-001_ses-1_dwi.nii.gz"
        dwi_prefix = f"ses-{session}/dwi/" if session else "dwi/"
        for ref in intended_for:
            if dwi_prefix in ref:
                # Check the fmap PE direction is the opposite of the DWI
                for dwi_s in dwi_sidecars:
                    dwi_ped = dwi_s.get("PhaseEncodingDirection", "")
                    if (dwi_ped, fmap_ped) in complements:
                        return True, f"epi_fmap_intendedfor:{fmap['_filename']}"

    return False, "no_reverse_pe_found"
```

**The IntendedFor evolution**: BIDS v1.x used relative paths in `IntendedFor` like `"ses-1/dwi/sub-001_ses-1_dwi.nii.gz"`. BIDS v2.0 uses BIDS URIs like `"bids::sub-001/ses-1/dwi/sub-001_ses-1_dwi.nii.gz"`. The extractor needed to handle both formats.

**Why phasediff/magnitude fieldmaps don't count**: a GRE phasediff/magnitude fieldmap provides phase information for SDC but QSIPrep's PEPOLAR method (TOPUP) requires a reverse-phase-encoding EPI acquisition. Phasediff fieldmaps trigger VECTA-DWI-014 because they can't serve as the complementary-PE reference for TOPUP-based SDC.

---

## 14. DICOM Collector

### 14.1 pydicom

```python
# src/vecta/collectors/dicom.py
import pydicom
from pathlib import Path

def collect_dicom_series(dicom_dir: Path) -> list[pydicom.Dataset]:
    """Read all DICOM files in a directory, return list of datasets."""
    datasets = []
    for dcm_file in sorted(dicom_dir.rglob("*.dcm")):
        try:
            ds = pydicom.dcmread(str(dcm_file), stop_before_pixels=True)
            datasets.append(ds)
        except pydicom.errors.InvalidDicomError:
            continue
    return datasets
```

**`stop_before_pixels=True`**: DICOM files store both metadata (header) and pixel data. For metadata-only checks, skipping the pixel data is much faster (pixel data can be hundreds of MB; headers are kilobytes).

**`rglob("*.dcm")`**: recursively finds all `.dcm` files. DICOM directories often have subdirectories per series.

### 14.2 DICOM tag access

```python
def extract_field_strength(ds: pydicom.Dataset) -> float | None:
    # DICOM tag (0018,0087) = MagneticFieldStrength
    tag = (0x0018, 0x0087)
    if tag in ds:
        return float(ds[tag].value)
    return None

def extract_sop_instance_uid(ds: pydicom.Dataset) -> str | None:
    # (0008,0018) = SOPInstanceUID — unique per DICOM image instance
    return getattr(ds, "SOPInstanceUID", None)
```

**DICOM tags**: every field in a DICOM file has a 4-byte tag `(group, element)`. `pydicom` lets you access them by tag tuple or by attribute name (`ds.MagneticFieldStrength`). The attribute name approach is more readable but can fail for private tags; the tag tuple approach always works.

### 14.3 DICOM source integrity checks

**VECTA-DWI-050** (geometry consistency): checks that all instances in a DWI series have consistent ImageOrientationPatient and ImagePositionPatient — catching cases where accidentally mixed scout images inflate the DICOM series.

**VECTA-DWI-060** (field-strength agreement): compares the `MagneticFieldStrength` in the DICOM header with the `MagneticFieldStrength` in the BIDS sidecar JSON. A mismatch suggests either a DICOM/BIDS mismatch (wrong DICOM used for conversion) or a header error.

---

## 15. Criteria Engine

### 15.1 How it works

The criteria engine takes a dict of variable results and evaluates each criterion's condition.

```python
# src/vecta/criteria/engine.py
from ..enums import ValueState, CriterionStatus

def evaluate_criterion(criterion: dict, var_results: dict[str, dict]) -> dict:
    """
    criterion: the criterion definition dict (from YAML)
    var_results: {variable_id: {"state": ValueState, "value": ...}}
    Returns: {"status": CriterionStatus, "triggered": bool, "evidence": [...]}
    """
    condition = criterion.get("condition", {})
    triggered, evidence = _evaluate_condition(condition, var_results)

    if triggered:
        status = CriterionStatus.FINDING
    else:
        # Check if any required variables were unknown
        required_vars = criterion.get("variables", {}).get("required", [])
        unknowns = [v for v in required_vars
                    if var_results.get(v, {}).get("state") in
                    (ValueState.UNKNOWN, ValueState.NOT_COLLECTED)]
        if unknowns:
            status = CriterionStatus.UNKNOWN
        else:
            status = CriterionStatus.SATISFIED

    return {
        "criterion_id": criterion["id"],
        "status": status,
        "triggered": triggered,
        "evidence": evidence
    }

def _evaluate_condition(condition: dict, var_results: dict) -> tuple[bool, list]:
    if "any_of" in condition:
        for sub in condition["any_of"]:
            result, ev = _evaluate_sub_condition(sub, var_results)
            if result:
                return True, ev
        return False, []
    if "all_of" in condition:
        evidence = []
        for sub in condition["all_of"]:
            result, ev = _evaluate_sub_condition(sub, var_results)
            if not result:
                return False, []
            evidence.extend(ev)
        return True, evidence
    ...

def _evaluate_sub_condition(sub: dict, var_results: dict) -> tuple[bool, list]:
    var_id = sub["variable"]
    required_states = sub.get("state", [])
    required_value = sub.get("value")

    result = var_results.get(var_id)
    if result is None:
        return False, []

    state = result["state"]
    value = result["value"]

    if required_states and state in required_states:
        return True, [f"{var_id}:{state}"]
    if required_value is not None and value == required_value:
        return True, [f"{var_id}={value}"]
    return False, []
```

### 15.2 The profile filter (the bug source)

```python
# src/vecta/output/assemble.py (simplified)

def assemble(spec, var_results):
    criterion_results = []
    
    # Only evaluate criteria listed in the profile
    for cid in spec.profile.get("criteria", []):   # ← THE CRITICAL LINE
        criterion_def = spec.criteria.get(cid)
        if criterion_def is None:
            raise ValueError(f"Criterion {cid} in profile but not in spec")
        result = evaluate_criterion(criterion_def, var_results)
        criterion_results.append(result)
    
    return criterion_results
```

**The bug**: VECTA-DWI-031 was defined in `spec.criteria` (loaded from the YAML file) but was NOT in `spec.profile["criteria"]` (the dwi_connectomics profile list). The `for cid in spec.profile.get("criteria", [])` loop never iterated over `VECTA-DWI-031`, so it was never evaluated.

**The fix**: add `VECTA-DWI-031` to the `criteria` list in `dwi_connectomics.yaml`.

**Lesson**: always write tests for each criterion that confirm it fires with an injected defect. If VECTA-DWI-031 had a test, the test would have caught that the criterion never triggered even when the bvec norms were wrong.

---

## 16. Output Assembler

### 16.1 Building the readiness verdict

```python
def _compute_readiness(
    criterion_results: list,
    blocking_criteria: set,
    review_criteria: set
) -> ReadinessState:
    triggered_ids = [r["criterion_id"] for r in criterion_results if r["triggered"]]

    for cid in triggered_ids:
        if cid in blocking_criteria:
            return ReadinessState.NOT_READY

    for cid in triggered_ids:
        if cid in review_criteria:
            return ReadinessState.REVIEW_REQUIRED

    if triggered_ids:
        return ReadinessState.READY_WITH_LIMITATIONS

    return ReadinessState.READY
```

Priority order: `NOT_READY` > `REVIEW_REQUIRED` > `READY_WITH_LIMITATIONS` > `READY`. A single blocking criterion overrides everything.

### 16.2 Output validation

After building the output dict, it's validated against the output JSON Schema before writing:

```python
import jsonschema

def write_output(output_dict: dict, output_dir: Path, schema: dict):
    # Validate against output schema — catches bugs in the assembler
    jsonschema.validate(output_dict, schema)
    
    with open(output_dir / "vecta.json", "w") as f:
        json.dump(output_dict, f, indent=2)
```

**Why validate output**: the output schema is a contract with downstream consumers. Validating before writing ensures the file is always well-formed. If the assembler has a bug (e.g., missing a required field), it fails immediately rather than writing a corrupted file that breaks downstream tools.

---

## 17. TSV Projector and Cohort Aggregator

### 17.1 TSV projection (per-session)

```python
# src/vecta/output/tsv.py
import csv

KEY_FIELDS = [
    "subject", "session", "readiness", "assessment_state",
    "n_findings", "finding_ids",
    "phase_encoding_direction", "total_readout_time",
    "has_reverse_pe", "bvec_plausible"
]

def project_to_tsv(vecta_json: dict, output_path: Path):
    row = {
        "subject": vecta_json["subject"],
        "session": vecta_json["session"],
        "readiness": vecta_json["readiness"],
        ...
    }
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=KEY_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerow(row)
```

### 17.2 Cohort aggregation

The cohort aggregator reads all per-session `vecta.json` files and combines them:

```python
# src/vecta/output/cohort.py
import pandas as pd
from pathlib import Path
import json

def aggregate_cohort(per_session_dir: Path, output_dir: Path):
    rows = []
    for session_dir in sorted(per_session_dir.iterdir()):
        vecta_file = session_dir / "vecta.json"
        if not vecta_file.exists():
            continue
        with open(vecta_file) as f:
            data = json.load(f)
        rows.append(_flatten_session(data))

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "session_summary.tsv", sep="\t", index=False)
    
    # Findings long format: one row per finding
    findings = []
    for row in rows:
        for finding in row.get("_findings_raw", []):
            findings.append({
                "subject": row["subject"],
                "session": row["session"],
                **finding
            })
    pd.DataFrame(findings).to_csv(output_dir / "findings_long.tsv", sep="\t", index=False)
```

**pandas**: the core data manipulation library in Python. Key operations used:
- `pd.DataFrame(list_of_dicts)`: creates a DataFrame from a list of row dicts
- `df.to_csv(path, sep="\t", index=False)`: writes to TSV without the row index
- `df.groupby("readiness").size()`: count sessions per readiness state
- `df.merge(other_df, on="subject", how="left")`: join two DataFrames on a column

---

## 18. HTML Report Renderer

### 18.1 Jinja2 templates

Jinja2 is a Python template engine. A template is an HTML file with special `{{ variable }}` and `{% for %}` syntax:

```html
<!-- templates/session_report.html -->
<!DOCTYPE html>
<html>
<head><title>Vecta Report: {{ subject }} {{ session }}</title></head>
<body>
  <h1>Readiness: <span class="readiness-{{ readiness }}">{{ readiness }}</span></h1>

  {% if findings %}
  <h2>Findings ({{ findings | length }})</h2>
  <ul>
  {% for finding in findings %}
    <li>
      <strong>{{ finding.criterion_id }}</strong>: {{ finding.title }}
      <br>Severity: {{ finding.severity }}
    </li>
  {% endfor %}
  </ul>
  {% else %}
  <p>No criteria triggered.</p>
  {% endif %}
</body>
</html>
```

```python
# src/vecta/output/html.py
from jinja2 import Environment, FileSystemLoader

def render_report(vecta_json: dict, template_dir: Path, output_path: Path):
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("session_report.html")
    html = template.render(**vecta_json)
    with open(output_path, "w") as f:
        f.write(html)
```

**`**vecta_json`**: unpacks the dict as keyword arguments to `render()`. Each key becomes a template variable.

---

## 19. CLI Design

### 19.1 argparse subcommands

```python
# src/vecta/cli.py
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog="vecta",
        description="Data Birth Integrity assessment for DWI datasets"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # vecta assess
    assess_p = subparsers.add_parser("assess", help="Assess a single session")
    assess_p.add_argument("--dataset", required=True, type=Path)
    assess_p.add_argument("--subject", required=True)
    assess_p.add_argument("--session")
    assess_p.add_argument("--spec", required=True, type=Path)
    assess_p.add_argument("--profile", required=True)
    assess_p.add_argument("--dicom", type=Path, help="DICOM directory (optional)")
    assess_p.add_argument("--output", required=True, type=Path)

    # vecta aggregate
    agg_p = subparsers.add_parser("aggregate", help="Aggregate per-session outputs")
    agg_p.add_argument("input_dir", type=Path)
    agg_p.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()

    if args.command == "assess":
        run_assess(args)
    elif args.command == "aggregate":
        run_aggregate(args)
```

**`subparsers`**: allows `vecta assess ...` and `vecta aggregate ...` as separate commands with their own arguments. The `dest="command"` stores which subcommand was used; `required=True` means not providing a subcommand is an error.

**`type=Path`**: automatically converts the string argument to a `Path` object. Much cleaner than calling `Path(args.dataset)` everywhere.

### 19.2 Entry point wiring

In `pyproject.toml`:
```toml
[project.scripts]
vecta = "vecta.cli:main"
```

When you run `pip install .`, pip creates a wrapper script `vecta` that calls `vecta.cli.main()`. This is how `vecta assess ...` works as a command.

---

## 20. Testing

### 20.1 pytest and fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def bids_root(tmp_path) -> Path:
    """Build a minimal BIDS tree in a temporary directory."""
    sub_dir = tmp_path / "sub-001" / "ses-1" / "dwi"
    sub_dir.mkdir(parents=True)

    # Create a minimal sidecar with all required fields
    sidecar = {
        "PhaseEncodingDirection": "j-",
        "TotalReadoutTime": 0.0384197,
        "Manufacturer": "Siemens",
        "MagneticFieldStrength": 3.0
    }
    with open(sub_dir / "sub-001_ses-1_acq-64dirax_dir-ap_dwi.json", "w") as f:
        json.dump(sidecar, f)

    # Create minimal bval/bvec
    ...
    return tmp_path

@pytest.fixture
def spec(tmp_path_factory) -> VectaSpec:
    return VectaSpec(
        spec_dir=Path("specification/v0.1"),
        profile_name="dwi_connectomics"
    )
```

**`tmp_path`**: a pytest built-in fixture that provides a temporary directory unique to each test. It's automatically cleaned up after the test.

**`@pytest.fixture`**: marks a function as a reusable test component. Tests declare fixtures as parameters and pytest injects them.

### 20.2 Parametrize for multiple test cases

```python
@pytest.mark.parametrize("sidecar_field,sidecar_value,expected_state", [
    ("PhaseEncodingDirection", "j-",    ValueState.OBSERVED),
    ("PhaseEncodingDirection", "j",     ValueState.OBSERVED),
    ("PhaseEncodingAxis",      "j",     ValueState.UNKNOWN),    # unsigned only
    (None,                     None,    ValueState.NOT_COLLECTED),
])
def test_pe_extraction(sidecar_field, sidecar_value, expected_state):
    sidecar = {}
    if sidecar_field:
        sidecar[sidecar_field] = sidecar_value
    state, value = extract_phase_encoding_direction(sidecar)
    assert state == expected_state
```

**`@pytest.mark.parametrize`**: runs the same test function with different inputs. Much cleaner than writing four separate test functions.

### 20.3 Golden output regression tests

A "golden output" is a saved expected output. The test runs the code, compares to the saved output, and fails if they differ.

```python
def test_assess_reference_case(bids_root, spec, tmp_path):
    output_dir = tmp_path / "output"
    run_assess_session(bids_root, "001", "1", spec, output_dir)

    with open(output_dir / "vecta.json") as f:
        actual = json.load(f)

    with open("tests/golden/reference_case/vecta.json") as f:
        expected = json.load(f)

    # Strip provenance timestamps (these change each run)
    actual.pop("provenance", None)
    expected.pop("provenance", None)

    assert actual == expected
```

**Why golden tests**: they catch regressions — if a code change accidentally changes the output format or values, the test fails. You update the golden file when you intentionally change the behavior.

### 20.4 Test coverage: 28 tests covering

- Meta-schema validation (JSON Schema validates JSON Schema — the schema for schemas)
- Specification YAML validation against input schemas
- Five synthetic BIDS fixtures (reference case, missing reverse PE, unknown PE direction, missing gradient files, field-strength conflict)
- Seven integration scenarios with golden expected outputs
- Criterion-level tests for each criterion

---

## 21. Research Module

### 21.1 QSIPrep outcome labeling

QSIPrep produces an output directory per subject. To determine if a session was successfully preprocessed, we check for the expected output files:

```python
# src/vecta/research/outcomes.py
from pathlib import Path
import json

def label_session_outcome(
    qsiprep_root: Path,
    subject: str,
    session: str | None,
    pipeline_version: str
) -> dict:
    """
    Checks if QSIPrep produced DWI derivatives for this session.
    Returns a dict with status ("success" | "failure" | "anat_only" | "missing")
    and evidence about what was/wasn't found.
    """
    if session:
        dwi_dir = qsiprep_root / f"sub-{subject}" / f"ses-{session}" / "dwi"
    else:
        dwi_dir = qsiprep_root / f"sub-{subject}" / "dwi"

    preproc_files = list(dwi_dir.glob("*desc-preproc_dwi.nii.gz")) if dwi_dir.exists() else []

    if preproc_files:
        return {"status": "success", "dwi_files": [f.name for f in preproc_files]}

    # Check if anat was produced (QSIPrep anat-only completion)
    anat_dir = qsiprep_root / f"sub-{subject}" / "anat"
    if anat_dir.exists() and list(anat_dir.glob("*desc-preproc_T1w.nii.gz")):
        return {"status": "anat_only", "evidence": "anat derivatives present, no DWI"}

    return {"status": "missing", "evidence": "no output directory found"}
```

**The anat_only detection**: this is how we discovered that def-021 (PhaseEncodingDirection removed) caused a *silent* QSIPrep failure — QSIPrep said "finished successfully!" but only produced anatomical outputs. The outcome labeler checks for `*desc-preproc_dwi.nii.gz` specifically, not just whether QSIPrep exited with code 0.

### 21.2 Joining Vecta findings with outcomes

```python
def join_outcomes(cohort_summary: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """
    Join Vecta readiness states with QSIPrep outcomes on subject+session.
    """
    merged = cohort_summary.merge(
        outcomes[["subject", "session", "status"]],
        on=["subject", "session"],
        how="left"  # keep all Vecta sessions; NaN status if no QSIPrep outcome
    )
    merged["qsiprep_success"] = merged["status"] == "success"
    return merged
```

**`how="left"`**: a left join keeps all rows from the left DataFrame (Vecta cohort) even if there's no matching row in the right DataFrame (outcomes). Sessions without QSIPrep outcomes get `NaN` status.

---

## 22. SLURM and Singularity

### 22.1 What SLURM is

SLURM (Simple Linux Utility for Resource Management) is a job scheduler used on HPC (High-Performance Computing) clusters. Instead of running a program directly, you submit a **job script** that describes the resources needed and the command to run. SLURM queues it and runs it when resources are available.

### 22.2 A SLURM job script

```bash
#!/bin/bash
#SBATCH --job-name=vecta_sub001          # job name
#SBATCH --output=logs/sub001_%j.out      # stdout log (%j = job ID)
#SBATCH --error=logs/sub001_%j.err       # stderr log
#SBATCH --cpus-per-task=8               # request 8 CPU cores
#SBATCH --mem=32G                        # request 32 GB RAM
#SBATCH --time=4:00:00                   # maximum walltime
#SBATCH --partition=interactive          # which queue to submit to

# The actual command
singularity run --cleanenv \
  -B /bids_root:/bids:ro \
  -B /output_dir:/output \
  -B /work_dir:/work \
  -B /freesurfer/license.txt:/opt/freesurfer/license.txt:ro \
  /path/to/qsiprep.sif /bids /output participant \
  --participant-label 001 \
  --output-resolution 2 \
  --hmc-model eddy \
  -w /work \
  --nthreads 8 --omp-nthreads 8 \
  2>&1 | tee logs/sub001_qsiprep.log
```

**`2>&1 | tee`**: `2>&1` redirects stderr to stdout; `tee file` writes to both stdout and a file simultaneously. This captures all output in one log file while also showing it in the SLURM `.out` file.

**Submitting and checking jobs**:
```bash
sbatch run_sub001.slurm          # submit job, returns job ID
squeue -u pndagiji               # check your running jobs
scancel 103555                   # cancel a job by ID
```

### 22.3 What Singularity is

Singularity (now called Apptainer) is a container system designed for HPC. Similar to Docker, it packages a complete software environment. Unlike Docker, it doesn't require root privileges to run — essential on shared cluster systems.

```bash
singularity run --cleanenv \
  -B /host/path:/container/path:ro \
  /path/to/qsiprep.sif \
  [arguments to the container]
```

**`--cleanenv`**: don't pass host environment variables into the container. Prevents conflicts between host and container library versions.

**`-B src:dest:ro`**: bind mount. Makes `/host/path` available inside the container at `/container/path`. `:ro` = read-only (the container can read but not write). This is how you give the container access to your data without copying it.

**`.sif` file**: Singularity Image Format. A single compressed file containing the entire container (OS, Python environment, neuroimaging tools). QSIPrep is distributed as a Docker image; we convert it to `.sif` for use on the cluster.

### 22.4 Generating and submitting jobs programmatically

Instead of hand-writing SLURM scripts for 62 sessions, we wrote a script that generates and submits them:

```bash
# scripts/run_injection_qsiprep.sh

SUBJECTS=("baseline" "def-021" "def-014" "def-030" "def-031")
for defect in "${SUBJECTS[@]}"; do
  # Write SLURM script to a file
  cat > "${LOG_DIR}/${defect}.slurm" << SLURM
#!/bin/bash
#SBATCH --job-name=vecta_${defect}
...
SLURM

  # Submit immediately
  JOB_ID=$(sbatch "${LOG_DIR}/${defect}.slurm" | awk '{print $4}')
  echo "Submitted ${defect}: job ${JOB_ID}"
done
```

**Heredoc (`<< SLURM ... SLURM`)**: writes a multi-line string directly into a file. Everything between the two `SLURM` markers is treated as text. This generates a complete SLURM script file for each defect.

**`awk '{print $4}'`**: `sbatch` outputs "Submitted batch job 103555". `awk '{print $4}'` extracts the 4th word (the job ID).

---

## 23. Controlled Defect Injection

### 23.1 The methodology

To verify that each Vecta criterion fires exactly when its target condition is present, we:
1. Copy a known-good session (sub-001 ses-1 — a Siemens Prisma session, rated `ready`)
2. Apply precisely one defect to each copy
3. Run Vecta on all five copies
4. Verify: (a) each criterion fires exactly for its target defect; (b) no false positives; (c) baseline remains `ready`

This is the neuroimaging equivalent of a **unit test with synthetic data**.

### 23.2 The injection script

```python
# scripts/build_injection_test.py
import json
import shutil
import numpy as np
from pathlib import Path

SOURCE_BIDS = Path("/path/to/CIDUR_BIDS/data_bids")
OUT_BASE = Path("/path/to/cidur_injection_test")

def copy_session(sub, ses, dest_name):
    """Copy a session from the source BIDS into a minimal test dataset."""
    src = SOURCE_BIDS / f"sub-{sub}" / f"ses-{ses}"
    dst = OUT_BASE / dest_name / f"sub-{sub}" / f"ses-{ses}"
    shutil.copytree(src, dst)
    return dst

def inject_021(session_dir: Path):
    """Remove PhaseEncodingDirection from DWI sidecar."""
    for json_file in (session_dir / "dwi").glob("*_dwi.json"):
        with open(json_file) as f:
            sidecar = json.load(f)
        sidecar.pop("PhaseEncodingDirection", None)
        with open(json_file, "w") as f:
            json.dump(sidecar, f, indent=2)

def inject_014(session_dir: Path):
    """Delete the reverse-PE EPI fieldmap."""
    fmap_dir = session_dir / "fmap"
    for f in fmap_dir.glob("*_epi.*"):
        f.unlink()

def inject_030(session_dir: Path):
    """Delete the bvec file — gradient table missing."""
    for bvec in (session_dir / "dwi").glob("*.bvec"):
        bvec.unlink()

def inject_031(session_dir: Path):
    """Scale all non-b0 bvec vectors to norm 0.5 (implausible)."""
    bval_file = next((session_dir / "dwi").glob("*.bval"))
    bvec_file = next((session_dir / "dwi").glob("*.bvec"))

    bvals = np.array([float(x) for x in bval_file.read_text().split()])
    bvecs = np.loadtxt(bvec_file)  # shape: (3, N)

    for i in range(bvecs.shape[1]):
        if bvals[i] > 50:  # non-b0 volume
            bvecs[:, i] *= 0.5  # scale to half-length

    np.savetxt(bvec_file, bvecs, fmt="%.6f")
```

**`numpy.loadtxt(bvec_file)`**: reads a text file into a 2D numpy array. FSL bvec format has 3 rows × N columns, so this gives a `(3, N)` array.

**`bvecs[:, i] *= 0.5`**: multiply the entire i-th column (all three components of gradient i) by 0.5. The `:` means "all rows".

### 23.3 What we discovered

The def-021 result was unexpected: QSIPrep reported "finished successfully!" with exit code 0, but produced **only anatomical derivatives** — no DWI output. The DWI session was silently excluded from the workflow during the grouping step.

This differs from the real-world sub-036/sub-069 failures where QSIPrep crashed immediately with:
```
AttributeError: Can only use .str accessor with string values!
```
at `merge.py:710` inside `get_acq_parameters_df()`.

Both represent failure to produce usable DWI output. The silent-skip mode is more dangerous because the exit code is 0 and the log says "finished successfully!"

**The lesson**: exit code 0 and "finished successfully!" are insufficient criteria for determining that DWI preprocessing succeeded. You must check for the presence of expected output files (`*desc-preproc_dwi.nii.gz`).

---

## 24. Statistical Methods

### 24.1 The 2×2 confusion matrix

For a binary classifier (Vecta flags vs. doesn't flag) against a binary outcome (QSIPrep fails vs. succeeds):

|  | QSIPrep fails | QSIPrep succeeds |
|--|---|---|
| **Vecta flags** | TP (true positive) | FP (false positive) |
| **Vecta doesn't flag** | FN (false negative) | TN (true negative) |

In our case:
- `ready` = "Vecta doesn't flag" 
- `ready_with_limitations` or `review_required` = "Vecta flags"

Results: TP=3, FP=40, TN=26, FN=0 (n=69)

### 24.2 Performance metrics

```python
import numpy as np
import scipy.stats as st

def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion k/n."""
    z = st.norm.ppf(1 - alpha/2)  # z = 1.96 for 95% CI
    p = k / n
    center = (p + z**2 / (2*n)) / (1 + z**2 / n)
    hw = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / (1 + z**2/n)
    return max(0, center - hw), min(1, center + hw)

TP, FP, TN, FN = 3, 40, 26, 0

sensitivity = TP / (TP + FN)        # = 1.000  (all failures caught)
specificity = TN / (TN + FP)        # = 0.394  (true negatives / total negatives)
ppv = TP / (TP + FP)                # = 0.070  (precision — of flagged, fraction that fail)
npv = TN / (TN + FN)                # = 1.000  (of not-flagged, fraction that succeed)

sens_ci  = wilson_ci(TP, TP + FN)   # [0.439, 1.000]
spec_ci  = wilson_ci(TN, TN + FP)   # [0.285, 0.515]
ppv_ci   = wilson_ci(TP, TP + FP)   # [0.024, 0.186]
npv_ci   = wilson_ci(TN, TN + FN)   # [0.871, 1.000]
```

**Why Wilson intervals instead of normal approximation?**: the normal approximation (Wald interval) breaks down when proportions are near 0 or 1 (e.g. sensitivity=1.0 gives a zero-width Wald interval, which is wrong). Wilson intervals are better calibrated at extremes.

**`scipy.stats.norm.ppf(0.975)`**: the percent-point function (inverse of CDF) at 97.5% = 1.96. This is the z-score for a 95% CI.

### 24.3 Interpreting PPV = 0.070

PPV (positive predictive value) = 3/43 = 7% means: of all 43 sessions Vecta flagged as non-ready, only 3 actually failed. 40 "false positives" (GE sessions without SDC) were flagged by VECTA-DWI-014 but processed successfully.

This is not a problem — VECTA-DWI-014 makes a **structural claim** (no reverse-PE reference available for SDC), not a prediction of pipeline crash. The 40 GE sessions ran without SDC via a fallback path. The SDC-absent output is a valid result with a known methodological limitation, which is exactly what `ready_with_limitations` means.

---

## 25. Key Bugs Found and What They Taught

### Bug 1: VECTA-DWI-031 never firing

**Symptom**: running controlled defect injection with def-031 (scaled bvec norms) produced `ready` instead of `ready_with_limitations`.

**Root cause**: `assemble.py` only iterates `spec.profile["criteria"]`. VECTA-DWI-031 was correctly defined in `criteria/dwi_connectomics.yaml` but was not listed in `profiles/dwi_connectomics.yaml` under `criteria:`.

**Fix**: add `VECTA-DWI-031` to the profile criteria list.

**Lesson**: a criterion defined in the spec YAML but not in the profile list is silently ignored. There's no error or warning — it just doesn't run. Always verify with injection testing.

---

### Bug 2: def-030 producing `ready_with_limitations` instead of `not_ready`

**Symptom**: deleting the bvec file (def-030) produced `ready_with_limitations` instead of `not_ready`.

**Root cause**: VECTA-DWI-030 was listed in the profile's `criteria` list but NOT in the `blocking_criteria` list. Non-blocking criteria produce `ready_with_limitations` regardless of severity.

**Fix**: add `VECTA-DWI-030` to `blocking_criteria` in the profile.

**Lesson**: `severity: critical` in the criterion YAML does not automatically make it blocking. The blocking designation is explicitly set in the **profile**, not the criterion. This separation is intentional (the same criterion could be blocking in one profile and non-blocking in another), but it means you can have a "critical" criterion that doesn't block if the profile is wrong.

---

### Bug 3: sub-076 failure incorrectly attributed to fieldmap absence

**Symptom**: the paper originally stated "Sub-076 failed because the fieldmap was absent (VECTA-DWI-014)."

**Root cause**: this was an untested assumption. We looked at sub-076's Vecta findings (VECTA-DWI-014) and assumed the finding predicted the failure mode.

**Investigation**: reading the actual QSIPrep log for sub-076 (844 lines, log truncated before crash). The log showed QSIPrep passed parameter extraction, completed anatomical preprocessing, and entered the eddy step. The crash occurred at the eddy step with no recoverable error message. Sub-076's sidecar had valid `PhaseEncodingDirection: "j-"` and `TotalReadoutTime: 0.0890532`. Its protocol (50 b1000 directions, 3 b0 volumes) was slightly atypical compared to other GE sessions (51-53 directions).

**Fix**: paper corrected to state the direct cause was not recovered and is not attributable to fieldmap absence.

**Lesson**: a Vecta finding identifies a structural condition in the data, not necessarily the cause of a specific failure. 40 other fieldmap-absent GE sessions with identical VECTA-DWI-014 findings ran eddy successfully. Vecta-DWI-014 correctly characterizes the methodological limitation (no SDC) but the eddy failure had a different, unidentified cause.

---

### Bug 4: def-021 injection — different failure mode than expected

**Symptom**: def-021 (PhaseEncodingDirection removed) ran for 42 minutes and reported "QSIPrep finished successfully!" The expected behavior was a crash like sub-036/sub-069.

**Investigation**: the 290-line log showed QSIPrep found 1 DWI scan but output `[]` after the grouping step. Output directory contained only anatomical derivatives.

**Root cause**: the injection used sub-001 (Siemens Prisma), whose fmap sidecar still had a valid `PhaseEncodingDirection`. This is a different context from sub-036/sub-069 (Siemens Skyra) where BOTH the DWI and fmap lacked PhaseEncodingDirection. QSIPrep may have handled the missing DWI PhaseEncodingDirection differently when the fmap had it.

**Fix**: paper updated to describe two distinct VECTA-DWI-021 failure modes: crash mode (sub-036/sub-069) and silent-skip mode (def-021). Both are DWI preprocessing failures. The silent-skip mode is operationally more dangerous.

**Lesson**: controlled injection results depend on the baseline session context. Using a different session than the real-world failures can expose different code paths in QSIPrep. This is actually scientifically interesting — it expands the characterization of what VECTA-DWI-021 predicts.

---

### Bug 5: sub-069 BIDS validation failure from miscopied .bval in fmap/

**Symptom**: running QSIPrep on the pre-intervention test BIDS for sub-069 failed BIDS validation.

**Root cause**: the setup script used `for f in "$FOR_REVIEW/sub-069/ses-1/fmap/"*; do cp "$f" ...` which copied ALL files including `.bval` files. EPI fieldmaps in BIDS do not have `.bval` files — BIDS validator rejected the dataset.

**Fix**: changed the loop to iterate only over `.nii.gz` and `.json` extensions:
```bash
for ext in nii.gz json; do
  for f in "$FOR_REVIEW/sub-069/ses-1/fmap/"*."$ext"; do
    [ -e "$f" ] && cp "$f" "$BIDS_DIR/sub-069/ses-1/fmap/"
  done
done
```

**`[ -e "$f" ]`**: tests if the file exists. When a glob pattern matches nothing (no `.json` files in the fmap dir), bash expands the pattern literally (the string `*."$ext"`). The existence check prevents trying to copy a file literally named `*.nii.gz`.

---

### Bug 6: FS_LICENSE path wrong

**Symptom**: SLURM jobs failed immediately because the FreeSurfer license file was not found.

**Root cause**: the path used was `/mnt/nfs/home/URMC-SH/pndagiji/Documents/others/containers/license.txt` (guessed). The actual path was `/mnt/nfs/home/urmc-sh.rochester.edu/pndagiji/Documents/others/data_mining/freesurfer/license.txt` (lowercase `urmc-sh.rochester.edu` vs `URMC-SH`).

**Discovery**: found the correct path by checking the existing working QSIPrep pipeline config file.

**Lesson**: never guess filesystem paths. Always verify from a known working configuration.

---

## 26. Manuscript Integration

### 26.1 Writing the paper in Markdown

The manuscript was written entirely in Markdown (`writing/abstract.md`, `writing/results.md`, `writing/discussion.md`, `writing/methods.md`, `writing/references.yaml`) and converted to Word docx using a Python script with `pandoc`.

```python
# writing/build_docx.py
import subprocess
import shutil

sections = [
    ("abstract.md", "abstract.docx"),
    ("methods.md", "methods.docx"),
    ("results.md", "results.docx"),
    ("discussion.md", "discussion.docx"),
]

for md_file, docx_file in sections:
    subprocess.run([
        "pandoc", md_file,
        "-o", docx_file,
        "--reference-doc", "reference.docx"  # Word template for formatting
    ])
```

**Why Markdown not Word**: version control (git) works well with plain text. Two people can edit `results.md` and see exactly what changed. Word `.docx` files are binary XML — git diffs are unreadable. The docx is a generated artifact, not the source of truth.

### 26.2 Numbers are never hardcoded

Every number in the manuscript (n=69, sensitivity=1.000, failure rate 2.4%) was computed from data and then written into the markdown. When we expanded the cohort from n=62 to n=69, we searched for all affected numbers and updated them together.

**The consistency audit** (done by an agent reading all three files) found 8 issues where numbers had been updated in one place but not another:
- discussion.md opening said "62 sessions" when results had been updated to 69
- Level 1 CI was different in the table vs. the discussion paragraph
- "97.1%" in one place, should be "97.6%"
- Duplicate "A third limitation" label
- TrackTBI incorrectly cited as confirming a VECTA-DWI-021 failure

**Lesson**: always run a consistency check before submitting. When you update a number, search for every other place that number appears.

### 26.3 Wilson CIs as Python one-liners

```python
from scipy.stats import norm
import numpy as np

def wilson_ci(k, n, alpha=0.05):
    z = norm.ppf(1 - alpha/2)
    p = k / n
    center = (p + z**2/(2*n)) / (1 + z**2/n)
    hw = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / (1 + z**2/n)
    return max(0, center - hw), min(1, center + hw)

# Recompute everything when n changes
TP, FP, TN, FN = 3, 40, 26, 0
print(f"Sensitivity: {TP/(TP+FN):.3f} {wilson_ci(TP, TP+FN)}")
print(f"NPV: {TN/(TN+FN):.3f} {wilson_ci(TN, TN+FN)}")
```

Running this script immediately before finalizing the methods section ensures all CIs in the paper are internally consistent.

---

## 27. Concept Glossary

| Term | Meaning |
|------|---------|
| **BIDS** | Brain Imaging Data Structure — standard directory layout for neuroimaging data |
| **DWI** | Diffusion-weighted MRI — measures water diffusion to reconstruct brain fiber structure |
| **bval** | Text file with one b-value per DWI volume |
| **bvec** | Text file with one 3D gradient direction per DWI volume (3 rows × N columns) |
| **SDC** | Susceptibility distortion correction — geometric correction using a reverse-PE fieldmap |
| **TOPUP** | FSL tool for SDC using two volumes acquired with opposite phase-encoding directions |
| **eddy** | FSL tool for correcting eddy-current distortions and head motion in DWI |
| **QSIPrep** | Python pipeline that runs SDC, eddy, and other DWI preprocessing steps |
| **SLURM** | Job scheduler for HPC clusters |
| **Singularity** | HPC container system (like Docker but for shared clusters) |
| **pyproject.toml** | Modern Python project configuration file (replaces setup.py) |
| **src layout** | Python package inside `src/` to avoid accidental uninstalled imports |
| **Pydantic v2** | Python library for data validation with type annotations |
| **JSON Schema** | Specification for describing and validating JSON/YAML document structure |
| **pytest fixture** | Reusable test component declared as a function parameter |
| **Golden output** | Saved expected output used for regression testing |
| **Wilson CI** | Confidence interval for proportions, accurate near 0 and 1 |
| **Sensitivity** | TP / (TP + FN) — fraction of true failures caught |
| **NPV** | TN / (TN + FN) — fraction of "not flagged" that truly succeed |
| **Defect injection** | Deliberately corrupt a known-good dataset to test detection |
| **Entry point** | CLI command wired to a Python function via pyproject.toml |
| **Heredoc** | `<< DELIMITER ... DELIMITER` — multi-line string in bash |
| **bind mount** | `-B host:container` — making a host path accessible inside a Singularity container |
| **IntendedFor** | BIDS sidecar field linking a fieldmap to the DWI scan it corrects |
| **PhaseEncodingDirection** | Signed axis (e.g. `"j-"`) — required by QSIPrep |
| **PhaseEncodingAxis** | Unsigned axis (e.g. `"j"`) — insufficient for SDC, triggers VECTA-DWI-021 |
| **Blocking criterion** | A criterion whose finding produces `not_ready` |
| **Review criterion** | A criterion whose `unknown` status produces `review_required` |
| **DBI** | Data Birth Integrity — the framework concept underpinning Vecta |
| **Lifecycle layer** | Where in the data pipeline a problem originated (scanner, DICOM, BIDS, etc.) |
| **Criterion attribution** | Identifying exactly which criterion triggered, for which variable, from which evidence |
| **Profile** | An intended-use declaration that selects which criteria are active |
| **Intended-use conditionality** | Readiness is only meaningful for a declared downstream use |
| **Null safety** | An absent variable is not treated as a safe zero — it's `unknown` |
| **Determinism** | Same inputs + same spec version = same output, always |
| **Version-pinning** | Every output records the exact spec version that produced it |
| **False positive** | A session Vecta flags that actually processes successfully (e.g. GE sessions with VECTA-DWI-014 that QSIPrep handles via no-SDC fallback) |
| **Silent failure** | QSIPrep reports success but produces no DWI output — exit code 0 is insufficient |
| **Completeness ratio** | Fraction of variables that were successfully extracted (not `unknown`/`not_collected`) |
