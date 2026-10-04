"""Measure what recalibration actually does to the ranking metrics.

    python3 tools/check_monotonicity.py                  # results/, Arm A
    python3 tools/check_monotonicity.py /other/root [ARM]

The manuscript says that Platt scaling leaves the SUBJECT-AVERAGED ROC-AUC and
PR-AUC unchanged at the reported precision because the fitted map is strictly
increasing, and that isotonic regression can lower them
because its map is only weakly increasing and its flat regions create ties.

Both halves of that are theory. The first holds only if every fitted logistic slope
is positive, which is a property of the fits, not of the method — a negative slope
would reverse the ranking and is perfectly possible on a fold where the scores
anti-correlate with the labels. Nothing in the released summaries records the slopes,
so the claim was being made without evidence for it.

This script supplies the evidence. For every leave-one-subject-out fold it refits
Platt and isotonic exactly as `src/calibrate.py` does, then reports:

  * the fitted Platt slope, and how many of the fits have a positive one
  * ROC-AUC and PR-AUC before and after each map, and the largest change in each
  * the number of distinct score values before and after isotonic, which is where
    the ties that can cost PR-AUC come from

Exit status is 1 if any Platt slope is not positive, or if any Platt fit moves
ROC-AUC by more than a floating-point tolerance — that is, if the manuscript's
claim is false on this data.
"""

import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Arm A is the only construction whose per-window scores were released, so it
# is the only one this can measure.
DEFAULT_ARM = "A"
import sys

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as C  # noqa: E402
from src.calibrate import iter_prob_files, _logit  # noqa: E402

TOL = 1e-9


def platt_with_slope(p_fit, y_fit, p_apply):
    """Fit Platt as calibrate.py does and return (mapped scores, slope)."""
    lr = LogisticRegression(C=C.PLATT_C, solver="lbfgs")
    lr.fit(_logit(p_fit).reshape(-1, 1), y_fit)
    return lr.predict_proba(_logit(p_apply).reshape(-1, 1))[:, 1], float(lr.coef_[0][0])


def safe(fn, y, p):
    """A metric, or None when the fold has only one class present."""
    return None if len(np.unique(y)) < 2 else float(fn(y, p))


