# Re-audit triage — for Guide Sir

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

Eight passes, run under one rule: *do not trust any previous audit conclusion, guard,
checklist, or correction; verify against the current manuscript, registry, source data,
code, and released artifacts.* Passes 5–8 were run without sight of the Pass 1–3
register, and independently re-derived three of its findings from the raw data.

Thirty-eight findings. Nothing has been patched. The full record, with evidence for
each, is in `REAUDIT_FINDINGS.md`; this page is only the sort.

**The headline.** The paper's numbers are in good shape — six wrong numbers in a
manuscript of this size, all small, all traceable. What the audit actually found is
that the *submitted document* contains material that is not manuscript text at all, and
that the twenty-check gate cannot see it because it was never pointed at those two
files. `ALL CHECKS PASS (20 of 20)` is true and does not mean what it appears to mean.

---

## 🔴 Must fix before submission

Factual errors, and content that should not reach an editor. No scientific judgement
required — each has one correct answer.

### The two that would be noticed first

| | Finding | Where |
|---|---|---|
| **R25** | The References section of the built manuscript is the internal verification trail, ending in a section headed **"Still to add before submission"** | `MANUSCRIPT.md:3100`, `:3483` |
| **R26** | The Code and Data Availability section contains two draft alternatives ("Short version" / "Longer version"), a note whose own first sentence reads *"It is **not** intended for the manuscript"*, and six unfilled `<placeholder>` tokens | `MANUSCRIPT.md:2980`, `:3010`, `:3056`; placeholders at `:62 :85 :2983 :2998 ×3 :3005 :3012` |
| ~~**R37**~~ | ~~**Why neither was caught.** `preflight.SECTIONS` lists ten files. `build_manuscript.ORDER` assembles twelve.~~ **CLOSED 25 Sep** | `tools/preflight.py`, `tools/build_manuscript.py` |

**R37 is closed.** It was the cause, so it was fixed first. `preflight.SECTIONS` is now
derived from `build_manuscript.SECTION_FILES`; scopes are per check (placeholders 12,
withdrawn 12, scan 11) with the one exclusion declared by name and reason; three regression
tests guard it, and the guard was verified to fail when the ten-file list is reintroduced and
to pick up a thirteenth section automatically. The placeholder line has gone from 2 to 8 —
the six in `CODE_AVAILABILITY.md` are now printed on every run. **R25 and R26 remain open**;
their content was not touched, and the mechanism for them already exists in the builder
(`<!-- not-for-submission:start/end -->`, used four times in `ABSTRACT.md` and zero times in
those two files).

### Wrong numbers and wrong claims

| | Finding | Correct value |
|---|---|---|
| **R13** | "The largest / widest margin in the study" attributed to Arm C, in Results, Discussion **and** Conclusion | Arm A's margin is **+1.0453** pts; Arm C's is **+0.8229**. And with seed SD 0.4206 and 0.6850 they overlap — so neither arm can claim it |
| **R2** | "Four of the twelve reach the Wilcoxon floor" | **Five** do — Table 4 on the same page shows five cells at (10/10) |
| **R5** | "Eleven of twelve" survives in three places after being corrected in two | Includes the generator, `tools/master_file.py:178`, so it regenerates |
| **R17** | "The only one whose raw calibration was already below the reference" | Also true of Arm A CNN (0.0671 against reference 0.0762) |
| **R15** | "By more than an order of magnitude" (`DISCUSSION.md:499`) | One of fifteen ratios is **×5.63**. Fourteen exceed ×10; the claim is not universal |
| **R14** | §7.5.1 asserts exact agreement; EEGNet's Arm A Brier prints as 0.1010 and 0.1009 | Difference 8.09e-05, from two executions. §7.7 discloses this for PR-AUC and balanced accuracy but **omits Brier** — the one metric that disagrees |

### Claims stated more strongly than measured

| | Finding |
|---|---|
| **R7** | "ROC-AUC is unchanged on all three" asserts the null in Results. The Discussion already words the same comparison correctly. Point estimates moved 0.022 and 0.007 |
| **R34** | The Highlights bullet says "ROC-AUC unchanged", dropping the "at the reported precision" qualifier the paper explicitly defends. 64 characters against an 85-character limit — there is room |
| **R35** | The Conclusion says "recall" where every other section says "pooled recall". One word |
| **R18** | Figure 1 — the opening design figure — lists **accuracy, Brier score and expected calibration error** as "measured on every fold". `fold_metrics()` computes none of the three. The manuscript states the correct position at `MANUSCRIPT.md:1318-1321` |

