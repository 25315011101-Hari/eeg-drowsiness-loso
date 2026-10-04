"""Generate the Master Paper Information File from the registry.

    python3 tools/master_file.py        # writes manuscript/MASTER_FILE.md

A master information file is a good idea and a dangerous one. Good, because one
page holding every fact about the paper is what stops two documents disagreeing.
Dangerous, because a *typed* master file is one more place for a number to go
stale, and it carries authority while it does so -- a wrong value in a file called
"single source of truth" is worse than the same value in a draft.

So this one is generated. Every figure below is read from MASTER_NUMBERS.csv, the
calibration summaries, and config.py at the moment it runs. Nothing is typed.
Regenerate it after any change and the file cannot drift; if a claim disappears
from the registry, this raises rather than printing a stale number.

The section numbering follows the working master file the authors drafted by hand,
so the two can be compared section by section.
"""

import csv
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import config as C  # noqa: E402

ARMS = ["A", "B", "C"]
_REG = None


def reg():
    global _REG
    if _REG is None:
        _REG = {}
        with open(C.REGISTRY_CSV) as fh:
            for row in csv.DictReader(fh):
                _REG[row["claim"].strip()] = row["value"].strip()
    return _REG


def v(claim):
    """A registry value, or a loud failure. Never a silent default."""
    r = reg()
    if claim not in r:
        raise KeyError("not in MASTER_NUMBERS.csv: %r" % claim)
    return r[claim]


def calib(arm):
    path = os.path.join(C.RESULT_DIR, arm, "calibration_summary.csv")
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


def build_id():
    path = os.path.join(HERE, "manuscript", "MANUSCRIPT.md")
    if not os.path.exists(path):
        return "(manuscript not built)", "(unknown)"
    import re
    text = open(path).read()
    m = re.search(r"\*Build ([0-9a-f]{12}) · (\S+) · ([\d,]+) words", text)
    return (m.group(1), m.group(3)) if m else ("(no build stamp)", "(unknown)")


