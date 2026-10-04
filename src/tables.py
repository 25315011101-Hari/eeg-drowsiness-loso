"""Emit every table in the Results section as markdown, straight from the data.

    python -m src.tables                 # all of them, to stdout
    python -m src.tables --out tables.md
    python -m src.tables --only 1 3 5

The point of generating them rather than typing them is that a table can never
drift from the run it describes.  Re-run this after any change to the result
files and paste the output over the old section.

Section numbers follow Results draft 4:

  1   architecture comparison, subject-averaged ROC-AUC and PR-AUC
  1a  arms A and C, which isolate balancing
  2   the CNN / CNN-BiLSTM ablation
  3   pooled confusion matrices
  3a  pooled against subject-averaged recall, and degenerate folds
  4   between-subject against between-seed spread, and the subject correlations
  5   pooled metrics with the Brier partition
  6   out-of-subject recalibration
  7   out-of-subject threshold selection
"""

import argparse
import io
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src import aggregate, stats  # noqa: E402

ARM_ORDER = ["A", "B", "C"]


def _p(v, bold_below=0.05):
    s = "p = %.4f" % v
    return "**%s**" % s if v < bold_below else s


def _table(header, body_rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in body_rows]
    return "\n".join(out)


# ------------------------------------------------------------------ section 1
def section_1(folds, pooled):
    o = io.StringIO()
    for col, title, chance in (("auc", "Subject-averaged ROC-AUC", None),
                               ("pr_auc", "Subject-averaged PR-AUC", True)):
        note = ""
        if chance:
            note = " (chance level %s)" % " / ".join(
                "%.4f" % C.arm_reference(a)["pr_auc"] for a in ARM_ORDER)
        o.write("**%s**%s\n\n" % (title, note))
        body = []
        for m in C.MODELS:
            cells = []
            for a in ARM_ORDER:
                mu, sd = stats.subject_averaged(folds, a, m, col)
                cells.append("%.3f ± %.3f" % (mu, sd))
            body.append([m, "{:,}".format(C.PARAMS[m])] + cells)
        o.write(_table(["Model", "Parameters"] + ["Arm %s" % a for a in ARM_ORDER], body))
        o.write("\n\n")

    o.write("**EEGNet against every other architecture, ROC-AUC, ten paired "
            "subject-level differences**\n\n")
    body = []
    for m in [x for x in C.MODELS if x != "EEGNet"]:
        cells = []
        for a in ARM_ORDER:
            r = stats.paired(folds, a, "EEGNet", m, "auc")
            cells.append("%s (%d/%d)" % (_p(r["p"]), r["a_wins"], r["n"]))
        body.append([m] + cells)
    o.write(_table(["EEGNet vs"] + ["Arm %s" % a for a in ARM_ORDER], body))
    o.write("\n\nSmallest attainable p-value on ten pairs: %.5f.\n\n"
            % C.P_FLOOR_WILCOXON_10)

    o.write("**The six pairwise comparisons that do not involve EEGNet**\n\n")
    body = []
    for a in ARM_ORDER:
        pw = stats.all_pairwise(folds, a, "auc")
        non = pw[(pw.a != "EEGNet") & (pw.b != "EEGNet")]
        body.append([a, "%d of %d" % (int((non.p < 0.05).sum()), len(non)),
                     "%.4f" % non.p.min()])
    o.write(_table(["Arm", "significant", "smallest p"], body))
    o.write("\n\n**Parameter count against ROC-AUC across the five architectures**\n\n")
    body = []
    for a in ARM_ORDER:
        r = stats.capacity_correlation(folds, a)
        body.append([a, "%+.3f" % r["rho"], "%.4f" % r["p"]])
    o.write(_table(["Arm", "rho", "p"], body))
    o.write("\n\nSmallest attainable p-value on five points: about %.3f.\n\n"
            % C.P_FLOOR_SPEARMAN_5)

    o.write("**Agreement between the per-arm orderings**\n\n")
    header = ["Metric"] + ["%s-%s" % (x, y) for x, y in
                           (("A", "B"), ("A", "C"), ("B", "C"))]
    body = []
    for col, label in (("auc", "ROC-AUC"), ("pr_auc", "PR-AUC"),
                       ("bal_acc", "Balanced accuracy"), ("f1", "F1")):
        d = stats.cross_arm_ordering(folds, col).set_index(["arm_a", "arm_b"])
        body.append([label] + ["%+.3f" % d.loc[(x, y), "rho"]
                               for x, y in (("A", "B"), ("A", "C"), ("B", "C"))])
    o.write(_table(header, body))
    return o.getvalue()


