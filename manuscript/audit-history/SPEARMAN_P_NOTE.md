# Which Spearman p-value the paper reports

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

*Raised 19 September 2026 as an open question. **Settled 23 September 2026: the
paper now reports the exact permutation p** (option 1 below), on the supervisor's
instruction to implement it first and review it after. This note is the record of
what was asked, what was found, and what was changed.*

> **For review.** The whole change is nine registered numbers and the sentences
> that quote them. Reproduce the evidence with
> `python3 tools/check_spearman_p.py --quiet-n10`, and see
> **What was changed** at the foot of this note for the file-by-file list.

---

## The question in one paragraph

The paper reports rank correlations across the **five architectures**. A p-value
for such a correlation can be computed two ways, and on five points they do not
agree. Section 6.5 stated one convention; the registry recorded p-values from the
other. On two claims the two conventions disagreed about significance at
α = 0.05. Neither number is arithmetically wrong — they answer different
questions — so which one the paper reports was an editorial decision rather than a
bug to be fixed.

## The two conventions

| | How it is obtained | On five points |
|---|---|---|
| **Exact** | Enumerate all 5! = 120 orderings of the ranks; count how many reach a correlation at least as extreme as the observed one. No distributional assumption. | Smallest two-sided p obtainable is **2/120 = 0.0167**. Nothing below it exists. |
| **t-approximation** | *t* = ρ√((n−2)/(1−ρ²)) against Student's *t* on n−2 = 3 degrees of freedom. This is what `scipy.stats.spearmanr` returns, so it is what `src/stats.py` records. | Asymptotic. Returns values *below* the exact floor, and exactly 0 when \|ρ\| = 1 — a division by zero, not a p-value. |

**Section 6.5 already committed to the exact convention**, in these words (this
was its wording before the change):

> "Relationships across architectures use Spearman rank correlation over the five
> architectures. With five observations the smallest attainable p-value is
> approximately 0.017…"

That 0.017 *is* 2/120. `src/registry.py` also applied it, but to one claim only —
the accuracy-against-recall correlation was capped at the floor, with the cap
recorded in the registry note. No other five-point correlation was capped.

**So the registry held p-values from both conventions.** That is what was fixed.

## What the audit found

Every rank correlation in the registry, separated by the sample it was computed
over. The separation matters: the drowsy-count correlations are worded like the
others but run over the **ten subjects**, where the approximation is sound.

| Family | n | Claims | Verdicts that change at α = 0.05 |
|---|---|---|---|
| Accuracy vs recall; parameters vs ROC-AUC; ROC-AUC vs Brier | 5 | 12 | **2** |
| Drowsy count vs PR-AUC | 10 | 45 | **0** |

The two:

| Claim | ρ | Recorded p | Exact p |
|---|---|---|---|
| **Arm B, pooled accuracy vs pooled recall** | −0.900 | 0.0374 — significant | **0.0833 — not** |
| Arm A, parameters vs ROC-AUC | −0.900 | 0.0374 — significant | **0.0833 — not** |

The ρ values themselves were recomputed independently and all three match the
registry exactly: −1.000, −0.900, −0.600.

## What each one would cost

**The second claim costs nothing.** Section 7.2 has already withdrawn it —
*"The capacity correlation is withdrawn… No claim is made that ranking quality is
a function of parameter count."* The exact test agrees with a decision the paper
had already taken on other grounds.

**The first claim is the live one.** Three places say that two of the three
constructions reach significance: the Figure 2 caption, Research Gap §3.2, and
Results §7.3. Under the exact convention only Arm A does.

**It does not weaken the paper's argument.** The claim the paper makes is about
*direction* — accuracy runs against recall — and that holds on all three
constructions either way. Research Gap §3.2 already says so in as many words:
*"The direction is therefore consistent on all three constructions and its
strength is not."* Moving Arm B from significant to not significant makes the
paper more conservative, and removes a mismatch between Section 6.5 and the
numbers it governs that a statistically attentive reviewer is likely to notice.

## The three ways to answer, as they were put to the supervisor

**Option 1 was chosen.**

1. **Report the exact p throughout** (A 0.0167, B 0.0833, C 0.3500). Consistent
   with Section 6.5 as already written; the most conservative. Changes the
   registry, Figure 2, and about six sentences. `P_FLOOR_SPEARMAN_5` would also be
   computed as 2/5! rather than typed as `0.0167`.
2. **Keep the t-approximation and document it.** No number changes. Section 6.5
   gains a sentence saying Spearman p-values use the t-approximation, that 0.017
   is the exact bound, and that the Arm A value is reported at that bound. The
   paper then carries both conventions knowingly rather than accidentally.
