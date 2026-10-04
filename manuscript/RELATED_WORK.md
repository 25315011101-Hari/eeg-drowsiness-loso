# 2. Related Work — draft 1 (16 September 2026)

<!-- not-for-submission:start -->
Written against Results draft 4 and the verified reference list in
`REFERENCES.md`. Every citation here was checked against a publisher or
repository record; none was written from memory.
<!-- not-for-submission:end -->

> **हिंदी।** यह section सिर्फ़ उन्हीं papers को cite करता है जिन्हें 16 सितम्बर को publisher
> के record पर जाकर verify किया गया। कोई भी citation याददाश्त से नहीं लिखी गई।

---

## 2.1 What the field detects, and how it reports it

EEG-based driver-drowsiness detection is active and well surveyed. The most recent
EEG-specific survey screened 267 records and analysed 87 papers [S1]; a parallel
systematic review covering 69 studies to August 2025 reports a median accuracy of
94.48 % for deep-learning methods and 91.80 % for classical machine learning, with
individual figures spanning 67 % to 100 % [S2]; and a 2026 comparative review gives
64 % to 98.7 % for physiological systems, with the explicit caution that such ranges
"should not be interpreted as directly comparable benchmark values" [S3].

Those numbers are this paper's starting point, and not because they are too high.
They are difficult to interpret without two quantities that are usually absent: **the
class ratio of the evaluation set, and the accuracy of the trivial always-majority
predictor on it.** An accuracy of 94.48 % is excellent on a balanced problem and worse
than predicting "alert" forever at 6 % prevalence. The reviews cannot supply the
missing context because the reviewed papers largely do not report it; the broader
review rates 27 of its 69 studies at high risk of bias, citing "dataset construction,
labeling procedures, insufficient reporting of ground-truth generation, and inadequate
validation strategies" [S2].

The 2026 review names the problem without pursuing its consequence — accuracy "can be
misleading in imbalanced settings where drowsy samples are relatively rare", with a
call to "move beyond accuracy-centered comparisons" [S3] — while its own vocabulary
stops at accuracy, precision, recall, specificity and F1, all threshold metrics
computed after a decision has been taken. This study extends that concern with a
measurement: on all three constructions the two most accurate architectures are
exactly the two with the lowest recall (Section 7).

None of the three reviews treats probability calibration as an evaluation dimension,
and none mentions it at all: *Brier*, *probability calibration*, *Platt*, *isotonic*,
*expected calibration error* and *reliability diagram* occur in none of the three full
texts. That is deliberately a claim about the reviews: their silence is evidence
about them, not proof that no study has ever calibrated an EEG drowsiness model. What
can be said without a negative search result is that the apparatus is standard
elsewhere (Section 2.4), that **these three reviews do not treat it as a distinct
evaluation dimension**, and that applied here it does not behave like a formality.
That is the gap this paper is built around.

## 2.2 Architectures

The architectures evaluated here are not new, and that is deliberate; two lines of
work supply all five.

**Compact, EEG-specific convolutions.** EEGNet [A1] factorises the problem the way the
signal is structured (a temporal filter bank across channels, a depthwise spatial convolution learning per-channel combinations, then a separable convolution), reaching
its published performance across four BCI paradigms with, in the configuration used
here, 1,809 trainable parameters. **ShallowConvNet** and **DeepConvNet** [A2] come
from the other direction: the shallow network mimics a filter-bank common spatial
pattern pipeline in ~14 k parameters, the deep network stacks five convolution–pooling
stages to ~150 k. These three span two orders of magnitude of capacity while remaining
architectures designed for EEG rather than borrowed from vision.

The other two are the generic baselines most often built for this task: a three-block
one-dimensional CNN, and the same CNN with its global temporal pooling replaced by two
bidirectional LSTM layers. They share the convolutional trunk, so the feature
extractor is fixed and the substitution changes only how the time axis is reduced.
**It also adds 135,936 parameters (3.04 times the CNN's own total, taking the
CNN-BiLSTM to 4.04 times it), so this is not a capacity-neutral ablation**, and
recurrence cannot be separated here from the added parameters; Section 7 reports the
comparison with that limit stated. The survey literature records CNN and CNN-LSTM
hybrids as the dominant deep architectures in this field [S2], so the pair is also the
comparison a reader is most likely to want.