# ----------------------------------------------------------------- section 1a
def section_1a(folds, pooled):
    return _contrast_table(
        folds, "A", "C",
        "**Arms A and C share their trimming and differ only in balancing, so "
        "this comparison isolates that factor.**")


def section_1b(folds, pooled):
    return _contrast_table(
        folds, "B", "C",
        "**Arms B and C share their balancing rule and differ only in trimming, so "
        "this comparison isolates that factor.**")


# All four metrics, not three. These tables showed ROC-AUC, PR-AUC and F1 and left
# balanced accuracy out, while the summary beside them counted "significant tests of
# twenty" over all four. A reader counting significant cells in the A → C table found
# six and was told seven; the seventh was CNN-BiLSTM's balanced accuracy at p = 0.0039.
# Ten of the forty contrasts were invisible, inside the two counts that carry the
# paper's design conclusion.
_CONTRAST_METRICS = (("auc", "ROC-AUC"), ("pr_auc", "PR-AUC"),
                     ("bal_acc", "Bal. acc."), ("f1", "F1"))


def _contrast_table(folds, arm_a, arm_b, lead):
    o = io.StringIO()
    o.write(lead + "\n\n")
    body = []
    per_metric = {col: stats.arm_contrast(folds, arm_a, arm_b, col)
                  for col, _label in _CONTRAST_METRICS}
    for m in C.MODELS:
        cells = []
        for col, _label in _CONTRAST_METRICS:
            r = per_metric[col]
            r = r[r.model == m].iloc[0]
            cells.append("%.3f → %.3f, %s" % (r.mean_a, r.mean_b, _p(r.p)))
        body.append([m] + cells)
    head = ["Model"] + ["%s %s → %s" % (label, arm_a, arm_b)
                        for _col, label in _CONTRAST_METRICS]
    o.write(_table(head, body))
    return o.getvalue()


# ------------------------------------------------------------------ section 2
def section_2(folds, pooled):
    o = io.StringIO()
    o.write("**CNN → CNN-BiLSTM: identical trunk, one component changed.**\n\n")
    labels = {"auc": "ROC-AUC", "pr_auc": "PR-AUC", "bal_acc": "Bal. acc.", "f1": "F1"}
    body = []
    for col, label in labels.items():
        cells = []
        for a in ARM_ORDER:
            r = stats.paired(folds, a, "CNN", "CNN-BiLSTM", col)
            cells.append("%.3f → %.3f, %s (%d/%d)"
                         % (r["mean_a"], r["mean_b"], _p(r["p"]),
                            r["n"] - r["a_wins"], r["n"]))
        body.append([label] + cells)
    o.write(_table(["Metric"] + ["Arm %s: CNN → BiLSTM" % a for a in ARM_ORDER], body))
    return o.getvalue()


