"""Measure what out-of-subject Platt scaling does to the ranking metrics.

    python3 tools/check_ranking_invariance.py

WHY THIS EXISTS

The paper says recalibration leaves ROC-AUC and PR-AUC "unchanged at the reported
precision". A monotone increasing map cannot reorder scores, so in exact arithmetic
that is a theorem rather than a measurement -- but the implementation clips
probabilities to [1e-6, 1 - 1e-6] before taking the logit, and a clip can tie
scores that were distinct. The claim is therefore an empirical one and has to be
measured.

It was, once, but at the WRONG GRANULARITY: `tools/check_monotonicity.py` reports
the largest movement in any SINGLE FOLD, and the paper then argued from that number
that the tables are unaffected. A single fold's movement is not what the tables
print. The tables print an average over fifty folds, and an average absorbs a
per-fold movement. Arguing from the per-fold maximum was arguing from the wrong
quantity -- conservative in direction, but it made the published justification
("below the precision reported anywhere in this paper") false for PR-AUC, whose
per-fold maximum is 34 times the printed unit.

WHAT THIS MEASURES

The same quantity the tables print, on the same scores, fitted the same way:

  * for every fold, Platt is fitted on the OTHER NINE subjects of that seed and
    applied to the held-out subject -- `calibrate.fit_apply_platt`, not a
    reimplementation of it, so this cannot drift from the pipeline;
  * ROC-AUC and PR-AUC are computed per fold, raw and recalibrated;
  * the folds are aggregated BOTH ways the paper aggregates: subject-averaged
    (mean over the ten subjects within a seed, then over the five seeds) and
    pooled (the ten folds of a seed concatenated and scored once, then over seeds);
  * each aggregate is compared raw against recalibrated at the precisions the
    paper actually prints -- three decimals in the Section 7.1 tables, four in the
    Section 7.5 tables.

It also reports the per-fold maximum, so the two granularities sit side by side and
the difference between them is visible rather than arguable.

SCOPE. Arm A only, because Arm A is the only construction whose per-window scores
were released, and three architectures within it. The released Arm A EEGNet scores
come from the earlier of the two Arm A executions (Section 7.9); that does not
affect this measurement, which compares raw against recalibrated within one and the
same set of scores.

Exits non-zero only if a SUBJECT-AVERAGED value -- the aggregation the paper's
ranking tables use -- changes at a precision the paper prints. The pooled figures
are printed for completeness and do not fail the run: no pooled post-recalibration
ranking metric is reported anywhere in the paper, and the movement there is a
property of pooling across ten differently-fitted maps rather than of the maps.

It writes `results/ranking_invariance.csv`, which `src/registry.py` reads, so the
numbers the manuscript quotes are registry rows like every other number.
"""

import glob
import os
import sys

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import config as C  # noqa: E402
from src.calibrate import fit_apply_platt  # noqa: E402

ARM = "A"
FILE_STEM = {m: m.replace("-", "") for m in C.MODELS}
# The precisions the paper prints these two metrics at: three decimals in the
# subject-averaged tables of Section 7.1, four in the pooled tables of Section 7.5.
PLACES = (3, 4)


def folds_of(path):
    """Every (subject, y, p_raw, p_platt) fold in one released seed file."""
    d = np.load(path, allow_pickle=True)
    y, p = d["y_true"], d["y_prob"].astype(float)
    subj = np.array([str(s) for s in d["subject"]])
    out = []
    for s in C.SUBJECTS:
        te = subj == s
        tr = ~te
        if not te.any() or len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
            continue
        out.append((s, y[te], p[te], fit_apply_platt(p[tr], y[tr], p[te])))
    return out


def score(y, p):
    return roc_auc_score(y, p), average_precision_score(y, p)


