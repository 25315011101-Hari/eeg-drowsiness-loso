"""Out-of-subject probability recalibration.

    python -m src.calibrate --arm C

For every leave-one-subject-out fold a SEPARATE calibrator is fitted on the
concatenated predictions for the other nine subjects of the same seed and then
applied to the held-out subject.  That is fifty calibrators per architecture per
arm, none of which ever saw the subject it was scored on.  Fitting one calibrator
on all the predictions at once would leak the test subject into its own
correction and is the mistake this module exists to avoid.

Two calibrators are compared:

  Platt      a logistic function of the logit, effectively unpenalised
             (LogisticRegression at C = config.PLATT_C).  Two parameters.
  isotonic   a monotone step function, non-parametric.

Both are strictly monotone, so neither can reorder any pair of windows: ROC-AUC
and PR-AUC are unchanged by construction.  Any improvement they produce is
therefore about the scale of the scores, not their ordering, and that is the
whole argument of the paper's calibration section.

Reported on two scales, both subject-averaged -- computed on each held-out
subject, then averaged over the ten subjects and the five seeds:

  Brier   mean squared error of the probability.  The reference is the class
          prior's own Brier score pi*(1-pi); a model ABOVE it is worse than a
          constant predictor that ignores the input.
  ECE     expected calibration error over config.ECE_BINS equal-width bins.

Pooled ECE is systematically smaller, because one subject's over-confidence
cancels another's under-confidence.  The two are never mixed.
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

CAL_KINDS = ("raw", "platt", "isotonic")
_NICE = {"CNNBiLSTM": "CNN-BiLSTM"}
_EPS = 1e-6


def expected_calibration_error(p, y, bins=None):
    """Equal-width-bin ECE. Empty bins contribute nothing and are not counted."""
    bins = C.ECE_BINS if bins is None else bins
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(y) == 0:
        return float("nan")
    idx = np.clip(np.digitize(p, np.linspace(0, 1, bins + 1)) - 1, 0, bins - 1)
    total = 0.0
    for k in range(bins):
        m = idx == k
        if m.any():
            total += abs(p[m].mean() - y[m].mean()) * m.sum()
    return float(total / len(y))


def brier(p, y):
    return float(np.mean((np.asarray(p, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def _logit(p):
    q = np.clip(np.asarray(p, dtype=float), _EPS, 1 - _EPS)
    return np.log(q / (1 - q))


def fit_apply_platt(p_fit, y_fit, p_apply):
    """Logistic function of the logit, fitted out of subject."""
    lr = LogisticRegression(C=C.PLATT_C, solver="lbfgs")
    lr.fit(_logit(p_fit).reshape(-1, 1), y_fit)
    return lr.predict_proba(_logit(p_apply).reshape(-1, 1))[:, 1]


def fit_apply_isotonic(p_fit, y_fit, p_apply):
    """Monotone step function, fitted out of subject."""
    return IsotonicRegression(out_of_bounds="clip").fit(p_fit, y_fit).predict(p_apply)


def iter_prob_files(result_dir, arm):
    """Yield (model, seed, path) for every probs_*.npz belonging to an arm."""
    root = os.path.join(result_dir, arm)
    for path in sorted(glob.glob(os.path.join(root, "**", "probs_*.npz"), recursive=True)):
        m = re.match(r"probs_(.+)_seed(\d+)\.npz", os.path.basename(path))
        if m:
            yield _NICE.get(m.group(1), m.group(1)), int(m.group(2)), path


def calibrate_arm(arm, result_dir=None, verbose=True):
    """Per-fold calibration for every architecture whose probability files exist."""
    result_dir = result_dir or C.RESULT_DIR
    rows = []
    files = list(iter_prob_files(result_dir, arm))
    if not files:
        raise FileNotFoundError("no probs_*.npz under %s"
                                % os.path.join(result_dir, arm))

    for name, seed, path in files:
        d = np.load(path, allow_pickle=True)
        y = d["y_true"].astype(int)
        p = d["y_prob"].astype(float)
        g = np.asarray([str(s) for s in d["subject"]])
        if int(y.sum()) != C.ARMS[arm]["n_drowsy"]:
            raise ValueError("%s holds %d drowsy windows, arm %s expects %d"
                             % (path, int(y.sum()), arm, C.ARMS[arm]["n_drowsy"]))

        for s in C.SUBJECTS:
            te = g == s
            if not te.any():
                raise ValueError("%s has no rows for subject %s" % (path, s))
            y_out, p_out = y[~te], p[~te]
            y_in, p_in = y[te], p[te]
            variants = {
                "raw": p_in,
                "platt": fit_apply_platt(p_out, y_out, p_in),
                "isotonic": fit_apply_isotonic(p_out, y_out, p_in),
            }
            for kind, q in variants.items():
                rows.append(dict(arm=arm, model=name, seed=seed, subject=s, cal=kind,
                                 brier=brier(q, y_in),
                                 ece=expected_calibration_error(q, y_in)))
        if verbose:
            print("  calibrated %s seed %d" % (name, seed), flush=True)

    return pd.DataFrame(rows)


def summarise(folds, arm):
    """Subject-averaged summary plus the paired tests raw against Platt."""
    ref = C.arm_reference(arm)["brier"]
    out = []
    for model in sorted(folds.model.unique()):
        row = dict(arm=arm, model=model, brier_reference=ref)
        for kind in CAL_KINDS:
            g = folds[(folds.model == model) & (folds.cal == kind)]
            # average within a seed over subjects, then over seeds
            row["ece_%s" % kind] = g.groupby("seed").ece.mean().mean()
            row["brier_%s" % kind] = g.groupby("seed").brier.mean().mean()
        for metric in ("brier", "ece"):
            raw = (folds[(folds.model == model) & (folds.cal == "raw")]
                   .groupby("subject")[metric].mean().loc[C.SUBJECTS])
            pla = (folds[(folds.model == model) & (folds.cal == "platt")]
                   .groupby("subject")[metric].mean().loc[C.SUBJECTS])
            row["p_%s" % metric] = wilcoxon(pla, raw).pvalue
            row["n_%s" % metric] = int((pla < raw).sum())
        row["above_reference_raw"] = bool(row["brier_raw"] > ref)
        row["above_reference_platt"] = bool(row["brier_platt"] > ref)
        out.append(row)
    return pd.DataFrame(out)


def report(summary, arm):
    ref = C.arm_reference(arm)["brier"]
    print("\nArm %s   class-prior Brier reference %.4f" % (arm, ref))
    print("%-16s %-23s %-23s" % ("", "ECE raw/platt/iso", "Brier raw/platt/iso"))
    for _, r in summary.iterrows():
        print("%-16s %6.4f %6.4f %6.4f   %6.4f %6.4f %6.4f   p(brier)=%.4f %d/10  "
              "p(ece)=%.4f %d/10"
              % (r.model, r.ece_raw, r.ece_platt, r.ece_isotonic,
                 r.brier_raw, r.brier_platt, r.brier_isotonic,
                 r.p_brier, r.n_brier, r.p_ece, r.n_ece))
    n = len(summary)
    print("  above the reference:  raw %d of %d  ->  platt %d of %d"
          % (int(summary.above_reference_raw.sum()), n,
             int(summary.above_reference_platt.sum()), n))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", action="append", choices=sorted(C.ARMS),
                    help="repeatable; default is every arm found")
    ap.add_argument("--result-dir", default=None)
    a = ap.parse_args(argv)
    result_dir = a.result_dir or C.RESULT_DIR

    arms = a.arm or [x for x in sorted(C.ARMS)
                     if list(iter_prob_files(result_dir, x))]
    if not arms:
        print("no probability files found under", result_dir)
        return 1

    for arm in arms:
        folds = calibrate_arm(arm, result_dir)
        summary = summarise(folds, arm)
        out = os.path.join(result_dir, arm)
        folds.to_csv(os.path.join(out, "calibration_folds.csv"), index=False)
        summary.to_csv(os.path.join(out, "calibration_summary.csv"), index=False)
        report(summary, arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
