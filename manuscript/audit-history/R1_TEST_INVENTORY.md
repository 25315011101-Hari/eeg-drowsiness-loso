# R1 — inventory of every inferential test

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

Enumeration first. **No counting rule is adopted in this file.** What follows is what
the code actually runs, measured by running it, so that a rule can be chosen against
the real inventory instead of the inventory being shaped to fit a rule.

Method: `src/stats.py`, `src/calibrate.py` and `src/thresholds.py` were read for every
call to `wilcoxon`, `spearman` or `spearmanr`; each call site's enclosing loop was
resolved to its instance count; then every family was **executed** against
`results/ALL_FOLDS.csv` and `results/ALL_POOLED.csv` and the p-values counted. The
released `calibration_summary.csv` and `threshold_summary.csv` supplied the fold-level
families. The result was then reconciled against `results/MASTER_NUMBERS.csv`
independently, and the two agree exactly.

---

## The three quantities

| | Quantity | Value |
|---|---|---|
| **1** | Unique inferential comparisons actually performed | **190** |
| | of which nominally significant at 0.05 | **82** |
| **2** | Unique comparisons whose own p is recorded in the registry | **190** |
| | registry rows carrying a p, before de-duplication | 193 + 12 note-only = 205 |
| **3** | All printed `p =` occurrences in the eleven section files | **163** |
| | distinct printed values among them | **54** |

**Why the earlier counts differed, exactly.**

* **181** was the count of registry rows whose claim is a p (189) minus the eight
  summary and floor rows. It is short by the 12 cross-arm ordering tests, whose p is
  recorded in a row's *note* rather than as a row of its own, and it does not subtract
  the 3 duplicated instances. 181 − 0 + 12 − 3 = 190.
* **117 / 162** were printed occurrences, not tests. Measured here as 119 in
  `RESULTS.md` and 163 across the eleven section files. A printed occurrence is not a
  test: `p = 0.0020` is printed 18 times and is the Wilcoxon floor shared by five
  different comparisons; `p = 0.0488` is printed 12 times for one.
* **190** is the only one of these numbers that counts comparisons.

---

## The inventory

`N` is instances performed. `nom.` is how many reach p < 0.05 without adjustment.
`Holm` and `BH` are what would survive *within that family alone* at 0.05 — shown as
information, not as a recommendation. `Reported` says how the manuscript presents the
family.

| Family | Comparison | Scope | N | nom. | Holm | BH | Reported | Repeated elsewhere? |
|---|---|---|---|---|---|---|---|---|
| Wilcoxon, n=10 subjects | EEGNet against each other architecture, ROC-AUC | 4 pairs × 3 arms | 12 | 11 | 8 | 10 | each p in Table 4 | same 12 restated in §7.9 and Discussion |
| Wilcoxon, n=10 | the other six architecture pairs, ROC-AUC | 6 pairs × 3 arms | 18 | 0 | 0 | 0 | **as a count only** — "none of the ten" | no |
| Wilcoxon, n=10 | CNN against CNN-BiLSTM, ROC-AUC | 1 pair × 3 arms | (3) | 0 | — | — | in the ablation table | **duplicate** — already one of the 30 pairs above; registered twice under two claim strings |
| Wilcoxon, n=10 | CNN against CNN-BiLSTM, PR-AUC / bal.acc / F1 | 3 metrics × 3 arms | 9 | 8 | — | — | each p in the ablation table | §7.2, §7.9 and §8.2 |
| Wilcoxon, n=10 | arm A against arm C — balancing isolated | 5 arch × 4 metrics | 20 | 7 | 1 | 4 | count "7 of 20" + a table | §7.1.1, §7.9, Highlights |
| Wilcoxon, n=10 | arm B against arm C — trimming isolated | 5 arch × 4 metrics | 20 | 0 | 0 | 0 | count "0 of 20" + a table of 15 | §7.1.2, §7.9 |
| Wilcoxon, fold-level | Platt against raw — Brier and ECE | 3 arms × 3 arch × 2 metrics | 18 | 13 | 3 | 5 | each p, §7.6 | §8.5 |
| Wilcoxon, fold-level | selected threshold against fixed 0.5 — bal.acc and F1 | arms A and C only, 3 arch × 2 rules × 2 metrics | 24 | 7 | 0 | 0 | each p, §7.8 | §8.6 |
| Spearman n=5 exact | parameter count against ROC-AUC | 3 arms | 3 | 0 | 0 | 0 | each p | withdrawn claim, §7.9 |
| Spearman n=5 exact | do two arms order the architectures alike | 3 arm pairs × 4 metrics | 12 | 3 | 0 | 0 | ρ printed, p in 8 cases | §7.4 |
| Spearman n=5 exact | ROC-AUC against pooled Brier | 3 arms × 2 conventions | 6 | 0 | 0 | 0 | each p | reported to forestall the question |
| Spearman n=5 exact | **accuracy against pooled recall** | 3 arms | 3 | 1 | 1 | 1 | each p | Abstract, §7.3, §8.3, Conclusion, Highlights |
| Spearman n=10, t-approx | drowsy-window count against PR-AUC, three forms | 3 arms × 5 arch × 3 forms | 45 | 32 | 25 | 32 | **as counts** — "fourteen of the fifteen", "none of the five" | §7.5.2, §8.7 |
| | **Unique comparisons performed** | | **190** | **82** | | | | |
| | sum over families, counting the 3 duplicates | | 193 | 82 | 43 | 60 | | |
| | if all 193 were treated as one family | | 193 | 82 | **11** | 57 | | |

