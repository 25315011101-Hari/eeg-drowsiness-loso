# 4 Methodology — draft 1

The dataset, how the recordings become labelled windows, and how the three window-set
constructions are built. Every parameter below was read out of the scripts that
produced the results. The architectures are
described in Section 5 and the evaluation protocol in Section 6.

## 4.1 Dataset

The DD-Database [D1] was used: electroencephalographic recordings made during a
simulated driving task, ten participants (seven male, three female, aged 20–50 years)
each completing two sessions, giving twenty recordings as EDF files with a companion
annotation file per recording. Recent reviews catalogue it as a public physiological
benchmark [S3], but none adds information about the recordings beyond what the deposit
itself states.

Recordings were sampled at 128 Hz. Four electrodes were retained (O1, O2, C3 and C4), with the channel order fixed in that sequence for every recording, so that
channel index carries the same meaning across subjects. The four-channel montage is
the constraint the study is built around: sparse enough for a wearable headband, and
the question is what such a montage can and cannot support. Recording length ranged
from 887,040 to 944,640 samples, 1.925 h to 2.050 h per session, 40.29 h in total.

**The annotation procedure is documented, and we do not read more into it than the
record states.** The deposit has no accompanying journal article, but its README
documents the procedure: volunteers were instructed to press an event button when they
felt drowsy during the test, and the annotation files contain the corresponding
event-button time marks, which the README describes as representing the volunteer's
drowsiness feeling. These marks are therefore treated here as documented
drowsiness-related event times. We do not interpret them as independently verified
physiological onset times, because the dataset documentation does not establish that a
recorded mark corresponds to the onset of a drowsiness episode. We take each mark as
the ground truth it is offered as and bound the reading
accordingly: every comparison here is between models scored against the same marks and
is unaffected, while every absolute figure is a figure against this annotation and
cannot be translated into another study's definition of drowsiness (Section 8.10).

## 4.2 Preprocessing

Each recording was filtered in two stages: a 50 Hz notch filter with quality factor 30
for mains interference, then a fourth-order Butterworth bandpass with cut-off
frequencies of 0.5 Hz and 40 Hz. Both were applied with zero-phase forward–backward
filtering, which is required rather than merely preferable here: windows are cut at
exact annotated time marks, so any group delay would displace the signal relative to
its label.

No artefact rejection, independent-component decomposition or channel interpolation
was applied, deliberately: the study asks what a four-channel montage supports under a
pipeline a wearable device could realistically run, so every stage requiring manual
inspection or a full montage was excluded.

## 4.3 Window extraction and labelling

The analysis unit is a 10-second window, 1,280 samples at 128 Hz, the decision resolution the application requires: long enough to contain several seconds of
rhythmic activity, short enough that an alert would still be timely.

A **drowsy** window is the 10 seconds *ending* at an annotated drowsiness-event time
mark, so it covers the interval immediately preceding that mark. Where two marks fell
close enough for their windows to overlap, the later candidate was discarded, so no
sample contributes to more than one drowsy window.

An **alert** window is taken from a non-overlapping grid over the recording, and is
retained only if its centre lies at least 20 seconds from every annotated
drowsiness-event time mark and it does not overlap any window already claimed. The
20-second guard band excludes the interval around each mark from the alert class.

**A note on this wording, because it is load-bearing.** The drowsy-window definition
is based on the documented event-button time mark. The mark is not treated as a
physiological drowsiness onset, because the dataset documentation does not establish
that interpretation: it records when the volunteer pressed the button, not where that
press falls within a drowsiness episode. The window rule is therefore stated purely as
a geometric relation to the mark (end the drowsy window at it, keep alert windows
20 s clear of it), which is exactly what the code does and exactly as much as the
deposit supports. If the marks turn out to be episode midpoints, this definition still
describes what was computed; one phrased in terms of onsets would not.

Applied to the twenty recordings this yields the raw per-subject counts, pooled over
each subject's two sessions, in **Supplementary Table S1**. Two properties of them
govern the rest of the study: drowsy windows are a small minority in every subject,
and the proportion varies over a factor of almost fifty between subjects, from 0.49 %
for S9 to 24.09 % for S7, so a subject is a source of variation in the learning
problem itself, not merely in the signal.

**Those counts are verifiable rather than merely reported.** Because Arm B is
untrimmed and its per-subject budget is the smallest subject total among them (992,
from S7), applying the proportional rule to them must reproduce Arm B's ten
per-subject drowsy counts exactly. It does for all ten; the released registry script
performs this check and refuses to emit the table if it fails.

