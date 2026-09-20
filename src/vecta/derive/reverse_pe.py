"""Reverse-PE availability derivation for dwi_connectomics profile.

Follows the algorithm declared in specification/v0.1/variables/acquisition.yaml
for VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE (formula reverse_pe_availability_v1):

  1. Determine target PE direction.
  2. Identify candidate reference acquisitions in the same subject/session:
     (a) other DWI entities with the complementary PE, OR
     (b) fmap EPI entities whose IntendedFor list points at the target
         AND whose PhaseEncodingDirection is complementary.
  3. Return true if any qualifying complementary acquisition exists;
     false if inventory + PE metadata are sufficient to establish absence;
     unknown otherwise.

The fmap path (b) is required by the BIDS layout used in CIDUR and most
prospective studies: the reverse-PE reference typically lives under
`fmap/*_dir-<X>_epi.{json,nii.gz}` and links to the DWI via IntendedFor.

Complementary-PE rule for BIDS PE strings: 'j' complements 'j-', 'i'
complements 'i-', 'k' complements 'k-'. Empty polarity means the AXES
match but polarity is unknown — that is NOT a complement.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..collectors.bids import BidsSession, DwiEntity
from ..enums import Confidence, ValueState
from ..models import VariableResult


FORMULA_ID = "reverse_pe_availability_v1"
FORMULA_VERSION = "0.1.0"
EXTRACTOR_VERSION = "0.1.0"


def _now():
    return datetime.now(timezone.utc)


def _complement(pe: str) -> str | None:
    """Return the complementary PE string, or None if we can't derive one."""
    if not pe or pe[0] not in ("i", "j", "k"):
        return None
    axis = pe[0]
    if pe.endswith("-"):
        return axis           # e.g. 'j-' → 'j'
    return axis + "-"         # e.g. 'j' → 'j-'


def derive_reverse_pe_availability(
    session: BidsSession, target: DwiEntity
) -> VariableResult:
    """Emit VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE for a target DWI entity."""

    dependency_evidence = [
        ev.evidence_id
        for ev in session.evidence
        if ev.source_field == "PhaseEncodingDirection"
    ]

    target_pe = target.sidecar.get("PhaseEncodingDirection")
    if target_pe is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            confidence=Confidence.HIGH,
            evidence_refs=dependency_evidence,
            extractor_id=FORMULA_ID,
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )

    wanted = _complement(target_pe)
    if wanted is None:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE",
            definition_version="0.1.0",
            value=None,
            state=ValueState.UNKNOWN,
            confidence=Confidence.HIGH,
            evidence_refs=dependency_evidence,
            extractor_id=FORMULA_ID,
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )

    # Search other DWI entities in the same session
    complementary_found = False
    inventory_complete = True
    for other in session.dwi_entities:
        if other is target:
            continue
        other_pe = other.sidecar.get("PhaseEncodingDirection")
        if other_pe is None:
            inventory_complete = False
            continue
        if other_pe == wanted:
            complementary_found = True
            break

    # Also search fmap EPI entities (reverse-PE via IntendedFor)
    if not complementary_found:
        target_name = target.json_path.stem  # e.g. sub-001_ses-1_acq-64dirax_dir-ap_dwi
        for fmap in session.fmap_epi_entities:
            fmap_pe = fmap.sidecar.get("PhaseEncodingDirection")
            if fmap_pe is None:
                inventory_complete = False
                continue
            if fmap_pe != wanted:
                continue
            # Check IntendedFor: BIDS-relative path segments must contain
            # the DWI target's stem. We match by containment rather than
            # exact equality because IntendedFor may or may not carry the
            # ses-* prefix depending on generator.
            targeted = any(target_name in entry for entry in fmap.intended_for)
            if targeted or not fmap.intended_for:
                # No IntendedFor list at all → assume applies to all DWI in session
                # (conservative but standard BIDS-Legacy behavior).
                complementary_found = True
                break

    if complementary_found:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE",
            definition_version="0.1.0",
            value=True,
            state=ValueState.OBSERVED,
            confidence=Confidence.HIGH,
            evidence_refs=dependency_evidence,
            extractor_id=FORMULA_ID,
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    if inventory_complete:
        return VariableResult(
            variable_id="VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE",
            definition_version="0.1.0",
            value=False,
            state=ValueState.OBSERVED,
            confidence=Confidence.HIGH,
            evidence_refs=dependency_evidence,
            extractor_id=FORMULA_ID,
            extractor_version=EXTRACTOR_VERSION,
            computed_at=_now(),
        )
    return VariableResult(
        variable_id="VECTA.DWI.ACQ.REVERSE_PE_AVAILABLE",
        definition_version="0.1.0",
        value=None,
        state=ValueState.UNKNOWN,
        confidence=Confidence.HIGH,
        evidence_refs=dependency_evidence,
        extractor_id=FORMULA_ID,
        extractor_version=EXTRACTOR_VERSION,
        computed_at=_now(),
    )
