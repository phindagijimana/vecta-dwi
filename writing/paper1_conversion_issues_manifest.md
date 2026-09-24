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

### 2a. GE sessions excluded for non-standard protocol (direction count)

| Session | Vendor rule reason | Pre-intervention Vecta | Vecta criterion |
|---|---|---|---|
| sub-020 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-025 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-030 ses-1 | GE, dir_count=12, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-041 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-042 ses-1 | Siemens, dir_count=24, phase=ap | ready_with_limitations | VECTA-DWI-014 |
| sub-048 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |
| sub-055 ses-1 | GE, dir_count=30, phase=None | ready_with_limitations | VECTA-DWI-014 |

**Interpretation.** The curation reason for these exclusions was
**protocol selection** (direction count outside the site's expected
range, or absent BIDS direction entity), not a metadata-integrity
failure. Vecta does not encode protocol selection rules and does not
fire VECTA-DWI-021 for these sessions: all six GE DWI sidecars carry
a signed `PhaseEncodingDirection` field, so the essential metadata
criterion is satisfied. VECTA-DWI-014 fires for each session because
none has a reverse-PE EPI fieldmap — the expected downstream
consequence for GE acquisitions at this site, regardless of direction
count. The direction count itself is outside Vecta's current scope
(see Section 7).

Note: sub-042 ses-1 is a Siemens 24-direction acquisition with `dir-ap`
in the BIDS filename and a signed `PhaseEncodingDirection: j-` in the
sidecar. It was excluded for the same direction-count reason (24 ≠ 67
expected Siemens directions) and fires only VECTA-DWI-014 (no reverse
PE available). This distinguishes it from sub-069, which also has
24-direction Siemens DWI but lacks a signed PED (see Section 2b).

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
- sub-036: no `dir-AP` or `dir-PA` in filename → phase=None
- sub-069: has `dir-ap` label but was still excluded (24-direction Siemens
  table; 24 ≠ 67 expected)

The curation script operated on BIDS filename entities only and had no
access to sidecar JSON. Vecta and the curation script identified the same
two sessions for concern via entirely independent evidence paths.

**Ground truth note.** The immediate ground truth for sub-036 and sub-069
is **manual exclusion from the analysis cohort** — the exclusion itself
was the outcome. The absent signed `PhaseEncodingDirection` additionally
implies downstream preprocessing failure: SDC calibration (topup /
SyN-SDC) requires the signed phase-encoding direction; without it,
QSIPrep cannot compute a displacement field and will exit with a
`KeyError: PhaseEncodingDirection` at the susceptibility-correction step.
This failure mode has been confirmed in the TrackTBI cohort (participant
TBI011204; see TrackTBI-Sub/bids.md §8), where the identical unsigned-PED
condition caused QSIPrep to fail until the metadata was repaired.

**Siemens Skyra PhaseEncodingDirection inference by the CIDUR BIDS pipeline.**
All 16 Siemens Skyra sessions retained in the post-intervention cohort carry
both `PhaseEncodingDirection: j-` AND `PhaseEncodingAxis: j` in their DWI
sidecars. The raw dcm2niix output for Siemens Skyra populates only
`PhaseEncodingAxis` (unsigned axis). The CIDUR BIDS curation pipeline
inferred and added `PhaseEncodingDirection` to retained sessions based on
the BIDS filename `dir-<X>` entity: acquisitions labeled `dir-ap` received
`PhaseEncodingDirection: j-`. Sub-036 and sub-069 were moved to
`for_review/` before this inference step ran and therefore their sidecars
contain only the raw dcm2niix output — `PhaseEncodingAxis: j` only,
no signed direction.

This means the 16 retained Skyra sessions pass VECTA-DWI-021 because the
*curated* sidecar has the signed field; sub-036 and sub-069 fail because
the *uncurated* sidecar does not. Vecta's criterion correctly reflects
the actual state of each session's sidecar as presented to it.

`PhaseEncodingAxis` and `PhaseEncodingDirection` are distinct BIDS fields
with distinct semantics. Vecta reads only `PhaseEncodingDirection`
(signed, includes polarity). This is the correct design: `PhaseEncodingAxis`
specifies which image axis is the phase-encoding axis but does not specify
polarity (positive vs. negative); SDC calibration requires polarity, so
the axis field cannot substitute for the direction field.

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

## 7. BIDS Validator result on pre-intervention dataset

BIDS Validator v1.15.0 was run on the pre-intervention dataset (71
sessions, NIfTI excluded from reconstruction).

Issues reported:
| Code | Type | Description | Count |
|---|---|---|---|
| 90 SIDECAR_WITHOUT_DATAFILE | ERROR | JSON sidecar without a corresponding NIfTI data file | 1 |
| 38 INCONSISTENT_SUBJECTS | WARN | Subjects do not all contain the same files | 1 |
| 97 MISSING_SESSION | WARN | Not all subjects contain the same sessions | 2 |

**The SIDECAR_WITHOUT_DATAFILE error** is a direct artifact of the
pre-intervention reconstruction methodology: NIfTI files were
intentionally excluded (only sidecar JSON, bval, bvec restored) to
save disk space. The validator correctly identifies that some JSON
sidecars lack companion NIfTI images.

**No errors or warnings were issued for:**
- Absent `PhaseEncodingDirection` in sub-036 or sub-069 sidecars
- Unsigned `PhaseEncodingAxis` without a signed direction field
- Missing reverse-PE EPI fieldmaps (BIDS specification does not require them)
- Any DWI gradient file issue

This confirms that BIDS validation passes the two sessions with
unsigned-only PE metadata (sub-036, sub-069) without issuing any
structural error. The metadata deficit flagged by VECTA-DWI-021 is
invisible to BIDS Validator.

---

## 8. Gap analysis: issues not currently captured by Vecta criteria

The following curation observations either fall outside Vecta's DBI
scope or point to future criterion additions:

| Observation | Sessions | Status | Notes |
|---|---|---|---|
| Non-standard gradient table size (30-dir, 12-dir, 24-dir) | 7 sessions | Out of scope | Protocol selection decision, not a DBI issue; direction count is a curation preference, not a metadata-integrity failure |
| dcm2niix generates duplicate fmap series without IntendedFor | 13 sessions | Potential v0.2 criterion | VECTA-DWI-071: EPI fmap has no IntendedFor and duplicates DWI geometry |
| Complementary-PE pair expressed only in sidecar, not in filename | sub-002 ses-3 | Potential v0.2 criterion | VECTA-DWI-072: BIDS filename dir entity absent or inconsistent with sidecar PhaseEncodingDirection |

**Direction count is explicitly out of scope.** Vecta assesses Data Birth
Integrity — whether the metadata needed for downstream use is present,
traceable, and preserved. Direction count selection is a protocol design
decision that belongs in a protocol reference, not a DBI criterion.
A session with 12 gradient directions is not a DBI failure; it may be
a valid acquisition for a different analysis goal. Enforcing direction
count requires a protocol reference YAML (which Vecta can hold) and a
comparator criterion, but this is a separate design question to be
addressed if and when the framework is extended for protocol compliance
checking.

**PhaseEncodingAxis tracking is intentionally absent.** Vecta reads only
`PhaseEncodingDirection` (signed). `PhaseEncodingAxis` (unsigned) cannot
substitute because it does not encode polarity. There is no gap here —
treating an unsigned axis field as equivalent to a signed direction field
would introduce false negatives (reporting PED as present when only
polarity-unknown axis is available).
