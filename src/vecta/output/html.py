"""HTML report renderer.

Renders one canonical assessment JSON as a human-readable HTML page.
Contract (Output Tech Spec §30, §69):
  - Renders from canonical JSON only.
  - Does NOT re-implement any scientific rule; severity/confidence/etc.
    come directly from the JSON.
  - No PHI by default (relies on the privacy filter to have already
    dropped restricted evidence).
  - Every finding shows observed condition, reference, evidence,
    severity+basis, confidence, potential effects (with relation status),
    recommended actions.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, select_autoescape

_env = Environment(autoescape=select_autoescape(["html", "xml"]))

_TEMPLATE = _env.from_string(
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Vecta-DWI assessment {{ p.assessment_id }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           max-width: 960px; margin: 2em auto; padding: 0 1em;
           color: #222; line-height: 1.45; }
    h1, h2, h3 { color: #113; margin-top: 1.6em; }
    .meta { color: #555; font-size: 0.9em; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
             font-size: 0.85em; font-weight: 600; }
    .readiness-ready { background: #d9f7d3; color: #175317; }
    .readiness-ready_with_limitations { background: #fff3c4; color: #6a5000; }
    .readiness-review_required { background: #ffe0a3; color: #7a4a00; }
    .readiness-not_ready { background: #ffd0d0; color: #7a1414; }
    .readiness-not_assessed { background: #e6e6e6; color: #444; }
    .sev-critical { background: #ffd0d0; color: #7a1414; }
    .sev-major    { background: #ffe0a3; color: #7a4a00; }
    .sev-moderate { background: #fff3c4; color: #6a5000; }
    .sev-informational { background: #e2ecff; color: #1a3d7a; }
    .conf { font-size: 0.8em; color: #666; }
    table.k v { border-collapse: collapse; }
    .kv td { padding: 3px 12px 3px 0; vertical-align: top; }
    .kv td.k { color: #555; white-space: nowrap; }
    .finding { border: 1px solid #ddd; border-radius: 6px;
               padding: 12px 16px; margin: 12px 0; background: #fbfbfb; }
    .finding .label { font-weight: 600; }
    .finding ul { margin: 4px 0 6px 20px; padding: 0; }
    details { margin: 8px 0; }
    summary { cursor: pointer; font-weight: 500; }
    .note { color: #666; font-size: 0.9em; }
    code { background: #f4f4f6; padding: 1px 4px; border-radius: 3px; }
    .footer { margin-top: 3em; color: #888; font-size: 0.85em; border-top: 1px solid #eee; padding-top: 1em; }
  </style>
</head>
<body>

<h1>Vecta-DWI assessment</h1>

<table class="kv">
  <tr><td class="k">Subject / session</td><td><code>{{ p.subject_id }}</code> / <code>{{ p.session_id }}</code></td></tr>
  <tr><td class="k">Profile</td><td>{{ p.profile.id }} v{{ p.profile.version }}</td></tr>
  {% if p.protocol_reference %}
  <tr><td class="k">Protocol reference</td><td>{{ p.protocol_reference.id }} v{{ p.protocol_reference.version }}</td></tr>
  {% endif %}
  <tr><td class="k">Assessment ID</td><td><code>{{ p.assessment_id }}</code></td></tr>
  <tr><td class="k">Assessment status</td><td><code>{{ p.assessment_status.state }}</code></td></tr>
  <tr><td class="k">Readiness</td>
      <td><span class="badge readiness-{{ p.readiness.state }}">{{ p.readiness.state }}</span></td></tr>
  {% if p.readiness.dimensions.assessment_completeness %}
  <tr><td class="k">Assessment completeness</td>
      <td>{{ p.readiness.dimensions.assessment_completeness.ratio }}
          ({{ p.readiness.dimensions.assessment_completeness.observed_or_derived }}
          / {{ p.readiness.dimensions.assessment_completeness.applicable_variables }})</td></tr>
  {% endif %}
</table>

<p class="note">
  Readiness does not guarantee clinical or scientific validity. Severity
  labels are provisional interpretations for the stated intended use, not
  probabilities.
</p>

<h2>Findings ({{ p.findings|length }})</h2>

{% if p.findings %}
  {% for f in p.findings|sort(attribute='severity', reverse=True) %}
    <div class="finding">
      <div>
        <span class="badge sev-{{ f.severity }}">{{ f.severity }}</span>
        <span class="conf">confidence: {{ f.confidence }}</span>
        <span class="conf">status: {{ f.severity_status }}</span>
        <span class="label">— {{ f.label }}</span>
      </div>
      <div class="meta">
        <code>{{ f.criterion_id }}</code> v{{ f.criterion_version }}
        · category {{ f.category }}
        · lifecycle {{ f.lifecycle_origin }}
      </div>
      <details open>
        <summary>Observed condition</summary>
        <pre>{{ f.observed_condition|tojson(indent=2) }}</pre>
      </details>
      {% if f.reference_condition %}
      <details>
        <summary>Reference condition</summary>
        <pre>{{ f.reference_condition|tojson(indent=2) }}</pre>
      </details>
      {% endif %}
      {% if f.potential_effects %}
      <details open>
        <summary>Potential effects (plausible unless empirically supported)</summary>
        <ul>
          {% for pe in f.potential_effects %}
          <li>
            <em>[{{ pe.relation }}]</em>
            <strong>{{ pe.effect_id }}</strong>: {{ pe.wording }}
          </li>
          {% endfor %}
        </ul>
      </details>
      {% endif %}
      {% if f.recommended_actions %}
      <details open>
        <summary>Recommended actions</summary>
        <ul>
          {% for a in f.recommended_actions %}
          <li>
            <em>[{{ a.action_class }}]</em>
            {{ a.text }}
            {% if a.requires_human_approval %}<span class="conf">(requires human approval)</span>{% endif %}
          </li>
          {% endfor %}
        </ul>
      </details>
      {% endif %}
      <details>
        <summary>Evidence + basis</summary>
        <div>Evidence: <code>{{ f.evidence_refs|join(', ') }}</code></div>
        <div>Severity basis: <code>{{ f.severity_basis|join(', ') }}</code></div>
        <div>Variables: <code>{{ f.variable_refs|join(', ') }}</code></div>
        <div>Empirical status: <code>{{ f.empirical_status.state }}</code></div>
      </details>
    </div>
  {% endfor %}
{% else %}
  <p>No findings emitted for the selected profile.</p>
{% endif %}

<h2>Unknown / unevaluable criteria</h2>

{% set unknown_criteria = p.criteria|selectattr('status', 'equalto', 'unknown')|list %}
{% if unknown_criteria %}
  <ul>
    {% for c in unknown_criteria %}
      <li><code>{{ c.criterion_id }}</code> — evidence insufficient to evaluate</li>
    {% endfor %}
  </ul>
{% else %}
  <p>All criteria evaluated deterministically.</p>
{% endif %}

<h2>Variables</h2>

<table class="kv">
  <thead>
    <tr><td class="k"><strong>Variable</strong></td><td><strong>Value</strong></td><td><strong>State</strong></td></tr>
  </thead>
  {% for vid, v in p.variables.items()|sort %}
    <tr>
      <td class="k"><code>{{ vid }}</code></td>
      <td>{% if v.value is none %}<em>(null)</em>{% else %}<code>{{ v.value }}</code>{% endif %}</td>
      <td><code>{{ v.state }}</code></td>
    </tr>
  {% endfor %}
</table>

<div class="footer">
  <div>Vecta software {{ p.provenance.vecta_software_version }}
       · spec {{ p.provenance.specification_version }}
       · schema {{ p.provenance.schema_version }}
       · profile {{ p.provenance.profile_version }}</div>
  <div>Executed at {{ p.provenance.executed_at }}</div>
  <div class="note">Rendered from canonical vecta.json. No scientific rule
  is re-implemented here.</div>
</div>

</body>
</html>
"""
)


def render_html(payload: dict[str, Any]) -> str:
    """Render one Assessment payload as HTML."""
    return _TEMPLATE.render(p=payload)
