"""Every inferential comparison this study performs, and what correction does to it.

    python -m src.multiplicity

Writes results/MULTIPLICITY.csv: one row per analysis family, plus three summary
rows, giving the number of comparisons, how many reach the nominal level, and how
many survive Benjamini-Hochberg and Benjamini-Yekutieli within that family.

Why this file exists. The study reported 190 inferential comparisons and never named
a significance level, never mentioned multiplicity, and never corrected for it. Three
different counts of "how many tests" were in circulation -- 175-181, 117, 163 -- none
of which counted the same thing. This module settles it by enumeration: it runs every
family and counts what comes back, so the denominator is measured rather than argued.

The count is 190 and not 193 because three comparisons are performed twice under two
names. `all_pairwise` tests CNN against CNN-BiLSTM on ROC-AUC as one of its ten pairs,
and `ablation` tests the same pair on the same metric as one of its four. Same
subjects, same metric, same test. They are counted once, in the architecture-pair
family, and the ablation family here carries only its other three metrics.

On the choice of procedures. Holm is not offered. Its first threshold is ALPHA / m,
and a Wilcoxon signed-rank test on ten subjects cannot return a p below 1/512, so in
any family of 26 or more such tests Holm rejects nothing for any dataset that could
have been collected -- see config.holm_family_ceiling. BH and BY are both reported
because they need different assumptions: BH controls the false discovery rate under
independence or positive regression dependency, BY under arbitrary dependence. The
comparisons here share subjects, share folds, overlap in architecture pairs, and use
four metrics computed from the same predictions, so positive dependency is plausible
but is not established. Reporting only BH would leave that unanswered.

Neither is the paper's decision rule. Both are sensitivity analyses against a primary
analysis that is exploratory, which is what a ten-subject design supports.
"""

import argparse
import glob
import itertools
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src import aggregate, stats  # noqa: E402

ARM_ORDER = ["A", "B", "C"]

# The family whose 45 comparisons are reported separately everywhere. It supplies 32
# of the 82 nominal results and every one of the survivors of a one-family BY, and
# what it measures -- that PR-AUC rises with a subject's event count -- is close to a
# property of the metric, which is why the paper also reports the prevalence-corrected
# form. Merged into a single total it makes the other families unreadable.
PREVALENCE_FAMILY = "drowsy count vs PR-AUC"


def bh(pvalues, alpha=None):
    """Benjamini-Hochberg: how many hypotheses are rejected at this level.

    Valid under independence or positive regression dependency.
    """
    alpha = C.ALPHA if alpha is None else alpha
    ordered = sorted(float(p) for p in pvalues)
    m = len(ordered)
    for i in range(m - 1, -1, -1):
        if ordered[i] <= alpha * (i + 1) / m:
            return i + 1
    return 0


def by(pvalues, alpha=None):
    """Benjamini-Yekutieli: the same step-up under ARBITRARY dependence.

    The threshold carries an extra 1/H(m), the m-th harmonic number, which is the
    price of not having to assume anything about how the tests depend on one another.
    """
    alpha = C.ALPHA if alpha is None else alpha
    ordered = sorted(float(p) for p in pvalues)
    m = len(ordered)
    harmonic = sum(1.0 / k for k in range(1, m + 1))
    for i in range(m - 1, -1, -1):
        if ordered[i] <= alpha * (i + 1) / (m * harmonic):
            return i + 1
    return 0


def nominal(pvalues, alpha=None):
    alpha = C.ALPHA if alpha is None else alpha
    return sum(1 for p in pvalues if float(p) < alpha)


def _summary_csv(result_dir, pattern, columns):
    """Collect one column of p-values from each released per-arm summary file."""
    out = []
    for path in sorted(glob.glob(os.path.join(result_dir, "*", pattern))):
        frame = pd.read_csv(path)
        for column in columns:
            if column in frame.columns:
                out += [float(v) for v in frame[column].dropna()]
    return out


