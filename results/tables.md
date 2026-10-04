## 1. Architecture comparison

**Subject-averaged ROC-AUC**

| Model | Parameters | Arm A | Arm B | Arm C |
|---|---|---|---|---|
| EEGNet | 1,809 | 0.884 ± 0.007 | 0.900 ± 0.008 | 0.883 ± 0.010 |
| ShallowConvNet | 14,121 | 0.846 ± 0.003 | 0.847 ± 0.014 | 0.833 ± 0.018 |
| CNN | 44,705 | 0.843 ± 0.009 | 0.866 ± 0.013 | 0.847 ± 0.017 |
| DeepConvNet | 150,226 | 0.812 ± 0.008 | 0.793 ± 0.033 | 0.834 ± 0.025 |
| CNN-BiLSTM | 180,641 | 0.821 ± 0.022 | 0.859 ± 0.016 | 0.847 ± 0.033 |

**Subject-averaged PR-AUC** (chance level 0.0832 / 0.0694 / 0.0727)

| Model | Parameters | Arm A | Arm B | Arm C |
|---|---|---|---|---|
| EEGNet | 1,809 | 0.431 ± 0.006 | 0.440 ± 0.026 | 0.407 ± 0.007 |
| ShallowConvNet | 14,121 | 0.411 ± 0.011 | 0.399 ± 0.014 | 0.372 ± 0.019 |
| CNN | 44,705 | 0.338 ± 0.005 | 0.360 ± 0.019 | 0.295 ± 0.012 |
| DeepConvNet | 150,226 | 0.405 ± 0.011 | 0.384 ± 0.018 | 0.386 ± 0.013 |
| CNN-BiLSTM | 180,641 | 0.399 ± 0.021 | 0.397 ± 0.038 | 0.377 ± 0.025 |

**EEGNet against every other architecture, ROC-AUC, ten paired subject-level differences**

| EEGNet vs | Arm A | Arm B | Arm C |
|---|---|---|---|
| ShallowConvNet | **p = 0.0039** (9/10) | **p = 0.0098** (8/10) | **p = 0.0020** (10/10) |
| CNN | **p = 0.0020** (10/10) | p = 0.0645 (8/10) | **p = 0.0488** (8/10) |
| DeepConvNet | **p = 0.0020** (10/10) | **p = 0.0020** (10/10) | **p = 0.0195** (9/10) |
| CNN-BiLSTM | **p = 0.0039** (9/10) | **p = 0.0020** (10/10) | **p = 0.0137** (9/10) |

Smallest attainable p-value on ten pairs: 0.00195.

**The six pairwise comparisons that do not involve EEGNet**

| Arm | significant | smallest p |
|---|---|---|
| A | 0 of 6 | 0.1934 |
| B | 0 of 6 | 0.0840 |
| C | 0 of 6 | 0.4316 |

**Parameter count against ROC-AUC across the five architectures**

| Arm | rho | p |
|---|---|---|
| A | -0.900 | 0.0374 |
| B | -0.500 | 0.3910 |
| C | -0.100 | 0.8729 |

Smallest attainable p-value on five points: about 0.017.

**Agreement between the per-arm orderings**

| Metric | A-B | A-C | B-C |
|---|---|---|---|
| ROC-AUC | +0.700 | +0.300 | +0.800 |
| PR-AUC | +0.900 | +0.700 | +0.600 |
| Balanced accuracy | +0.700 | +0.900 | +0.900 |
| F1 | +1.000 | +1.000 | +1.000 |

## 1a. Arms A and C isolate balancing

**Arms A and C share their trimming and differ only in balancing, so this comparison isolates that factor.**

| Model | ROC-AUC A → C | PR-AUC A → C | F1 A → C |
|---|---|---|---|
| EEGNet | 0.884 → 0.883, p = 0.4922 | 0.431 → 0.407, p = 0.1055 | 0.388 → 0.382, p = 0.9102 |
| ShallowConvNet | 0.846 → 0.833, p = 0.6250 | 0.411 → 0.372, **p = 0.0039** | 0.354 → 0.312, **p = 0.0059** |
| CNN | 0.843 → 0.847, p = 0.8457 | 0.338 → 0.295, **p = 0.0020** | 0.267 → 0.219, **p = 0.0469** |
| DeepConvNet | 0.812 → 0.834, **p = 0.0488** | 0.405 → 0.386, p = 0.1934 | 0.310 → 0.300, p = 0.1641 |
| CNN-BiLSTM | 0.821 → 0.847, **p = 0.0488** | 0.399 → 0.377, p = 0.2324 | 0.361 → 0.353, p = 0.9102 |

