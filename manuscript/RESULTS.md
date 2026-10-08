# Results — draft 4 · THREE-ARM REBUILD (16 September 2026)

<!-- not-for-submission:start -->
Draft 3 was the post-audit baseline on two dataset constructions. **Draft 4 adds
the third construction (Arm C) and rebuilds every section that it touches.** Every
number was regenerated on 16 September 2026 by `registry.py` directly from the raw
result files, and every value appears in `MASTER_NUMBERS.csv`, which is the only
list of values this manuscript cites.
<!-- not-for-submission:end -->

> **What this study does not claim, and why.**
> No pair of architectures other than those involving EEGNet separates significantly
> *on ROC-AUC* on any of the three constructions, so no ranking among the lower four
> is claimed; those same pairs do separate on balanced accuracy, which Section 7.1
> reports. No relation between parameter count and ranking quality is claimed:
> ρ = −0.900 → −0.500 → −0.100 across the three arms, nominal on none. Threshold
> selection is not claimed to help or to fail universally; where it helps is reported
> with the mechanism proposed for it (Supplementary Note 2). The CNN / CNN-BiLSTM
> ablation is not claimed to isolate the sequence-reduction component alone, because
> the recurrent block also quadruples the parameter count (Section 7.2).
>
> **Findings that hold on all three constructions.** The three-against-two
> Brier partition, the EEGNet ranking result, the ablation, the accuracy argument,
> the between-subject variation result, and the effect of out-of-subject
> recalibration.

**Figure 2** is the design in one picture; every number in its boxes is read from
the pipeline configuration, so it cannot drift from the code that produced the
results.

![Figure 2. Study design and leave-one-subject-out evaluation.](../figures/figure2_study_design.png)

> **Figure 2. Study design and leave-one-subject-out evaluation.** Top row, from the
> recordings to the three window-set constructions; middle row, the fold protocol and
> what is held out at each stage; bottom row, the four families of measurement. The
> labelling box says *a drowsy window ends at an annotated drowsiness-event time
> mark* and the alert class keeps a 20-second guard from every such mark. The reference
> time is the dataset's documented event-button time mark associated with the
> volunteer's drowsiness feeling; it is not interpreted here as a physiological
> drowsiness onset (Section 4.1).

**Figure S1**, in the supplementary material, collects the study in one
multi-panel overview for readers who want the whole comparison on one page. It is
supplementary rather than a main figure because its reliability panels can be drawn
only for Arm A (the one construction whose per-window scores are released) and
this paper reports findings where they replicate on all three.

## Overview

Five architectures were evaluated on **three constructions of the same ten
recordings** (window counts and reference values: **Table 1**, Section 4.4), under
leave-one-subject-out cross-validation with five seeds: 50 folds per architecture per
arm, 250 per arm, **750 in total**.

**Two averaging conventions, kept strictly apart.** A *subject-averaged* value is
computed inside a fold and averaged over the ten subjects, each weighted equally; a
*pooled* value concatenates all ten folds within a seed and scores them once,
weighting each subject by its window count. The two differ substantially here:
pooled recall exceeds subject-averaged recall by 0.13 to 0.25 for every architecture
on all three arms, so each table states which it uses. **Subject-averaged is the
default**, every significance test being a paired test on the ten subject-level
differences; pooled values are used in Section 7.3 and Section 7.5. **Accuracy exists only
as a pooled quantity**, here and in the Discussion. No table mixes the two.

The ± is the standard deviation across the five seed-level values, so it measures
seed-to-seed variability, not spread between subjects; that is Section 7.4, and
re-execution variability Section 7.7.

Per-arm references: class prior 0.0832 / 0.0694 / 0.0727 (the PR-AUC chance level);
π(1 − π) = **0.0762** / **0.0645** / **0.0674** (the Brier score of the constant
predictor emitting the prior); always-alert accuracy **91.68 %** / **93.06 %** /
**92.73 %**. Two decimals throughout, since the margins in Section 7.3 are smaller
than a tenth of a point.

These are three settings of one problem, not three datasets. **Both construction
choices are isolated, each by one pair of arms:**

| Contrast | Held constant | Varied | Isolates |
|---|---|---|---|
| **A vs C** | trimming (both trimmed) | balancing | the balancing rule (Section 7.1.1) |
| **B vs C** | balancing (both proportional) | trimming | trimming (Section 7.1.2) |

Three of the four cells were run, which is what gives two controlled contrasts
rather than one; the fourth, untrimmed with every drowsy window kept, was not. A
finding holding on all three is not an artefact of one of them, but the arms are not
independent datasets, and no external replication is claimed.

## 7.1 Architecture comparison

**Table 3. Subject-averaged ranking quality on all three constructions.** Upper
block ROC-AUC, lower block PR-AUC; each cell is the mean over ten subjects, ± the
standard deviation across the five seed-level means. Bold marks the best value in
a column. PR-AUC chance levels are the prevalences in Table 1.

**Subject-averaged ROC-AUC** (mean over ten subjects, ± SD across five seeds):

| Model | Parameters | Arm A | Arm B | Arm C |
|---|---|---|---|---|
| EEGNet | 1,809 | **0.884 ± 0.007** | **0.900 ± 0.008** | **0.883 ± 0.010** |
| ShallowConvNet | 14,121 | 0.846 ± 0.003 | 0.847 ± 0.014 | 0.833 ± 0.018 |
| CNN | 44,705 | 0.843 ± 0.009 | 0.866 ± 0.013 | 0.847 ± 0.017 |
| DeepConvNet | 150,226 | 0.812 ± 0.008 | 0.793 ± 0.033 | 0.834 ± 0.025 |
| CNN-BiLSTM | 180,641 | 0.821 ± 0.022 | 0.859 ± 0.016 | 0.847 ± 0.033 |

**Subject-averaged PR-AUC** (chance level 0.0832 / 0.0694 / 0.0727):

| Model | Parameters | Arm A | Arm B | Arm C |
|---|---|---|---|---|
| EEGNet | 1,809 | **0.431 ± 0.006** | **0.440 ± 0.026** | **0.407 ± 0.007** |
| ShallowConvNet | 14,121 | 0.411 ± 0.011 | 0.399 ± 0.014 | 0.372 ± 0.019 |
| CNN | 44,705 | 0.338 ± 0.005 | 0.360 ± 0.019 | 0.295 ± 0.012 |
| DeepConvNet | 150,226 | 0.405 ± 0.011 | 0.384 ± 0.018 | 0.386 ± 0.013 |
| CNN-BiLSTM | 180,641 | 0.399 ± 0.021 | 0.397 ± 0.038 | 0.377 ± 0.025 |

**What replicates: EEGNet, and only EEGNet.** The smallest architecture, at 1,809
parameters, leads on ROC-AUC and PR-AUC on all three. Paired on the ten
subject-level differences, never on the fifty folds:

| EEGNet vs | Arm A | Arm B | Arm C |
|---|---|---|---|
| ShallowConvNet | **p = 0.0039** (9/10) | **p = 0.0098** (8/10) | **p = 0.0020** (10/10) |
| CNN | **p = 0.0020** (10/10) | p = 0.0645 (8/10) | **p = 0.0488** (8/10) |
| DeepConvNet | **p = 0.0020** (10/10) | **p = 0.0020** (10/10) | **p = 0.0195** (9/10) |
| CNN-BiLSTM | **p = 0.0039** (9/10) | **p = 0.0020** (10/10) | **p = 0.0137** (9/10) |

