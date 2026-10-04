"""Recompute every rank-correlation p-value in the registry from first principles.

    python3 tools/check_spearman_p.py            # report
    python3 tools/check_spearman_p.py --strict   # exit non-zero on a disagreement

This reports. It changes nothing, and it is deliberately not wired into
`preflight.py`, because what it finds is not a defect that a script may decide:
it is a question about which test the paper means, and that is the authors' to
answer.

WHAT IT CHECKS

A Spearman p-value can be computed two ways, and they do not agree on small
samples:

  exact     enumerate all n! orderings of the ranks and count how many reach a
            correlation at least as extreme as the observed one. No assumption.
            For n = 5 there are only 120 orderings, so the smallest two-sided p
            obtainable is 2/120 = 0.0167 -- there is no such thing as p = 0.001
            from five points.
  t-approx  t = rho * sqrt((n - 2) / (1 - rho^2)) against Student's t on n - 2
            degrees of freedom. This is what scipy.stats.spearmanr returns, and
            what src/stats.py therefore records. It is an asymptotic result, and
            at n = 5 it returns values below the exact floor -- including exactly
            0 when |rho| = 1, which is a division by zero rather than a p-value.

HISTORY. This tool was written on 19 September 2026 as an audit, when the
registry held p-values from BOTH conventions: `src/registry.py` capped the
accuracy-against-recall claim at C.P_FLOOR_SPEARMAN_5 and left three other
five-point families reporting the approximation, one of them p = 0.0000 from five
points. On 23 September 2026 all four five-point families moved to the exact p
(`stats.spearman`), which changed nine registered values and two significance
verdicts. The tool now serves as their regression test: the five-point rows must
agree exactly, and the ten-subject rows are the evidence that leaving that family
on the approximation changes nothing.

The script separates the claims by the n they were computed over, because that
is where a careless audit goes wrong -- the drowsy-count correlations look like
the others but run over the TEN subjects, where the approximation is sound:

  n = 5   over the five architectures
  n = 10  over the ten subjects

and, for each, compares the recorded p with the exact one and reports every
claim whose verdict at alpha = 0.05 would change.

WHAT IT DOES NOT DO

It does not decide anything. It prints what each convention gives and where they
part company; which one the paper reports was settled by the authors, and is
stated in Section 6.5 and recorded in manuscript/audit-history/SPEARMAN_P_NOTE.md.
"""

import argparse
import csv
import itertools
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import config as C  # noqa: E402

MASTER = os.path.join(HERE, "results", "MASTER_NUMBERS.csv")
ALPHA = 0.05

# Every rank correlation in the registry, with the n it was computed over. The n
# comes from the function in src/stats.py that produces it, not from the claim's
# wording: capacity_correlation and ranking_vs_reliability and accuracy_vs_recall
# run over C.MODELS (five), subject_count_correlation over C.SUBJECTS (ten).
FAMILIES_5 = [
    ("Arm %s Spearman pooled accuracy vs pooled recall",
     "Arm %s p for Spearman pooled accuracy vs pooled recall"),
    ("Arm %s rho parameters vs ROC-AUC",
     "Arm %s p for parameters vs ROC-AUC"),
    ("Arm %s rho ROC-AUC (pooled) vs pooled Brier",
     "Arm %s p for ROC-AUC (pooled) vs pooled Brier"),
    ("Arm %s rho ROC-AUC (subject_averaged) vs pooled Brier",
     "Arm %s p for ROC-AUC (subject_averaged) vs pooled Brier"),
]
FORMS_10 = ("raw", "minus prevalence", "over prevalence")


def null_distribution(n):
    """Every value Spearman's rho can take on n untied ranks, once per ordering.

    rho = 1 - 6 * sum(d^2) / (n^3 - n), so the whole distribution follows from
    the sum of squared rank differences and needs no correlation routine.
    """
    base = np.arange(n)
    out = np.empty(math.factorial(n), dtype=np.int64)
    for i, perm in enumerate(itertools.permutations(range(n))):
        out[i] = ((base - np.asarray(perm)) ** 2).sum()
    return 1.0 - 6.0 * out / (n * (n * n - 1))


