# 1. Introduction — draft 1 (16 September 2026)

<!-- not-for-submission:start -->
Written against Results draft 4, Discussion draft 4 and the verified reference
list. Every number appears in `MASTER_NUMBERS.csv` or `LITERATURE_NUMBERS.csv`.
<!-- not-for-submission:end -->

---

Driver drowsiness is a condition that a monitoring system must detect *before*
it produces a lapse, and electroencephalography is the modality closest to the
state itself rather than to its consequences. A camera sees a closed eyelid; the
EEG sees the cortical change that precedes it. That advantage is why the field
is large and well surveyed, and why its reported performance is high: across 69
studies reviewed to August 2025, the median reported accuracy is 94.48 % for
deep-learning methods and 91.80 % for classical machine learning [S2], and an
EEG-specific survey of 87 papers records figures up to 99.23 % [S1].

**Those numbers cannot be read.** Not because they are implausible, but because
accuracy on a rare-event problem cannot be interpreted without two quantities that the
reviewed papers largely do not report: the class ratio of the evaluation set,
and the accuracy of the trivial predictor that always answers with the majority
class. On the data used here, "always alert" scores between 91.68 % and 93.06 %
depending on the construction. Against that, the 94.48 % median of the reviewed
deep-learning studies is a margin of a few points at most, and on a dataset whose
prevalence is not reported, the margin cannot be computed at all. The figure is
not implausible; it is unreadable.

This paper is an attempt to evaluate the same familiar architectures in a way
that does not have that problem, and to report honestly what survives.

## What we found by asking three questions the field has not asked together