Eleven of twelve reach the nominal level; the exception is CNN on Arm B
(p = 0.0645), where EEGNet still leads on eight of ten subjects. Five land on the
attainable floor 2/2¹⁰ = 0.00195 by improving on every subject, and none has a tied
subject, so that floor holds throughout.

**What does not replicate: the rest of the ROC-AUC ordering.** **None of the six
pairs not involving EEGNet reaches significance on ROC-AUC on any arm** (smallest
p = 0.1934, 0.0840, 0.4316 on Arms A, B, C), so the apparent ranking of the lower
four is not a measurement, and no claim is made that DeepConvNet ranks lowest: it is
fourth on Arm C by 0.0007 (0.8339 against 0.8332), p = 0.6250.
**This concerns ranking quality only**: on balanced accuracy four of those six pairs
separate on Arm A, four on Arm B and five on Arm C, the ablation of Section 7.2 among
them. They fail to separate on the *ordering* of windows, not on behaviour at a fixed
threshold.

**The capacity correlation is withdrawn.** Between parameters and subject-averaged
ROC-AUC, ρ = −0.900 (p = 0.0833), −0.500 (p = 0.4500) and **−0.100 (p = 0.9500)** on
Arms A, B and C: decaying to nothing, significant on none, since over five
architectures only a perfect correlation clears 0.05 (floor 0.0167). **No claim is
made that ranking quality is a function of parameter count.**

Agreement between the per-arm orderings, exact permutation p-values; bold marks the
nominal level, which over five points only a perfect ordering reaches:

| Metric | A–B | A–C | B–C |
|---|---|---|---|
| ROC-AUC | +0.700, p = 0.2333 | +0.300, p = 0.6833 | +0.800, p = 0.1333 |
| PR-AUC | +0.900, p = 0.0833 | +0.700, p = 0.2333 | +0.600, p = 0.3500 |
| Balanced accuracy | +0.700, p = 0.2333 | +0.900, p = 0.0833 | +0.900, p = 0.0833 |
| F1 | **+1.000, p = 0.0167** | **+1.000, p = 0.0167** | **+1.000, p = 0.0167** |

Nine of twelve do not reach it, which is the more informative half: +0.300 between
the Arm A and Arm C ROC-AUC orderings is not evidence of agreement. Only F1
separates, ordering the five identically on all three; ROC-AUC is least stable,
consistent with the pairwise result above.

### 7.1.1 Arms A and C isolate the effect of balancing

Arms A and C share the trimming and the same 9,260 windows, differing only in
whether every drowsy window is retained (A, 770 drowsy) or each subject's own ratio
is preserved (C, 673), a controlled comparison, which no pair involving Arm B is.
On the ten subject-level differences:

| Model | ROC-AUC A → C | PR-AUC A → C | Bal. acc. A → C | F1 A → C |
|---|---|---|---|---|
| EEGNet | 0.884 → 0.883, p = 0.4922 | 0.431 → 0.407, p = 0.1055 | 0.708 → 0.718, p = 0.1055 | 0.388 → 0.382, p = 0.9102 |
| ShallowConvNet | 0.846 → 0.833, p = 0.6250 | 0.411 → 0.372, **p = 0.0039** | 0.700 → 0.694, p = 0.4316 | 0.354 → 0.312, **p = 0.0059** |
| CNN | 0.843 → 0.847, p = 0.8457 | 0.338 → 0.295, **p = 0.0020** | 0.618 → 0.599, p = 0.0742 | 0.267 → 0.219, **p = 0.0469** |
| DeepConvNet | 0.812 → 0.834, **p = 0.0488** | 0.405 → 0.386, p = 0.1934 | 0.627 → 0.628, p = 0.4922 | 0.310 → 0.300, p = 0.1641 |
| CNN-BiLSTM | 0.821 → 0.847, **p = 0.0488** | 0.399 → 0.377, p = 0.2324 | 0.696 → 0.714, **p = 0.0039** | 0.361 → 0.353, p = 0.9102 |

**Removing surplus drowsy windows raises the ranking quality of the two largest
architectures** (DeepConvNet +0.0217 and CNN-BiLSTM +0.0259 in ROC-AUC, both
significant, both rising on seven or more subjects), while leaving EEGNet untouched
(−0.0009, p = 0.4922). **PR-AUC and F1 move the other way for the three that do not
gain**, as expected at Arm C's lower prevalence. Balancing therefore changes which of
the lower four appears second-best and changes nothing about EEGNet.

### 7.1.2 Arms B and C isolate the effect of trimming

Arms B and C share the balancing rule, differing only in whether recordings are
first trimmed to the shortest. **Across all twenty tests (five architectures by four
metrics, each paired on the ten subject-level differences), not one reaches
significance**; the smallest p is 0.1309.

| Model | ROC-AUC B → C | PR-AUC B → C | Bal. acc. B → C | F1 B → C |
|---|---|---|---|---|
| EEGNet | 0.900 → 0.883, p = 0.3750 | 0.440 → 0.407, p = 0.1309 | 0.725 → 0.718, p = 0.7695 | 0.397 → 0.382, p = 0.6250 |
| ShallowConvNet | 0.847 → 0.833, p = 0.4922 | 0.399 → 0.372, p = 0.3223 | 0.706 → 0.694, p = 0.6250 | 0.319 → 0.312, p = 0.7695 |
| CNN | 0.866 → 0.847, p = 0.4922 | 0.360 → 0.295, p = 0.1602 | 0.601 → 0.599, p = 0.9102 | 0.245 → 0.219, p = 0.9453 |
| DeepConvNet | 0.793 → 0.834, p = 0.1602 | 0.384 → 0.386, p = 0.6953 | 0.621 → 0.628, p = 0.7695 | 0.271 → 0.300, p = 0.2500 |
| CNN-BiLSTM | 0.859 → 0.847, p = 0.9219 | 0.397 → 0.377, p = 0.9219 | 0.725 → 0.714, p = 0.9219 | 0.372 → 0.353, p = 0.8457 |

| Contrast | Factor isolated | Significant tests of twenty | Smallest p |
|---|---|---|---|
| A vs C | balancing | **7** | 0.0020 |
| B vs C | trimming | **0** | 0.1309 |

**Of the two choices, balancing matters and trimming does not**: a result, not an absence of one, since trimming costs about 7 % of the data for no measurable change.
Two caveats: trimming necessarily cuts the per-subject budget from 992 windows to
926 and shifts prevalence from 6.94 % to 7.27 %, consequences attributed to it here;
and a null on ten subjects is consistent with a real effect too small to detect, so
this is no *measurable* effect rather than no effect.

## 7.2 The CNN / CNN-BiLSTM ablation

The CNN and the CNN-BiLSTM share their convolutional trunk exactly, differing only
in what reduces the time axis: global average pooling against two bidirectional LSTM
layers. The shared trunk makes the feature extractor identical, but **this is not a
capacity-controlled comparison**: the recurrent block adds 135,936 parameters, 3.04
times the CNN's own total, taking the CNN-BiLSTM to 4.04 times it, so recurrence
cannot be separated from the capacity accompanying it. Subject-averaged, ten paired
differences:

