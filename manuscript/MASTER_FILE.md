# Master Paper Information File

**Generated, not typed.** Every number below is read from `results/MASTER_NUMBERS.csv` (1977 rows), the calibration summaries and `config.py` at the moment this ran. Regenerate with

```
python3 tools/master_file.py
```

A hand-typed master file is one more place for a number to go stale, and it
carries authority while it does so. This one cannot: a claim that leaves the
registry makes the generator fail rather than print an old value.

| | |
|---|---|
| Target journal | Biomedical Signal Processing and Control |
| Manuscript build | `9b125f0f2c59` |
| Manuscript length | `25844 words`, from the build stamp |
| Registry | 1977 rows |
| Dataset | Drivers Drowsiness Database (DD-Database), Dryad 10.5061/dryad.5tb2rbp9c, CC0 1.0 |

## 1. Study size

| | |
|---|---|
| Subjects | 10 |
| Seeds | 5 |
| Architectures | 5 |
| Folds per arm | 250 |
| Total folds | 750 |
| Window length, samples | 1280 |
| Seeds used | 42, 1, 2, 3, 4 |
| EEG channels | O1, O2, C3, C4 at 128 Hz |
| Window | 10 s, non-overlapping |

**Labelling.** A drowsy window ends at an annotated drowsiness-event time mark; alert windows keep a 20 s guard from every such mark. The dataset documentation identifies the marks as event-button time marks recorded when volunteers felt drowsy. It does not establish whether the recorded time corresponds to the onset of a drowsiness episode or another point within the episode, so the word *onset* is not used.

## 2. The three constructions

| Arm | Construction | Windows | Per subject | Drowsy | Prevalence | Brier reference | Always alert |
|---|---|---|---|---|---|---|---|
| A | trimmed, every drowsy window kept | 9260 | 926 | 770 | 8.3153 % | 0.0762 | 91.68 % |
| B | untrimmed, subject's own class ratio | 9920 | 992 | 688 | 6.9355 % | 0.0645 | 93.06 % |
| C | trimmed, subject's own class ratio | 9260 | 926 | 673 | 7.2678 % | 0.0674 | 92.73 % |

**Two contrasts, each varying one factor.** A against C isolates the balancing rule with trimming held constant; B against C examines trimming with balancing held at proportional. The fourth cell of the design was not run, so the trimming result is conditional on that balancing rule.

**Accuracy is printed to two decimal places throughout**, including the baselines, because the margins in Results Section 5.3 are smaller than a tenth of a point. Full precision: 91.6847, 93.0645, 92.7322.

## 3. Architectures

| Architecture | Parameters | Configuration |
|---|---|---|
| EEGNet | 1,809 | authors' reference implementation |
| ShallowConvNet | 14,121 | authors' reference implementation |
| CNN | 44,705 | prespecified for this study |
| DeepConvNet | 150,226 | authors' reference implementation |
| CNN-BiLSTM | 180,641 | prespecified for this study |

The recurrent block adds 135,936 parameters -- 3.04 times the CNN's own total, taking the CNN-BiLSTM to 4.04 times it -- so the CNN / CNN-BiLSTM pair is the closest architectural comparison in the study but **not a capacity-neutral ablation**.

## 4. Ranking quality, subject-averaged

**ROC-AUC** (mean ± SD across the five seed-level means)

| Model | Arm A | Arm B | Arm C |
|---|---|---|---|
| EEGNet | 0.884 ± 0.0074 | 0.9003 ± 0.0079 | 0.8831 ± 0.0095 |
| ShallowConvNet | 0.846 ± 0.003 | 0.8472 ± 0.0141 | 0.8332 ± 0.0184 |
| CNN | 0.8428 ± 0.0094 | 0.8662 ± 0.0128 | 0.8469 ± 0.0173 |
| DeepConvNet | 0.8123 ± 0.0079 | 0.793 ± 0.0328 | 0.8339 ± 0.0251 |
| CNN-BiLSTM | 0.8213 ± 0.0221 | 0.859 ± 0.0161 | 0.8472 ± 0.0332 |

**PR-AUC** (mean ± SD across the five seed-level means)

| Model | Arm A | Arm B | Arm C |
|---|---|---|---|
| EEGNet | 0.4314 ± 0.0058 | 0.4398 ± 0.0257 | 0.4073 ± 0.0074 |
| ShallowConvNet | 0.411 ± 0.0115 | 0.3994 ± 0.0144 | 0.3724 ± 0.0189 |
| CNN | 0.3382 ± 0.005 | 0.3599 ± 0.0193 | 0.2946 ± 0.0121 |
| DeepConvNet | 0.4051 ± 0.0108 | 0.3841 ± 0.0177 | 0.3862 ± 0.0128 |
| CNN-BiLSTM | 0.3986 ± 0.0207 | 0.397 ± 0.0384 | 0.3772 ± 0.0251 |

**EEGNet's ROC-AUC is higher in all twelve paired comparisons, and the difference reaches the nominal level in eleven** (4 of 4 on Arm A, 3 of 4 on Arm B, 4 of 4 on Arm C). The one exception is the CNN on Arm B at p = 0.0645. None of the six non-EEGNet pairs separates on ROC-AUC on any arm; the smallest such p is 0.1934, 0.084 and 0.4316.

## 5. Accuracy against recall

