"""Check the four files that go to the journal, together, as one package.

    python3 tools/check_submission_package.py            # checks docx/
    python3 tools/check_submission_package.py <dir>      # checks somewhere else

Build the package first:

    python3 tools/build_docx.py
    python3 tools/build_highlights.py
    python3 tools/build_pdf.py
    python3 tools/build_pdf.py --supplementary

WHY THIS EXISTS

Each builder audits its own output and none of them can see the others. Four files
leave this repository together, and the ways a submission goes wrong are mostly ways
one file disagrees with another: a .docx built before the last manuscript change, a
highlights file from a different build, a supplementary PDF whose tables the article
cites and the supplement does not carry. No single builder can catch any of those.

The collision check below exists for a specific reason. On 7 October 2026 the
corresponding author opened the supplementary PDF and found "DeepConvNet8,212" --
a model name printed on top of the next column's number, eight times across two
tables. Every automated check in this repository passed on that file. It was found by
a person reading it, and two detectors written for it afterwards both reported "no
collisions" before one was written that worked. A check that can only be performed by
a person is a check that will eventually not be performed, so it is here.

WHAT IS NOT CHECKED, DELIBERATELY

  * Whether the paper is any good, or whether its claims hold. That is what the rest
    of tools/preflight.py is for.
  * Whether the guide's current wording still says what tools/journal_requirements.json
    quotes. No script can do that; re-reading the guide is a listed item.
  * The competing-interest declaration submitted through the journal's own tool. It
    is not a file in this package and cannot be seen from here.
"""

import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from tools import build_docx, build_highlights, check_frontmatter  # noqa: E402

MANUSCRIPT = os.path.join(HERE, build_docx.MANUSCRIPT)
SUPPLEMENT = os.path.join(HERE, "manuscript", "SUPPLEMENTARY.md")

# What the three builders are named to produce. The build id is not written here; it
# is read from the manuscript, and every file must carry that one.
EXPECTED = {
    "manuscript docx":   ("Manuscript_BSPC_%s_build_%s.docx", "the editable source file the guide requires"),
    "highlights docx":   ("Highlights_BSPC_%s_build_%s.docx", "the separate editable highlights file"),
    "manuscript pdf":    ("Manuscript_BSPC_%s_build_%s.pdf", "the reading copy"),
    "supplementary pdf": ("Supplementary_BSPC_%s_build_%s.pdf", "published exactly as received"),
}

PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]{2,60}>")

# The declarations the article has to carry, by the heading each one is written under.
# Named here rather than counted, because the failure this catches is one of them
# going missing, and a count cannot tell you which. The wording of each declaration is
# the authors'; this only asks whether it is in the file that leaves the building.
DECLARATIONS = [
    "Declaration of competing interest",
    "CRediT author contribution statement",
    "Acknowledgements",
    "Funding",
    "Data availability",
]


def say(ok, label, detail=""):
    print("  %-22s %-4s %s" % (label, "PASS" if ok else "FAIL", detail))
    return ok


def build_id():
    with open(MANUSCRIPT, encoding="utf-8") as fh:
        return build_docx.build_id(fh.read(), build_docx.MANUSCRIPT)


def find(out_dir, pattern, bid):
    """The one file matching this builder's naming, whatever date it carries."""
    stem, ext = pattern.rsplit("_build_", 1)[0], pattern.rsplit(".", 1)[1]
    label = stem.split("_BSPC_")[0]
    hits = [n for n in sorted(os.listdir(out_dir))
            if re.match(r"^%s_BSPC_\d{4}-\d{2}-\d{2}_build_[0-9a-f]+\.%s$"
                        % (re.escape(label), ext), n)]
    return hits


def missing_declarations(path):
    """Which required declarations are absent from the built .docx.

    A function rather than four lines inside run(), so that a test can call it on a
    real built document. The comparison is over the document's visible text: the
    builder strips the not-for-submission blocks, so a declaration that survives only
    inside one of those is absent here, which is the point.
    """
    with zipfile.ZipFile(path) as z:
        doc = z.read("word/document.xml").decode("utf-8")
    text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", doc))
    return [d for d in DECLARATIONS if d not in text]


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True).stdout


def pdf_collisions(path):
    """Two words printed on top of each other, anywhere in the file.

    Measured from the word boxes, not from the extracted text: poppler reports a
    collision sometimes as overlapping boxes and sometimes as one merged token, and a
    detector that looks for only one of those reports a clean file either way. Both
    are counted here, which is the difference between the two detectors that failed on
    7 October 2026 and the one that worked.
    """
    xml = subprocess.run(["pdftotext", "-bbox", path, "-"],
                         capture_output=True, text=True).stdout
    page, hits = 0, []
    for pm in re.finditer(r"<page[^>]*>(.*?)</page>", xml, re.S):
        page += 1
        rows = {}
        for wm in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" '
                              r'xMax="([\d.]+)" yMax="[\d.]+">(.*?)</word>', pm.group(1)):
            rows.setdefault(round(float(wm.group(2))), []).append(
                (float(wm.group(1)), float(wm.group(3)), wm.group(4)))
        for y in sorted(rows):
            ws = sorted(rows[y])
            for i in range(len(ws) - 1):
                # -0.5 pt of slack: an accented letter and its mark are reported as
                # two boxes that touch, and that is not a collision.
                if ws[i + 1][0] - ws[i][1] < -0.5:
                    hits.append("page %d: %r on %r" % (page, ws[i][2], ws[i + 1][2]))
    # A merged pair reads as a word run straight into a NUMBER: "DeepConvNet8,212",
    # "ShallowConvNet0.2049". The digits have to look like a value for this to be a
    # collision rather than a name -- the first version of this line required only one
    # digit and reported "python3", which appears in the manuscript's own commands.
    merged = [w for w in pdf_text(path).split()
              if re.match(r"^[A-Za-z]{4,}\d[\d.,]{2,}$", w.strip(".,;:()"))]
    return hits, sorted(set(merged))


