# Step 3 — scientific and technical check

> **Historical audit record — not current manuscript status.**
> Written during the audit it describes, and deliberately left as written. Counts of
> tests and checks, and statements such as "nothing has been written into the
> manuscript", were true on the date of the entry and are not true now: findings
> recorded here have since been acted on. For the current state read
> `manuscript/MANUSCRIPT.md` and its build stamp, and `results/MASTER_NUMBERS.csv`.
> The register below is evidence of what was found and when, not a status page.

*24 September 2026, against the current build.*

> **All twenty findings were fixed on 24 September 2026**, on your instruction, together with F11
> and F16 because the same edits touched them. Each fixed finding is marked **FIXED**
> below with what was changed. **Passing preflight is not scientific approval** —
> it means today's guards pass; the audit has to be re-run now that the findings
> are closed. **Passing preflight is not scientific approval** — it means
> today's guards pass; the audit has to be re-run once the remaining findings close.

Every finding below was re-derived from the released data or the code, not taken on
anyone's word. Where a finding needs the author's judgement rather than arithmetic,
it says so.

---

## What was checked, and what came back clean

| Area | Verdict |
|---|---|
| Dataset numbers and arm arithmetic | **clean** — re-derived from source |
| LOSO protocol and leakage | **clean** — verified on all 750 folds |
| Metric definitions | clean; the *conventions* are not (F7, F12) |
| Statistical tests | clean since the exact-p change; two claims built on them are not (F10) |
| Claims against evidence | **7 findings** |
| References and citations | **1 finding**, plus minor items |
| Reproducibility statements | **4 findings** |

**Dataset arithmetic.** Re-derived every arm from `results/raw_window_counts.csv`
and `config.py`: 926 × 10 = 9,260 and 992 × 10 = 9,920; the per-subject drowsy
counts sum to 770, 688 and 673 exactly; prevalences 8.3153 %, 6.9355 %, 7.2678 %.
Arm B, the untrimmed arm, matches the raw per-subject counts under the proportional
rule for all ten subjects. Arms A and C do not — **and that is the correct result**,
because they are trimmed; §4.3 already explains it (782 drowsy windows survive
overlap removal, trimming removes a further twelve to give 770). The check
confirms the trimming story rather than contradicting it.

**LOSO.** On all 750 folds: every subject is held out exactly once in each of the
75 (arm, model, seed) groups; **no fold has its test subject in its own validation
set**; every validation set has exactly 2 subjects, leaving 7 for training. The code
path matches (`train_loso.py:116-126`): the test subject is excluded from the
training pool before validation subjects are drawn from it.

---

## HIGH — these would be caught by a reviewer

### F1. **FIXED** — A claim the paper formally withdrew is live in the Results summary

`manuscript/RESULTS.md:976-977`

> "(DeepConvNet, 93.56 %) misses 338 of 673 drowsy windows and **is beaten on every
> metric in this paper by EEGNet**, 4.1 accuracy points lower"

`WITHDRAWN.md:47` retires exactly this claim, and §7.3 retracts it in the paper's own
words at `RESULTS.md:398-402`: *"It is not beaten on all of them… An earlier draft
said it was 'beaten on every metric reported in this paper', which was false on both
counts."* On Arm C, DeepConvNet beats EEGNet on pooled Brier (0.0511 against 0.0952)
and on pooled precision (0.564 against 0.390).

**The systemic part is worse than the sentence.** `check_withdrawn.py` matches
literal strings. The retired phrase is *"beaten on every metric **reported** in this
paper"*; the live claim drops one word. The checker reports the file clean. **Any
paraphrase of a withdrawn claim escapes the guard**, so the guard is weaker than the
repository believes it to be.

### F2. **FIXED** — `results/README.md` says the probability files are not released. Fifteen are.

`results/README.md:42-46`

> "## Not released — The per-window probability files (`probs_*.npz`) are too large
> to ship."

`ls results/A/probs_*.npz` → **15 files, 3.3 MB**. The top-level `README.md:295-298`
says the opposite and *records that it was corrected for precisely this reason*.
`results/README.md` is the uncorrected copy, still shipped in the release.

### F3. **FIXED** — The code-availability statement contradicts itself, and both halves are submitted

`manuscript/CODE_AVAILABILITY.md` line 19 against line 44:

> line 19: "**The per-window probability files are released for Arm A only** (15
> files, 3.2 MB…)"
> line 44: "The per-window probability files those two analyses were computed from
> **are not released**…"

Line 19 is true. Both are inside the file `build_manuscript.py` assembles into the
submitted manuscript, so whichever an editor takes, one printed statement is false.
No automated check can catch this: `scan.py` checks numbers, not claims.

### F4. **FIXED** — The paper says Arm A was never repeated. It was — and the paper reports it.

Three places state that only Arm B was re-executed:

