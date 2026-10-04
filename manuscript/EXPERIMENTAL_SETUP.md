# 6 Experimental Setup — draft 1

How the architectures of Section 5 were trained and evaluated on the window sets
of Section 4, and what is and is not reproducible from the released files.

## 6.1 Subject-independent evaluation

Leave-one-subject-out cross-validation was used. In each fold one subject is held
out entirely for testing; of the remaining nine, two are drawn at random as the
validation set and seven are used for training. The three sets are disjoint at the
subject level, and no window from the test subject takes part in training, early
stopping or any other selection.

Each architecture was run under five random seeds, {42, 1, 2, 3, 4}, giving 50
folds per architecture per arm, 250 folds per arm and 750 folds in total. The
validation pair for a given (seed, test subject) is drawn before any resume check,
so the random sequence is identical whether a run completes in one session or is
resumed. This was verified: within an arm, all 50 validation pairs are identical
across all five architectures, so the architectures are compared on the same folds
and not merely on the same subjects.

## 6.2 Normalisation and class weighting

Per-channel z-score statistics (one mean and one standard deviation per channel)
were computed on the training fold only and applied unchanged to the validation and
test folds; no statistic crosses from the held-out subject into training.

Class imbalance was handled by weighting the loss, not by resampling: the drowsy
class takes the ratio of alert to drowsy windows in that fold's training set, the
alert class weight one. No synthetic minority oversampling was used, since it would
fabricate EEG windows that no participant produced.

## 6.3 Training

All models were trained with the Adam optimiser at a learning rate of 1 × 10⁻³,
binary cross-entropy loss, batch size 64, for at most 60 epochs. Training stopped
early when validation average precision had not improved for 8 epochs, and the
weights of the best validation epoch were restored. Average precision is monitored
rather than loss or accuracy because it is the quantity the minority class is
judged on.

Every fold records the epochs actually used and its two validation subjects, so the
composition of each of the 750 folds is recoverable from the result files.

Arms A and B were trained on an NVIDIA Tesla P100-PCIE-16GB. **Arm C was trained on
a different configuration, two NVIDIA T4 GPUs**, because the P100 was not available
when it was run; the protocol was otherwise identical. This is why Arm C is excluded
from the repeated-execution check of Section 6.7, which compares runs on matched
hardware.

## 6.4 Metrics

Threshold-free ranking quality is reported as ROC-AUC and as PR-AUC (average
precision); threshold-dependent behaviour at the default threshold of 0.5 as
balanced accuracy, F1, precision and recall. **Accuracy is reported descriptively
and relative to the always-alert reference, never as the criterion for ranking the
architectures, and no conclusion about which architecture is preferable rests on
it.** It is analysed in Section 7, its rank relation to recall is one of the paper's
findings.

Probability quality is reported as the Brier score and as the expected calibration
error with ten equal-width bins. The two are named distinctly: the Brier score
is a proper scoring rule combining calibration and refinement, so it is described as
probability reliability, while *calibration* is reserved for the expected calibration
error and reliability diagrams.

Two levels of aggregation are used and are always named. **Subject-level** values
are computed within a fold and then averaged over the ten subjects, so every subject
counts equally. **Pooled** values concatenate the predictions of all ten folds of a
seed before scoring, so they reflect the deployed mixture. The two do not coincide
when subjects differ in difficulty.

## 6.5 Statistical testing

Comparisons between architectures use the Wilcoxon signed-rank test on the **ten
subject-level differences**, never on the fifty folds, since folds from the same
subject share a test set and are not independent. With ten paired observations the
smallest attainable p-value is 2/2¹⁰ = 0.00195, and this floor is stated wherever a
p-value approaches it.

**The floor rises when a pair ties.** The implementation discards zero differences,
so a comparison in which one subject scores identically under both architectures is
a test on nine pairs, and its floor is 2/2⁹ = 0.00391, twice the value above. One
comparison in this study has such a tie, and its p-value is reported against the
nine-pair floor.

Relationships across architectures use Spearman rank correlation over the five
architectures with **exact** p-values: every one of the 5! = 120 orderings of five
ranks is enumerated and the two-sided p is the proportion at least as extreme as the
observed correlation. The *t*-approximation that packages return by
default is not used at this sample size, because it returns values the sample cannot
produce, including zero for a perfect correlation, which is a
division by zero rather than a probability.

The consequence is a hard floor: two of the 120 orderings are at least as extreme as
a perfect correlation, so the smallest attainable two-sided p-value is
2/120 = 0.0167 and **nothing short of a perfect rank reversal can reach p < 0.05
across five architectures at all.** A significant result here sits on the floor by
construction and is reported as an association across a small set, not an
established law.

