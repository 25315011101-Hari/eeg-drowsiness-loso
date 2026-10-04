# 9 Conclusion — draft 5

What the study establishes, stated no more strongly than the measurements allow.

This study evaluated five convolutional and recurrent-convolutional architectures for
EEG driver-drowsiness detection under leave-one-subject-out cross-validation with five
seeds, on three constructions of the same ten recordings (750 folds), reporting
ranking quality and probability reliability as separate outcomes.

**It does not identify a universally superior architecture**, and shows instead that
discrimination, threshold-dependent detection and probabilistic prediction quality can
lead to different architecture-level conclusions under one subject-independent
protocol on one dataset.

**Three findings replicate on all three constructions.** The compact
depthwise-separable architecture ranks best, at subject-averaged ROC-AUC 0.884, 0.900
and 0.883, significant in eleven of twelve paired comparisons, while no other pair of
architectures separates significantly anywhere. Exactly three of the five exceed the
class-prior Brier reference every time and exactly two fall below it, with the same
membership, so ranking quality and probability reliability are separate properties,
and the unreliable set includes the best-ranking architecture. And one logistic
function per fold, fitted on the other nine subjects, takes the architectures whose
probabilities were retained from one of three below the reference to three of three on
each construction, leaving the subject-averaged ROC-AUC and PR-AUC unchanged at the
reported precision: the reliability gap is a matter of the scale of the scores rather
than of their ordering.

**One hypothesis was tested and withdrawn.** The inverse relationship between
parameter count and ranking quality decays ρ = −0.900 → −0.500 → −0.100 across the
three constructions and is significant on none, so only the claim about the single
compact architecture survives.

**Both design questions were answered, and asymmetrically.** Balancing moves the
intermediate architectures — DeepConvNet and CNN-BiLSTM gain 0.0217 and 0.0259 in
ROC-AUC, both p = 0.0488, while EEGNet moves by 0.0009 — whereas trimming moves
nothing, **no test of the twenty reaching significance** (smallest p = 0.1309) despite
discarding roughly 7 % of the windows. With ten subjects that is weak evidence of
absence rather than evidence of none, and the fourth cell was not run, so the trimming
result is conditional on proportional balancing rather than a main effect.

**Three methodological findings bear on how results of this kind should be reported.**
At 7 % to 8 % prevalence accuracy orders these architectures *against* pooled recall on
all three constructions, and the study's highest accuracy, 93.6 % against an
always-alert baseline of 92.73 %, belongs to an architecture detecting 335 of 673
drowsy windows, which also has the best Brier score of the five there, so which
architecture looks best depends on which measure is asked for. Between-subject
variation in PR-AUC exceeds seed variation by one to two orders of magnitude, so an
interval computed over seeds understates the uncertainty that matters. And repeated
execution under identical settings reproduced one architecture to four decimal places
while moving individual folds of two others by more than 0.20 in ROC-AUC, so
single-run comparisons carry an unreported source of variation.

These findings indicate that model selection should consider ranking quality,
probability reliability, threshold behaviour and subject-level uncertainty jointly
rather than any one alone. The paper reports that evidence; it does not recommend an
architecture for deployment, which would require more than ten subjects, one dataset
and one simulator protocol.

> **हिंदी।** तीन बातें तीनों arms पर दोहराई गईं: compact model सबसे अच्छा; वही तीन models
> reference से ऊपर और वही दो नीचे; और एक logistic fit सबको नीचे ले आता है बिना ranking बदले।
> एक परिकल्पना — "parameters कम तो बेहतर" — जाँच कर हटा दी गई। और एक design सवाल का जवाब मिला:
> बीच के models का क्रम balancing बदलता है, trimming नहीं।

---

