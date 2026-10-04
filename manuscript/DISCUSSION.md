# Discussion and Conclusion — draft 5 (aligned to Results draft 4, three arms)

All values are subject-averaged unless explicitly identified as pooled.

<!-- not-for-submission:start -->
Every number below was regenerated on 16 September 2026 by `registry.py` from the
raw result files and checked against `MASTER_NUMBERS.csv` (1977 rows, regenerated
the same day). An automated scan of this document reports **zero numbers that do not
appear in that registry**.

> **हिंदी।** हर numerical value उसी दिन registry से दोबारा निकाली गई है और
> `MASTER_NUMBERS.csv` में verify की गई है। यह draft अब तीनों arms पर आधारित है।

**Numbering.** These are Sections 8 and 9 of the nine-section structure
(1 Introduction · 2 Related Work · 3 Research Gap · 4 Methodology ·
5 Architectures · 6 Experimental Setup · 7 Results · 8 Discussion ·
9 Conclusion). Limitations is Section 8.10, a subsection of the Discussion rather
than a section of its own: it constrains the claims made in Section 8.1 to Section 8.9 and reads
better beside them than after them.
<!-- not-for-submission:end -->

---

The results section reports what was measured. This section states what those
measurements do and do not license, taking the findings in the order in which a
reader is likely to question them.

> **हिंदी।** Results में सिर्फ़ नाप बताया गया है। इस section में यह कहा गया है कि उस नाप से
> क्या दावा किया जा सकता है और क्या नहीं — उसी क्रम में जिस क्रम में reviewer सवाल उठाएगा।

## 8.1 One architecture separates; the rest of the ordering is not a measurement

EEGNet (1,809 parameters) attains the highest subject-averaged ROC-AUC and PR-AUC on
all three constructions and exceeds every other architecture in eleven of the twelve
paired comparisons, the exception being the CNN on Arm B (p = 0.0645, with 8 of 10
subjects still favouring it); five of the twelve sit on the attainable floor
(Section 7.1).

**Nothing else in the ROC-AUC ordering survives.** The six pairs not involving EEGNet
reach significance on no arm (smallest p 0.1934, 0.0840 and 0.4316), so the apparent
second to fifth places are not measurements and this paper claims nothing about them.
Arm C makes the point plainly: fourth and fifth are separated by 0.0007 in ROC-AUC at
p = 0.6250. This is a claim about ranking and nothing more. Those same six pairs
separate readily on balanced accuracy, four to five of six per arm, Section 8.2's
ablation among them: the architectures are distinguishable, but not by how well they
order windows.

**The capacity hypothesis is withdrawn.** The natural reading — that a smaller model
wins because the training set is small — was tested as a rank correlation between
parameter count and ROC-AUC, giving ρ = −0.900 (p = 0.0833), −0.500 (0.4500) and
−0.100 (0.9500), significant on none and decaying monotonically to nothing. An earlier
analysis based on two constructions called it "not replicated"; with the third
construction the honest description is stronger. **The Arm A correlation was an artefact of the two extremes, and one of
them has since moved**: DeepConvNet is lowest on Arms A and B but fourth of five on
Arm C. What remains is a statement about one architecture rather than about a
capacity axis, and one made on two ranking metrics only, since Section 8.5 places
this same architecture on the wrong side of the class-prior Brier reference.

Two mechanisms are consistent with EEGNet's advantage and cannot be separated here.
The depthwise-separable factorisation applies one temporal filter bank across channels
and then learns per-channel spatial combinations, which suits a four-channel montage
where the informative pattern is a rhythm shared across electrodes rather than a
channel-specific waveform. Independently, EEGNet is the only one of the three
architectures tested for it that reproduces across identical executions
(Section 8.8), so part of the gap may be that the deeper stacks are not reaching a
stable solution rather than reaching a worse one.

> **हिंदी।** तीनों arms पर EEGNet सबसे ऊपर है — बारह में से ग्यारह comparisons significant।
> लेकिन बाक़ी चार models आपस में कहीं भी significantly अलग नहीं हैं, इसलिए दूसरे–तीसरे स्थान का
> कोई दावा नहीं किया गया। "parameters कम इसलिए बेहतर" वाला नियम तीनों arms पर घटते-घटते ख़त्म हो
> जाता है (ρ −0.900 → −0.500 → −0.100), इसलिए उसे पूरी तरह हटा दिया गया है।

## 8.2 The recurrent block changes detection, not ranking

