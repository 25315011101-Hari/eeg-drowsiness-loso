"""Every statistical quantity the paper reports, computed from ALL_FOLDS.csv
and ALL_POOLED.csv and from nothing else.

Two conventions are kept strictly apart and every function says which it uses.

  subject-averaged   computed inside a fold, then averaged over the ten
                     subjects with equal weight.  This is the default, because
                     every significance test here is a paired test on ten
                     subject-level differences and because equal weighting is
                     what leave-one-subject-out is for.
  pooled             the ten folds of one seed are concatenated and scored once,
                     which weights each subject by its window count.  Used only
                     where the quantity is intrinsically pooled: the confusion
                     matrices and the Brier scores.

Pooled recall exceeds subject-averaged recall by 0.13 to 0.25 for every
architecture on every arm, so mixing them silently would be a large error.  No
function here returns a mixture.

Testing rules, applied without exception:

  * paired tests use the ten subject-level differences, never the fifty folds,
    because folds from the same subject are not independent.  The smallest
    p-value this can return is config.P_FLOOR_WILCOXON_10 = 0.00195.
  * correlations across architectures use five points, where the smallest
    attainable p-value is about config.P_FLOOR_SPEARMAN_5 = 0.017.  A result
    near that floor is reported with the floor beside it.
"""

import itertools
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

METRICS = ("auc", "pr_auc", "bal_acc", "f1", "precision", "recall")

# Enumerating n! orderings is exact and costs nothing up to about eight points.
# Ten points is 3,628,800 orderings, which is still tractable but is recomputed
# forty-five times during a registry build, so above this threshold the
# t-approximation is used and the fact is recorded on the result.
EXACT_SPEARMAN_MAX_N = 8
_EXACT_NULL = {}


def _spearman_null(n):
    """Every value Spearman's rho can take on n untied ranks, once per ordering.

    rho = 1 - 6 * sum(d^2) / (n^3 - n), so the whole null distribution follows
    from the sum of squared rank differences and needs no correlation routine.
    Cached, because a registry build asks for n = 5 several dozen times.
    """
    if n not in _EXACT_NULL:
        base = np.arange(n)
        d2 = np.fromiter(
            (((base - np.asarray(p)) ** 2).sum()
             for p in itertools.permutations(range(n))),
            dtype=np.int64, count=math.factorial(n))
        _EXACT_NULL[n] = 1.0 - 6.0 * d2 / (n * (n * n - 1))
    return _EXACT_NULL[n]


def spearman(x, y):
    """Spearman's rho, with an EXACT two-sided p-value on small samples.

    Why this exists rather than a bare call to scipy.  `scipy.stats.spearmanr`
    returns a p-value from the t-approximation

        t = rho * sqrt((n - 2) / (1 - rho^2))     on n - 2 degrees of freedom

    which is asymptotic.  Across the five architectures this paper correlates,
    n = 5, and the approximation is not merely imprecise there -- it returns
    values that cannot exist.  There are 120 orderings of five ranks, so the
    smallest two-sided p obtainable is 2/120 = 0.0167, yet the approximation
    reported 0.0374 for rho = -0.900 and exactly 0.0000 for rho = 1.000, the
    latter a division by zero rather than a probability.

    Section 6.5 of the manuscript already states the 0.0167 floor.  Reporting a
    p below a floor the Methods section declares is a contradiction, so the
    p-value is now obtained the way the floor implies: by counting the orderings
    at least as extreme as the observed one.

    Returns (rho, p, exact) where `exact` says which route produced the p, so a
    caller can record it rather than a reader having to guess.
    """
    r = spearmanr(x, y)
    rho = float(r.statistic)
    n = len(x)
    if n > EXACT_SPEARMAN_MAX_N or not np.isfinite(rho):
        return rho, float(r.pvalue), False
    null = _spearman_null(n)
    return rho, float((np.abs(null) >= abs(rho) - 1e-9).mean()), True


# ---------------------------------------------------------------- selectors
def rows(folds, arm, model=None):
    d = folds[folds.ar == arm]
    return d if model is None else d[d.model == model]


def subject_means(folds, arm, model, col):
    """One value per subject, averaged over the five seeds. Index order S1..S10."""
    s = rows(folds, arm, model).groupby("subject")[col].mean()
    return s.reindex(C.SUBJECTS)


