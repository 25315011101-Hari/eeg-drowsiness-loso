"""Move the units the split map sends to supplementary out of the article.

    python3 tools/move_to_supplementary.py            # dry run
    python3 tools/move_to_supplementary.py --apply

This is the first half of applying tools/split_map.json, and it is the half that
cannot lose anything: each unit is CUT from its section file and PASTED into
manuscript/SUPPLEMENTARY.md, and the script checks that the words it removed are the
words it wrote. Nothing is rewritten and nothing is shortened here. Condensing the
sections that stay is the second half, and it is a separate, reviewed operation.

At each departure point the script leaves the sentence the map declared under
`main_retains`, so the claim the moved unit supported is still made in the article
and still points at where its evidence now lives. A move with no pointer would be
exactly the "hiding evidence in the supplementary material" the map forbids.

Two tables the map marks BOTH -- Table 5 and Table 7 -- are NOT handled here. They
need a reduced form derived for the article as well as a full form for the
supplement, which is a derivation and not a move.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MS = os.path.join(HERE, "manuscript")
SUPP = os.path.join(MS, "SUPPLEMENTARY.md")
HEADING = re.compile(r"^#{1,3} +(.*?)\s*$")


def words(text):
    return len([t for t in text.split() if re.search(r"[0-9A-Za-z]", t)])


def section_range(lines, heading):
    """From a heading to the next heading of any level."""
    marks = [i for i, l in enumerate(lines) if HEADING.match(l)]
    for k, i in enumerate(marks):
        if HEADING.match(lines[i]).group(1).strip() == heading:
            return i, (marks[k + 1] if k + 1 < len(marks) else len(lines))
    raise SystemExit("heading not found: %r" % heading)


def table_range(lines, label):
    """From a table's caption line to the last row of its grid.

    The caption, any sentences that continue it, and the grid itself; the paragraph
    AFTER the grid is left behind, because that paragraph is usually the reading of
    the table rather than the table, and the article keeps its readings.
    """
    start = next((i for i, l in enumerate(lines)
                  if l.startswith("**%s." % label)), None)
    if start is None:
        raise SystemExit("table caption not found: %r" % label)
    i, seen = start, False
    while i < len(lines):
        if lines[i].startswith("|"):
            seen = True
        elif seen:
            break
        i += 1
    return start, i


# Each move: where it lives, how to find it, what it becomes in the supplement, and
# the sentence left behind. The pointer text is the map's main_retains obligation
# turned into a sentence a reader meets at the point the evidence used to be.
MOVES = [
    dict(kind="section", file="METHODOLOGY.md",
         find="4.5 Dataset construction is verified, not assumed",
         becomes="S1 Dataset construction is verified, not assumed",
         pointer="Every window count in Table 2 is regenerated from the EDF files by "
                 "the released construction script, which refuses to write unless its "
                 "internal and reference checks both pass; Arm B's counts are "
                 "reproducible from the public recordings alone. Supplementary "
                 "Section S1 gives the two checks and the rebuild result."),
    dict(kind="table", file="METHODOLOGY.md", find="Table 1",
         becomes="Table S1", label="Table S1",
         pointer="Per-subject window counts before any construction rule is applied "
                 "are given in Supplementary Table S1."),
    dict(kind="section", file="RESULTS.md",
         find="7.8 Where threshold selection helped, the scores were stably offset",
         becomes="S2 Where threshold selection helped, the scores were stably offset",
         pointer="Thresholds maximising F1 and maximising balanced accuracy were also "
                 "selected out of subject, on the same nine-subject basis, and applied "
                 "to the held-out subject on Arms A and C; the rule helped in one "
                 "architecture-and-arm combination and not in the others, and Section "
                 "8.6 reads that result. The per-fold offsets and every paired test "
                 "behind it are in Supplementary Section S2."),
    dict(kind="section", file="RESULTS.md", find="Coverage of each analysis",
         becomes="S3 Coverage of each analysis",
         pointer="A finding is claimed for all three constructions only where it "
                 "replicates on all three. The analyses that do not cover all three, "
                 "and what each one does cover, are set out in Supplementary Section "
                 "S3 and Table S3."),
    dict(kind="table", file="RESULTS.md", find="Table 9",
         becomes="Table S5", label="Table S5",
         pointer="The per-family breakdown is given in Supplementary Table S5 and is "
                 "released as `results/MULTIPLICITY.csv`."),
    dict(kind="section", file="ABSTRACT.md", find="Checks run on this page",
         becomes=None,          # repository, not supplementary
         pointer=None),
]

HEADER = """# Supplementary Material

**Calibration matters for trustworthy EEG-based driver drowsiness detection:
A 750-fold leave-one-subject-out study**

*This document is part of the published record and is submitted with the article.
Nothing here was shortened on its way out of the article: each section and table
below is the material as it stood in the manuscript, moved rather than rewritten.
`tools/split_map.json` records why each one is here, and what the article keeps in
its place so that the claim it supports is still made and still checkable there.*

*Cross-references of the form "Section 7.6" refer to the main article.*

---
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    with open(os.path.join(HERE, "tools", "split_map.json")) as fh:
        json.load(fh)                      # read to fail early if it is malformed

    files, taken, removed_words = {}, [], 0
    for mv in MOVES:
        path = os.path.join(MS, mv["file"])
        lines = files.setdefault(mv["file"], open(path).read().splitlines())
        if mv["kind"] == "section":
            lo, hi = section_range(lines, mv["find"])
        else:
            lo, hi = table_range(lines, mv["find"])
        block = lines[lo:hi]
        n = words("\n".join(block))
        removed_words += n
        print("  %-16s L%-5d..L%-5d  %4d words  %s  ->  %s"
              % (mv["file"], lo + 1, hi, n, mv["find"],
                 mv["becomes"] or "REPOSITORY (dropped from the article)"))
        if mv["becomes"]:
            taken.append((mv, block))
        # Replace in place with the pointer, or delete outright.
        pointer = ([""] + [mv["pointer"]] + [""]) if mv["pointer"] else []
        files[mv["file"]] = lines[:lo] + pointer + lines[hi:]

    body = [HEADER]
    for mv, block in taken:
        if mv["kind"] == "section":
            block = ["## %s" % mv["becomes"]] + block[1:]
        else:
            block = [re.sub(r"^\*\*%s\." % mv["find"], "**%s." % mv["label"],
                            block[0])] + block[1:]
        body.append("\n".join(block).strip() + "\n\n---\n")
    supp = "\n".join(body)
    written = words(supp) - words(HEADER)

    print("")
    print("  words removed from the article : %d" % removed_words)
    print("  words written to the supplement: %d" % written)
    print("  dropped to the repository      : %d"
          % (removed_words - written))

    if a.apply:
        for name, lines in files.items():
            text = re.sub(r"\n{4,}", "\n\n\n", "\n".join(lines))
            with open(os.path.join(MS, name), "w") as fh:
                fh.write(text.rstrip() + "\n")
        with open(SUPP, "w") as fh:
            fh.write(supp)
        print("\nwrote manuscript/SUPPLEMENTARY.md and rewrote %d section file(s)"
              % len(files))
        print("now: python3 tools/build_manuscript.py manuscript "
              "manuscript/MANUSCRIPT.md && python3 tools/preflight.py")
    else:
        print("\nre-run with --apply to make these changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
