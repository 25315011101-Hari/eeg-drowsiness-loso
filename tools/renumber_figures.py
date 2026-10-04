"""Apply a figure renumbering to every citation, caption, file name and check at once.

    python3 tools/renumber_figures.py MAP.json              # dry run, prints every change
    python3 tools/renumber_figures.py MAP.json --apply      # and makes them

Why this is a script. A figure's number appears in at least six unrelated places: the
prose that cites it, the caption under it, the alt text of the embed, the name of the
PNG and the PDF, the provenance listing, and the split map. Renumbering by hand
changes some of them, and the failure is silent -- a sentence that says "Figure 4" and
points at the recalibration plot reads perfectly and is simply wrong.

The map is JSON, old paper number to new paper number:

    {"6": "1", "1": "2", "2": "3", "3": "4", "4": "5", "5": "6"}

Two rules make it safe.

  * Every substitution is computed from the ORIGINAL text in a single pass. Applying
    the map one entry at a time is what turns 1 into 2 and then 2 into 3 in the same
    sentence, and it is the reason this is not a sequence of sed commands.
  * Nothing outside the declared file list is touched, and inside it nothing on a
    PROTECTED line is touched. Some sentences in this repository are about what the
    numbering USED to be -- the note recording the 19 September renumbering, the
    snapshot script's account of a bundle that mismatched, a test's explanation of
    which figure a claim used to live in. Rewriting those would not update history;
    it would falsify it.

The Python function names in src/figures.py are deliberately NOT the paper's numbers
and are left alone: figure0() has drawn figure1_study_design since the figures were
first written. Only the paper's numbering and the file stems that carry it move.

What it does not do, and what must follow it: regenerate the provenance listing, the
split-map page and the manuscript, then run preflight. The script prints the commands.
"""

import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where a paper figure number or a figure file stem can appear. Anything not listed
# here is not rewritten, which is deliberate: the blast radius is declared, not
# discovered at run time.
FILES = [
    "manuscript/ARCHITECTURES.md",
    "manuscript/RESULTS.md",
    "manuscript/DISCUSSION.md",
    "manuscript/METHODOLOGY.md",
    "manuscript/EXPERIMENTAL_SETUP.md",
    "manuscript/INTRODUCTION.md",
    "manuscript/ABSTRACT.md",
    "manuscript/CONCLUSION.md",
    "manuscript/REPRODUCIBILITY.md",
    "tools/split_map.json",
    "tools/figure_provenance.py",
    "src/figures.py",
    "tests/test_pipeline.py",
]

# Lines that are ABOUT the old numbering and must keep it. Matched as substrings, and
# each one says why, because an unexplained exclusion is how a real reference gets
# skipped by accident.
PROTECTED = {
    "renumbered into citation order on 19 September 2026":
        "the test's own note on what the numbering was before that renumbering",
    "Numbered on 19 September 2026 in order of first citation":
        "the status page's record of the previous renumbering",
    "The first had a Figure 2 and a registry from different":
        "tools/snapshot.py's account of a bundle that was already wrong; history",
    "It was Figure 1 until the figures were":
        "the same historical note, continued onto its own line",
}

# "Figure 4", "**Figure 4**", "Figure S1" -- the number only is replaced.
CITE = re.compile(r"\bFigure (S?\d+)\b")
# "figure4_brier_partition", including inside ../figures/... paths and test lists.
STEM = re.compile(r"\bfigure(\d+)(_[a-z0-9_]+)\b")
# "test_figure_4_partition_matches..." -- a test named for the figure it checks.
TESTNAME = re.compile(r"\btest_figure_(\d+)_")


def load_map(path):
    with open(path) as fh:
        m = json.load(fh)
    if sorted(m) != sorted(set(m.values())):
        raise SystemExit("the map is not a permutation: %r maps onto %r"
                         % (sorted(m), sorted(set(m.values()))))
    return m


def protected(line):
    for needle, why in PROTECTED.items():
        if needle in line:
            return why
    return None


def rewrite(line, m):
    """One pass over the original line. Every group is looked up in the original map."""
    def cite(mo):
        return "Figure %s" % m.get(mo.group(1), mo.group(1))

    def stem(mo):
        return "figure%s%s" % (m.get(mo.group(1), mo.group(1)), mo.group(2))

    def testname(mo):
        return "test_figure_%s_" % m.get(mo.group(1), mo.group(1))

    out = CITE.sub(cite, line)
    out = STEM.sub(stem, out)
    out = TESTNAME.sub(testname, out)
    return out