## 2. The CNN / CNN-BiLSTM ablation

**CNN → CNN-BiLSTM: identical trunk, one component changed.**

| Metric | Arm A: CNN → BiLSTM | Arm B: CNN → BiLSTM | Arm C: CNN → BiLSTM |
|---|---|---|---|
| ROC-AUC | 0.843 → 0.821, p = 0.6953 (4/10) | 0.866 → 0.859, p = 0.8457 (4/10) | 0.847 → 0.847, p = 0.5566 (6/10) |
| PR-AUC | 0.338 → 0.399, **p = 0.0059** (9/10) | 0.360 → 0.397, p = 0.2324 (7/10) | 0.295 → 0.377, **p = 0.0039** (9/10) |
| Bal. acc. | 0.618 → 0.696, **p = 0.0098** (8/10) | 0.601 → 0.725, **p = 0.0020** (10/10) | 0.599 → 0.714, **p = 0.0039** (9/10) |
| F1 | 0.267 → 0.361, **p = 0.0195** (8/10) | 0.245 → 0.372, **p = 0.0195** (9/10) | 0.219 → 0.353, **p = 0.0039** (10/10) |

## 3. Pooled confusion matrices

**Arm A** (9260 windows, 770 drowsy; always-alert accuracy 91.68 %)

| Model | TN | FP | FN | TP | Recall | Precision | Accuracy |
|---|---|---|---|---|---|---|---|
| DeepConvNet | 8,212 | 278 | 395 | 375 | 0.487 | 0.574 | 92.73 % |
| CNN | 8,095 | 395 | 380 | 390 | 0.506 | 0.497 | 91.63 % |
| CNN-BiLSTM | 7,800 | 690 | 272 | 498 | 0.646 | 0.419 | 89.61 % |
| EEGNet | 7,631 | 859 | 187 | 583 | 0.758 | 0.405 | 88.71 % |
| ShallowConvNet | 7,090 | 1,400 | 158 | 612 | 0.794 | 0.304 | 83.17 % |

Accuracy against pooled recall: rho = -1.000 (p = 0.0000).

**Arm B** (9920 windows, 688 drowsy; always-alert accuracy 93.06 %)

| Model | TN | FP | FN | TP | Recall | Precision | Accuracy |
|---|---|---|---|---|---|---|---|
| CNN | 8,966 | 266 | 428 | 260 | 0.377 | 0.494 | 93.00 % |
| DeepConvNet | 8,871 | 361 | 379 | 309 | 0.449 | 0.461 | 92.54 % |
| EEGNet | 8,420 | 812 | 157 | 531 | 0.772 | 0.395 | 90.23 % |
| CNN-BiLSTM | 8,491 | 741 | 235 | 453 | 0.658 | 0.380 | 90.17 % |
| ShallowConvNet | 7,578 | 1,654 | 146 | 542 | 0.787 | 0.247 | 81.85 % |

Accuracy against pooled recall: rho = -0.900 (p = 0.0374).

**Arm C** (9260 windows, 673 drowsy; always-alert accuracy 92.73 %)

| Model | TN | FP | FN | TP | Recall | Precision | Accuracy |
|---|---|---|---|---|---|---|---|
| DeepConvNet | 8,328 | 259 | 338 | 335 | 0.498 | 0.564 | 93.56 % |
| CNN | 8,247 | 340 | 341 | 332 | 0.493 | 0.494 | 92.65 % |
| EEGNet | 7,759 | 828 | 145 | 528 | 0.785 | 0.390 | 89.50 % |
| CNN-BiLSTM | 7,774 | 813 | 180 | 493 | 0.732 | 0.377 | 89.28 % |
| ShallowConvNet | 7,092 | 1,495 | 155 | 518 | 0.770 | 0.257 | 82.19 % |

Accuracy against pooled recall: rho = -0.600 (p = 0.2848).



## 3a. Recall conventions and degenerate folds

**Pooled and subject-averaged recall**

