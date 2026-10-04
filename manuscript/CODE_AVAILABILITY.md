# Code and data availability

<!-- not-for-submission:start -->
Two versions were drafted. The **Short version** below is the one that goes into the
manuscript, and it is the only part of this file the builder keeps. The longer
variant and the correction note that follow are working material, kept here so the
authors can see them, and are stripped from the assembled document by the markers
around them. They were not marked until 25 September 2026, and until then both rode
into the built manuscript's back matter — the longer variant beside the short one it
was an alternative to, and a note whose own first sentence says it does not belong
in the paper.

Two versions. The first is for the statement BSPC asks for; the second is a
longer paragraph for the end of the Methods section if the editor wants the
reproducibility detail in the body rather than in a back-matter statement.
<!-- not-for-submission:end -->

## Statement

> **Code availability.** All code used in this study is available at
> `<repository URL>`. It covers the full pipeline: window construction from the
> raw EDF recordings, leave-one-subject-out training of all five architectures,
> out-of-subject probability recalibration and threshold selection, every
> statistic reported, and a script that regenerates all tables in Section 7
> directly from the result files. The per-fold results for all 750 folds are
> released with it, along with the calibration and threshold summaries, so every
> table and every significance test can be regenerated without a GPU and without
> access to the recordings. **The per-window probability files are released for
> Arm A only** (15 files, 3.2 MB, three architectures x five seeds); the released
> test suite refits all 150 of its calibrators from those scores and asserts that
> the published Arm A summary is reproduced. For Arms B and C the calibration and
> threshold analyses are released as computed summaries, and recomputing them from
> raw scores requires re-running the training stage.
>
> **Data availability.** The EEG recordings are the Drivers Drowsiness Database
> (DD-Database) [D1], openly available from Dryad at
> https://doi.org/10.5061/dryad.5tb2rbp9c under a CC0 1.0 Universal public-domain
> dedication. They are not redistributed here. The window-construction script reproduces each of the three
> dataset constructions from the original EDF files and verifies the result
> against the per-subject window counts reported in Supplementary Table S1 before writing
> anything.
>
> **Third-party code.** EEGNet, ShallowConvNet and DeepConvNet use the ARL
> reference implementation [A1], obtained from
> https://github.com/vlawhern/arl-eegmodels.

---

<!-- not-for-submission:start -->

## Longer version (for the end of Methods)

> The complete pipeline is released as code at `<repository URL>`, together with
> the per-fold results for all 750 folds and the calibration and threshold
> summaries. The per-window probability files those two analyses were computed
> from are released for Arm A only — fifteen files, three architectures at five
> seeds each — so the Arm A calibration is recomputable from the raw scores, while
> for Arms B and C the corresponding analyses are verifiable from the summaries
> rather than recomputable without re-running training. The released Arm A EEGNet
> scores come from the earlier of the two Arm A executions reported in Section 7.9.
>
> Reproducing the analysis requires only NumPy, pandas, SciPy and scikit-learn:
> every table and every significance test in Section 7 is regenerated from the
> released per-fold files by a single command, on a laptop, in about two minutes.
> Reproducing the *training* additionally requires TensorFlow, a GPU and the
> original recordings, and takes approximately three hours per construction for
> all five architectures.
>
> Four choices that materially affect the reported numbers are enforced in the
> code rather than left to convention, and are stated here so that a reader can
> check them. (i) Each leave-one-subject-out fold receives its own calibrator and
> its own selected threshold, fitted on the other nine subjects of the same seed;
> no calibrator or threshold is fitted on a set containing the subject it is
> applied to. (ii) Every paired test operates on the ten subject-level
> differences rather than on the fifty folds, since folds from the same subject
> are not independent. (iii) Subject-averaged and pooled estimators are computed
> by separate functions and reported in separate tables; they differ here by up
> to 0.25 in recall. (iv) Folds in which the model predicts no drowsy window at
> the default threshold are retained in every average, with F1 = 0 and balanced
> accuracy = 0.500 by construction.
>
> A number enters the manuscript only if it appears in a registry regenerated
> from the raw result files, and an automated scan of each draft reports any
> printed figure absent from that registry. Both documents scan clean. The scan
> verifies numbers and not claims, so it is a floor rather than a guarantee.
>
> Execution is not bit-reproducible on a GPU and the paper does not claim it is;
> the repeated-execution check of Section 7.7 quantifies what varies between
> identical runs, and the reported seed-level standard deviations should be read
> as lower bounds for every architecture except EEGNet.

---

## Note on the false-positive correction (16 September 2026)

This is recorded here so that the change is documented rather than silent. It is
**not** intended for the manuscript; the corrected tables are already in
Section 4 of Results draft 4.

Drafts 1 to 3 reconstructed the pooled false-positive counts by inverting the
per-fold precision, on the reasoning that a fold's predicted-positive total is
TP / precision. That inversion is undefined when precision is zero, and precision
is zero for every degenerate fold — including folds that predicted some windows
drowsy and got all of them wrong, which have false positives but no true ones.
Those folds were therefore treated as having predicted nothing.

The effect, measured against the false positives recorded directly from the
predictions in `ALL_POOLED.csv`:

| Arm | largest FP under-count | largest accuracy shift |
|---|---|---|
| A | 17 windows (ShallowConvNet) | 0.23 points |
| B | 3 windows (DeepConvNet) | 0.07 points |
| C | 7 windows (CNN-BiLSTM, ShallowConvNet) | 0.11 points |

No conclusion changes. Two sentences of wording do:

* Arm A, the CNN's accuracy was 91.7 % and is 91.63 %, against an always-alert
  baseline of 91.68 %. It was reported as matching the baseline and in fact falls
  just short of it, which strengthens rather than weakens the section's argument:
  on Arm A only one architecture exceeds the baseline, not two.
* Arm C, the CNN's accuracy was 92.7 % and is 92.65 %, against a baseline of
  92.73 %. "CNN matches it" becomes "CNN falls just short".

The accuracy gap between DeepConvNet and EEGNet on Arm C moves from 4.0 to 4.1
points. The accuracy-versus-recall rank correlations (−1.000, −0.900, −0.600) are
unchanged.

The check that caught it is in the released test suite
(`test_reconstructed_false_positives_are_a_lower_bound`), and
`stats.pooled_confusion` now marks every confusion matrix it returns as either
`fp_source="recorded"` or `fp_source="reconstructed"`.

<!-- not-for-submission:end -->
