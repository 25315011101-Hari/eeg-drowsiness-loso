# Multiplicity — my recommendation

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

Hari Singh Jatav · 25 September 2026 · for Dr. Mitul Kumar Ahirwal

---

## The situation in four lines

The paper reports **190 distinct inferential comparisons**. **82** reach p < 0.05 without
adjustment. No α is declared anywhere, and multiplicity is never mentioned. The 190 was
counted twice independently — by re-running every test family against the released fold
data, and by reconciling against the number registry — and the two agree exactly.

---

## What I recommend

**A. The universe: 190 comparisons.** Not a choice — this is what the pipeline runs, and it
is established from the code and the registry. The number of times a p-value is *printed*
(163) is not the same thing, because one comparison can be restated three times and five
comparisons can share the same floor value.

**B. Families: the twelve analysis families, with the prevalence family disclosed on its own
line.** The drowsy-count / prevalence family is 45 comparisons and supplies 32 of the 82.
Merging it with everything else makes the other results unreadable.

**C. Framing: exploratory.** Report nominal p-values transparently. Give Benjamini–Hochberg
**and** Benjamini–Yekutieli per family as *sensitivity analyses*. Do not make any correction
the primary decision rule, and stop using "significant" as the paper's load-bearing evidence.

---

## Why not simply correct and report what survives

Two measurements, from opposite directions, say the same thing.

**Holm cannot work at this sample size.** The smallest p a Wilcoxon signed-rank test on ten
subjects can return is 1/512. Holm's first threshold is α/m. At m = 26, α/26 = 1/520, which
is below the floor. So in any family of 26 or more such tests, Holm rejects nothing *for any
dataset that could have been collected*. It is not being conservative; it is not measuring.

**Benjamini–Yekutieli, over one family, keeps only the near-tautology.**

| Analysis set | Tests | nominal | BH | BY |
|---|---|---|---|---|
| All registered comparisons | 190 | 82 | 57 | **24** |
| Drowsy-count / prevalence family | 45 | 32 | 32 | 30 |
| Remaining comparisons | 145 | 50 | 22 | **0** |

All 24 of those BY survivors are from the prevalence family. Every architecture comparison,
arm contrast, calibration and threshold result falls. BY is the correct procedure when tests
are dependent — and ours are: shared subjects, shared folds, overlapping architecture pairs,
and four metrics computed from the same predictions.

So BH-as-primary is attackable on exactly one question — *"your tests are dependent; why not
BY?"* — and the honest answer would be that two headline claims disappear. Under exploratory
framing, that same question is just one more row in a sensitivity table. **This is the whole
argument for C.**

---

## The three questions you will ask, answered

**"Does exploratory framing weaken the paper?"** Less than it sounds, because most of this
paper's contributions are not p-value findings at all:

| Contribution | Depends on a p-value? |
|---|---|
| Three architectures above the class-prior Brier reference, two below, on all three arms | No — a descriptive partition |
| Between-subject spread exceeds between-seed spread, ×5.6 to ×47.8 | No — a ratio of standard deviations |
| Accuracy beats the always-alert baseline while missing half the events | No — read off the confusion matrix |
| The two most accurate architectures are the two with the lowest recall, on all three arms | No — an ordering; the ρ is only its quantitative form |
| Recalibration carries three architectures from above the reference to below it | Largely no — every value moves one way |
| EEGNet ranks first, winning on 11 of 12 pairs | Partly — the win counts stand on their own |
| **Balancing matters and trimming does not** | **Yes — 7 of 20 against 0 of 20** |
| **Threshold selection improves balanced accuracy and F1** | **Yes — and this family keeps 0 under both BH and BY** |

Two claims genuinely soften. Everything the paper is actually *about* is descriptive and
untouched.

**"Won't disclosing 190 tests invite the fishing objection?"** It is the opposite, if stated
carefully. Across the 190, 82 reached nominal p < 0.05 against 9.5 expected under a simple
global-null reference at α = 0.05 — and still 50 of 145 against 7.2 after removing the
prevalence family. Because the comparisons are dependent and were not generated under a
single global-null experiment, this is descriptive context for the disclosure and not a
formal test, and must be worded that way. Bounded like that, it is the difference between a
paper that counted and a paper that did not.

**"What does this change in the manuscript?"** One synchronized pass, not a find-and-replace
on "significant": Abstract, Highlights, Results §7.1–§7.9, Discussion, Conclusion, the table
captions, plus a generated multiplicity table. Two open findings come with it, because both
are entangled with how p-values are presented — the tied subject that lowers one
comparison's floor to 1/256, and the balanced-accuracy column missing from two contrast
tables (where the count "seven of twenty" turns out to be correct and the table incomplete).

---

## What I have not done

Nothing has been changed. No manuscript edit, no multiplicity table, no new tool, no change
to the checks. The numbers above came from a script run outside the repository. Baseline
unchanged: **40 tests pass, 20 of 20 pre-submission checks pass.**

I am not a statistician, and the framing decision is properly yours. But if the question is
which position is hardest for a reviewer to attack, I believe it is this one — and I have
measured it from both ends rather than argued it.

**Supporting documents:** `R1_TEST_INVENTORY.md` (every one of the 190, by family),
`R1_DECISION_NOTE.md` (the full argument), `REAUDIT_TRIAGE.md` (all 39 audit findings,
sorted), `REAUDIT_FINDINGS.md` (evidence for each).
