"""Check that every "Section N" reference in the manuscript points somewhere real.

    python3 tools/check_crossrefs.py SECTION_MAP.json file1.md file2.md ...

Renumbering a manuscript is the kind of edit that fails silently. A reference to
"Section 5" does not break when Section 5 stops being the Results; it just starts
pointing at the wrong place, and no spell-checker, compiler or reviewer's first
read will catch it. This script makes that failure loud.

It takes a section map — the numbering the manuscript is supposed to have — and
reports three things:

  MISSING   a reference to a section number that does not exist in the map
  UNUSED    a section nothing refers to (not an error, but worth knowing)
  SUMMARY   how many references point at each section, so that a renumbering can
            be checked against the counts from before it

The map is a JSON object of number to name, for example:

    {"1": "Introduction", "2": "Related Work", "5": "Results"}

Subsection references such as "Section 6.4" are checked against their parent: a
reference to 6.4 requires that section 6 exists. Checking every subsection would
mean maintaining a map of the whole document, which is more bookkeeping than the
problem deserves.
"""

import json
import os
import re
import sys
from collections import Counter

REF = re.compile(r"Section\s+(\d+)(\.\d+[a-z]?)?")


def references(path):
    """Yield (full_reference, top_level_number) for each cross-reference."""
    with open(path) as fh:
        text = fh.read()
    text = re.sub(r"`[^`]*`", " ", text)
    for m in REF.finditer(text):
        yield m.group(0), m.group(1)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[0]) as fh:
        section_map = json.load(fh)
    known = set(section_map)

    counts, missing = Counter(), []
    for path in argv[1:]:
        if not os.path.exists(path):
            print("skipped (not found):", path)
            continue
        for ref, top in references(path):
            counts[top] += 1
            if top not in known:
                missing.append((path, ref))

    print("section map:")
    for n in sorted(known, key=lambda x: int(x)):
        print("  %-4s %-28s referenced %d time(s)"
              % (n, section_map[n], counts.get(n, 0)))

    unused = [n for n in known if not counts.get(n)]
    if unused:
        print("\nreferenced by nothing: %s"
              % ", ".join("%s (%s)" % (n, section_map[n])
                          for n in sorted(unused, key=lambda x: int(x))))

    if missing:
        print("\nMISSING — these point at a section that is not in the map:")
        for path, ref in missing:
            print("  %-28s %s" % (os.path.basename(path), ref))
    print("\n%d cross-reference(s) checked, %d broken"
          % (sum(counts.values()), len(missing)))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
