"""Load and validate the specification at engine start.

Spec files (variables/*.yaml, criteria/*.yaml, profiles/*.yaml) are
validated against their input JSON Schemas before any data is assessed
(Spec Blueprint §23). Invalid or internally inconsistent specifications
fail loudly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


class SpecificationError(Exception):
    """Raised when the specification is invalid or inconsistent."""


@dataclass
class LoadedSpec:
    root: Path
    version: str
    variables: dict[str, dict[str, Any]] = field(default_factory=dict)
    criteria: dict[str, dict[str, Any]] = field(default_factory=dict)
    profile: dict[str, Any] = field(default_factory=dict)
    tolerances: dict[str, dict[str, Any]] = field(default_factory=dict)
    evidence: dict[str, dict[str, Any]] = field(default_factory=dict)


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def _build_schema_registry(schema_root: Path) -> Registry:
    reg = Registry()
    for f in schema_root.rglob("*.schema.json"):
        doc = json.loads(f.read_text())
        if doc.get("$id"):
            reg = reg.with_resource(doc["$id"], Resource(contents=doc, specification=DRAFT202012))
        reg = reg.with_resource(
            "file://" + str(f.resolve()),
            Resource(contents=doc, specification=DRAFT202012),
        )
    return reg


def _validate(instance: Any, schema_path: Path, registry: Registry, label: str) -> None:
    schema = json.loads(schema_path.read_text())
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        lines = [f"Specification validation failed for {label}:"]
        for e in errors[:20]:
            loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
            lines.append(f"  at {loc}: {e.message}")
        if len(errors) > 20:
            lines.append(f"  ...and {len(errors) - 20} more")
        raise SpecificationError("\n".join(lines))


def load(spec_root: Path, profile_id: str = "dwi_connectomics") -> LoadedSpec:
    """Load specification/v0.1 (or equivalent), validating everything."""
    spec_root = Path(spec_root)
    if not (spec_root / "manifest.yaml").is_file():
        raise SpecificationError(f"No manifest.yaml at {spec_root}")

    manifest = _load_yaml(spec_root / "manifest.yaml")
    version = manifest.get("version")
    if not version:
        raise SpecificationError("manifest.yaml missing version")

    schema_root = spec_root / "schemas"
    registry = _build_schema_registry(schema_root)
    var_schema = schema_root / "input/variable.schema.json"
    crit_schema = schema_root / "input/criterion.schema.json"
    prof_schema = schema_root / "input/profile.schema.json"

    loaded = LoadedSpec(root=spec_root, version=version)

    for vf in sorted((spec_root / "variables").glob("*.yaml")):
        doc = _load_yaml(vf)
        _validate(doc, var_schema, registry, f"variables/{vf.name}")
        for v in doc["variables"]:
            vid = v["variable_id"]
            if vid in loaded.variables:
                raise SpecificationError(f"Duplicate variable_id {vid}")
            loaded.variables[vid] = v

    for cf in sorted((spec_root / "criteria").glob("*.yaml")):
        doc = _load_yaml(cf)
        _validate(doc, crit_schema, registry, f"criteria/{cf.name}")
        for c in doc["criteria"]:
            cid = c["criterion_id"]
            if cid in loaded.criteria:
                raise SpecificationError(f"Duplicate criterion_id {cid}")
            loaded.criteria[cid] = c

    prof_file = spec_root / "profiles" / f"{profile_id}.yaml"
    if not prof_file.is_file():
        raise SpecificationError(f"Profile file not found: {prof_file}")
    prof_doc = _load_yaml(prof_file)
    _validate(prof_doc, prof_schema, registry, f"profiles/{prof_file.name}")
    loaded.profile = prof_doc

    tol_file = spec_root / "tolerances" / "default_tolerances.yaml"
    if tol_file.is_file():
        loaded.tolerances = _load_yaml(tol_file).get("tolerances", {})

    ev_file = spec_root / "evidence" / "evidence_registry.yaml"
    if ev_file.is_file():
        ev_doc = _load_yaml(ev_file)
        for e in ev_doc.get("evidence", []):
            loaded.evidence[e["evidence_id"]] = e

    # Referential integrity: every criterion in the profile exists;
    # every criterion's required variables exist; every evidence ref
    # in a criterion exists.
    for cid in loaded.profile.get("criteria", []):
        if cid not in loaded.criteria:
            raise SpecificationError(
                f"Profile {profile_id} references unknown criterion {cid}"
            )
    for cid, c in loaded.criteria.items():
        for vid in c.get("requires", []):
            if vid not in loaded.variables:
                raise SpecificationError(
                    f"Criterion {cid} requires unknown variable {vid}"
                )
        for eref in c.get("evidence_refs", []):
            if eref not in loaded.evidence:
                raise SpecificationError(
                    f"Criterion {cid} references unknown evidence {eref}"
                )

    return loaded