| Metric | Arm A: CNN → BiLSTM | Arm B: CNN → BiLSTM | Arm C: CNN → BiLSTM |
|---|---|---|---|
| ROC-AUC | 0.843 → 0.821, p = 0.695 (4/10) | 0.866 → 0.859, p = 0.846 (4/10) | 0.847 → 0.847, p = 0.557 (6/10) |
| PR-AUC | 0.338 → 0.399, **p = 0.0059** (9/10) | 0.360 → 0.397, p = 0.232 (7/10) | 0.295 → 0.377, **p = 0.0039** (9/10) |
| Bal. acc. | 0.618 → 0.696, **p = 0.0098** (8/10) | 0.601 → 0.725, **p = 0.0020** (10/10) | 0.599 → 0.714, **p = 0.0039** (9/10) |
| F1 | 0.267 → 0.361, **p = 0.0195** (7/10) | 0.245 → 0.372, **p = 0.0195** (9/10) | 0.219 → 0.354, **p = 0.0039** (9/10) |

**Balanced accuracy and F1 improve on all three arms at the nominal level; no
ROC-AUC change reaches it on any arm**: not the same as no change, the point
estimate falling 0.022 on Arm A and 0.007 on Arm B. The recurrent block therefore
improves minority-class detection at a fixed threshold with no detectable change in
the ordering of windows at this sample size. PR-AUC reaches the nominal level on Arms
A and C but not Arm B (p = 0.232), so that gain replicates on the two trimmed
constructions only. This is the **closest architectural comparison** in the study,
the two networks sharing every layer except the one under test; it is deliberately
not called the cleanest *ablation*, for the capacity reason above.

## 7.3 At a fixed threshold, accuracy moves against every other measure

**Figure 3** shows what this section reports.

![Figure 3. Accuracy runs against recall on all three constructions.](../figures/figure3_accuracy_against_recall.png)

> **Figure 3. Accuracy runs against recall on all three constructions.** (a)–(c) one
> construction each, on shared axes; each point is one architecture, pooled recall
> horizontally against pooled accuracy vertically, with nothing joining them. The
> dashed rule is that construction's always-alert accuracy, without which an accuracy
> cannot be read at this prevalence; **on Arm B all five architectures lie below it.**
> Each panel gives the Spearman correlation between accuracy and recall (ρ = −1.000,
> −0.900, −0.600) with its exact two-sided permutation p over the 120 orderings of
> five ranks. Only Arm A reaches significance; the attainable floor over five
> architectures is 0.0167, so only a perfect reversal clears 0.05.

True positives come from the per-fold recall and drowsy-window counts in
`ALL_FOLDS.csv`; false positives are counted directly from the predictions in
`ALL_POOLED.csv`. They are **not** obtained by inverting per-fold precision, which is
undefined at precision zero, the case for every degenerate fold, including folds that
predicted some windows drowsy and got all of them wrong. Inverting precision
**under-counts false positives** by 0 to 17 windows per architecture here and moves
the accuracy column by up to 0.23 points, so Table 4 uses the recorded counts.

**Table 4. Pooled confusion matrices at the default 0.5 threshold, all three
constructions.** Counts summed over the ten folds within a seed, then averaged over
the five seeds; within each construction the architectures are ordered by accuracy.
Arm A holds 9,260 windows and 770 drowsy, always-alert accuracy 91.68 %; Arm B 9,920
and 688, 93.06 %; Arm C 9,260 and 673, 92.73 %. The four raw counts each row is
computed from (TN, FP, FN and TP) are in **Supplementary Table S2**, this table
complete. Bold marks the construction; no data cell is emphasised. **Recall and
accuracy carry ± the standard deviation across the five seeds; precision deliberately
does not**, being a ratio of two varying quantities, so that the mean of the per-seed
ratios and the ratio of the seed means differ (at the third decimal for fourteen of
the fifteen rows, by up to 0.023), and a ± would be a dispersion about a different
centre from the one printed. The printed precision is TP/(TP+FP) read off this
table's own counts; the per-seed range for each row is in the released registry.

| Arm | Model | Recall | Precision | Accuracy |
|---|---|---|---|---|
| **A** | DeepConvNet | 0.487 ± 0.105 | 0.574 | 92.73 ± 0.42 % |
| **A** | CNN | 0.506 ± 0.076 | 0.497 | 91.63 ± 1.17 % |
| **A** | CNN-BiLSTM | 0.646 ± 0.124 | 0.419 | 89.61 ± 0.93 % |
| **A** | EEGNet | 0.758 ± 0.019 | 0.405 | 88.71 ± 0.81 % |
| **A** | ShallowConvNet | 0.794 ± 0.017 | 0.304 | 83.17 ± 1.35 % |
| **B** | CNN | 0.377 ± 0.121 | 0.494 | 93.00 ± 0.90 % |
| **B** | DeepConvNet | 0.449 ± 0.186 | 0.461 | 92.54 ± 1.01 % |
| **B** | EEGNet | 0.772 ± 0.028 | 0.395 | 90.23 ± 1.35 % |
| **B** | CNN-BiLSTM | 0.658 ± 0.120 | 0.380 | 90.17 ± 1.22 % |
| **B** | ShallowConvNet | 0.787 ± 0.055 | 0.247 | 81.85 ± 6.22 % |
| **C** | DeepConvNet | 0.498 ± 0.043 | 0.564 | 93.56 ± 0.69 % |
| **C** | CNN | 0.493 ± 0.071 | 0.494 | 92.65 ± 1.09 % |
| **C** | EEGNet | 0.785 ± 0.021 | 0.390 | 89.50 ± 1.27 % |
| **C** | CNN-BiLSTM | 0.732 ± 0.062 | 0.377 | 89.28 ± 0.87 % |
| **C** | ShallowConvNet | 0.770 ± 0.057 | 0.257 | 82.19 ± 1.54 % |

**One row is far less stable than the rest.** ShallowConvNet on Arm B has pooled
accuracy 81.85 % with a seed SD of 6.22 points, ranging 70.88 % to 85.72 %, against a
largest seed SD of 1.5394 anywhere else in the column; it is the same architecture
and seed Section 7.5 flags for Brier (0.2246 against about 0.11 for the other four).
One run therefore accounts for much of the gap that makes it look reliably worst
here. Its ordering does not change, but the size of the gap is not stable.

**On all three arms accuracy runs against recall**: ρ = −1.000, −0.900 and −0.600,
and on all three the two most accurate architectures are exactly the two with the
lowest recall. The arms differ only in how far the best accuracy gets past the
always-alert baseline. On **Arm A** DeepConvNet alone exceeds it, while missing more
than half the drowsy windows. On **Arm B** *none* reaches it: the best, CNN at
93.00 % against 93.06 %, detects 38 % of drowsy windows. On **Arm C** DeepConvNet
reaches the study's highest accuracy, 93.56 %, detecting under half the drowsy
windows; its margin over the baseline is narrower than Arm A's, so Arm C supplies the
highest accuracy, not the widest margin.

