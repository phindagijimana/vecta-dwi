# CIDUR DWI conversion issues: inventory and Vecta mapping

Companion document for the Vecta-DWI Paper 1 results. Records every
post-conversion data-management intervention applied to the CIDUR_BIDS
dataset, maps each intervention to the Vecta criterion that captures the
underlying condition, and documents the pre-intervention sensitivity
analysis comparing Vecta findings across 71 (pre) and 62 (post) sessions.

---

## 1. Conversion-stage exclusions (outside Vecta scope)

These exclusions occurred before the BIDS tree was finalized and before
Vecta was applied. They define the outer boundary of the assessment
denominator. Vecta does not re-evaluate conversion-stage decisions.

| Subject | Sessions excluded | Reason documented |
|---|---|---|
| sub-016 | All (ses-1) | DWI acquisition flagged as corrupt at conversion |
| sub-018 | All (ses-1) | DWI acquisition flagged as corrupt at conversion |
| sub-047 | All (ses-1) | DWI acquisition flagged as corrupt at conversion |
| sub-065 | All (ses-1) | DWI acquisition flagged as corrupt at conversion |
| sub-002 | ses-1, ses-2 | Corrupt multi-echo phase images; DWI removed from BIDS |

**Vecta mapping:** None. These subjects/sessions are absent from the
BIDS tree that Vecta evaluates. If Vecta were applied to an earlier
draft BIDS tree that included these acquisitions, VECTA-DWI-050 (DICOM
geometry inconsistency) and VECTA-DWI-060 (DICOM/BIDS mismatch) would
be the most likely candidate criteria; however, no BIDS sidecar or
acquisition metadata is available for them from which to make that
determination.

---

## 2. Vendor selection rule exclusions (DWI)

Recorded in `CIDUR_BIDS/special_case_vendor_actions.csv`. The vendor
selection script detected DWI acquisitions that did not match the
expected site protocol (correct vendor, direction count, and BIDS
phase-encoding direction entity). Non-matching acquisitions were moved
from `data_bids/` to `for_review/special_cases_vendor/`.

The script used BIDS filename entities as its detection signal: it
read `acq-<N>dirax` to extract direction count and `dir-<X>` to detect
phase label. It did not inspect sidecar JSON content.

### 2a. GE sessions excluded for non-standard protocol

| Session | Vendor rule reason | Pre-intervention Vecta | Vecta criterion |
|---|---|---|---|
| sub-020 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-025 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-030 ses-1 | GE, dir_count=12, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-041 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-042 ses-1 | Siemens, dir_count=24, phase=ap | ready_with_limitations | VECTA-DWI-014 |
| sub-048 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-055 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |

**Interpretation.** These sessions lack a reverse-PE EPI fieldmap
regardless of direction count or phase label — consistent with the
site-level GE protocol that does not acquire EPI fieldmaps. VECTA-DWI-014
fires for each, correctly characterizing the distortion-correction
limitation. The curation motivation (non-standard direction count or no
phase-entity label) is a protocol-selection decision that Vecta does not
encode; Vecta captures the consequence (no reverse-PE reference) but
not the cause (wrong acquisition version). A future criterion extending
Vecta to enforce expected gradient-table size against a protocol
reference would close this gap.

Note: sub-042 ses-1 is Siemens (dir_count=24) with `phase=ap` (dir-AP
in filename) and was excluded because the 24-direction table is below
the site's expected 67-direction Siemens protocol. Its sidecar contains
a signed `PhaseEncodingDirection: j-`, so VECTA-DWI-021 did not trigger
(contrast with sub-069 below).

### 2b. Siemens sessions excluded for unsigned phase-encoding metadata

| Session | Vendor rule reason | Pre-intervention Vecta | Vecta criteria |
|---|---|---|---|
| sub-036 ses-1 | Siemens, dir_count=64, phase=None | review_required | VECTA-DWI-021, VECTA-DWI-001 |
| sub-069 ses-1 | Siemens, dir_count=24, phase=ap | review_required | VECTA-DWI-021, VECTA-DWI-001 |