| Model | Arm A: subj-avg → pooled | Arm B: subj-avg → pooled | Arm C: subj-avg → pooled |
|---|---|---|---|
| EEGNet | 0.5217 → 0.7577 (+0.2360) | 0.5398 → 0.7721 (+0.2323) | 0.5343 → 0.7851 (+0.2508) |
| ShallowConvNet | 0.5725 → 0.7943 (+0.2218) | 0.5957 → 0.7875 (+0.1918) | 0.5687 → 0.7700 (+0.2012) |
| CNN | 0.2856 → 0.5062 (+0.2206) | 0.2318 → 0.3773 (+0.1456) | 0.2395 → 0.4933 (+0.2538) |
| DeepConvNet | 0.2885 → 0.4868 (+0.1982) | 0.2823 → 0.4488 (+0.1665) | 0.2865 → 0.4981 (+0.2116) |
| CNN-BiLSTM | 0.4756 → 0.6462 (+0.1707) | 0.5320 → 0.6584 (+0.1264) | 0.5258 → 0.7322 (+0.2064) |

**Degenerate folds** (no true positive at 0.5, so F1 = 0 and balanced accuracy = 0.500 by construction)

| Arm | EEGNet | ShallowConvNet | CNN | DeepConvNet | CNN-BiLSTM |
|---|---|---|---|---|---|
| A | 9 / 50 | 4 / 50 | 17 / 50 | 11 / 50 | 7 / 50 |
| B | 5 / 50 | 4 / 50 | 12 / 50 | 12 / 50 | 3 / 50 |
| C | 9 / 50 | 4 / 50 | 20 / 50 | 14 / 50 | 7 / 50 |

## 4. Between-subject variation

**Between-subject spread against between-seed spread, PR-AUC**

| Arm | ratio over the five architectures | subject PR-AUC range, averaged over architectures |
|---|---|---|
| A | 12 to 48 times | 0.027 (S9) to 0.810 (S7) |
| B | 6 to 18 times | 0.079 (S8) to 0.825 (S7) |
| C | 10 to 36 times | 0.022 (S9) to 0.818 (S7) |

**A subject's drowsy-window count against its PR-AUC** (raw / after subtracting the subject's own prevalence)

| Model | Arm A: raw / minus prevalence | Arm B: raw / minus prevalence | Arm C: raw / minus prevalence |
|---|---|---|---|
| EEGNet | +0.915 / +0.903 | +0.891 / +0.891 | +0.903 / +0.879 |
| ShallowConvNet | +0.952 / +0.891 | +0.830 / +0.806 | +0.915 / +0.879 |
| CNN | +0.927 / +0.867 | +0.588 / +0.442 | +0.976 / +0.915 |
| DeepConvNet | +0.927 / +0.891 | +0.915 / +0.891 | +0.903 / +0.879 |
| CNN-BiLSTM | +0.976 / +0.915 | +0.794 / +0.794 | +0.939 / +0.903 |

**The same relationship as a multiple of chance** (PR-AUC divided by prevalence), which has the opposite sign

| Model | Arm A | Arm B | Arm C |
|---|---|---|---|
| EEGNet | -0.564 (0.0897) | -0.806 (0.0049) | -0.527 (0.1173) |
| ShallowConvNet | -0.430 (0.2145) | -0.673 (0.0330) | -0.588 (0.0739) |
| CNN | -0.612 (0.0600) | -0.709 (0.0217) | -0.624 (0.0537) |
| DeepConvNet | -0.418 (0.2291) | -0.479 (0.1615) | -0.382 (0.2763) |
| CNN-BiLSTM | -0.273 (0.4458) | -0.879 (0.0008) | -0.382 (0.2763) |

## 5. Probability reliability

**Arm A** (class-prior Brier reference 0.0762)

| Model | ROC-AUC | PR-AUC | Bal. acc. | Brier |
|---|---|---|---|---|
| EEGNet | 0.9015 ± 0.0066 | 0.5103 ± 0.0631 | 0.8283 ± 0.0108 | **0.1010** |
| ShallowConvNet | 0.8801 ± 0.0065 | 0.4742 ± 0.0482 | 0.8147 ± 0.0038 | **0.1291** |
| CNN | 0.8762 ± 0.0075 | 0.4790 ± 0.0215 | 0.7298 ± 0.0286 | 0.0671 |
| DeepConvNet | 0.8703 ± 0.0257 | 0.4987 ± 0.0514 | 0.7270 ± 0.0471 | 0.0592 |
| CNN-BiLSTM | 0.8751 ± 0.0242 | 0.4913 ± 0.0460 | 0.7825 ± 0.0529 | **0.0781** |

**Arm B** (class-prior Brier reference 0.0645)

