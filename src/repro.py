"""Compare two executions of the same arm under identical settings.

    python -m src.repro --arm B --run1 results/backup/ALL_FOLDS_armB_run1.csv

Arm B was executed twice, several hours apart, with the same preprocessing, the
same seeds and the same validation-subject assignments.  The two runs differ only
in GPU non-determinism.  This module quantifies what that alone does.

Why it is in the paper at all: for two of the three architectures checked, the
spread between two identical runs is comparable to -- and for F1 larger than --
the standard deviation reported over five seeds.  Those five seeds share a single
execution, so that standard deviation **understates** the true run-to-run
uncertainty.  Reporting the seed SD without this check would present a lower
bound as if it were the whole of the variation.

The first thing checked is that the two runs really are comparable. If both files
record their validation-subject assignments and those assignments differ anywhere,
the runs are not a reproducibility test and the comparison is refused. If one file
does not record them at all, the comparison proceeds but is marked
`validation_pairs_identical = False`, because an unverifiable claim is not the same
as a verified one: the difference between such runs cannot be attributed to GPU
non-determinism alone, and the report says so.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src import aggregate  # noqa: E402

KEY = ["model", "seed", "subject"]


def agreement(run1, run2, arm, cols=("bal_acc", "f1", "recall")):
    """How many folds agree to full precision on each threshold-dependent metric.

    Reported separately from `compare` because the two answer different questions:
    `compare` asks how far a fold moved, this asks how many did not move at all.
    """
    a = run1[run1.arm == C.ARMS[arm]["key"]] if "arm" in run1.columns else run1
    b = run2[run2.ar == arm] if "ar" in run2.columns else run2
    merged = a.merge(b, on=KEY, suffixes=("_1", "_2"))
    out = []
    for model, g in merged.groupby("model"):
        row = dict(arm=arm, model=model, n_folds=len(g))
        for col in cols:
            d = (g["%s_1" % col] - g["%s_2" % col]).abs()
            row["identical_%s" % col] = int((d <= 1e-12).sum())
        for col in ("auc", "pr_auc", "bal_acc"):
            row["mean_1_%s" % col] = float(g["%s_1" % col].mean())
            row["mean_2_%s" % col] = float(g["%s_2" % col].mean())
        out.append(row)
    return pd.DataFrame(out)


def compare(run1, run2, arm, col="auc", tol=1e-12):
    """Fold-by-fold comparison of two runs of the same arm.

    Two counts are reported, because "identical" needs a definition.
    `folds_identical` counts folds agreeing to within `tol`, which is what
    "identical to full floating-point precision" means here; `folds_bit_identical`
    counts exact equality of the stored values. On this data the two differ by
    two folds for EEGNet, so the looser count is the one quoted and the stricter
    one is kept beside it.
    """
    a = run1[run1.arm == C.ARMS[arm]["key"]] if "arm" in run1.columns else run1
    b = run2[run2.ar == arm] if "ar" in run2.columns else run2

    merged = a.merge(b, on=KEY, suffixes=("_1", "_2"))
    if merged.empty:
        raise ValueError("the two runs share no (model, seed, subject) folds")

    pairs_known = ("val_subs_1" in merged.columns and "val_subs_2" in merged.columns
                   and merged.val_subs_1.notna().all() and merged.val_subs_2.notna().all())
    if pairs_known:
        differing = int((merged.val_subs_1 != merged.val_subs_2).sum())
        if differing:
            raise ValueError(
                "%d of %d folds were given different validation subjects in the two "
                "runs; they are not a reproducibility comparison"
                % (differing, len(merged)))

    out = []
    for model, g in merged.groupby("model"):
        d = (g["%s_1" % col] - g["%s_2" % col]).abs()
        out.append(dict(
            arm=arm, model=model, metric=col, n_folds=len(g),
            mean_1=float(g["%s_1" % col].mean()),
            mean_2=float(g["%s_2" % col].mean()),
            largest_fold_difference=float(d.max()),
            folds_identical=int((d <= tol).sum()),
            folds_bit_identical=int((d == 0).sum()),
            validation_pairs_identical=bool(pairs_known),
        ))
    return pd.DataFrame(out).sort_values("largest_fold_difference").reset_index(drop=True)


def subject_shift(run1, run2, arm, cols=("auc", "f1")):
    """Largest movement of a subject-level mean between the two runs.

    This is the quantity to compare against the reported seed SD, because the
    subject-level mean is what the paper's tables average.
    """
    a = run1[run1.arm == C.ARMS[arm]["key"]] if "arm" in run1.columns else run1
    b = run2[run2.ar == arm] if "ar" in run2.columns else run2
    out = []
    for model in sorted(set(a.model) & set(b.model)):
        row = dict(arm=arm, model=model)
        for col in cols:
            x = a[a.model == model].groupby("subject")[col].mean()
            y = b[b.model == model].groupby("subject")[col].mean()
            common = x.index.intersection(y.index)
            row["max_subject_shift_%s" % col] = float((x[common] - y[common]).abs().max())
            row["overall_shift_%s" % col] = float(abs(
                a[a.model == model][col].mean() - b[b.model == model][col].mean()))
            seed_sd = b[b.model == model].groupby("seed")[col].mean().std(ddof=1)
            row["seed_sd_%s" % col] = float(seed_sd)
        out.append(row)
    return pd.DataFrame(out)


def report(cmp_df, shift_df):
    print("\nrepeated execution, identical settings, GPU non-determinism only")
    print("%-16s %-21s %-12s %s" % ("model", "mean ROC-AUC 1 / 2",
                                    "largest fold", "identical (bit-identical)"))
    for r in cmp_df.itertuples():
        print("%-16s %.4f / %.4f       %.4f       %d / %d  (%d)"
              % (r.model, r.mean_1, r.mean_2, r.largest_fold_difference,
                 r.folds_identical, r.n_folds, r.folds_bit_identical))
    print("\nmovement between the two runs, against the reported seed SD")
    print("  (the overall shift is the mean over all folds; the subject shift is the")
    print("   largest movement of a single subject's mean, which is what the tables average)")
    for r in shift_df.itertuples():
        print("  %-16s ROC-AUC overall %.4f, subject %.4f (seed SD %.4f)"
              % (r.model, r.overall_shift_auc, r.max_subject_shift_auc, r.seed_sd_auc))
        print("  %-16s F1      overall %.4f, subject %.4f (seed SD %.4f)"
              % ("", r.overall_shift_f1, r.max_subject_shift_f1, r.seed_sd_f1))
    if not bool(cmp_df.validation_pairs_identical.all()):
        print("\n  VALIDATION PAIRS NOT VERIFIED: one of the two runs did not record")
        print("  its validation-subject assignments, so the two runs cannot be shown to")
        print("  have drawn the same pairs. The differences below are an upper bound on")
        print("  GPU non-determinism, not a measurement of it.")
    untouched = cmp_df[cmp_df.folds_bit_identical == cmp_df.n_folds]
    if len(untouched):
        print("\n  NOT RE-EXECUTED: %s. Every fold is bit-identical, which means these"
              % ", ".join(sorted(untouched.model)))
        print("  rows were carried over rather than run again. They are excluded from")
        print("  the comparison below and the paper reports the check as covering only")
        print("  the architectures that were genuinely re-run.")
    real = cmp_df[cmp_df.folds_bit_identical < cmp_df.n_folds]
    if real.empty:
        print("\n  no architecture was actually re-executed; nothing to conclude")
        return
    best, worst = real.iloc[0], real.iloc[-1]
    print("\n  Of the %d architectures re-executed, %s is reproducible to %d decimal "
          "places" % (len(real), best.model,
                      int(-np.floor(np.log10(max(best.largest_fold_difference, 1e-12))))))
    print("  and %s moves a single fold by %.4f. For every architecture except %s the"
          % (worst.model, worst.largest_fold_difference, best.model))
    print("  reported seed SD is a lower bound on run-to-run uncertainty.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True, choices=sorted(C.ARMS))
    ap.add_argument("--run1", required=True, help="the earlier run's fold table")
    ap.add_argument("--result-dir", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    result_dir = a.result_dir or C.RESULT_DIR
    run2, _ = aggregate.load(result_dir)
    run1 = pd.read_csv(a.run1)

    cmp_df = compare(run1, run2, a.arm)
    shift_df = subject_shift(run1, run2, a.arm)
    report(cmp_df, shift_df)

    out = a.out or os.path.join(result_dir, a.arm, "reproducibility.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmp_df.merge(shift_df, on=["arm", "model"]).to_csv(out, index=False)
    agr = agreement(run1, run2, a.arm)
    agr_path = os.path.join(os.path.dirname(out), "reproducibility_agreement.csv")
    agr.to_csv(agr_path, index=False)
    print("\nwrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