3. **Report both.** Exact in the text and in Figure 2, t-approximation in a
   supplementary table with the reason they differ. The most transparent; the
   most words.

## Two smaller points, both now done

- `config.P_FLOOR_WILCOXON_10` was computed in code (`2.0 / 2 ** 10`) while
  `config.P_FLOOR_SPEARMAN_5` was the typed literal `0.0167`; the value is
  0.016666… **Both are now computed.**
- The registry carries two rows named "smallest attainable … p" next to one
  another, and neither claim names the test it belongs to. This is what caused
  the Wilcoxon floor (0.001953125, over ten subjects) to be read as the Spearman
  floor (0.0167, over five architectures) during review. **Both constants in
  `config.py` now name their test in a comment.** Renaming the registry *claims*
  themselves would prevent a repeat more firmly, but claim names are lookup keys,
  so that rename is still outstanding and must be made with the scanner run
  afterwards.


---

## What was changed, 23 September 2026

Option 1. Every rank correlation across the five architectures now carries the
exact two-sided permutation p; the correlations over the ten subjects keep the
*t*-approximation, and Section 6.5 now says so and says why.

**Code**

| File | Change |
|---|---|
| `src/stats.py` | new `spearman(x, y)` returning `(rho, p, exact)`. Enumerates the n! orderings when n ≤ 8 and falls back to the approximation above that, reporting which route was taken. The four five-point call sites now use it: `accuracy_vs_recall`, `capacity_correlation`, `ranking_vs_reliability`, `cross_arm_ordering`. |
| `config.py` | `P_FLOOR_SPEARMAN_5` is now computed as 2/5! rather than typed as `0.0167`, and both floors say which test they govern. |
| `src/registry.py` | the floor-cap on the accuracy-against-recall claim is gone. An exact p cannot fall below the floor, so there is nothing to cap. |
| `tests/test_pipeline.py` | `test_five_point_correlations_use_the_exact_permutation_p` — asserts the exact route is taken, agrees with an independent enumeration, and that no registered five-point p lies below the floor. |
| `tools/check_spearman_p.py` | now the regression test for this, not an audit of it. `--strict` exits non-zero on any disagreement. |

**The nine registered values**

| Claim | Was | Now |
|---|---|---|
| Arm B accuracy vs recall | 0.0374 | **0.0833** |
| Arm C accuracy vs recall | 0.2848 | 0.3500 |
| Arm A parameters vs ROC-AUC | 0.0374 | **0.0833** |
| Arm B parameters vs ROC-AUC | 0.391 | 0.4500 |
| Arm C parameters vs ROC-AUC | 0.8729 | 0.9500 |
| Arm A ROC-AUC (pooled) vs Brier | 0.1041 | 0.1333 |
| Arm B ROC-AUC (pooled) vs Brier | 0.1041 | 0.1333 |
| Arm C ROC-AUC (pooled) vs Brier | 0.8729 | 0.9500 |
| Arm A ROC-AUC (subject-averaged) vs Brier | 0.1041 | 0.1333 |

Arm A's accuracy-against-recall p was already 0.0167 and did not move: it was the
one claim the old code capped at the floor. **Bold** marks the two whose verdict
at α = 0.05 changed. No ρ changed, no other number in the paper changed, and the
registry gained no rows from this change — it held 1,750 both before and after,
and has grown since only where a later measurement was registered.

**Text.** Section 6.5 now states the exact convention, the 0.0167 floor and its
consequence — *nothing short of a perfect rank reversal can reach p < 0.05 across
five architectures* — and records that the ten-subject family keeps the
approximation because recomputing all forty-five exactly changes no verdict.
Eighteen quoted p-values were updated across `INTRODUCTION.md`, `RESEARCH_GAP.md`,
`RESULTS.md` (including the Figure 2 caption), `DISCUSSION.md` and
`CONCLUSION.md`, together with the sentences whose meaning changed with them —
"only the first two reach significance" is now "only the first".

**What this did not cost the paper.** The claim is about *direction*, and the
direction holds on all three constructions under either convention. Research Gap
§3.2 already said so: *"The direction is therefore consistent on all three
constructions and its strength is not."* The capacity correlation was already
withdrawn on other grounds, so the exact test agrees with a decision the paper had
taken independently. `preflight.py` reports 16 of 16 checks passing.

**One thing the change also removed.** Three `cross_arm_ordering` rows carried
`p = 0.0000` for ρ = 1.000 — impossible from five points, and a division by zero
rather than a probability. Those p-values were never printed in the manuscript,
only recorded in the registry, but they were there to be copied.