**Root cause.** Both sessions were acquired on a Siemens Skyra scanner
whose dcm2niix version populated only the unsigned `PhaseEncodingAxis`
field (value: `j`) in the BIDS sidecar JSON, without the signed
`PhaseEncodingDirection` field (e.g., `j-`). Vecta reads only the signed
field; its absence causes:

- `VECTA-DWI-021` (essential metadata insufficient): PhaseEncodingDirection
  absent from BIDS sidecar; TotalReadoutTime present but unusable without
  confirmed PE direction for SDC calibration.
- `VECTA-DWI-001` (PE direction unknown): cannot determine polarity from
  `PhaseEncodingAxis` alone.

**Concordance with curation decision.** The vendor selection script
excluded both sessions because their BIDS filenames lacked a recognized
phase-entity label:
- sub-036: no `dir-AP` or `dir-PA` in filename (phase=None)
- sub-069: has `dir-ap` label but was still excluded (24-direction Siemens
  table; 24 ≠ 67 expected)

The curation script operated on BIDS filename entities only and had no
access to sidecar JSON. Vecta and the curation script identified the same
two sessions for concern via entirely independent evidence paths. This
concordance validates both the curation decision and the Vecta criterion:
the session-level metadata condition that makes SDC calibration impossible
was correctly characterized by Vecta's sidecar-based rule.

**Siemens Skyra dcm2niix export note.** Not all Siemens Skyra sessions
exhibit this behavior. Among the 28 Siemens sessions in the post-
intervention cohort (all rated ready), the sidecar JSONs contain signed
`PhaseEncodingDirection` values. The unsigned-axis-only export appears
to be version- or sequence-specific. Sub-042 (Siemens, 24-dir) does
carry a signed `PhaseEncodingDirection: j-` and does not trigger
VECTA-DWI-021 — confirming that the criterion discriminates based on
sidecar content, not scanner platform alone.

---

## 3. Vendor selection rule exclusions (fmap)

Thirteen Siemens sessions had extra EPI fieldmap files moved to
`for_review/special_cases_vendor/`:

| Sessions | Excluded file pattern | Reason |
|---|---|---|
| sub-007, sub-014, sub-032, sub-039, sub-046, sub-058, sub-061, sub-066, sub-069, sub-074, sub-075, sub-077, sub-078 | `*_acq-multidirax_dir-pa_epi.*` | Siemens, dir_count=None, phase=pa |

**Root cause.** dcm2niix generated these files by extracting the
b=0 reference volumes from the main DWI acquisition and packaging them
as a separate EPI series. The resulting JSON sidecar carries
`PhaseEncodingDirection: j` but no `IntendedFor` field — it is a
duplicate of the main session fieldmap, not a distinct acquisition.

**Effect on Vecta assessment.** None. Each of these sessions already
contained the primary EPI fieldmap (`sub-XXX_ses-1_dir-pa_epi.json`)
with a proper `IntendedFor` entry pointing to the DWI acquisition.
Vecta's IntendedFor-aware reverse-PE algorithm uses the primary fmap
and rates these sessions as ready, both before and after the removal
of the acq-multidirax duplicates. The 13 fmap exclusions introduce no
readiness state change.

---

## 4. The sub-002 ses-3 readiness regression

Sub-002 ses-3 is present in both the pre- and post-intervention BIDS
trees and is included in the 62-session assessment denominator. It is
the one shared session that changed readiness state between the two
assessments.

| Assessment | DWI entities present | REVERSE_PE_AVAILABLE | Readiness |
|---|---|---|---|
| Pre-intervention | acq-30dirax (PED: j) + acq-50dirax (PED: j−) | True | ready |
| Post-intervention | acq-50dirax (PED: j−) only | False | ready_with_limitations |

**Mechanism.** In the pre-intervention BIDS, both DWI acquisitions are
present. Vecta evaluates the first entity alphabetically (acq-30dirax)
and searches for a complementary PE direction among all DWI entities in
the session. The acq-50dirax entity carries `PhaseEncodingDirection: j-`,
which is the complement of `j`, so `REVERSE_PE_AVAILABLE` is derived as
True and VECTA-DWI-014 is satisfied.