Arm C is the strongest form of the argument: the architecture reaching the study's
highest accuracy would miss 338 of 673 drowsy windows, and on **ROC-AUC, PR-AUC,
balanced accuracy, F1 and recall** it is beaten by EEGNet, which scores 4.1 accuracy
points lower. **A model can exceed the always-alert baseline while detecting fewer
than half the events that accuracy is being used to judge it on.** That is why PR-AUC
and balanced accuracy are used throughout and accuracy is reported only here. **It is
not beaten on all measures, which is stated rather than omitted**: on Arm C
DeepConvNet has the lowest pooled Brier score of the five (0.0511 against the
class-prior reference 0.0674, EEGNet's 0.0952 being above it) and the highest pooled
precision (0.564 against 0.390).  **No architecture here is best on every
measure, and which appears best depends on which measure is asked for.**

### 7.3.1 Pooled and subject-averaged recall differ by a large margin

The recall column above is pooled. Subject-averaged recall (each subject weighted
equally, the convention used everywhere else in this paper) is substantially lower
for every architecture on every arm:

| Model | Arm A: subj-avg → pooled | Arm B: subj-avg → pooled | Arm C: subj-avg → pooled |
|---|---|---|---|
| EEGNet | 0.5217 → 0.7577 (+0.2360) | 0.5398 → 0.7721 (+0.2323) | 0.5343 → 0.7851 (+0.2508) |
| ShallowConvNet | 0.5725 → 0.7943 (+0.2218) | 0.5957 → 0.7875 (+0.1918) | 0.5687 → 0.7700 (+0.2012) |
| CNN | 0.2856 → 0.5062 (+0.2206) | 0.2318 → 0.3773 (+0.1456) | 0.2395 → 0.4933 (+0.2538) |
| DeepConvNet | 0.2885 → 0.4868 (+0.1982) | 0.2823 → 0.4488 (+0.1665) | 0.2865 → 0.4981 (+0.2116) |
| CNN-BiLSTM | 0.4756 → 0.6462 (+0.1707) | 0.5320 → 0.6584 (+0.1264) | 0.5258 → 0.7322 (+0.2064) |

The gap follows directly from Section 7.4: subjects contributing few drowsy windows
are the ones the models fail on, and pooling gives them almost no weight. The Arm C
CNN is the clearest case (0.2395 against 0.4933, a gap of 0.2538), where S8, S9 and
S10 contribute 8, 3 and 6 drowsy windows at recall 0.000 each and account for fifteen
of that architecture's twenty degenerate folds, while S7 contributes 238 windows at
recall 0.800 and S3 164 at 0.548. Both conventions are reported so that a reader who
pools the predictions obtains Section 7.3's figures rather than concluding the
subject-averaged figures elsewhere are in error.

Degenerate folds (the model predicts no drowsy window at 0.5, so F1 = 0 and balanced
accuracy = 0.500 by construction) occur for every architecture on every arm:

| Arm | EEGNet | ShallowConvNet | CNN | DeepConvNet | CNN-BiLSTM |
|---|---|---|---|---|---|
| A | 9 / 50 | 4 / 50 | 17 / 50 | 11 / 50 | 7 / 50 |
| B | 5 / 50 | 4 / 50 | 12 / 50 | 12 / 50 | 3 / 50 |
| C | 9 / 50 | 4 / 50 | 20 / 50 | 14 / 50 | 7 / 50 |

They depress F1 and balanced accuracy without affecting the threshold-free ROC-AUC
and PR-AUC. Arm C has the most, consistent with its being the trimmed construction
with the lower prevalence.

## 7.4 Between-subject variation dominates seed variation

**Figure 4** shows what this section reports.

![Figure 4. The variation that matters is between people, not between seeds.](../figures/figure4_subject_against_seed_spread.png)

> **Figure 4. The variation that matters is between people, not between seeds.**
> (a)–(c) one construction each, on shared axes. For each architecture, the standard
> deviation of subject-level PR-AUC across the ten subjects (filled mark) against the
> standard deviation across the five seed-level means (open mark), joined by a
> hairline; the axis is logarithmic because the two differ by roughly an order of
> magnitude, and open against filled carries the distinction without colour. The
> multiple ending each row is that architecture's ratio of the two; each panel title
> gives its construction's smallest and largest. Architectures are in parameter order
> in all three panels. An interval computed over seeds describes the distance to the
> open mark, not the distance that matters.

For every architecture on every arm the standard deviation of subject-level PR-AUC
across the ten subjects exceeds the standard deviation across the five seed-level
means by a wide margin:

| Arm | Ratio range over the five architectures |
|---|---|
| A | 12 to 48 times |
| B | 6 to 18 times |
| C | 10 to 36 times |

EEGNet's subject spread is 0.2692 against a seed spread of 0.0058 on Arm A and
0.2679 against 0.0074 on Arm C. Averaged over the five architectures, subject-level
PR-AUC ranges 0.027 to 0.810 on Arm A, 0.079 to 0.825 on Arm B and 0.022 to 0.818 on
Arm C, the minimum being S9 on Arms A and C and S8 on Arm B and the maximum S7 on all
three. *(This compares subject spread with* seed *spread; Section 7.7 shows seed
spread is not the whole of run-to-run variation, and the two should be read
together.)*

The spread tracks how many drowsy windows a subject contributes: the rank correlation
between a subject's drowsy-window count and its PR-AUC is positive for every
architecture on every arm. The second value in each cell subtracts that subject's own
prevalence before correlating, removing the chance baseline:

| Model | Arm A: raw / minus prevalence | Arm B: raw / minus prevalence | Arm C: raw / minus prevalence |
|---|---|---|---|
| EEGNet | +0.915 / +0.903 | +0.891 / +0.891 | +0.903 / +0.879 |
| ShallowConvNet | +0.952 / +0.891 | +0.830 / +0.806 | +0.915 / +0.879 |
| CNN | +0.927 / +0.867 | +0.588 / +0.442 | +0.976 / +0.915 |
| DeepConvNet | +0.927 / +0.891 | +0.915 / +0.891 | +0.903 / +0.879 |
| CNN-BiLSTM | +0.976 / +0.915 | +0.794 / +0.794 | +0.939 / +0.903 |

The correction answers the obvious objection (the chance level of PR-AUC being the
prevalence itself, a subject with more drowsy windows would score higher even from a
model that had learned nothing) and the correlation survives it almost undiminished:
**after correction ρ ≥ +0.79 with p ≤ 0.0061 on fourteen of the fifteen model–arm
combinations**. The exception is CNN on Arm B (ρ = +0.442, p = 0.200), the
architecture with the most degenerate folds there; on Arm C the same architecture
gives the table's *highest* correlation (+0.915, p = 0.0002), so the exception belongs
to that arm-by-architecture combination and not to the CNN. As a ratio rather than a
difference (PR-AUC divided by prevalence, the fold-change over chance), the relationship reverses, negatively and significantly on Arm B for four of five
architectures (ρ from −0.673 to −0.879, p ≤ 0.033) and significantly for none on Arms
A and C; that form is reported only because a reader may compute it, while the
difference form above is the one this paper uses and the one that replicates.

Two consequences follow: subject-level variation, not seed variation, is what an
interval on these results must represent, and the PR-AUC of a single fold is partly a
statement about the test subject's event count, which limits how far one subject's
result can be read.

## 7.5 Probability reliability

**Figure 5** is the headline of this section.

![Figure 5. Three of five architectures score worse than a constant predictor,](../figures/figure5_brier_partition.png)

> **Figure 5. Three of five architectures score worse than a constant predictor,
> identically on all three constructions.** Each mark is one architecture's pooled
> Brier score on one construction, minus that construction's class-prior reference
> π(1 − π): 0.0762, 0.0645 and 0.0674 for Arms A, B and C. Plotting the margin
> rather than the raw score is what lets three different references share one axis:
> zero is the constant predictor that ignores the EEG and emits the prior, and a mark
> to its right is a model whose probabilities are worse than that constant. Which
> side of the rule a mark falls on is the whole encoding: no colour coding, marker
> shape alone identifying the construction, so the figure reads unchanged in
> greyscale. **The partition is the same three architectures above and the same two
> below on every construction**, despite three different prevalences.


**Pooled Brier scores**, in which the predictions of all ten folds within a seed
are concatenated before scoring. ROC-AUC, PR-AUC and balanced accuracy in these
tables are likewise pooled, so each table is internally consistent; the
subject-averaged ROC-AUC values are in Section 7.1.

**Arm A** (class-prior Brier reference 0.0762)

| Model | ROC-AUC | PR-AUC | Bal. acc. | Brier |
|---|---|---|---|---|
| EEGNet | 0.9015 ± 0.0066 | 0.5103 ± 0.0631 | 0.8283 ± 0.0108 | **0.1010 ± 0.0050** |
| ShallowConvNet | 0.8801 ± 0.0065 | 0.4742 ± 0.0482 | 0.8147 ± 0.0038 | **0.1291 ± 0.0086** |
| CNN | 0.8762 ± 0.0075 | 0.4790 ± 0.0215 | 0.7298 ± 0.0286 | 0.0671 ± 0.0071 |
| DeepConvNet | 0.8703 ± 0.0257 | 0.4987 ± 0.0514 | 0.7270 ± 0.0471 | 0.0592 ± 0.0040 |
| CNN-BiLSTM | 0.8751 ± 0.0242 | 0.4913 ± 0.0460 | 0.7825 ± 0.0529 | **0.0781 ± 0.0062** |

**Arm B** (class-prior Brier reference 0.0645)

| Model | ROC-AUC | PR-AUC | Bal. acc. | Brier |
|---|---|---|---|---|
| EEGNet | 0.9190 ± 0.0052 | 0.5222 ± 0.0383 | 0.8421 ± 0.0104 | **0.0859 ± 0.0088** |
| ShallowConvNet | 0.8782 ± 0.0191 | 0.4302 ± 0.1178 | 0.8042 ± 0.0173 | **0.1369 ± 0.0495** |
| CNN | 0.8722 ± 0.0130 | 0.4084 ± 0.0722 | 0.6742 ± 0.0567 | 0.0577 ± 0.0056 |
| DeepConvNet | 0.8617 ± 0.0242 | 0.4134 ± 0.0904 | 0.7049 ± 0.0835 | 0.0603 ± 0.0047 |
| CNN-BiLSTM | 0.8740 ± 0.0306 | 0.4603 ± 0.0823 | 0.7891 ± 0.0546 | **0.0743 ± 0.0058** |

**Arm C** (class-prior Brier reference 0.0674)

| Model | ROC-AUC | PR-AUC | Bal. acc. | Brier |
|---|---|---|---|---|
| EEGNet | 0.9155 ± 0.0041 | 0.5079 ± 0.0501 | 0.8444 ± 0.0040 | **0.0952 ± 0.0071** |
| ShallowConvNet | 0.8614 ± 0.0280 | 0.3767 ± 0.0341 | 0.7980 ± 0.0278 | **0.1383 ± 0.0126** |
| CNN | 0.8764 ± 0.0107 | 0.4660 ± 0.0373 | 0.7269 ± 0.0279 | 0.0608 ± 0.0066 |
| DeepConvNet | 0.8874 ± 0.0196 | 0.5093 ± 0.0812 | 0.7340 ± 0.0230 | 0.0511 ± 0.0063 |
| CNN-BiLSTM | 0.8961 ± 0.0163 | 0.4775 ± 0.0442 | 0.8188 ± 0.0270 | **0.0808 ± 0.0078** |

**This partition is the most consistent result in the study.** On all three
constructions exactly the same three architectures (EEGNet, ShallowConvNet and
CNN-BiLSTM) exceed the class-prior Brier reference, and the same two (CNN and
DeepConvNet) fall below it (**Table 5**, Figure 5). The claim is about the
seed-averaged Brier score the table reports, not about every individual seed;
Section 7.7 gives the run-to-run variation bearing on this.

**Table 5. Pooled Brier score against each construction's class-prior reference.**
Bold marks a score *above* the reference, meaning probabilities worse than a
constant predictor that ignores the EEG and emits the class prior. The reference is
π(1 − π) and differs by construction, which is why the comparison is made within a
column rather than across the table.

| Model | Arm A (ref 0.0762) | Arm B (ref 0.0645) | Arm C (ref 0.0674) | |
|---|---|---|---|---|
| EEGNet | **0.1010** | **0.0859** | **0.0952** | above ×3 |
| ShallowConvNet | **0.1291** | **0.1369** | **0.1383** | above ×3 |
| CNN-BiLSTM | **0.0781** | **0.0743** | **0.0808** | above ×3 |
| CNN | 0.0671 | 0.0577 | 0.0608 | below ×3 |
| DeepConvNet | 0.0592 | 0.0603 | 0.0511 | below ×3 |

Three constructions, three prevalences, three reference values, one identical
partition. All five architectures are covered on all three arms, the Brier score
needing only the pooled predictions `ALL_POOLED.csv` records for every run.

The narrow margins are stated rather than hidden. Above the reference they run from
**+0.0019** (CNN-BiLSTM on Arm A, 0.0781 against 0.0762) to +0.0724 (ShallowConvNet
on Arm B); below it from −0.0042 (DeepConvNet on Arm B) to −0.0170 (DeepConvNet on
Arm A). The two sitting closest to their reference are each comfortably on the same
side of it on the other two arms (+0.0098 and +0.0134; −0.0170 and −0.0163). **What
replicates is the side of the reference each architecture falls on, three times out
of three; the size of the margin is not claimed to be stable.**

The three exceeding the reference include the best-ranking architecture on every arm,
so ranking quality and probability reliability are separate properties: an
architecture can order windows well and still emit probabilities worse, scored as
probabilities, than a constant predictor emitting the prior. **No monotone coupling
is claimed**: the rank correlation between ROC-AUC and pooled raw Brier reaches
significance on no arm (the floor at five points being about 0.017), and ranges from
ρ = −0.100 (p = 0.9500) to +0.800 (p = 0.1333) depending on arm and on which average
of ROC-AUC is used. What *is* claimed is the separation and the partition's
membership, a matter of sign rather than rank, which does not depend on the
estimator.

### 7.5.1 Expected calibration error

Expected calibration error is reported **subject-averaged**: it is computed on each
held-out subject with ten equal-width bins and then averaged over the ten subjects
and the five seeds. This is the same convention as every paired test in the paper.
It is available for the architectures whose per-window probability files were
retained: three per arm.

*A note on the Brier column, which invites a reasonable objection.* The
subject-averaged Brier scores below are numerically identical to the pooled ones of
Section 7.5, which looks like the estimator mixing this paper says it never does. It
is not: **the Brier score is a mean of squared errors and every subject contributes
the same number of windows on every arm** (926, 992 and 926), so the mean of the ten
per-subject means equals the pooled mean exactly. The two coincide for this one
metric on this one dataset, only because the per-subject budgets are equal by
construction; they do not coincide for ECE, for recall, or for anything else.

| Arm | Model | ROC-AUC (subject-averaged) | ECE raw | Brier raw |
|---|---|---|---|---|
| A | EEGNet | 0.884 | 0.1950 | 0.1009 |
| A | CNN-BiLSTM | 0.821 | 0.0912 | 0.0781 |
| A | CNN | 0.843 | **0.0605** | 0.0671 |
| B | EEGNet | 0.900 | 0.1717 | 0.0859 |
| B | ShallowConvNet | 0.847 | 0.2049 | 0.1369 |
| B | DeepConvNet | 0.793 | **0.0679** | 0.0603 |
| C | EEGNet | 0.883 | 0.1918 | 0.0952 |
| C | ShallowConvNet | 0.833 | 0.2001 | 0.1383 |
| C | DeepConvNet | 0.834 | **0.0460** | 0.0511 |

**On every arm the architecture with the best raw calibration is one of the
lower-ranking ones**, and EEGNet's calibration error is 2.5 to 4.2 times the
best-calibrated architecture's on the same arm (3.2 × on Arm A, 2.5 × on Arm B,
4.2 × on Arm C), the Brier partition's separation seen through a second measure, and
now three times.