def main():
    print("what out-of-subject Platt scaling does to the ranking metrics")
    print("Arm %s, the released per-window scores, fitted with "
          "calibrate.fit_apply_platt\n" % ARM)

    problems = []
    worst_fold = {"auc": 0.0, "pr_auc": 0.0}
    any_model = False
    summary = []           # rows for results/ranking_invariance.csv

    for model in C.MODELS:
        paths = sorted(glob.glob(os.path.join(
            HERE, "results", ARM, "probs_%s_seed*.npz" % FILE_STEM[model])))
        if not paths:
            continue
        any_model = True

        per_seed = {"raw": [], "cal": [], "praw": [], "pcal": []}
        pooled = {"raw": [], "cal": [], "praw": [], "pcal": []}
        n_folds = 0

        for path in paths:
            fold_auc_r, fold_auc_c, fold_pr_r, fold_pr_c = [], [], [], []
            ys, praws, pcals = [], [], []
            for _s, y, p_raw, p_cal in folds_of(path):
                n_folds += 1
                a_r, p_r = score(y, p_raw)
                a_c, p_c = score(y, p_cal)
                fold_auc_r.append(a_r); fold_auc_c.append(a_c)
                fold_pr_r.append(p_r); fold_pr_c.append(p_c)
                worst_fold["auc"] = max(worst_fold["auc"], abs(a_c - a_r))
                worst_fold["pr_auc"] = max(worst_fold["pr_auc"], abs(p_c - p_r))
                ys.append(y); praws.append(p_raw); pcals.append(p_cal)
            # subject-averaged: mean over the subjects of this seed
            per_seed["raw"].append(np.mean(fold_auc_r))
            per_seed["cal"].append(np.mean(fold_auc_c))
            per_seed["praw"].append(np.mean(fold_pr_r))
            per_seed["pcal"].append(np.mean(fold_pr_c))
            # pooled: this seed's ten folds concatenated and scored once
            yy = np.concatenate(ys)
            a_r, p_r = score(yy, np.concatenate(praws))
            a_c, p_c = score(yy, np.concatenate(pcals))
            pooled["raw"].append(a_r); pooled["cal"].append(a_c)
            pooled["praw"].append(p_r); pooled["pcal"].append(p_c)

        print("  %s   %d folds, %d seed file(s)" % (model, n_folds, len(paths)))
        for label, d in (("subject-averaged", per_seed), ("pooled", pooled)):
            for metric, kr, kc in (("ROC-AUC", "raw", "cal"),
                                   ("PR-AUC", "praw", "pcal")):
                r, c = float(np.mean(d[kr])), float(np.mean(d[kc]))
                bits = []
                for places in PLACES:
                    same = round(r, places) == round(c, places)
                    bits.append("%ddp %s" % (places, "same" if same else "CHANGES"))
                    # Only the subject-averaged aggregation gates the run: it is
                    # the one the paper's ranking tables print.
                    if not same and label == "subject-averaged":
                        problems.append(
                            "%s %s %s changes at %d dp: %.*f -> %.*f"
                            % (model, label, metric, places, places, r, places, c))
                if label == "subject-averaged":
                    summary.append(
                        ("Arm %s %s subject-averaged %s change after Platt" % (ARM, model, metric),
                         ("%.10f" % abs(c - r)).rstrip("0").rstrip(".") or "0",
                         "%s raw %.6f, recalibrated %.6f" % (metric, r, c)))
                print("      %-16s %-8s raw %.6f   Platt %.6f   delta %+.2e   %s"
                      % (label, metric, r, c, c - r, "  ".join(bits)))
        print("")

    if not any_model:
        print("  no released probability files found")
        return 1

    print("  largest movement in any SINGLE fold:  ROC-AUC %.3e   PR-AUC %.3e"
          % (worst_fold["auc"], worst_fold["pr_auc"]))
    print("  (that is the quantity tools/check_monotonicity.py reports; it is not\n"
          "   the quantity the tables print)")

    # Written where registry.py can pick it up, so the manuscript cites these as
    # registered numbers rather than as something measured once in a terminal.
    out = os.path.join(HERE, "results", "ranking_invariance.csv")
    with open(out, "w") as fh:
        fh.write("arm,claim,value,note\n")
        for claim, value, note in summary:
            fh.write('%s,"%s",%s,"%s"\n' % (ARM, claim.split(" ", 2)[2], value, note))
    print("\n  wrote results/ranking_invariance.csv (%d row(s))" % len(summary))

    print("\n%d subject-averaged value(s) change at a precision the paper prints"
          % len(problems))
    for p in problems:
        print("    " + p)
    if not problems:
        print("At three and four decimals, every SUBJECT-AVERAGED ROC-AUC and PR-AUC "
              "is\nidentical before and after recalibration. The pooled figures above "
              "are not\na reported quantity and are printed for completeness.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