Correlations over the ten subjects are a different case: the approximation is sound
at that size, so those p-values are the *t*-approximation. This was checked: recomputing all forty-five exactly changes no verdict at α = 0.05 (`tools/check_spearman_p.py`).

Dispersion is reported as a standard deviation, with the quantity it is taken over
named: the five seed-level means for run-to-run variability, the ten subjects for
between-subject spread. **A third convention appears once**, for the selected
thresholds of Supplementary Note 2, where the spread is taken over the fifty folds
directly because a threshold is chosen per fold and there is no intermediate average.
A fifty-fold standard deviation blends subject and seed variation and is **not
comparable with either of the other two**; it is named again in that section's table
and used only to say how widely a chosen threshold moves, never as an uncertainty on
a reported score.

### 6.5.1 Multiplicity, and why the analyses are reported as exploratory

The nominal level throughout is α = 0.05. This study performs **190 distinct
inferential comparisons** in 12 analysis families, one per question asked. The count
is not an estimate: `src/multiplicity.py` re-runs every family against the released
fold data and writes `results/MULTIPLICITY.csv`, and the released test suite fails if that table
and a fresh recomputation disagree. A comparison performed twice under
two names (the CNN against CNN-BiLSTM ROC-AUC test, which appears both among the
architecture pairs and in the ablation) is counted once.

**The analyses are exploratory, and the p-values are reported as nominal.** Two
measurements led to that decision, both properties of the design rather than of the
results.

The first is that a step-down family-wise procedure cannot operate at this sample
size. Holm's first threshold is α/m, so a test whose smallest attainable p exceeds
α/m cannot reject for *any* dataset once the family reaches that size. The ten-pair
Wilcoxon floor gives a ceiling of m = 25, the nine-pair floor m = 12, and the
five-point Spearman floor m = 3; beyond those sizes the procedure returns the same
verdict whatever the data show, which is an absence of measurement rather than
conservatism. The Spearman ceiling is reached with exact equality — 2/5! and α/3 are
both 1/60 — so this study's accuracy-against-recall result sits precisely on the
Holm boundary for its three-test family, and whether it survives turns on whether
the comparison is written ≤ or <. A criterion that a convention decides is not one
this paper will rest a claim on.

The second is that the comparisons are dependent: they share subjects and folds,
overlap in architecture pairs, and use four metrics computed from the same
predictions. Benjamini–Hochberg controls the false discovery rate under independence
or positive regression dependency, which is plausible here but is not established;
Benjamini–Yekutieli holds under arbitrary dependence and is therefore also reported.

**Both are reported per family as sensitivity analyses, not as the decision rule**,
and Section 7.10 gives the table. No claim in this paper rests on a comparison
having survived a correction: where a result is called significant, it is significant
at the nominal level, and the reader is given what correction would do to it.

## 6.6 Recalibration and threshold selection

Two post-hoc corrections were evaluated, both fitted **out of subject**: for a
held-out subject the correction is fitted on the predictions for the other nine and
applied to that subject, so no label from the test subject enters the fit.

The first is Platt scaling: a logistic function fitted on the logit of the model's
output, effectively unpenalised. The second is isotonic regression.

**A logistic mapping is strictly increasing when its fitted slope is positive**, and
only then; a negative slope would reverse the ranking. That is a property of the
fits, not of the method, so it was measured. On Arm A, the construction whose per-window scores are released, **all
150 fitted slopes are positive**, ranging from 0.3243 to 1.3312. Neither per-fold
movement is exactly zero, and the residual has an identified cause: the ε-clip
applied before the logit maps every score below the clip to a single value, creating
ties on 10 of the 150 folds and as many as 95 on one, which moves a single fold's ROC-AUC by at most 4 × 10⁻⁵ and its PR-AUC by at
most 0.0034.

**A per-fold bound does not settle whether a reported table moves**, because the
tables print an average over fifty folds, which absorbs per-fold movement; the
reported quantity was therefore measured directly. For the subject-averaged metrics
of Table 3 and Section 7.1, ROC-AUC and PR-AUC were recomputed after applying the
fold-specific Platt calibrators; at the reported precision the subject-averaged
values were unchanged. **This statement is restricted in two ways.** It holds for the
subject-averaged aggregation used for the reported ranking metrics, and does not
imply invariance of pooled metrics under different fold-specific calibration maps. It
is also restricted in coverage: the recomputation requires per-window probability
scores, released for Arm A only, so it covers three architectures on one arm, three of the fifteen
architecture-by-arm cells Table 3 reports. For the other twelve the property is
untested, not established.

