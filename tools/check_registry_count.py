"""Check that every row count a document claims for the registry is the real one.

    python3 tools/check_registry_count.py results/MASTER_NUMBERS.csv file1.md ...

The manuscript contains audit sentences of the form "checked against
MASTER_NUMBERS.csv (1710 rows)". That number goes stale every time the registry
is regenerated, and a stale one is worse than no claim at all: it is an audit
statement that does not hold, in a paper whose argument is that its numbers are
checkable. It also cannot be caught by `scan.py`, because a count of registry rows
is not itself a registry row.

So it gets its own check. The script reads the true row count from the CSV, finds
every four-or-more-digit number in each document that sits next to the word "row",
"rows" or "registry", and reports any that disagree.

Exit status is 1 if any claim is wrong, so this can gate a release.
"""

import csv
import os
import re
import sys

# A four-or-more-digit number IMMEDIATELY followed by "row", "rows" or "-row".
# Deliberately tight. An earlier, looser version matched any such number within
# forty characters of the word "registry" or "row", which caught the year in
# "regenerated on 16 September 2026 by registry.py" and the window total in "rows
# sum to 9,260" — false alarms that would train a reader to ignore this check.
CLAIM = re.compile(r"(\d[\d,]{3,})[  -]?rows?\b", re.I)

# A line carrying this marker records a count as of some past date on purpose —
# a dated audit, or a note quoting a superseded figure — and is not checked.
EXEMPT = "registry-count: historical"


def true_count(csv_path):
    with open(csv_path) as fh:
        return sum(1 for _ in csv.DictReader(fh))


def claims(path):
    """Yield (line number, claimed count as int, the line) for each claim."""
    with open(path) as fh:
        for n, line in enumerate(fh, 1):
            if EXEMPT in line:
                continue
            for m in CLAIM.finditer(line):
                yield n, int(m.group(1).replace(",", "")), line.strip()


def fix(path, actual):
    """Rewrite every non-exempt row-count claim in `path` to `actual`.

    This exists because the count changes on every registry rebuild, and a human
    updating six documents by hand is how the claim went stale in the first place.
    Thousands separators in the original are preserved.
    """
    with open(path) as fh:
        lines = fh.readlines()
    changed = 0
    for i, line in enumerate(lines):
        if EXEMPT in line:
            continue
        def sub(m):
            global_changed.append(1)
            had_comma = "," in m.group(1)
            n = "{:,}".format(actual) if had_comma else str(actual)
            return m.group(0).replace(m.group(1), n)
        global_changed = []
        new = CLAIM.sub(sub, line)
        if new != line:
            lines[i] = new
            changed += len(global_changed)
    if changed:
        with open(path, "w") as fh:
            fh.writelines(lines)
    return changed


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    do_fix = "--fix" in argv
    argv = [a for a in argv if a != "--fix"]
    csv_path, docs = argv[0], argv[1:]
    actual = true_count(csv_path)

    if do_fix:
        total = 0
        for path in docs:
            if os.path.exists(path):
                n = fix(path, actual)
                total += n
                if n:
                    print("updated %-28s %d claim(s) -> %d"
                          % (os.path.basename(path), n, actual))
        print("\n%d claim(s) rewritten to %d" % (total, actual))
        return 0
    print("%s holds %d data row(s)\n" % (os.path.basename(csv_path), actual))

    total, wrong = 0, []
    for path in docs:
        if not os.path.exists(path):
            print("skipped (not found):", path)
            continue
        for n, claimed, line in claims(path):
            total += 1
            ok = claimed == actual
            if not ok:
                wrong.append((path, n, claimed, line))
            print("  %-28s line %-5d %-7d %s"
                  % (os.path.basename(path), n, claimed, "ok" if ok else "WRONG"))

    if wrong:
        print("\nWRONG — these claim a row count the registry does not have:")
        for path, n, claimed, line in wrong:
            print("  %s:%d claims %d, actual %d"
                  % (os.path.basename(path), n, claimed, actual))
            print("      %s" % (line[:120],))
    print("\n%d row-count claim(s) checked, %d wrong" % (total, len(wrong)))
    return 1 if wrong else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