def families(folds, pooled, result_dir=None):
    """Every inferential comparison the study performs, grouped by the question asked.

    Returns an ordered dict of family name -> list of p-values. The order is the order
    the manuscript presents them in, so the table reads alongside the Results section.
    """
    result_dir = result_dir or C.RESULT_DIR
    out = {}

    pairs = {a: stats.all_pairwise(folds, a, "auc") for a in ARM_ORDER}
    out["EEGNet pairs, ROC-AUC"] = [
        r.p for a in ARM_ORDER for r in pairs[a].itertuples()
        if "EEGNet" in (r.a, r.b)]
    out["other architecture pairs, ROC-AUC"] = [
        r.p for a in ARM_ORDER for r in pairs[a].itertuples()
        if "EEGNet" not in (r.a, r.b)]
    # ROC-AUC excluded: that comparison is already one of the ten pairs above.
    out["ablation, CNN against CNN-BiLSTM"] = [
        r.p for a in ARM_ORDER for r in stats.ablation(folds, a).itertuples()
        if r.metric != "auc"]

    for x, y, factor in (("A", "C", "balancing"), ("B", "C", "trimming")):
        out["arm %s against arm %s, %s isolated" % (x, y, factor)] = [
            r.p for col in ("auc", "pr_auc", "bal_acc", "f1")
            for r in stats.arm_contrast(folds, x, y, col).itertuples()]

    out["recalibration, Platt against raw"] = _summary_csv(
        result_dir, "calibration_summary.csv", ("p_brier", "p_ece"))
    out["threshold selection against 0.5"] = _summary_csv(
        result_dir, "threshold_summary.csv", ("p_ba", "p_f1"))

    out["parameter count against ROC-AUC"] = [
        stats.capacity_correlation(folds, a)["p"] for a in ARM_ORDER]
    out["cross-arm ordering agreement"] = [
        r.p for col in ("auc", "pr_auc", "bal_acc", "f1")
        for r in stats.cross_arm_ordering(folds, col).itertuples()]
    ranking = []
    for a in ARM_ORDER:
        both = stats.ranking_vs_reliability(folds, pooled, a)
        ranking += [both[k][1] for k in sorted(both)]
    out["ROC-AUC against pooled Brier"] = ranking
    out["accuracy against pooled recall"] = [
        stats.accuracy_vs_recall(folds, a, pooled)["p"] for a in ARM_ORDER]

    out[PREVALENCE_FAMILY] = [
        p for a in ARM_ORDER
        for r in stats.subject_count_correlation(folds, a).itertuples()
        for p in (r.p_raw, r.p_lift, r.p_ratio)]

    return out


def table(folds, pooled, result_dir=None, alpha=None):
    """One row per family, then the three rows the manuscript quotes."""
    alpha = C.ALPHA if alpha is None else alpha
    fam = families(folds, pooled, result_dir)
    rows = []
    for name, ps in fam.items():
        rows.append(dict(scope="family", name=name, n_tests=len(ps),
                         n_nominal=nominal(ps, alpha), n_bh=bh(ps, alpha),
                         n_by=by(ps, alpha), alpha=alpha))

    everything = [p for ps in fam.values() for p in ps]
    prevalence = list(fam[PREVALENCE_FAMILY])
    remaining = [p for name, ps in fam.items() if name != PREVALENCE_FAMILY
                 for p in ps]
    for label, ps in (("all registered comparisons", everything),
                      ("drowsy-count / prevalence family", prevalence),
                      ("remaining comparisons", remaining)):
        rows.append(dict(scope="summary", name=label, n_tests=len(ps),
                         n_nominal=nominal(ps, alpha), n_bh=bh(ps, alpha),
                         n_by=by(ps, alpha), alpha=alpha))
    return pd.DataFrame(rows)


def build(result_dir=None, out_path=None, verbose=True):
    result_dir = result_dir or C.RESULT_DIR
    out_path = out_path or os.path.join(result_dir, "MULTIPLICITY.csv")
    folds, pooled = aggregate.load(result_dir)
    frame = table(folds, pooled, result_dir)
    frame.to_csv(out_path, index=False)
    if verbose:
        print("wrote %s: %d row(s)" % (out_path, len(frame)))
        total = frame[frame.scope == "summary"]
        total = total[total.name == "all registered comparisons"].iloc[0]
        print("  %d comparison(s), %d at nominal p < %g, %d survive BH, %d survive BY"
              % (total.n_tests, total.n_nominal, total.alpha, total.n_bh, total.n_by))
    return frame


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--result-dir", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    frame = build(a.result_dir, a.out)
    print()
    print(frame.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
