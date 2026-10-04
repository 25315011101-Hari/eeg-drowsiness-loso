"""Out-of-subject decision-threshold selection.

    python -m src.thresholds --arm C

The alternative to recalibrating the probabilities is to leave them alone and
move the decision threshold instead.  This module fits the threshold the same
way calibrate.py fits its calibrators: on the other nine subjects of the same
seed, never on the subject it is scored on.

Two selection rules, each maximised over config.THRESHOLD_GRID on the
nine-subject set:

  sel-F1   the threshold that maximises F1 out of subject
  sel-BA   the threshold that maximises balanced accuracy out of subject

Each is compared against the fixed 0.5 threshold on the ten subject-level
differences.  Both directions are reported.  A significant drop is as much a
result as a significant gain, and in this study most of the significant changes
are drops.

The spread of the selected threshold across folds is reported alongside, because
it is what separates the cases: a threshold that is stable across subjects
transfers to a new one, and a threshold whose standard deviation is a third of
its own mean does not.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import balanced_accuracy_score, f1_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src.calibrate import iter_prob_files  # noqa: E402

RULES = ("sel-F1", "sel-BA")
FIXED = "fixed0.5"


def grid():
    lo, hi, n = C.THRESHOLD_GRID
    return np.linspace(lo, hi, n)


def sweep(y, p):
    """F1 and balanced accuracy at every grid threshold, in one pass.

    Counting is done with two sorted searches instead of 197 relabellings of the
    whole array, which is what makes the out-of-subject fit affordable: it runs
    150 times per arm on roughly 8,300 windows each.  `test_sweep_matches_the
    _direct_computation` asserts it agrees with sklearn to floating-point noise,
    so this is a speed change and not a method change.
    """
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    g = grid()
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos

    pos_sorted = np.sort(p[y == 1])
    all_sorted = np.sort(p)
    # predicted positive means p >= t, so count the tail at or above each t
    tp = len(pos_sorted) - np.searchsorted(pos_sorted, g, side="left")
    pp = len(all_sorted) - np.searchsorted(all_sorted, g, side="left")
    fp = pp - tp
    fn = n_pos - tp
    tn = n_neg - fp

    with np.errstate(divide="ignore", invalid="ignore"):
        denom = 2 * tp + fp + fn
        f1 = np.where(denom > 0, 2 * tp / np.where(denom > 0, denom, 1), 0.0)
        recall = tp / n_pos if n_pos else np.zeros_like(tp, dtype=float)
        specificity = tn / n_neg if n_neg else np.zeros_like(tn, dtype=float)
    ba = 0.5 * (recall + specificity)
    return g, f1, ba


def best_threshold(y, p, metric):
    """The grid point maximising a metric. Ties go to the lowest threshold."""
    g, f1, ba = sweep(y, p)
    if metric == "f1":
        scores = f1
    elif metric == "bal_acc":
        scores = ba
    else:
        raise ValueError("unknown metric %r" % (metric,))
    return float(g[int(np.argmax(scores))])


def score_at(y, p, t):
    pred = (np.asarray(p) >= t).astype(int)
    return (balanced_accuracy_score(y, pred), f1_score(y, pred, zero_division=0))


def thresholds_arm(arm, result_dir=None, verbose=True):
    """Per-fold threshold selection for every architecture with probability files."""
    result_dir = result_dir or C.RESULT_DIR
    chosen, scored = [], []
    files = list(iter_prob_files(result_dir, arm))
    if not files:
        raise FileNotFoundError("no probs_*.npz under %s" % os.path.join(result_dir, arm))

    for name, seed, path in files:
        d = np.load(path, allow_pickle=True)
        y = d["y_true"].astype(int)
        p = d["y_prob"].astype(float)
        g = np.asarray([str(s) for s in d["subject"]])

        for s in C.SUBJECTS:
            te = g == s
            y_out, p_out = y[~te], p[~te]
            y_in, p_in = y[te], p[te]
            t_f1 = best_threshold(y_out, p_out, "f1")
            t_ba = best_threshold(y_out, p_out, "bal_acc")
            chosen.append(dict(arm=arm, model=name, seed=seed, subject=s,
                               t_f1=t_f1, t_ba=t_ba))
            for rule, t in ((FIXED, C.FIXED_THRESHOLD), ("sel-F1", t_f1), ("sel-BA", t_ba)):
                ba, f1 = score_at(y_in, p_in, t)
                scored.append(dict(arm=arm, model=name, seed=seed, subject=s,
                                   rule=rule, threshold=t, bal_acc=ba, f1=f1))
        if verbose:
            print("  thresholds %s seed %d" % (name, seed), flush=True)

    return pd.DataFrame(chosen), pd.DataFrame(scored)


def summarise(chosen, scored, arm):
    """One row per architecture and rule, with both paired tests against fixed 0.5."""
    out = []
    for model in sorted(scored.model.unique()):
        thr = chosen[chosen.model == model]
        base = (scored[(scored.model == model) & (scored.rule == FIXED)]
                .groupby("subject")[["bal_acc", "f1"]].mean().loc[C.SUBJECTS])
        for rule in RULES:
            sel = (scored[(scored.model == model) & (scored.rule == rule)]
                   .groupby("subject")[["bal_acc", "f1"]].mean().loc[C.SUBJECTS])
            out.append(dict(
                arm=arm, model=model, rule=rule,
                ba_fixed=base.bal_acc.mean(), ba_sel=sel.bal_acc.mean(),
                p_ba=wilcoxon(sel.bal_acc, base.bal_acc).pvalue,
                f1_fixed=base.f1.mean(), f1_sel=sel.f1.mean(),
                p_f1=wilcoxon(sel.f1, base.f1).pvalue,
                thr_f1_mean=thr.t_f1.mean(), thr_f1_sd=thr.t_f1.std(ddof=1),
                thr_ba_mean=thr.t_ba.mean(), thr_ba_sd=thr.t_ba.std(ddof=1)))
    return pd.DataFrame(out)


def classify(row, alpha=0.05):
    """Label each test a gain, a loss or no change. Direction matters, so it is explicit."""
    verdict = {}
    for metric, p in (("bal_acc", row.p_ba), ("f1", row.p_f1)):
        fixed = row.ba_fixed if metric == "bal_acc" else row.f1_fixed
        sel = row.ba_sel if metric == "bal_acc" else row.f1_sel
        if p < alpha:
            verdict[metric] = "gain" if sel > fixed else "loss"
        else:
            verdict[metric] = "none"
    return verdict


def report(summary, arm):
    print("\nArm %s   threshold selection against the fixed %.1f threshold"
          % (arm, C.FIXED_THRESHOLD))
    gains = losses = 0
    for _, r in summary.iterrows():
        v = classify(r)
        gains += sum(x == "gain" for x in v.values())
        losses += sum(x == "loss" for x in v.values())
        print("  %-16s %-7s BA %.3f->%.3f p=%.4f [%s] | F1 %.3f->%.3f p=%.4f [%s]"
              % (r.model, r.rule, r.ba_fixed, r.ba_sel, r.p_ba, v["bal_acc"],
                 r.f1_fixed, r.f1_sel, r.p_f1, v["f1"]))
    print("  %d tests: %d significant gains, %d significant losses"
          % (2 * len(summary), gains, losses))
    print("  selected thresholds, mean +/- SD over the fifty folds")
    for model in summary.model.unique():
        r = summary[summary.model == model].iloc[0]
        print("    %-16s F1-optimal %.4f +/- %.4f | BA-optimal %.4f +/- %.4f"
              % (model, r.thr_f1_mean, r.thr_f1_sd, r.thr_ba_mean, r.thr_ba_sd))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", action="append", choices=sorted(C.ARMS))
    ap.add_argument("--result-dir", default=None)
    a = ap.parse_args(argv)
    result_dir = a.result_dir or C.RESULT_DIR

    arms = a.arm or [x for x in sorted(C.ARMS) if list(iter_prob_files(result_dir, x))]
    if not arms:
        print("no probability files found under", result_dir)
        return 1

    for arm in arms:
        chosen, scored = thresholds_arm(arm, result_dir)
        summary = summarise(chosen, scored, arm)
        out = os.path.join(result_dir, arm)
        chosen.to_csv(os.path.join(out, "threshold_chosen.csv"), index=False)
        scored.to_csv(os.path.join(out, "threshold_folds.csv"), index=False)
        summary.to_csv(os.path.join(out, "threshold_summary.csv"), index=False)
        report(summary, arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