def seed_means(folds, arm, model, col):
    """One value per seed, each the mean over the ten subjects."""
    return rows(folds, arm, model).groupby("seed")[col].mean()


def subject_averaged(folds, arm, model, col):
    """(mean, SD across the five seed-level means). The paper's default estimator."""
    per = seed_means(folds, arm, model, col)
    return float(per.mean()), float(per.std(ddof=1))


def pooled_row(pooled, arm, model):
    """(mean, SD) for each pooled metric of one architecture on one arm."""
    d = pooled[(pooled.ar == arm) & (pooled.model == model)]
    return {c: (float(d[c].mean()), float(d[c].std(ddof=1)))
            for c in ("auc", "pr_auc", "bal_acc", "brier") if c in d.columns}


# ---------------------------------------------------------------- paired tests
def paired(folds, arm, model_a, model_b, col):
    """Wilcoxon on the ten subject-level differences, a against b.

    `ties` and `n_effective` are not decoration. scipy discards zero differences,
    so a tied subject makes this a test on nine pairs whose smallest attainable
    two-sided p is 2/2**9, twice the ten-pair floor the methods section quotes.
    Thirteen of the comparisons in this study have a tie and one has two, so a
    caller that assumes ten pairs will quote the wrong floor for those.

    `b_wins` is counted strictly, like `a_wins`. Deriving it as n - a_wins counts
    a tie as a win for b, which is how one registry row came to say 10/10 improved
    where the manuscript correctly said 9/10.
    """
    a = subject_means(folds, arm, model_a, col)
    b = subject_means(folds, arm, model_b, col)
    ties = int((a == b).sum())
    return dict(arm=arm, a=model_a, b=model_b, metric=col,
                mean_a=float(a.mean()), mean_b=float(b.mean()),
                p=float(wilcoxon(a, b).pvalue),
                a_wins=int((a > b).sum()), b_wins=int((b > a).sum()),
                ties=ties, n=len(a), n_effective=len(a) - ties,
                p_floor=2.0 / 2 ** (len(a) - ties))


def all_pairwise(folds, arm, col="auc"):
    """All ten pairs on one arm, so that the ordering claim can be checked."""
    return pd.DataFrame([paired(folds, arm, x, y, col)
                         for x, y in itertools.combinations(C.MODELS, 2)])


def best_model_comparisons(folds, arm, best="EEGNet", col="auc"):
    return pd.DataFrame([paired(folds, arm, best, m, col)
                         for m in C.MODELS if m != best])


def ablation(folds, arm, base="CNN", variant="CNN-BiLSTM"):
    """The one controlled architectural comparison: identical trunk, one component."""
    return pd.DataFrame([paired(folds, arm, base, variant, c)
                         for c in ("auc", "pr_auc", "bal_acc", "f1")])


def arm_contrast(folds, arm_a, arm_b, col="auc"):
    """The same architecture on two arms, paired by subject.

    Arms A and C share their trimming and differ only in balancing, so this
    isolates that one factor.  No pair involving arm B isolates anything.
    """
    out = []
    for m in C.MODELS:
        x = subject_means(folds, arm_a, m, col)
        y = subject_means(folds, arm_b, m, col)
        ties = int((x == y).sum())
        out.append(dict(model=m, metric=col, arm_a=arm_a, arm_b=arm_b,
                        mean_a=float(x.mean()), mean_b=float(y.mean()),
                        delta=float(y.mean() - x.mean()),
                        p=float(wilcoxon(x, y).pvalue),
                        b_higher=int((y > x).sum()),
                        a_higher=int((x > y).sum()),
                        # Eight of these forty contrasts tie on at least one subject
                        # and one ties on three, so the attainable floor is not the
                        # ten-pair one for them. Carried here rather than assumed.
                        ties=ties, n=len(x), n_effective=len(x) - ties,
                        p_floor=2.0 / 2 ** (len(x) - ties)))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- correlations
def capacity_correlation(folds, arm, col="auc"):
    """Parameter count against ranking quality, across the five architectures."""
    values = [subject_averaged(folds, arm, m, col)[0] for m in C.MODELS]
    params = [C.PARAMS[m] for m in C.MODELS]
    rho, p, exact = spearman(params, values)
    return dict(arm=arm, metric=col, rho=rho, p=p, exact=exact,
                p_floor=C.P_FLOOR_SPEARMAN_5,
                order=[m for _, m in sorted(zip(values, C.MODELS), reverse=True)])


