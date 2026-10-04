# Full re-audit — findings register

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

*24 September 2026, after the twenty Step 3 findings were closed.*
*Nothing below has been patched. Every finding is recorded as*
**Finding → Evidence → Impact → Required action → Status.**

**The rule this audit followed:** the current manuscript, registry and code are the
only source of truth. No conclusion from the earlier audit was carried forward
untested, and `STEP3_SCIENTIFIC_CHECK.md` and `SPEARMAN_P_NOTE.md` were treated as
records of past work, not as evidence.

**Passes complete:** 1 (numerical integrity), 2 (statistical integrity),
3 (protocol and leakage). **Outstanding:** 4 (claim-to-evidence), 5 (figures and
tables), 6 (references and literature), 7 (reproducibility), 8 (language).

---

## Passes that came back clean

### Pass 1 — numerical integrity: CLEAN

Re-derived rather than trusted. For all three arms: windows per subject × 10 equals
the arm total; the per-subject drowsy counts sum to the arm total; π(1 − π) matches
the registered Brier reference to nine decimals; the registered prevalence matches
100 π. Parameter counts are integers matching `config.PARAMS`. `src/scan.py` finds
zero unregistered numbers across all ten submitted sections, and the row-count guard
finds zero wrong "N rows" claims.

### Pass 3 — protocol and leakage: CLEAN

Re-derived on all 750 folds, not on a sample. Every subject is held out exactly once
in each of the 75 (arm, model, seed) groups. **Zero folds have the test subject
inside their own validation set.** Every validation set has exactly two subjects,
leaving seven for training, matching `config.N_VAL`. Fold total is 750 as declared.

### Pass 2 — the four areas within it that came back clean

**Spearman framework.** Exact permutation for every five-point correlation, the
t-approximation only at n = 10, by the declared code path. All 69 registered ρ/p
pairs recompute. No reported p falls below the 0.0167 floor.

**Capacity correlation.** ρ = −0.900 / −0.500 / −0.100 with exact p = 0.0833 /
0.4500 / 0.9500 all reproduce; withdrawn consistently in all five sections.

**Platt versus isotonic.** Every ECE and Brier value in Table 7 and all 18
raw-vs-Platt p-values reproduce. The strictly-increasing / non-decreasing asymmetry
is kept everywhere, and **no ranking-invariance claim is made for isotonic** in any
file.

**Wilcoxon aggregation.** Every Wilcoxon in the codebase runs on ten subject-level
values. **There is no test anywhere on fifty folds.**

---

## Findings

### R1 — Multiplicity is never mentioned, in a paper reporting 181 tests

**FINDING.** The study runs at least 181 individual significance tests and reports
79 as significant at α = 0.05. No file mentions multiplicity in any form.

**EVIDENCE.** A case-insensitive search for *bonferroni, multiple compar,
multiplicity, family-wise, false discovery, FDR* across every manuscript file and
`README.md` returns **nothing** — I ran it. Per pre-enumerated family, with Holm:
EEGNet ROC-AUC 11 of 12 → 8; A-vs-C contrast 7 of 20 → 1; ablation 8 of 12 → 5;
raw-vs-Platt 13 of 18 → 3; threshold selection 7 of 24 → **0**; five-point Spearman
4 of 24 → **0**.

**IMPACT.** Two narratives sit entirely inside families that survive nothing.
"Across the twenty-four tests, seven changes reach significance" (threshold
selection) → Holm leaves zero. "Seven of twenty" (balancing) → Holm leaves one, and
neither ROC-AUC result the claim rests on (both p = 0.0488) survives. The paper
discloses every family size honestly and then never lets the denominator touch the
p-value.

**REQUIRED ACTION.** Name the pre-specified families and their sizes in §6.5, state
a correction (Holm within family fits, since the families are already enumerated),
and where a family survives nothing, say so in the sentence that draws the
conclusion. Add multiplicity to §8.10.

**STATUS.** CONFIRMED — I verified the absence of any mention myself.

---

### R2 — "Four of the twelve" reach the Wilcoxon floor. Five do.

**FINDING.** Two sentences say four EEGNet comparisons reach p = 2/2¹⁰; five do, and
the paper's own table prints five.

**EVIDENCE.** `RESULTS.md:182` *"which four of the twelve reach by improving on every
subject"* and `RESULTS.md:996` *"with four comparisons reaching the attainable
p-floor of 0.0020"*. I recomputed: **five** are at p = 0.001953125 exactly — EEGNet
vs CNN and vs DeepConvNet on Arm A, vs DeepConvNet and vs CNN-BiLSTM on Arm B, vs
ShallowConvNet on Arm C. The table at `RESULTS.md:174-178` shows five bold
`p = 0.0020` cells; `DISCUSSION.md:33-37` names all five.

**IMPACT.** A reader checking the sentence against the table three lines above finds
the paper miscounting its own strongest results — in a paper whose argument is that
counts are machine-checked.

**REQUIRED ACTION.** "four" → "five" in both places, and register the count.
`src/scan.py` ignores integers below 1000, so nothing catches this class.

**STATUS.** CONFIRMED.

---

### R3 — Some Wilcoxon tests ran on fewer than ten pairs, and the stated floor does not hold for them

**FINDING.** `scipy.stats.wilcoxon` discards zero differences by default. Where a
subject ties, the effective n falls and the attainable floor rises — but §6.5
declares the floor as 2/2¹⁰ without qualification.

**EVIDENCE.** `src/stats.py:138` and `:172` call `wilcoxon(a, b)` with no
`zero_method`. I recomputed the ablation family: **Arm C CNN vs CNN-BiLSTM on F1**
prints `p = 0.0039` at `RESULTS.md:312`, and 0.00390625 is **exactly 2/2⁹ — the
floor for nine pairs**, because one subject's difference is exactly zero. Arm A on
F1 likewise has one tie. Neither ROC-AUC nor PR-AUC is affected, so "eleven of
twelve" is safe.

**IMPACT.** A reviewer reading §6.5 takes p = 0.0039 as two steps above the
ten-subject floor; it is *at* the nine-subject floor. A result presented as a
ten-subject test was a nine-subject test.

**REQUIRED ACTION.** Record and print the effective n for every Wilcoxon, or set
`zero_method` explicitly and say which. Add one sentence to §6.5 that ties reduce
the effective n and raise the floor.

**STATUS.** CONFIRMED.

---

### R4 — The headline partition is stable at the reported aggregation but not within it

**FINDING.** The Brier partition — "the strongest replication in the study" — holds
as stated on the seed-averaged values, but holds in only **10 of the 15 (arm, seed)
cells** underneath them.