**No hyperparameters were searched, and the architectures were fixed before any result
was seen.** EEGNet, ShallowConvNet and DeepConvNet were taken from their authors'
reference implementations without architectural change beyond the output-layer
adaptation of Section 5; the CNN and CNN-BiLSTM have no published configuration to
adopt and were fixed in advance rather than tuned. This bounds the claim — the
comparison is between these configurations, not between architectures at their best,
and for two of the five the configuration is ours — but it buys the fact that no
search was fitted to ten subjects.

## 2.3 The closest cross-subject work

A drowsiness detector is deployed on a driver it has never seen, so evaluation should
hold out whole subjects; a protocol mixing one subject's windows across training and
test measures something closer to within-subject memorisation.

The strongest cross-subject work adopts this explicitly: Cui et al. [C1] evaluate a
compact separable-convolution network on 11 subjects under leave-one-subject-out
cross-validation, reporting 78.35 % mean accuracy against conventional baselines at
53.40–72.68 % and earlier deep methods at 71.75–75.19 %. It is the closest
methodological neighbour to this study: the same leave-one-subject-out protocol, a
separable-convolution architecture of the same family as EEGNet, and a comparable
subject count. **It is a different dataset and a different recording protocol**, so
its figures are not a benchmark competed against; they are a reminder of what honest
cross-subject performance looks like, well below the 94 % medians of the aggregate
reviews.

Their evaluation set is also imbalanced, and the comparison is instructive: 2,952
samples of which 1,221 are drowsy, a prevalence of 41.4 % against 6.94 % to 8.32 %
here. **Their reported accuracy therefore clears its own always-alert baseline of
58.6 % by roughly twenty points, where ours does not.** The same number that is
uninterpretable on this dataset is informative on theirs, and the difference is the
class ratio, not the architecture. Their per-subject distributions vary widely, so a
pooled prevalence understates how uneven the comparison is subject by subject; the
point stands at the aggregate level, which is where they report.

Neither survey establishes how common subject-independent evaluation actually is. [S2]
gives the reason — "incomplete reporting in several studies, including missing details
on sample characteristics, annotation methods, and validation schemes restricts the
reliability of cross-study synthesis" — and [S1] makes no such statement, so this is
one review's finding and not two. That is itself the finding.

## 2.4 Calibration: a literature this field has not drawn on

Outside EEG, the separation of *discrimination* from *calibration* is well
established. Guo et al. [P1] showed that modern neural networks are systematically
over-confident, the effect growing as architectures grew; Van Calster et al. [P2],
writing for clinical prediction, put the consequence plainly: a model can rank cases
correctly while systematically mis-stating absolute probabilities, and one with
slightly lower AUC but better calibration can be the more useful in practice.

The remedies are long-established and cheap: Platt scaling fits a two-parameter
logistic function to the score [P5], isotonic regression a non-parametric
non-decreasing map [P4]. **The two differ in their effect on ranking, because isotonic
regression can introduce ties through its flat regions whereas a logistic map is
strictly increasing when its fitted slope is positive.**

That condition was measured rather than assumed, and the measurement is reported in
Section 7.6: on the construction whose per-window scores were retained all 150 fitted
Platt slopes are positive, the subject-averaged ROC-AUC and PR-AUC are unchanged at
the reported precision, and isotonic regression behaves as its weaker monotonicity
predicts, lowering both on most of the same folds. Reliability is measured by the
Brier score [P6] and by the binned expected calibration error [P3].

**This paper's contribution is to bring that apparatus to EEG drowsiness detection and
to find that it is not a formality here.** Three of the five architectures (including
the one with the highest subject-averaged ROC-AUC on every construction) produce
probabilities whose Brier score is *worse than a constant predictor that ignores the
EEG entirely and emits the class prior*, and the partition of the five about that
reference is identical on all three constructions. The Brier score is computed for all
five on all three; the recalibration analysis covers the three architectures per
construction whose per-window probabilities were retained, and the two coverages are
not to be read as one.