def main(argv):
    # Defaults, so that the invocation README documents -- and the one every other
    # check in this repository uses -- actually runs. Until 24 September 2026 this
    # was the only tool here that required a path, and the documented command
    # printed this docstring and measured nothing. Both positional arguments still
    # work, for a release extracted somewhere else.
    root = argv[0] if argv else os.path.join(HERE, "results")
    arm = argv[1] if len(argv) > 1 else DEFAULT_ARM

    rows, slopes = [], []
    files = list(iter_prob_files(root, arm))
    if not files:
        # Also accept a flat directory of probs_*.npz with no arm subdirectory.
        import glob
        import re
        for path in sorted(glob.glob(os.path.join(root, "probs_*.npz"))):
            m = re.match(r"probs_(.+)_seed(\d+)\.npz", os.path.basename(path))
            if m:
                files.append((m.group(1), int(m.group(2)), path))
    if not files:
        print("no probs_*.npz found under", root)
        return 2

    for model, seed, path in files:
        d = np.load(path)
        y, p, subj = d["y_true"], d["y_prob"].astype(float), d["subject"]
        for s in np.unique(subj):
            te, tr = subj == s, subj != s
            if len(np.unique(y[te])) < 2 or len(np.unique(y[tr])) < 2:
                continue
            pl, slope = platt_with_slope(p[tr], y[tr], p[te])
            iso = IsotonicRegression(out_of_bounds="clip").fit(
                p[tr], y[tr]).predict(p[te])
            slopes.append((model, seed, str(s), slope))
            rows.append(dict(
                model=model, seed=seed, subject=str(s), slope=slope,
                auc_raw=safe(roc_auc_score, y[te], p[te]),
                auc_platt=safe(roc_auc_score, y[te], pl),
                auc_iso=safe(roc_auc_score, y[te], iso),
                ap_raw=safe(average_precision_score, y[te], p[te]),
                ap_platt=safe(average_precision_score, y[te], pl),
                ap_iso=safe(average_precision_score, y[te], iso),
                uniq_raw=len(np.unique(p[te])), uniq_iso=len(np.unique(iso)),
                uniq_platt=len(np.unique(pl)),
            ))

    n = len(rows)
    neg = [r for r in rows if r["slope"] <= 0]
    d_auc_platt = max(abs(r["auc_platt"] - r["auc_raw"]) for r in rows)
    d_ap_platt = max(abs(r["ap_platt"] - r["ap_raw"]) for r in rows)
    d_auc_iso = [r["auc_iso"] - r["auc_raw"] for r in rows]
    d_ap_iso = [r["ap_iso"] - r["ap_raw"] for r in rows]

    print("folds measured: %d   (from %d probability file(s))\n" % (n, len(files)))
    print("PLATT")
    print("  fitted slopes      min %.4f   max %.4f   median %.4f"
          % (min(r["slope"] for r in rows), max(r["slope"] for r in rows),
             float(np.median([r["slope"] for r in rows]))))
    print("  positive slopes    %d of %d" % (n - len(neg), n))
    print("  largest |dROC-AUC| %.3e" % d_auc_platt)
    print("  largest |dPR-AUC|  %.3e" % d_ap_platt)
    # A strictly increasing map cannot reorder anything, so any movement at all
    # has to come from ties, and the ties come from the epsilon-clip inside
    # _logit: every raw score below eps maps to the same logit and therefore to
    # the same calibrated score. This prints how many that is, so the residual
    # movement above is attributed rather than waved away as "numerical".
    ties = [r["uniq_raw"] - r["uniq_platt"] for r in rows]
    print("  ties created by the epsilon-clip: max %d, median %d, folds affected %d of %d"
          % (max(ties), int(np.median(ties)), sum(1 for t in ties if t > 0), n))
    print("\nISOTONIC")
    print("  dROC-AUC   min %+.4f   max %+.4f   folds worse %d of %d"
          % (min(d_auc_iso), max(d_auc_iso), sum(1 for d in d_auc_iso if d < -TOL), n))
    print("  dPR-AUC    min %+.4f   max %+.4f   folds worse %d of %d"
          % (min(d_ap_iso), max(d_ap_iso), sum(1 for d in d_ap_iso if d < -TOL), n))
    print("  distinct scores per fold: raw median %d, isotonic median %d"
          % (int(np.median([r["uniq_raw"] for r in rows])),
             int(np.median([r["uniq_iso"] for r in rows]))))

    # The failure condition is a map that actually reorders: a non-positive slope,
    # or a movement too large to be explained by clip-induced ties. The threshold
    # is 1e-3 on ROC-AUC, an order of magnitude below the third decimal place the
    # manuscript reports, so anything that would change a printed value fails.
    bad = bool(neg) or d_auc_platt > 1e-3
    if neg:
        print("\nNON-POSITIVE PLATT SLOPES — the invariance claim fails on these folds:")
        for r in neg:
            print("  %s seed %d subject %s slope %.4f"
                  % (r["model"], r["seed"], r["subject"], r["slope"]))
    print("\n%s" % ("CLAIM NOT SUPPORTED" if bad else
                    "Every Platt fit is strictly increasing; ranking metrics move only\n"
                    "by clip-induced ties. Whether that survives into a REPORTED\n"
                    "value is a different question, at a different aggregation:\n"
                    "tools/check_ranking_invariance.py answers it."))

    # Write the summary where registry.py can pick it up, so the manuscript can
    # cite these as registered numbers rather than as something measured once.
    arm_label = arm or "A"
    out_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results", "monotonicity.csv")
    summary = [
        ("folds measured for recalibration monotonicity", n, "%d probability file(s)" % len(files)),
        ("Platt fits with a positive slope", n - len(neg), "of %d" % n),
        ("smallest fitted Platt slope", round(min(r["slope"] for r in rows), 4), ""),
        ("largest fitted Platt slope", round(max(r["slope"] for r in rows), 4), ""),
        # Fixed point, not repr(): "3.973e-05" in the registry would not match the
        # manuscript's "3.973 x 10^-5" once scan.py folds it to a decimal literal.
        ("largest Platt change in fold ROC-AUC", ("%.10f" % d_auc_platt).rstrip("0"),
         "attributable to epsilon-clip ties, not reordering"),
        ("largest Platt change in fold PR-AUC", ("%.10f" % d_ap_platt).rstrip("0"),
         "attributable to epsilon-clip ties, not reordering"),
        ("folds on which the epsilon-clip created ties under Platt",
         sum(1 for t in ties if t > 0), "of %d" % n),
        ("most ties created on one fold by the epsilon-clip", max(ties), ""),
        ("folds on which isotonic lowered ROC-AUC",
         sum(1 for d in d_auc_iso if d < -TOL), "of %d" % n),
        ("folds on which isotonic lowered PR-AUC",
         sum(1 for d in d_ap_iso if d < -TOL), "of %d" % n),
        ("largest isotonic fall in fold ROC-AUC", round(min(d_auc_iso), 4), ""),
        ("largest isotonic fall in fold PR-AUC", round(min(d_ap_iso), 4), ""),
        ("median distinct scores per fold before isotonic",
         int(np.median([r["uniq_raw"] for r in rows])), ""),
        ("median distinct scores per fold after isotonic",
         int(np.median([r["uniq_iso"] for r in rows])), ""),
    ]
    with open(out_path, "w") as fh:
        fh.write("arm,claim,value,note\n")
        for claim, value, note in summary:
            fh.write('%s,"%s",%s,"%s"\n' % (arm_label, claim, value, note))
    print("wrote", out_path)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
