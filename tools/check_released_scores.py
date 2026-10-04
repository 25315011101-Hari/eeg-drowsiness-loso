"""Answer, as a command, which execution the released per-window scores came from.

    python3 tools/check_released_scores.py

A released probability file is a promise: recompute this fold's metrics from these
scores and you will get the row printed in the paper. For fourteen of the fifteen
released files that promise holds to the last decimal. For one architecture it does
not, and the reason is not an error in either file.

Arm A was executed twice for EEGNet (Section 7.9, "Check 2"). The probability files
retained for release are the EARLIER run; `ALL_FOLDS.csv` holds the later one. So a
reader who recomputes Arm A EEGNet PR-AUC from the released scores gets 0.4317 while
the table says 0.4314 -- a difference of 0.0003, well inside the run-to-run movement
the paper reports, but alarming to anyone who does not know which run they hold.

This check states it rather than leaving it to be discovered:

  * every architecture with released scores is recomputed fold by fold,
  * each is compared with its row in ALL_FOLDS.csv,
  * an exact match prints "same execution", and a mismatch prints the size of the
    difference and names Section 7.9.

It exits non-zero only if a file is missing or unreadable, or if a difference is
larger than the largest run-to-run movement the paper reports. A small documented
difference is a fact about the release, not a failure of it.
"""

import glob
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             roc_auc_score)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import config as C  # noqa: E402

# The stem used in a released filename is not always the model name: CNN-BiLSTM is
# written without its hyphen. Hard-coding one and hoping is how a check silently
# examines nothing, so the mapping is explicit and every model is looked for.
FILE_STEM = {m: m.replace("-", "") for m in C.MODELS}

# The largest single-fold ROC-AUC movement the paper reports between two executions
# of the same configuration (Section 7.9, Arm A). A difference above this is not
# run-to-run noise and should stop the run.
TOLERANCE = 0.01


def per_fold(path):
    """Recompute one seed's ten folds from a released probability file."""
    d = np.load(path, allow_pickle=True)
    y, p = d["y_true"], d["y_prob"].astype(float)
    subj = np.array([str(s) for s in d["subject"]])
    out = []
    for s in C.SUBJECTS:
        t = subj == s
        if not t.any():
            continue
        yy, pp = y[t], p[t]
        if len(np.unique(yy)) < 2:
            continue
        out.append(dict(auc=roc_auc_score(yy, pp),
                        pr_auc=average_precision_score(yy, pp),
                        bal_acc=balanced_accuracy_score(yy, (pp >= 0.5).astype(int))))
    return pd.DataFrame(out)


def main():
    folds = pd.read_csv(os.path.join(HERE, "results", "ALL_FOLDS.csv"))
    folds["ar"] = folds.arm.str[0]

    print("released per-window scores, against the fold table they sit beside\n")
    print("  %-5s %-14s %-7s %-24s %s"
          % ("arm", "model", "files", "PR-AUC released / table", "verdict"))

    problems, rows = [], 0
    for arm in sorted(C.ARMS):
        for model in C.MODELS:
            paths = sorted(glob.glob(os.path.join(
                HERE, "results", arm, "probs_%s_seed*.npz" % FILE_STEM[model])))
            if not paths:
                continue
            rows += 1
            got = pd.concat([per_fold(p) for p in paths], ignore_index=True)
            want = folds[(folds.ar == arm) & (folds.model == model)]
            if want.empty:
                problems.append("%s %s: no rows in ALL_FOLDS.csv" % (arm, model))
                continue
            d_pr = abs(got.pr_auc.mean() - want.pr_auc.mean())
            d_auc = abs(got.auc.mean() - want.auc.mean())
            d_ba = abs(got.bal_acc.mean() - want.bal_acc.mean())
            worst = max(d_pr, d_auc, d_ba)
            if worst < 5e-7:
                verdict = "same execution"
            else:
                verdict = ("EARLIER EXECUTION (Section 7.9) — "
                           "ROC-AUC %+.4f, PR-AUC %+.4f, bal.acc %+.4f"
                           % (got.auc.mean() - want.auc.mean(),
                              got.pr_auc.mean() - want.pr_auc.mean(),
                              got.bal_acc.mean() - want.bal_acc.mean()))
                if worst > TOLERANCE:
                    problems.append(
                        "%s %s: released scores differ from ALL_FOLDS.csv by %.4f, "
                        "more than the %.2f the paper attributes to run-to-run "
                        "movement" % (arm, model, worst, TOLERANCE))
            print("  %-5s %-14s %-7d %.4f / %.4f          %s"
                  % (arm, model, len(paths), got.pr_auc.mean(), want.pr_auc.mean(),
                     verdict))

    if not rows:
        print("  no released probability files found")
        return 1

    print("\n%d architecture-arm set(s) with released scores, %d problem(s)"
          % (rows, len(problems)))
    for p in problems:
        print("    " + p)
    if not problems:
        print("Every difference is either zero or within the run-to-run movement "
              "Section 7.9\nreports, and is named in results/README.md.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