**Does the finding survive a different preprocessing decision?** Turning continuous
recordings with event marks into labelled windows requires choices the raw data does
not make (whether to trim recordings to a common length, how to handle each subject's class ratio), and those choices move the prevalence, which moves every
threshold-dependent metric. We therefore built **three constructions of the same ten
recordings** and report which findings hold on all three. They are three cells of a
two-by-two design of trimming against balancing, **the fourth not evaluated**; the
three still yield two contrasts, each varying one factor. The answer is asymmetric:
balancing produces seven significant differences across twenty paired tests, trimming
none, its smallest p being 0.1309. With ten subjects that null is weak evidence, and
the paper says "no measurable effect" rather than "no effect" throughout.

The discipline is costly: it removed two claims a single construction would have
supported. An inverse relationship between parameter count and ranking quality decays
ρ = −0.900 → −0.500 → −0.100 across the three and reaches significance on none, so it
is withdrawn, as is the claim that the deepest architecture ranks worst, true on two constructions and false on the third.

**Are the probabilities any good, as probabilities?** A separate question from
whether the model ranks windows correctly. Outside EEG it is routine: neural networks
are systematically over-confident [P1], and discrimination and calibration are
understood as separate properties, so a model that ranks cases correctly may still
mis-state absolute risk badly enough to be the wrong choice [P2]. Here, as a checkable
statement, **none of the three most recent reviews of this field treats the
calibration of predicted probabilities as an evaluation dimension** [S1, S2, S3]: verified by full-text search: *Brier*, *probability calibration*, *Platt*,
*isotonic*, *expected calibration error* and *reliability diagram* occur in none of
them. The 2026 review names the problem that makes it matter, that accuracy "can be
misleading in imbalanced settings where drowsy samples are relatively rare", yet its
own vocabulary stops at accuracy, precision, recall, specificity and F1 [S3], five metrics that all presuppose a threshold and none of which can detect a mis-stated
probability.

Asking it here produces the paper's central result. Scored against the Brier score of
a constant predictor that ignores the EEG and emits the class prior, **three of the
five architectures are worse than that constant**, including the one with the highest
subject-averaged ROC-AUC on all three constructions, and the partition of the five
about that reference is *identical* on all three, despite three different prevalences.
Ranking quality and probability reliability are separable, and here they separate.

The gap is repairable, and cheaply: a two-parameter logistic function fitted per fold
**on the other nine subjects only** brings every measured architecture below the
reference on every construction, while leaving the ordering essentially untouched, a condition checked rather than assumed (Section 7.6). The ordering information was
already present; only its mapping onto the probability scale was wrong.

**What does the uncertainty actually come from?** With ten subjects an interval over
random seeds describes almost nothing [E2]. For subject-level PR-AUC, between-subject
spread exceeds between-seed spread by roughly an order of magnitude on every
construction, 12 to 48 times on Arm A, 6 to 18 on Arm B, 10 to 36 on Arm C. Worse,
when one construction was executed twice under identical settings, differing only in
GPU non-determinism, two of three architectures moved an individual subject's mean by
more than the standard deviation this paper reports as its ±.

## Contributions

1. **A three-construction evaluation protocol**, in which a finding is claimed only
   where it replicates on all three window-set constructions of the same recordings
   and is otherwise reported with the constructions it covers named, and in which two
   pairs of constructions each isolate one construction choice. Two claims a single
   construction would have supported are withdrawn under it, and the two choices
   differ sharply: balancing moves results, trimming does not.

2. **An evaluation of probability reliability for EEG drowsiness detection**, a
   dimension none of the three most recent reviews treats, finding that three of five
   architectures (including the highest-ranking one) score worse than a constant
   predictor emitting the class prior, with the same partition on all three
   constructions. *We do not claim priority*: an earlier draft said "the first report,
   to our knowledge", and that is withdrawn, because priority rests on a systematic
   search that was not performed. What is stated instead is checkable.

3. **A demonstration that the gap is one of scale rather than of ordering**:
   out-of-subject logistic recalibration, fitted per fold on the other nine subjects,
   removes it on every construction with the **subject-averaged** ROC-AUC and PR-AUC
   unchanged at the reported precision, measured rather than inferred, on the three
   Arm A architectures whose per-window scores are released, three of fifteen
   architecture-by-arm cells. The invariance is not claimed for pooled metrics.

4. **Evidence that accuracy does not merely fail to separate these architectures but
   orders them against recall.** On all three constructions **the two most accurate
   architectures are exactly the two with the lowest recall** (ρ = −1.000, −0.900,
   −0.600, only the first clearing the exact threshold), and on Arm C the single
   architecture exceeding the always-alert baseline detects 335 of 673 drowsy windows.
   What accuracy does **not** license is a general ranking: that same architecture
   attains the best pooled Brier score and the highest pooled precision, while the best
   ROC-AUC belongs to one of the three worse than the constant predictor. No
   architecture here wins on every measure.

5. **A mechanism for when out-of-subject threshold selection helps**, in place of the
   blanket negative a single construction supports: it transfers between subjects when
   a model's scores are stably offset in one direction, and not otherwise.

6. **A quantification of execution non-determinism**, which single-run comparisons do
   not report: where measured, a single subject's mean moved further between two
   identical runs than the seed-level ± this paper reports. It covers three
   architectures on one construction and one on a second, so **for every architecture
   not covered the reported ± is a lower bound**.

7. **A complete, tested, released pipeline.** All 750 per-fold results are published
   with code regenerating every table and significance test from them, without a GPU
   and without the recordings; a registry records every value the manuscript may cite
   and an automated scan reports any figure absent from it.

What this study does *not* establish: three constructions of ten recordings are not
three datasets, and nothing here is external replication. The surviving architecture
ranking is narrow: EEGNet exceeds every alternative and **no other pair separates
significantly on ROC-AUC on any construction**, though those same pairs do separate on
balanced accuracy, so the limit is on ranking quality rather than distinguishability.
Calibration is measured on three of the five architectures per construction. These
bounds are stated where they bite and collected in Section 8.10.

## Organisation

Section 2 reviews the relevant work and Section 3 the four gaps that set the design.
Section 4 describes the dataset and the three constructions, Section 5 the five
architectures, Section 6 the evaluation protocol and its two averaging conventions.
Section 7 reports the results, Section 8 discusses what they license, Section 8.10 the
limitations, and Section 9 concludes.

---

## Notes for the next pass — not part of the paper

- Target length for BSPC is about one page; this runs slightly long. If it must
  shrink, the contribution list compresses to a single paragraph and the three
  question headings can become plain topic sentences.
- Contribution 2 says "to our knowledge". Keep that hedge unless a systematic
  search of EEG drowsiness papers for calibration reporting is actually run; a
  bare "first" is a claim a reviewer can falsify with one counterexample.
- The Abstract is written last, from this section plus the Results summary.
- Check whether BSPC wants contributions as a bulleted list or as prose.