def cross_arm_ordering(folds, col="auc"):
    """Do the arms order the five architectures the same way?"""
    out = []
    for a, b in itertools.combinations(sorted(C.ARMS), 2):
        x = [subject_averaged(folds, a, m, col)[0] for m in C.MODELS]
        y = [subject_averaged(folds, b, m, col)[0] for m in C.MODELS]
        rho, p, exact = spearman(x, y)
        out.append(dict(metric=col, arm_a=a, arm_b=b,
                        rho=rho, p=p, exact=exact))
    return pd.DataFrame(out)


def subject_count_correlation(folds, arm):
    """Does a subject's drowsy-window count predict its PR-AUC?

    Three forms, because they do not agree and reporting only one would be
    selective:

      raw     count against PR-AUC
      lift    count against PR-AUC minus the subject's own prevalence, which is
              the chance level of PR-AUC.  This is the form the paper uses.
      ratio   count against PR-AUC divided by prevalence, the multiple of
              chance.  It has the opposite sign, because the denominator grows
              faster than the numerator.
    """
    n_per_subject = C.ARMS[arm]["n_per_subject"]
    out = []
    for m in C.MODELS:
        d = rows(folds, arm, m).groupby("subject")[["pr_auc", "n_drowsy"]].mean()
        d = d.reindex(C.SUBJECTS)
        prevalence = d.n_drowsy / n_per_subject
        forms = {"raw": d.pr_auc,
                 "lift": d.pr_auc - prevalence,
                 "ratio": d.pr_auc / prevalence}
        row = dict(arm=arm, model=m)
        for tag, series in forms.items():
            # Through the paper's own wrapper, not scipy directly. At n = 10 the
            # two are identical, because EXACT_SPEARMAN_MAX_N is 8 and the wrapper
            # falls through to the same t-approximation. The call mattered anyway:
            # this was the one five-point-or-larger family still bypassing the
            # wrapper, so if the subject count ever dropped below nine it would have
            # stayed on the approximation while every other family moved to exact.
            rho, pval, _exact = spearman(d.n_drowsy, series)
            row["rho_%s" % tag] = float(rho)
            row["p_%s" % tag] = float(pval)
        out.append(row)
    return pd.DataFrame(out)


def ranking_vs_reliability(folds, pooled, arm):
    """ROC-AUC against raw pooled Brier across the five architectures.

    Reported only so that a reader who computes it is not surprised by its
    absence.  It is estimator-dependent and significant on no arm, so the paper
    claims the separation of the two properties, not a coupling between them.
    """
    brier = [pooled_row(pooled, arm, m)["brier"][0] for m in C.MODELS]
    out = {}
    for tag, auc in (("pooled", [pooled_row(pooled, arm, m)["auc"][0] for m in C.MODELS]),
                     ("subject_averaged",
                      [subject_averaged(folds, arm, m, "auc")[0] for m in C.MODELS])):
        rho, p, _ = spearman(auc, brier)
        out[tag] = (rho, p)
    return out


# ---------------------------------------------------------------- spreads
def spread_ratio(folds, arm, col="pr_auc"):
    """Between-subject SD against between-seed SD, per architecture.

    Subject spread exceeds seed spread many times over on every arm, which is
    why an interval on these results must be taken over subjects.
    """
    out = []
    for m in C.MODELS:
        subject_sd = float(subject_means(folds, arm, m, col).std(ddof=1))
        seed_sd = float(seed_means(folds, arm, m, col).std(ddof=1))
        out.append(dict(arm=arm, model=m, metric=col,
                        subject_sd=subject_sd, seed_sd=seed_sd,
                        ratio=subject_sd / seed_sd if seed_sd else np.inf))
    return pd.DataFrame(out)


def subject_range(folds, arm, col="pr_auc"):
    """Per-subject value averaged over the five architectures, and its extremes."""
    s = rows(folds, arm).groupby("subject")[col].mean().reindex(C.SUBJECTS)
    return dict(arm=arm, metric=col, values=s,
                min=float(s.min()), min_subject=str(s.idxmin()),
                max=float(s.max()), max_subject=str(s.idxmax()))