After the vendor rule removes acq-30dirax (phase=None in its filename),
only acq-50dirax remains. Vecta evaluates the sole DWI entity (acq-50dirax,
PED: j−), finds no complementary acquisition and no EPI fmap, and derives
`REVERSE_PE_AVAILABLE` as False. VECTA-DWI-014 triggers.

**Significance.** The vendor rule used the BIDS filename entity `dir-<X>`
to identify phase direction. Both acquisitions lacked this label; the
30-direction acquisition was excluded as a non-conforming GE protocol
variant. The curation script did not read the sidecar JSON and therefore
could not detect the complementary-PE relationship that Vecta identifies
at the metadata level. This case demonstrates that filename-entity-based
curation can unintentionally dissolve valid complementary-PE relationships
that are expressed only in sidecar metadata — a pattern Vecta is designed
to detect.

---

## 5. Pre-intervention vs post-intervention readiness summary

| Readiness state | Pre-intervention (n=71) | Post-intervention (n=62) | Change |
|---|---|---|---|
| ready | 29 (40.8%) | 28 (45.2%) | −1 (sub-002 ses-3 regression) |
| ready_with_limitations | 40 (56.3%) | 34 (54.8%) | −6 (7 excluded → 1 regression added) |
| review_required | 2 (2.8%) | 0 (0%) | −2 (sub-036, sub-069 excluded) |

The post-intervention cohort contains no review_required sessions.
All 9 curation decisions that changed the denominator were
directionally aligned with Vecta findings: the two sessions with the
most severe metadata deficit (review_required) were removed; the seven
sessions with only VECTA-DWI-014 were also removed, reducing the
ready_with_limitations count; and one session with a hidden
complementary-PE relationship was partially degraded from ready to
ready_with_limitations by the removal.

---

## 6. Mapping to Vecta criteria

| CIDUR intervention | Sessions affected | Vecta criterion | Criterion fires |
|---|---|---|---|
| Corrupt DWI at conversion | sub-016, sub-018, sub-047, sub-065 | (outside scope) | N/A |
| Corrupt multi-echo phase images | sub-002 ses-1, ses-2 | (outside scope) | N/A |
| GE non-standard dir count (30-dir, 12-dir) | sub-020, sub-025, sub-030, sub-041, sub-048, sub-055 | VECTA-DWI-014 | Yes (no reverse PE) |
| Siemens non-standard dir count (24-dir, 64-dir, phase=None) | sub-036 | VECTA-DWI-021, VECTA-DWI-001 | Yes (unsigned PED) |
| Siemens 24-dir with dir-ap label | sub-042 | VECTA-DWI-014 | Yes (no reverse PE; PED present) |
| Siemens 24-dir, phase=ap, unsigned PED | sub-069 | VECTA-DWI-021, VECTA-DWI-001 | Yes (unsigned PED) |
| Siemens duplicate fmap (acq-multidirax) | sub-007, sub-014, sub-032, sub-039, sub-046, sub-058, sub-061, sub-066, sub-069, sub-074, sub-075, sub-077, sub-078 | None | No change |
| Vendor removal of complementary-PE GE DWI | sub-002 ses-3 (30-dir removed) | VECTA-DWI-014 | Not triggered pre-; triggered post- |

---

## 7. Gap analysis: issues not captured by current Vecta criteria

The following curation observations do not map to an existing Vecta
criterion at v0.1:

| Observation | Sessions | Gap description | Proposed criterion |
|---|---|---|---|
| Non-standard gradient table size (30-dir, 12-dir, 24-dir GE) | 6 sessions | Vecta does not validate acquisition direction count against a protocol expectation | v0.2: VECTA-DWI-070 — DWI gradient count deviates from protocol reference |
| dcm2niix generates duplicate fmap series without IntendedFor | 13 sessions | Vecta detects IntendedFor absence but does not identify duplicate/phantom EPI fmaps | v0.2: VECTA-DWI-071 — EPI fmap has no IntendedFor and duplicates DWI geometry |
| Complementary-PE pair expressed only in sidecar, not in filename | sub-002 ses-3 | Vecta correctly detects the pair but has no criterion for acquisitions whose filename label is inconsistent with sidecar PE direction | v0.2: VECTA-DWI-072 — BIDS filename dir entity absent or inconsistent with sidecar PhaseEncodingDirection |
