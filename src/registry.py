"""Build MASTER_NUMBERS.csv, the list of every value the manuscript may cite.

    python -m src.registry

The rule this enforces: **a number enters the manuscript only if it appears in
MASTER_NUMBERS.csv, and this script is re-run on the day of any edit.**
src/scan.py then reads a draft and reports any number in it that is not here.

Every row is computed from the raw result files at the moment this runs.
Nothing is copied from a document, because a registry that was typed in would
only prove that the typing was self-consistent.

Columns:
  section   which analysis the value belongs to
  claim     an English description precise enough to be looked up
  value     the number
  note      provenance, a p-value, a count of subjects, or a comparison
"""

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src import aggregate, stats  # noqa: E402

ARM_ORDER = ["A", "B", "C"]


def _r(section, claim, value, note="", places=4):
    if isinstance(value, (np.floating, float)):
        value = round(float(value), places)
    elif isinstance(value, (np.integer,)):
        value = int(value)
    return dict(section=section, claim=claim, value=value, note=note)


def dataset_rows():
    out = [_r("data", "folds in ALL_FOLDS", C.total_folds()),
           _r("data", "folds per arm", C.folds_per_arm()),
           _r("data", "architectures", len(C.MODELS)),
           _r("data", "seeds", len(C.SEEDS)),
           _r("data", "subjects", C.N_SUBJECTS),
           _r("data", "window length samples", C.WIN, "%.0f s at %.0f Hz"
              % (C.WIN_SEC, C.FS)),
           _r("stats", "smallest attainable Wilcoxon p on ten pairs",
              C.P_FLOOR_WILCOXON_10, "2 / 2^10 = 1/512", places=8),
           _r("stats", "smallest attainable Spearman p on five points",
              C.P_FLOOR_SPEARMAN_5)]
    for a in ARM_ORDER:
        spec, ref = C.ARMS[a], C.arm_reference(a)
        out += [
            _r("data", "Arm %s windows" % a, spec["n_windows"], spec["label"]),
            _r("data", "Arm %s windows per subject" % a, spec["n_per_subject"]),
            _r("data", "Arm %s drowsy windows" % a, spec["n_drowsy"]),
            _r("data", "Arm %s alert windows" % a, spec["n_windows"] - spec["n_drowsy"]),
            _r("data", "Arm %s prevalence percent" % a, 100 * ref["prevalence"]),
            _r("data", "Arm %s class-prior Brier reference" % a, ref["brier"],
               "pi*(1-pi)"),
            _r("data", "Arm %s PR-AUC chance level" % a, ref["pr_auc"], "the prior"),
            _r("data", "Arm %s always-alert accuracy percent" % a, ref["accuracy"]),
            # Also registered at the two decimal places the manuscript prints.
            # Without this row, a sentence quoting "92.73 %" passes scan.py only
            # because some unrelated row happens to carry the same string — which
            # is a pass by coincidence, not by audit.
            _r("data", "Arm %s always-alert accuracy percent, 2 dp" % a,
               round(ref["accuracy"], 2), "as printed in the manuscript"),
        ]
        for s, n in spec["per_subject_drowsy"].items():
            out.append(_r("data", "Arm %s %s drowsy windows" % (a, s), n))
    for m in C.MODELS:
        out.append(_r("model", "%s trainable parameters" % m, C.PARAMS[m]))
    # The two ratios the prose quotes. Registered rather than typed, because a
    # derived ratio drifts exactly like a derived count: the manuscript said the
    # ADDED parameters were "four times the CNN's total" in three places, where
    # 135,936 / 44,705 is 3.04 and it is the CNN-BiLSTM TOTAL that is 4.04 times.
    out.append(_r("model", "CNN-BiLSTM added parameters as a multiple of the CNN",
                  (C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"]) / C.PARAMS["CNN"],
                  "135,936 / 44,705", places=2))
    out.append(_r("model", "CNN-BiLSTM total parameters as a multiple of the CNN",
                  C.PARAMS["CNN-BiLSTM"] / C.PARAMS["CNN"],
                  "180,641 / 44,705", places=2))
    out.append(_r("model", "CNN-BiLSTM minus CNN trainable parameters",
                  C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"], "the recurrent block's cost"))
    return out


def per_model_rows(folds, pooled):
    out = []
    for a in ARM_ORDER:
        for m in C.MODELS:
            for col in ("auc", "pr_auc", "bal_acc", "f1", "precision", "recall"):
                mu, sd = stats.subject_averaged(folds, a, m, col)
                out.append(_r("results", "Arm %s %s %s SUBJECT-AVERAGED" % (a, m, col), mu))
                out.append(_r("results", "Arm %s %s %s seed SD" % (a, m, col), sd))
            for col, (mu, sd) in stats.pooled_row(pooled, a, m).items():
                out.append(_r("pooled", "Arm %s %s %s POOLED" % (a, m, col), mu))
                out.append(_r("pooled", "Arm %s %s %s pooled seed SD" % (a, m, col), sd))
            # The extreme single-seed pooled Brier, so that an outlying seed can be
            # named in the text. Arm B ShallowConvNet reaches 0.2246 on one seed
            # against about 0.11 on the other four, which is the kind of fact a
            # figure's error bar shows and a caption should be able to quote.
            per_seed = pooled[(pooled.arm == C.ARMS[a]["npz"].replace(".npz", ""))
                              | (pooled.arm.str.startswith(a + "_"))]
            per_seed = per_seed[per_seed.model == m]["brier"]
            if len(per_seed):
                out.append(_r("pooled", "Arm %s %s smallest single-seed pooled Brier"
                              % (a, m), per_seed.min()))
                out.append(_r("pooled", "Arm %s %s largest single-seed pooled Brier"
                              % (a, m), per_seed.max(),
                              "over the %d seeds" % len(per_seed)))
            ref = C.arm_reference(a)["brier"]
            b = stats.pooled_row(pooled, a, m)["brier"][0]
            out.append(_r("pooled", "Arm %s %s pooled Brier margin over reference" % (a, m),
                          b - ref, "Brier %.4f, reference %.4f" % (b, ref)))
            for col in ("pr_auc", "recall", "auc"):
                for s, v in stats.subject_means(folds, a, m, col).items():
                    out.append(_r("subject", "Arm %s %s %s %s" % (a, m, s, col), v))
    return out


def comparison_rows(folds):
    out = []
    for a in ARM_ORDER:
        pw = stats.all_pairwise(folds, a, "auc")
        for r in pw.itertuples():
            out.append(_r("stats", "Arm %s %s vs %s ROC-AUC p" % (a, r.a, r.b), r.p,
                          "%d/%d for %s%s" % (
                              r.a_wins, r.n, r.a,
                              "" if not r.ties else
                              "; %d tied, so %d pair(s) tested, floor %.6f"
                              % (r.ties, r.n_effective, r.p_floor))))
        non = pw[(pw.a != "EEGNet") & (pw.b != "EEGNet")]
        out.append(_r("stats", "Arm %s smallest p among non-EEGNet ROC-AUC pairs" % a,
                      non.p.min(), "%d of %d significant"
                      % (int((non.p < 0.05).sum()), len(non))))
        # The manuscript's "eleven of twelve paired comparisons" is spelled out in
        # words, so scan.py never sees a digit and cannot check it.  Register both
        # counts so the claim is traceable to a row rather than to a sentence.
        eeg = pw[(pw.a == "EEGNet") | (pw.b == "EEGNet")]
        out.append(_r("stats", "Arm %s EEGNet ROC-AUC pairs significant" % a,
                      int((eeg.p < 0.05).sum()), "of %d pairs involving EEGNet" % len(eeg)))
        out.append(_r("stats", "Arm %s EEGNet ROC-AUC pairs tested" % a, len(eeg)))
        for r in stats.ablation(folds, a).itertuples():
            # b_wins is counted strictly. Deriving it as n - a_wins counted a tied
            # subject as an improvement, which is how this row said 10/10 where the
            # manuscript correctly said 9/10. Where a tie exists the note also says
            # so, because the test then runs on fewer than ten pairs.
            note = "%.4f -> %.4f, %d/%d improved" % (r.mean_a, r.mean_b,
                                                     r.b_wins, r.n)
            if r.ties:
                note += "; %d tied, so %d pair(s) tested, floor %.6f" % (
                    r.ties, r.n_effective, r.p_floor)
            out.append(_r("stats", "Arm %s CNN vs CNN-BiLSTM %s p" % (a, r.metric),
                          r.p, note))
        cc = stats.capacity_correlation(folds, a)
        out.append(_r("stats", "Arm %s rho parameters vs ROC-AUC" % a, cc["rho"],
                      "p=%.4f" % cc["p"]))
        out.append(_r("stats", "Arm %s p for parameters vs ROC-AUC" % a, cc["p"]))
        for r in stats.subject_count_correlation(folds, a).itertuples():
            out.append(_r("stats", "Arm %s %s rho drowsy count vs PR-AUC raw"
                          % (a, r.model), r.rho_raw, "p=%.4f" % r.p_raw))
            out.append(_r("stats", "Arm %s %s rho drowsy count vs PR-AUC minus prevalence"
                          % (a, r.model), r.rho_lift, "p=%.4f" % r.p_lift))
            out.append(_r("stats", "Arm %s %s rho drowsy count vs PR-AUC over prevalence"
                          % (a, r.model), r.rho_ratio, "p=%.4f" % r.p_ratio))
            for tag, p in (("raw", r.p_raw), ("minus prevalence", r.p_lift),
                           ("over prevalence", r.p_ratio)):
                out.append(_r("stats", "Arm %s %s p drowsy count vs PR-AUC %s"
                              % (a, r.model, tag), p))

    for col in ("auc", "pr_auc", "bal_acc", "f1"):
        for r in stats.cross_arm_ordering(folds, col).itertuples():
            out.append(_r("stats", "%s-%s ordering agreement %s" % (r.arm_a, r.arm_b, col),
                          r.rho, "p=%.4f" % r.p))
            # As a value, not only in the note. src/scan.py reads values and not
            # notes, so a p held only in a note cannot be printed in the manuscript
            # -- which is part of why this was the one correlation table in the
            # paper with no p column.
            out.append(_r("stats", "%s-%s ordering agreement %s p"
                          % (r.arm_a, r.arm_b, col), r.p))

    # Two controlled contrasts, each isolating one construction choice.
    #   A vs C : both trimmed, balancing differs      -> isolates balancing
    #   B vs C : both proportional, trimming differs  -> isolates trimming
    for x, y, factor in (("A", "C", "balancing"), ("B", "C", "trimming")):
        for col in ("auc", "pr_auc", "bal_acc", "f1"):
            for r in stats.arm_contrast(folds, x, y, col).itertuples():
                out.append(_r("stats", "%s vs %s %s %s p" % (x, y, r.model, col), r.p,
                              "%s isolated; %.4f -> %.4f, %d/%d higher on %s%s"
                              % (factor, r.mean_a, r.mean_b, r.b_higher, r.n, y,
                                 "" if not r.ties else
                                 "; %d tied, so %d pair(s) tested, floor %.6f"
                                 % (r.ties, r.n_effective, r.p_floor))))
                out.append(_r("stats", "%s vs %s %s %s delta" % (x, y, r.model, col),
                              r.delta))
        sig = sum(int(r.p < 0.05)
                  for col in ("auc", "pr_auc", "bal_acc", "f1")
                  for r in stats.arm_contrast(folds, x, y, col).itertuples())
        smallest = min(r.p
                       for col in ("auc", "pr_auc", "bal_acc", "f1")
                       for r in stats.arm_contrast(folds, x, y, col).itertuples())
        out.append(_r("stats", "%s vs %s significant tests of twenty" % (x, y), sig,
                      "%s isolated" % factor))
        out.append(_r("stats", "%s vs %s smallest p over twenty tests" % (x, y),
                      smallest, "%s isolated" % factor))

    sig = [(r.rho_lift, r.p_lift)
           for a in ARM_ORDER
           for r in stats.subject_count_correlation(folds, a).itertuples()
           if r.p_lift < 0.05]
    total = len(ARM_ORDER) * len(C.MODELS)
    out += [_r("stats", "significant prevalence-corrected correlations",
               "%d of %d" % (len(sig), total)),
            _r("stats", "minimum rho among the significant prevalence-corrected "
               "correlations", min(x[0] for x in sig)),
            _r("stats", "maximum p among the significant prevalence-corrected "
               "correlations", max(x[1] for x in sig))]
    return out


def threshold_metric_rows(folds, pooled):
    out = []
    for a in ARM_ORDER:
        cm = stats.pooled_confusion(folds, a, pooled)
        for r in cm.itertuples():
            for field in ("tn", "fp", "fn", "tp"):
                out.append(_r("confusion", "Arm %s %s %s" % (a, r.model, field.upper()),
                              round(getattr(r, field))))
            out.append(_r("confusion", "Arm %s %s pooled recall" % (a, r.model), r.recall))
            out.append(_r("confusion", "Arm %s %s pooled precision" % (a, r.model),
                          r.precision))
            out.append(_r("confusion", "Arm %s %s pooled accuracy percent" % (a, r.model),
                          r.accuracy))
        # Seed dispersion for the three pooled quantities Table 5 prints. It was
        # absent while every column of the tables beside it carried a seed SD, and
        # the omission hid the largest instability in the study: ShallowConvNet on
        # Arm B is 81.85 % with an SD of 6.22 points, one seed at 70.88 %.
        for r in stats.pooled_confusion_spread(folds, a, pooled).itertuples():
            for col, label in (("accuracy", "pooled accuracy percent"),
                               ("recall", "pooled recall"),
                               ("precision", "pooled precision")):
                out.append(_r("confusion", "Arm %s %s %s seed SD" % (a, r.model, label),
                              getattr(r, "%s_sd" % col)))
                out.append(_r("confusion",
                              "Arm %s %s smallest single-seed %s" % (a, r.model, label),
                              getattr(r, "%s_min" % col)))
                out.append(_r("confusion",
                              "Arm %s %s largest single-seed %s" % (a, r.model, label),
                              getattr(r, "%s_max" % col),
                              "over the %d seeds" % int(r.n_seeds)))
        avr = stats.accuracy_vs_recall(folds, a, pooled)
        if a == ARM_ORDER[-1]:
            # The one row Section 7.3 singles out, and the bound it is measured
            # against. Registered rather than typed, so the sentence naming it
            # cannot outlive the fact.
            sds = {(x, r.model): float(r.accuracy_sd)
                   for x in ARM_ORDER
                   for r in stats.pooled_confusion_spread(folds, x, pooled).itertuples()}
            worst = max(sds, key=sds.get)
            rest = max(v for k, v in sds.items() if k != worst)
            out += [
                _r("confusion", "largest pooled accuracy seed SD",
                   sds[worst], "Arm %s %s" % worst),
                _r("confusion", "largest pooled accuracy seed SD elsewhere", rest,
                   "every other architecture-by-arm cell is below this"),
            ]
        # The p is the EXACT two-sided permutation p over the 120 orderings of
        # five ranks (see stats.spearman), so it cannot fall below the attainable
        # floor and needs no cap.  It used to come from scipy's t-approximation
        # and was then capped at the floor here -- which fixed the one claim that
        # ran past the floor and left three other five-point families reporting
        # approximated p-values, one of them p = 0.0000 from five points.
        note = "p=%.4f, five architectures, exact permutation p" % avr["p"]
        out.append(_r("confusion", "Arm %s Spearman pooled accuracy vs pooled recall" % a,
                      avr["rho"], note))
        # Registered as a value of its own, not only inside the note above, so the
        # manuscript may quote the p as well as the rho and the scanner can check it.
        out.append(_r("confusion",
                      "Arm %s p for Spearman pooled accuracy vs pooled recall" % a,
                      avr["p"], "exact permutation p over 120 orderings"))
        best = cm.iloc[0]
        eeg = cm[cm.model == "EEGNet"].iloc[0]
        out.append(_r("confusion", "Arm %s most accurate minus EEGNet accuracy points" % a,
                      round(best.accuracy - eeg.accuracy, 1),
                      "%s %.2f %% against EEGNet %.2f %%"
                      % (best.model, best.accuracy, eeg.accuracy)))

        for r in stats.recall_conventions(folds, a).itertuples():
            # `per_model_rows` already emitted this same claim, computed by a
            # different route (stats.subject_averaged over the metric loop).  Two
            # rows with one key is a defect in a registry whose whole purpose is
            # one row per claim, so the duplicate is dropped -- but the agreement
            # between the two routes is worth keeping, so it becomes an assertion
            # instead of a row.  If the two ever diverge this raises here rather
            # than silently publishing whichever row a lookup happened to find.
            mu, _ = stats.subject_averaged(folds, a, r.model, "recall")
            assert abs(mu - r.subject_averaged) < 5e-5, (
                "Arm %s %s subject-averaged recall disagrees between "
                "stats.subject_averaged (%.6f) and stats.recall_conventions (%.6f)"
                % (a, r.model, mu, r.subject_averaged))
            out.append(_r("results", "Arm %s %s recall POOLED" % (a, r.model), r.pooled))
            out.append(_r("results", "Arm %s %s pooled minus subject-averaged recall"
                          % (a, r.model), r.difference))

        deg = stats.degenerate_folds(folds, a)
        for m, n in deg.items():
            out.append(_r("results", "Arm %s %s degenerate folds" % (a, m), n,
                          "of %d" % (len(C.SEEDS) * C.N_SUBJECTS)))

        sp = stats.spread_ratio(folds, a, "pr_auc")
        for r in sp.itertuples():
            out.append(_r("spread", "Arm %s %s subject SD of PR-AUC" % (a, r.model),
                          r.subject_sd))
            out.append(_r("spread", "Arm %s %s seed SD of PR-AUC" % (a, r.model),
                          r.seed_sd))
            out.append(_r("spread", "Arm %s %s subject to seed SD ratio" % (a, r.model),
                          r.ratio))
        out.append(_r("spread", "Arm %s minimum subject to seed SD ratio" % a,
                      sp.ratio.min()))
        out.append(_r("spread", "Arm %s maximum subject to seed SD ratio" % a,
                      sp.ratio.max()))
        rng = stats.subject_range(folds, a, "pr_auc")
        out.append(_r("spread", "Arm %s minimum subject PR-AUC over architectures" % a,
                      rng["min"], rng["min_subject"]))
        out.append(_r("spread", "Arm %s maximum subject PR-AUC over architectures" % a,
                      rng["max"], rng["max_subject"]))

        rr = stats.ranking_vs_reliability(folds, pooled, a)
        for tag, (rho, p) in rr.items():
            out.append(_r("stats", "Arm %s rho ROC-AUC (%s) vs pooled Brier" % (a, tag),
                          rho, "p=%.4f" % p))
            out.append(_r("stats", "Arm %s p for ROC-AUC (%s) vs pooled Brier"
                          % (a, tag), p))

        # gaps between adjacent architectures, so a draft may cite one
        order = sorted(C.MODELS,
                       key=lambda m: stats.subject_averaged(folds, a, m, "auc")[0],
                       reverse=True)
        for x, y in zip(order, order[1:]):
            gap = (stats.subject_averaged(folds, a, x, "auc")[0]
                   - stats.subject_averaged(folds, a, y, "auc")[0])
            out.append(_r("results", "Arm %s %s minus %s subject-averaged ROC-AUC"
                          % (a, x, y), gap))
    return out


def posthoc_rows(result_dir):
    """Calibration and threshold-selection values, if those analyses have been run."""
    out = []
    for a in ARM_ORDER:
        cal = os.path.join(result_dir, a, "calibration_summary.csv")
        if os.path.exists(cal):
            s = pd.read_csv(cal)
            for r in s.itertuples():
                for kind in ("raw", "platt", "isotonic"):
                    out.append(_r("calib", "Arm %s %s %s ECE SUBJECT-AVERAGED"
                                  % (a, r.model, kind), getattr(r, "ece_%s" % kind)))
                    out.append(_r("calib", "Arm %s %s %s Brier SUBJECT-AVERAGED"
                                  % (a, r.model, kind), getattr(r, "brier_%s" % kind)))
                out.append(_r("calib", "Arm %s %s raw vs platt Brier p" % (a, r.model),
                              r.p_brier, "%d/10 improved" % r.n_brier))
                out.append(_r("calib", "Arm %s %s raw vs platt ECE p" % (a, r.model),
                              r.p_ece, "%d/10 improved" % r.n_ece))
            out.append(_r("calib", "Arm %s architectures above the reference raw" % a,
                          "%d of %d" % (int(s.above_reference_raw.sum()), len(s))))
            out.append(_r("calib", "Arm %s architectures above the reference after platt"
                          % a, "%d of %d" % (int(s.above_reference_platt.sum()), len(s))))
            best = s.loc[s.ece_raw.idxmin()]
            eeg = s[s.model == "EEGNet"]
            if len(eeg):
                out.append(_r("calib", "Arm %s EEGNet ECE as a multiple of the "
                              "best-calibrated architecture" % a,
                              round(float(eeg.ece_raw.iloc[0]) / float(best.ece_raw), 1),
                              "best is %s" % best.model))

        agr = os.path.join(result_dir, a, "reproducibility_agreement.csv")
        if os.path.exists(agr):
            for r in pd.read_csv(agr).itertuples():
                for col in ("bal_acc", "f1", "recall"):
                    out.append(_r("repro", "Arm %s %s folds identical on %s between runs"
                                  % (a, r.model, col),
                                  int(getattr(r, "identical_%s" % col)),
                                  "of %d" % int(r.n_folds)))
                for col in ("auc", "pr_auc", "bal_acc"):
                    out.append(_r("repro", "Arm %s %s run 1 mean %s" % (a, r.model, col),
                                  getattr(r, "mean_1_%s" % col)))
                    out.append(_r("repro", "Arm %s %s run 2 mean %s" % (a, r.model, col),
                                  getattr(r, "mean_2_%s" % col)))

        rep = os.path.join(result_dir, a, "reproducibility.csv")
        if os.path.exists(rep):
            for r in pd.read_csv(rep).itertuples():
                # A run that differs from its predecessor in nothing at all, down to
                # the bit, on a GPU that is not deterministic, was not re-executed:
                # the file was carried over. src/repro.py excludes these from its
                # verdict. The registry did not, so eight rows advertised CNN and
                # CNN-BiLSTM as "50 of 50 identical" -- perfect reproducibility --
                # for two architectures that were never independently run. The
                # manuscript never made that claim; the released registry did.
                carried = (float(r.largest_fold_difference) == 0.0
                           and int(r.folds_bit_identical) == int(r.n_folds))
                caveat = ("; NOT an independent re-execution -- every fold is "
                          "bit-identical, so this file was carried over"
                          if carried else "")
                out.append(_r("repro", "Arm %s %s run 1 mean ROC-AUC" % (a, r.model),
                              r.mean_1))
                out.append(_r("repro", "Arm %s %s run 2 mean ROC-AUC" % (a, r.model),
                              r.mean_2))
                out.append(_r("repro", "Arm %s %s largest single-fold ROC-AUC difference"
                              % (a, r.model), r.largest_fold_difference))
                out.append(_r("repro", "Arm %s %s folds identical between runs"
                              % (a, r.model), int(r.folds_identical),
                              "of %d, to within 1e-12%s" % (int(r.n_folds), caveat)))
                out.append(_r("repro", "Arm %s %s folds bit-identical between runs"
                              % (a, r.model), int(r.folds_bit_identical),
                              "of %d%s" % (int(r.n_folds), caveat)))
                for col in ("auc", "f1"):
                    out.append(_r("repro", "Arm %s %s largest subject-level %s shift "
                                  "between runs" % (a, r.model, col),
                                  getattr(r, "max_subject_shift_%s" % col)))
                    out.append(_r("repro", "Arm %s %s overall %s shift between runs"
                                  % (a, r.model, col),
                                  getattr(r, "overall_shift_%s" % col)))
                    out.append(_r("repro", "Arm %s %s seed SD of %s"
                                  % (a, r.model, col),
                                  getattr(r, "seed_sd_%s" % col)))

        thr = os.path.join(result_dir, a, "threshold_summary.csv")
        if os.path.exists(thr):
            for r in pd.read_csv(thr).itertuples():
                out.append(_r("thresh", "Arm %s %s %s bal_acc p" % (a, r.model, r.rule),
                              r.p_ba, "%.3f -> %.3f" % (r.ba_fixed, r.ba_sel)))
                out.append(_r("thresh", "Arm %s %s %s F1 p" % (a, r.model, r.rule),
                              r.p_f1, "%.3f -> %.3f" % (r.f1_fixed, r.f1_sel)))
                for field in ("ba_fixed", "ba_sel", "f1_fixed", "f1_sel",
                              "thr_f1_mean", "thr_f1_sd", "thr_ba_mean", "thr_ba_sd"):
                    out.append(_r("thresh", "Arm %s %s %s %s"
                                  % (a, r.model, r.rule, field), getattr(r, field)))
    return out


def multiplicity_rows(folds, pooled, result_dir):
    """Every number the multiplicity section may cite.

    The denominator this registers -- 190 -- is the one quantity in that section
    that is not a judgement call: it is what the pipeline runs. Three different
    counts were in circulation before this existed (175-181, 117, 163), none of
    which counted the same thing, so it is computed here rather than stated.
    """
    from src import multiplicity as M
    frame = M.table(folds, pooled, result_dir)
    out = [_r("multiplicity", "nominal significance level", C.ALPHA)]

    for r in frame[frame.scope == "family"].itertuples():
        out += [
            _r("multiplicity", "%s comparisons" % r.name, r.n_tests),
            _r("multiplicity", "%s at nominal level" % r.name, r.n_nominal),
            _r("multiplicity", "%s surviving BH" % r.name, r.n_bh),
            _r("multiplicity", "%s surviving BY" % r.name, r.n_by),
        ]
    for r in frame[frame.scope == "summary"].itertuples():
        out += [
            _r("multiplicity", "%s, tests performed" % r.name, r.n_tests),
            _r("multiplicity", "%s, at nominal level" % r.name, r.n_nominal),
            _r("multiplicity", "%s, surviving BH" % r.name, r.n_bh),
            _r("multiplicity", "%s, surviving BY" % r.name, r.n_by),
            # The reference count under a single global null. Descriptive context
            # for the disclosure, NOT a test: the comparisons are dependent and
            # were not generated under one global-null experiment.
            _r("multiplicity", "%s, global-null reference count" % r.name,
               C.ALPHA * r.n_tests, "alpha x number of comparisons", places=2),
        ]

    out += [
        _r("multiplicity", "analysis families", int((frame.scope == "family").sum())),
        # Where every BY survivor of the one-family analysis comes from. Without
        # this the row reads as "nothing in this paper survives"; with it, it reads
        # as "the correction is dominated by one family of 45".
        _r("multiplicity", "one-family BY survivors from the prevalence family",
           int(frame[(frame.scope == "summary")
                     & (frame.name == "all registered comparisons")].n_by.iloc[0])),
        # The floors, and the family size past which Holm cannot reject at all.
        _r("multiplicity", "smallest attainable Wilcoxon p on nine pairs",
           2.0 / 2 ** 9, "one tied subject leaves nine non-zero differences",
           places=9),
        _r("multiplicity", "Holm family ceiling for the ten-pair Wilcoxon floor",
           C.holm_family_ceiling(C.P_FLOOR_WILCOXON_10),
           "beyond this m, alpha/m falls below the floor"),
        _r("multiplicity", "Holm family ceiling for the nine-pair Wilcoxon floor",
           C.holm_family_ceiling(2.0 / 2 ** 9)),
        _r("multiplicity", "Holm family ceiling for the five-point Spearman floor",
           C.holm_family_ceiling(C.P_FLOOR_SPEARMAN_5),
           "2/5! and alpha/3 are both 1/60, so this boundary is an equality"),
    ]
    return out


def raw_count_rows(result_dir):
    """The per-subject window counts before any balancing, with a verification.

    These come from the preprocessing run, not from ALL_FOLDS.csv, so they cannot
    be recomputed without the EDF files. They can, however, be CHECKED: applying
    the proportional rule to them must reproduce Arm B's per-subject drowsy counts
    exactly, because Arm B is untrimmed and its budget is the smallest subject
    total. If that check fails the table is wrong and the rows are not emitted.
    """
    from src.preprocess import keep_drowsy_count
    path = os.path.join(result_dir, "raw_window_counts.csv")
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path).set_index("subject")
    budget = int(df.windows.min())
    if budget != C.ARMS["B"]["n_per_subject"]:
        raise AssertionError("raw counts give budget %d, Arm B uses %d"
                             % (budget, C.ARMS["B"]["n_per_subject"]))
    for s, want in C.ARMS["B"]["per_subject_drowsy"].items():
        got = keep_drowsy_count(int(df.loc[s, "drowsy"]), int(df.loc[s, "windows"]),
                                budget, "proportional")
        if got != want:
            raise AssertionError("raw counts do not reproduce Arm B for %s: %d vs %d"
                                 % (s, got, want))

    lens = os.path.join(result_dir, "recording_lengths.csv")
    extra_rows = []
    if os.path.exists(lens):
        L = pd.read_csv(lens).set_index("quantity")
        short = int(L.loc["shortest_recording", "value"])
        long_ = int(L.loc["longest_recording", "value"])
        total = float(L.loc["total_recorded_signal", "value"])
        extra_rows = [
            _r("data", "shortest recording samples", short, "the trim target"),
            _r("data", "longest recording samples", long_),
            _r("data", "shortest recording hours", short / C.FS / 3600, places=3),
            _r("data", "longest recording hours", long_ / C.FS / 3600, places=3),
            _r("data", "total recorded signal hours", total, "untrimmed"),
            _r("data", "trimmed total signal hours",
               20 * short / C.FS / 3600, "twenty recordings at the trim length",
               places=1),
        ]

    out = extra_rows + [_r("data", "smallest subject window total before balancing", budget,
              "the per-subject budget; equals Arm B windows per subject"),
           _r("data", "drowsy windows before balancing, all subjects",
              int(df.drowsy.sum()), "untrimmed"),
           _r("data", "drowsy windows lost to trimming in Arm A",
              int(df.drowsy.sum()) - C.ARMS["A"]["n_drowsy"], "")]
    for s in C.SUBJECTS:
        r = df.loc[s]
        out += [_r("data", "%s windows before balancing" % s, int(r.windows)),
                _r("data", "%s drowsy windows before balancing" % s, int(r.drowsy)),
                _r("data", "%s alert windows before balancing" % s, int(r.alert)),
                _r("data", "%s prevalence before balancing percent" % s,
                   float(r.prevalence_percent), places=2)]
    return out


def pooled_ece_rows(result_dir):
    """Pooled ECE, if released. It is systematically smaller than the
    subject-averaged value because one subject's over-confidence cancels
    another's, so it is registered under an explicit POOLED label and never
    mixed with the subject-averaged column."""
    path = os.path.join(result_dir, "pooled_ece.csv")
    if not os.path.exists(path):
        return []
    return [_r("calib", "Arm %s %s %s ECE POOLED" % (r.arm, r.model, r.cal),
               r.ece_pooled, "not comparable with the subject-averaged column")
            for r in pd.read_csv(path).itertuples()]


def release_size_rows(result_dir):
    """Facts about what the release physically contains.

    The data-availability statement quotes the size and file count of the released
    probability files. Those are claims about the release like any other and are
    measured from it rather than remembered, so that shrinking or growing the
    release cannot silently falsify the statement.
    """
    out = []
    for arm in ARM_ORDER:
        paths = sorted(glob.glob(os.path.join(result_dir, arm, "probs_*.npz")))
        if not paths:
            continue
        mb = sum(os.path.getsize(p) for p in paths) / (1024.0 * 1024.0)
        out.append(_r("data", "Arm %s probability files released" % arm, len(paths)))
        out.append(_r("data", "Arm %s probability files released, megabytes" % arm,
                      round(mb, 1), "measured from the release", places=1))
    return out


def monotonicity_rows(result_dir):
    """What recalibration measurably did to the ranking metrics.

    The manuscript claims Platt scaling leaves ROC-AUC and PR-AUC unchanged
    because its map is strictly increasing.  That holds only if every fitted
    slope is positive, which is a property of the fits and was not recorded
    anywhere.  `tools/check_monotonicity.py` measures it; this reads the file it
    writes, so the claim is backed by a registry row like every other number.

    Absent file, no rows -- the claim must then be softened in the text.
    """
    path = os.path.join(result_dir, "monotonicity.csv")
    if not os.path.exists(path):
        return []
    out = []
    # Read as text. These values are written by the measuring tool in the exact
    # decimal form the manuscript prints, and letting pandas parse then re-round
    # them turns 0.0000397267 into 4e-05, which no sentence in the paper matches.
    for r in pd.read_csv(path, dtype=str).fillna("").itertuples():
        out.append(dict(section="calib", claim="Arm %s %s" % (r.arm, r.claim),
                        value=r.value, note=r.note))
    return out


def ranking_invariance_rows(result_dir):
    """What recalibration did to the ranking metrics AT THE REPORTED AGGREGATION.

    `monotonicity_rows` above records the largest movement in any single fold.
    That is the right quantity for asking whether the map reorders scores, and
    the wrong one for asking whether a printed table moves: the tables print an
    average over fifty folds, and an average absorbs a per-fold movement. The
    paper argued the second question from the first, and the justification was
    false for PR-AUC as a result.

    `tools/check_ranking_invariance.py` measures the quantity the tables print --
    subject-averaged, the aggregation of Table 4 and Section 7.1 -- and this reads
    the file it writes.

    Absent file, no rows, and the claim must then be softened in the text.
    """
    path = os.path.join(result_dir, "ranking_invariance.csv")
    if not os.path.exists(path):
        return []
    out = []
    # Text, not floats: 0.0000009981 must survive into the registry in the decimal
    # form a sentence can quote, and pandas would hand back 9.981e-07.
    for r in pd.read_csv(path, dtype=str).fillna("").itertuples():
        out.append(dict(section="calib", claim="Arm %s %s" % (r.arm, r.claim),
                        value=r.value, note=r.note))
    return out


def build(result_dir=None, out_path=None, verbose=True):
    result_dir = result_dir or C.RESULT_DIR
    out_path = out_path or C.REGISTRY_CSV
    folds, pooled = aggregate.load(result_dir)
    stats.assert_consistent(folds, pooled)

    rows = (dataset_rows()
            + per_model_rows(folds, pooled)
            + comparison_rows(folds)
            + threshold_metric_rows(folds, pooled)
            + posthoc_rows(result_dir)
            + pooled_ece_rows(result_dir)
            + monotonicity_rows(result_dir)
            + ranking_invariance_rows(result_dir)
            + release_size_rows(result_dir)
            + raw_count_rows(result_dir)
            + multiplicity_rows(folds, pooled, result_dir))
    df = pd.DataFrame(rows)
    # the registry's own row count, so a draft may cite it
    df = pd.concat([df, pd.DataFrame([_r("data", "rows in MASTER_NUMBERS.csv",
                                         len(df) + 1,
                                         "self-referential; counts this row")])],
                   ignore_index=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    df.to_csv(out_path, index=False)
    if verbose:
        print("wrote %s: %d rows" % (out_path, len(df)))
        print(df.section.value_counts().to_string())
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--result-dir", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    build(a.result_dir, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