The CNN and the CNN-BiLSTM share their convolutional trunk exactly and differ only in
how the time axis is reduced, making this a far tighter comparison than any other in
the study, but it is **not** capacity-controlled: the recurrent block adds 135,936
parameters, 3.04 times the CNN's own total and taking the CNN-BiLSTM to 4.04 times
it. Whether the effect comes from recurrence or from the capacity arriving with it
cannot be separated here, and we do not claim it can.

The result is the same on all three constructions (Section 7.2): adding the recurrent
block does not significantly change ROC-AUC on any arm, the point estimate falling by
0.022 and 0.007 on two of the three, while significantly improving balanced accuracy
and F1 on every arm.

This is a coherent pattern rather than a contradiction. ROC-AUC is threshold-free and
measures only the ordering of windows, while balanced accuracy and F1 are evaluated at
the fixed 0.5 threshold and depend on where the score distribution sits relative to
it. The recurrent block therefore does not order windows better; it moves drowsy
windows above the operating point actually used. Degenerate folds, in which no window
is predicted drowsy at 0.5 and F1 is identically zero, fall from 17 to 7 of 50 on
Arm A, 12 to 3 on Arm B and 20 to 7 on Arm C.

The PR-AUC gain replicates on the two trimmed constructions and not the untrimmed one
(p = 0.0059 and 0.0039 against 0.232), so the claim is made on balanced accuracy and
F1, with PR-AUC reported as construction-dependent. Stated that way it is also less
impressive than it first appears, because Section 8.6 shows the same movement of the
score distribution relative to the threshold can be obtained from any of these
architectures by recalibration, without adding 135,936 parameters.

> **हिंदी।** BiLSTM block ranking नहीं सुधारता (ROC-AUC तीनों arms पर वही), पर fixed threshold
> पर detection सुधारता है — degenerate folds 17→7 (A), 12→3 (B), 20→7 (C), और balanced accuracy
> व F1 तीनों arms पर significant। PR-AUC सिर्फ़ trimmed arms पर सुधरा।

## 8.3 Accuracy gives a misleading picture of minority-class detection here

Always predicting "alert" gives 91.7 % accuracy on Arm A, 93.1 % on Arm B and
92.73 % on Arm C. Accuracy and pooled recall are negatively rank-correlated on all
three constructions (ρ = −1.000, −0.900 and −0.600 across the five architectures),
and on all three the two most accurate architectures are exactly the two that detect
the fewest drowsy windows.

The two extremes of the three make the same point from opposite directions. On
**Arm B** no architecture reaches the baseline at all: the closest is the CNN at
93.00 % against 93.06 %, with subject-averaged recall 0.2318, while CNN-BiLSTM and
EEGNet at balanced accuracy 0.725 detect roughly twice as many events. On **Arm C**
DeepConvNet reaches the study's highest accuracy, 93.56 % against a baseline of
92.73 %, while detecting 335 of 673 drowsy windows where EEGNet detects 528, and while being beaten by EEGNet on ROC-AUC, PR-AUC, balanced accuracy, F1 and recall at
4.1 accuracy points lower.

The second case is the stronger argument, and worth stating explicitly because it is
the one a reviewer will treat as a counterexample. **Exceeding the always-alert
accuracy baseline does not by itself establish superior detection of drowsiness
events**, because accuracy does not distinguish how well the minority class is
detected. It is not, however, evidence that such a model is worse on everything: the
same architecture has the lowest pooled Brier score of the five on that construction.

The consequence is stronger than "accuracy is a poor summary". Under 7 % to 8 %
prevalence accuracy here *decreases* as recall rises, exactly reversed on Arm A,
nearly so on Arm B, approximately on Arm C (p = 0.3500), where the two least
sensitive architectures exchange places and EEGNet is third on accuracy while having
the highest recall of the five. A leaderboard ordered by accuracy would put the
architectures detecting fewest drowsy windows at the top on all three. That matters
for the literature as much as for this study: reported accuracies above 90 % are not
interpretable without the class ratio and the always-majority baseline beside them,
and the two are frequently absent. This work reports the baseline for each
construction explicitly, and reports PR-AUC against its chance level, the prevalence
itself (0.0832, 0.0694, 0.0727), rather than against 0.5.

> **हिंदी।** 93.1 % तो "हमेशा alert" कहने से ही मिल जाता है। Arm C पर एक model उस बाधा को पार
> करता है (93.6 %) — पर वही 673 में से 338 drowsy windows चूक जाता है और हर दूसरे metric पर
> हारता है। इसलिए accuracy यहाँ कमज़ोर नहीं, उलटी दिशा में ले जाने वाला metric है।