# ------------------------------------------------------------------ section 3
def section_3(folds, pooled):
    o = io.StringIO()
    for a in ARM_ORDER:
        spec, ref = C.ARMS[a], C.arm_reference(a)
        o.write("**Arm %s** (%d windows, %d drowsy; always-alert accuracy %.2f %%)\n\n"
                % (a, spec["n_windows"], spec["n_drowsy"], ref["accuracy"]))
        cm = stats.pooled_confusion(folds, a, pooled)
        body = [["%s" % r.model, "{:,.0f}".format(r.tn), "{:,.0f}".format(r.fp),
                 "{:,.0f}".format(r.fn), "{:,.0f}".format(r.tp),
                 "%.3f" % r.recall, "%.3f" % r.precision, "%.2f %%" % r.accuracy]
                for r in cm.itertuples()]
        o.write(_table(["Model", "TN", "FP", "FN", "TP", "Recall", "Precision",
                        "Accuracy"], body))
        r = stats.accuracy_vs_recall(folds, a, pooled)
        o.write("\n\nAccuracy against pooled recall: rho = %+.3f (p = %.4f).\n\n"
                % (r["rho"], r["p"]))
    return o.getvalue()


# ----------------------------------------------------------------- section 3a
def section_3a(folds, pooled):
    o = io.StringIO()
    o.write("**Pooled and subject-averaged recall**\n\n")
    body = []
    for m in C.MODELS:
        cells = []
        for a in ARM_ORDER:
            r = stats.recall_conventions(folds, a)
            r = r[r.model == m].iloc[0]
            cells.append("%.4f → %.4f (+%.4f)"
                         % (r.subject_averaged, r.pooled, r.difference))
        body.append([m] + cells)
    o.write(_table(["Model"] + ["Arm %s: subj-avg → pooled" % a for a in ARM_ORDER], body))

    o.write("\n\n**Degenerate folds** (no true positive at %.1f, so F1 = 0 and "
            "balanced accuracy = 0.500 by construction)\n\n" % C.FIXED_THRESHOLD)
    n = len(C.SEEDS) * C.N_SUBJECTS
    body = []
    for a in ARM_ORDER:
        d = stats.degenerate_folds(folds, a)
        body.append([a] + ["%d / %d" % (d[m], n) for m in C.MODELS])
    o.write(_table(["Arm"] + C.MODELS, body))
    return o.getvalue()


# ------------------------------------------------------------------ section 4
def section_4(folds, pooled):
    o = io.StringIO()
    o.write("**Between-subject spread against between-seed spread, PR-AUC**\n\n")
    body = []
    for a in ARM_ORDER:
        s = stats.spread_ratio(folds, a, "pr_auc")
        rng = stats.subject_range(folds, a, "pr_auc")
        body.append([a, "%.0f to %.0f times" % (s.ratio.min(), s.ratio.max()),
                     "%.3f (%s) to %.3f (%s)"
                     % (rng["min"], rng["min_subject"], rng["max"], rng["max_subject"])])
    o.write(_table(["Arm", "ratio over the five architectures",
                    "subject PR-AUC range, averaged over architectures"], body))

    o.write("\n\n**A subject's drowsy-window count against its PR-AUC** "
            "(raw / after subtracting the subject's own prevalence)\n\n")
    body = []
    for m in C.MODELS:
        cells = []
        for a in ARM_ORDER:
            r = stats.subject_count_correlation(folds, a)
            r = r[r.model == m].iloc[0]
            cells.append("%+.3f / %+.3f" % (r.rho_raw, r.rho_lift))
        body.append([m] + cells)
    o.write(_table(["Model"] + ["Arm %s: raw / minus prevalence" % a for a in ARM_ORDER],
                   body))

    o.write("\n\n**The same relationship as a multiple of chance** "
            "(PR-AUC divided by prevalence), which has the opposite sign\n\n")
    body = []
    for m in C.MODELS:
        cells = []
        for a in ARM_ORDER:
            r = stats.subject_count_correlation(folds, a)
            r = r[r.model == m].iloc[0]
            cells.append("%+.3f (%.4f)" % (r.rho_ratio, r.p_ratio))
        body.append([m] + cells)
    o.write(_table(["Model"] + ["Arm %s" % a for a in ARM_ORDER], body))
    return o.getvalue()


