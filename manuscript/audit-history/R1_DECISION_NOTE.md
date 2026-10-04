# R1 — multiplicity: note for Guide Sir

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

One page. The full inventory is in `R1_TEST_INVENTORY.md`; the register entry is R1 in
`REAUDIT_FINDINGS.md`. Nothing has been written into the manuscript.

---

## Where things stand

The manuscript reports **190 distinct inferential comparisons**, of which **82** reach
p < 0.05 nominally. No α is declared as a study-wide criterion. The words
"multiplicity", "multiple testing", "family-wise", "Bonferroni", "Holm" and "FDR" appear
zero times. The 190 was counted twice, independently — by executing every test family
against the released fold data, and by reconciling against `MASTER_NUMBERS.csv` — and the
two agree exactly.

Three decisions are needed, and they are separate.

---

## The three decisions, in one block

> **Decision A — Proposed: 190 distinct inferential comparisons actually performed and
> registered.** Established directly from the code and the registry. The 163 printed
> `p =` occurrences and the 93 results visible in tables are not the multiplicity
> universe.
>
> **Decision B — Open.** The confirmatory family boundary needs to be selected
> explicitly. It moves the answer from 82 nominal to 43, 11, or 0 depending on where it
> is drawn.
>
> **Decision B — Proposed: per-family, with the prevalence family disclosed separately.**
> The families are the twelve in `R1_TEST_INVENTORY.md`. The drowsy-count / prevalence
> family is reported on its own line because it supplies 32 of the 82 nominal results and
> every one of the 24 that survive one-family BY.
>
> **Decision C — Proposed: C3, exploratory framing, with per-family BH *and* BY as
> sensitivity analyses rather than as the decision rule.** Neither Holm nor BY is the
> primary criterion. Holm cannot reject anything in a Wilcoxon family of 26 or more
> ten-subject comparisons, because even the smallest attainable exact p-value cannot cross
> its first threshold. BY over one family of 190 keeps 24, and all 24 are from the
> prevalence family — which makes it a bound worth disclosing, not a criterion to decide by.
> Nominal p-values are reported transparently and "significant" stops being load-bearing
> evidence.
>
> **Important boundary case.** The five-architecture Spearman result has
> p = 2/5! = 1/60, exactly equal to α/3 = 1/60. The treatment of equality must be
> specified, rather than described as a floating-point accident.
>
> **Attached, because both are directly affected by how C is settled:** R3/R9 (the tied
> subject, which lowers that comparison's floor to 2/2⁹ and its Holm ceiling to m ≤ 12)
> and R39 (the ten hidden balanced-accuracy tests, now reconciled).

**The four numbers the framing rests on**, every one recomputed from the released fold data:

| Analysis set | Tests | nominal p < 0.05 | BH | BY |
|---|---|---|---|---|
| All registered comparisons | 190 | 82 | 57 | 24 |
| Drowsy-count / prevalence family | 45 | 32 | 32 | 30 |
| Remaining comparisons | 145 | 50 | 22 | 0 |

**How the count should be stated** — not as "82 significant findings":

> Across 190 registered comparisons, 82 yielded nominal p < 0.05. Of these, 32 arose from
> the 45-comparison drowsy-count / prevalence family and 50 from the remaining 145
> comparisons.

**Sir's approval is needed on B and C before anything is implemented.** A is established by
the pipeline and is not a judgement call.

---

## Decision A — the multiplicity universe

**Proposed: 190.** Every distinct inferential comparison actually performed and
registered.

The alternatives are not competing answers to the same question. 163 is the number of
printed `p =` occurrences, which counts restatements (the twelve Table 4 comparisons
appear three times) and shared floor values (`p = 0.0020` is printed eighteen times for
five different comparisons). 93 is what a reader can see in a table. At least **74 of the
190 are reported only as a count or a bound** — "none of the ten", "ρ ≥ +0.79 with
p ≤ 0.0061 on fourteen of the fifteen". They were still run. A multiplicity statement is
about what was run.

This one the data settles. A and B/C are different in kind: A is a fact, B and C are
methodological choices.

---

## Decision B — where the family boundary is drawn

It changes the answer by a factor of four:

| Family structure | n | nominal | Holm | BH |
|---|---|---|---|---|
| one family of everything | 190 | 82 | **11** | 57 |
| by analysis question, twelve families | 190 | 82 | **43** | 60 |
| confirmatory subset (44) against the rest | 44 | 27 | **0** | 23 |

The third row is the one to look at, and it is not a typo.

---

## The finding that bears on Decision C

**For a Wilcoxon family of 26 or more ten-subject comparisons, Holm correction cannot
reject even the smallest attainable two-sided p-value. It is therefore uninformative for
those families in this design.**

Stated that narrowly on purpose. Holm is not unavailable in general — it rejects freely
in small families, and the table in Decision B shows it doing so. The limitation is
specific to family size in a ten-subject paired design.

The smallest p a Wilcoxon signed-rank test on ten pairs can return is 2/2¹⁰ = 1/512.
Holm's first threshold is α/m. So the most extreme result physically attainable clears
the first hurdle only while m ≤ α/floor. In exact rational arithmetic, no floating point:

| Test | Smallest attainable p | Holm can reject only if | At that m |
|---|---|---|---|
| Wilcoxon, 10 subjects | 1/512 | m ≤ 25 | strictly, 1/512 < 1/500 |
| Wilcoxon, 9 subjects (one tie — see R3/R9) | 1/256 | m ≤ 12 | strictly, 1/256 < 1/240 |
| Spearman exact, 5 architectures | 1/60 | m ≤ 3 | **equality — the boundary is exact** |

```
m=25  alpha/m = 1/500   floor 1/512   floor <= alpha/m ?  True
m=26  alpha/m = 1/520   floor 1/512   floor <= alpha/m ?  False
```

This is why the 44-test confirmatory family keeps zero: its smallest p is 1/512, the
floor, and α/44 = 1/880 is below it. Holm rejects nothing there **because the sample has
ten subjects**, not because the effects are absent — for that family, the correction
returns the same verdict for every dataset that could have been collected.

**The boundary case, stated correctly.** The accuracy-against-recall result lies exactly
at the Holm boundary. This is a mathematical identity, not a floating-point accident:

$$\frac{2}{5!} \;=\; \frac{2}{120} \;=\; \frac{1}{60} \;=\; \frac{0.05}{3} \;=\; \frac{\alpha}{3}$$

Verified as exact rationals: `Fraction(2, 120) == Fraction(5,100)/3` → `True`. The
Spearman ceiling is m ≤ 3 and the family is exactly 3, so the result sits precisely on
the ceiling — and it is the only one of the three rows above that reaches its boundary
with equality rather than strictly. **Whether equality is accepted therefore determines
the decision**, and that convention has to be specified rather than left to whichever
comparison operator an implementation happens to use.

---

## Decision C — the correction policy

Three options, with what each costs:

**C1. Holm.** Available for small families, uninformative for the large ones. For any
Wilcoxon family of 26 or more ten-subject comparisons it returns zero regardless of the
data, and the one headline result that would survive sits exactly on the boundary, so
the answer turns on a convention rather than on evidence. If Holm is chosen, the family
boundary of Decision B has to keep every family at or below the ceilings in the table
above, and the equality convention has to be stated.

**C2. Benjamini–Hochberg.** No floor problem at any family size. It separates the
families much as the paper's own narrative does: the A-vs-C balancing contrast keeps 4 of
7, calibration keeps 5 of 13, threshold selection keeps 0 of 7. A reviewer asking "did
you correct for multiple testing?" gets a direct answer, and the multiplicity adjustment
is explicitly present in the paper. The cost is that several claims currently stated as
significant would have to be restated, and the threshold-selection and
cross-arm-ordering sections lose their inferential support.

**C3. Declare the analyses exploratory and report nominal p-values, once, plainly.**
State the number of tests (190), state that no correction was applied, state why, and
stop using "significant" as a load-bearing word in the Abstract and Conclusion. This is
internally coherent with the design as built. The cost is that no claim can be called
confirmed.

**This is a methodological choice, not something the data settles.** Decision A is
established by the code and the registry; B and C are not. The ceiling table is an
argument about what Holm can measure at n = 10 — it is not evidence that C3 is correct.

**If C3 is chosen, and BH is also reported**, the manuscript must say in the same place
that the BH results are a **sensitivity / secondary multiplicity analysis, not the
primary inferential decision rule**. Otherwise a reviewer will reasonably ask why a
correction that was computed was not used for the primary claims, and the transparency
becomes a liability instead of an asset.

I have changed nothing in the manuscript.

---

## My recommendation: C3 + BH, with one addition and one warning

I agree with C3 plus BH as a sensitivity analysis. Three things should go with it, and one
of them changes the plan.

### The warning: BH's assumption does not hold here, and a reviewer will say so

BH controls the false discovery rate under independence or positive regression dependency.
These 190 comparisons are neither. They share ten subjects, share folds, overlap in
architecture pairs, and correlate across metrics — ROC-AUC, PR-AUC, F1 and balanced
accuracy are computed from the same predictions. Positive dependency is plausible but is
not established, and it is exactly the kind of thing a methods reviewer at BSPC asks about.

Under Benjamini–Yekutieli, which is valid under **arbitrary** dependence:

| Family | N | nominal | BH | **BY** |
|---|---|---|---|---|
| EEGNet pairs, ROC-AUC | 12 | 11 | 10 | 8 |
| ablation, 3 metrics | 9 | 8 | 8 | 6 |
| **A vs C balancing** | 20 | 7 | 4 | **0** |
| calibration, Platt vs raw | 18 | 13 | 5 | 3 |
| threshold selection | 24 | 7 | 0 | 0 |
| **accuracy vs pooled recall** | 3 | 1 | 1 | **0** |
| drowsy count vs PR-AUC | 45 | 32 | 32 | 30 |
| one family of everything | 190 | 82 | 57 | 24 |

**The two results the paper leans on hardest are the two that BH keeps and BY does not:**
the A-vs-C balancing contrast (4 → 0) and the accuracy-against-pooled-recall correlation
(1 → 0).

This is the strongest argument for C3 over C2, and it is worth being explicit about.
If BH is the **primary** rule, then the dependence question becomes an attack on the
paper's primary inference, and the answer to it is that two headline claims disappear. If
BH is a **sensitivity** analysis, the dependence question is just one more sensitivity
row. C3 is robust to a problem that C2 is not.

**So report both BH and BY**, in the same table, and say which assumption each needs. One
extra column removes the single most likely methodological attack. Reporting BH alone and
then being asked "why not BY, given the dependence?" is the worst of the three outcomes.

### The addition: the disclosure is an argument in the paper's favour, and it is being left on the table

Under a global null at α = 0.05:

```
all 190 comparisons       : observed 82, expected  9.5
excluding drowsy-count    : observed 50 of 145, expected 7.2
drowsy-count family alone : observed 32 of 45,  expected 2.2
```

Roughly seven times the reference, and still seven times after removing the family most
likely to be dismissed as near-tautological.

**This must not be presented as inferential evidence** — you are right to insist on that.
The comparisons are dependent and were not generated under a single global-null experiment,
so there is no valid global-null test here. The wording has to carry that itself, in the
same sentence, not in a later caveat:

> Across the 190 registered comparisons, 82 yielded nominal p < 0.05, against 9.5 expected
> under a simple global-null reference at α = 0.05. Because the comparisons are dependent
> and were not generated under a single global-null experiment, this comparison is
> descriptive context for the multiplicity disclosure rather than a formal global-null test.

Bounded that way it still earns its place. It is the difference between a paper that
discloses 190 tests alongside their reference count and a paper that quietly reports 82
significant findings. Same numbers, and only one of them reads as careful.

### Recomputed exactly, as you asked — and one row changes the picture

The split table, every cell computed from the released fold data, nothing by hand:

| Analysis set | Tests | nominal | BH | BY |
|---|---|---|---|---|
| All registered comparisons | 190 | 82 | 57 | 24 |
| Drowsy-count / prevalence family | 45 | 32 | 32 | 30 |
| Remaining comparisons | 145 | 50 | 22 | **0** |

**And of the 24 that survive BY over all 190, all 24 are from the drowsy-count family:**

```
BY over all 190: 24 survive.   {'drowsy count': 24}
BH over all 190: 57 survive.   {'drowsy count': 30, 'EEGNet pairs': 9, 'ablation': 6,
                                'calibration': 5, 'A vs C': 4, 'threshold': 3}
```

This has to be stated plainly because it is the hardest version of the objection. Under a
single family of 190 with arbitrary-dependence control, the **only** thing that survives is
the finding that PR-AUC rises with a subject's event count — the one result closest to being
a property of the metric. Every architecture comparison, every arm contrast, every
calibration and threshold result falls.

Two conclusions follow, and they point the same way.

**First, one-family BY is a reductio, not a verdict.** A correction whose sole survivor is
the near-definitional result is not telling us which findings are real; it is telling us that
190 dependent tests on ten subjects cannot support family-wise or arbitrary-dependence
control at this sample size. That is the same lesson as the Holm ceiling, arrived at from the
other direction.

**Second, the paper cannot claim its findings survive multiplicity control under arbitrary
dependence, and should not try.** This is not an argument for hiding the row. It is the
argument that C3 is the only honest framing available — not merely the most defensible one.
If the analyses are exploratory, this row is expected and says something true about n = 10.
If they were presented as confirmatory, this row would be fatal.

So the sensitivity analysis should be reported **per family**, with the one-family row
included as a bound and with its composition stated — because a bare "BY over 190 keeps 24"
reads as "nothing in this paper survives", and the correct reading is "the correction is
dominated by a single family of 45 near-tautological tests".

This also sharpens your instinct about splitting the 82. The split is not only about not
misleading on the count. **Without the split, the sensitivity analysis is uninterpretable.**

### The thing Decision B actually has to settle

The drowsy-count family is 45 of the 190 and 32 of the 82, and it survives everything —
BH 32, BY 30, by far the most robust family in the study. It is also the family measuring
that PR-AUC rises with prevalence, which is close to a property of the metric. The paper
already knows this: it reports the prevalence-corrected form precisely because the raw
form is near-definitional.

This does not change Decision A — the 190 is what was run. But it changes what "82" means,
and the count should be reported split rather than as one number, so the reader is not
misled in either direction.

### Two implementation points

**C3 is not a wording patch on "significant".** If the analyses are exploratory, then R4
("the strongest replication in the study"), R7 ("ROC-AUC is unchanged on all three"), R34
(the Highlights bullet) and the "establishes / isolates / demonstrates" verbs from Pass 8
are part of the same change. A search-and-replace on "significant" would leave the paper
confirmatory in tone and exploratory in its statistics, which is worse than either. C3 is
one synchronized pass from Abstract to Conclusion, and it absorbs several Pass-8 findings
rather than sitting beside them.

**Generate the table, do not type it.** The BH and BY columns should be produced by a tool
that reads the registry and writes a CSV, gated by preflight like everything else here.
R31 is already a finding about what happens to a hand-maintained table in this repository.

### What I would say to sir, in one sentence

Report the analyses as exploratory over a transparent universe of 190 comparisons, give BH
**and** BY per family as sensitivity analyses rather than as the decision rule, disclose the
drowsy-count family separately because it supplies 32 of the 82 and every one of the 24
one-family BY survivors, and state the 82-against-9.5 comparison as descriptive context
only — because this framing is the one that stays honest when a reviewer applies
arbitrary-dependence control, and no framing that leans on correction survives that.

I am not a statistician, and this is a methodological judgement that is properly sir's. But
having measured it from both directions — the Holm ceiling and the one-family BY reductio —
I do not think there is a defensible route here that keeps "significant" as load-bearing
evidence. C3 is not the safe choice among three; it is the one the design supports.

### Ready when the decision is approved, not before

The BH/BY table should be generated, not typed: a tool that reads the registry, writes
`results/MULTIPLICITY.csv`, and is gated by preflight like the other nineteen checks. I have
not written it, and I have added nothing to the repository for this — the numbers above came
from a scratch script outside it. R31 is already a finding about hand-maintained tables here,
and a tool wired in before the policy is settled would have to be rewritten when it is.

Current baseline preserved: **40 tests pass, 20 of 20 preflight checks pass, no manuscript
change.**

---

## Two related items that must be settled with this

**R3/R9 — the tied subject.** One Wilcoxon comparison has an exact tie, so its effective
n is 9 and its floor is 2/2⁹ = 0.00390625, not the 2/2¹⁰ that §6.5 states generically.
Under any correction its ceiling is m ≤ 12, not m ≤ 25. The registry also records that
comparison as 10/10 improved where the manuscript correctly says 9/10.

**R39 — the ten hidden tests.** Reconciled: all ten balanced-accuracy arm contrasts were
performed, all ten are in the registry, and every value matches. "Seven of twenty" is
**correct**. But the tables show three metrics, so a reader counting significant cells
finds six and is told seven. The seventh is A vs C, CNN-BiLSTM, balanced accuracy,
p = 0.0039 — which supports the paper's own mechanism sentence. Showing the column costs
nothing and closes the gap.