| Arm | ρ | p | attainable floor on five points |
|---|---|---|---|
| A | -1.0 | 0.0167 | 0.0167 |
| B | -0.9 | 0.0833 | 0.0167 |
| C | -0.6 | 0.35 | 0.0167 |

**The correlation is over five architectures, not ten subjects.** Its attainable floor is therefore 0.0167, not the Wilcoxon floor of 0.00195312 that applies to the paired subject-level tests. Quoting the Wilcoxon floor for this correlation would claim a precision five points cannot give.

What holds on all three constructions without needing a p-value: **the two most accurate architectures are exactly the two with the lowest recall.** On Arm C the correlation does not reach significance, because the two least sensitive architectures exchange places with one another.

## 6. Probability quality

**Pooled Brier score**, with each arm's class-prior reference

| Model | Arm A | Arm B | Arm C |
|---|---|---|---|
| EEGNet | 0.1010 **above** | 0.0859 **above** | 0.0952 **above** |
| ShallowConvNet | 0.1291 **above** | 0.1369 **above** | 0.1383 **above** |
| CNN | 0.0671 below | 0.0577 below | 0.0608 below |
| DeepConvNet | 0.0592 below | 0.0603 below | 0.0511 below |
| CNN-BiLSTM | 0.0781 **above** | 0.0743 **above** | 0.0808 **above** |
| *reference* | *0.0762* | *0.0645* | *0.0674* |

The same three architectures are above the reference and the same two below it on every construction. The Brier score is a proper scoring rule covering calibration **and** refinement; it is not a pure calibration measure.

## 7. Recalibration, measured

| | |
|---|---|
| Folds measured | 150 |
| Platt fits with a positive slope | 150 |
| Smallest fitted slope | 0.3243 |
| Largest fitted slope | 1.3312 |
| Largest Platt change in fold ROC-AUC | 0.0000397267 |
| Largest Platt change in fold PR-AUC | 0.003413347 |
| Folds where the ε-clip created ties | 10 |
| Most ties on one fold | 95 |
| Isotonic lowered ROC-AUC on | 123 |
| Isotonic lowered PR-AUC on | 144 |
| Distinct scores per fold, before isotonic | 926 |
| Distinct scores per fold, after isotonic | 25 |

A logistic map preserves the ranking only when its fitted slope is positive, which is a property of the fits and was therefore measured. The per-fold movements above bound what one fold can move; they are NOT what the tables print, which is an average over fifty folds. The reported quantity was measured separately:

| EEGNet, subject-averaged ROC-AUC change after Platt | 0.0000009981 |
| EEGNet, subject-averaged PR-AUC change after Platt | 0.0000222899 |
| CNN, subject-averaged ROC-AUC change after Platt | 0 |
| CNN, subject-averaged PR-AUC change after Platt | 0 |
| CNN-BiLSTM, subject-averaged ROC-AUC change after Platt | 0 |
| CNN-BiLSTM, subject-averaged PR-AUC change after Platt | 0 |

So the claim is **the subject-averaged ROC-AUC and PR-AUC are unchanged at the reported precision**, not algebraic invariance and not a statement about pooled metrics, which are not invariant because a different map is fitted for each fold.

**Calibration coverage is three architectures per arm, and not the same three.**

| Arm | Architectures with per-window scores retained |
|---|---|
| A | CNN, CNN-BiLSTM, EEGNet |
| B | DeepConvNet, EEGNet, ShallowConvNet |
| C | DeepConvNet, EEGNet, ShallowConvNet |

Brier scores cover all five architectures on all three arms, because they need only the pooled predictions. Per-window probability files are released for Arm A only: 15 files, 3.2 MB.

## 8. Variation

| Arm | subject-to-seed SD ratio for PR-AUC, across the five architectures |
|---|---|
| A | 12 to 48 times |
| B | 6 to 18 times |
| C | 10 to 36 times |

**Repeated execution.** Where it was measured, a single subject's mean moved further between two identical runs than the seed-level ± this paper reports:

| | overall shift over 50 folds | largest single subject's shift |
|---|---|---|
| DeepConvNet, ROC-AUC | 0.003 | **0.0407** |
| DeepConvNet, F1 | 0.0213 | **0.1273** |
| ShallowConvNet, ROC-AUC | 0.0057 | **0.0334** |
| ShallowConvNet, F1 | 0.001 | **0.0702** |

**The two columns are not interchangeable.** The overall figures are means over all fifty folds; the subject-level figures are what bear on how the tables should be read, and they are four to fourteen times larger. An earlier draft labelled the overall figures as subject-level, and that mislabelling is the reason this table prints both.

## 9. Smallest cells, for anyone quoting a subject

| Subject | Arm A | Arm B | Arm C |
|---|---|---|---|
| S9 | 5 | 5 | 3 |
| S10 | 9 | 7 | 6 |
| S8 | 11 | 8 | 8 |

Drowsy-window counts differ by arm, so a sentence about a subject must say which arm it means.

## 10. What is still open

These are decisions, not measurements, and no generator can fill them in.

- **The repository is not published.** The data-availability statement promises files no one can yet fetch.
- CRediT roles, to be confirmed by both authors.
- Title, acknowledgements and funding are settled; the AI declaration is omitted on the corresponding author's instruction. See REPRODUCIBILITY.md section 5 for the wording and the record.

`python3 tools/preflight.py` reports every remaining placeholder by file and line on each run.