## 8.4 Of the two construction choices, balancing is the one that matters

An earlier analysis based on two constructions could not say which construction
choice — trimming to equal duration, or how the class ratio is handled — was
responsible for the differences between arms, because Arms A and B differ in both. **Arm C settles both**, completing three of the
four cells and so giving two controlled contrasts: A and C share their trimming and
differ only in balancing, B and C share their balancing rule and differ only in
trimming.

Removing the surplus drowsy windows significantly raises the ranking quality of the
two largest architectures (DeepConvNet 0.812 → 0.834 and CNN-BiLSTM 0.821 → 0.847 in
ROC-AUC, both p = 0.0488), while leaving EEGNet untouched (0.884 → 0.883, p = 0.4922).
That is the mechanism behind the reordering of the middle of the table in
Section 8.1. **Trimming, by contrast, does nothing measurable**: across the twenty
tests of the B-against-C contrast not one reaches significance, smallest p = 0.1309,
although trimming discards about 7 % of the data.

The asymmetry is the useful part (**seven of twenty for balancing, zero of twenty for trimming**), and it must not be read as evidence that trimming has no effect: with ten
subjects the test is underpowered and the fourth cell was not run, so this is no
*measurable* effect rather than no effect. What it does support is a statement about
where attention is better spent: a researcher building a window set from these
recordings has clear evidence that the class-ratio rule changes results and no
evidence either way about equalising durations.

Two further things follow. The instability of the intermediate ordering now has an
identified cause rather than being attributed to noise. And **the conclusion about
EEGNet is the one conclusion in this study demonstrably insensitive to the
construction choice that moves the others**: its ROC-AUC changes by 0.0009 between
the two constructions differing only in balancing, against 0.0217 and 0.0259 for the
two largest architectures.

The prevalence-sensitive metrics move the other way for the architectures that do not
gain — ShallowConvNet's PR-AUC falls 0.411 → 0.372 (p = 0.0039), the CNN's
0.338 → 0.295 (p = 0.0020) — which is expected at Arm C's lower prevalence rather
than contradictory. Reporting both directions is the point: one construction change
helps one group on one family of metrics and penalises another group on another.

> **हिंदी।** तीन arms से दो नियंत्रित तुलनाएँ मिलती हैं। **A बनाम C** में सिर्फ़ balancing अलग
> है — बीस में से सात tests significant। **B बनाम C** में सिर्फ़ trimming अलग है — बीस में से
> **शून्य** significant, सबसे छोटा p = 0.1309। यानी **balancing मायने रखती है, trimming नहीं**,
> हालाँकि trimming लगभग 7 % data हटा देती है। EEGNet दोनों में अडिग रहता है।

## 8.5 Ranking quality and probability reliability are separate properties

The clearest replication in the study is the Brier partition, which now holds three
times (**Figure 5**). Against the class-prior reference π(1 − π) — 0.0762, 0.0645, 0.0674 — the same three architectures exceed it on all three constructions (EEGNet,
ShallowConvNet, CNN-BiLSTM) and the same two fall below (CNN, DeepConvNet), despite
three different prevalences, two different window counts and three different
reference values.

Exceeding the reference means the probabilities, scored as probabilities, are worse
than a constant predictor that ignores the input and emits the prior, and the set
that does so includes the best-ranking architecture on every arm. DeepConvNet, which
never exceeds a reference, has the lowest raw calibration error of the three
architectures measured on Arm B (0.0679) and on Arm C (0.0460).

The margins are not uniformly wide and the narrow ones are stated rather than hidden:
the smallest is CNN-BiLSTM on Arm A at +0.0019, and DeepConvNet on Arm B sits only
0.0042 below its own, both comfortably on the same side on the other two
constructions. **What replicates is the side of the reference each architecture falls
on, three times out of three; the size of the margin is not claimed to be stable.**

It is tempting to read the partition as an inverse coupling between ranking and
reliability, but none is claimed: the rank correlation between ROC-AUC and raw Brier
reaches significance on no arm and ranges from ρ = −0.100 to +0.800 with the choice
of averaging and the construction, so it is not a measurement. What is claimed is
only the separation — **the architectures with the strongest ranking performance were
not those with the most reliable raw probabilities** — which rests on which side of
the reference each falls, a sign rather than a rank, and does not depend on the
estimator.

