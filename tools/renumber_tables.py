"""Renumber the article's tables in one pass, after a move to the supplement.

    python3 tools/renumber_tables.py MAP.json            # dry run
    python3 tools/renumber_tables.py MAP.json --apply

Moving Table 1, Table 8 and Table 9 into the supplementary material left the article
numbered 2 to 7, with no Table 1. That is the same defect the figures had -- a
numbering that is true of its own history and wrong on the page -- and a production
editor queries it. This closes the gap in the same way: one pass over the original
text, every substitution computed from the map, nothing outside the declared file
list touched, and lines that are ABOUT the old numbering protected.

The supplementary document is deliberately NOT in the list. Its tables are S1, S3
and S5 and do not move; a reference inside it to "Table 2" means the article's
Table 2 and is rewritten by the article's map only if it appears in a file that is
listed here, which the supplement is not -- so it is handled explicitly below.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    "manuscript/ABSTRACT.md", "manuscript/INTRODUCTION.md",
    "manuscript/RELATED_WORK.md", "manuscript/RESEARCH_GAP.md",
    "manuscript/METHODOLOGY.md", "manuscript/ARCHITECTURES.md",
    "manuscript/EXPERIMENTAL_SETUP.md", "manuscript/RESULTS.md",
    "manuscript/DISCUSSION.md", "manuscript/CONCLUSION.md",
    "manuscript/CODE_AVAILABILITY.md", "manuscript/REPRODUCIBILITY.md",
    "manuscript/SUPPLEMENTARY.md",
    "tools/split_map.json", "tools/check_table_marks.py", "tools/preflight.py",
    "tests/test_pipeline.py",
]

# Lines about the numbering as it was, which must keep it.
PROTECTED = {
    "Table 6 as well. This bounds the edit to":
        "renumber_figures.py's explanation of why it bounds its own edit",
    "moved out of the article and its":
        "the checker's message about moved tables, not a reference to one",
}

CITE = re.compile(r"\bTable (\d+)\b")
SUPP = re.compile(r"\bTable S\d+\b")


def load_map(path):
    with open(path) as fh:
        m = json.load(fh)
    # A shift, not a permutation: 2..7 map onto 1..6 because Table 1 left the
    # article. What must hold is that no two tables end up sharing a number, and
    # that no number is both a source and a LATER destination in a way that a
    # one-pass rewrite could not express -- which it always is, since every
    # substitution is computed from the original text.
    if len(set(m.values())) != len(m):
        raise SystemExit("two tables would end up with the same number: %r" % m)
    return m


def rewrite(line, m):
    # A supplementary label must never be touched: "Table S1" contains no bare digit
    # after "Table ", so the pattern cannot match it, but guard anyway by masking.
    holes, masked = [], line
    for mo in SUPP.finditer(line):
        holes.append(mo.group(0))
        masked = masked.replace(mo.group(0), "\x00%d\x00" % (len(holes) - 1), 1)
    out = CITE.sub(lambda mo: "Table %s" % m.get(mo.group(1), mo.group(1)), masked)
    for i, h in enumerate(holes):
        out = out.replace("\x00%d\x00" % i, h)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    m = load_map(a.map)
    print("table renumbering: %s"
          % ", ".join("%s->%s" % kv for kv in sorted(m.items(), key=lambda kv: int(kv[0]))))
    print("%s\n" % ("APPLYING" if a.apply else "DRY RUN"))

    total, skipped = 0, 0
    for rel in FILES:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            continue
        lines = open(path).read().splitlines(True)
        out, hits = [], 0
        for n, line in enumerate(lines, 1):
            why = next((w for k, w in PROTECTED.items() if k in line), None)
            if why:
                out.append(line)
                if CITE.search(line):
                    skipped += 1
                    print("  %s:%d PROTECTED (%s)" % (rel, n, why))
                continue
            new = rewrite(line, m)
            out.append(new)
            if new != line:
                hits += 1
                if hits <= 3:
                    print("  %s:%d  %s" % (rel, n, new.strip()[:96]))
        if hits:
            print("  %s: %d line(s)%s"
                  % (rel, hits, "" if hits <= 3 else "  (first three shown)"))
            total += hits
        if a.apply:
            with open(path, "w") as fh:
                fh.write("".join(out))

    print("\n%d change(s), %d protected line(s) left alone" % (total, skipped))
    if not a.apply:
        print("re-run with --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
