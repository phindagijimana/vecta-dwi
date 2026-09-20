"""Versioned TSV projection of an Assessment.

The projection map lives in specification/v0.1/registries/projection_registry.yaml
(created here on first use). Each column has a stable identifier and a
JSONPath-like path into the canonical Assessment payload.

Null/unknown values are emitted as the literal string "NA" so that
`false` and `unknown` are visually distinct in the flat file (Output
Tech Spec §29).
"""

from __future__ import annotations

import io
from typing import Any


PROJECTION_ID = "vecta_session_tsv_v1"
NULL_STRING = "NA"


# Static projection map for v0.1 — mirrors Output Dictionary §25 recommended
# analysis-friendly scalar TSV. Later versions can load this from
# registries/projection_registry.yaml.
COLUMNS: list[tuple[str, str]] = [
    # (column_name, path)
    ("session_id",                     "$.session_id"),
    ("subject_id",                     "$.subject_id"),
    ("profile",                        "$.profile.id"),
    ("readiness_state",                "$.readiness.state"),
    ("assessment_status",              "$.assessment_status.state"),
    ("assessment_completeness_ratio",  "$.readiness.dimensions.assessment_completeness.ratio"),
    ("manufacturer",                   "$.variables['VECTA.DWI.SCANNER.MANUFACTURER'].value"),
    ("model",                          "$.variables['VECTA.DWI.SCANNER.MODEL'].value"),
    ("field_strength",                 "$.variables['VECTA.DWI.SCANNER.FIELD_STRENGTH'].value"),
    ("software_version",               "$.variables['VECTA.DWI.SCANNER.SOFTWARE_VERSION'].value"),
    ("voxel_size_mm",                  "$.variables['VECTA.DWI.ACQ.VOXEL_SIZE'].value"),
    ("volume_count",                   "$.variables['VECTA.DWI.ACQ.VOLUME_COUNT'].value"),
    ("bval_count",                     "$.variables['VECTA.DWI.ACQ.BVAL_COUNT'].value"),
    ("shell_count",                    "$.variables['VECTA.DWI.ACQ.SHELL_COUNT'].value"),
    ("bvec_count",                     "$.variables['VECTA.DWI.ACQ.BVEC_COUNT'].value"),
    ("bvec_plausibility",              "$.variables['VECTA.DWI.ACQ.BVEC_PLAUSIBILITY'].value"),
    ("pe_direction",                   "$.variables['VECTA.DWI.ACQ.PE_DIRECTION'].value"),
    ("total_readout_time_present",     "$.variables['VECTA.DWI.ACQ.TOTAL_READOUT_TIME_PRESENT'].value"),
    ("reverse_pe_available",           "$.variables['VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE'].value"),
    ("dicom_series_count",             "$.variables['VECTA.DWI.DICOM.SERIES_COUNT'].value"),
    ("dicom_dwi_series_count",         "$.variables['VECTA.DWI.DICOM.DWI_SERIES_COUNT'].value"),
    ("dicom_geometry_consistent",      "$.variables['VECTA.DWI.DICOM.SERIES_GEOMETRY_CONSISTENT'].value"),
    ("dicom_bids_field_strength_agree","$.variables['VECTA.DWI.DICOM.FIELD_STRENGTH_AGREES_WITH_BIDS'].value"),
    ("finding_count",                  "@count_findings()"),
    ("major_finding_count",            "@count_findings(severity=major)"),
    ("critical_finding_count",         "@count_findings(severity=critical)"),
    ("blocking_finding_count",         "@count(readiness.blocking_finding_refs)"),
    ("review_finding_count",           "@count(readiness.review_finding_refs)"),
]


def _get_path(payload: dict[str, Any], path: str) -> Any:
    """Tiny JSONPath-lite: only handles $.a.b['key'].c form used above."""
    # Strip leading $.
    if path.startswith("$."):
        path = path[2:]
    node = payload
    # Split on . but respect ['...']
    parts: list[str] = []
    buf = ""
    i = 0
    while i < len(path):
        c = path[i]
        if c == ".":
            if buf:
                parts.append(buf)
                buf = ""
        elif c == "[":
            end = path.index("]", i)
            key = path[i + 1:end].strip("'\"")
            if buf:
                parts.append(buf)
                buf = ""
            parts.append(key)
            i = end
        else:
            buf += c
        i += 1
    if buf:
        parts.append(buf)
    for p in parts:
        if node is None:
            return None
        if isinstance(node, dict):
            node = node.get(p)
        else:
            return None
    return node


def _eval_transform(payload: dict[str, Any], transform: str) -> Any:
    """Handle the small set of @-prefixed transforms used by the projection."""
    if transform == "@count_findings()":
        return len(payload.get("findings", []))
    if transform.startswith("@count_findings(severity="):
        # @count_findings(severity=major)
        sev = transform[len("@count_findings(severity="):-1]
        return sum(1 for f in payload.get("findings", []) if f.get("severity") == sev)
    if transform.startswith("@count(readiness."):
        # @count(readiness.blocking_finding_refs)
        field = transform[len("@count(readiness."):-1]
        return len(payload.get("readiness", {}).get(field, []))
    raise ValueError(f"Unknown TSV transform: {transform}")


def _fmt(value: Any) -> str:
    if value is None:
        return NULL_STRING
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return "|".join(_fmt(v) for v in value)
    if isinstance(value, dict):
        # For structured values (e.g. required_series_present), summarize
        if "missing" in value:
            missing = value["missing"]
            return "|".join(missing) if missing else "none"
        return str(value)
    return str(value)


def to_row(payload: dict[str, Any]) -> dict[str, str]:
    """Project one Assessment payload into a dict of TSV cell values."""
    row: dict[str, str] = {}
    for name, path in COLUMNS:
        if path.startswith("@"):
            value = _eval_transform(payload, path)
        else:
            value = _get_path(payload, path)
        row[name] = _fmt(value)
    return row


def render_tsv(payloads: list[dict[str, Any]]) -> str:
    """Render a header + one row per payload as TSV text."""
    buf = io.StringIO()
    header = "\t".join(name for name, _ in COLUMNS)
    buf.write(header + "\n")
    for p in payloads:
        row = to_row(p)
        buf.write("\t".join(row[name] for name, _ in COLUMNS) + "\n")
    return buf.getvalue()