The practical reading is that architecture selection and probability calibration are
two decisions, not one. A monitor that raises an alarm at a fixed confidence
threshold, or feeds a downstream risk estimate, consumes the probability rather than
the ranking, so a model chosen on ROC-AUC alone can be the wrong choice for that
consumer even when it is the right choice on ordering.

> **हिंदी।** तीनों arms पर वही तीन models reference से ऊपर हैं और वही दो नीचे — prevalence और
> reference अलग होने के बावजूद। यानी ranking अच्छी होना और probability भरोसेमंद होना, दो अलग गुण
> हैं। जहाँ अंतर कम है (Arm A पर CNN-BiLSTM, +0.0019) वह भी साफ़ लिखा गया है।

## 8.6 Out-of-subject recalibration closes the gap; threshold selection helps in one case only

**Figure 6** shows the repair: every measured architecture that began above its
construction's reference crosses below it after recalibration, on all three
constructions.

Platt scaling was applied fold by fold: **for each leave-one-subject-out fold a
separate logistic calibrator was fitted on the pooled predictions for the other nine
subjects and applied to the held-out subject**, fifty per architecture per arm, none
ever seeing the subject it scored. It covers the architectures whose per-window
probabilities were retained: CNN, CNN-BiLSTM and EEGNet on Arm A, DeepConvNet, EEGNet
and ShallowConvNet on Arms B and C, between them all five.

Scored on subject-averaged Brier, the count is the same on each construction: **two
of the three architectures are above the class-prior reference before recalibration
and none is above it after.** The architectures with the worst raw reliability
improve most: on Arm A EEGNet's calibration error falls 0.1950 → 0.0625 and
CNN-BiLSTM's 0.0912 → 0.0561; on Arm B ShallowConvNet's 0.2049 → 0.0605 and EEGNet's
0.1717 → 0.0547; on Arm C ShallowConvNet's 0.2001 → 0.0724 and EEGNet's
0.1918 → 0.0580. On the ten subject-level differences **EEGNet's calibration error
improves on all ten subjects on all three arms, p = 0.0020 each**, thirty of thirty,
at the smallest value ten paired observations can attain. DeepConvNet improves on
neither arm where it was measured (p = 0.770 and p = 0.625), which is consistent
rather than anomalous: it was the best-calibrated architecture before recalibration
on both, so there was little to correct, and on Arm C its calibration error is
nominally slightly worse afterwards, 0.0460 → 0.0502, the expected behaviour of
fitting a two-parameter correction to a distribution that does not need one.

The interpretive weight rests on monotonicity, so monotonicity was measured rather
than assumed. A logistic function of the logit is strictly increasing **when its
fitted slope is positive**, and a negative slope — possible on a fold where scores
anti-correlate with labels — would reverse the ranking instead of preserving it. On
Arm A, the construction whose per-window scores were retained, **all 150 fitted
slopes are positive**, 0.3243 to 1.3312, and Platt moves ROC-AUC by at most 4 × 10⁻⁵
and PR-AUC by at most 0.0034. Neither is exactly zero, for an identifiable reason
rather than numerical noise: the ε-clip before the logit maps every score below it to
one value, creating ties on 10 of the 150 folds and as many as 95 on one. Both bounds
sit below the precision at which this paper reports either metric, so the claim is
"unchanged at the reported precision", not "algebraically invariant". That one such
map per fold, fitted without seeing the test subject, moves every measured
architecture below the reference on every construction is what establishes that the
ordering information was already present and only its mapping onto the probability
scale was wrong: **the reliability gap is a matter of scale, not of ordering.**
Isotonic regression reaches comparable values but is not uniformly better, as one
expects of a more flexible estimator at these fold sizes.

**Threshold selection is the alternative route to the same goal, and an earlier
analysis based on two constructions reported that it never works. Arm C requires that
claim to be narrowed.** Selecting the
F1-optimal or balanced-accuracy-optimal threshold on the nine training subjects and
applying it to the tenth was evaluated on the three architectures with retained
probabilities on Arms A and C: twenty-four tests, of which seven reach significance:
four losses and three gains, all three gains belonging to DeepConvNet on Arm C
(balanced accuracy 0.628 → 0.661 and F1 0.300 → 0.342 under the F1-optimal rule,
balanced accuracy 0.628 → 0.694 under the balanced-accuracy rule). The four losses are
the same failure each time: the F1-optimal rule lowering balanced accuracy, for
CNN-BiLSTM and EEGNet on Arm A and EEGNet and ShallowConvNet on Arm C.

