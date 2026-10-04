# 3 Research Gap — draft 1 (19 September 2026)

Section 2 surveys what the field has done. This section states, in one place, what
it has not: four gaps that together determine what this study measures and how it
reports it. Every claim here is either a statement about the reviewed literature or
a forward reference to a measurement made later in the paper; none is new evidence.

> **हिंदी।** यह section चार कमियाँ एक जगह रखता है। पहले ये बातें Introduction और Related
> Work दोनों में बिखरी थीं — अब एक ही बार, यहीं।

---

## 3.1 Subject-independent evaluation is not consistently reported

A drowsiness detector is deployed on a driver it has never seen, so evaluation should
hold out whole subjects; a protocol mixing one subject's windows across training and
test measures something closer to within-subject memorisation. The strongest
cross-subject work adopts leave-one-subject-out explicitly (Section 2.3), but how
common the practice is cannot be established from the surveys: [S2] names the
obstacle — "incomplete reporting in several studies, including missing details on
sample characteristics, annotation methods, and validation schemes" — and [S1] does
not address the question at all. **That silence is the gap.** It is not a claim that
the field evaluates badly, but that from the published record a reader often cannot
tell.

## 3.2 Accuracy is reported without the two quantities that make it readable

Drowsiness events are rare — the positive class is 6.94 %, 7.27 % or 8.32 % of windows
in the three constructions used here — so accuracy is dominated by the majority class
and the precision–recall curve is the more informative summary [E1].

That much is well understood. The gap is that **the class ratio and the majority-class
baseline are usually absent from the report**, which leaves the headline number
unreadable: 94.48 % is excellent on a balanced problem and worse than predicting
"alert" forever at 6 % prevalence. The most recent comparative review names the
problem and recommends the field "move beyond accuracy-centered comparisons", yet its
own comparison stops at accuracy, precision, recall, specificity and F1 [S3].

This study measures something stronger than weakness: Section 7.3 reports that
accuracy runs **against** recall rather than merely failing to track it, the two most
accurate architectures being exactly the two with the lowest recall on all three
constructions, with the direction consistent on all three and its strength not.

## 3.3 Probability calibration is not treated as an evaluation dimension

Outside EEG, discrimination and calibration are long established as separate
properties of a classifier (Section 2.4). None of the three recent reviews examined
here treats predicted-probability calibration as a distinct evaluation dimension, and
none mentions it at all. (Two review this field directly; the third [S2] reviews
behavioural rather than physiological indicators and is cited for what the wider
literature reports.)

That is deliberately a claim about the reviews rather than about the field: one
review's silence is evidence about the review, not proof that no study has ever
calibrated an EEG drowsiness model. What follows is narrower and sufficient: a reader of these reviews would not learn that a model can rank well and still state
probabilities worse than a constant, which Section 7.5 reports three of the five
architectures here doing.

## 3.4 Uncertainty is computed over the wrong source of variation

With ten subjects an interval computed over random seeds describes almost nothing of
the variation that matters, and Varoquaux [E2] shows how badly small samples inflate
the error bars cross-validation produces. Here subject-level variation in PR-AUC
exceeded seed-level variation by roughly an order of magnitude on all three
constructions (Section 7.4), so an interval representing seeds understates what a new
driver would encounter.

## 3.5 What this study does about them

The four gaps set the design: evaluation is leave-one-subject-out on all folds
(Section 6.1); every accuracy is reported beside its class ratio and always-alert
baseline (Section 7.3); probability reliability is measured against the Brier score of
a constant predictor emitting the class prior, with recalibration fitted out of
subject (Section 7.5 and Section 7.6); and intervals are taken over subjects, not seeds
(Section 7.4).

One further choice follows from the gaps jointly. Because a finding that depends on
how the window set was built is not a finding about drowsiness detection, the study
runs on **three constructions of the same ten recordings**, claiming a result for all
three only where it replicates on all three and otherwise naming the constructions it
covers (Section 4.4).
