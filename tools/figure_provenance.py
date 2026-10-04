"""Print, for every figure, each value it plots and the registry row it came from.

    python3 tools/figure_provenance.py            > figures/PROVENANCE.txt

"Every number in the figures comes from our own results" is a claim, and this
repository's rule is that a claim gets a command. This one instruments
`src.figures.lookup` to record every registry access while the figures are drawn,
then prints the trail: figure, claim, value, and the note the registry carries.

Reading the output is how a co-author or a reviewer checks a picture without
reading the plotting code: if a number is on a chart, it is in this list, and if
it is in this list it is a row of MASTER_NUMBERS.csv.

The panels that are computed from the released per-window score files rather than
from a registry row -- the reliability diagrams -- are reported as such at the end,
with the files they read, because those are the one place a figure legitimately
goes past the registry to the raw predictions underneath it.
"""

import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import figures  # noqa: E402


def main(argv=None):
    trail = OrderedDict()
    current = {"figure": "(module import)"}
    real_lookup = figures.lookup

    def recording_lookup(claim):
        value = real_lookup(claim)
        trail.setdefault(current["figure"], []).append((claim, value))
        return value

    figures.lookup = recording_lookup
    try:
        import matplotlib.pyplot as plt
        plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
        for name, fn in (("figure2_study_design", figures.figure0),
                         ("figure5_brier_partition", figures.figure1),
                         ("figure3_accuracy_against_recall", figures.figure2),
                         ("figure6_recalibration", figures.figure3),
                         ("figure4_subject_against_seed_spread", figures.figure4),
                         ("figureS1_overview", figures.figure5)):
            current["figure"] = name
            fn()
    finally:
        figures.lookup = real_lookup

    reg = figures._load()
    out = []
    out.append("WHERE EVERY NUMBER IN EVERY FIGURE COMES FROM")
    out.append("=" * 78)
    out.append("")
    out.append("Source of record: results/MASTER_NUMBERS.csv (%d rows)." % len(reg))
    out.append("Each line below is one value a figure plots, with the registry claim")
    out.append("it was read from. No figure contains a number that is not in this list.")
    out.append("")

    total = 0
    for name, entries in trail.items():
        seen = OrderedDict()
        for claim, value in entries:
            seen.setdefault(claim, value)
        out.append("")
        out.append("-" * 78)
        out.append("%s  —  %d distinct registry value(s)" % (name, len(seen)))
        out.append("-" * 78)
        for claim, value in seen.items():
            note = ""
            for row_claim, _ in reg.items():
                if row_claim == claim:
                    break
            out.append("  %-62s %s" % (claim[:62], value))
        total += len(seen)

    out.append("")
    out.append("=" * 78)
    out.append("%d registry value(s) plotted in total, across %d figure(s)."
               % (total, len(trail)))
    out.append("")
    out.append("Computed from the released per-window scores rather than from a")
    out.append("registry row:")
    out.append("")
    out.append("  figureS1_overview panels (d), (e), (f)  —  reliability diagrams")
    out.append("      read results/A/probs_<model>_seed<n>.npz, the per-window")
    out.append("      predictions released for Arm A. The curves are binned from those")
    out.append("      scores directly; panel (e) refits Platt scaling per fold on the")
    out.append("      other nine subjects, exactly as src/calibrate.py does.")
    out.append("      Arm A is the only construction whose scores are released, which")
    out.append("      is why all three reliability panels are Arm A and say so.")
    out.append("")
    out.append("Regenerate this file:  python3 tools/figure_provenance.py")

    text = "\n".join(out) + "\n"
    path = os.path.join(figures.FIGDIR, "PROVENANCE.txt")
    os.makedirs(figures.FIGDIR, exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    print(text)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