# ------------------------------------------------------------------ section 5
def section_5(folds, pooled):
    o = io.StringIO()
    for a in ARM_ORDER:
        ref = C.arm_reference(a)["brier"]
        o.write("**Arm %s** (class-prior Brier reference %.4f)\n\n" % (a, ref))
        body = []
        for m in C.MODELS:
            r = stats.pooled_row(pooled, a, m)
            brier = r["brier"][0]
            mark = "**%.4f**" % brier if brier > ref else "%.4f" % brier
            body.append([m,
                         "%.4f ± %.4f" % r["auc"],
                         "%.4f ± %.4f" % r["pr_auc"],
                         "%.4f ± %.4f" % r["bal_acc"],
                         mark])
        o.write(_table(["Model", "ROC-AUC", "PR-AUC", "Bal. acc.", "Brier"], body))
        o.write("\n\n")

    o.write("**The partition, with the margin against each arm's own reference**\n\n")
    body = []
    for m in C.MODELS:
        cells, sides = [], []
        for a in ARM_ORDER:
            ref = C.arm_reference(a)["brier"]
            b = stats.pooled_row(pooled, a, m)["brier"][0]
            cells.append("%.4f (%+.4f)" % (b, b - ref))
            sides.append("above" if b > ref else "below")
        verdict = "%s ×%d" % (sides[0], len(sides)) if len(set(sides)) == 1 else " / ".join(sides)
        body.append([m] + cells + [verdict])
    o.write(_table(["Model"] + ["Arm %s (ref %.4f)" % (a, C.arm_reference(a)["brier"])
                                for a in ARM_ORDER] + [""], body))

    o.write("\n\n**ROC-AUC against raw pooled Brier across the five architectures** "
            "(reported only because a reader may compute it)\n\n")
    body = []
    for a in ARM_ORDER:
        r = stats.ranking_vs_reliability(folds, pooled, a)
        body.append([a, "%+.3f (%.4f)" % r["pooled"],
                     "%+.3f (%.4f)" % r["subject_averaged"]])
    o.write(_table(["Arm", "with pooled ROC-AUC", "with subject-averaged ROC-AUC"], body))
    return o.getvalue()


# ------------------------------------------------------------------ section 6
def section_6(folds, pooled, result_dir=None):
    """Recalibration. Reads the per-arm calibration_summary.csv files."""
    result_dir = result_dir or C.RESULT_DIR
    o = io.StringIO()
    found = False
    for a in ARM_ORDER:
        path = os.path.join(result_dir, a, "calibration_summary.csv")
        if not os.path.exists(path):
            continue
        found = True
        s = pd.read_csv(path)
        ref = C.arm_reference(a)["brier"]
        o.write("**Arm %s** (reference %.4f), subject-averaged\n\n" % (a, ref))
        body = [[r.model, "%.4f" % r.ece_raw, "%.4f" % r.ece_platt,
                 "%.4f" % r.ece_isotonic, "%.4f" % r.brier_raw,
                 "%.4f" % r.brier_platt, "%.4f" % r.brier_isotonic]
                for r in s.sort_values("model").itertuples()]
        o.write(_table(["Model", "ECE raw", "ECE + Platt", "ECE + isotonic",
                        "Brier raw", "Brier + Platt", "Brier + isotonic"], body))
        o.write("\n\nAbove the reference: %d of %d raw → %d of %d after Platt scaling.\n\n"
                % (int(s.above_reference_raw.sum()), len(s),
                   int(s.above_reference_platt.sum()), len(s)))

    if not found:
        return "No calibration_summary.csv found. Run python -m src.calibrate first.\n"

    o.write("**Raw against Platt on the ten subject-level differences**\n\n")
    body = []
    for a in ARM_ORDER:
        path = os.path.join(result_dir, a, "calibration_summary.csv")
        if not os.path.exists(path):
            continue
        for r in pd.read_csv(path).sort_values("model").itertuples():
            body.append([a, r.model,
                         "%s (%d/10)" % (_p(r.p_brier), r.n_brier),
                         "%s (%d/10)" % (_p(r.p_ece), r.n_ece)])
    o.write(_table(["Arm", "Model", "Brier", "ECE"], body))
    return o.getvalue()