**Current adjustment, every row: none.** No α is declared as a study-wide criterion.
The one α in the manuscript, `EXPERIMENTAL_SETUP.md:104`, governs the comparison of the
exact Spearman test against its t-approximation, not multiplicity. The words
"multiplicity", "multiple testing", "family-wise", "Bonferroni", "Holm" and "FDR"
appear zero times in the manuscript.

---

## Three things the enumeration turned up that were not visible before

**1. The accuracy-against-recall claim survives Holm on an exact tie.** This is the
paper's headline inferential result — it appears in the Abstract, Highlights, §7.3, §8.3
and the Conclusion. Arm A's exact permutation p is 2/5! and Holm's first threshold over
three tests is 0.05/3. These are the same number:

```
Spearman exact floor on 5 points, 2/5! = 0.01666666666666667
Holm first threshold, alpha/3          = 0.01666666666666667
equal exactly?                          True
difference                              = 0.000e+00
```

So it survives if the comparison is `≤` and fails if it is `<`. Nothing about the data
decides it. This is not an argument for or against correcting — it is a fact that has to
be known before the R1 decision is made, because "the headline result survives Holm"
would be true and misleading.

**2. Where the family is drawn changes the answer by a factor of four.** 82 nominal
becomes 43 under within-family Holm and 11 under one-family Holm. The two thresholds
`Holm` and `BH` disagree sharply on precisely the two families the paper's design
argument rests on: the A-vs-C balancing contrast goes 7 → 1 under Holm and 7 → 4 under
BH. Whichever is chosen has to be chosen on a stated principle, because the numbers do
not agree.

**3. The threshold-selection family is the one that disappears completely.** 7 of 24
nominal, 0 under Holm, 0 under BH — and its 24 tests are the largest single family
reported with individual p-values. The calibration family goes 13 → 3. Both are
presented in §7.6 and §7.8 as findings rather than as diagnostics.

---

## Observations relevant to a counting rule — not yet a rule

These come out of the enumeration rather than being imposed on it:

* **The 3 duplicates are real duplicates.** `all_pairwise` registers
  `Arm A CNN vs CNN-BiLSTM ROC-AUC p` and `ablation` registers
  `Arm A CNN vs CNN-BiLSTM auc p`. Same subjects, same metric, same test, two claim
  strings. Two rows, one comparison. The de-duplication guard in preflight
  (`duplicate keys`) cannot see this, because it compares claim strings.
* **A restatement is not a test.** The 12 Table 4 comparisons appear again in §7.9 and
  the Discussion. Counting printed occurrences counts them three times; that is the
  whole of the 163-against-190 gap.