**Platt-recalibrated ROC-AUC and PR-AUC are therefore reported as unchanged at the
reported precision, not as algebraically invariant**, because the stronger claim is
false as implemented. `tools/check_monotonicity.py` regenerates the per-fold figures
and `tools/check_ranking_invariance.py` the subject-averaged ones.

Isotonic regression is only **non-decreasing**: its flat regions merge distinct
scores into ties, which can lower ROC-AUC and PR-AUC and cannot raise them beyond
ties already present. This too was measured: on the same 150 folds it
lowers ROC-AUC on 123 and PR-AUC on 144, and reduces the median number of distinct
scores per fold from 926 to 25. It is reported alongside Platt scaling, and no
ranking-invariance claim is made for it.

Fifty calibrators are fitted per architecture per arm, one per fold, none of which
sees the subject it is applied to; fitting a single calibrator on all predictions at
once would leak the test subject into its own correction.

Separately, decision thresholds maximising F1 and maximising balanced accuracy were
selected on the same nine-subject basis and applied to the held-out subject, to test
whether moving the threshold recovers what recalibration recovers. Each is chosen
over a grid of 197 points spanning 0.01 to 0.99.

**Coverage.** Both analyses require the per-window probability files, which were
retained for three of the five architectures per arm: CNN, CNN-BiLSTM and EEGNet on
Arm A, and DeepConvNet, EEGNet and ShallowConvNet on Arms B and C. Threshold
selection was additionally **not run on Arm B**. Only the Brier partition of
Section 7 covers all five architectures on all three arms, because it needs only the
pooled predictions.

Because validation predictions were not retained during training, these corrections
are fitted across folds rather than inside them. This is a weaker arrangement than a
true inner-validation fit and is recorded as a limitation (Section 8.10, Limitation 3);
it does not leak test labels, which is the property that matters for validity.

## 6.7 Reproducibility

Setting a seed does not make a GPU run deterministic, and this study does not claim
that it does. Two repeated-execution checks were made, and they differ in strength.

**Check 1 — Arm B, three architectures, validation pairs verified.** Arm B was
executed twice, several hours apart, under the same preprocessing, the same five
seeds and validation-subject assignments confirmed identical on all 150 folds, so the
two runs differ only in GPU non-determinism. EEGNet, ShallowConvNet and DeepConvNet
were genuinely re-executed; CNN and CNN-BiLSTM were not, which is verifiable rather
than assumed: every one of their folds is bit-identical between the two files.

**Check 2 — Arm A, EEGNet only, validation pairs unverified.** An earlier Arm A
execution of EEGNet was retained. Against the current run it agrees to full
floating-point precision on balanced accuracy and F1 for 44 of the 50 folds and on
recall for 49 of 50; no mean over folds differs by more than 0.0008 (ROC-AUC 0.8840
against 0.8840, PR-AUC 0.4317 against 0.4314, balanced accuracy 0.7092 against
0.7084); and the largest single-fold ROC-AUC difference is 0.0032. **The earlier run
did not record its validation-subject assignments, so we cannot confirm that the two
runs drew the same pairs.** Its differences are therefore an upper bound on GPU
non-determinism and not a measurement of it, and attributing them to kernel selection
alone would overstate what the retained files support.

Arm C was not repeated. The consequences for how the reported ± should be read are
in Section 7.

All 750 folds are retained individually with their metrics, epoch count and
validation-subject pair.

---


## Notes for the next pass — not part of the paper

- **Subject demographics — closed 2 October 2026.** "Seven male, three female, aged
  20–50" is sourced: the deposit's README states that the file labelling carries
  volunteer number, gender and trial number, and its abstract gives the 20–50 age
  range for the cohort. Per-subject ages are not in the deposit, so no demographics
  column can be added to Supplementary Table S1.
- **Dataset citation.** DD-Database needs its formal citation and a licence /
  availability statement — BSPC expects a data-availability section.
- **Resolved.** The earlier note here said Section 4.4 described both arms as
  though fully evaluated, pending three architectures on Arm B. All five ran on all
  three arms; Section 4.4 now covers three arms, and Section 6
  must say plainly which results exist on which arm.
- **Reference implementations.** The EEGNet / ShallowConvNet / DeepConvNet source
  (the ARL EEGModels repository) needs its citation in Section 5.
- **Two things a reviewer will probably ask.** Why 20 s for the alert guard band
  and not 10 or 30; and whether the 10 s window length was tuned. Both were fixed
  a priori and never varied — say so explicitly rather than leaving it open.
- **Length.** Sections 3 and 4 together will run to roughly two and a half journal
  pages as drafted. If space is tight, Section 4.5 and Section 6.7 compress to one paragraph each,
  but they are also the two subsections that most distinguish this manuscript from
  a typical submission, so cut them last.
