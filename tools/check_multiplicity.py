"""Check the released multiplicity table against a fresh recomputation.

    python3 tools/check_multiplicity.py

results/MULTIPLICITY.csv is the table Section 7.10 prints. This re-runs every
family from the released fold data and compares cell by cell, so the released
table cannot drift from what the pipeline actually computes.

It also re-derives the two facts the multiplicity argument rests on, rather than
trusting the numbers in the prose:

  * the Holm family ceilings implied by the three p-value floors, and whether each
    boundary is reached strictly or with equality;
  * where the survivors of a one-family Benjamini-Yekutieli analysis come from.

The second is the one that matters. If every survivor of the one-family analysis
comes from the drowsy-count family, the sentence in Section 7.10 that says so is
true; if that ever stops holding, the sentence has to change, and a check is the
only thing that will notice.
"""

import os
import sys
from fractions import Fraction

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import config as C  # noqa: E402
from src import aggregate, multiplicity as M  # noqa: E402

COLUMNS = ["n_tests", "n_nominal", "n_bh", "n_by"]


def check_released(result_dir):
    """Every cell of the released table, against a fresh run."""
    path = os.path.join(result_dir, "MULTIPLICITY.csv")
    if not os.path.exists(path):
        print("  MULTIPLICITY.csv is missing; run python -m src.multiplicity")
        return ["results/MULTIPLICITY.csv missing"]
    released = pd.read_csv(path)
    folds, pooled = aggregate.load(result_dir)
    fresh = M.table(folds, pooled, result_dir)

    problems = []
    if list(released.name) != list(fresh.name):
        problems.append("the released table has different rows from a fresh run")
        return problems
    for i in range(len(fresh)):
        for col in COLUMNS:
            got, want = int(released[col].iloc[i]), int(fresh[col].iloc[i])
            if got != want:
                problems.append("%s: %s is %d, recomputes to %d"
                                % (fresh.name.iloc[i], col, got, want))
    print("  released table  %d row(s) x %d column(s) compared"
          % (len(fresh), len(COLUMNS)))
    return problems


def check_ceilings():
    """The Holm ceilings, in exact rational arithmetic."""
    alpha = Fraction(5, 100)
    floors = [("Wilcoxon, ten pairs", Fraction(2, 2 ** 10), 25),
              ("Wilcoxon, nine pairs", Fraction(2, 2 ** 9), 12),
              ("Spearman exact, five points", Fraction(2, 120), 3)]
    problems = []
    for name, floor, expected in floors:
        m = 1
        while floor <= alpha / (m + 1):
            m += 1
        exact = floor == alpha / m
        print("  %-28s floor %-7s  m <= %2d  %s"
              % (name, floor, m, "EQUALITY" if exact else "strict"))
        if m != expected:
            problems.append("%s: ceiling is %d, the paper says %d"
                            % (name, m, expected))
    # The paper states that the Spearman boundary is an equality and the other two
    # are strict. That asymmetry is why the accuracy-against-recall result is the
    # one that sits on the boundary, so it is checked rather than described.
    if Fraction(2, 120) != alpha / 3:
        problems.append("2/5! no longer equals alpha/3; Section 6.5.1 is wrong")
    return problems


def check_by_survivors(result_dir):
    """Where the survivors of a one-family BY analysis come from."""
    folds, pooled = aggregate.load(result_dir)
    fam = M.families(folds, pooled, result_dir)
    labelled = sorted((float(p), name) for name, ps in fam.items() for p in ps)
    m = len(labelled)
    harmonic = sum(1.0 / k for k in range(1, m + 1))
    kept = 0
    for i in range(m - 1, -1, -1):
        if labelled[i][0] <= C.ALPHA * (i + 1) / (m * harmonic):
            kept = i + 1
            break
    sources = {}
    for _p, name in labelled[:kept]:
        sources[name] = sources.get(name, 0) + 1
    print("  one-family BY   %d of %d survive, from: %s"
          % (kept, m, sources or "nothing"))
    problems = []
    others = {k: v for k, v in sources.items() if k != M.PREVALENCE_FAMILY}
    if others:
        problems.append(
            "Section 7.10 says every one-family BY survivor is from the "
            "prevalence family; these are not: %s" % others)
    return problems


def main(argv):
    result_dir = argv[0] if argv else C.RESULT_DIR
    print("multiplicity\n")
    problems = (check_released(result_dir) + check_ceilings()
                + check_by_survivors(result_dir))
    print("\n%d problem(s)" % len(problems))
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