### Figures, tables and guards

| | Finding |
|---|---|
| **R19** | Table 6's caption states "Bold marks a score above the reference". Table 6 contains no bold at all — and it is the table for the paper's self-described strongest replication |
| **R21** | Table 5 has exactly one bolded cell and no stated rule. That bold encodes R13, the claim that is false — so it must be settled with R13, not separately |
| **R16** | The released registry advertises CNN and CNN-BiLSTM as "50 of 50" reproduced. `repro.py` classifies both as never re-executed and actively refuses to report a verdict for them; the registry export undoes that |
| **R31** | `REPRODUCIBILITY.md` — the page written *because* "six reviews have each quoted at least one sentence from a superseded draft" — says "Sixteen checks". There are twenty |
| **R39** | The A → C and B → C tables print three metrics, so each shows 15 of its 20 tests, while the text counts "twenty". **Reconciled:** all ten balanced-accuracy tests were run, all ten are in the registry, every value matches, and "seven of twenty" is **correct**. But a reader counting significant cells finds six and is told seven. The seventh is A vs C, CNN-BiLSTM, balanced accuracy, p = 0.0039 — which *supports* the paper's own mechanism sentence. Show the column; do not change the count |
| **R38** | The `table marks` guard reads Table 7 only, of eight tables. It is the right shape to have caught R19 and R21 |
| **R3 / R9** | One Wilcoxon comparison has a tied subject, so its effective n is 9 and its floor is 2/2⁹ = 0.0039, not the 2/2¹⁰ that §6.5 states generically. The manuscript's 9/10 is right; the registry's 10/10 is wrong |

---

## 🟠 Scientific or editorial decision required

These have no single correct answer. Each changes how strongly a result can be stated,
and each needs your judgement before anything is written.

### R1 — Multiplicity. Enumerated, and a resolution is proposed.

**The denominator is settled: 190** distinct inferential comparisons, of which 82 reach
nominal p < 0.05. Counted twice independently — by executing every test family against the
released fold data, and by reconciling against `MASTER_NUMBERS.csv` — and the two agree
exactly. The earlier "175–181" was short by the 12 cross-arm ordering tests, whose p sits in
a registry row's *note* rather than in a row of its own, and did not subtract 3 duplicates.
The "117 / 162" were printed `p =` occurrences, not tests.

**Proposed resolution: exploratory framing, with per-family BH and BY as sensitivity
analyses, not as the decision rule.** Full argument in `R1_DECISION_NOTE.md`; the three
numbers that decide it:

| Analysis set | Tests | nominal | BH | BY |
|---|---|---|---|---|
| All registered comparisons | 190 | 82 | 57 | 24 |
| Drowsy-count / prevalence family | 45 | 32 | 32 | 30 |
| Remaining comparisons | 145 | 50 | 22 | **0** |

Two measured constraints rule out correction as the primary criterion. **Holm** cannot
reject anything in a Wilcoxon family of 26 or more ten-subject comparisons, because the
smallest attainable p is 1/512 and α/26 = 1/520 is below it. **BY** over one family of 190
keeps 24, and **all 24 are from the prevalence family** — every architecture comparison, arm
contrast, calibration and threshold result falls. That is a reductio about n = 10, not a
verdict on the findings; but it does mean the paper cannot claim its results survive
arbitrary-dependence control, and should not try.

**Sir's decision is needed on the family boundary and the correction policy.** The
denominator is not a judgement call; those two are.

### R4 — "The strongest replication in the study"

The Brier partition holds on all three arms **when the five seeds are averaged**. On
individual seeds it holds on all three arms simultaneously in only 1 of 5, and 6 of 75
runs flip. The sentence's grammatical scope may imply per-seed robustness it does not
have. Decision: re-scope the sentence, or report the per-seed figure alongside it.

### R36 — Whether Table 5 should carry seed dispersion

Adding ± to Table 5 is honest and also changes the story. ShallowConvNet on Arm B is
**81.85 % ± 6.22**, ranging 70.88 % to 85.72 % — one seed accounts for most of the gap
that makes it look reliably worst. And the same dispersion is what dissolves R13's
superlative. Related: **R20**, the Brier column in the §7.5 tables has no ± while the
three columns beside it do, and the SDs are already in the registry.

### Literature claims that are plausible but undocumented

