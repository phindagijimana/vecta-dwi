# Authorship

## Current author list

**First author:** Philbert Ndagijimana (corresponding author)
— Conceptualization, Methodology, Software, Formal Analysis, Investigation,
Data Curation, Writing – Original Draft, Visualization

**[Co-author(s)]:** TBD — see below for candidates

**Last author / PI:** James J Gugger
— Conceptualization, Supervision, Writing – Review & Editing,
Funding Acquisition, Resources

---

## What is blocking submission

Four items in `journal_sections.md` require PI input and cannot be resolved
without an author conversation:

| Item | Where it appears | Who resolves it |
|---|---|---|
| IRB protocol number | Ethics Statement | PI |
| CRediT contributions | CRediT Author Statement | All co-authors |
| Funding grant numbers | Funding section | PI |
| Acknowledgments | Acknowledgments section | PI |
| TrackTBI full-cohort citation | methods.md [TODO] | PI (knows which paper covers the full 649-subject FITBIR cohort; candidate: Nelson et al. 2019 JAMA Neurology, PMID 31157856) |

---

## How to find co-authors

### 1. PI (required, last author)

The PI must be a co-author. Without them:
- The IRB protocol number cannot be confirmed
- The FITBIR/TrackTBI data use agreement is tied to a named PI investigator
- The funding statement has no grant numbers

Action: schedule a meeting with your direct supervisor to walk through the
manuscript and confirm their co-authorship and the four items above.

### 2. Data contributors (ICMJE criteria)

Under ICMJE, a co-author must satisfy all three:
1. Substantial contribution to conception/design OR data acquisition/analysis
2. Drafted or critically revised the manuscript
3. Approved the final version

People who only collected scans or ran conversions do not qualify — they go
in Acknowledgments, not the author list.

Candidates to evaluate:
- Whoever performed or supervised the original CIDUR BIDS conversion
  (the 62-session dataset used for development — if they materially shaped
  the data that drove criterion development, they may qualify)
- Anyone listed as co-investigator on the FITBIR data use agreement

### 3. FITBIR data use agreement

Check the DUA for the TrackTBI data access — it may name specific
investigators. Those investigators may need to be co-authors or may need
to provide written permission confirming the analysis is covered under
the agreement.

---

## Author order convention (neuroimaging)

- First: primary contributor (you)
- Middle: data contributors, roughly by contribution magnitude
- Last: PI/senior author

---

## Acknowledgments candidates

People who contributed but do not meet ICMJE co-authorship criteria:
- Scanner operators and MRI technologists (CIDUR data collection)
- BIDS conversion staff (if not qualifying as co-authors)
- Anyone who facilitated TrackTBI access but is not on the DUA as PI
- Compute infrastructure (URMC HPC/computing resources, if applicable)