def main(argv=None):
    r = reg()
    bid, words = build_id()
    L = []
    w = L.append

    w("# Master Paper Information File")
    w("")
    w("**Generated, not typed.** Every number below is read from "
      "`results/MASTER_NUMBERS.csv` (%d rows), the calibration summaries and "
      "`config.py` at the moment this ran. Regenerate with" % len(r))
    w("")
    w("```")
    w("python3 tools/master_file.py")
    w("```")
    w("")
    w("A hand-typed master file is one more place for a number to go stale, and it")
    w("carries authority while it does so. This one cannot: a claim that leaves the")
    w("registry makes the generator fail rather than print an old value.")
    w("")
    w("| | |")
    w("|---|---|")
    w("| Target journal | Biomedical Signal Processing and Control |")
    # The build id and word count are facts about the build, not results, so they
    # are quoted from the manuscript's own stamp inside a code span rather than
    # asserted as bare numbers -- scan.py checks bare numbers against the results
    # registry, and a manuscript word count is not a row of it.
    w("| Manuscript build | `%s` |" % bid)
    w("| Manuscript length | `%s words`, from the build stamp |" % words)
    w("| Registry | %d rows |" % len(r))
    w("| Dataset | Drivers Drowsiness Database (DD-Database), Dryad "
      "10.5061/dryad.5tb2rbp9c, CC0 1.0 |")
    w("")

    w("## 1. Study size")
    w("")
    w("| | |")
    w("|---|---|")
    for label, claim in (("Subjects", "subjects"), ("Seeds", "seeds"),
                         ("Architectures", "architectures"),
                         ("Folds per arm", "folds per arm"),
                         ("Total folds", "folds in ALL_FOLDS"),
                         ("Window length, samples", "window length samples")):
        w("| %s | %s |" % (label, v(claim)))
    w("| Seeds used | %s |" % ", ".join(str(s) for s in C.SEEDS))
    w("| EEG channels | O1, O2, C3, C4 at %.0f Hz |" % C.FS)
    w("| Window | %.0f s, non-overlapping |" % C.WIN_SEC)
    w("")
    # The deposit's README -- read at the source on 2 October 2026 -- documents the
    # annotation procedure: volunteers were instructed to press an event button when
    # they felt drowsy, and the marks are described as the volunteer's drowsiness
    # feeling registered by that button. An earlier reading of the deposit stopped at
    # its abstract, which is why this line once said the procedure was undocumented.
    # What the README still does not establish is where a mark falls within an episode,
    # so *onset* remains unused.
    w("**Labelling.** A drowsy window ends at an annotated drowsiness-event time "
      "mark; alert windows keep a 20 s guard from every such mark. The dataset "
      "documentation identifies the marks as event-button time marks recorded when "
      "volunteers felt drowsy. It does not establish whether the recorded time "
      "corresponds to the onset of a drowsiness episode or another point within the "
      "episode, so the word *onset* is not used.")
    w("")

    w("## 2. The three constructions")
    w("")
    w("| Arm | Construction | Windows | Per subject | Drowsy | Prevalence | "
      "Brier reference | Always alert |")
    w("|---|---|---|---|---|---|---|---|")
    for a in ARMS:
        w("| %s | %s | %s | %s | %s | %s %% | %s | %s %% |" % (
            a, C.ARMS[a]["label"], v("Arm %s windows" % a),
            v("Arm %s windows per subject" % a), v("Arm %s drowsy windows" % a),
            v("Arm %s prevalence percent" % a),
            v("Arm %s class-prior Brier reference" % a),
            v("Arm %s always-alert accuracy percent, 2 dp" % a)))
    w("")
    w("**Two contrasts, each varying one factor.** A against C isolates the "
      "balancing rule with trimming held constant; B against C examines trimming "
      "with balancing held at proportional. The fourth cell of the design was not "
      "run, so the trimming result is conditional on that balancing rule.")
    w("")
    w("**Accuracy is printed to two decimal places throughout**, including the "
      "baselines, because the margins in Results Section 5.3 are smaller than a "
      "tenth of a point. Full precision: %s, %s, %s." % tuple(
          v("Arm %s always-alert accuracy percent" % a) for a in ARMS))
    w("")

    w("## 3. Architectures")
    w("")
    w("| Architecture | Parameters | Configuration |")
    w("|---|---|---|")
    source = {"EEGNet": "authors' reference implementation",
              "ShallowConvNet": "authors' reference implementation",
              "DeepConvNet": "authors' reference implementation",
              "CNN": "prespecified for this study",
              "CNN-BiLSTM": "prespecified for this study"}
    for m in C.MODELS:
        w("| %s | %s | %s |" % (m, "{:,}".format(C.PARAMS[m]), source[m]))
    w("")
    # The ratio is computed, not typed. This line said "four times the CNN's total"
    # of the ADDED parameters, where 135,936 / 44,705 is 3.04; 4.04 is the ratio of
    # the CNN-BiLSTM's total. Both are now divisions rather than adjectives.
    w("The recurrent block adds %s parameters -- %.2f times the CNN's own total, "
      "taking the CNN-BiLSTM to %.2f times it -- so the CNN / CNN-BiLSTM pair is "
      "the closest architectural comparison in the study but **not a "
      "capacity-neutral ablation**."
      % ("{:,}".format(C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"]),
         (C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"]) / C.PARAMS["CNN"],
         C.PARAMS["CNN-BiLSTM"] / C.PARAMS["CNN"]))
    w("")

    w("## 4. Ranking quality, subject-averaged")
    w("")
    for metric, title in (("auc", "ROC-AUC"), ("pr_auc", "PR-AUC")):
        w("**%s** (mean ± SD across the five seed-level means)" % title)
        w("")
        w("| Model | Arm A | Arm B | Arm C |")
        w("|---|---|---|---|")
        for m in C.MODELS:
            cells = ["%s ± %s" % (v("Arm %s %s %s SUBJECT-AVERAGED" % (a, m, metric)),
                                  v("Arm %s %s %s seed SD" % (a, m, metric)))
                     for a in ARMS]
            w("| %s | %s |" % (m, " | ".join(cells)))
        w("")
    # "Leads in eleven of twelve" conflated two counts. EEGNet's mean ROC-AUC is
    # higher in all twelve; the difference reaches the nominal level in eleven.
    w("**EEGNet's ROC-AUC is higher in all twelve paired comparisons, and the "
      "difference reaches the nominal level in eleven** (%s of 4 on Arm A, "
      "%s of 4 on Arm B, %s of 4 on Arm C). The one exception is the CNN on Arm B "
      "at p = %s. None of the six non-EEGNet pairs separates on ROC-AUC on any "
      "arm; the smallest such p is %s, %s and %s." % (
          v("Arm A EEGNet ROC-AUC pairs significant"),
          v("Arm B EEGNet ROC-AUC pairs significant"),
          v("Arm C EEGNet ROC-AUC pairs significant"),
          v("Arm B EEGNet vs CNN ROC-AUC p"),
          v("Arm A smallest p among non-EEGNet ROC-AUC pairs"),
          v("Arm B smallest p among non-EEGNet ROC-AUC pairs"),
          v("Arm C smallest p among non-EEGNet ROC-AUC pairs")))
    w("")

    w("## 5. Accuracy against recall")
    w("")
    w("| Arm | ρ | p | attainable floor on five points |")
    w("|---|---|---|---|")
    for a in ARMS:
        w("| %s | %s | %s | %s |" % (
            a, v("Arm %s Spearman pooled accuracy vs pooled recall" % a),
            v("Arm %s p for Spearman pooled accuracy vs pooled recall" % a),
            v("smallest attainable Spearman p on five points")))
    w("")
    w("**The correlation is over five architectures, not ten subjects.** Its "
      "attainable floor is therefore %s, not the Wilcoxon floor of %s that applies "
      "to the paired subject-level tests. Quoting the Wilcoxon floor for this "
      "correlation would claim a precision five points cannot give." % (
          v("smallest attainable Spearman p on five points"),
          v("smallest attainable Wilcoxon p on ten pairs")))
    w("")
    w("What holds on all three constructions without needing a p-value: **the two "
      "most accurate architectures are exactly the two with the lowest recall.** "
      "On Arm C the correlation does not reach significance, because the two least "
      "sensitive architectures exchange places with one another.")
    w("")

    w("## 6. Probability quality")
    w("")
    w("**Pooled Brier score**, with each arm's class-prior reference")
    w("")
    w("| Model | Arm A | Arm B | Arm C |")
    w("|---|---|---|---|")
    for m in C.MODELS:
        cells = []
        for a in ARMS:
            b = float(v("Arm %s %s brier POOLED" % (a, m)))
            ref = float(v("Arm %s class-prior Brier reference" % a))
            cells.append("%.4f %s" % (b, "**above**" if b > ref else "below"))
        w("| %s | %s |" % (m, " | ".join(cells)))
    w("| *reference* | %s |" % " | ".join(
        "*%s*" % v("Arm %s class-prior Brier reference" % a) for a in ARMS))
    w("")
    w("The same three architectures are above the reference and the same two below "
      "it on every construction. The Brier score is a proper scoring rule covering "
      "calibration **and** refinement; it is not a pure calibration measure.")
    w("")

    w("## 7. Recalibration, measured")
    w("")
    w("| | |")
    w("|---|---|")
    for label, claim in (
            ("Folds measured", "Arm A folds measured for recalibration monotonicity"),
            ("Platt fits with a positive slope", "Arm A Platt fits with a positive slope"),
            ("Smallest fitted slope", "Arm A smallest fitted Platt slope"),
            ("Largest fitted slope", "Arm A largest fitted Platt slope"),
            ("Largest Platt change in fold ROC-AUC",
             "Arm A largest Platt change in fold ROC-AUC"),
            ("Largest Platt change in fold PR-AUC",
             "Arm A largest Platt change in fold PR-AUC"),
            ("Folds where the ε-clip created ties",
             "Arm A folds on which the epsilon-clip created ties under Platt"),
            ("Most ties on one fold", "Arm A most ties created on one fold by the epsilon-clip"),
            ("Isotonic lowered ROC-AUC on", "Arm A folds on which isotonic lowered ROC-AUC"),
            ("Isotonic lowered PR-AUC on", "Arm A folds on which isotonic lowered PR-AUC"),
            ("Distinct scores per fold, before isotonic",
             "Arm A median distinct scores per fold before isotonic"),
            ("Distinct scores per fold, after isotonic",
             "Arm A median distinct scores per fold after isotonic")):
        w("| %s | %s |" % (label, v(claim)))
    w("")
    w("A logistic map preserves the ranking only when its fitted slope is positive, "
      "which is a property of the fits and was therefore measured. The per-fold "
      "movements above bound what one fold can move; they are NOT what the tables "
      "print, which is an average over fifty folds. The reported quantity was "
      "measured separately:")
    w("")
    for label, claim in (
            ("EEGNet, subject-averaged ROC-AUC change after Platt",
             "Arm A EEGNet subject-averaged ROC-AUC change after Platt"),
            ("EEGNet, subject-averaged PR-AUC change after Platt",
             "Arm A EEGNet subject-averaged PR-AUC change after Platt"),
            ("CNN, subject-averaged ROC-AUC change after Platt",
             "Arm A CNN subject-averaged ROC-AUC change after Platt"),
            ("CNN, subject-averaged PR-AUC change after Platt",
             "Arm A CNN subject-averaged PR-AUC change after Platt"),
            ("CNN-BiLSTM, subject-averaged ROC-AUC change after Platt",
             "Arm A CNN-BiLSTM subject-averaged ROC-AUC change after Platt"),
            ("CNN-BiLSTM, subject-averaged PR-AUC change after Platt",
             "Arm A CNN-BiLSTM subject-averaged PR-AUC change after Platt")):
        w("| %s | %s |" % (label, v(claim)))
    w("")
    w("So the claim is **the subject-averaged ROC-AUC and PR-AUC are unchanged at "
      "the reported precision**, not algebraic invariance and not a statement about "
      "pooled metrics, which are not invariant because a different map is fitted "
      "for each fold.")
    w("")
    w("**Calibration coverage is three architectures per arm, and not the same "
      "three.**")
    w("")
    w("| Arm | Architectures with per-window scores retained |")
    w("|---|---|")
    for a in ARMS:
        rows = calib(a)
        w("| %s | %s |" % (a, ", ".join(sorted(x["model"] for x in rows)) or "—"))
    w("")
    w("Brier scores cover all five architectures on all three arms, because they "
      "need only the pooled predictions. Per-window probability files are released "
      "for Arm A only: %s files, %s MB." % (
          v("Arm A probability files released"),
          v("Arm A probability files released, megabytes")))
    w("")

    w("## 8. Variation")
    w("")
    w("| Arm | subject-to-seed SD ratio for PR-AUC, across the five architectures |")
    w("|---|---|")
    for a in ARMS:
        ratios = [float(v("Arm %s %s subject to seed SD ratio" % (a, m)))
                  for m in C.MODELS]
        w("| %s | %.0f to %.0f times |" % (a, min(ratios), max(ratios)))
    w("")
    w("**Repeated execution.** Where it was measured, a single subject's mean moved "
      "further between two identical runs than the seed-level ± this paper reports:")
    w("")
    w("| | overall shift over 50 folds | largest single subject's shift |")
    w("|---|---|---|")
    for m, metric, label in (("DeepConvNet", "auc", "DeepConvNet, ROC-AUC"),
                             ("DeepConvNet", "f1", "DeepConvNet, F1"),
                             ("ShallowConvNet", "auc", "ShallowConvNet, ROC-AUC"),
                             ("ShallowConvNet", "f1", "ShallowConvNet, F1")):
        w("| %s | %s | **%s** |" % (
            label, v("Arm B %s overall %s shift between runs" % (m, metric)),
            v("Arm B %s largest subject-level %s shift between runs" % (m, metric))))
    w("")
    w("**The two columns are not interchangeable.** The overall figures are means "
      "over all fifty folds; the subject-level figures are what bear on how the "
      "tables should be read, and they are four to fourteen times larger. An "
      "earlier draft labelled the overall figures as subject-level, and that "
      "mislabelling is the reason this table prints both.")
    w("")

    w("## 9. Smallest cells, for anyone quoting a subject")
    w("")
    w("| Subject | Arm A | Arm B | Arm C |")
    w("|---|---|---|---|")
    smallest = sorted(C.SUBJECTS,
                      key=lambda s: int(v("Arm C %s drowsy windows" % s)))[:3]
    for s in smallest:
        w("| %s | %s | %s | %s |" % (s, v("Arm A %s drowsy windows" % s),
                                     v("Arm B %s drowsy windows" % s),
                                     v("Arm C %s drowsy windows" % s)))
    w("")
    w("Drowsy-window counts differ by arm, so a sentence about a subject must say "
      "which arm it means.")
    w("")

    w("## 10. What is still open")
    w("")
    w("These are decisions, not measurements, and no generator can fill them in.")
    w("")
    w("- **The repository is not published.** The data-availability statement "
      "promises files no one can yet fetch.")
    w("- CRediT roles, to be confirmed by both authors.")
    w("- Title, acknowledgements and funding are settled; the AI declaration is "
      "omitted on the corresponding author's instruction. See REPRODUCIBILITY.md "
      "section 5 for the wording and the record.")
    w("")
    w("`python3 tools/preflight.py` reports every remaining placeholder by file "
      "and line on each run.")
    w("")

    text = "\n".join(L) + "\n"
    out = os.path.join(HERE, "manuscript", "MASTER_FILE.md")
    with open(out, "w") as fh:
        fh.write(text)
    print("wrote manuscript/MASTER_FILE.md")
    print("  %d lines, from a %d-row registry" % (text.count("\n") + 1, len(r)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
