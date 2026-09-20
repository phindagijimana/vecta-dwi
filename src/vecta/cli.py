"""Vecta-DWI command-line interface.

Commands:
  vecta assess         Run assessment for one BIDS session and emit vecta.json
  vecta aggregate      Aggregate per-session vecta.json files into cohort tables
  vecta validate-spec  Validate the specification files without running anything
  vecta explain        Explain a finding by ID (prints criterion, evidence, rationale)
  vecta version        Print software + spec versions
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import SCHEMA_VERSION, SPEC_VERSION, __version__ as VECTA_VERSION


def _cmd_assess(args: argparse.Namespace) -> int:
    from .collectors import bids as bids_collector
    from .collectors import dicom as dicom_collector
    from .output.assemble import (
        assess_session,
        check_referential_integrity,
        to_dict,
        validate_against_schema,
    )
    from .spec.loader import load as load_spec

    spec = load_spec(Path(args.spec), profile_id=args.profile)
    session = bids_collector.collect(
        Path(args.dataset), subject_id=args.subject, session_id=args.session
    )
    dcm_inv = None
    if args.dicom:
        dcm_inv = dicom_collector.collect(Path(args.dicom))

    assessment = assess_session(session, spec, dicom_inventory=dcm_inv)
    payload = to_dict(assessment)

    schema_root = Path(args.spec) / "schemas"
    validate_against_schema(payload, schema_root)
    check_referential_integrity(payload)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "vecta.json").write_text(json.dumps(payload, indent=2))

    if "tsv" in args.formats:
        from .output.tsv import render_tsv
        (out / "vecta.tsv").write_text(render_tsv([payload]))
    if "html" in args.formats:
        try:
            from .output.html import render_html
        except ImportError:
            print("HTML output requested but html module not built yet", file=sys.stderr)
        else:
            (out / "report.html").write_text(render_html(payload))

    print(f"Wrote {out / 'vecta.json'}", file=sys.stderr)
    print(f"  readiness:  {payload['readiness']['state']}", file=sys.stderr)
    print(f"  findings:   {len(payload['findings'])}", file=sys.stderr)
    return 0


def _cmd_aggregate(args: argparse.Namespace) -> int:
    from .output import cohort as cohort_module

    payloads = []
    for p in sorted(Path(args.assessments_dir).rglob("vecta.json")):
        payloads.append(json.loads(p.read_text()))
    if not payloads:
        print(f"No vecta.json files found under {args.assessments_dir}", file=sys.stderr)
        return 1

    result = cohort_module.aggregate(payloads)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "session_summary.tsv").write_text(cohort_module.render_session_summary(result))
    (out / "findings_long.tsv").write_text(cohort_module.render_findings_long(result))
    (out / "variables_long.tsv").write_text(cohort_module.render_variables_long(result))
    (out / "finding_prevalence.tsv").write_text(cohort_module.render_finding_prevalence(result))
    (out / "missingness_matrix.tsv").write_text(cohort_module.render_missingness_matrix(result))
    print(
        f"Aggregated {result.assessed_sessions} sessions "
        f"({result.completed_sessions} completed) → {out}",
        file=sys.stderr,
    )
    return 0


def _cmd_validate_spec(args: argparse.Namespace) -> int:
    from .spec.loader import load as load_spec, SpecificationError

    try:
        spec = load_spec(Path(args.spec), profile_id=args.profile)
    except SpecificationError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(
        f"Specification {spec.version} valid: "
        f"{len(spec.variables)} variables, {len(spec.criteria)} criteria, "
        f"{len(spec.evidence)} evidence entries, "
        f"{len(spec.tolerances)} tolerances.",
        file=sys.stderr,
    )
    return 0


def _cmd_explain(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.assessment).read_text())
    finding = next((f for f in payload.get("findings", []) if f["finding_id"] == args.finding_id), None)
    if finding is None:
        print(f"Finding {args.finding_id} not found in {args.assessment}", file=sys.stderr)
        return 1
    print(f"Finding: {finding['finding_id']}")
    print(f"  Criterion:      {finding['criterion_id']} v{finding['criterion_version']}")
    print(f"  Label:          {finding['label']}")
    print(f"  Category:       {finding['category']}")
    print(f"  Severity:       {finding['severity']} ({finding['severity_status']})")
    print(f"  Confidence:     {finding['confidence']}")
    print(f"  Profile:        {finding['affected_profile']}")
    print(f"  Observed:       {finding['observed_condition']}")
    if finding.get("reference_condition"):
        print(f"  Reference:      {finding['reference_condition']}")
    print(f"  Evidence:       {', '.join(finding['evidence_refs'])}")
    if finding.get("potential_effects"):
        print("  Potential effects:")
        for pe in finding["potential_effects"]:
            print(f"    - [{pe['relation']}] {pe['effect_id']}: {pe['wording'].strip()}")
    if finding.get("recommended_actions"):
        print("  Recommended actions:")
        for a in finding["recommended_actions"]:
            print(f"    - [{a['action_class']}] {a['text'].strip()}")
    print(f"  Empirical:      {finding['empirical_status']['state']}")
    print(f"  Spec version:   {finding['spec_version']}")
    return 0


def _cmd_version(args: argparse.Namespace) -> int:
    print(f"vecta-dwi software: {VECTA_VERSION}")
    print(f"specification:      {SPEC_VERSION}")
    print(f"schema:             {SCHEMA_VERSION}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vecta", description="Vecta-DWI CLI")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("assess", help="Assess a BIDS session")
    a.add_argument("--dataset", required=True, help="BIDS dataset root")
    a.add_argument("--subject", required=True, help="Subject label (without sub- prefix)")
    a.add_argument("--session", required=True, help="Session label (without ses- prefix)")
    a.add_argument("--dicom", help="Optional DICOM source directory")
    a.add_argument("--spec", required=True, help="Specification root (e.g. specification/v0.1)")
    a.add_argument("--profile", default="dwi_connectomics")
    a.add_argument("--output", required=True, help="Directory to write vecta.json etc.")
    a.add_argument("--formats", nargs="+", default=["json"], choices=["json", "tsv", "html"])
    a.set_defaults(func=_cmd_assess)

    ag = sub.add_parser("aggregate", help="Aggregate per-session assessments")
    ag.add_argument("assessments_dir", help="Directory tree containing vecta.json files")
    ag.add_argument("--output", required=True, help="Directory for cohort artifacts")
    ag.set_defaults(func=_cmd_aggregate)

    v = sub.add_parser("validate-spec", help="Validate a specification without running data")
    v.add_argument("--spec", required=True)
    v.add_argument("--profile", default="dwi_connectomics")
    v.set_defaults(func=_cmd_validate_spec)

    e = sub.add_parser("explain", help="Explain a finding by ID")
    e.add_argument("--assessment", required=True, help="Path to a vecta.json file")
    e.add_argument("--finding-id", required=True)
    e.set_defaults(func=_cmd_explain)

    ver = sub.add_parser("version", help="Print software + spec versions")
    ver.set_defaults(func=_cmd_version)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