- `DISCUSSION.md:609` (Limitation 10): *"Arms A and C were not repeated"*
- `RESULTS.md:1031` (Table 8, the coverage table): Arm A marked **"not run"**
- `README.md:264`: *"Arms A and C were not repeated"*

But `results/A/reproducibility.csv`, `results/A/reproducibility_agreement.csv` and
`results/backup/ALL_FOLDS_armA_run1_EEGNet.csv` all exist, and §7.9 describes the
check in detail at `RESULTS.md:809-818` — *"**Check 2 — Arm A, EEGNet only**"*.
`INTRODUCTION.md:168` also has it right.

This error runs in the unusual direction: **it understates the study**. Table 8 is
introduced as the table that exists *"so that no section has to be read as covering
more than it does"*, and here it reports less coverage than the study has.

### F5. **FIXED** — The released Arm A EEGNet probabilities are from a different execution than the fold table

Recomputing per-fold metrics from the released `probs_*.npz` files and comparing to
`ALL_FOLDS.csv`:

| model | PR-AUC from npz / from folds | balanced accuracy | verdict |
|---|---|---|---|
| CNN | 0.3382 / 0.3382 | 0.6182 / 0.6182 | same run |
| CNN-BiLSTM | 0.3986 / 0.3986 | 0.6962 / 0.6962 | same run |
| **EEGNet** | **0.4317 / 0.4314** | **0.7092 / 0.7084** | **different run** |