The selected thresholds explain the split. **Threshold selection transfers between
subjects when a model's scores are stably offset in one direction, and not
otherwise.** DeepConvNet on Arm C has an F1-optimal threshold of 0.3171 ± 0.0521 (far
below 0.5, its spread a sixth of its own value), so one number learned on nine
subjects is close to correct on the tenth. EEGNet and ShallowConvNet on the same arm
sit far *above* 0.5, at 0.7210 ± 0.0538 and 0.8257 ± 0.0581, and lose balanced
accuracy when the F1-optimal rule trades recall for precision in architectures already
over-predicting the minority class; the CNN on Arm A, at 0.4606 ± 0.1626, has a spread
a third of its own value and nothing transfers at all.

A symmetry is worth stating, the most informative single observation in this pair of
analyses: **the architecture that recalibration helped least is the one that threshold
selection helped most.** DeepConvNet is the only architecture whose raw calibration
was already below the reference, the only one Platt scaling did not significantly
improve, and the only one that gained from threshold selection. The two operations
address the same defect from opposite ends — recalibration reshapes the score
distribution so a fixed threshold is correct, threshold selection moves the threshold
to where the unreshaped distribution has put it — so scores that are well-shaped but
shifted are helped by the second and not the first, and mis-shaped scores by the first
and not the second.

The recommendation therefore stands for a stated reason rather than as a blanket
result. Recalibration applies more widely — six of six architectures whose raw
calibration was above the reference improved significantly on both Brier score and
calibration error, against one of six that threshold selection helped — the Platt
route leaves the subject-averaged ranking metrics unchanged at the reported precision,
and it preserves a fixed, interpretable operating point. **Recalibrate out of subject
and keep a fixed threshold; select a threshold only where the score distribution is
demonstrably offset and tight, and verify that on held-out subjects rather than
assuming it.**

> **हिंदी।** हर LOSO fold के लिए अलग logistic calibrator बनाया गया — test subject को छोड़कर
> बाक़ी नौ subjects की predictions पर — और फिर unseen subject पर लगाया गया। **तीनों arms पर
> पहले तीन में से दो model reference से ख़राब थे, calibration के बाद तीनों reference से बेहतर हो
> गए।** ROC-AUC और PR-AUC जिस precision पर रिपोर्ट हुए हैं उस पर नहीं बदले — तीनों arms पर जितने
> fits जाँचे जा सके, सबका slope positive था। Threshold चुनने वाला
> रास्ता आम तौर पर काम नहीं करता — चौबीस में से चार significant नुक़सान — पर Arm C के DeepConvNet
> पर तीन significant फ़ायदे मिले, क्योंकि उसका threshold 0.3171 ± 0.0521 पर स्थिर था।

## 8.7 Subject-level variation, not seed variation, is what an interval must represent

For every architecture on every construction the standard deviation of subject-level
PR-AUC across the ten subjects exceeds that across the five seed-level means by a
wide margin — 12 to 48 times on Arm A (EEGNet 0.2692 against 0.0058, CNN 0.2399
against 0.0050, CNN-BiLSTM 0.2440 against 0.0207), 6 to 18 on Arm B, 10 to 36 on
Arm C — and
subject-level PR-AUC ranges from 0.027 to 0.810, 0.079 to 0.825 and 0.022 to 0.818,
the worst subject being S9 on the trimmed constructions and S8 on the untrimmed one,
the best S7 on all three.

The spread is not unstructured: a subject's PR-AUC tracks how many drowsy windows it
contributes. Because the chance level of PR-AUC *is* the prevalence the correlation
could be an artefact, so each subject's prevalence was subtracted, and it survives at
ρ ≥ +0.79 with p ≤ 0.0061 on fourteen of the fifteen model-by-construction
combinations. The lift above chance, not merely the chance level, rises with the event
count. The single exception is the CNN on Arm B (ρ = +0.442, p = 0.200), also the
architecture with the most degenerate folds there; the same architecture on Arm C
gives one of the two *highest* corrected correlations in the study (+0.9152,
p = 0.0002), so the exception belongs to one arm-by-architecture combination rather
than to the CNN.