*Pooled expected calibration error is systematically smaller*, one subject's
over-confidence cancelling another's under-confidence. On Arm A the pooled raw values
for the same three are CNN 0.0526, CNN-BiLSTM 0.0792 and EEGNet 0.1944; on Arm B, for
the two architectures without subject-level files, CNN 0.0435 and CNN-BiLSTM 0.0862.
These are given for completeness, are **not** comparable with the subject-averaged
column above, and no analysis in this paper mixes them.

## 7.6 Out-of-subject logistic recalibration removes the reliability gap

**Figure 6** shows what this section reports.

![Figure 6. A single logistic function per fold, fitted on the other nine](../figures/figure6_recalibration.png)

> **Figure 6. A single logistic function per fold, fitted on the other nine
> subjects, brings every measured architecture below the reference.** (a)–(c) one
> construction each, on shared axes. Horizontal axis: **subject-averaged** Brier score
> minus the same construction's class-prior reference, zero being the constant
> predictor, the reference of Figure 5, but against the subject-averaged score, since
> every value in this section is subject-averaged. One row per architecture: open mark
> raw, filled mark after out-of-subject Platt scaling, hairline the change, on Figure
> 4's convention and without colour. Rows are ordered by raw score, worst at the top.
> Every architecture that began right of the rule ends left of it, on all three
> constructions. **The three architectures per panel are those whose per-window
> probabilities were retained, and they are not the same three on each
> construction**: CNN, CNN-BiLSTM and EEGNet on Arm A; DeepConvNet, EEGNet and
> ShallowConvNet on Arms B and C. **On Arm A, where the released scores allow it to be
> measured**, recalibration leaves the subject-averaged ROC-AUC and PR-AUC unchanged
> at the reported precision; that measurement does not extend to Arms B and C.