def main(argv):
    out_dir = os.path.join(HERE, argv[0] if argv else "docx")
    if not os.path.isdir(out_dir):
        raise SystemExit("%s does not exist. Build the package first; the commands are "
                         "at the top of this file." % os.path.relpath(out_dir, HERE))
    if not shutil_which("pdftotext"):
        raise SystemExit("pdftotext is not installed, and two of these checks read the "
                         "built PDFs. Install poppler-utils and run this again rather "
                         "than treating a missing tool as a pass.")

    bid = build_id()
    print("submission package in %s" % os.path.relpath(out_dir, HERE))
    print("manuscript build %s\n" % bid)
    ok = []

    # 1. the four files, and all of them from this build
    paths = {}
    for label, (pattern, why) in EXPECTED.items():
        hits = find(out_dir, pattern, bid)
        if len(hits) != 1:
            ok.append(say(False, label,
                          "%d file(s) match; expected exactly one -- %s"
                          % (len(hits), why)))
            continue
        name = hits[0]
        paths[label] = os.path.join(out_dir, name)
        carried = name.rsplit("_build_", 1)[1].split(".")[0]
        ok.append(say(carried == bid, label,
                      name if carried == bid else
                      "%s carries build %s; the manuscript is at %s -- rebuild"
                      % (name, carried, bid)))
    if not all(ok):
        print("\nPACKAGE INCOMPLETE. Nothing below was checked.")
        return 1

    print("")
    # 2. the manuscript .docx still matches the manuscript
    feed = build_docx.without_build_stamp(MANUSCRIPT, out_dir)
    doc = zipfile.ZipFile(paths["manuscript docx"]).read("word/document.xml").decode()
    tables = len(build_docx.TABLE.findall(doc))
    problems, _notes = build_docx.audit(feed, paths["manuscript docx"], tables)
    os.remove(feed)
    ok.append(say(not problems, "docx matches source",
                  "%d tables, every image and every non-ASCII character present"
                  % tables if not problems else problems[0]))

    # 3. the highlights file carries this manuscript's bullets, within the guide's limits
    with open(MANUSCRIPT, encoding="utf-8") as fh:
        bullets = build_highlights.bullets_from(fh.read())
    hp = build_highlights.audit(bullets, paths["highlights docx"])
    L = check_frontmatter.limits(check_frontmatter.requirements())
    over = [b for b in bullets if len(b) > L["highlight_chars"]]
    in_range = L["highlights_min"] <= len(bullets) <= L["highlights_max"]
    ok.append(say(not hp and not over and in_range, "highlights match",
                  "%d bullets, longest %d of %d characters"
                  % (len(bullets), max(len(b) for b in bullets), L["highlight_chars"])
                  if not (hp or over) else (hp[0] if hp else "a bullet is over the limit")))

    # 3a. the declarations the journal requires are actually in the submitted file
    #
    # They are checked in the BUILT .docx rather than in the sources, because the
    # builder strips the not-for-submission blocks and a declaration that only exists
    # inside one of those would read as present everywhere except where it counts. The
    # competing-interest declaration also goes through the journal's own tool; that
    # submission cannot be seen from here, and this check is not a substitute for it.
    absent = missing_declarations(paths["manuscript docx"])
    ok.append(say(not absent, "declarations present",
                  "all %d in the submitted .docx: %s"
                  % (len(DECLARATIONS), ", ".join(DECLARATIONS))
                  if not absent else "missing from the .docx: " + ", ".join(absent)))

    # 4. no two words printed on top of each other, in either PDF
    for label in ("manuscript pdf", "supplementary pdf"):
        hits, merged = pdf_collisions(paths[label])
        ok.append(say(not hits and not merged, "%s legible" % label.split()[0],
                      "no overlapping text" if not (hits or merged)
                      else "; ".join((hits + merged)[:3])))

    # 5. every supplementary item the article cites is in the supplement, with a caption
    with open(MANUSCRIPT, encoding="utf-8") as fh:
        article = fh.read()
    supp = pdf_text(paths["supplementary pdf"])
    cited = sorted(set(re.findall(r"\b((?:Table|Figure) S\d+)\b", article)))
    missing = [c for c in cited if c + "." not in supp]
    ok.append(say(not missing, "supplement complete",
                  "%d item(s) cited by the article, each present with its caption: %s"
                  % (len(cited), ", ".join(cited)) if not missing
                  else "cited but not in the supplement: " + ", ".join(missing)))

    # 6. nothing unfilled left anywhere a reader will see
    found = []
    for label in ("manuscript pdf", "supplementary pdf"):
        for m in PLACEHOLDER.finditer(pdf_text(paths[label])):
            if "@" not in m.group(0) and "/" not in m.group(0):
                found.append("%s: %s" % (label, m.group(0)))
    ok.append(say(not found, "no placeholders",
                  "none in either built document" if not found else "; ".join(found[:3])))

    bad = ok.count(False)
    print("\n%s  (%d of %d checks passed)"
          % ("PACKAGE READY" if not bad else "%d CHECK(S) FAILED" % bad,
             len(ok) - bad, len(ok)))
    if not bad:
        print("\nThis says the four files agree with the manuscript and with each other.\n"
              "It does not say the submission is complete: the competing-interest\n"
              "declaration goes through the journal's own tool and is not a file here,\n"
              "and the guide's wording still has to be re-read at the source.")
    return 1 if bad else 0


def shutil_which(name):
    import shutil
    return shutil.which(name)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