| Model | ROC-AUC | PR-AUC | Bal. acc. | Brier |
|---|---|---|---|---|
| EEGNet | 0.9190 ± 0.0052 | 0.5222 ± 0.0383 | 0.8421 ± 0.0104 | **0.0859** |
| ShallowConvNet | 0.8782 ± 0.0191 | 0.4302 ± 0.1178 | 0.8042 ± 0.0173 | **0.1369** |
| CNN | 0.8722 ± 0.0130 | 0.4084 ± 0.0722 | 0.6742 ± 0.0567 | 0.0577 |
| DeepConvNet | 0.8617 ± 0.0242 | 0.4134 ± 0.0904 | 0.7049 ± 0.0835 | 0.0603 |
| CNN-BiLSTM | 0.8740 ± 0.0306 | 0.4603 ± 0.0823 | 0.7891 ± 0.0546 | **0.0743** |

**Arm C** (class-prior Brier reference 0.0674)

| Model | ROC-AUC | PR-AUC | Bal. acc. | Brier |
|---|---|---|---|---|
| EEGNet | 0.9155 ± 0.0041 | 0.5079 ± 0.0501 | 0.8444 ± 0.0040 | **0.0952** |
| ShallowConvNet | 0.8614 ± 0.0280 | 0.3767 ± 0.0341 | 0.7980 ± 0.0278 | **0.1383** |
| CNN | 0.8764 ± 0.0107 | 0.4660 ± 0.0373 | 0.7269 ± 0.0279 | 0.0608 |
| DeepConvNet | 0.8874 ± 0.0196 | 0.5093 ± 0.0812 | 0.7340 ± 0.0230 | 0.0511 |
| CNN-BiLSTM | 0.8961 ± 0.0163 | 0.4775 ± 0.0442 | 0.8188 ± 0.0270 | **0.0808** |

**The partition, with the margin against each arm's own reference**

| Model | Arm A (ref 0.0762) | Arm B (ref 0.0645) | Arm C (ref 0.0674) |  |
|---|---|---|---|---|
| EEGNet | 0.1010 (+0.0248) | 0.0859 (+0.0214) | 0.0952 (+0.0278) | above ×3 |
| ShallowConvNet | 0.1291 (+0.0529) | 0.1369 (+0.0724) | 0.1383 (+0.0709) | above ×3 |
| CNN | 0.0671 (-0.0091) | 0.0577 (-0.0068) | 0.0608 (-0.0066) | below ×3 |
| DeepConvNet | 0.0592 (-0.0170) | 0.0603 (-0.0042) | 0.0511 (-0.0163) | below ×3 |
| CNN-BiLSTM | 0.0781 (+0.0019) | 0.0743 (+0.0098) | 0.0808 (+0.0134) | above ×3 |

**ROC-AUC against raw pooled Brier across the five architectures** (reported only because a reader may compute it)

| Arm | with pooled ROC-AUC | with subject-averaged ROC-AUC |
|---|---|---|
| A | +0.800 (0.1041) | +0.800 (0.1041) |
| B | +0.800 (0.1041) | +0.000 (1.0000) |
| C | -0.100 (0.8729) | +0.000 (1.0000) |

## 6. Out-of-subject recalibration

**Arm A** (reference 0.0762), subject-averaged

| Model | ECE raw | ECE + Platt | ECE + isotonic | Brier raw | Brier + Platt | Brier + isotonic |
|---|---|---|---|---|---|---|
| CNN | 0.0605 | 0.0447 | 0.0473 | 0.0671 | 0.0585 | 0.0604 |
| CNN-BiLSTM | 0.0912 | 0.0561 | 0.0584 | 0.0781 | 0.0590 | 0.0599 |
| EEGNet | 0.1950 | 0.0625 | 0.0603 | 0.1009 | 0.0635 | 0.0610 |

Above the reference: 2 of 3 raw → 0 of 3 after Platt scaling.

**Arm B** (reference 0.0645), subject-averaged

| Model | ECE raw | ECE + Platt | ECE + isotonic | Brier raw | Brier + Platt | Brier + isotonic |
|---|---|---|---|---|---|---|
| DeepConvNet | 0.0679 | 0.0631 | 0.0613 | 0.0603 | 0.0592 | 0.0577 |
| EEGNet | 0.1717 | 0.0547 | 0.0548 | 0.0859 | 0.0538 | 0.0522 |
| ShallowConvNet | 0.2049 | 0.0605 | 0.0595 | 0.1369 | 0.0584 | 0.0583 |

Above the reference: 2 of 3 raw → 0 of 3 after Platt scaling.

**Arm C** (reference 0.0674), subject-averaged

