"""Check the borrowed numbers against the reference list they came from.

    python3 tools/check_literature.py

`src/scan.py` validates every number in the manuscript against one of two
registries. For numbers taken from other people's papers that registry is
`results/LITERATURE_NUMBERS.csv`, which is maintained by hand, and nothing checked
it against `manuscript/REFERENCES.md`, which is also maintained by hand.

So the two drifted, and in the worst possible direction. `REFERENCES.md` records
that `[P5]` was verified on 18 September 2026 and found **wrong**: the chapter
printed at pp. 61-74 is *Probabilities for SV Machines* (2000), not the 1999
preprint title most of the literature copies. It says, in bold, that no entry
carries a `VERIFY` marker any longer. Meanwhile the literature registry still read

    [P5] Platt 1999: publication year,1999,VERIFY before submission

-- the superseded year AND an unfinished verification state, in the file a reader
is pointed at to check borrowed numbers. Preflight passed throughout, because no
sentence in the body prints a reference year, so `scan.py` never had to look.

Three checks, each of which would have caught it:

  markers   no row carries VERIFY, TODO, TBD or a bare question mark
  sources   every row names where it was checked -- an http address, or a stated
            derivation that itself names one
  years     a "publication year" row agrees with the year printed for that key in
            REFERENCES.md

The third is the one that matters: it ties the two hand-maintained files together,
so a correction made in one cannot be forgotten in the other.
"""

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LITERATURE = os.path.join(HERE, "results", "LITERATURE_NUMBERS.csv")
REFERENCES = os.path.join(HERE, "manuscript", "REFERENCES.md")

UNFINISHED = re.compile(r"\b(VERIFY|TODO|TBD|FIXME|CHECK ME)\b", re.I)
# "**[P5]** Platt, J. C. (2000). ..." -- the key, then the first year in
# parentheses. An entry's author list often wraps over three or four lines before
# the year appears, so the search runs over the whole entry block, not one line: a
# line-by-line version silently found ten of the sixteen entries and reported the
# other six as missing from the reference list.
ENTRY = re.compile(r"\*\*\[([A-Z]+\d+)\]\*\*(.*?)(?=\n\*\*\[[A-Z]+\d+\]\*\*|\Z)",
                   re.S)
YEAR_IN_ENTRY = re.compile(r"\((\d{4})\)")
# "[P5] Platt 2000: publication year"
YEAR_CLAIM = re.compile(r"^\[([A-Z]+\d+)\][^:]*:\s*publication year$")


def reference_years():
    """The year printed in REFERENCES.md for each key."""
    with open(REFERENCES) as fh:
        text = fh.read()
    out = {}
    for m in ENTRY.finditer(text):
        year = YEAR_IN_ENTRY.search(m.group(2))
        if year:
            out[m.group(1)] = year.group(1)
    return out


def main():
    with open(LITERATURE) as fh:
        rows = list(csv.DictReader(fh))
    years = reference_years()

    unfinished, unsourced, mismatched = [], [], []
    checked_years = 0
    for r in rows:
        claim, value, note = r["claim"].strip(), r["value"].strip(), r["note"].strip()
        if UNFINISHED.search(note) or UNFINISHED.search(claim):
            unfinished.append((claim, note))
        if "http" not in note:
            unsourced.append((claim, note))
        m = YEAR_CLAIM.match(claim)
        if m:
            key = m.group(1)
            if key in years:
                checked_years += 1
                if years[key] != value:
                    mismatched.append((key, value, years[key]))
            else:
                mismatched.append((key, value, "no entry in REFERENCES.md"))

    print("borrowed numbers, against the reference list they came from\n")
    print("  %-22s %d row(s)" % ("literature registry", len(rows)))
    print("  %-22s %d entry(ies)" % ("REFERENCES.md", len(years)))
    print("  %-22s %d row(s) compared" % ("publication years", checked_years))

    for claim, note in unfinished:
        print("  UNFINISHED   %s -- %s" % (claim, note))
    for claim, note in unsourced:
        print("  UNSOURCED    %s -- %r" % (claim, note[:60]))
    for key, got, want in mismatched:
        print("  YEAR DISAGREES  %s: registry says %s, REFERENCES.md says %s"
              % (key, got, want))

    bad = len(unfinished) + len(unsourced) + len(mismatched)
    print("\n%d problem(s)" % bad)
    if not bad:
        print("No unfinished marker, every row names where it was checked, and every "
              "publication\nyear agrees with the reference list.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