Scores were recalibrated by Platt scaling (a logistic function fitted on the logit)
and separately by isotonic regression. **For each leave-one-subject-out fold a
separate calibrator was fitted on the other nine subjects of the same seed and
applied to the held-out subject**, giving fifty calibrators per architecture per arm,
none of which saw the subject it scored. All values are subject-averaged.

**Coverage.** Per-window probability files were retained for CNN, CNN-BiLSTM and
EEGNet on Arm A and for DeepConvNet, EEGNet and ShallowConvNet on Arms B and C, so
the analysis rests on three architectures per arm; the two sets differ, so between
them all five are covered and only EEGNet on all three. The effect of each
recalibration is given in **Table 6**.

**Table 6. Expected calibration error and Brier score, raw and after each
recalibration, all three constructions.** **Bold marks a Brier + Platt value that
Platt recalibration carried from above the construction's class-prior Brier
reference to below it**: 0.0762 on Arm A, 0.0645 on Arm B, 0.0674 on Arm C. The
mark appears in that one column only: the reference is π(1 − π), a Brier-scale
quantity, and there is no corresponding reference against which a calibration error
could be marked. Only three architectures
per construction retained per-window probabilities, and the two sets differ, so
between them all five are covered and only EEGNet is covered on all three. The three expected-calibration-error columns are given for every row in
**Supplementary Table S4**, which is this table complete; their reading is in
the paragraphs below, which give the direction and range of the change for
every architecture.

| Arm | Model | Brier raw | Brier + Platt | Brier + isotonic |
|---|---|---|---|---|
| **A** | CNN | 0.0671 | 0.0585 | 0.0604 |
| **A** | CNN-BiLSTM | 0.0781 | **0.0590** | 0.0599 |
| **A** | EEGNet | 0.1009 | **0.0635** | 0.0610 |
| **B** | DeepConvNet | 0.0603 | 0.0592 | 0.0577 |
| **B** | EEGNet | 0.0859 | **0.0538** | 0.0522 |
| **B** | ShallowConvNet | 0.1369 | **0.0584** | 0.0583 |
| **C** | DeepConvNet | 0.0511 | 0.0529 | 0.0528 |
| **C** | EEGNet | 0.0952 | **0.0573** | 0.0551 |
| **C** | ShallowConvNet | 0.1383 | **0.0658** | 0.0663 |

**The same count on all three arms.** Before recalibration, two of the three
architectures are *above* the class-prior Brier reference on each arm (CNN-BiLSTM
and EEGNet on Arm A, EEGNet and ShallowConvNet on Arms B and C) and one is below
it (CNN 0.0671 on Arm A, DeepConvNet 0.0603 on Arm B, DeepConvNet 0.0511 on Arm C).
After Platt scaling **none is above the reference on any arm**: three of three fall
below it, three times. The Arm A set of three architectures differs from the
Arm B set, but **the Arm B and Arm C sets are the same three architectures**, so
this is two distinct sets of three rather than three independent ones. The
replication is across constructions, not across architectures.

The architectures whose reliability was worst improve the most: on Arm A EEGNet's
calibration error falls 0.1950 → 0.0625 and CNN-BiLSTM's 0.0912 → 0.0561; on Arm B
ShallowConvNet's falls 0.2049 → 0.0605 and EEGNet's 0.1717 → 0.0547; on Arm C
ShallowConvNet's falls 0.2001 → 0.0724 and EEGNet's 0.1918 → 0.0580.

On the ten subject-level differences, raw against Platt:

| Arm | Model | Brier | ECE |
|---|---|---|---|
| A | CNN | p = 0.0488 (9/10) | p = 0.084 (7/10) |
| A | CNN-BiLSTM | p = 0.0488 (9/10) | p = 0.0488 (9/10) |
| A | EEGNet | p = 0.0371 (8/10) | **p = 0.0020 (10/10)** |
| B | DeepConvNet | p = 0.770 (5/10) | p = 0.770 (4/10) |
| B | EEGNet | p = 0.0488 (8/10) | **p = 0.0020 (10/10)** |
| B | ShallowConvNet | p = 0.0273 (9/10) | p = 0.0039 (9/10) |
| C | DeepConvNet | p = 0.557 (6/10) | p = 0.625 (6/10) |
| C | EEGNet | p = 0.0371 (9/10) | **p = 0.0020 (10/10)** |
| C | ShallowConvNet | p = 0.0371 (8/10) | p = 0.0059 (9/10) |