def exact_p(rho, table):
    """Two-sided exact p: the share of orderings at least as extreme as rho."""
    return float((np.abs(table) >= abs(rho) - 1e-9).mean())


def registry():
    with open(MASTER) as fh:
        return {r["claim"].strip(): r for r in csv.DictReader(fh)}


def report(reg, pairs, table, n, label):
    """Print one family and return its disagreements."""
    print("\n  %s  (n = %d, %d orderings, smallest attainable two-sided p %.4f)"
          % (label, n, len(table), 2.0 / len(table)))
    print("  %-52s %8s %10s %9s" % ("claim", "rho", "recorded", "exact"))
    flips = []
    for rho_key, p_key in pairs:
        if rho_key not in reg or p_key not in reg:
            continue
        try:
            rho = float(reg[rho_key]["value"])
            recorded = float(reg[p_key]["value"])
        except ValueError:
            continue
        ex = exact_p(rho, table)
        flipped = (recorded < ALPHA) != (ex < ALPHA)
        if flipped:
            flips.append((rho_key, rho, recorded, ex))
        print("  %-52s %8.3f %10.4f %9.4f %s"
              % (rho_key[:52], rho, recorded, ex,
                 "<-- verdict changes" if flipped else ""))
    return flips


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any alpha = 0.05 verdict changes")
    ap.add_argument("--quiet-n10", action="store_true",
                    help="summarise the ten-subject family instead of listing it")
    args = ap.parse_args(argv)

    reg = registry()
    print("rank-correlation p-values, recorded against exact")
    print("Since 23 September 2026 the five-point families are recorded EXACTLY, so "
          "those\nrows agree by construction and this tool is their regression test. "
          "The ten-subject\nfamily is still the t-approximation; the comparison "
          "below is what justifies that.")

    t5 = null_distribution(5)
    pairs5 = [(a % arm, b % arm) for a, b in FAMILIES_5 for arm in C.ARM_ORDER] \
        if hasattr(C, "ARM_ORDER") else \
        [(a % arm, b % arm) for a, b in FAMILIES_5 for arm in ("A", "B", "C")]
    flips5 = report(reg, pairs5, t5, 5, "across the five architectures")

    t10 = null_distribution(10)
    pairs10 = [("Arm %s %s rho drowsy count vs PR-AUC %s" % (arm, m, form),
                "Arm %s %s p drowsy count vs PR-AUC %s" % (arm, m, form))
               for arm in ("A", "B", "C") for m in C.MODELS for form in FORMS_10]
    if args.quiet_n10:
        present = [(r, p) for r, p in pairs10 if r in reg and p in reg]
        flips10 = []
        for rho_key, p_key in present:
            rho = float(reg[rho_key]["value"])
            recorded = float(reg[p_key]["value"])
            ex = exact_p(rho, t10)
            if (recorded < ALPHA) != (ex < ALPHA):
                flips10.append((rho_key, rho, recorded, ex))
        print("\n  across the ten subjects  (n = 10): %d claim(s) checked, "
              "%d verdict change(s)" % (len(present), len(flips10)))
        for k, rho, rec, ex in flips10:
            print("      %-50s %6.3f  %.4f -> %.4f" % (k[:50], rho, rec, ex))
    else:
        flips10 = report(reg, pairs10, t10, 10, "across the ten subjects")

    flips = flips5 + flips10
    print("\n%d claim(s) whose verdict at alpha = %.2f depends on which "
          "convention is used" % (len(flips), ALPHA))
    for key, rho, recorded, ex in flips:
        print("    %s" % key)
        print("        rho = %+.3f   recorded p = %.4f (significant)   "
              "exact p = %.4f (not)" % (rho, recorded, ex))
    if flips:
        print("\nNeither number is wrong. They answer different questions, and "
              "which one the\npaper should report is a decision for the authors "
              "-- see\nmanuscript/audit-history/SPEARMAN_P_NOTE.md.")
    return 1 if (args.strict and flips) else 0


if __name__ == "__main__":
    raise SystemExit(main())