| | Finding | Decision |
|---|---|---|
| **R27** | "None of the three most recent reviews treats calibration as an evaluation dimension" — the full-text search is recorded for [S3] only, yet the next sentence says it was verified by full-text search | Run the search for [S1] and [S2], or narrow the claim to what was checked |
| **R29** | "Single-run reporting **is the common practice**" (uncited); and a reporting-detail finding attributed to [S1, S2] that neither entry's verification note supports | Cite, or hedge to our own reading |
| **R28** | [C1]'s numbers are cited to the IEEE version and were verified from the arXiv preprint | Re-check against IEEE Xplore, or cite the preprint alongside |

### Carried from Passes 1–3, still open

**R6** — the ranking-invariance claim is scoped in Results and unscoped in five other
places. **R8** — the one table that withholds p-values is the one where a bare ρ
misleads most. **R10** — a third dispersion convention is used but never declared.

---

## 🟢 Documented limitation — no manuscript change required

Real, worth knowing, already honest or genuinely minor.

| | Finding | Why it can stand |
|---|---|---|
| **R33** | Arm A and Arm C window counts are not checkable from any released file; only Arm B is (and Arm B's recompute **exactly** — all ten subjects) | Consequence of not redistributing the recordings, which the paper is honest about. Could be closed by shipping a trimmed counts CSV |
| **R32** | `tests/test_training_smoke.py` defines zero `test_` functions, so the 37-test gate never runs it — and it is the only test that checks the training loop for leakage | Fully disclosed in both README and REPRODUCIBILITY.md as a separate manual command. A coverage gap, not a false claim |
| **R30** | [S1] / [S2] borrowed numbers carry a DOI but no page or table locator, where [S3] and [C1] do | Traceability gap; no numeric mismatch found |
| **R24** | Figure S1 panel (h) does not state its estimator convention, though the panels either side of it do — and it is subject-averaged, unlike them | One caption clause |
| **R23** | Figure 2 prints p to three decimals; the text prints the same p to four | Cosmetic, though 0.0167 is a floor value where the digits carry meaning |
| **R22** | Table 8 bolds "not run" in one cell and not in an identical one | Cosmetic |
| **R11, R12** | Two wording items and one code-hygiene item with no current effect | As recorded |

---

## What the audit did *not* find

Worth stating, because it is most of the paper.

Passes 1 and 3 came back clean on numerical integrity and on protocol and leakage, and
Pass 7 re-checked the second of those independently: `train_loso.py` and `calibrate.py`
fit out-of-subject correctly, and `repro.py` actively excludes carried-over files rather
than reporting a fabricated reproduction. Seeding is honest — no GPU determinism is
claimed, and `README.md:272-273` says so in as many words. `ALL_FOLDS.csv` holds exactly
750 folds, 250 per arm; `ALL_POOLED.csv` holds 75; `run_all.py --from aggregate` runs in
about thirteen seconds and leaves both byte-identical. Every Table 4 subject-averaged
ROC-AUC, all twelve EEGNet Wilcoxon p-values and win counts, the three capacity
correlations, the three accuracy-against-recall correlations, the Table 6 Brier margins,
Table 1's window arithmetic, Table 3's parameter counts and the Platt-invariance figures
were all recomputed from the released data and matched.

Six numbers wrong out of a manuscript this size is a good result. The problem is not
the arithmetic; it is the two files nobody was checking.

---

## Order — where we are

1. ~~**R37** — the structural cause.~~ **Done.** Scope derived from the builder, per-check,
   three regression tests, guard verified in both directions.
2. ~~**R1's denominator** — one counting rule, applied once.~~ **Done.** 190, counted twice
   independently. Enumeration in `R1_TEST_INVENTORY.md`, decision note in
   `R1_DECISION_NOTE.md`.
3. **R1's family boundary and correction policy** — *awaiting sir*. Nothing downstream can be
   written until this is settled, because R3/R9, R7, R4, R34 and the Pass-8 verbs all change
   with it.
4. Then **R25, R26** — the working notes and six placeholders inside the assembled document.
   R37 made them visible; the builder already has the mechanism to strip them.
5. Then the wrong numbers as a batch: **R13 + R21** together, **R2, R5, R14, R15, R17**, and
   **R39** (show the balanced-accuracy column; the count is right).
6. **R31, R38, R16** — the remaining guards — last, each fixed so it cannot recur.

**Nothing in the manuscript has been changed.** Baseline preserved: 40 tests pass, 20 of 20
preflight checks pass. The multiplicity numbers above came from a scratch script outside the
repository; no `MULTIPLICITY.csv` and no multiplicity tool have been added, because the tool
would have to be rewritten once the policy is settled.

Once it is settled, the implementation is one synchronized pass — registry → multiplicity
tool → `MULTIPLICITY.csv` → manuscript tables → preflight gate, and Abstract → Methods →
Results → Discussion → Conclusion → tables and captions in a single sweep, never a
find-and-replace on "significant".

---

## Implemented, 25 September 2026

Sir approved the recommendation, and it was carried out in one synchronized pass.
`45 tests pass, 21 of 21 preflight checks pass.`

**The multiplicity decision (R1).** `src/multiplicity.py` enumerates the twelve
families and writes `results/MULTIPLICITY.csv`; 70 registry rows carry every number
the section cites; §6.5.1 declares α = 0.05, the 190-comparison universe and the
exploratory framing; §7.10 gives the per-family BH and BY table with the 82 = 32 + 50
split and states plainly that under one-family BY all 24 survivors come from the
prevalence family. A 21st preflight check re-runs the table, re-derives the Holm
ceilings in exact rational arithmetic, and fails if a one-family BY survivor ever
comes from outside that family.

**Closed with it:** R3/R9 (ties — found to affect 21 comparisons, not one; `paired`
and `arm_contrast` now carry `ties`, `n_effective` and `p_floor`, and the registry
note that derived `b_wins` as `n - a_wins` is fixed), R39 (both contrast tables now
generated at four metrics, so seven significant cells are visible where the text says
seven), R13 (the superlative moved to the true claim — highest accuracy, not widest
margin), R2 (five, not four), R5 (leads in all twelve, reaches the level in eleven),
R7, R14 (Brier added to the two-execution disclosure), R15, R17, R19, R21, R22, R34,
R35, R4 (scoped to the seed-averaged aggregation), R16 (carried-over files no longer
advertised as reproduced), R31 (the status page is now tested against preflight),
R38 (the mark guard now checks every captioned table), and **R25 and R26** — the
working notes and draft alternatives are stripped from the assembled document by the
markers the builder already had.

**Still open:** R20 and R36 (dispersion on the Brier and pooled-accuracy columns),
R6, R8, R10, R11, R12, R18, R23, R24, R27–R30, R32, R33, R37-adjacent guard work, and
the three author decisions.

---

## R20 + R36, 25 September 2026

`48 tests pass, 21 of 21 preflight checks pass.`

No new dispersion convention was invented: Section 7.5 already reported "± the seed
SD", and these two findings were that three columns did not follow it. The Brier
column of all three per-arm tables now carries the SD that was already in the
registry, and Table 5's recall and accuracy carry a seed SD computed by
`stats.pooled_confusion_spread`, which is new. Every mean is unchanged.

**The pass turned up something the finding did not anticipate.** R36 asked for ± on
accuracy, recall *and* precision. A test written to assert that adding dispersion
moves no reported value failed on precision, and the reason is that precision is a
ratio of two varying quantities: the mean of the five seeds' precisions is not the
precision read off the seed-mean counts. They differ at the third decimal for
fourteen of the fifteen rows and by up to 0.0227. Putting ± on the printed precision
would have placed an interval around a centre other than the one printed. Precision
therefore carries no ±, the caption says why, and a test pins the fourteen and the
0.0227 so the explanation cannot outlive the fact.

**Still open:** R6, R8, R10, R11, R12, R18, R23, R24, R27-R30, R32, R33, guards, and
the three author decisions.

---

## R6 / R8 / R10 / R11 / R12 / R18 / R23 / R24, 25 September 2026

`48 tests pass, 21 of 21 preflight checks pass.` Verified first, patched second. All
eight were still valid against the current text, and **none moved a numerical
result.**

**R12** — `subject_count_correlation` now goes through `stats.spearman`. Identical
output at n = 10; the point was that it was the last family bypassing the wrapper.
**R18** — Figure 1's closing line claimed eight metrics are measured per fold.
`fold_metrics` returns six. It now reads *"Measured on every fold: ROC-AUC · PR-AUC ·
recall · F1 · balanced accuracy · precision"* and, on a second line, *"Derived
afterwards, pooled or from the probability files: accuracy · Brier score · expected
calibration error"*. **R23** — Figure 2 prints p to four decimals, matching the text.
**R24** — Figure S1 panel (h) states that it is subject-averaged, unlike the pooled
panels on either side of it.

**R8** — the cross-arm ordering table was the only correlation table in the paper
without p-values, under a sentence calling the ordering "not arbitrary". It now
carries all twelve, and the paragraph says what they show: nine of the twelve do not
reach the nominal level, and only the three F1 rows separate, by landing on the
0.0167 floor. A prerequisite surfaced on the way: `src/scan.py` reads registry
*values* and not *notes*, and these twelve p-values lived only in notes — so they
could not have been printed at all until they were registered as values.

**R6** — the ranking-invariance claim is scoped in all four remaining places. It is a
measurement on three architectures on Arm A: three of the fifteen architecture-by-arm
cells Table 4 reports. Scoping the Abstract pushed it to 257 words against a 250
limit, so that paragraph was tightened; it now stands at 248.

**R10** — the fifty-fold standard deviation used for selected thresholds is declared
in §6.5 as the third convention and named again at the table, with the reason it is
not comparable to the other two. **R11** — "parameter count does not predict ranking
quality" is now withdrawn as unsupported rather than refuted, with the reason that
five points cannot settle it either way; the "highest corrected correlation" is
reported as one of two tied at +0.9152; and the Platt uniqueness claim is narrowed to
"improved on neither metric", the CNN having failed only on calibration error at
p = 0.0840.

**Still open:** R27-R30 (literature verification, which needs sources rather than
wording), R32, R33, and the three author decisions.

---

## R27 / R28 / R29 / R30, 25 September 2026

`48 tests pass, 21 of 21 preflight checks pass.` These four needed sources, not
wording, so the two review full texts were retrieved and searched before anything was
changed.

**R27 — the claim holds, and is now stronger than it was written.** Both [S1]
(*Cognitive Neurodynamics*, via Springer) and [S2] (*Archives of Academic Emergency
Medicine*, via PMC) were searched in full text. *Brier*, *probability calibration*,
*Platt*, *isotonic*, *expected calibration error* and *reliability diagram* occur in
neither. With [S3] already checked, the three-review claim now rests on a search of
all three rather than of one, and the hedge "the most recent of them does not mention
it at all" has been replaced by what is now known: none of the three does.

**R29 — one half survived the check and one half did not.**
The validation-reporting claim was attributed to [S1, S2]. [S2] supports it, in its
own words: *"incomplete reporting in several studies, including missing details on
sample characteristics, annotation methods, and validation schemes restricts the
reliability of cross-study synthesis."* **[S1] makes no such statement.** Both places
now attribute it to [S2] alone and quote it.
The claim that single-run reporting "is the common practice" is supported by
**neither** review — neither discusses repeated runs at all. It is removed, and the
Discussion now says plainly that how often such comparisons rest on a single run is
not something this paper can establish.

**A scope problem surfaced while checking.** [S2] excludes "vehicle telemetry,
physiological signals without behavioral imaging" — it is a review of behavioural
indicators, not of EEG. Its own entry already carried that caveat, but the Research
Gap counted it among reviews of "this field". Both places now say which two review
this field directly and why the third is cited.

**R28 — cannot be closed as asked, and now says so.** The published IEEE article is
paywalled and was not retrievable. The five accuracy figures are verbatim in the
abstract of arXiv v4, dated 18 February 2022, which postdates the journal DOI and is
therefore very probably the accepted version — strong evidence, not a check of the
published article. The entry now instructs citing the preprint alongside the DOI and
says which numbers were read from where.

**R30 — closed.** Every [S1] and [S2] row in `LITERATURE_NUMBERS.csv` now carries a
verbatim locator quote from the full text, which is better than a page number for
articles paginated by article ID.

**Still open:** R32, R33, and the three author decisions.

---

## R32 / R33, 25 September 2026

`48 tests pass, 1 skipped (visibly), 21 of 21 preflight checks pass.`

**R32 — the gap is closed rather than disclosed.** `tests/test_training_smoke.py` is
the only test that runs real model builds through `train_loso.run_one` and checks
that a held-out subject never appears in its own fold's training or validation split,
that every architecture builds at the study's parameter count, and that a resumed run
does not shift the validation draw. It defined no `test_`-prefixed function, so
`pytest tests/` — the command preflight runs to decide whether the paper is green —
collected none of it. It now has a pytest entry point that runs when TensorFlow and
the ARL reference implementation are present and **skips visibly** when they are not,
and preflight prints the skip rather than folding it into a count:

```
tests              PASS  (48 passed, 1 SKIPPED -- see below)
    SKIPPED [1] tests/test_training_smoke.py:174: TensorFlow or the ARL reference
    implementation is not installed; see README for how to run this test
```

A disclosed gap in the leakage check was still a gap in the leakage check. Now the
gate either runs it or says out loud that it did not.

**R33 — closed as far as it can be, and stated plainly where it cannot.** Arm B is
independently verifiable from the released `raw_window_counts.csv`; Arms A and C are
built from trimmed recordings whose post-trim counts were in no released file, so
their totals could be checked only against `config.ARMS`, which is where they came
from. `src/preprocess.py` now writes `window_counts_arm_<X>.csv` on every arm build,
before the save gate and whether or not the reference check passes, so a rebuild from
the recordings produces the missing file. For a reader holding only the released
bundle the gap cannot be closed, because the recordings are not redistributed, and
both `results/README.md` and Methodology §4.3 now say so: the Table 1 check covers
Arm B and no other arm, and Arm A's "further twelve" is stated so a rebuild can be
checked against it rather than presented as something the bundle verifies.

**Remaining:** the complete scientific audit, then figures/tables/numbers/claims
final verification, then references. The three author decisions are parked until
submission preparation.

---

## Audit on build bd18ebaae5ce, 25 September 2026

An independent audit of the snapshot returned PASS on build integrity, numerical
integrity, fold structure, LOSO leakage, Spearman, multiplicity, figures, provenance,
Table 5, Brier and calibration, and the literature registry. Four items came back, and
three were acted on.

**Acted on — the ranking-invariance scope.** §7.6 stated the result as "for the three
architectures with released probability scores" without naming the arm, and the
Figure 5 caption attached the invariance sentence directly after enumerating the
architectures shown on all three constructions. Both now say Arm A, and §7.6 adds that
this is three of the fifteen architecture-by-arm cells Table 4 reports and that the
property is untested elsewhere rather than established.

*One correction to the audit's reasoning, which does not change its conclusion.* The
audit read the 150 Platt fits as 3 architectures × 3 arms × 5 seeds × 10 subjects. It
is 3 architectures × 5 seeds × 10 subjects **on Arm A alone**, and §7.6 already said
so ("on Arm A, the arm whose per-window scores are released, all 150 fitted slopes are
positive"). The sentence that needed scoping was the one stating the *result*, not the
one stating the slopes.

**Acted on — the threshold mechanism.** "Threshold selection helps exactly when the
scores are stably offset" read as a general rule derived from one case. It now says
what was measured: effective in one case, and that case is the one with a stable
offset; that it rests on twenty-four comparisons of which seven reach the nominal level
and none survives either correction; and that a threshold below 0.5 locates a useful
cut without establishing under-confidence, which this section does not measure. The
section heading changed from "helps only where" to "where threshold selection helped".

**Acted on — this folder.** These records were sitting beside the manuscript sources,
where their frozen counts ("40 tests pass", "20 of 20 checks") were read as current
status. They are now in `manuscript/audit-history/`, each carrying a banner, with a
README stating where current status actually lives.

**Not acted on, by agreement — the submission blockers.** The `<repository URL>`,
`<citation>`, `<source>` and `<licence>` placeholders and the CRediT confirmation are
author decisions, parked until submission preparation. Preflight prints all eight
placeholders and all three pending decisions on every run, so they cannot be forgotten.

---

## Audit on build 112fcddaa05c, 25 September 2026

The audit returned PASS on every area it examined — build synchronisation, registry,
750 folds, dataset constructions, LOSO structure and leakage, Spearman, multiplicity,
Figures 2 and 5, Platt ranking invariance, threshold analysis, calibration, literature
registry, preflight and tests — and confirmed that the two action items from the
previous build are closed. It raised two minor items, both acted on.

**The RuntimeWarning.** `stats.recall_conventions` divided by a zero drowsy count on
synthetic test folds, returned nan, and printed `invalid value encountered in scalar
divide` on every run of the suite. The auditor's instinct was right: guard the case,
do not suppress the warning. Pooled recall weights each fold by its drowsy count and
is genuinely undefined when that total is zero, so it now returns nan deliberately
and emits nothing. That cannot happen on this study's data — every subject
contributes at least five drowsy windows — which is exactly why the warning was easy
to ignore, and why a warning nobody acts on hides the next one. A test builds the
degenerate case, runs it under `warnings.simplefilter("error")`, and fails on any
warning at all. Suite: 49 passed, 1 skipped, no warnings.

**"Attributable to the scale of the scores."** Causal wording for two measurements
set side by side, and the ranking half of the pair was measured on Arm A only. The
sentence now says the gap is *associated with* scale rather than with a material
change in ordering, states that this holds for the Arm A cells where ranking
invariance was directly measured and only there, and ends by saying plainly that
recalibration was not an intervention on ordering — so this is an inference from two
measurements, not a demonstration.

**Unchanged, by agreement:** the repository, citation, source and licence
placeholders, and the CRediT confirmation. Preflight prints all of them on every run.

---

## Figure 6, and an architecture description that was wrong

Added 25 September 2026, after a hand-drawn draft of an architecture diagram was
checked against the code.

**The draft found a real error in the manuscript.** Section 5.3 described the
CNN-BiLSTM's LSTM layers as using "recurrent dropout 0.4". The code passes Keras's
`dropout` argument and never sets `recurrent_dropout` anywhere:

```
=== is recurrent_dropout used anywhere in the code? ===
   NOT PRESENT anywhere in the code

L.Bidirectional(L.LSTM(64, return_sequences=True, dropout=0.4)),
L.Bidirectional(L.LSTM(32, dropout=0.4))
```

The two are separate arguments — one drops the layer's inputs, the other its
recurrent connections — so a reader reimplementing from the paper would have built a
different model. This is a reproducibility error, not a wording preference, and it
survived every check because nothing compared the prose with the code.

**The draft also contained a structural error of its own**, inherited from a
misreading rather than from the manuscript: it flattened the three convolution blocks
into one convolution stack followed by a single pooling, normalisation and dropout.
The trunk has three blocks, each with its own pooling, so the time axis runs
1,280 → 640 → 320 → 160 and not 1,280 → 640. Section 5.3 had this right.

**Both are the same failure: the architecture was written down three times.** In the
builders, in the prose, and in the diagram — and three copies drift. `src/models.py`
now holds the layers as data (`CONV_TRUNK`, `RECURRENT_BLOCK`, `HEAD`); the builders
construct from them, Figure 6 draws from them, and
`test_the_architectures_section_describes_the_model_the_code_builds` fails if the
prose disagrees. Verified by reintroducing the error, which produced:

```
AssertionError: assert 'dropout 0.4 on its inputs' in '# 5 Architectures ...'
```

**On the diagram itself.** The draft was made in draw.io. The layout was sound and
was used as the design reference, but the asset is generated rather than drawn,
because a hand-drawn figure is a place where numbers are typed and nothing checks
them — the same class of drift as the stale Figure 2 and the stale registry earlier
in this audit. Figure 6 is now drawn by `src/figures.py`, redrawn by preflight with
the other six, and covered by the provenance check. Preflight expects seven figures.

---

## The CNN-BiLSTM parameter count, checked

Raised 25 September 2026 as a red finding: an independent recomputation of the
CNN-BiLSTM gave 184,737 against the registered 180,641, a difference of exactly
4,096. Checked from the layer spec rather than assumed either way.

**The registered number is right.** Recomputed from `src/models.py`'s tuples:

```
trunk trainable              36384
BiLSTM 64  (from 128)        98816   -> 128 features
BiLSTM 32  (from 128)        41216   ->  64 features
Dense 64   (from  64)         4160
Dense 1    (from  64)           65
CNN-BiLSTM TOTAL            180641   config says 180641   MATCH
CNN TOTAL                    44705   config says  44705   MATCH
difference                  135936
```

**Where the 4,096 came from.** The trunk figure (36,384) and the recurrent block
(140,032) in the independent check were both correct. The head was not: it used the
CNN's head for both models. The two models end in the same HEAD *tuple*, but that is
the same layer definition and not the same parameter count — the CNN's `Dense(64)`
receives 128 features from global average pooling over 128 channels, while the
CNN-BiLSTM's receives 64, being the second bidirectional layer's 32 units in each
direction. (128 − 64) × 64 = 4,096, which is the discrepancy exactly.

**What was nevertheless wrong, and is now fixed.** `config.PARAMS` held these counts
as a typed dict. They were correct, but nothing derived them, which is why settling a
4,096 discrepancy took a full recomputation. `models.trainable_parameters()` now
computes them from the same tuples the builders construct from, and a test asserts
`config.PARAMS` against it — including that a reference implementation raises rather
than guessing, since EEGNet, ShallowConvNet and DeepConvNet have no spec in this
file and their counts are measured. Section 5.3 now also says why the two heads
differ, so the next person recomputing them does not repeat the same step.

**Status:** not a defect in the paper. A defect in how the paper's numbers could be
checked, now closed.

---

## The capacity ratio, 25 September 2026

Raised as a red finding on build bb96afbacacc, and correct.

Three places stated that the recurrent block's 135,936 added parameters were "four
times the CNN's total". They are not:

```
added / CNN  = 135936 / 44705 = 3.0407
total / CNN  = 180641 / 44705 = 4.0407
```

The four-times figure belongs to the CNN-BiLSTM's **total**, not to what the block
adds. Wrong at `RESULTS.md:336`, `RELATED_WORK.md:80` and in `tools/master_file.py`,
which put it into the generated `MASTER_FILE.md`. `RESULTS.md:310` said "four times
as many" of the total and was right, but read ambiguously beside the added figure in
the same sentence. `DISCUSSION.md:89` already had the distinction right, at "three
times" and "four times".

All five now say 3.04 and 4.04, and the generator computes both by division instead
of asserting an adjective. Both ratios are registry rows, so `scan.py` checks them
like any other number.

**This is the same failure as the parameter counts, one layer up.** The counts were
right and derived; the arithmetic *on top of* them was typed. A test now asserts both
ratios from `config.PARAMS` and fails if "four times the CNN" reappears anywhere the
added figure is quoted. 52 tests pass.

Nothing about the models, the training or the results changed. What changed is that a
reader can no longer be told the added capacity is a third larger than it is.

---

## The snapshot itself, 25 September 2026

The audit of ad5c8355ad83 closed the capacity-ratio finding and raised a limitation:
`tools/master_file.py` and the test sources were not in the bundle, so the generator
that had just been corrected could not be read, only its output.

That is the third time a hand-assembled snapshot has been short of what the audit of
it then needed. The first paired a Figure 2 and a registry from different days and
produced two false findings. The fourth left out `src/models.py`, so the parameter
counts had to be checked against the layers as described rather than as built, and
the check came out 4,096 high. Now the generators and the tests.

**Curating a bundle by hand is the same failure as typing a number by hand**, and it
is the one failure this project has spent a week removing everywhere else. It is now
`tools/snapshot.py`: one declared list, stamped with the manuscript's own build id,
with this build's preflight and test output captured at the moment of packing rather
than quoted. It carries the whole of `src/`, `tools/` and `tests/` — so a claim about
a number, a claim about a check, and a claim about what the suite asserts can each be
read at its source — plus the manuscript, the registry, every released table, all
seven figures and the audit history. 73 files.

A test asserts that `src`, `tools` and `tests` are in the declared set and that the
data files an audit starts from are too, so the bundle cannot quietly shrink again.

The raw recordings are still absent and still not redistributable; `results/README.md`
says which window counts that leaves checkable and which it does not.

**And one thing the script exposed on its first run.** Packing it twice gave the same
filename with different contents. The build id is a digest of the assembled
*manuscript body*, so it does not move when a tool, a test or the packing script
changes — right for the paper, wrong for the bundle, and precisely the ambiguity the
build id was introduced to remove, reappearing one level up. Every snapshot now
carries a SNAPSHOT ID as well, a digest over every file packed, and the zip is named
by both. Cite the build id when you mean the paper; cite the snapshot id when you
mean the set of files you audited.

---

## The fourth pre-submission item, 25 September 2026

The audit of snapshot 869a900ec261 closed the snapshot limitation and named something
that was being carried in conversation rather than anywhere a tool would look: the
training smoke test skips wherever TensorFlow is absent, and a skip is not a pass.

It is now tracked like the three author decisions, and as a real check rather than a
reminder. A pass writes `results/smoke_test_passed.txt` with its own time and the
modification times of `src/train_loso.py`, `src/models.py` and `config.py`;
`tools/check_submission_ready.py` reads that record and reports the item PENDING
again if any of the three has changed since. A pass recorded before the last change
to the training loop is no evidence about the code being submitted, and now nothing
has to remember that.

```
decisions          ATTENTION  (4 of 4 pre-submission item(s) still open)
    repository     PENDING
    CRediT roles   PENDING
    licence        PENDING
    training smoke PENDING
```

`DECISION_SHEET.md` carries it as item 4, with the command to run. Its own stale
line — "fifteen checks, one verdict" against the twenty-one there now — was removed
rather than updated: the count has changed four times, and a number restated in two
places is a number that will disagree with itself.

