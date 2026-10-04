"""Split the two tables the map marks BOTH: reduced in the article, complete in the supplement.

    python3 tools/split_wide_tables.py            # dry run
    python3 tools/split_wide_tables.py --apply

Table 4, the pooled confusion matrices, and Table 6, the calibration table, are wider
than a two-column page holds at readable type. The map's answer is not to drop
columns but to print the columns a claim is checked from in the article and the
complete table in the supplementary material, which is part of the published record.

No value is deleted and no value is retyped. The reduced table is built by SELECTING
columns from the grid that is already in the manuscript, and the full table is that
same grid copied verbatim into the supplement. If a cell changes in the source, both
outputs change with it, because both are made from it.

  Table 4  article: Arm, Model, Recall, Precision, Accuracy
           Table S2: every column, including the four raw confusion counts
  Table 6  article: Arm, Model, Brier raw, Brier + Platt, Brier + isotonic
           Table S4: every column, including the three expected-calibration-error
                     columns

Why those columns stay. Section 7.3's claim is that accuracy runs against recall, and
a reader checks it from recall, precision and accuracy; the four counts are what those
three are computed FROM, and are evidence for the computation rather than for the
claim. Section 7.6's claim is that recalibration moves every measured architecture
below the class-prior Brier reference, and that is read from the three Brier columns —
which also carry the bold marks tools/check_table_marks.py verifies. The calibration
error is reported in the article's prose, with its direction and range for every
architecture, so the finding is stated there even though its columns are not.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "manuscript", "RESULTS.md")
SUPP = os.path.join(HERE, "manuscript", "SUPPLEMENTARY.md")


def grid_at(lines, caption_prefix):
    """The header, rule and body rows of the first grid after a caption."""
    start = next(i for i, l in enumerate(lines) if l.startswith(caption_prefix))
    i = start
    while not lines[i].startswith("|"):
        i += 1
    top = i
    while i < len(lines) and lines[i].startswith("|"):
        i += 1
    return start, top, i


def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def emit(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def reduce_grid(lines, caption_prefix, keep):
    """Return (full block, reduced block, span) for the grid under this caption."""
    start, top, end = grid_at(lines, caption_prefix)
    header = cells(lines[top])
    body = [cells(l) for l in lines[top + 2:end]]
    idx = [header.index(k) for k in keep]
    reduced = emit(keep, [[r[j] for j in idx] for r in body])
    return lines[top:end], reduced, (start, top, end), header, len(body)


T4_KEEP = ["Arm", "Model", "Recall", "Precision", "Accuracy"]
T6_KEEP = ["Arm", "Model", "Brier raw", "Brier + Platt", "Brier + isotonic"]

T4_CAPTION_OLD = ("The per-arm tables are reproduced separately in the\n"
                  "supplementary material.")
T4_CAPTION_NEW = ("The four raw confusion counts each row is computed from — TN, FP, FN\n"
                  "and TP — are given for every row in **Supplementary Table S2**, which is\n"
                  "this table complete.")
T4_MOVED_SENTENCE = ("The four count columns are\nseed means and carry no ±, since a "
                     "count rounded to the nearest window would carry a\ndispersion "
                     "narrower than the rounding.")

T6_CAPTION_OLD = ("The\nper-arm tables are reproduced separately in the supplementary "
                  "material.")
T6_CAPTION_NEW = ("The three expected-calibration-error columns are given for every row in\n"
                  "**Supplementary Table S4**, which is this table complete; their reading "
                  "is in\nthe paragraphs below, which give the direction and range of the "
                  "change for\nevery architecture.")

S2_CAPTION = """**Table S2. Pooled confusion matrices at the default 0.5 threshold, all three
constructions — complete.** This is Table 4 of the article with the four raw counts
restored. Counts are summed over the ten folds within a seed and then averaged over
the five seeds. The four count columns are seed means and carry no ±, since a count
rounded to the nearest window would carry a dispersion narrower than the rounding.
Recall and accuracy carry ± the standard deviation across the five seeds; precision
does not, for the reason given with Table 4."""

S4_CAPTION = """**Table S4. Expected calibration error and Brier score, raw and after each
recalibration, all three constructions — complete.** This is Table 6 of the article
with the three expected-calibration-error columns restored. Only three architectures
per construction retained per-window probabilities, and the two sets differ, so
between them all five are covered and only EEGNet is covered on all three. Bold marks
a Brier + Platt value that Platt recalibration carried from above the construction's
class-prior Brier reference to below it."""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    lines = open(RESULTS).read().splitlines()
    plan = []
    for prefix, keep, label in (("**Table 4.", T4_KEEP, "Table 4"),
                                ("**Table 6.", T6_KEEP, "Table 6")):
        full, reduced, span, header, n = reduce_grid(lines, prefix, keep)
        plan.append((label, full, reduced, span, header, n))
        print("  %s: %d columns -> %d, %d data rows kept in both"
              % (label, len(header), len(keep), n))
        print("      article keeps : %s" % ", ".join(keep))
        print("      supplement adds: %s"
              % ", ".join(c for c in header if c not in keep))

    if not a.apply:
        print("\nre-run with --apply")
        return 0

    # Replace the grids in the article, later one first so the earlier span holds.
    for label, full, reduced, (start, top, end), header, n in reversed(plan):
        lines[top:end] = reduced
    text = "\n".join(lines)
    text = text.replace(T4_CAPTION_OLD, T4_CAPTION_NEW)
    text = text.replace(T4_MOVED_SENTENCE, "")
    text = text.replace(T6_CAPTION_OLD, T6_CAPTION_NEW)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    with open(RESULTS, "w") as fh:
        fh.write(text.rstrip() + "\n")

    supp = open(SUPP).read().rstrip()
    for label, full, reduced, span, header, n in plan:
        caption = S2_CAPTION if label == "Table 4" else S4_CAPTION
        supp += "\n\n" + caption + "\n\n" + "\n".join(full) + "\n\n---\n"
    with open(SUPP, "w") as fh:
        fh.write(supp + "\n")

    print("\nrewrote manuscript/RESULTS.md and appended Tables S2 and S4 "
          "to manuscript/SUPPLEMENTARY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
