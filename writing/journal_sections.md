# NeuroImage Submission Requirements

_Complete all placeholders marked [TODO] before submission._

---

## Highlights

(3–5 bullet points; ≤85 characters each; required by NeuroImage)

- Vecta-DWI assesses DWI preprocessing readiness before pipelines run
- TrackTBI external validation (1,275 sessions): sensitivity 0.989, NPV 0.984, PPV 1.000
- Perfect vendor stratification: Siemens→ready_with_limitations; GE/Philips→review_required
- PhaseEncodingDirection absence causes silent DWI skip—undetectable from pipeline exit code
- Validated across 5 datasets: CIDUR (development), TrackTBI (1,275 sessions), 3 OpenNeuro cohorts

---

## Keywords

diffusion-weighted MRI; data quality; preprocessing readiness; BIDS; metadata integrity; susceptibility distortion correction; reproducibility; quality control

---

## CRediT Author Statement

_Fill in actual contributions once co-authors are confirmed._

**[First author / P. Ndagijimana]:** Conceptualization, Methodology, Software, Formal Analysis, Investigation, Data Curation, Writing – Original Draft, Visualization

**[Co-author(s)]:** [TODO — specify contributions: e.g., Data Curation, Resources, Investigation]

**[PI / Last author]:** Conceptualization, Supervision, Writing – Review & Editing, Funding Acquisition, Resources

---

## Ethics Statement

The CIDUR study was approved by the University of Rochester Medical Center Institutional Review Board (IRB protocol #[TODO: insert protocol number]). All participants provided written informed consent prior to enrollment. The TrackTBI pilot data were accessed under an existing data use agreement with the Federal Interagency Traumatic Brain Injury Research (FITBIR) informatics system; no new participants were recruited for this study. The three OpenNeuro validation datasets (ds000201, ds003416, ds004712) are publicly available under open access terms; no IRB approval was required for secondary analysis of de-identified public data.

---

## Data Availability Statement

The CIDUR dataset contains protected health information and is not publicly available. Vecta assessment outputs (readiness states, criterion findings) for CIDUR sessions, stripped of subject-level identifiers, are available from the corresponding author upon reasonable request subject to institutional data use procedures.

The three OpenNeuro datasets used for external validation are publicly available:
- Stockholm SleepyBrain (ds000201): https://openneuro.org/datasets/ds000201
- MASiVar (ds003416): https://openneuro.org/datasets/ds003416
- ON-Harmony (ds004712): https://openneuro.org/datasets/ds004712

The TrackTBI pilot data are available via the FITBIR data repository (https://fitbir.nih.gov/) to investigators with an approved data use agreement.

---

## Code Availability Statement

Vecta-DWI v0.1 is open-source and publicly available at:
https://github.com/phindagijimana/vecta-dwi

The repository includes the complete versioned specification (YAML variable, criterion, and profile definitions), the Python engine, JSON Schema validation contracts, synthetic BIDS test fixtures with golden expected outputs, all analysis scripts used in this paper, and installation instructions. The software can be installed directly from GitHub:

```
pip install git+https://github.com/phindagijimana/vecta-dwi.git
```

Specification version: v0.1.0. All results in this paper were produced using Vecta-DWI v0.1.

---

## Declaration of Competing Interests

The authors declare no competing financial or non-financial interests.

---

## Funding

[TODO: insert grant numbers and funding agencies. Example format:
"This work was supported by [Agency] grant [number] (to [PI initials]) and [Agency] grant [number] (to [PI initials])."]

---

## Acknowledgments

[TODO: acknowledge data collection staff, scanner operators, and any individuals who provided access to TrackTBI data or assisted with BIDS conversion but do not qualify as co-authors under ICMJE criteria.]

---

## Checklist notes for submission

- [ ] Clark et al. (2024) reference — complete journal/volume/pages from PMID 39484409
- [ ] IRB protocol number — insert in Ethics Statement
- [ ] CRediT — confirm with all co-authors and fill in
- [ ] Funding — insert grant numbers from PI
- [ ] Acknowledgments — draft with PI
- [ ] Clark et al. (2024) — complete journal/volume/pages (PMID 39484409)
- [ ] TrackTBI citation — replace Yue et al. (2013) with full cohort citation; marked [TODO] in methods.md
- [ ] IRB protocol number — insert in Ethics Statement
- [ ] CRediT — confirm with all co-authors
- [ ] Funding — insert grant numbers from PI
- [ ] Acknowledgments — draft with PI
- [x] Figures 1–4 — GENERATED: figure_1_cidur_readiness_outcome.png, figure_2_detection_levels.png, figure_3_criterion_heatmap.png, figure_4_tracktbi_readiness_outcome.png (300 DPI, writing/figures/)
- [x] Full TrackTBI external validation — COMPLETED: 1,275 sessions, sensitivity 0.989, NPV 0.984, PPV 1.000
- [x] QSIPrep version — RESOLVED: 1.0.1.dev0+gee9aa2e.d20250115 throughout
- [x] Abstract restructured — TrackTBI primary, CIDUR development, 250 words, CIs included
- [x] Criterion descriptions — Table 1 aligned with spec YAML finding labels
- [x] Never_attempted asymmetry — explained (22.8% vs 10.0%); proportional imputation added
- [x] v0.1.1 note — removed; clean v0.1.0 version statement in methods and Table 10
- [x] Table numbering — all 11 tables labeled and numbered consecutively