# ---------------------------------------------------------------- thresholded
def degenerate_folds(folds, arm):
    """Folds with no true positive at 0.5, so F1 = 0 and balanced accuracy = 0.500.

    They are kept in every average.  Dropping them would silently improve every
    threshold-dependent number in the paper.  In this data F1 = 0, precision = 0
    and recall = 0 select the same folds, which assert_consistent() checks.
    """
    return {m: int((rows(folds, arm, m).f1 == 0).sum()) for m in C.MODELS}


def pooled_confusion(folds, arm, pooled=None):
    """The pooled confusion matrix: counts summed over the ten folds within a
    seed, then averaged over the five seeds.

    True positives come from the per-fold recall and drowsy count, which is
    exact.  False positives are taken from ALL_POOLED.csv, where they were
    counted directly from the predictions.

    They CANNOT be recovered from the per-fold summaries alone, and this is not
    a rounding detail.  A fold's predicted-positive count is TP / precision,
    which is undefined when precision is zero -- and precision is zero for every
    degenerate fold, including those that predicted some windows drowsy and got
    all of them wrong.  Treating those folds as having predicted nothing
    under-counts false positives by up to 17 windows per architecture on this
    data, which moves the accuracy column by up to 0.2 points.  Passing `pooled`
    avoids the whole problem; omitting it falls back to the reconstruction and
    marks the result as approximate.
    """
    spec = C.ARMS[arm]
    n_total, n_drowsy = spec["n_windows"], spec["n_drowsy"]
    out = []
    for m in C.MODELS:
        d = rows(folds, arm, m)
        tp = float(np.mean([float((g.recall * g.n_drowsy).sum())
                            for _, g in d.groupby("seed")]))
        exact = False
        if pooled is not None:
            q = pooled[(pooled.ar == arm) & (pooled.model == m)]
            if not q.empty and "fp" in q.columns and q.fp.notna().all():
                fp = float(q.fp.mean())
                exact = True
        if not exact:
            fp_s = []
            for _, g in d.groupby("seed"):
                with np.errstate(divide="ignore", invalid="ignore"):
                    pp = np.where(g.precision > 0,
                                  (g.recall * g.n_drowsy) / g.precision.replace(0, np.nan),
                                  0.0)
                fp_s.append(float(np.nan_to_num(pp).sum())
                            - float((g.recall * g.n_drowsy).sum()))
            fp = float(np.mean(fp_s))
        fn = n_drowsy - tp
        tn = n_total - tp - fp - fn
        out.append(dict(arm=arm, model=m, tn=tn, fp=fp, fn=fn, tp=tp,
                        recall=tp / (tp + fn) if tp + fn else np.nan,
                        precision=tp / (tp + fp) if tp + fp else 0.0,
                        accuracy=100.0 * (tp + tn) / n_total,
                        fp_source="recorded" if exact else "reconstructed"))
    df = pd.DataFrame(out).sort_values("accuracy", ascending=False).reset_index(drop=True)
    return df


def recall_conventions(folds, arm):
    """Subject-averaged against pooled recall, the two conventions side by side.

    Pooled recall weights each fold by its drowsy count, so it is undefined when a
    selection contains no drowsy windows at all. That cannot happen on this study's
    data -- every subject contributes at least five -- but it did happen in a test
    built from synthetic folds, where numpy divided by zero, returned nan, and
    printed a RuntimeWarning that has been visible in every test run since. A
    warning nobody acts on is noise that hides the next one, so the case is named
    here and returns nan deliberately rather than by accident.
    """
    out = []
    for m in C.MODELS:
        d = rows(folds, arm, m)
        sa = subject_averaged(folds, arm, m, "recall")[0]
        drowsy = float(d.n_drowsy.sum())
        pooled = float((d.recall * d.n_drowsy).sum() / drowsy) if drowsy else np.nan
        out.append(dict(arm=arm, model=m, subject_averaged=sa, pooled=pooled,
                        difference=pooled - sa))
    return pd.DataFrame(out)