**EEGNet (the only architecture measured on all three arms) improves its
calibration error on all ten subjects on all three, at p = 0.0020, the attainable
floor.** That is thirty subject-level improvements out of thirty. DeepConvNet does
not improve significantly on either arm where it was measured, which is consistent
rather than contradictory: it was the best-calibrated architecture before
recalibration on both, so there was little to correct. On Arm C its calibration
error is nominally slightly worse after Platt scaling (0.0460 → 0.0502, p = 0.625),
which is the expected behaviour of fitting a two-parameter correction to something
that needs none.

**Platt scaling leaves the subject-averaged ROC-AUC and PR-AUC unchanged at the
reported precision, and this was measured rather than assumed.** A logistic map
preserves the ordering only when its fitted slope is positive, and on Arm A (the arm
whose per-window scores are released), all 150 fitted slopes are positive (0.3243 to
1.3312). The residual within-fold movement has an identified cause: the ε-clip before
the logit maps every score below it to one value, creating ties on 10 of the 150 folds
and up to 95 on one, moving a single fold's ROC-AUC by at most 0.0000397267 and its
PR-AUC by at most 0.003413347. On the quantity the tables actually print, the largest
observed changes were 0.0000009981 in ROC-AUC and 0.0000222899 in PR-AUC, both for
EEGNet, with CNN and CNN-BiLSTM showing zero change at the reported precision.

**That is the whole of the measurement**: three architectures on one arm, three of the
fifteen architecture-by-arm cells Table 3 reports, because the recomputation needs
per-window scores and those are released for Arm A only. For the other twelve cells
the property is untested rather than established. **Nor does the invariance extend to
pooled post-recalibration metrics**: separate Platt maps per fold need not preserve
the ordering of scores across folds, so pooled post-recalibration ROC-AUC and PR-AUC
were not used as reported ranking metrics.

Read together, these measurements are consistent with the reliability gap being a
matter of the scale of the scores rather than of their ordering: on Arm A the
ordering is essentially unchanged while one map per fold, fitted without seeing the
test subject, brings every measured architecture below the reference on every
construction. Since the recalibration was not an intervention on ordering, that is an
inference from two measurements set side by side rather than a demonstration.
Isotonic regression reaches comparable values and is not uniformly better, consistent
with its greater flexibility being a liability at these fold sizes.

## 7.7 Run-to-run variability differs sharply between architectures

Two repeated-execution checks exist, and they cover different things.

**Check 1: Arm B, three architectures.** Arm B was executed twice, several hours
apart, under identical preprocessing, seeds and validation-subject pairs (all 150
confirmed identical), so the runs differ only in GPU non-determinism. CNN and
CNN-BiLSTM were *not* re-executed: their rows in the earlier file are bit-identical
to the later one, so the check covers the three architectures tabulated below.

**Check 2: Arm A, EEGNet only.** An earlier Arm A execution of EEGNet agrees with
the current run to full floating-point precision on balanced accuracy and F1 for 44
of 50 folds and on recall for 49 of 50; no mean differs by more than 0.0008 (ROC-AUC
0.8840 against 0.8840, PR-AUC 0.4317 against 0.4314, balanced accuracy 0.7092 against
0.7084), and the largest single-fold ROC-AUC difference is 0.0032. **This check is
weaker than Check 1: the earlier run did not record its validation-subject
assignments, so the two runs cannot be confirmed to have drawn the same pairs, and
the difference cannot be attributed to GPU non-determinism alone.**

**Which run the released scores come from.** The Arm A per-window files hold the
**earlier** EEGNet execution, not the tabulated one; the CNN and CNN-BiLSTM files hold
the tabulated run. Recomputing from the released EEGNet scores therefore gives PR-AUC
0.4317 against the 0.4314 printed here and balanced accuracy 0.7092 against 0.7084,
ROC-AUC agreeing to four decimals. **The Brier score moves too, and is listed because
it is the one place the two files disagree in a number the paper prints twice**: the
calibration summary gives 0.1009 for EEGNet on Arm A where the results tables give
0.1010. Every Arm A fold holds the same 926 windows, so pooled and subject-averaged
Brier are the same quantity, and they agree to sixteen decimal places for CNN and
CNN-BiLSTM, which is how this is known to be a run-to-run difference and not an
estimator difference. It is stated because a reproduction disagreeing silently in the
fourth decimal would look like an error; `tools/check_released_scores.py` reports it
for every released file.

**Arm C was not repeated.** EEGNet is therefore the only architecture examined on two
arms, and its largest single-fold ROC-AUC movement is 0.0002 on Arm B against 0.0032
on Arm A: small in both, but an order of magnitude apart, itself a reason not to
treat one reproducibility check as settling the question.

| Model | mean ROC-AUC, run 1 / run 2 | largest single-fold difference | folds identical |
|---|---|---|---|
| EEGNet | 0.9003 / 0.9003 | **0.0002** | 27 / 50 |
| ShallowConvNet | 0.8415 / 0.8472 | 0.2219 | 1 / 50 |
| DeepConvNet | 0.7900 / 0.7930 | 0.2020 | 0 / 50 |

"Identical" means agreeing to within 1 × 10⁻¹²; of EEGNet's 27 such folds, 25 are
identical bit for bit.

EEGNet is reproducible to four decimal places; the other two are not. **How far they
move depends on which average is taken, and both are reported because only the larger
one bears on how the tables should be read.**

| Model | ROC-AUC: overall / largest subject / seed SD | F1: overall / largest subject / seed SD |
|---|---|---|
| ShallowConvNet | 0.0057 / **0.0334** / 0.0141 | 0.0010 / **0.0702** / 0.0336 |
| DeepConvNet | 0.0030 / **0.0407** / 0.0328 | 0.0213 / **0.1273** / 0.0562 |

The *overall* shift (the mean over all fifty folds) is small, at most 0.0057 in
ROC-AUC and 0.0213 in F1. An individual *subject's* mean shifts four to fourteen
times further, and **for both architectures and both metrics it exceeds the
seed-to-seed standard deviation this paper reports as the ±**: a single subject's
ROC-AUC moves 0.0407 for DeepConvNet against a reported ± of 0.0328, its F1 0.1273
against 0.0562. 

The consequence for reading the tables above is direct. For ShallowConvNet and
DeepConvNet the ± over five seeds **understates** the run-to-run uncertainty, because
the seeds share one execution, and a single subject's value moves further between two
identical runs than that ± allows, a further reason not to read Section 7.1's
intermediate ordering as meaningful, which Section 7.1 withdraws on independent
grounds. For architectures not repeated the reported ± is likewise a lower bound:
four of five on Arm A, two of five on Arm B, and all five on Arm C.

The Arm B numbers reported here are from **run 2**, because the recalibration
described in Section 6.6 was computed from that run's probabilities. Run 1 is retained in
`backup/ALL_FOLDS_armB_run1.csv`.


