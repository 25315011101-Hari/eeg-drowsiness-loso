"""Build the separate highlights file the submission system asks for.

    python3 tools/build_highlights.py                 # into docx/
    python3 tools/build_highlights.py --out-dir <dir> # somewhere else

The guide for authors asks for the highlights twice: in the article, and again on
their own.

    "Submit highlights as a separate editable file in the online submission system."

The five bullets live in manuscript/ABSTRACT.md, which is where they belong -- beside
the abstract they summarise -- and they reach this file through manuscript/MANUSCRIPT.md,
the assembled text, so that the highlights submitted are by construction the highlights
in the paper submitted. Typing them a second time into a Word document would create a
second place for them to be right, and a second place for them to go stale; this project
has already lost one correction that way (tools/check_generated.py exists because of it).

WHAT IS IN THE FILE, AND WHAT IS NOT

A heading reading "Highlights", then the five bullets. Nothing else: not the title,
not the authors, not the abstract. The guide says only "a separate editable file" and
does not say what belongs inside one, so this is the smallest file that answers the
request, chosen by the corresponding author on 7 October 2026. The paper's title was
considered and left out, because whether this journal wants identifying material in a
separately uploaded file has not been read at the source, and an unchecked guess is
worse than a plain file.

WHAT THIS SCRIPT REFUSES TO DO

Build a file that breaks the guide's limits. The count of bullets and the length of
each are checked BEFORE pandoc is called, against tools/journal_requirements.json --
the same quoted limits tools/check_frontmatter.py reads, not a second copy of the
numbers. If the highlights are out of range the file is not written at all, because a
file that exists is a file somebody can upload.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from tools import build_docx, check_frontmatter  # noqa: E402

MANUSCRIPT = build_docx.MANUSCRIPT
HEADING = "Highlights"


def bullets_from(text):
    """The five highlight bullets, read the way check_frontmatter reads them."""
    block = check_frontmatter.sections(text).get("highlights")
    if block is None:
        raise SystemExit("%s has no '## Highlights' section. It is assembled from "
                         "manuscript/ABSTRACT.md; if the heading was renamed, rename it "
                         "there rather than teaching this script a second spelling."
                         % MANUSCRIPT)
    found = [l[2:].strip() for l in block.splitlines() if l.startswith("- ")]
    if not found:
        raise SystemExit("the '## Highlights' section of %s carries no bullets"
                         % MANUSCRIPT)
    return found


def within_the_guides_limits(found):
    """Refuse to write a file the guide would reject. Limits are quoted, not remembered."""
    data = check_frontmatter.requirements()
    L = check_frontmatter.limits(data)
    problems = []
    if not L["highlights_min"] <= len(found) <= L["highlights_max"]:
        problems.append("%d bullet(s); the guide allows %d to %d"
                        % (len(found), L["highlights_min"], L["highlights_max"]))
    for i, b in enumerate(found, 1):
        if len(b) > L["highlight_chars"]:
            problems.append("bullet %d is %d character(s) over the limit of %d: %r"
                            % (i, len(b) - L["highlight_chars"],
                               L["highlight_chars"], b[:50]))
    if problems:
        for p in problems:
            print("PROBLEM:", p)
        raise SystemExit("no file was written. Fix the highlights in "
                         "manuscript/ABSTRACT.md and rebuild the manuscript.")
    return L, data


def audit(found, path):
    """Check the built document carries every bullet, once, unaltered."""
    with zipfile.ZipFile(path) as z:
        doc = z.read("word/document.xml").decode("utf-8")
    text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", doc))

    problems = []
    if HEADING not in text:
        problems.append("the heading %r is not in the document" % HEADING)
    for i, b in enumerate(found, 1):
        n = text.count(b)
        if n != 1:
            problems.append("bullet %d appears %d time(s) in the document, expected 1: %r"
                            % (i, n, b[:50]))
    # One list item per bullet and no more: a lost bullet and a duplicated one both
    # leave the text looking plausible, and only the count says which happened.
    items = doc.count("<w:numPr>")
    if items != len(found):
        problems.append("the document has %d list item(s) and the manuscript has %d"
                        % (items, len(found)))
    return problems


def run(out_dir):
    source = os.path.join(HERE, MANUSCRIPT)
    if not os.path.exists(source):
        raise SystemExit("%s does not exist" % MANUSCRIPT)
    with open(source, encoding="utf-8") as fh:
        text = fh.read()
    bid = build_docx.build_id(text, MANUSCRIPT)
    found = bullets_from(text)
    L, data = within_the_guides_limits(found)

    stamp = datetime.date.today().isoformat()
    name = "Highlights_BSPC_%s_build_%s.docx" % (stamp, bid)
    out_dir = os.path.join(HERE, out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)

    feed = os.path.join(out_dir, ".highlights.md")
    with open(feed, "w", encoding="utf-8") as fh:
        fh.write("# %s\n\n" % HEADING)
        for b in found:
            fh.write("- %s\n" % b)

    ref = build_docx.reference_doc(os.path.join(out_dir, ".reference-highlights.docx"))
    proc = subprocess.run(["pandoc", feed, "-o", out, "--standalone",
                           "--reference-doc", ref],
                          capture_output=True, text=True)
    os.remove(ref)
    if proc.returncode != 0:
        os.remove(feed)
        raise SystemExit("pandoc failed:\n" + (proc.stderr or proc.stdout))
    os.remove(feed)

    print("wrote %s" % os.path.relpath(out, HERE))
    print("  build %s · %s" % (bid, stamp))
    print("  source           the '## Highlights' section of %s" % MANUSCRIPT)
    print("  limits           %d to %d bullets, %d characters each, read from "
          "journal_requirements.json (guide read %s)"
          % (L["highlights_min"], L["highlights_max"], L["highlight_chars"],
             data["verified"]["date"]))
    for i, b in enumerate(found, 1):
        print("  %d  %3d  %s" % (i, len(b), b))

    problems = audit(found, out)
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        print("The file was written but does not match the manuscript. Do not submit it.")
        return 1
    print("  audit            all %d bullet(s) present once, unaltered, under the heading"
          % len(found))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="docx",
                    help="where to write the .docx (default: docx/)")
    args = ap.parse_args(argv)
    return run(args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