The same relationship appears in the opposite sign from the other direction, and is
reported because a reviewer who computes it will find it. The ratio of PR-AUC to
prevalence (the multiple of chance rather than the margin over it) correlates
*negatively* with the event count, significantly on Arm B for four of five
architectures — CNN-BiLSTM ρ = −0.879 (p = 0.0008), EEGNet −0.806 (0.0049), CNN
−0.709 (0.0217), ShallowConvNet −0.673 (0.0330), DeepConvNet −0.479 (0.162, not
significant) — and for none on Arms A and C, where all five are still negative. There is no contradiction: absolute PR-AUC rises
with event count while the multiple of chance falls, the ordinary behaviour of a
ratio whose denominator grows faster than its numerator. Citing only the favourable
framing would be selective.

Two consequences follow for how any result on this dataset should be reported. An
uncertainty interval computed over seeds understates the uncertainty that matters by
an order of magnitude, so the interval must be over subjects; and the PR-AUC of any
single fold is partly a statement about that subject's event count, which bounds how
far one subject's result can be interpreted.

> **हिंदी।** Subjects के बीच का फ़र्क़ seeds के बीच के फ़र्क़ से Arm A पर 12–48 गुना, Arm B पर
> 6–18 गुना और Arm C पर 10–36 गुना है। इसलिए error bar seeds पर नहीं, subjects पर बननी चाहिए।
> PR-AUC/prevalence वाला उल्टा result भी लिखा गया है, क्योंकि reviewer उसे ख़ुद निकाल लेगा।

## 8.8 Reproducibility is architecture-dependent, and this affects how the tables are read

Arm B was executed twice under identical preprocessing, seeds and validation-subject
assignments — all 150 pairs confirmed identical — differing only in GPU
non-determinism. EEGNet reproduced to four decimal places, largest single-fold
ROC-AUC difference 0.0002 and 27 of 50 folds identical to full precision;
ShallowConvNet and DeepConvNet did not, at 0.2219 and 0.2020 with 1 and 0 folds
identical. A second, weaker check on Arm A for EEGNet alone gives a largest
single-fold difference of 0.0032; it is weaker because that earlier run did not
record its validation-subject assignments, so the two runs cannot be confirmed to
have drawn the same pairs. It is worth reporting anyway: even the architecture this
paper calls reproducible is reproducible to a degree that depends on the run examined.

This changes how the tables are read. For ShallowConvNet and DeepConvNet the standard
deviation across five seeds **understates** the run-to-run uncertainty, since those
seeds share one execution, and the size of the understatement depends on which
average is taken. Over all fifty folds the two runs differ by at most 0.0057 in
ROC-AUC and 0.0213 in F1, which is reassuring; but an individual subject's mean (what every table in this paper averages) moves by up to 0.0407 in ROC-AUC and 0.1273
in F1, exceeding the reported seed-level standard deviation in all four cases.
Nothing a protocol can control distinguishes the two runs. It is an independent
reason not to read Section 8.1's intermediate ordering as meaningful, and it suggests
that any architecture-level comparison resting on a single training run carries an
unreported source of variation that can exceed the differences being claimed; how often such comparisons do rest on a single run is not something we can establish,
since neither review we cite reports whether the studies it surveys repeated their
training.

> **हिंदी।** Arm B दो बार चलाया गया। EEGNet चार दशमलव तक वही रहा; बाक़ी दो नहीं (सबसे बड़ा
> fold-अंतर 0.2219 और 0.2020)। पूरे पचास folds का औसत तो मुश्किल से बदलता है (≤ 0.0057
> ROC-AUC), पर **किसी एक subject का औसत 0.0407 तक हिल जाता है — जो reported ± (0.0328) से
> भी ज़्यादा है**। इसलिए उन दोनों का ± असली अनिश्चितता से कम दिखता है — यह बात छिपाई नहीं गई है।

## 8.9 What this means for a deployed system

Read together the findings point to a design that differs from the one the
literature's reporting conventions suggest. **These are conclusions within the
evaluated protocol (one dataset, ten subjects, four channels, a simulator), offered
as what this evidence supports, not as deployment guidance.** At that strength, four
things follow.

**On architecture.** EEGNet attains the highest subject-averaged ROC-AUC on all three
constructions, is the only architecture whose advantage survives the construction
choice that moves the others (Section 8.4), and the only one of three tested for
reproducibility that reproduces across executions. It is not best on every measure —
DeepConvNet is ahead of it on pooled Brier and pooled precision on Arm C — so this is
a statement about ranking quality.

