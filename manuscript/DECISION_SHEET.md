# What is settled here, and what is still open

*Not part of the manuscript. 25 September 2026.*

Everything else in this paper is checked by a command. What is on this page cannot
be, because these are not facts about the data — they are statements two people have
to be willing to sign. This page exists so that settling them is one sitting with the
guide rather than several separate remembering-to-do-its.

The count that used to open this page is gone, on 7 October 2026. It stood in three
places — the title, the paragraph above and the closing line — and all three
disagreed, which is the failure the closing section of this page warns against.

Check where they stand at any time:

```
python3 tools/check_submission_ready.py
```

Each decision is confirmed by **deleting the draft note that says it is not**. No
second file to keep in step, and nothing can be marked done by accident.

---

## 1. 🟢 Repository — published 5 October 2026

A public repository is **recommended for reproducibility**; whether it is mandatory
for this journal must be confirmed from the journal's current submission
requirements, and that has not been done. This heading read "blocks submission"
until 4 October 2026, which stated as settled something nobody had checked; the
correction is recorded here rather than made silently.

The data-availability statement promises a reader can fetch files that reproduce
every table in the paper. Until 5 October 2026 that promise pointed at a placeholder
address; it now points at a published repository, and the three checks below were run
against a fresh clone of it rather than against this working copy.

**Published at https://github.com/25315011101-Hari/eeg-drowsiness-loso on
5 October 2026**, nine commits and 149 files, into a public repository of that exact
name that already existed and was empty — checked with `git ls-remote` before
anything was written. `tools/set_repository_url.py` filled the address into
`CODE_AVAILABILITY.md` twice, the assembled manuscript and `CITATION.cff`: four of
the five files it checks, the fifth being `MASTER_FILE.md`, which is on the list so a
stale copy is not left behind and holds none because its generator never writes the
placeholder.

**Checked from a fresh clone on 5 October 2026** — no script can do this from inside
the package it is checking, so it was done from a clone taken with no credentials, the
way a reader would:

- [x] the repository clones publicly, with no sign-in — nine commits, 149 files
- [x] `results/ALL_FOLDS.csv` there has 750 rows: 250 per arm, five models, five
      seeds, ten subjects
- [x] `python3 tools/preflight.py` passes there — ALL CHECKS PASS, 25 of 25.
      `training smoke` reports PENDING because that clone has no TensorFlow, which is
      the documented expected state

The licence was confirmed in the same step: MIT, with the draft note deleted from
`LICENSE` and the "authors must confirm" sentence from `README.md`.

**Optional but preferred:** archive a GitHub release on Zenodo for a DOI, and pass
`--doi 10.5281/zenodo.<id>`. A DOI survives a repository being renamed, made
private or deleted; a GitHub address does not.

---

## 2. 🟢 CRediT roles — confirmed 1 October 2026

The corresponding author confirmed the CRediT roles on 1 October 2026; the former
CREDIT-DRAFT marker is no longer present in `ABSTRACT.md`. The statement as submitted,
and the four roles considered and declined with the reason for each, are in
`manuscript/ABSTRACT.md`. The proposal below is kept as the record of what was
proposed, not as something still to settle.

The journal requires each author's contribution in CRediT terms. The draft below
is a **proposal based on how the work was divided** — it is not evidence of
anything. Strike any role that was not performed; add any that was.

**The rule that matters: a role nobody performed is not a courtesy, it is a false
statement of authorship.** This is easier to get wrong generously than meanly.

| Role | What it means | Hari Singh Jatav | Mitul Kumar Ahirwal |
|---|---|---|---|
| Conceptualization | Formulating the research question and aims | proposed | proposed |
| Methodology | Designing the protocol — the three constructions, LOSO, the calibration analysis | proposed | proposed |
| Software | Writing the code that produced the results | proposed | — |
| Validation | Checking that results are reproducible and correct | — | proposed |
| Formal analysis | The statistics: the paired tests, the rank correlations, the Brier partition | proposed | — |
| Investigation | Running the experiments; the 750 folds | proposed | — |
| Data curation | Obtaining and preparing the recordings; the window constructions | proposed | — |
| Writing – original draft | Writing the first version of the manuscript | proposed | — |
| Writing – review & editing | Critical revision of the text | — | proposed |
| Visualization | Making the figures | proposed | — |
| Supervision | Oversight and guidance of the work | — | proposed |
| Resources | Providing lab facilities, computing, materials | not claimed | **decide** |
| Funding acquisition | Obtaining financial support | — | — |
| Project administration | Coordinating and managing the work | not claimed | **decide** |

Two to settle explicitly, because the acknowledgement says the BCI Laboratory
conducted and supported the work:

- **Resources** — if the lab provided the computing or facilities through the
  supervisor, this role is his and is currently missing from the proposal.
- **Project administration** — claim it only if someone actually coordinated the
  work as a managed project, not merely supervised it. Supervision already covers
  guidance.

**Funding acquisition is left empty deliberately.** No funding was received, so
nobody acquired any. It is not an oversight.

**Confirmed.** The two role lists in `manuscript/ABSTRACT.md` were edited to match
what was actually done and the `<!-- CREDIT-DRAFT: ... -->` line beneath them was
removed. `ABSTRACT.md` carries the date and the person: "Confirmed by the corresponding
author on 1 October 2026." Nothing above is an instruction any more; it is the record of
what was proposed before that decision.

---

## 3. 🟢 Licence — MIT, confirmed 5 October 2026

Both authors confirmed MIT on 5 October 2026; the "NOTE TO THE AUTHORS BEFORE
PUBLISHING" block is no longer present in `LICENSE`, and `README.md` no longer says
the authors must confirm before publishing. The two institutional questions below are
kept because they are worth asking again if the institute's position changes, not
because the licence is unsettled.