**That check covers Arm B and no other arm.** It works because Arm B is untrimmed, so
the released counts are the counts it was built from. Arms A and C are built from
trimmed recordings whose post-trim counts are not in the released bundle, so their
published totals can be confirmed only by rebuilding from the original recordings,
which are not redistributed. The arithmetic giving Arm A its total is stated so that
such a rebuild can be checked against it: 782 drowsy windows survive overlap removal
across the untrimmed recordings, and trimming to the shortest removes a further
twelve, leaving the 770 Arm A retains. A rebuild writes its own per-subject counts
beside the released ones for exactly this comparison.

## 4.4 Per-subject budget and the three dataset arms

Pooled directly, S9 would contribute 1,431 windows and S7 only 992, weighting the
result towards the subjects with the longest usable recordings. An equal budget was
therefore drawn from every subject, the budget being the smallest subject total, and
windows within a subject were drawn without replacement using a fixed seed.

Three arms were constructed from two binary choices (whether recordings are trimmed
to a common length, and how each subject's class ratio is handled), three of the four
combinations being run.

**Arm A: trimmed, drowsy-preserving.** Every recording was first trimmed to the
length of the shortest, 887,040 samples (1.925 h), keeping the later portion, so
that all sessions contribute an equal duration; total duration is then 38.5 h. All
drowsy windows of a subject were retained and the budget filled with alert windows.
This yields **9,260 windows, 926 per subject, of which 770 (8.32 %) are drowsy**.

**Arm B: untrimmed, prevalence-preserving.** No trimming; the full 40.29 h is
used. The number of drowsy windows kept for a subject is the budget multiplied by
that subject's own prevalence, so each subject's class ratio is carried through
unchanged. This yields **9,920 windows, 992 per subject, of which 688 (6.94 %) are
drowsy**.

**Arm C: trimmed, prevalence-preserving.** Trimming as in Arm A, balancing as in
Arm B. This yields **9,260 windows, 926 per subject, of which 673 (7.27 %) are
drowsy**.

**Three cells of a two-by-two design give two controlled contrasts, one per factor.**
Arms A and C are both trimmed and differ only in the balancing rule, so their
comparison isolates balancing; Arms B and C both preserve each subject's class ratio
and differ only in trimming, so theirs isolates trimming. Section 7 reports both. The
fourth cell (untrimmed with every drowsy window kept) was not run; it would give a
second instance of each contrast rather than a new factor.

Trimming carries its own consequences: it reduces the per-subject budget from 992
windows to 926 and shifts the prevalence from 6.94 % to 7.27 %. These are effects of
trimming rather than confounds beside it, and the B-against-C contrast attributes them
to it.

Per-subject drowsy counts, S1 through S10 in order, are 82, 58, 178, 79, 60, 50,
238, 11, 5, 9 for Arm A; 67, 46, 163, 68, 47, 38, 239, 8, 5, 7 for Arm B; and 65,
43, 164, 63, 46, 37, 238, 8, 3, 6 for Arm C.

Three reference values follow from each arm's class prior and are used throughout the
results. The three constructions are summarised in **Table 1**.

**Table 1. The three constructions, and the reference values each one implies.**
Prevalence is set by the construction, and every prevalence-dependent reference
follows from it: the PR-AUC chance level is the prevalence itself, the Brier
reference is π(1 − π), and the always-alert accuracy is 1 − π. This is the table
Section 7 refers back to rather than repeating.

| Arm | Trimming | Balancing | Windows | Per subject | Drowsy | Prevalence | PR-AUC chance | Brier reference π(1 − π) | Always-alert accuracy |
|---|---|---|---|---|---|---|---|---|---|
| **A** | trimmed to shortest | every drowsy window kept | 9,260 | 926 | 770 | 8.32 % | 0.0832 | **0.0762** | 91.68 % |
| **B** | untrimmed | subject's own ratio preserved | 9,920 | 992 | 688 | 6.94 % | 0.0694 | **0.0645** | 93.06 % |
| **C** | trimmed to shortest | subject's own ratio preserved | 9,260 | 926 | 673 | 7.27 % | 0.0727 | **0.0674** | 92.73 % |

The prior is the chance level for average precision, and π(1 − π) is the Brier score
of the constant predictor that always outputs it, the reference against which
probability reliability is read, a model above it being worse, as a probability, than
that constant.


Every window count in Table 1 is regenerated from the EDF files by the released construction script, which refuses to write unless its internal and reference checks both pass; Arm B's counts are reproducible from the public recordings alone. Supplementary Note 1 gives the two checks and the rebuild result.