Thresholds maximising F1 and maximising balanced accuracy were also selected out of subject, on the same nine-subject basis, and applied to the held-out subject on Arms A and C; the rule helped in one architecture-and-arm combination and not in the others, and Section 8.6 reads that result. The per-fold offsets and every paired test behind it are in Supplementary Note 2.

## 7.9 Summary of findings

Every figure below is reported with its evidence in the section named; this list
restates, it does not add.

1. **EEGNet ranks best on all three arms** (Section 7.1): higher mean ROC-AUC in all twelve
   paired comparisons, nominal in eleven (exception p = 0.0645), five on the
   attainable floor of 0.0020; highest PR-AUC on all three.
2. **No other pair separates on ROC-AUC** (Section 7.1): none of the six non-EEGNet pairs is
   significant on any arm (smallest p = 0.0840), and no claim is made that
   DeepConvNet ranks lowest. Those same pairs *do* separate on balanced
   accuracy, four to five of six per arm, so the failure is specific to ranking.
3. **Parameter count is not shown to predict ranking quality** (Section 7.1): ρ decays
   −0.900 (p = 0.0833) → −0.500 → **−0.100 (p = 0.9500)**, nominal on none. Withdrawn
   as unsupported, not refuted: five points cannot settle it either way (Section 6.5).
4. **Balancing matters; trimming does not** (Section 7.1.1 to Section 7.1.2): balancing moves
   DeepConvNet 0.0217 and CNN-BiLSTM 0.0259 in ROC-AUC (both p = 0.0488), EEGNet
   unchanged: seven of twenty significant; trimming, **zero of twenty, smallest
   p = 0.1309**, despite costing about 7 % of the data.
5. **The recurrent block improves detection at a fixed threshold on all three arms**
   (Section 7.2): balanced accuracy and F1 nominal on all three, no ROC-AUC change nominal on
   any; the PR-AUC gain replicates on the two trimmed arms only.
6. **Accuracy is insufficient for comparing models here** (Section 7.3): accuracy and pooled
   recall are negatively rank-correlated on all three (ρ = −1.000, −0.900, −0.600;
   only the first nominal, on the floor). On Arm C the most accurate architecture
   misses 338 of 673 drowsy windows and is beaten by EEGNet on five metrics though
   **not** on pooled Brier or precision; on Arm B none reaches the baseline.
7. **Pooled and subject-averaged recall differ by 0.13 to 0.25** everywhere (Section 7.3.1),
   because the subjects with fewest drowsy windows are the ones the models fail on.
8. **Between-subject variation exceeds seed variation 12–48 ×, 6–18 × and 10–36 ×**
   (Section 7.4), and subject-level PR-AUC tracks the drowsy-window count even after the
   prevalence baseline is removed (ρ ≥ +0.79, p ≤ 0.0061 on fourteen of fifteen).
9. **Ranking quality and probability reliability are separate, with an identical
   partition on all three arms** (Section 7.5): EEGNet, ShallowConvNet and CNN-BiLSTM above
   the class-prior Brier reference, CNN and DeepConvNet below, all five covered. No
   monotone coupling is claimed.
10. **Out-of-subject recalibration removes the reliability gap on all three arms**
    (Section 7.6), leaving subject-averaged ROC-AUC and PR-AUC unchanged at the reported
    precision; EEGNet improves its calibration error on thirty of thirty
    subject-arms, p = 0.0020 each.
11. **Threshold selection helps only where the scores are stably offset**: three
    significant gains of twenty-four, all DeepConvNet on Arm C, and four significant
    losses (Supplementary Note 2).
12. **Reproducibility is architecture-dependent** (Section 7.7): EEGNet reproduced to four
    decimals while two others moved single folds by over 0.20 in ROC-AUC and a
    subject's mean by up to 0.0407 and 0.1273, exceeding the reported ± in every
    case. Only three architectures were re-executed, so for the rest the reported ±
    is untested as an uncertainty estimate.

## 7.10 Multiplicity

This study performs **190 distinct inferential comparisons** across 12 analysis
families, of which **82 yielded nominal p < 0.05**. That count is not homogeneous:
**32 of the 82 come from the 45-comparison drowsy-count family** and **50 from the
remaining 145**. The family is separated throughout for that reason, and because what
it measures (that PR-AUC rises with a subject's event count) is close to a property
of the metric, which is why Section 7.4 also reports the prevalence-corrected form.
For context on the disclosure rather than as a test: 82 against a global-null
reference count of 9.5 at α = 0.05, and 50 against 7.25 once the prevalence family is
removed. The comparisons are dependent and were not generated under a single
global-null experiment, so this is descriptive and **not** a formal global-null test.
The per-family breakdown is in Supplementary Table S5 and is released as
`results/MULTIPLICITY.csv`.

**The result that matters here.** Treating all 190 as one family, Benjamini–Yekutieli
retains 24, and **all 24 are from the drowsy-count family**; applied to the remaining
145 alone it retains none. Every architecture comparison, arm contrast, recalibration
and threshold-selection result falls under arbitrary-dependence control over a single
family of this size.

That is a statement about ten subjects, not a verdict on the findings: a procedure
whose sole survivor is the result closest to being a property of the metric is
reporting that 190 dependent comparisons on ten subjects cannot support family-wise
or arbitrary-dependence control. Section 6.5.1 reaches the same conclusion from the
other direction: past a family of twenty-five ten-subject Wilcoxon tests, Holm
cannot reject for any dataset at all. **This paper therefore does not claim that its
findings survive multiplicity control.** Results are stated as nominal, and the two
depending most directly on inference, that balancing changes architecture ranking
where trimming does not (Section 7.1.1), and that threshold selection improves
balanced accuracy and F1 (Supplementary Note 2), are the two that weaken most under
correction and are worded accordingly.


A finding is claimed for all three constructions only where it replicates on all three. The analyses that do not cover all three, and what each one does cover, are set out in Supplementary Note 3 and Table S3.

## Notes for the next pass — not part of the paper

- Section 7.4 was retitled from "dominates run-to-run variation" to "dominates **seed**
  variation", resolving the conflict with Section 7.7 noted in draft 3.
- **Methods must state**: the averaging convention exactly as the Overview does;
  that expected calibration error uses ten equal-width bins; that Arm C was executed
  on a different GPU configuration (T4 × 2) from Arms A and B, which is why Arm C is
  not part of the repeated-execution check.
- The Arm A ShallowConvNet and DeepConvNet calibration rows of draft 2 remain
  withdrawn for want of a source. If those probability files are ever recovered,
  Section 7.6 Arm A becomes five architectures; nothing else changes.
- **Threshold selection was not run on Arm B.** It is the only remaining coverage
  gap and should be recorded as a one-line limitation rather than filled: the Arm B
  probability files exist, but repeated attempts to run it were blocked by the
  execution platform dropping attached inputs.
- The fourth cell of the design — untrimmed with every drowsy window kept — was not
  run. It is no longer needed to isolate a factor, since A vs C isolates balancing
  and B vs C isolates trimming; it would give a second instance of each contrast.
- Subject demographics are now fully sourced: **ten volunteers, seven male and three
  female** from the recording filenames, **aged 20 to 50** from the dataset deposit's
  own description. This item is closed.
- Rule in force: a number enters the manuscript only if it appears in
  `MASTER_NUMBERS.csv`, and `registry.py` is re-run on the day of any edit.