# ------------------------------------------------------------------ section 7
def section_7(folds, pooled, result_dir=None):
    """Threshold selection. Reads the per-arm threshold_summary.csv files."""
    from src.thresholds import classify
    result_dir = result_dir or C.RESULT_DIR
    o = io.StringIO()
    gains = losses = tests = 0
    found = False

    for a in ARM_ORDER:
        path = os.path.join(result_dir, a, "threshold_summary.csv")
        if not os.path.exists(path):
            continue
        found = True
        s = pd.read_csv(path)
        o.write("**Arm %s**\n\n" % a)
        body = []
        for r in s.sort_values(["model", "rule"]).itertuples():
            v = classify(r)
            gains += sum(x == "gain" for x in v.values())
            losses += sum(x == "loss" for x in v.values())
            tests += 2
            body.append([r.model,
                         "F1-optimal" if r.rule == "sel-F1" else "BA-optimal",
                         "%.3f → %.3f, %s" % (r.ba_fixed, r.ba_sel, _p(r.p_ba)),
                         "%.3f → %.3f, %s" % (r.f1_fixed, r.f1_sel, _p(r.p_f1))])
        o.write(_table(["Model", "Rule", "Balanced accuracy", "F1"], body))
        o.write("\n\n")

    if not found:
        return "No threshold_summary.csv found. Run python -m src.thresholds first.\n"

    o.write("Across the %d tests: %d significant gains, %d significant losses.\n\n"
            % (tests, gains, losses))
    o.write("**The selected thresholds themselves**\n\n")
    body = []
    for a in ARM_ORDER:
        path = os.path.join(result_dir, a, "threshold_summary.csv")
        if not os.path.exists(path):
            continue
        for model, g in pd.read_csv(path).groupby("model"):
            r = g.iloc[0]
            body.append([a, model, "%.4f ± %.4f" % (r.thr_f1_mean, r.thr_f1_sd),
                         "%.4f ± %.4f" % (r.thr_ba_mean, r.thr_ba_sd)])
    o.write(_table(["Arm", "Model", "F1-optimal threshold",
                    "Balanced-accuracy-optimal threshold"], body))
    return o.getvalue()


SECTIONS = {
    "1": ("Architecture comparison", section_1),
    "1a": ("Arms A and C isolate balancing", section_1a),
    "1b": ("Arms B and C isolate trimming", section_1b),
    "2": ("The CNN / CNN-BiLSTM ablation", section_2),
    "3": ("Pooled confusion matrices", section_3),
    "3a": ("Recall conventions and degenerate folds", section_3a),
    "4": ("Between-subject variation", section_4),
    "5": ("Probability reliability", section_5),
    "6": ("Out-of-subject recalibration", section_6),
    "7": ("Threshold selection", section_7),
}


def render(which=None, result_dir=None):
    result_dir = result_dir or C.RESULT_DIR
    folds, pooled = aggregate.load(result_dir)
    stats.assert_consistent(folds, pooled)
    out = io.StringIO()
    for key in (which or list(SECTIONS)):
        if key not in SECTIONS:
            raise SystemExit("unknown section %r; expected one of %s"
                             % (key, list(SECTIONS)))
        title, fn = SECTIONS[key]
        out.write("## %s. %s\n\n" % (key, title))
        try:
            out.write(fn(folds, pooled, result_dir))
        except TypeError:
            out.write(fn(folds, pooled))
        out.write("\n\n")
    return out.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", default=None, metavar="SECTION")
    ap.add_argument("--out", default=None)
    ap.add_argument("--result-dir", default=None)
    a = ap.parse_args(argv)
    text = render(a.only, a.result_dir)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(text)
        print("wrote", a.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