**On probabilities.** EEGNet's raw scores should not be read as probabilities: their
Brier score is worse than a constant predictor's on all three constructions. Passed
through a logistic fit obtained from held-out subjects they fall below the class-prior
reference with no ranking metric changing at the reported precision (Section 8.6).
Any system reporting a probability from a model of this kind should therefore be
calibrated out of subject and checked against the class-prior reference first.

**On thresholds.** For EEGNet the F1-optimal rule transferred worse than leaving the
threshold alone on both constructions where it was tested (balanced accuracy
p = 0.0273 and p = 0.0098), while the balanced-accuracy rule moved it significantly on
neither. **This evidence covers Arms A and C only — threshold selection was not run on
Arm B** — so it supports validating a threshold rule separately rather than adopting
one on these two arms.

**On uncertainty.** A figure quoted for expected performance should carry an interval
over subjects: a subject-blind interval understates the variation in subject-level
PR-AUC by ×5.63 at the lowest and ×47.77 at the highest across the fifteen
architecture-by-arm combinations.

None of these four is visible in a table of accuracies, which is the practical
argument for the protocol used here.

> **हिंदी।** निचोड़ — और यह सिर्फ़ इसी protocol के भीतर: compact model का ranking सबसे अच्छा रहा,
> उसकी probabilities को out-of-subject logistic fit से ठीक करना ज़रूरी है, threshold का नियम अलग
> से जाँचना होगा (Arm B पर चला ही नहीं), और अनिश्चितता subjects पर बतानी चाहिए।

---

## 8.10 Limitations

These are constraints on what the study establishes, in descending order of how much
they bound the conclusions.

1. **Ten subjects.** This bounds every statistical statement here. The Wilcoxon
   signed-rank test on ten paired subject-level differences has an attainable minimum
   of 2/2¹⁰ = 1/512 = 0.00195, and several results sit exactly at that floor, as strong as
   this sample permits and no stronger. Correlations across the five architectures
   rest on five points, where the minimum is p ≈ 0.017, which is why the capacity
   correlation of Section 8.1 was withdrawn rather than defended. The protocol makes
   the most of the sample (every test subject-disjoint, every test set a whole unseen
   subject, every calibrator and threshold fitted without it), but that controls
   optimism rather than manufacturing power.

2. **Three constructions of the same recordings, not three datasets.** Arms A, B and C
   are built from the same ten recordings and are not independent. A finding holding
   on all three is evidence that it is not specific to one evaluated construction
   choice, not external replication, and no such claim is made. Both factors are
   isolated — A and C differ only in balancing, B and C only in trimming — but each by
   a single pair; the fourth cell, untrimmed with every drowsy window kept, was not run
   and would give a second instance of each contrast.

3. **Calibration coverage is three of five on each construction.** Per-window files
   were retained for CNN, CNN-BiLSTM and EEGNet on Arm A and DeepConvNet, EEGNet and
   ShallowConvNet on Arms B and C, so Section 8.6 rests on three architectures per
   construction. Between them all five are covered, but only EEGNet on all three, and
   the Arm B and Arm C sets are the same three, so the three-fold replication is not
   three independent sets of architectures. A *pooled* raw calibration error is
   additionally available on Arm B for the two architectures without subject-level
   files (CNN 0.0435, CNN-BiLSTM 0.0862), but pooled and subject-averaged ECE are not
   comparable and are not mixed here, so those two values extend no comparison. All
   five contribute to the Brier partition of Section 8.5, which is computed from
   pooled scores.

4. **Threshold selection was evaluated on two constructions, not three.** Section 8.6
   covers Arms A and C; it was not run on Arm B, so the narrowing of the draft-3 claim
   rests on one construction's evidence and the mechanism proposed for it (stability
   and direction of the selected threshold) is untested on a third.

5. **Four channels and one montage.** All results are for O1, O2, C3 and C4 at 128 Hz.
   The architectures' relative standing may depend on the channel count — the
   depthwise-separable factorisation's advantage is plausibly tied to a small channel
   set — and nothing here tests that.

6. **One dataset, one recording protocol.** A single sustained-attention driving
   protocol with one annotation scheme. Labels from a different behavioural criterion,
   or recorded in a vehicle rather than a simulator, are a different problem.

7. **The window–label relation is a design choice.** Drowsy windows end at an
   annotation event and are not aligned to a fixed grid, while alert windows come from
   a regular grid with a guard interval. This is stated in the methodology because it
   is a choice with consequences, not a neutral preprocessing step: a different
   alignment would change the prevalence and could change the results.

