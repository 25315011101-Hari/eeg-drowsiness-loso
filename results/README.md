# Released result files

Everything here was produced by the code in this repository. Regenerate the
derived files at any time with:

    python run_all.py --from aggregate --result-dir results

## The two tables everything else reads

| File | Rows | What it is |
|---|---|---|
| `ALL_FOLDS.csv` | 750 | one row per (arm, model, seed, subject): the subject-level metrics of a single leave-one-subject-out fold |
| `ALL_POOLED.csv` | 75 | one row per (arm, model, seed): the ten folds of that seed concatenated and scored once |

`ALL_POOLED.csv` carries the false-positive count that was measured directly from
the predictions. It cannot be recovered from `ALL_FOLDS.csv`, because a fold's
predicted-positive total is TP / precision and precision is zero for every
degenerate fold.

## Per-arm post-hoc analyses

| Path | Source |
|---|---|
| `A/calibration_folds.csv`, `A/calibration_summary.csv` | per-fold out-of-subject Platt and isotonic recalibration, three architectures |
| `A/threshold_chosen.csv`, `A/threshold_folds.csv`, `A/threshold_summary.csv` | out-of-subject threshold selection, same three |
| `B/calibration_folds.csv`, `B/calibration_summary.csv` | same, for Arm B's three architectures |
| `A/probs_<model>_seed<n>.npz` | **the per-window scores themselves** — 15 files, 3.2 MB, three architectures x five seeds. Arm A only |
| `A/reproducibility.csv`, `A/reproducibility_agreement.csv` | the Arm A repeated-execution comparison, EEGNet only |
| `B/reproducibility.csv`, `B/reproducibility_agreement.csv` | the Arm B repeated-execution comparison, three architectures |
| `C/calibration_summary.csv`, `C/threshold_summary.csv` | Arm C summaries; the fold-level files did not survive the session that produced them |

Threshold selection was never run on Arm B. This is a gap, not an omission from
the release, and the paper records it as a limitation.

## Derived

| File | Built by |
|---|---|
| `MASTER_NUMBERS.csv` | `src/registry.py` — every value the manuscript may cite |
| `tables.md` | `src/tables.py` — the Results tables, as markdown |
| `pooled_ece.csv` | pooled expected calibration error, kept separate because it is **not** comparable with the subject-averaged column |
| `monotonicity.csv` | `tools/check_monotonicity.py` — what the 150 Arm A calibrators did to the ranking metrics |
| `ranking_invariance.csv` | `tools/check_ranking_invariance.py` — what those calibrators did to the **subject-averaged** ranking metrics, which is what the tables print |
| `raw_window_counts.csv`, `recording_lengths.csv` | measured off the EDF files; Table 1 and the trimming target are verifiable from these |

**What these counts do and do not let you check.** `raw_window_counts.csv` is
untrimmed, so **Arm B is independently verifiable from it**: applying the
proportional rule to those numbers reproduces Arm B's per-subject drowsy counts
exactly, and `src/registry.py` refuses to emit the raw-count rows if it does not.
**Arms A and C are not**, because both are built from trimmed recordings and their
post-trim counts are not in this bundle. Their totals can be checked only by
rebuilding from the original EDF recordings, which are not redistributed here;
`src/preprocess.py` then writes `window_counts_arm_A.csv` and
`window_counts_arm_C.csv` alongside this file. Until someone does that, the Arm A
and Arm C window counts rest on `config.ARMS`, which is where the published figures
came from — stated here rather than left for a reader to discover.
| `LITERATURE_NUMBERS.csv` | every number borrowed from another paper, with the source it was verified against |
| `backup/ALL_FOLDS_armB_run1.csv` | the earlier Arm B execution, retained for the reproducibility check |
| `backup/ALL_FOLDS_armA_run1_EEGNet.csv` | the earlier Arm A EEGNet execution, likewise |

## Released, and what it lets you recompute

**The per-window probability files ARE released, for Arm A.** Fifteen
`probs_<model>_seed<n>.npz` files, 3.2 MB in total, covering CNN, CNN-BiLSTM and
EEGNet at five seeds each. `calibrate.py` and `thresholds.py` recompute from them
directly, and the test suite refits all 150 Arm A calibrators from those scores and
asserts that the published Arm A summary comes back.

> **Corrected 24 September 2026.** This section previously said the probability
> files were "too large to ship" and were not released. They were released, and had
> been for some time; the top-level `README.md` had already been corrected and this
> copy had not. If the two disagree again, measure the directory rather than
> believing either file.

**Not released:** the per-window scores for Arms B and C, which were not retained.
For those two constructions the calibration and threshold analyses are available as
the computed summaries above, and recomputing them from raw scores would mean
re-running training.

**One thing to know before recomputing.** The released Arm A **EEGNet** probability
files come from the earlier of the two Arm A executions described in Section 7.9 of
the paper, not from the run tabulated in `ALL_FOLDS.csv`. Recomputing per-fold
PR-AUC from them gives 0.4317 where `ALL_FOLDS.csv` holds 0.4314, and balanced
accuracy 0.7092 against 0.7084; ROC-AUC agrees to four decimals. CNN and CNN-BiLSTM
match `ALL_FOLDS.csv` exactly. The gap is the run-to-run movement the paper reports,
not an error in either file.