**EVIDENCE.** The claim, `RESULTS.md:600-604`: *"On all three constructions, exactly
the same three architectures exceed the class-prior Brier reference."* At the
seed-averaged level that is **true** — I re-verified it. Per seed, from
`ALL_POOLED.csv`, the partition fails on A-seed2, A-seed3, B-seed1, B-seed42,
C-seed2. **Arm A CNN-BiLSTM is below the reference on two of five seeds** (0.0696
and 0.0754 against 0.0762); its mean margin is +0.0019 against a between-seed SD of
0.0062. No test is applied to the partition.

**IMPACT.** "Identical on all three constructions" reads as a robust replication.
One of the five architectures sits inside its own seed spread of the cut point, so a
rerun with other seeds could produce a different partition — for the paper's most
emphasised result. The paper already concedes the *margin* is not stable; it does
claim the *side* is, three times out of three.

**REQUIRED ACTION.** Report how many of the 15 arm × seed cells reproduce the
partition (the per-seed values are already registered), and either attach an
interval to each margin or narrow "strongest replication" to the architectures whose
margin exceeds their own seed spread.

**STATUS.** CONFIRMED. **This is a scope-and-strength finding, not a false number:**
every printed value is correct at the aggregation it is printed for.

---

### R5 — "Eleven of twelve" survives in three places after being corrected in two

**FINDING.** EEGNet leads **twelve** of twelve on the point estimate; eleven is the
significance count. The Abstract and Conclusion now say this correctly; three other
places still do not.

**EVIDENCE.** `MASTER_FILE.md:83`, `DISCUSSION.md:32-33`, `RESULTS.md:995-996` all
say "leads in eleven of twelve". I recomputed: EEGNet's mean is higher in all 12;
the exception is Arm B vs CNN, 0.9003 against 0.8662, p = 0.0645, higher on 8 of 10
subjects.

**IMPACT.** A reader of the Discussion concludes EEGNet was beaten once. It never
was. And the paper contradicts itself between sections.

**REQUIRED ACTION.** Use the Abstract's wording in all three. Note `MASTER_FILE.md`
is generated — fix `tools/master_file.py`.

**STATUS.** CONFIRMED.

---

### R6 — The ranking-invariance claim is scoped in Results and unscoped in five other places

**FINDING.** The measurement covers Arm A only, three architectures — 3 of the 15
(architecture, arm) cells the ranking tables report. Results says so; the Abstract,
Highlights, Introduction item 3, §6.6 and the Figure 5 caption do not.

**EVIDENCE.** Correct: `RESULTS.md:806-808` *"For the three architectures with
released probability scores…"*, matching `results/ranking_invariance.csv` (six rows,
all Arm A) and the tool's own stated scope. Unscoped: `ABSTRACT.md:60-62`,
`ABSTRACT.md:74`, `INTRODUCTION.md:134-137` (which says *"the aggregation the ranking
tables report"*), `EXPERIMENTAL_SETUP.md:134-137` (*"Table 4 and Section 7.1"* —
Table 4 has 15 cells, 3 were recomputed).

**IMPACT.** A reviewer reads a general property of the method where there is a
measurement on one fifth of the reported cells, on the one arm with released scores.

**REQUIRED ACTION.** Carry the Results scoping into all five, and point at §8.10
item 3, which already states the coverage limit.

**STATUS.** CONFIRMED. This is the same class of error F9 fixed for *aggregation*,
now found for *coverage*.

---

### R7 — "ROC-AUC is unchanged on all three" asserts the null in Results, where the Discussion no longer does

**FINDING.** The ablation sentence in Results still says "unchanged" where the point
estimate falls by 0.0215.

**EVIDENCE.** `RESULTS.md:313-314` *"ROC-AUC is unchanged on all three"*, repeated at
`:1014`. Recomputed: 0.8428 → 0.8213 (p = 0.6953), 0.8662 → 0.8590 (p = 0.8457),
0.8469 → 0.8472 (p = 0.5566). At `RESULTS.md:243` a change of **+0.0217** is called
significant. `DISCUSSION.md:94-97` was corrected on 24 September and now reads
correctly — Results was not.

**IMPACT.** "Unchanged" licenses the mechanistic story that the recurrent block does
not order windows better. The data are equally consistent with it ordering them
worse by an amount this sample cannot resolve.