8. **The annotation protocol is documented by the depositors, but no peer-reviewed
   data descriptor describing it was found, and a mark's position within an episode is
   unknown.** The annotation protocol is
   documented in the dataset README: volunteers were instructed to press an event
   button when they felt drowsy, and the annotation files contain the resulting
   event-button time marks. DD-Database is nevertheless a standalone deposit with no
   accompanying article — the Dryad landing page lists no related work, the Zenodo
   mirror no related publications, and no data descriptor exists in the usual venues —
   so the procedure is documented by the depositors but is not described in a
   peer-reviewed data descriptor. The documentation does not establish whether each
   mark represents the onset of a drowsiness episode or another point within it. The
   most recent comparative review reaches a compatible conclusion from outside this
   study, cataloguing the deposit,
   restating its own facts and no others, and recording that "the way event annotations
   are segmented or converted into window-level learning targets may vary across
   studies and affect the reported metrics" [S3], an independent statement of both
   halves, and the reason this study reports three constructions instead of one. This
   bounds what every label means and therefore what every number means. It does **not**
   undermine the internal comparisons: all five architectures, three constructions and
   750 folds are scored against the same marks. It bounds the external reading: a figure such as "recall 0.785" is recall against this annotation and cannot be
   translated into a rate of detecting drowsiness as another study would define it. We
   treat the marks as the ground truth they are offered as, and state what the
   documentation does and does not establish.

9. **No hyperparameter search, and two of five configurations are ours.** Each
   architecture was used at a fixed configuration with a common training schedule;
   EEGNet, ShallowConvNet and DeepConvNet came from their authors' reference
   implementations unchanged apart from the output layer, while the CNN and CNN-BiLSTM
   have no published configuration and were specified in advance. This keeps the
   comparison controlled and avoids fitting a search to ten subjects, but it compares
   these configurations rather than architectures at their respective best, and for the two baselines a different reasonable specification might have placed them
   differently.

10. **Execution non-determinism is unquantified for most of the study.** Section 8.8
   covers three architectures on Arm B and EEGNet alone on Arm A, the Arm A check
   being the weaker of the two. **Arm C was not repeated at all**, and was additionally
   run on a different GPU configuration. The reported seed-level standard deviations
   are lower bounds on uncertainty for every architecture on Arm C, and for every
   architecture except EEGNet on Arms A and B.

> **हिंदी।** सबसे बड़ी सीमा दस subjects है — p का सबसे छोटा सम्भव मान 0.00195 है, और कई result
> ठीक उसी पर हैं। दूसरी, तीनों arms एक ही recordings से बने हैं, इसलिए यह "अलग dataset" नहीं है;
> A और C सिर्फ़ balancing में अलग हैं, पर trimming को अलग करने वाला चौथा arm नहीं चलाया गया।
> तीसरी, calibration हर arm पर सिर्फ़ तीन models पर है। और चौथी — **dataset का कोई base paper
> नहीं है**, इसलिए labels किस मापदंड पर लगाए गए यह कहीं दर्ज नहीं। इससे models की आपसी तुलना पर
> कोई असर नहीं पड़ता (सबको एक ही marks पर नापा गया), पर absolute आँकड़ों का बाहरी अर्थ सीमित हो
> जाता है — यह साफ़ लिख दिया गया है।

---

## Notes for the next pass — not part of the paper

- This draft is aligned to **Results draft 4** (three arms, 16 September 2026). Both
  documents scan clean against the 1977-row registry.
- **Methods must state the averaging convention.** Every metric here is computed
  within a fold and then averaged over the ten subjects with equal weight. Pooling all
  predictions before scoring gives systematically higher recall — by 0.13 to 0.25 for
  every architecture on all three arms — so a reviewer who pools will get different
  numbers and must be told why.
- **Methods must also record** that Arm C was executed on a different GPU
  configuration from Arms A and B, which is why it is not part of the
  repeated-execution check.
- Section 8.10 item 3 will need updating if the CNN and CNN-BiLSTM Arm B or Arm C
  probability files are recovered.
- Section 8.10 item 4 closes if threshold selection is ever run on Arm B; the probability
  files exist.
- Section 8.10 item 2 closes only if the fourth cell of the design is run.
- The conclusion's "eleven of twelve" refers to EEGNet vs CNN on Arm B failing at
  p = 0.0645. Keep the exact p-value in Results so the phrase is checkable.
- Subject demographics are fully sourced: ten volunteers, seven male and three female
  from the recording filenames, aged 20 to 50 from the dataset deposit itself. Closed.
