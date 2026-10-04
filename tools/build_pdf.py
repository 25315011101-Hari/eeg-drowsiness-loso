"""Build the manuscript PDF from manuscript/MANUSCRIPT.md, reproducibly.

    python3 tools/build_pdf.py                 # the article
    python3 tools/build_pdf.py --supplementary # the supplementary document
    python3 tools/build_pdf.py --out-dir pdf   # somewhere other than pdf/

Until 3 October 2026 the PDF was the one artefact in this repository that no command
produced. manuscript/REPRODUCIBILITY.md describes a filename convention for it --
`Manuscript_BSPC_<date>_build_<id>.pdf`, "built, not edited" -- and an archive/ folder
of superseded drafts that does not exist. So the convention was documented and the
PDFs were made by hand, outside the repository, which is the same gap the registry and
the figure provenance trail were built to close.

What this script guarantees, and why each guarantee is here:

  * The filename carries the build id, so a copy in someone's downloads folder can be
    checked against what the repository produces. That was the stated reason for the
    convention, and reviewers had repeatedly read superseded copies before it.
  * The build id in the filename is read from the manuscript's own stamp rather than
    recomputed, so the PDF cannot claim an id the text does not carry.
  * The font is FreeSerif, chosen because it covers every non-ASCII character the
    manuscript uses -- including U+26A0, which DejaVu Serif lacks. A missing glyph is
    dropped silently by XeLaTeX, and a silently dropped character in a paper about
    exact numbers is the kind of loss this repository exists to prevent.
  * Any "Missing character" in the TeX log is a FAILURE, not a warning. No PDF is
    kept if a glyph was dropped.
  * Figures are resolved from manuscript/, because the manuscript embeds them as
    ../figures/<stem>.png relative to its own folder.

One presentation normalisation is applied to the Markdown before pandoc sees it, and
it is applied here rather than in the manuscript:

  * A heading inside a block quote (`> ### ...`) becomes bold text inside the quote.
    LaTeX cannot open a list after a sectioning command inside a quote environment,
    and the data-availability BLOCKER notice is written that way. The manuscript is
    not changed for the convenience of a typesetter, so the transform lives here and
    is reported when it fires.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUSCRIPT = os.path.join("manuscript", "MANUSCRIPT.md")
SUPPLEMENT = os.path.join("manuscript", "SUPPLEMENTARY.md")

# Covers every non-ASCII character in the manuscript, checked against the actual
# character set rather than assumed. Changing this font means re-checking that.
FONT = "FreeSerif"

BUILD_ID = re.compile(r"(?m)^\*Build ([0-9a-f]{6,})\b")
QUOTED_HEADING = re.compile(r"(?m)^(>\s*)#{1,6}\s+(.*?)\s*$")


def build_id(text, path):
    """The id the manuscript stamps itself with -- not recomputed here."""
    m = BUILD_ID.search(text)
    if not m:
        raise SystemExit("%s carries no build stamp; run tools/build_manuscript.py "
                         "first so the PDF can be named after the text it contains"
                         % path)
    return m.group(1)


def normalise(text):
    """Presentation-only fixes, each reported so none of them is invisible."""
    notes = []

    def demote(m):
        notes.append(m.group(2)[:60])
        return "%s**%s**" % (m.group(1), m.group(2))
    text = QUOTED_HEADING.sub(demote, text)
    for n in notes:
        print("  note: heading inside a block quote set as bold instead: %r" % n)
    return text


def run(source, out_dir, label):
    path = os.path.join(HERE, source)
    if not os.path.exists(path):
        raise SystemExit("%s does not exist" % source)
    with open(path) as fh:
        text = fh.read()

    bid = build_id(open(os.path.join(HERE, MANUSCRIPT)).read(), MANUSCRIPT)
    stamp = datetime.date.today().isoformat()
    name = "%s_BSPC_%s_build_%s.pdf" % (label, stamp, bid)
    os.makedirs(os.path.join(HERE, out_dir), exist_ok=True)
    out = os.path.join(HERE, out_dir, name)

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in.md")
        with open(src, "w") as fh:
            fh.write(normalise(text))
        log = os.path.join(tmp, "tex.log")
        cmd = ["pandoc", src, "-o", out,
               "--pdf-engine=xelatex",
               "--pdf-engine-opt=-interaction=nonstopmode",
               "--resource-path=%s" % os.path.join(HERE, "manuscript"),
               "-V", "mainfont=%s" % FONT,
               "-V", "geometry:a4paper,margin=2.5cm",
               "-V", "fontsize=10pt",
               "-V", "linkcolor=blue",
               # No table of contents. The journal's guide requires none, a submitted
               # article does not carry one, and it added five pages of front matter
               # to a 42-page manuscript. Dropped on the corresponding author's
               # decision of 3 October 2026.
               "--verbose"]
        proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        with open(log, "w") as fh:
            fh.write(proc.stdout + proc.stderr)
        blob = proc.stdout + proc.stderr

    if proc.returncode != 0 or not os.path.exists(out):
        tail = [l for l in blob.splitlines() if l.startswith("!")][:5]
        raise SystemExit("pandoc/xelatex failed:\n  %s" % "\n  ".join(tail or
                         blob.splitlines()[-5:]))

    # A dropped glyph is a lost character, and this manuscript's whole point is that
    # characters are not lost. Refuse the PDF rather than ship it with a hole.
    missing = sorted(set(re.findall(r"Missing character: There is no (.)", blob)))
    if missing:
        os.remove(out)
        raise SystemExit("the font %s has no glyph for %s, so those characters would "
                         "be dropped silently. The PDF was deleted rather than "
                         "delivered with holes in it. Pick a font that covers them."
                         % (FONT, " ".join(repr(c) for c in missing)))

    pages = None
    try:
        import pypdf
        pages = len(pypdf.PdfReader(out).pages)
    except Exception:
        pass
    print("wrote %s" % os.path.relpath(out, HERE))
    print("  build %s · %s · %s" % (bid, stamp, FONT))
    if pages:
        print("  %d pages" % pages)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--supplementary", action="store_true",
                    help="build the supplementary document instead of the article")
    ap.add_argument("--out-dir", default="pdf")
    args = ap.parse_args(argv)
    if args.supplementary:
        run(SUPPLEMENT, args.out_dir, "Supplementary")
    else:
        run(MANUSCRIPT, args.out_dir, "Manuscript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