def pooled_confusion_by_seed(folds, arm, pooled):
    """The same pooled confusion matrix, but per seed rather than averaged over them.

    `pooled_confusion` averages the five seeds and returns one row per
    architecture, which is what the tables print. It therefore has no dispersion
    to report, and Table 5 gave pooled accuracy, recall and precision as bare
    point estimates while the tables beside it carried a seed SD on every column.

    That hid the largest instability in the study. ShallowConvNet on Arm B has a
    pooled accuracy of 81.85 % with a seed SD of 6.22 points, ranging from 70.88 %
    to 85.72 % -- one seed accounts for most of the gap that makes it look reliably
    worst, and the same outlier seed is the one the Figure S1 caption already flags
    for Brier. This function exposes the per-seed values so the SD can be reported.

    `pooled` is required, not optional: the false-positive reconstruction used as a
    fallback in `pooled_confusion` is approximate, and an approximate count has no
    business setting the width of a reported interval.
    """
    if pooled is None:
        raise ValueError("pooled results are required: a dispersion may not be "
                         "computed from reconstructed false-positive counts")
    spec = C.ARMS[arm]
    n_total, n_drowsy = spec["n_windows"], spec["n_drowsy"]
    out = []
    for m in C.MODELS:
        d = rows(folds, arm, m)
        q = pooled[(pooled.ar == arm) & (pooled.model == m)]
        if q.empty or "fp" not in q.columns or q.fp.isna().any():
            raise ValueError("no recorded false positives for Arm %s %s" % (arm, m))
        fp_by_seed = q.set_index("seed").fp
        for seed, g in d.groupby("seed"):
            tp = float((g.recall * g.n_drowsy).sum())
            fp = float(fp_by_seed.loc[seed])
            fn = n_drowsy - tp
            tn = n_total - tp - fp - fn
            out.append(dict(
                arm=arm, model=m, seed=seed, tn=tn, fp=fp, fn=fn, tp=tp,
                recall=tp / (tp + fn) if tp + fn else np.nan,
                precision=tp / (tp + fp) if tp + fp else np.nan,
                accuracy=100.0 * (tn + tp) / n_total))
    return pd.DataFrame(out)


def pooled_confusion_spread(folds, arm, pooled):
    """(mean, SD over the five seeds) for pooled accuracy, recall and precision."""
    per = pooled_confusion_by_seed(folds, arm, pooled)
    out = []
    for m in C.MODELS:
        d = per[per.model == m]
        row = dict(arm=arm, model=m, n_seeds=len(d))
        for col in ("accuracy", "recall", "precision"):
            row["%s_mean" % col] = float(d[col].mean())
            row["%s_sd" % col] = float(d[col].std(ddof=1))
            row["%s_min" % col] = float(d[col].min())
            row["%s_max" % col] = float(d[col].max())
        out.append(row)
    return pd.DataFrame(out)


def accuracy_vs_recall(folds, arm, pooled=None):
    """Rank correlation between an architecture's accuracy and its pooled recall.

    Negative on every arm.  This is the quantitative form of the claim that
    accuracy is not merely weak here but points the wrong way.
    """
    cm = pooled_confusion(folds, arm, pooled)
    rho, p, exact = spearman(cm.accuracy, cm.recall)
    return dict(arm=arm, rho=rho, p=p, exact=exact)


# ---------------------------------------------------------------- self-checks
def assert_consistent(folds, pooled):
    """Invariants that must hold before any number is quoted. Raises on failure."""
    problems = []

    if len(folds) != C.total_folds():
        problems.append("ALL_FOLDS.csv has %d rows, expected %d"
                        % (len(folds), C.total_folds()))
    expected_pooled = len(C.ARMS) * len(C.MODELS) * len(C.SEEDS)
    if len(pooled) != expected_pooled:
        problems.append("ALL_POOLED.csv has %d rows, expected %d"
                        % (len(pooled), expected_pooled))

    for arm in sorted(C.ARMS):
        d = rows(folds, arm)
        if d.empty:
            problems.append("arm %s missing from ALL_FOLDS.csv" % arm)
            continue
        total = d.groupby(["model", "seed"]).n_drowsy.sum().unique()
        if set(total.tolist()) != {C.ARMS[arm]["n_drowsy"]}:
            problems.append("arm %s: folds sum to %s drowsy windows, expected %d"
                            % (arm, sorted(set(total.tolist())), C.ARMS[arm]["n_drowsy"]))
        for m in C.MODELS:
            g = rows(folds, arm, m)
            n_f1 = int((g.f1 == 0).sum())
            n_pr = int((g.precision == 0).sum())
            if n_f1 != n_pr:
                problems.append("arm %s %s: %d folds with F1 = 0 but %d with "
                                "precision = 0" % (arm, m, n_f1, n_pr))

    if problems:
        raise AssertionError("; ".join(problems))
    return True