| Model | ECE raw | ECE + Platt | ECE + isotonic | Brier raw | Brier + Platt | Brier + isotonic |
|---|---|---|---|---|---|---|
| DeepConvNet | 0.0460 | 0.0502 | 0.0509 | 0.0511 | 0.0529 | 0.0528 |
| EEGNet | 0.1918 | 0.0580 | 0.0576 | 0.0952 | 0.0573 | 0.0551 |
| ShallowConvNet | 0.2001 | 0.0724 | 0.0709 | 0.1383 | 0.0658 | 0.0663 |

Above the reference: 2 of 3 raw → 0 of 3 after Platt scaling.

**Raw against Platt on the ten subject-level differences**

| Arm | Model | Brier | ECE |
|---|---|---|---|
| A | CNN | **p = 0.0488** (9/10) | p = 0.0840 (7/10) |
| A | CNN-BiLSTM | **p = 0.0488** (9/10) | **p = 0.0488** (9/10) |
| A | EEGNet | **p = 0.0371** (8/10) | **p = 0.0020** (10/10) |
| B | DeepConvNet | p = 0.7695 (5/10) | p = 0.7695 (4/10) |
| B | EEGNet | **p = 0.0488** (8/10) | **p = 0.0020** (10/10) |
| B | ShallowConvNet | **p = 0.0273** (9/10) | **p = 0.0039** (9/10) |
| C | DeepConvNet | p = 0.5566 (6/10) | p = 0.6250 (6/10) |
| C | EEGNet | **p = 0.0371** (9/10) | **p = 0.0020** (10/10) |
| C | ShallowConvNet | **p = 0.0371** (8/10) | **p = 0.0059** (9/10) |

## 7. Threshold selection

**Arm A**

| Model | Rule | Balanced accuracy | F1 |
|---|---|---|---|
| CNN | BA-optimal | 0.618 → 0.649, p = 0.2324 | 0.267 → 0.269, p = 1.0000 |
| CNN | F1-optimal | 0.618 → 0.616, p = 0.5703 | 0.267 → 0.260, p = 0.3750 |
| CNN-BiLSTM | BA-optimal | 0.696 → 0.717, p = 0.2324 | 0.361 → 0.334, p = 0.1055 |
| CNN-BiLSTM | F1-optimal | 0.696 → 0.677, **p = 0.0488** | 0.361 → 0.354, p = 0.4961 |
| EEGNet | BA-optimal | 0.709 → 0.707, p = 0.8457 | 0.389 → 0.368, p = 0.3594 |
| EEGNet | F1-optimal | 0.709 → 0.667, **p = 0.0273** | 0.389 → 0.348, p = 0.1641 |

**Arm C**

| Model | Rule | Balanced accuracy | F1 |
|---|---|---|---|
| DeepConvNet | BA-optimal | 0.628 → 0.694, **p = 0.0137** | 0.300 → 0.330, p = 0.3750 |
| DeepConvNet | F1-optimal | 0.628 → 0.661, **p = 0.0059** | 0.300 → 0.342, **p = 0.0273** |
| EEGNet | BA-optimal | 0.718 → 0.712, p = 0.6250 | 0.382 → 0.354, p = 0.1289 |
| EEGNet | F1-optimal | 0.718 → 0.659, **p = 0.0098** | 0.382 → 0.330, p = 0.1641 |
| ShallowConvNet | BA-optimal | 0.694 → 0.690, p = 0.2324 | 0.312 → 0.307, p = 0.4922 |
| ShallowConvNet | F1-optimal | 0.694 → 0.652, **p = 0.0488** | 0.312 → 0.313, p = 1.0000 |

Across the 24 tests: 3 significant gains, 4 significant losses.

**The selected thresholds themselves**

| Arm | Model | F1-optimal threshold | Balanced-accuracy-optimal threshold |
|---|---|---|---|
| A | CNN | 0.4606 ± 0.1626 | 0.0442 ± 0.0336 |
| A | CNN-BiLSTM | 0.6593 ± 0.1410 | 0.2081 ± 0.1255 |
| A | EEGNet | 0.6903 ± 0.0497 | 0.4092 ± 0.0492 |
| C | DeepConvNet | 0.3171 ± 0.0521 | 0.0958 ± 0.0352 |
| C | EEGNet | 0.7210 ± 0.0538 | 0.4192 ± 0.0404 |
| C | ShallowConvNet | 0.8257 ± 0.0581 | 0.4800 ± 0.0862 |