§7.9 discloses that two Arm A EEGNet runs exist — those exact figures appear at
`RESULTS.md:812-813`. What is **not** disclosed is that the *released* probability
files are the earlier one. So every Arm A EEGNet calibration number (ECE, Brier,
the recalibration result, Figure 5's row, Figure S1 panels d–e) is computed from a
different execution than the ROC-AUC printed beside it in the same table.

The differences are tiny and the paper already characterises run-to-run movement.
But a reviewer who recomputes PR-AUC from the released file gets 0.4317 while the
table says 0.4314, and will think something is wrong. A paper that publishes
per-window scores has to say which run they are.

### F6. **FIXED** — Table 7's bolding does not follow the rule its own caption states

Caption (`RESULTS.md:721-723`): *"Bold marks a value that Platt recalibration moved
below the construction's class-prior **Brier** reference."*

That rule selects six cells, all in the **Brier + Platt** column: A/CNN-BiLSTM,
A/EEGNet, B/EEGNet, B/Shallow, C/EEGNet, C/Shallow.

What is actually bolded:

- **Arm A rows bold the ECE + Platt column instead** — including CNN, which the rule
  does not select at all (its raw Brier 0.0671 was already below the 0.0762
  reference). The two Arm A cells the rule *does* select are left unbolded.
- Arms B and C bold both columns; their Brier bolds are correct.

So the mark means one thing in the Arm A rows and another below them, and on Arms B
and C it is applied to ECE values against a Brier-scale reference.

### F7. **FIXED** — The headline rank correlations are specific to *pooled* recall, and are unlabelled in the Abstract

`stats.accuracy_vs_recall` correlates accuracy with **pooled** recall. Recomputed
both ways:

| arm | pooled recall (what is reported) | subject-averaged recall (the paper's stated default) |
|---|---|---|
| A | **ρ = −1.000**, p = 0.0167 | ρ = −0.900, p = 0.0833 |
| B | ρ = −0.900, p = 0.0833 | ρ = −0.900, p = 0.0833 |
| C | ρ = −0.600, p = 0.3500 | ρ = −0.800, p = 0.1333 |

The "exact reversal" on Arm A, and the fact that Arm A is the only significant case,
**both depend on the pooled convention**. §7.3, §8.3 and Contribution 4 all say
"pooled recall" and are clean. Two places do not: `ABSTRACT.md:52-53` and the
standalone summary at `RESULTS.md:973-974`. Since `RESULTS.md:90` declares
subject-averaged the default, an unlabelled ρ reads as the subject-averaged one.

**The weaker claim is safe.** I verified that *"the two most accurate architectures
are exactly the two with the lowest recall"* holds under **both** conventions on all
three arms. Only the ρ values need the label.

---

## MEDIUM

### F8. **FIXED** — "Untouched by construction" is a withdrawn phrase, and it is false for isotonic

`RESULTS.md:944` and `DISCUSSION.md:363`: *"it leaves the ranking metrics untouched
**by construction**"* — where "it" is recalibration generally. `WITHDRAWN.md:26`
retires "unchanged by construction". `results/monotonicity.csv` records that
**isotonic lowered ROC-AUC on 123 of 150 folds and PR-AUC on 144 of 150**, with
falls of −0.3643 and −0.3155. The sentence is load-bearing: it is the stated reason
to prefer recalibration over threshold selection.

### F9. **CLOSED WITH SCOPE QUALIFIER** — The "below the reported precision" justification is false for PR-AUC

`RESULTS.md:785-786`: the Platt maps move PR-AUC by at most 0.003413347, *"both
below the precision reported anywhere in this paper"*. The paper prints PR-AUC at
four decimals (0.5103) and three (Table 4). **0.0034 is 34 × the four-decimal unit
and 3.4 × the three-decimal unit.** The ROC-AUC half of the sentence (0.0000397) is
fine.

*Judgement needed:* this is a single-fold maximum, and the reported values are means
over fifty folds, so the conclusion may well survive. The stated justification does
not. Settling it means registering post-Platt subject-averaged values and comparing
at the printed precision.

### F10. **FIXED** — "Falls short only because the two least sensitive architectures swap places"

`INTRODUCTION.md:144-147` and `DISCUSSION.md:154-156`. I undid exactly that swap on
Arm C: **ρ goes from −0.600 to −0.700, not to a reversal.** The remaining gap is
that EEGNet has the *highest* recall of all five (0.7851) while being only third
most accurate. And the exact p for −0.700 is 0.2333 — still not significant. So the
swap accounts for a quarter of the shortfall, and removing it would not change the
verdict. "Only because" attributes the outcome to a cause that does not explain it.

### F11. **FIXED** — "Three of the five on Arm A" should be four

`RESULTS.md:864`. Only EEGNet was re-executed on Arm A, so four of five were not
repeated. The error understates a limitation.

### F12. **FIXED** — The Overview overstates where pooled values are confined

`RESULTS.md:92-95`: *"Pooled values are used only where the quantity is intrinsically
pooled: the confusion matrices of §7.3 and the Brier scores of §7.5."* But the §7.5
tables also report **pooled ROC-AUC, PR-AUC and balanced accuracy**, none of which is
intrinsically pooled — EEGNet Arm A is 0.9015 pooled against 0.884 subject-averaged.
The §7.5 text itself is honest about this; the Overview sentence a reviewer relies on
is not. The companion claim *"No table mixes the two"* is true.

### F13. **FIXED** — The literature registry still carries a superseded year and two live VERIFY markers

`results/LITERATURE_NUMBERS.csv:38-39` still reads `[P5] Platt 1999: publication
year,1999,VERIFY before submission` and the same for `[P6]`. `REFERENCES.md:7` states
*"**No entry is marked `VERIFY` any longer**"* and records that **[P5] was wrong —
the printed chapter is *Probabilities for SV Machines* (2000)**. The registry the
scanner validates borrowed numbers against asserts both the superseded year and an
unfinished verification state. Preflight misses it because no body sentence prints a
reference year.

---

## LOW — mechanical, no scientific risk

| | Where | Problem |
|---|---|---|
| F14 | `README.md:323,326` | "Fifteen checks" (16) and "eight section files" (12) |
| F15 | `REPRODUCIBILITY.md:121` | "the 35 tests" — `pytest` reports **37 passed** |
| F16 | `README.md:54,158` | **FIXED** — both sentences corrected, and preflight now checks both READMEs |
| F17 | `REFERENCES.md:110` | `[R1]` is defined with a 17-line note and **cited nowhere**; it will print as an uncited reference |
| F18 | `README.md:235` | The documented `check_monotonicity.py` command exits 2; it needs a root directory argument |
| F19 | `tools/preflight.py` docstring | Says eleven checks, lists fifteen, says "six manuscript sections" where there are ten |
| F20 | `tests/test_pipeline.py:541` | `test_figure_1_partition…` — the Brier partition is Figure 4 since the renumbering; the test asserts the right thing under the wrong name |

---

## What I did not check

- Whether the claims about the **outside literature** are fair — that needs the
  surveys themselves, which are not in the repository. Two such claims rest on
  nothing recorded in the verified reference file: the "none of the three reviews
  treats calibration" claim is documented for `[S3]` only, and the "neither survey
  establishes how common subject-independent evaluation is" claim has no record for
  either survey. Both are flagged for your judgement, not asserted as errors.
- Anything requiring a GPU or the raw EDF recordings.

---

## Suggested order of work

1. **F1–F5** first. These are the ones a reviewer catches, and F1 and F4 are
   contradictions inside the paper rather than matters of taste.
2. **F6, F7** next: both are in main-paper tables and captions.
3. **F8–F13**: wording, with F9 needing one measurement before it can be settled.
4. **F14–F20**: mechanical.
5. Then strengthen the guards that missed these — `check_withdrawn.py` should cover
   `README.md` and should not be defeated by dropping one word, and the "which run
   is released" question in F5 deserves a check of its own.


---

## What was changed on 24 September 2026

**F1.** The Results summary item 6 now states the corrected claim — DeepConvNet is
beaten on ROC-AUC, PR-AUC, balanced accuracy, F1 and recall but **not** on pooled
Brier or pooled precision — and names the convention and the exact p-values, which
also closes the summary half of F7.

**The guard that missed it was rebuilt.** `check_withdrawn.py` now also looks for
*paraphrases*: a retired claim's content words, in order, close together, with at
most one missing, anchored on the first and last. Tested against the exact sentence
that escaped it for three drafts — it is caught. Short phrases and loose middle
matches are excluded, so the report stayed readable: eleven near misses before
anchoring, one after, and that one was a stale build.

**F2.** `results/README.md`'s "Not released" section was wrong and is now a
"Released, and what it lets you recompute" section, with the correction dated and
its cause recorded. Seven files the inventory had omitted are listed, including
both reproducibility comparisons and the Arm A backup.

**F3.** The long code-availability version now says the probability files are
released for Arm A, matching the short version twenty lines above it.

**F4.** Corrected in all three places: Limitation 10, Table 8 and `README.md`. The
table row now reads "EEGNet only, and weaker (Section 7.9)". **F11** was the same
misunderstanding one sentence away and was corrected with it: four of five on Arm A,
two of five on Arm B.

**F5.** §7.9 now states which execution the released scores come from, with the
numbers a reader will get if they recompute. And it is a command, not a claim:
`tools/check_released_scores.py` recomputes every released file fold by fold,
prints "same execution" or names Section 7.9, and fails only if a difference exceeds
the run-to-run movement the paper reports.

**F16**, because extending the guard required it: `README.md` carried two retired
claims — that no pair isolates trimming (Arms B and C do) and that a window ends at
an "annotation onset" (the deposit documents only time marks). Both corrected.

**Preflight is now seventeen checks**, and the withdrawn check covers `README.md`
and `results/README.md` as well as the manuscript, failing on a near miss as well as
an exact match. `ALL CHECKS PASS (17 of 17)`; 37 tests pass.


---

## F7, closed 24 September 2026

The Abstract now names the convention and the result of the exact test: *"the rank
correlation between accuracy and **pooled** recall is −1.000, −0.900 and −0.600,
**reaching significance on the first alone**."* The descriptive claim beside it —
the two most accurate architectures are the two with the lowest recall — was left
unqualified **because I verified it holds under both conventions on all three
constructions**, so it needs no label.

**The Abstract did not carry F1's error.** It names no architecture in the
accuracy-versus-recall paragraph and makes no "beaten on every metric" claim, so
there was nothing to undo there. Checked rather than assumed.

Three further things the rewrite fixed, all in the same paragraph family:

- **"EEGNet leads in eleven of twelve paired comparisons"** was describing the
  *significance* count as if it were the *lead* count. Recomputed: EEGNet's point
  estimate is higher in **twelve of twelve**, and the difference reaches p < 0.05 in
  eleven — the exception is Arm B against the CNN, 0.9003 vs 0.8662, p = 0.0645. The
  Abstract now reads "leads all twelve paired comparisons, significantly in eleven",
  which is what the Conclusion already said.
- **"A finding is reported only if it replicates on all three"** promised more than
  the paper does: the recalibration monotonicity check is Arm A only, threshold
  selection is Arm C only, and the recurrent block's PR-AUC gain holds on the two
  trimmed arms. Each is honestly scoped where it appears; the flat Abstract sentence
  was the overstatement. It now reads "A finding is claimed for all three only where
  it replicates on all three", and the same correction was made to Contribution 1 and
  to Research Gap §3.5 so the three statements of the rule agree.
- **Highlight 4** carried *"leaving ROC-AUC intact"* — the unhedged form of a claim
  the body hedges, and "intact" is the word `WITHDRAWN.md` retired. It now reads
  "ROC-AUC unchanged at the precision reported", matching §7.6.

**Two words of slack.** The Abstract was at 248 of 250 words, so the additions had
to be paid for. I did not pay for them by dropping a finding: the clause *"EEGNet
improves its calibration error on all three"* was cut in one draft and **put back**.
The words came from scaffolding instead — the architecture list no longer says the
architectures are "convolutional and recurrent-convolutional" before naming five
convolutional architectures, and the rhetorical opener "does not merely fail to
separate these architectures" is now the plain "Accuracy orders these architectures
against recall." One removal was substantive and deliberate: **"both usually
absent"**, a quantitative generalisation about the literature that nothing in
`LITERATURE_NUMBERS.csv` measures. Final count 245 words, all limits met.

**Still open in this family, and deliberately untouched:** the Abstract's
*"leaving ROC-AUC and PR-AUC unchanged at the reported precision"* is F9's sentence.
It is not guesswork territory — it needs the measurement — so it was left exactly as
it stands until F9 settles it.


---

## F9 — the measurement, 24 September 2026

**Nothing has been rewritten.** This is the measurement you asked for, taken before
any wording was touched. `tools/check_ranking_invariance.py` reproduces it.

Method: the released Arm A scores; Platt fitted per fold on the other nine subjects
of the same seed with `calibrate.fit_apply_platt` (the pipeline's own function, not
a reimplementation); ROC-AUC and PR-AUC per fold, raw and recalibrated; aggregated
**both** ways the paper aggregates; compared at three and four decimals, the
precisions the paper prints.

### Subject-averaged — the aggregation of Table 4 and Section 7.1

| Model | Metric | Raw | After Platt | Δ | 3 dp | 4 dp |
|---|---|---|---|---|---|---|
| EEGNet | ROC-AUC | 0.884025 | 0.884026 | +1.0 × 10⁻⁶ | same | same |
| EEGNet | PR-AUC | 0.431710 | 0.431732 | +2.2 × 10⁻⁵ | same | same |
| CNN | ROC-AUC | 0.842776 | 0.842776 | **0** | same | same |
| CNN | PR-AUC | 0.338237 | 0.338237 | **0** | same | same |
| CNN-BiLSTM | ROC-AUC | 0.821331 | 0.821331 | **0** | same | same |
| CNN-BiLSTM | PR-AUC | 0.398585 | 0.398585 | **0** | same | same |

Four of the six move by exactly zero. I also checked the rounding margin, because
"unchanged at 4 dp" is worthless if a value sits on a boundary: the smallest margin
is EEGNet's PR-AUC, and even there the distance to the nearest boundary is **twice**
the movement. For ROC-AUC it is 25 times.

**So for the values the paper reports, the claim is true — Case 2.**

### Pooled — the aggregation of Section 7.5

| Model | Metric | Raw | After Platt | Δ |
|---|---|---|---|---|
| EEGNet | ROC-AUC | 0.9019 | 0.8886 | **−0.0133** |
| EEGNet | PR-AUC | 0.5114 | 0.4305 | **−0.0810** |
| CNN | ROC-AUC | 0.8762 | 0.8695 | −0.0066 |
| CNN | PR-AUC | 0.4790 | 0.4342 | −0.0448 |
| CNN-BiLSTM | ROC-AUC | 0.8751 | 0.8570 | −0.0181 |
| CNN-BiLSTM | PR-AUC | 0.4913 | 0.4100 | −0.0813 |

These are large. **They are not a violation of the monotonicity argument**, and I
confirmed the mechanism rather than inferring it:

1. within each fold, recalibration moves ROC-AUC by at most 3 × 10⁻⁵ — the ordering
   *is* preserved, as the positive slopes require;
2. pooled with the pipeline's **ten different per-fold maps**, ROC-AUC moves −0.0079
   on the seed tested;
3. pooled with **one single map** fitted on everything (an invalid protocol, used
   here only as a diagnostic), ROC-AUC moves **+0.0000**.

A monotone map preserves ordering *within the set it is applied to*. Ten different
maps do not preserve ordering *across* those ten sets, because each fold's scores are
rescaled differently — one subject's recalibrated range becomes [0.008, 0.978] while
another's stays [0.000, 1.000]. Pooling after per-fold recalibration is therefore a
**different quantity**, not a broken theorem.

**The paper never computes a post-recalibration pooled ROC-AUC or PR-AUC.** Section
7.5's pooled table is of raw scores, and the registry holds no post-Platt ranking
row at all. So no printed number is wrong.

### What this means for the sentence

Two separate things, and only the first is a straightforward error:

**(a) The justification is false as written.** `RESULTS.md:785` and
`EXPERIMENTAL_SETUP.md:130` argue from the per-fold maximum — *"moves ROC-AUC by at
most 0.0000397267 and PR-AUC by at most 0.003413347 — both below the precision
reported anywhere in this paper."* PR-AUC's 0.0034 is **34 times** the four-decimal
unit. The per-fold maximum was never the right quantity to argue from: the tables
print an average over fifty folds, and an average absorbs a per-fold movement. The
argument should be the measurement above, which is now available.

**(b) The conclusion holds, but only under one aggregation, and the paper does not
say which.** As written the claim is unrestricted. A reader who tested it the pooled
way — and §7.5 prints pooled ranking metrics, so that is a natural thing to try —
would find changes of up to 0.08 and conclude the paper was wrong.

My recommendation, for you and sir to accept or reject: keep the conclusion, replace
the justification with the subject-averaged measurement, name the aggregation, and
add one sentence explaining the pooled behaviour so that a reader who checks it
finds the explanation already there rather than an apparent contradiction. That is
your Case 2 plus a scope qualifier — not a hedge, but a statement of what was
actually measured.

`tools/check_ranking_invariance.py` is **deliberately not wired into preflight yet**:
it exits non-zero on the pooled comparison, and what its exit condition ought to be
depends on the wording decision.


---

## F9 — closed with a scope qualifier, 24 September 2026

The conclusion was kept and scoped, as you decided. What changed is the
*justification* and the *scope*, in one terminology across nine locations.

**The reasoning that was removed.** Every place that argued from the per-fold
maximum — *"moves ROC-AUC by at most 0.0000397267 and PR-AUC by at most
0.003413347, both below the precision reported anywhere in this paper"* — now says
instead that a per-fold bound is not the quantity the tables print, and gives the
measurement of the quantity they do print. The per-fold figures are kept where they
belong: as a bound on what one fold can move, with the ε-clip named as the cause.

**The wording, in your words**, in Experimental Setup §6.6, Results §7.6, and — with
the aggregation named — in the Abstract, Highlight 4, Introduction Contribution 3,
Conclusion, Related Work (twice), the Figure 5 caption, Results summary item 10 and
the generated `MASTER_FILE.md`. Nine locations plus the two generated files; a grep
for an unscoped "unchanged at the reported precision" now returns nothing outside
`WITHDRAWN.md`'s ban list.

**The numbers are registry rows, not typed.** `check_ranking_invariance.py` writes
`results/ranking_invariance.csv`, and `registry.py` reads it the same way it reads
`monotonicity.csv`. Six new rows; the registry went from 1,750 to 1,756 — which the
row-count guard caught immediately in four documents that still said 1,750, and
those are corrected.

**The guard is wired, with the exit condition matching the final wording.**
`ranking invariance` fails only if a **subject-averaged** value changes at a printed
precision. The pooled comparison is printed by the same tool and deliberately does
not gate the run, because no pooled post-recalibration ranking metric is reported
anywhere in the paper.

**Preflight is now eighteen checks. `ALL CHECKS PASS (18 of 18)`; 37 tests pass.**
As you said, that is not scientific approval — it is today's guards passing. F6, F8,
F10 and F12–F20 remain.

One thing noticed in passing and **not** changed, because it is outside F9:
`DISCUSSION.md:94` says the recurrent block *"leaves ROC-AUC unchanged on every arm"*
and then prints 0.843 → 0.821. The claim is about significance (p = 0.695), not about
the value, and the wording does not say so. Worth adding to the list.


---

## F10 — closed 24 September 2026, and the measurement went further than my first report

**A correction to my own earlier account.** In the Step 3 report I wrote that undoing
the swap "raises ρ from −0.600 to −0.700" and left it there, which implied the
reversal was otherwise intact on Arm C. Laying the two orderings side by side shows
it is not:

| by accuracy | | by recall, actual | | required for ρ = −1.000 |
|---|---|---|---|---|
| DeepConvNet 93.5551 | | EEGNet 0.7851 | | ShallowConvNet |
| CNN 92.6458 | | ShallowConvNet 0.7700 | | CNN-BiLSTM |
| EEGNet 89.4968 | | CNN-BiLSTM 0.7322 | | EEGNet |
| CNN-BiLSTM 89.2765 | | DeepConvNet 0.4981 | | CNN |
| ShallowConvNet 82.1879 | | CNN 0.4933 | | DeepConvNet |

**All five positions differ** from an exact reversal. There are two distinct
departures, not one: a three-way rotation among the most sensitive three (EEGNet
sits first on recall where an exact reversal needs it third), and the exchange of
the two least sensitive. Undoing only the second gives ρ = −0.700, exact
p = 0.2333 — **still not significant**, so the named cause does not even account for
the outcome it was offered to explain.

**The replacement** follows your rule that the sentence should describe the ordering
and not offer it as a causal explanation. Introduction Contribution 4 now reads
*"On Arm C the ordering departs from an exact reversal in more than one place
(p = 0.3500): the two least sensitive architectures exchange places with each other,
at recall 0.493 and 0.498, and EEGNet, third on accuracy, has the highest recall of
the five."* Discussion §8.3 carries the same correction in its own words.

**No new number entered the manuscript.** 0.493 and 0.498 were already registered;
"third" and "highest of the five" are orderings a reader can read off Table 5. The
counterfactual ρ = −0.700 and its p = 0.2333 are recorded here as the evidence for
the correction and deliberately left out of the paper: a counterfactual invites the
question of why that one and not others, and the descriptive statement is both
shorter and checkable.

### One thing in your proposed wording I did not use

Your draft read: *"The observed ordering produces a perfect inverse rank correlation
(ρ = −1.000); however, this value ... becoming −0.700 when the identified pair is
swapped."* Those two numbers belong to **different constructions**. ρ = −1.000 is
**Arm A**, where the reversal is exact; the sentence being repaired is about **Arm
C**, where ρ = −0.600. And −0.700 is what Arm C becomes when the swap is *undone*,
not what Arm A becomes when a pair *is* swapped. As written it would have said Arm
A's perfect reversal degrades to −0.700 under a swap, which is a new claim and not
a true one. Your principle — describe, do not explain causally, and add no
unmeasured number — is what the replacement follows.

`ALL CHECKS PASS (18 of 18)`; 37 tests pass.


---

## F6 — closed 24 September 2026

No statistic changed. Six cells moved from bold to plain and six from plain to bold;
every printed value is the one that was there before.

**Why it drifted.** Most tables in the paper are generated by `src/tables.py`.
Table 7 is not — it was merged by hand from three per-arm tables when the tables
were numbered, and a hand-merged table carries its emphasis by hand too. Nothing
caught it because **every number was correct**: `src/scan.py` reads values and
cannot see which of them are wrapped in asterisks.

**The rule, applied mechanically.** The rows were rebuilt from
`results/<arm>/calibration_summary.csv` rather than retyped, with the caption's
condition — raw Brier above the construction's reference, recalibrated Brier below
it — evaluated per row. It selects six cells, all in **Brier + Platt**:
CNN-BiLSTM and EEGNet on Arm A, EEGNet and ShallowConvNet on Arms B and C.

**The caption now says where the mark can appear and why it cannot appear
elsewhere:** the reference is π(1 − π), a Brier-scale quantity, so there is no
reference against which a calibration error could be marked. That was the deeper
error — the Arm A rows marked ECE cells against a Brier-scale threshold, a
comparison that does not exist.

**And it is a command now, not a convention.** `tools/check_table_marks.py` reads
the table out of the manuscript, recomputes the rule from the released summaries,
and compares the two sets of cells. Run against the pre-fix table it reports:

```
MARKED IN THE WRONG COLUMN  Arm A CNN: ECE + Platt = 0.0447
MARKED IN THE WRONG COLUMN  Arm A CNN-BiLSTM: ECE + Platt = 0.0561
MARKED IN THE WRONG COLUMN  Arm A EEGNet: ECE + Platt = 0.0625
RULE SELECTS BUT NOT MARKED  Arm A CNN-BiLSTM
RULE SELECTS BUT NOT MARKED  Arm A EEGNet
5 discrepancy(ies)
```

It is wired into preflight, which is **nineteen checks**. `ALL CHECKS PASS
(19 of 19)`; 37 tests pass.


---

## F8 — closed 24 September 2026

The sentence is load-bearing: it is one of three reasons the paper gives for
preferring recalibration to threshold selection, in Results §7.8 and Discussion
§8.7. It said recalibration *"leaves the ranking untouched by construction"*, which
was wrong twice over — "unchanged by construction" is a phrase `WITHDRAWN.md:26`
retired, and the sentence is about recalibration in general, where it is false.

**It is false for isotonic.** `results/monotonicity.csv`, already registered:
isotonic regression **lowered ROC-AUC on 123 of 150 folds and PR-AUC on 144 of
150**, with falls of −0.3643 and −0.3155. Isotonic is only non-decreasing, so its
flat regions merge distinct scores into ties. "Untouched by construction" is the
opposite of that.

**And "by construction" was never right even for Platt.** The ε-clip before the
logit can tie scores that were distinct, so the invariance is measured, not
guaranteed — which is exactly what F9 settled, and at which aggregation.

**The replacement scopes the reason to the route the paper actually recommends.**
Both sentences now read that *the Platt route* leaves the **subject-averaged**
ranking metrics unchanged at the reported precision, measured rather than
guaranteed, and **not true of isotonic regression on the same folds** (§6.6).

This does not weaken the argument — it sharpens it. I checked the claim the
sentence sits beside: every architecture whose raw calibration was above the
class-prior reference improved significantly on **both** Brier score and calibration
error under Platt, and it is exactly **six of six** across the three arms (Arm A
EEGNet and CNN-BiLSTM, Arms B and C EEGNet and ShallowConvNet; every p < 0.05 on
both measures). So the preference for Platt over both isotonic and threshold
selection now rests on stated, measured grounds.

`ALL CHECKS PASS (19 of 19)`; 37 tests pass; 58 cross-references in the two edited
files resolve, including the new pointers to §6.6.


---

## F12 and F13 — closed 24 September 2026

### F12

Rather than patch the sentence, I counted where pooled values actually are. The
registry holds them in more places than the Overview admitted, so the replacement
enumerates rather than generalises:

- **§7.3**, the confusion matrices and everything read off them — recall, precision
  and accuracy;
- **§7.5**, the Brier scores *together with the ROC-AUC, PR-AUC and balanced
  accuracy printed beside them*, with a pointer to their subject-averaged
  counterparts in §7.1 and to the subject-averaged Brier in §7.6.

**And one fact that was nowhere in the paper.** The registry has no
subject-averaged row for accuracy and no pooled-suffixed one either — it exists
only as `pooled accuracy percent`. **Accuracy exists only as a pooled quantity**,
because it is read off the pooled confusion matrix. The Overview now says so, and
says it applies "wherever an accuracy appears, including in the Discussion" — which
closes the gap where §8.3's accuracy figures were pooled and unlabelled.

Two smaller things in the same passage: the ± is now described correctly for both
conventions (in §7.5 it is the SD of the five per-seed *pooled* scores, not of means
over subjects), and a stale cross-reference is fixed — between-subject spread is
§7.4, not "Section 6". The cross-reference checker could not catch that one: Section
6 exists, it is simply the wrong section.

### F13

`REFERENCES.md` says in bold that no entry carries a `VERIFY` marker, and records
that **[P5] was checked and found wrong** — the chapter printed at pp. 61–74 is
*Probabilities for SV Machines* (**2000**), not the 1999 preprint title most of the
literature copies. The literature registry still read `[P5] Platt 1999: publication
year, 1999, VERIFY before submission`. Both rows now carry the verified year and the
catalogue record they were checked against, lifted from the `REFERENCES.md` entries
rather than invented. All 70 rows now name a source; the only two without an http
address state their derivation and name one inside it.

**Why nothing caught it, and what does now.** No sentence in the body prints a
reference year, so `scan.py` never had to look at those rows. `tools/check_literature.py`
ties the two hand-maintained files together — it reads the year printed for each key
in `REFERENCES.md` and compares it with the registry, refuses unfinished markers, and
requires a source on every row. Against the stale row it reports all three ways:

```
UNFINISHED   [P5] Platt 1999: publication year -- VERIFY before submission
UNSOURCED    [P5] Platt 1999: publication year -- 'VERIFY before submission'
YEAR DISAGREES  P5: registry says 1999, REFERENCES.md says 2000
```

Writing it also turned up a bug in my own first draft: a line-by-line parser found
ten of the sixteen entries, because an author list often wraps for three lines
before the year appears, and it reported the other six as missing from the reference
list. It now reads whole entry blocks — all sixteen.

Preflight is **twenty checks**. `ALL CHECKS PASS (20 of 20)`; 37 tests pass.


---

## F14–F20, and the Discussion item — closed 24 September 2026

Each item verified individually, so mechanical cleanup and scientific wording stay
separable.

| Item | Result |
|---|---|
| **F14** README "Fifteen checks" → **twenty**; "eight section files" → **twelve** | PASS |
| **F15** REPRODUCIBILITY "the 35 tests" → **37** | PASS |
| **F17** `[R1]` cited in the body | PASS |
| **F18** documented `check_monotonicity.py` command runs | PASS |
| **F19** preflight docstring in step with the live check list | PASS |
| **F20** test renamed for the figure it actually asserts | PASS |
| **Separate** `DISCUSSION.md:94` "leaves ROC-AUC unchanged" | PASS |
| **Separate, newly found** the parameter multiple in the same paragraph | PASS |

Every count was read from the live system, not from the report: preflight's own run
line, `ORDER` imported from `build_manuscript.py`, and `pytest`'s summary.

### F18 — the interface, not the documentation

I ran the documented command exactly as written first. It printed the usage text and
measured nothing, so the two possibilities had to be separated.

**The interface was the outlier.** Every other check in this repository —
`check_released_scores`, `check_ranking_invariance`, `check_literature`,
`check_table_marks`, `preflight` — takes no arguments and finds `results/` itself.
`check_monotonicity.py` alone required a path, and the README documented it the way
its siblings behave. So the tool was given the defaults its documentation assumed;
both positional arguments still work for a release extracted elsewhere.

**Output byte-identical.** I kept a copy of `results/monotonicity.csv` before the
change and diffed after: no measured value moved. The change is to how the tool is
invoked, not to what it computes.

**One thing found while in there:** the tool's own docstring and its closing message
still asserted the pre-F9 claim — that Platt "cannot change ROC-AUC or PR-AUC", and
that the movement is "below the precision the manuscript reports". Both now match
the corrected wording, and the closing message points at
`check_ranking_invariance.py` for the question it cannot answer.

### F17 — cited where it bears on the argument, not to fill a slot

`[R1]` was defined with a seventeen-line note and cited nowhere, so it would have
printed as an uncited reference. Its own entry says it may be cited **only** as
prior work by the same group on EEG drowsiness detection, never as a description of
DD-Database.

That is exactly what the Related Work paragraph on the deposit's missing
documentation needed: the depositing group has earlier published work on EEG
drowsiness detection, but on a different database with a different montage,
sampling rate and annotation criterion — so **even the group's own published work
does not document these recordings**. The sentence strengthens the point rather
than decorating it, and introduces no number. All sixteen defined keys are now
cited; none is cited without being defined.

### The Discussion item, kept separate

*"Adding the recurrent block **leaves ROC-AUC unchanged** on every arm
(0.843 → 0.821, …)"* — 0.843 → 0.821 is a fall of 0.022, so "unchanged" cannot mean
what it says. The intended meaning was statistical, and it is now stated that way:
**"does not significantly change ROC-AUC on any arm … the point estimate falls on
two of the three, by 0.022 and 0.007, and neither movement approaches significance
on the ten paired subjects."** The p-values were already there and are unchanged;
what changed is a word that claimed equality the data does not show.

**And a second error in the same two sentences, not previously on the list.** The
paragraph said the recurrent block *"adds 135,936 parameters, four times the CNN's
total"*. From `config.PARAMS`: 135,936 / 44,705 = **3.04×**. It is the CNN-BiLSTM's
*total* of 180,641 that is 4.04× the CNN's. The multiple was attached to the wrong
quantity; the sentence now gives both.

`ALL CHECKS PASS (20 of 20)`; 37 tests pass; scan clean on every edited section.