**REQUIRED ACTION.** Use the Discussion's wording in both Results places. The paper
already applies this discipline to trimming ("no measurable effect", not "no
effect").

**STATUS.** CONFIRMED.

---

### R8 — The one table that withholds p-values is the one where a bare ρ misleads most

**FINDING.** The cross-arm ordering table prints twelve rank correlations with no
p-values, under a sentence asserting the ordering is "not arbitrary". Nine of the
twelve are non-significant.

**EVIDENCE.** `RESULTS.md:213-222`. The p-values are already registered: ROC-AUC
A–B ρ = +0.700 (p = 0.2333), A–C +0.300 (**p = 0.6833**), B–C +0.800 (p = 0.1333);
only the three F1 rows at ρ = +1.000 reach the 0.0167 floor.

**IMPACT.** Every other correlation in the paper carries its p. Here a reader sees
"+0.300" as agreement where it is indistinguishable from chance at n = 5.

**REQUIRED ACTION.** Add the p column and narrow the topic sentence to what the
table supports.

**STATUS.** CONFIRMED.

---

### R9 — The registry counts tied subjects as improvements, so two cited cells disagree with it

**FINDING.** `registry.py` computes "improved" as `n − a_wins`, which folds ties into
improvements. Two registry rows therefore assert counts the data does not show, one
of them a unanimity.

**EVIDENCE.** `src/registry.py:137-138`. I recomputed: Arm A CNN vs CNN-BiLSTM on F1
is **7 improved, 1 tied, 2 worse** — the registry note says *"8/10 improved"*. Arm C
is **9 improved, 1 tied** — the registry says *"10/10 improved"*. The manuscript
prints (7/10) and (9/10), which are correct, so **the manuscript and the registry
disagree**.

**IMPACT.** The repository's central guarantee is that every value the manuscript may
cite traces to a registry row. Two do not. `scan.py` cannot catch it — it ignores
integers below 1000. "10/10 improved" asserts unanimity that did not occur.

**REQUIRED ACTION.** Make the count strict, or emit improved / tied / worse as three
numbers, and re-emit the registry. The same tie causes R3, so fix them together.

**STATUS.** CONFIRMED.

---

### R10 — A third dispersion convention is used but not declared

**FINDING.** The selected-threshold spreads are standard deviations over fifty
folds — neither of the two conventions §6.5 declares — and they carry argumentative
weight.

**EVIDENCE.** `EXPERIMENTAL_SETUP.md:73-76` declares two conventions.
`src/thresholds.py:147-148` takes the SD over the raw 50-row frame. The figure is
then argued from: `RESULTS.md:966-967` *"a spread of 0.1626 on a mean of 0.4606 — a
third of its own value"*.

**IMPACT.** A fifty-fold SD blends subject and seed variation and is not comparable
to any other ± in the paper. The "stably offset" mechanism is argued from a number
whose denominator the reader cannot infer.

**REQUIRED ACTION.** Name it in §6.5 and in the caption, or report the
between-subject SD, which is the spread the transfer argument actually needs.

**STATUS.** CONFIRMED.

---

### R11 — Two smaller wording items

**FINDING.** (a) "Parameter count does not predict ranking quality" is a flat
negative drawn from a family where the paper has just shown p < 0.05 is unattainable
unless |ρ| = 1. (b) Two uniqueness claims overstate: "the highest corrected
correlation in the study (+0.915)" is **tied** with Arm A CNN-BiLSTM at +0.9152, and
DeepConvNet is "the only one Platt scaling did not significantly improve" only under
the reading "on neither metric" — Arm A CNN also failed on ECE (p = 0.0840).

**EVIDENCE.** `RESULTS.md:1004-1006` against `EXPERIMENTAL_SETUP.md:94-96`;
`DISCUSSION.md:400-401`; `RESULTS.md:974`.

**IMPACT.** (a) A reader could take "does not predict" as tested and refuted rather
than as underpowered. (b) A checker finds a tie where "the highest" was claimed.

**REQUIRED ACTION.** (a) State it as the Discussion does — not supported, withdrawn,
and five points cannot settle it either way. (b) "among the highest"; "the only one
Platt scaling improved on neither metric".

**STATUS.** CONFIRMED.

---

### R12 — One code-hygiene item with no current effect

**FINDING.** `subject_count_correlation` calls `spearmanr` directly rather than the
paper's own `stats.spearman` wrapper.

**EVIDENCE.** `src/stats.py:224`.

**IMPACT.** None today: n = 10 exceeds `EXACT_SPEARMAN_MAX_N = 8`, so the route is
identical. If the subject count ever fell below nine, this family would silently stay
on the t-approximation while everything else moved to exact.

**REQUIRED ACTION.** Route it through `stats.spearman`.

**STATUS.** CONFIRMED.

---

### R13 — "The largest margin in the study" is attributed to the wrong arm

**FINDING.** Arm C is said three times to be where an architecture beats the
always-alert baseline by the largest or widest margin in the study. Arm A's margin is
larger. The paper's own Table 5, on the same page, contains the refutation.

**EVIDENCE.** Recomputed from `results/ALL_FOLDS.csv` and `results/ALL_POOLED.csv`,
not from the registry:

| Arm | Best architecture | Accuracy | Always-alert baseline | Margin | Seed SD |
|---|---|---|---|---|---|
| A | DeepConvNet | 92.7300 % | 91.6847 % | **+1.0453 pts** | 0.4206 |
| B | CNN | 92.9980 % | 93.0645 % | −0.0665 pts | 0.8977 |
| C | DeepConvNet | 93.5551 % | 92.7322 % | +0.8229 pts | 0.6850 |

Claimed at `RESULTS.md:401`, `RESULTS.md:406`, `RESULTS.md:1020`, `DISCUSSION.md:140`
and `CONCLUSION.md:56`. The reconstructed accuracies reproduce every Table 5 value
exactly, so the table and the sentence are computed from the same numbers.

**IMPACT.** A checkable superlative that fails on the paper's own data, repeated in
Results, Discussion and Conclusion. A second point compounds it: 1.0453 ± 0.4206
against 0.8229 ± 0.6850 means the two margins overlap within seed dispersion, so the
honest statement is not "Arm C is largest" nor "Arm A is largest" but that the two are
not separated at this number of seeds.

**REQUIRED ACTION.** The superlative cannot stand as written. Either drop it, or
attribute the larger margin to Arm A, or state that the two margins do not separate.

**STATUS.** CONFIRMED — measured independently in Pass 4 and again in Pass 8.

---

### R14 — EEGNet's Arm A Brier is printed as two different numbers, and §7.7 does not disclose it

**FINDING.** EEGNet's pooled Arm A Brier score appears as 0.1010 in the results tables
and as 0.1009 in the calibration summary, while §7.5.1 states the two agree exactly.

**EVIDENCE.**

```
ALL_POOLED.csv mean of 5 seeds : 0.10098375   -> prints 0.1010
calibration_summary.csv        : 0.10090286   -> prints 0.1009
difference                     : 8.09e-05
CNN          difference        : 2.78e-17
CNN-BiLSTM   difference        : 4.16e-17
```

The cause is that the two files were written by different executions. §7.7 already
discloses that two executions exist and that they differ, but it enumerates PR-AUC and
balanced accuracy — it omits Brier, which is the one metric of the three that does not
agree to four decimal places.

**IMPACT.** A reader reconciling the calibration section against the results tables
finds a discrepancy the paper says cannot exist.

**REQUIRED ACTION.** Either regenerate both from one execution, or add Brier to the
§7.7 disclosure and stop asserting exact agreement in §7.5.1.

**STATUS.** CONFIRMED.

---

### R15 — "More than an order of magnitude" is false for one of the fifteen cases

**FINDING.** `DISCUSSION.md:499` states that a subject-blind interval understates the
variation in subject-level PR-AUC by more than an order of magnitude. One of the
fifteen architecture × arm ratios is 5.63.

**EVIDENCE.** `results/MASTER_NUMBERS.csv`, rows `... subject to seed SD ratio`:
minimum 5.6339 (Arm B, CNN-BiLSTM), maximum 47.7655 (Arm A, CNN). Fourteen of fifteen
exceed ×10; one does not. The hedged wording elsewhere — "roughly an order of
magnitude" at `INTRODUCTION.md:100` and `RESEARCH_GAP.md:74` — is not affected.

**IMPACT.** Narrow, but it is an unqualified quantitative claim that the paper's own
registry refutes in one cell.

**REQUIRED ACTION.** Qualify the `DISCUSSION.md:499` sentence, or give the range.

**STATUS.** CONFIRMED.

---

### R16 — The released registry advertises reproducibility for two architectures that were never re-executed

**FINDING.** Eight registry rows describe CNN and CNN-BiLSTM as "50 of 50" identical
folds, while `src/repro.py` classifies both as never independently re-executed
(`largest_fold_difference = 0.000000`, `folds_bit_identical = 50` — the signature of a
carried-over file, not of a reproduced run).

**EVIDENCE.** `results/MASTER_NUMBERS.csv` reproducibility rows against
`results/*/reproducibility.csv` and `src/repro.py`'s own exclusion logic. The
manuscript is correct — it says three architectures were re-executed. The released
registry is the artefact that is wrong.

**IMPACT.** A reviewer who reads the registry rather than the manuscript concludes
five architectures were reproduced. `repro.py` is well written and actively refuses to
report a fabricated verdict; the registry export undoes that protection.

**REQUIRED ACTION.** The registry rows must carry the same exclusion `repro.py`
applies, or be removed.

**STATUS.** CONFIRMED.

---

### R17 — "The only one whose raw calibration was already below the reference" is true of two

**FINDING.** A uniqueness claim in the recalibration discussion holds for a second
architecture as well.

**EVIDENCE.** Arm A CNN's raw pooled Brier is 0.0671 against the Arm A reference of
0.0762 — already below it, the same condition the sentence says is unique to one
architecture. `results/MASTER_NUMBERS.csv`, Table 6 at `MANUSCRIPT.md:1827-1833`.

**IMPACT.** A stated uniqueness that is not unique.

**REQUIRED ACTION.** Drop "the only one", or scope it to the arm and metric where it
does hold.

**STATUS.** CONFIRMED.

---

### R18 — Figure 1 says accuracy, Brier and ECE are "measured on every fold". None of the three is

**FINDING.** The first figure in the paper — the design figure — ends with a line
listing eight metrics as measured on every fold. `fold_metrics()` computes six, and
accuracy, Brier score and expected calibration error are not among them.

**EVIDENCE.** `src/figures.py:994-995`, rendered verbatim into
`figures/figure1_study_design.png`:

> "Measured on every fold: ROC-AUC · PR-AUC · recall · F1 · balanced accuracy ·
> accuracy · Brier score · expected calibration error"

`src/train_loso.py:80-93`, `fold_metrics()`, returns `auc, pr_auc, bal_acc, f1,
precision, recall` and nothing else. Accuracy is built downstream in
`src/stats.py:302-332` from pooled confusion counts. The manuscript states the
correct position at `MANUSCRIPT.md:1318-1321`: *"Accuracy exists only as a pooled
quantity. It is read off the pooled confusion matrix and has no subject-averaged
counterpart anywhere in this paper."*

**IMPACT.** This is the estimator-convention conflation the paper spends several
sections guarding against, printed in its own opening figure and contradicting its own
Methods. It is the most visible single error found in Passes 5–8.

**REQUIRED ACTION.** The three pooled-only metrics must come off that line, or the
line must distinguish per-fold metrics from seed-pooled ones.

**STATUS.** CONFIRMED.

---

### R19 — Table 6's caption states a bold rule; the table contains no bold at all

**FINDING.** Table 6's caption says "Bold marks a score *above* the reference" and the
sentence introducing it says the three architectures are "marked in bold". No cell in
Table 6 carries bold markup.

**EVIDENCE.** `MANUSCRIPT.md:1815-1817` and caption `MANUSCRIPT.md:1821-1825` against
the table body at `MANUSCRIPT.md:1827-1833`, e.g.
`| EEGNet | 0.1010 | 0.0859 | 0.0952 | above ×3 |`. The §7.5 per-arm tables do carry
the bold correctly (`MANUSCRIPT.md:1789-1793`), which is why the omission survived.

**IMPACT.** Table 6 is the table for the paper's self-described "strongest replication
in the study", and it fails to show the partition its caption promises.

**REQUIRED ACTION.** Bold the nine above-reference cells, or remove the rule from the
caption and the prose.

**STATUS.** CONFIRMED.

---

### R20 — The Brier column carries no dispersion while the three columns beside it do

**FINDING.** In all three §7.5 per-arm tables, ROC-AUC, PR-AUC and balanced accuracy
are given as mean ± seed SD. Brier, in the same row, is a bare number. The seed SD
exists in the registry and is drawn as an error bar in Figure S1.

**EVIDENCE.** `MANUSCRIPT.md:1787-1794`, `:1797-1803`, `:1807-1813`.
`results/MASTER_NUMBERS.csv:92` `Arm A EEGNet brier pooled seed SD,0.005`;
`:410` `Arm B ShallowConvNet brier pooled seed SD,0.0495`. `src/figures.py:617-621`
draws exactly this SD as `yerr`. The paper flags the consequence itself in the Figure
S1 caption (`MANUSCRIPT.md:1275-1276`): *"one of the five seeds gives 0.2246 against
about 0.11 for the other four."*

**IMPACT.** The single most unstable number in the Brier tables is the one a reader
cannot see is unstable.

**REQUIRED ACTION.** Add ± seed SD to the Brier column, using the registry values.

**STATUS.** CONFIRMED.

---

### R21 — Table 5 has one bolded cell and no stated rule

**FINDING.** Table 5's caption states no emphasis rule, yet exactly one data cell is
bold: Arm C, DeepConvNet, 93.56 %. Arm A DeepConvNet at 92.73 %, which also beats its
arm's baseline, is not bold.

**EVIDENCE.** Caption `MANUSCRIPT.md:1578-1584` (no rule); `MANUSCRIPT.md:1588`
(not bold) against `MANUSCRIPT.md:1598` (bold). The only justification is prose at
`MANUSCRIPT.md:1615-1617` — and that prose is R13, the claim that is false.

**IMPACT.** The emphasis silently encodes the incorrect superlative of R13. Fixing
R13 without fixing this leaves the wrong cell highlighted.

**REQUIRED ACTION.** Remove the bold, or state a rule in the caption — after R13 is
settled, not before.

**STATUS.** CONFIRMED.

---

### R22 — Table 8 bolds "not run" in one cell and not in an identical one

**FINDING.** Two cells read "not run"; one is bold, one is not, and the caption states
no rule.

**EVIDENCE.** `MANUSCRIPT.md:2291` `| Threshold selection | same 3 | **not run** |
same 3 |` against `MANUSCRIPT.md:2292` `| Repeated-execution check | ... | not run |`.
Caption `MANUSCRIPT.md:2282-2284`.

**IMPACT.** Cosmetic. A reader may look for a distinction that does not exist.

**REQUIRED ACTION.** Bold both or neither.

**STATUS.** CONFIRMED (minor).

---

### R23 — Figure 2 prints p to three decimals; the text prints the same p to four

**FINDING.** `src/figures.py:364-366` formats the panel p-values as `%.3f`, so Arm A's
0.0167 renders as "0.017" and Arm B's 0.0833 as "0.083". The body text and registry
give four.

**EVIDENCE.** `src/figures.py:356-366`; `results/MASTER_NUMBERS.csv:1149-1150`,
`:1229-1230`, `:1309-1310`; text at `MANUSCRIPT.md:683-684`, `:1418`, `:2219`, `:2233`.

**IMPACT.** No numeric contradiction. It does make the figure harder to reconcile with
the text, and 0.0167 is a floor value, where the trailing digits carry meaning.

**REQUIRED ACTION.** Raise the figure format to `%.4f`.

**STATUS.** CONFIRMED (minor).

---

### R24 — Figure S1 panel (h) does not state its estimator convention, though its neighbours do

**FINDING.** The caption labels panels (a)–(c) "subject-averaged" and (g) and (i)
"pooled". Panel (h), raw expected calibration error, is labelled with neither — and it
is subject-averaged, unlike the two panels on either side of it.

**EVIDENCE.** Caption `MANUSCRIPT.md:1265-1281`; code `src/figures.py:749-770`, which
looks up `"Arm %s %s raw ECE SUBJECT-AVERAGED"`.

**IMPACT.** A reader is likelier to infer "pooled" from the neighbours than the truth.
Resolvable only by cross-referencing §7.5.1 prose, so the caption is not self-contained.

**REQUIRED ACTION.** Add "(subject-averaged)" to panel (h)'s caption clause.

**STATUS.** CONFIRMED.

---

### R25 — The built manuscript's References section is the internal audit trail, including an unfinished TODO list

**FINDING.** `manuscript/REFERENCES.md` is a working verification document, and
`tools/build_manuscript.py` copies it into `MANUSCRIPT.md` without stripping any of it.
The submission document's reference list therefore contains the authors' verification
commentary and a section headed "Still to add before submission".

**EVIDENCE.** Verified directly in the built file:

```
3100:  click. **Nothing in this list was written from memory.**
3483:  ## Still to add before submission
```

`tools/build_manuscript.py:52-88` strips only Hindi blockquotes, headings matching
`Notes for the next pass|Notes\b.*not part of the paper`, the file's own top `#` line,
and text between `<!-- not-for-submission:start/end -->` markers. `REFERENCES.md`
carries none of those markers.

**IMPACT.** Severe, and independent of whether any citation is correct. An editor
opening the reference list reads internal deliberation and an admission of unfinished
work. No preflight check sees it — see R38 for why.

**REQUIRED ACTION.** Wrap the commentary in `not-for-submission` markers or move it
out of the assembled file, then rebuild and re-read the built References section.

**STATUS.** CONFIRMED.

---

### R26 — The built manuscript's Code and Data Availability section contains two draft alternatives, a note that says it does not belong, and six placeholders

**FINDING.** `CODE_AVAILABILITY.md` is assembled into `MANUSCRIPT.md` as shipped. It
contains two alternative draft statements labelled "Short version" and "Longer
version", an internal note whose own first sentence disclaims it, a second and
unfilled copy of the Data Availability statement, and six unfilled placeholders.

**EVIDENCE.** Verified directly:

```
2980: ## Short version (for the journal's Data Availability statement)
3010: ## Longer version (for the end of Methods)
3056: **not** intended for the manuscript; the corrected tables are already in
```

Placeholders present in `MANUSCRIPT.md`:

```
  62: <repository URL>      85: <repository URL>     2983: <repository URL>
2998: <citation>          2998: <source>             2998: <licence>
3005: <citation>          3012: <repository URL>
```

`tools/preflight.py`'s `check_placeholders()` reports two, because it reads only the
ten section files — see R38.

**IMPACT.** Severe, and of the same kind as R25: the assembled paper contains a passage
that states it is not part of the paper, beside unfilled tokens, in back matter a desk
editor reads. "ALL CHECKS PASS (20 of 20)" does not see any of it.

**REQUIRED ACTION.** Reduce `CODE_AVAILABILITY.md` to the one statement intended for
submission, or remove it from the build order.

**STATUS.** CONFIRMED.

---

### R27 — The three-review calibration claim is documented for one of the three reviews

**FINDING.** The paper states three times, and offers as "a statement that can actually
be checked", that none of the three most recent reviews treats probability calibration
as an evaluation dimension. The full-text search that substantiates it is recorded for
[S3] only.

**EVIDENCE.** `INTRODUCTION.md:62-69`, repeated at `RELATED_WORK.md:48-49` and
`RESEARCH_GAP.md:57-58`. The itemised search (zero occurrences of Brier, Platt,
isotonic, reliability diagram) is at `REFERENCES.md:274-290` and
`results/LITERATURE_NUMBERS.csv` rows 54-65, all sourced to the S3 DOI. The [S1] entry
(`REFERENCES.md:194-203`) and [S2] entry (`:205-220`) record nothing about calibration.

**IMPACT.** Two-thirds of a repeated, foundational research-gap claim rest on no
documented check — and the sentence immediately after it says the claim *was* verified
by full-text search, which a reader will read as covering all three.

**REQUIRED ACTION.** Run and record the same search for [S1] and [S2], or narrow the
sentence to what was actually checked.

**STATUS.** CONFIRMED (the documentation gap is confirmed; whether [S1]/[S2] in fact
discuss calibration cannot be determined from this repository).

---

### R28 — [C1]'s borrowed numbers are cited to the IEEE article and verified from the arXiv preprint

**FINDING.** Every figure attributed to Cui et al. [C1], including the class-balance
counts behind this paper's most direct comparison with prior work, was checked against
the preprint, not the version the reference entry cites.

**EVIDENCE.** `REFERENCES.md:155-158` cites *IEEE TNNLS*, doi 10.1109/TNNLS.2022.3147208.
`REFERENCES.md:160` and `:171-175` record verification from arxiv.org/abs/2107.09507
and arxiv.org/pdf/2107.09507, including the 2,952 / 1,731 / 1,221 counts and the
41.4 % / 58.6 % split used at `RELATED_WORK.md:118-126`.

**IMPACT.** Table numbering and figures can move between preprint and camera-ready.
Nothing here confirms the published version carries the same Table I.

**REQUIRED ACTION.** Check against IEEE Xplore, or cite the preprint alongside the DOI
and say the numbers come from it.

**STATUS.** PLAUSIBLE — cannot be resolved from the repository.

---

### R29 — Two literature claims about field practice carry no support

**FINDING.** (a) `DISCUSSION.md:456-459` asserts that reporting a single run "is the
common practice" in this literature, with no citation. (b) `RELATED_WORK.md:128-130`
and `RESEARCH_GAP.md:23-24` attribute to [S1, S2] the finding that reviewed studies
"frequently do not report their validation scheme in enough detail to tell"; neither
reference's verification note records this, and [S2]'s own note says its inclusion
criteria centre on behavioural indicators rather than EEG.

**EVIDENCE.** As cited. `REFERENCES.md:194-203` ([S1]) records screening counts and
accuracy figures only; `:205-220` ([S2]) records a risk-of-bias quote about
"inadequate validation strategies", which is a quality claim, not a reporting-detail
claim, and at `:218-220` explicitly directs the reader to cite [S1] for the
EEG-specific picture.

**IMPACT.** Both are negative or universal claims about a literature, stated as
established. They are the class of sentence a reviewer from that literature will
challenge first.

**REQUIRED ACTION.** Cite, or hedge to the authors' own reading.

**STATUS.** CONFIRMED that the support is not documented here; the underlying claims
may well be true.

---

### R30 — [S1] and [S2] borrowed numbers carry no page or table locator, where [S3] and [C1] do

**FINDING.** `results/LITERATURE_NUMBERS.csv` gives only a DOI as the source for the
[S1]/[S2] rows, while the same file demonstrates page- and table-level locators for
[S3] and [C1].

**EVIDENCE.** `results/LITERATURE_NUMBERS.csv` rows 2-10 and 43 (DOI only) against rows
49-65 ("table number of the dataset comparison table,3"; "page on which DD-Database is
described in body text,8") and rows 11-21.

**IMPACT.** Traceability gap, not a demonstrated error — no mismatch was found between
those rows and the manuscript text.

**REQUIRED ACTION.** Add page numbers for the S1/S2 headline figures, to the standard
the file already meets elsewhere.

**STATUS.** CONFIRMED (as a gap).

---

### R31 — REPRODUCIBILITY.md, the page written to stop stale claims, understates preflight by four checks

**FINDING.** `manuscript/REPRODUCIBILITY.md:117` says "Sixteen checks, one verdict" and
lists sixteen. `tools/preflight.py` runs twenty.

**EVIDENCE.** `REPRODUCIBILITY.md:117` and its §4 table (16 rows) against
`tools/preflight.py:5` ("Twenty separate checks") and its `main()` (20 entries). The
four absent from the table are `released scores`, `ranking invariance`, `table marks`
and `literature` — the four added between 19 and 24 September.

**IMPACT.** This page exists because "six reviews of this work have now each quoted at
least one sentence from a superseded draft". It is now itself the superseded draft, for
exactly the class of fact it was built to pin down.

**REQUIRED ACTION.** Regenerate §4's table from `preflight.py`'s docstring, by script
rather than by hand.

**STATUS.** CONFIRMED.

---

### R32 — The only test that exercises the training loop is never run by the gate that declares the paper green

**FINDING.** `tests/test_training_smoke.py` is the only test that runs real model builds
through `train_loso.run_one` and checks for train/validation/test leakage,
resume-safety and parameter-count fidelity. It defines zero `test_`-prefixed
functions, so `pytest tests/ -q` — the exact command preflight runs — never collects it.

**EVIDENCE.**

```
tests/test_pipeline.py:37
tests/test_training_smoke.py:0
37 tests collected in 1.06s
```

`tools/preflight.py:168` runs `[py, "-m", "pytest", "tests/", "-q"]`. `README.md:218-223`
and `REPRODUCIBILITY.md:121` both correctly describe it as a separate manual command,
so this is disclosed, not hidden.

**IMPACT.** A regression in the training loop — a leaked test subject, a broken
validation draw, a parameter-count drift — would not be caught by the automated gate.
The leakage guarantee is the one the paper most depends on and the one the gate does
not test.

**REQUIRED ACTION.** None strictly, since it is disclosed. Preflight could report
whether the smoke test has been run, as it already reports the two non-failing items.

**STATUS.** CONFIRMED as a coverage gap; NOT A DEFECT as a documentation matter.

---

### R33 — Arm A and Arm C window counts cannot be checked against anything released

**FINDING.** `results/raw_window_counts.csv` makes Arm B's per-subject drowsy counts
independently recomputable. Arms A and C are built from trimmed recordings, and no
released file gives post-trim counts; their totals are asserted by `config.ARMS` and
checked only against themselves.

**EVIDENCE.** Independent recomputation: `round(992 · n_drowsy_raw / n_total_raw)`
capped at `n_drowsy_raw`, applied to `results/raw_window_counts.csv`, reproduces Arm B's
`config.py:71-72` counts exactly for all ten subjects (67, 46, 163, 68, 47, 38, 239, 8,
5, 7). No equivalent is possible for A or C: `src/preprocess.py:258-300` compares a
fresh EDF rebuild against `config.ARMS`, and the EDF files are excluded by
`.gitignore:2`. `METHODOLOGY.md:120-122` asserts "trimming removes a further twelve,
leaving 770"; no shipped script computes that twelve.

**IMPACT.** Two of three arms — including Arm A, whose probability files are released
and whose calibration is advertised as recomputable — rest on counts a reader cannot
check from the bundle. This follows from not redistributing the recordings, which the
paper is honest about; it is a verifiability limit, not evidence of an error.

**REQUIRED ACTION.** Ship a `raw_window_counts_trimmed.csv`, or state plainly that A/C
counts are checkable only by rebuilding from the original recordings.

**STATUS.** CONFIRMED (as a gap).

---

### R34 — The Highlights bullet drops the precision qualifier the body treats as load-bearing

**FINDING.** Every statement of the recalibration-invariance claim says "unchanged at
the reported precision", a wording the paper explicitly defends against the stronger
"algebraically invariant". The Highlights bullet says "unchanged".

**EVIDENCE.** `ABSTRACT.md:61-62` (body, qualified) against `ABSTRACT.md:74`:
"- Recalibration closes the gap; subject-averaged ROC-AUC unchanged". The measured
change is 0.0000009981 (`results/ranking_invariance.csv`), i.e. nonzero.
`EXPERIMENTAL_SETUP.md:142-144`: *"The distinction is kept because the stronger claim is
false as implemented."* The bullet is 64 characters against an 85-character limit
(`ABSTRACT.md:199`), so there is room.

**IMPACT.** Highlights are read by people who read nothing else, and this one asserts
the claim the paper elsewhere calls false.

**REQUIRED ACTION.** Restore the qualifier in the bullet.

**STATUS.** CONFIRMED.

---

### R35 — The Conclusion drops the "pooled" qualifier on recall that every other section carries

**FINDING.** `CONCLUSION.md:54-55` states the headline accuracy-against-recall finding
with "recall" unqualified. Every other section says "pooled recall", because pooled and
subject-averaged recall differ by 0.13 to 0.25 here.

**EVIDENCE.** `CONCLUSION.md:54-55` against `ABSTRACT.md:52`, `RESULTS.md:390-392`,
`DISCUSSION.md:127`, `INTRODUCTION.md:146`, `RESEARCH_GAP.md:45` — all qualified.

**IMPACT.** A reader who reaches only the Conclusion cannot tell which convention is
meant, and §7.3.1 offers a subject-averaged recall table to misapply it to. (The
qualitative claim does survive under both conventions — established earlier — but the
sentence gives the reader no way to know that.)

**REQUIRED ACTION.** Name the convention, as every other section does.

**STATUS.** CONFIRMED.

---

### R36 — Table 5's pooled accuracy, recall and precision carry no dispersion, and one of them varies by 14.8 points

**FINDING.** Table 5 reports pooled accuracy, recall and precision as single numbers
averaged over five seeds. The adjacent §7.5 tables, computed by the same pooling
convention, carry ± seed SD. The hidden dispersion is large.

**EVIDENCE.** Reconstructed from `results/ALL_FOLDS.csv` and `results/ALL_POOLED.csv`
(accuracy = (N − D − FP + Σ recall·n_drowsy)/N). Every reconstructed mean reproduces its
printed Table 5 value exactly, which validates the reconstruction:

```
arm model            mean acc     seed SD    min        max        range
B   ShallowConvNet   81.8528 %    6.2246     70.8770    85.7157    14.8387
A   ShallowConvNet   83.1706 %    1.3482     81.6631    84.9676     3.3045
C   ShallowConvNet   82.1879 %    1.5394     80.6803    83.9741     3.2937
A   DeepConvNet      92.7300 %    0.4206     92.1922    93.1749     0.9827
C   DeepConvNet      93.5551 %    0.6850     92.6350    94.2333     1.5983
B   CNN              92.9980 %    0.8977     92.0363    94.3347     2.2984
```

The 70.88 % seed is seed 42, the same outlier the paper flags for Brier at
`RESULTS.md:62-63` ("one of the five seeds gives 0.2246 against about 0.11 for the
other four") without connecting it to Table 5.

**IMPACT.** Two consequences. A reader comparing architectures in Table 5 cannot see
that one architecture's number is not stable to within six points. And it bears
directly on R13: 1.0453 ± 0.4206 against 0.8229 ± 0.6850 means the two best margins
overlap, so no "largest margin" claim is supportable in either direction.

**REQUIRED ACTION.** Report seed dispersion for Table 5's pooled quantities, at least
where it is this large, and settle R13 against it.

**STATUS.** CONFIRMED.

---

### R37 — Preflight's placeholder and scan checks read ten files; the build assembles twelve

**FINDING.** `tools/preflight.py`'s `SECTIONS` constant lists the ten body sections.
`tools/build_manuscript.py`'s `ORDER` lists twelve. `CODE_AVAILABILITY.md` and
`REFERENCES.md` are assembled into the submitted document and are read by no
placeholder check and no unregistered-number scan.

**EVIDENCE.**

```
preflight SECTIONS: ABSTRACT, INTRODUCTION, RELATED_WORK, RESEARCH_GAP, METHODOLOGY,
                    ARCHITECTURES, EXPERIMENTAL_SETUP, RESULTS, DISCUSSION, CONCLUSION
build ORDER       : ... the same ten, plus CODE_AVAILABILITY.md, REFERENCES.md
```

**IMPACT.** This is the single structural cause of both R25 and R26, and it is why
"ALL CHECKS PASS (20 of 20)" coexists with six unfilled placeholders and a TODO list
inside the submitted document. It is the most consequential guard defect found: not a
check that failed, a check that was never pointed at the file.

**REQUIRED ACTION.** Derive `SECTIONS` from `build_manuscript.ORDER` rather than
restating it, so the two cannot diverge again.

**STATUS.** **CLOSED, 25 September 2026.**

`build_manuscript.py` now exports `SECTION_FILES`, derived from `ORDER`, and
`preflight.py` imports it instead of restating it. The scope is per check, because the
three scopes genuinely differ, and every difference is declared:

| Check | Files | Excluded |
|---|---|---|
| placeholders | 12 | none |
| withdrawn | 12 | none |
| scan | 11 | `REFERENCES.md` |

The one exclusion is `REFERENCES.md` from `scan` only, with the reason recorded in
`SCOPE_EXCLUSIONS`: its numbers are publication years, arXiv identifiers, DOI
fragments, page ranges and accuracies borrowed from other papers. They live in
`results/LITERATURE_NUMBERS.csv`, which `check_literature.py` gates, not in
`MASTER_NUMBERS.csv`, which this scan reads. Scanning it against the results registry
reports 22 unregistered numbers, all of which are correct. `CODE_AVAILABILITY.md`
scans clean at 0, so it needed no exclusion.

**The classification question was settled on evidence, not convenience.** Both files
are genuine manuscript sections: `REFERENCES.md` is the only source of the bibliography
anywhere in the repository, and `CODE_AVAILABILITY.md` holds the Data Availability
statement BSPC requires — its own first line reads "draft text for the manuscript".
Declaring either one an internal file and excluding it from audit would have left its
content in the assembled document while formally removing it from scope, which is the
R25/R26 hole written into the design. The internal material inside those two files is a
separate problem, with a mechanism already built for it: the
`<!-- not-for-submission:start/end -->` markers, used four times in `ABSTRACT.md` and
zero times in these two. That is R25 and R26, and no content was touched here.

**Three regression tests** in `tests/test_pipeline.py`, 40 tests now passing:

* `test_audit_scope_is_derived_from_the_builder_not_restated` — asserts
  `preflight.SECTIONS == build_manuscript.SECTION_FILES == [n for n, _ in ORDER]`, and
  names the two files whose omission was this finding.
* `test_every_audit_scope_exclusion_is_named_with_a_reason` — an exclusion must name a
  file the builder actually assembles and carry a reason, so a stale exclusion for a
  removed file fails rather than reading as if it were still being handled.
* `test_a_new_section_is_audited_without_anyone_remembering_to_add_it` — injects a
  section into `ORDER` and asserts it lands in every scope; then declares it excluded
  from one and asserts it leaves that scope and stays in the others.

Deliberately broken to confirm the guard bites. Reintroducing the hand-written
ten-file list in a scratch copy:

```
AssertionError: preflight.SECTIONS has drifted from build_manuscript.SECTION_FILES
  Right contains 2 more items, first extra item: 'CODE_AVAILABILITY.md'
AssertionError: scan excludes REFERENCES.md, which the builder does not assemble
2 failed, 1 passed
```

And the other direction — a thirteenth section added to `ORDER` alone, `preflight.py`
untouched:

```
placeholders  ATTENTION  (9 placeholder(s) in 13 assembled section(s))
    ZZ_NEW_SECTION.md:3  <author email>
```

**What the gate now says.** `ALL CHECKS PASS (20 of 20)`, and the placeholder line has
gone from 2 to 8:

```
placeholders  ATTENTION  (8 placeholder(s) in 12 assembled section(s))
    ABSTRACT.md:92  <repository URL>          ABSTRACT.md:115  <repository URL>
    CODE_AVAILABILITY.md:12  <repository URL>
    CODE_AVAILABILITY.md:27  <citation> <source> <licence>
    CODE_AVAILABILITY.md:34  <citation>
    CODE_AVAILABILITY.md:41  <repository URL>
```

The six that were invisible are now printed on every run. They still do not fail the
run, by design — a placeholder is a fact to act on, and the author may be about to fill
it in — but they can no longer pass unseen.

---

### R38 — The table-mark guard covers one table of eight

**FINDING.** `tools/check_table_marks.py` reads Table 7 only. Tables 5 and 6 both carry
emphasis defects (R19, R21) that the guard is the right shape to have caught.

**EVIDENCE.** `tools/check_table_marks.py:1` — *"Check that Table 7's bold marks are the
ones its caption's rule selects"*; line 47, line 81, line 100, all Table 7.
Preflight reports "0 discrepancy(ies)", truthfully, about Table 7.

**IMPACT.** A check named `table marks` in the preflight output reads as covering the
tables. It covers one of them.

**REQUIRED ACTION.** Extend it to every table that states a rule in its caption, and
make a table that bolds cells without stating a rule an error in itself.

**STATUS.** CONFIRMED.

---

### R39 — The two contrast tables show fifteen tests each and the text counts twenty

**FINDING.** The A → C and B → C tables print three metrics — ROC-AUC, PR-AUC and F1 —
so each shows 15 of its family's 20 paired tests. The balanced-accuracy column is absent
from both. The summary table beside them counts "significant tests of twenty", and the
headline results "seven of twenty" and "zero of twenty" are computed over all four
metrics. The omission is stated nowhere.

**EVIDENCE.** Tables at `RESULTS.md:234-240` and `:265-271`, each with headers
`| Model | ROC-AUC A → C | PR-AUC A → C | F1 A → C |` and five data rows — measured at
15 printed p-values each. Summary table at `RESULTS.md:275-278`, "Significant tests of
twenty". `stats.arm_contrast` is called over `("auc", "pr_auc", "bal_acc", "f1")`
(`registry.py:165`), so the families are 20. The word "balanced" does not occur between
`RESULTS.md:225` and `:290` outside the section headings, and both sections introduce
their table as being "on the ten subject-level differences" with no mention that a
metric is held back.

**IMPACT.** A reader who counts the cells gets fifteen and is told twenty, with nothing
to explain the difference. Ten of the forty arm-contrast tests are invisible, and they
are inside the two counts that carry the paper's design conclusion — "balancing is the
one that matters and trimming is not". The missing tests may well be the uninteresting
ones; a reader cannot tell, and that is the defect.

**RECONCILED, 25 September 2026.** All five questions answered against the code and the
registry, not the manuscript:

1. **Are the ten tests performed?** Yes, all ten. `stats.arm_contrast` is called over
   four metrics including `bal_acc`.
2. **Are all ten in the registry?** Yes, and every registry value matches the recomputed
   value exactly.
3. **Their p-values:**

```
A vs C  EEGNet          0.7084 -> 0.7176   +0.0092   p = 0.1055
A vs C  ShallowConvNet  0.7002 -> 0.6943   -0.0059   p = 0.4316
A vs C  CNN             0.6182 -> 0.5987   -0.0195   p = 0.0742
A vs C  DeepConvNet     0.6271 -> 0.6277   +0.0005   p = 0.4922
A vs C  CNN-BiLSTM      0.6962 -> 0.7142   +0.0180   p = 0.0039   significant
B vs C  EEGNet          0.7249 -> 0.7176   -0.0073   p = 0.7695
B vs C  ShallowConvNet  0.7060 -> 0.6943   -0.0117   p = 0.6250
B vs C  CNN             0.6010 -> 0.5987   -0.0023   p = 0.9102
B vs C  DeepConvNet     0.6213 -> 0.6277   +0.0064   p = 0.7695
B vs C  CNN-BiLSTM      0.7253 -> 0.7142   -0.0111   p = 0.9219
```

4. **Is "seven of twenty" computed over all four metrics?** Yes, and it is correct:

```
A vs C : all four metrics n=20 sig=7 | three shown metrics sig=6 | bal_acc alone sig=1
B vs C : all four metrics n=20 sig=0 | three shown metrics sig=0 | bal_acc alone sig=0
```

5. **So the count is right and the table is incomplete.** A reader counting significant
   cells in the visible table finds **six** and is told **seven**. The seventh is
   `A vs C, CNN-BiLSTM, balanced accuracy, p = 0.0039` — and that is the same
   architecture and the same contrast the paper's mechanism sentence already names
   ("DeepConvNet +0.0217 and CNN-BiLSTM +0.0259 in ROC-AUC, both significant"). The
   hidden cell **supports** the claim; it does not contradict it.

**REQUIRED ACTION.** Show the balanced-accuracy column in both tables. The count needs
no change, nothing in the science moves, and the 6-against-7 gap closes. The alternative
— a sentence saying the table shows three of the four metrics — leaves the reader unable
to verify the count they are given, so it is the weaker option.

**STATUS.** CONFIRMED, reconciled, action determined. Not applied.

---

## Summary

| | Count |
|---|---|
| Passes complete | 8 of 8 |
| Findings | 39 (R37 closed) |
| Confirmed by independent measurement in this pass | R13, R15, R16, R18, R19, R20, R21, R25, R26, R31, R32, R33, R36, R37, R38 |
| Re-confirmed blind, having already been found in Passes 1–3 | R1 (= multiplicity), R2 (= "four of twelve"), R7 (= "ROC-AUC unchanged") |
| Numbers found wrong in the manuscript | R2, R5, R13, R14, R15, R17 |
| Guard defects (a check that could not see the defect) | R37, R38, R16, R32 |

**Two findings are new in kind and were invisible to all twenty checks.** R25 and R26
are not errors in the science; they are the internal working notes and six unfilled
placeholders sitting inside the document that `REPRODUCIBILITY.md` calls "the only file
to review, cite or submit". R37 explains why no check saw them. Nothing in Passes 1–3
would ever have found these, because Passes 1–3 audited the numbers, and these are not
numbers.

**On cross-validation of the earlier passes.** Passes 5–8 were run without sight of
R1–R12 and under instruction to distrust every prior conclusion. They independently
re-derived R1, R2 and R7 from the source data. That is evidence the earlier register is
sound, not evidence it is complete — R13 through R38 are all new.

**One number is not yet settled.** Pass 4 counted roughly 175–181 nominal tests with 78
significant; Pass 8 counted 117 `p =` occurrences in `RESULTS.md` and 162 across the
manuscript. These are different counting rules, not a contradiction. R1 cannot be put to
sir with a number until one counting rule is fixed and applied once.