`LICENSE` proposed **MIT**, with a note at its foot saying the choice was
not the draft's to make.

MIT was proposed because it is the least restrictive common choice for research
code and places no obligation on a reviewer who clones the repository. That is a
reason, not a decision. Two things to check with the institute:

- **Does MANIT have a policy on releasing code produced at the institute?** Some
  institutes require a specific licence or a copyright line naming the institute
  rather than the authors. The copyright line in `LICENSE` names both authors and
  the Centre for AI; it may need to name the institute instead.
- **Is a more restrictive licence wanted?** Apache-2.0 adds an explicit patent
  grant; GPL-3.0 requires derivative works to stay open. Neither is more correct
  than MIT — they encode different intentions.

Two things the licence does **not** cover, and should not be changed to cover:

- the DD-Database recordings, which are not distributed here and are CC0 1.0 at
  their Dryad record;
- the ARL model implementations, which are cloned from their own repository under
  their own licence.

**Confirmed.** The "NOTE TO THE AUTHORS BEFORE PUBLISHING" block was removed from the
foot of `LICENSE` after the choice was settled. `README.md` carries the date and the
people: "confirmed by both authors on 5 October 2026."

**If the licence is ever changed**, the two questions above are the ones to ask again,
and the change is not to `LICENSE` alone: `README.md` and `CITATION.cff` name the
licence too and must be changed with it — `check_submission_ready.py` fails if `LICENSE`
and `README.md` disagree.

---

## 4. 🟢 The training smoke test — passed 1 October 2026, against the recorded source versions

It was run in an environment with TensorFlow on 1 October 2026 and passed.
`results/smoke_test_passed.txt` records that pass together with the modification times
of the three files it was checked against — `src/train_loso.py`, `src/models.py` and
`config.py` — and all three still predate the record, so
`tools/check_submission_ready.py` reports the item confirmed rather than open. If any
of the three is changed, it goes back to open and the test is run again.

**What that evidence is, stated exactly.** The recorded smoke test covers the source
versions recorded with it; the three files predate the record. A modification time is
weaker than a content hash, and git cannot strengthen it here: this directory became a
git repository on 4 October 2026, three days after the test ran, so the history begins
after the evidence and cannot speak to what happened between 1 and 4 October. Running
the test again in an environment with TensorFlow would settle it outright, and is the
cheaper of the two ways to remove the doubt.

The rest of this section says why it is the test that matters.

Not a decision — a verification the automated gate cannot perform for itself.

`tests/test_training_smoke.py` is the only test that builds real models and checks
the properties the paper leans on hardest: that a held-out subject never reaches its
own fold's training or validation split, that every architecture builds at the
parameter count reported, and that a resumed run does not shift the validation draw.
It needs TensorFlow and the ARL reference implementation, so in an environment
without them it skips — visibly, but a visible skip is still a skip.

**Before submission, run it once in an environment that has them:**

```
python3 tests/test_training_smoke.py
```

A pass writes `results/smoke_test_passed.txt` recording when it ran and the
modification times of `src/train_loso.py`, `src/models.py` and `config.py`.
`tools/check_submission_ready.py` reads that record and reports this item PENDING
again if any of those three has changed since — because a pass recorded before the
last change to the training loop is no evidence about the code being submitted.

---

## 5. 🟠 Supplementary structure — do Tables S5, S2 and S4 belong under Note 3?

Not a journal requirement and not an error: a question about how the supplementary
document reads. Measured 7 October 2026 against build 3c5cb5bf85fd.

`manuscript/SUPPLEMENTARY.md` carries one first-level heading, the document title,
and four second-level headings: Supplementary Figure S1, and Supplementary Notes 1, 2
and 3. Table S1 sits under Note 1, whose subject it is. Note 3 opens *"Stated once, so
that no section has to be read as covering more than it does. **Table S3** gives
it."* — it names one table. Tables S5 (multiplicity), S2 (pooled confusion matrices)
and S4 (calibration error and Brier) then follow Note 3 without second-level headings
of their own, separated only by rules, although they concern different analyses.

So a reader who opens Note 3 expecting coverage reaches confusion matrices without
passing another heading. That raises a structural question about whether those three
should be grouped under separate notes. It is a question, not a demonstrated error:
nothing in the guide or in this repository establishes that they are misplaced.

This is also where the current ordering becomes visible. The tables appear as S1, S3,
S5, S2, S4 down the page, and the article cites them in a third order again — S1,
Figure S1, S2, S4, S5, S3. **The reason for that ordering has not been established:**
`tools/split_map.json` records which material moved and what the article retains in
its place, but it gives no reason for the numbers, and the phrases "citation order"
and "order of appearance" do not occur in it. The grouping question is therefore
settled first, because a renumbering decided before it would be decided without
knowing what the sections are.

**To settle, in this order:**

- [ ] decide whether S5, S2 and S4 each get a Supplementary Note of their own
- [ ] read the guide at the source on supplementary table numbering — what is known
      and what is not is in `tools/journal_requirements.json`,
      `not_enforced_here.supplementary_material.silent_on`
- [ ] only then, the numbering

Nothing is changed until the first two are answered. Both orders are recorded above
so that neither has to be measured again.

## What is not on this page

Everything else the paper says about itself is checked by
`python3 tools/preflight.py`, which runs every check `REPRODUCIBILITY.md` §4 lists
and prints one verdict. The count is not repeated here: it has changed four times,
and a number restated in two places is a number that will disagree with itself.

The paper is internally finished. The settled author decisions and the
training-smoke-test record above are no longer open; what remains is the supplementary
question in section 5, and it is a question, not a defect.