Two details matter for comparison with other work. First, every calibrator is
fitted **out of subject**: one per leave-one-subject-out fold, on the other nine
subjects only. Fitting a single calibrator on all predictions would leak the
test subject into its own correction and would report an optimistic number.
Second, the class-prior Brier reference π(1 − π) is not a convention chosen for
convenience; it is the score the constant predictor actually attains, so
"above the reference" has an operational meaning rather than a stylistic one.

## 2.5 The dataset, and what makes three constructions necessary

This study uses the Drivers Drowsiness Database (DD-Database) [D1]: ten healthy
volunteers aged 20–50, two two-hour trials each in a driving simulator, with four EEG,
two EOG and one ECG channel in EDF format and a separate annotation file per recording
marking drowsiness events. Its CC0 1.0 public-domain dedication is what makes a fully
reproducible release of the window-construction pipeline possible.

**The deposit stands alone**: no accompanying journal article or data descriptor. Its
own README documents the event-button procedure and describes the annotation marks as
corresponding to the volunteer's drowsiness feeling; what it does not establish is that
these marks represent independently verified physiological onset times. The most recent
review catalogues it as a benchmark and restates the landing page's facts without
adding anything about where a mark falls within an episode [S3], which is the point:
that has not been established anywhere. The depositing group has
earlier published work on EEG drowsiness detection [R1], but on a different database
with a different montage, sampling rate and annotation criterion, so it documents
neither these recordings nor their labels. We cite the dataset as a dataset and record
in Section 8.10 that the annotation protocol is undocumented, which bounds the
external reading of every absolute figure while leaving comparisons between
architectures and between constructions unaffected, all being scored against the same
marks.

Turning continuous recordings with event marks into a labelled window set requires
choices the raw data does not make: whether to trim recordings to a common length, how
to align windows to events, how to handle each subject's class ratio. Those choices
change the prevalence, and prevalence changes every threshold-dependent metric.

This is not only our own reading of the deposit. The 2026 review reaches the same
conclusion independently: the protocol "is specifically designed to induce drowsiness
under controlled night-driving-like conditions, which is useful for physiological
modeling but also introduces protocol-specific bias", and "the way event annotations
are segmented or converted into window-level learning targets may vary across studies
and affect the reported metrics" [S3].

That is the problem this study's design addresses. Rather than present one
construction's results as *the* results, it builds **three constructions of the same
ten recordings** and reports which findings survive all three. They are three cells of
a two-by-two design of trimming against balancing, **the fourth not evaluated**; two
contrasts remain, each varying one factor (A–C isolates the balancing rule, B–C
examines trimming with balancing held at proportional), and because the fourth cell is
missing the trimming contrast is conditional on that rule rather than a main effect.

The purpose is not to claim external replication, the recordings being the same
recordings, but to test whether findings persist under three plausible constructions
of them. A finding surviving all three is evidence that it is not specific to one
evaluated construction choice, without establishing generalisation beyond this
dataset; a single-construction analysis cannot test that sensitivity at all.

---

## Notes for the next pass — not part of the paper

- Reference tags `[A1]`, `[S2]` and so on are placeholders for the journal's
  numbering; `REFERENCES.md` holds the full verified entries.
- `[P5]` and `[P6]` are now verified against catalogue records, and `[P5]` changed:
  the printed chapter is *Probabilities for SV Machines*, under a different title
  and year from the one this draft carried. `REFERENCES.md` gives both forms.
  Body text cites the work only as `[P5]`, so no sentence changes.
- Length is roughly twelve hundred words, which suits BSPC. If the section must
  shrink, Section 2.2 compresses best; Section 2.4 is load-bearing and should not.
- Every number quoted from our own results is in `MASTER_NUMBERS.csv`; the
  numbers quoted from other papers are in `REFERENCES.md` with their source URL.
- Decide with the guide whether to name individual high-accuracy papers. The
  recommendation in `REFERENCES.md` is not to: the aggregate framing via [S1]
  and [S2] makes the same point without inviting a defence of any one study.