def figure_keys_block(text, m):
    """Remap the KEYS of split_map.json's "figures" object, and only those.

    The table numbers live in the same file under the same spellings, so a whole-file
    substitution on '"6": {' would renumber Table 6 as well. This bounds the edit to
    the figures object by brace depth.
    """
    start = text.find('"figures": {')
    if start < 0:
        return text, []
    i = text.index("{", start)
    depth, j = 0, i
    while j < len(text):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    block = text[i:j + 1]
    changes = []

    def key(mo):
        new = m.get(mo.group(1), mo.group(1))
        if new != mo.group(1):
            changes.append('figures key "%s" -> "%s"' % (mo.group(1), new))
        return '%s"%s": {' % (mo.group(1) and "", new)

    # Only keys at the top level of the figures object: two-space-plus indentation
    # followed by a quoted number and a brace.
    new_block = re.sub(r'"(S?\d+)":\s*\{', key, block)
    return text[:i] + new_block + text[j + 1:], changes


def stem_renames(m):
    """Old stem to new stem, read off the files that exist rather than assumed."""
    out = {}
    d = os.path.join(HERE, "figures")
    for name in sorted(os.listdir(d)):
        base, ext = os.path.splitext(name)
        if ext not in (".png", ".pdf"):
            continue
        mo = re.match(r"^figure(\d+)(_[a-z0-9_]+)$", base)
        if not mo:
            continue
        new = m.get(mo.group(1))
        if new and new != mo.group(1):
            out.setdefault(base, "figure%s%s" % (new, mo.group(2)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map", help="JSON file, old figure number to new")
    ap.add_argument("--apply", action="store_true",
                    help="write the changes; without it nothing is modified")
    a = ap.parse_args(argv)

    m = load_map(a.map)
    print("figure renumbering: %s"
          % ", ".join("%s->%s" % kv for kv in sorted(m.items())))
    print("%s\n" % ("APPLYING" if a.apply else "DRY RUN -- nothing will be written"))

    total, skipped = 0, 0
    for rel in FILES:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            print("  missing, skipped: %s" % rel)
            continue
        text = open(path).read()
        lines = text.splitlines(True)
        out, hits = [], []
        for n, line in enumerate(lines, 1):
            why = protected(line)
            if why:
                out.append(line)
                if CITE.search(line) or STEM.search(line):
                    skipped += 1
                    print("  %s:%d PROTECTED (%s)" % (rel, n, why))
                continue
            new = rewrite(line, m)
            out.append(new)
            if new != line:
                hits.append((n, line.rstrip("\n"), new.rstrip("\n")))
        joined = "".join(out)
        extra = []
        if rel.endswith(".json"):
            joined, extra = figure_keys_block(joined, m)
        if hits or extra:
            print("  %s: %d line(s)" % (rel, len(hits) + len(extra)))
            for n, before, after in hits:
                print("      %d- %s" % (n, before.strip()[:100]))
                print("      %d+ %s" % (n, after.strip()[:100]))
            for e in extra:
                print("      %s" % e)
            total += len(hits) + len(extra)
        if a.apply and joined != text:
            with open(path, "w") as fh:
                fh.write(joined)

    renames = stem_renames(m)
    print("\nfigure files:")
    for old, new in sorted(renames.items()):
        for ext in (".png", ".pdf"):
            print("  %s%s -> %s%s" % (old, ext, new, ext))
    if a.apply and renames:
        # Two stages, because 1->2 and 2->3 collide if done in place.
        tmp = os.path.join(HERE, "figures", ".renumber")
        os.makedirs(tmp, exist_ok=True)
        for old, new in renames.items():
            for ext in (".png", ".pdf"):
                src = os.path.join(HERE, "figures", old + ext)
                if os.path.exists(src):
                    shutil.move(src, os.path.join(tmp, new + ext))
        for name in sorted(os.listdir(tmp)):
            shutil.move(os.path.join(tmp, name),
                        os.path.join(HERE, "figures", name))
        os.rmdir(tmp)

    print("\n%d text change(s), %d protected line(s) left alone, %d file rename(s)"
          % (total, skipped, len(renames) * 2))
    if a.apply:
        print("\nnow, in this order:")
        print("  python3 -m src.figures")
        print("  python3 tools/figure_provenance.py")
        print("  python3 tools/check_split_map.py --write")
        print("  python3 tools/preflight.py")
    else:
        print("\nre-run with --apply to make these changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