* **Three forms of one question is three tests, not one.** `subject_count_correlation`
  deliberately reports raw, prevalence-corrected and ratio forms because they disagree
  in sign. They are three different hypotheses about the same variable, and the paper
  is explicit that reporting one would be selective. They cannot be collapsed to 15.
* **Two estimator conventions of one question may be one test or two.**
  `ranking_vs_reliability` runs pooled and subject-averaged ROC-AUC against the same
  Brier values. Neither is significant, so nothing turns on it here — but the rule has
  to say which it is, because the same pattern would matter if one were significant.
* **Descriptive quantities are not in any of these counts** — means, SDs, confusion
  matrices, accuracy, recall, precision, the spread ratios, the Brier partition, ECE
  values and the reproducibility differences carry no p and were never counted.
* **One family is on the wrong code path.** The 45 drowsy-count correlations run on ten
  subjects through `scipy.stats.spearmanr` directly, not through `stats.spearman`, so
  they use the t-approximation while every n=5 family uses the exact permutation test.
  At n=10 the two agree closely, so no reported value is wrong — this is finding R12,
  and it is noted here because it is the largest family in the inventory and the one
  that contributes 32 of the 82 nominal significances.

---

## The denominator, stated three ways

Any multiplicity statement has to name which of these it means:

| Candidate denominator | Value | What it counts |
|---|---|---|
| Comparisons performed | **190** | every distinct inferential comparison the code runs |
| Comparisons whose p is printed in a table | **93** | measured, see below |
| Comparisons with an individually printed p | **93 to 116** | 93 in tables, plus part of the 23 prose occurrences |
| Printed `p =` occurrences | **163** | not a count of tests; includes restatements and shared floor values |

The 93 is measured by counting `p =` inside each table of `RESULTS.md`:

| Table | p-values printed | of a family of |
|---|---|---|
| Table 4, EEGNet pairs | 12 | 12 |
| A → C contrast | 15 | **20** |
| B → C contrast | 15 | **20** |
| ablation, CNN → BiLSTM | 12 | 12 (3 of them duplicates) |
| recalibration, Brier and ECE | 18 | 18 |
| threshold selection, two tables | 12 + 12 | 24 |
| **total in tables** | **96 occurrences, 93 unique comparisons** | |

A further 23 `p =` occurrences sit in the prose of `RESULTS.md`, and these mix three
different things: comparisons reported nowhere else (the 3 capacity correlations, the 3
accuracy-against-recall correlations), restatements of values already in a table, and
two individual drowsy-count p-values quoted as exceptions. So the number of comparisons
with an individually printed p is at least 93 and at most 116.

**That leaves at least 74 of the 190 reported only as a count or a bound** — the 18
non-EEGNet pairs as "none of the ten", and 43 of the 45 drowsy-count correlations as
"ρ ≥ +0.79 with p ≤ 0.0061 on fourteen of the fifteen" and "significance for none of
the five". They were still run, and an honest multiplicity statement is about 190, not
about what a reader can see.

**One thing the measurement exposed.** The A → C and B → C tables each print three
metrics — ROC-AUC, PR-AUC and F1 — so 15 of each family's 20 tests are shown. The
balanced-accuracy column is absent from both. But the headline counts drawn from those
families, "seven of twenty" and "zero of twenty", are over all four metrics. A reader
cannot see 10 of the 40 arm-contrast tests that those two counts are computed from.

Checked: the omission is stated nowhere. §7.1.1 and §7.1.2 introduce the tables as
being "on the ten subject-level differences" and the summary table counts "twenty
tests", and the word "balanced" does not appear between lines 225 and 290 of
`RESULTS.md` except in the section headings. A reader who counts the cells gets fifteen
and is told twenty, with nothing to explain the difference. Recorded separately as
**R39**, since it is a reporting defect rather than a multiplicity question.

**Nothing above has been written into the manuscript.** The next step is to choose the
denominator and the correction policy, or to state explicitly that the p-values are
descriptive — and the tie in observation 1 means that choice cannot be deferred to a
footnote.
