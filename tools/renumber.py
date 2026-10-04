"""Apply a section renumbering to every heading and cross-reference at once.

    python3 tools/renumber.py MAP.json manuscript/*.md
    python3 tools/renumber.py MAP.json --dry-run manuscript/*.md

Renumbering a manuscript by hand is the edit that fails quietly. A reference to
"Section 5" does not break when the Results stop being Section 5; it starts
pointing at the Experimental Setup, and nothing complains. This applies the whole
map in one pass, reports every substitution, and can be run with --dry-run first
so the change can be read before it is made.

The map is JSON, old number to new number, longest key first internally so that
"3.6" is not eaten by "3":

    {"3.6": "5", "3": "4", "4": "6", "5": "7", "6": "8", "7": "8.10", "8": "9"}

Two rules make it safe:

  * Every reference is rewritten from the ORIGINAL text, never from text this run
    has already rewritten. Sequential substitution is what turns 5 into 7 and then
    7 into 8.10 in the same sentence.
  * A number with a deeper part keeps it: under the map above, "Section 5.3"
    becomes "Section 7.3" because 5 maps to 7, and "Section 3.6.1" becomes
    "Section 5.1" because the longer key 3.6 wins over 3.

Headings are rewritten too, matching "# 5. Results" and "## 5.3 Something".

It does not renumber anything it was not told about, and it prints a count per
mapping so the result can be checked against expectations rather than hoped at.
"""

import json
import os
import re
import sys
from collections import Counter

REF = re.compile(r"\bSection\s+(\d+(?:\.\d+)*)")
HEAD = re.compile(r"^(#{1,6})\s+(\d+(?:\.\d+)*)\.?(\s+)", re.M)


def load_map(path):
    with open(path) as fh:
        raw = json.load(fh)
    # Longest key first: "3.6" must be tried before "3".
    return sorted(raw.items(), key=lambda kv: -len(kv[0]))


def remap(number, pairs):
    """Return the new number for one dotted reference, or None if unmapped."""
    for old, new in pairs:
        if number == old:
            return new
        if number.startswith(old + "."):
            return new + number[len(old):]
    return None


def apply(text, pairs, counts):
    def ref(m):
        new = remap(m.group(1), pairs)
        if new is None:
            return m.group(0)
        counts["Section %s -> Section %s" % (m.group(1), new)] += 1
        return "Section %s" % new

    def head(m):
        new = remap(m.group(2), pairs)
        if new is None:
            return m.group(0)
        counts["heading %s -> %s" % (m.group(2), new)] += 1
        return "%s %s%s" % (m.group(1), new, m.group(3))

    # Both passes read the same original string, so nothing is rewritten twice.
    text = HEAD.sub(head, text)
    return REF.sub(ref, text)


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 1
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    pairs = load_map(argv[0])
    files = argv[1:]

    total = Counter()
    for path in files:
        if not os.path.exists(path):
            print("  missing: %s" % path)
            continue
        with open(path) as fh:
            before = fh.read()
        counts = Counter()
        after = apply(before, pairs, counts)
        if after != before and not dry:
            with open(path, "w") as fh:
                fh.write(after)
        if counts:
            print("%s%s" % (os.path.basename(path), "  (dry run)" if dry else ""))
            for k, n in sorted(counts.items()):
                print("    %-34s x%d" % (k, n))
        total.update(counts)

    print("\n%d substitution(s) across %d file(s)%s"
          % (sum(total.values()), len(files), ", nothing written" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
