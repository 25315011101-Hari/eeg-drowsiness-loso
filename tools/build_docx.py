"""Build the editable manuscript the journal asks for, and refuse a wrong one.

    python3 tools/build_docx.py                 # the article, into docx/
    python3 tools/build_docx.py --out-dir <dir> # somewhere other than docx/

The guide for authors is explicit, and it is why this script exists at all:

    "Save files in an editable format, using the extension .doc/.docx for Word
     files and .tex for LaTeX files. A PDF is not an acceptable source file."

So the PDF this project has built since 3 October 2026 cannot be submitted. The
same twelve section files produce this .docx instead; nothing in the manuscript
is written twice. The sentence above is recorded in tools/journal_requirements.json
with the date the guide was read, so that it is a quotation this repository holds
rather than a rule somebody remembers.

THE FILENAME, AND WHY IT IS NOT "Manuscript.docx"

manuscript/REPRODUCIBILITY.md section 1 sets the convention
`<label>_BSPC_<date>_build_<id>.<ext>`, and gives the reason: six reviews of this
work each quoted at least one sentence from a superseded draft, because every build
carried the same filename and a downloads folder filled with `… (1)`, `… (2)`. That
reason was written when the PDF was the file under review. It now applies to this
file instead, because this is the one that goes to the journal, so the convention
moves with the role rather than staying with the extension.

The build id is READ from the manuscript's own stamp, never recomputed, so a .docx
cannot be named after an id its text does not carry. tools/build_pdf.py does the
same thing for the same reason; the two scripts agree because they read one stamp.

The supplementary document is deliberately NOT built here. manuscript/SUPPLEMENTARY.md
carries no build stamp, so it cannot be named under the convention above, and whether
the guide's "editable source file" sentence reaches supplementary material has not
been read at the source. Both are open questions, named here rather than answered by
a default.

WHY THERE IS A POST-PROCESSING STEP, AND WHY IT IS NOT A HAND EDIT

A plain `pandoc MANUSCRIPT.md -o x.docx` converts faithfully -- every table,
every figure and all twenty-six non-ASCII characters survive, measured on
4 October 2026. What it cannot do is fit a ten-column table across a portrait
page. Rendered through Word, that one table's headers broke into stacks of
single words and three of its six header phrases were no longer readable.
Making the type smaller does not fix it: at 8 pt with 2 cm margins the table was
still unreadable, because ten columns do not fit in 17 cm however small the
letters are. A landscape section for that one table does fix it: all ten columns,
all three rows, one page.

The repair therefore has to happen after pandoc has written the file. The
temptation is to open the .docx in Word and widen the columns by hand. That is
forbidden here, and not as a matter of taste: this project lost a correction
exactly that way on 2 October 2026, when a generated file was edited instead of
its generator and the next run silently discarded the edit. tools/check_generated.py
exists because of it. A .docx built from MANUSCRIPT.md is a generated file like
any other, so the landscape section is applied by this script, on every build,
from the structure of the document rather than from anybody's memory of which
table was the wide one.

WHAT IS APPLIED

  1. Page setup, through a pandoc reference document: A4, 2 cm margins. Pandoc's
     own default leaves the page setup empty, which means Word's defaults, which
     means no stable basis for a landscape section.
  2. A landscape section around every table wider than LANDSCAPE_MIN_COLUMNS,
     and only those. Today exactly one table qualifies. If the manuscript gains
     or loses a wide table the count changes and this script says so, rather than
     carrying a hidden rule about "the Table 1 fix".

WHAT IS NOT APPLIED, DELIBERATELY

  * No change to the manuscript. The wide table is wide because it reports a
    two-by-two design in ten columns, and splitting or transposing it to suit a
    page is letting the paper be edited by the page.
  * No global landscape, and no global small type. Both were measured and
    neither was needed.
"""

import argparse
import collections
import datetime
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUSCRIPT = os.path.join("manuscript", "MANUSCRIPT.md")

# The id tools/build_manuscript.py stamps at the foot of the manuscript. Read, never
# recomputed -- see the docstring.
BUILD_ID = re.compile(r"(?m)^\*Build ([0-9a-f]{6,})\b")

# A4 in twips (1/1440 inch), 2 cm margins. Chosen because the default -- an empty
# <w:sectPr/> -- leaves every page property to the reader's copy of Word.
PAGE = ('<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"'
        ' w:header="709" w:footer="709" w:gutter="0"/>')
PORTRAIT = "<w:sectPr>" + PAGE + "</w:sectPr>"
LANDSCAPE = ("<w:sectPr>"
             '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
             '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"'
             ' w:header="709" w:footer="709" w:gutter="0"/>'
             "</w:sectPr>")

# Seven columns still fit a portrait A4 at this type size; eight is where the
# measured breakage began. The threshold is named rather than inlined so that the
# next person can see it is a measurement and not a preference.
LANDSCAPE_MIN_COLUMNS = 8

TABLE = re.compile(r"<w:tbl>.*?</w:tbl>", re.S)

# A table row that carries no properties of its own. The lookahead is what keeps
# keep_tables_together from giving a row a second <w:trPr>; see that function.
BARE_ROW = re.compile(r"<w:tr>(?!<w:trPr>)")


def build_id(text, path):
    """The id the manuscript stamps itself with -- not recomputed here."""
    m = BUILD_ID.search(text)
    if not m:
        raise SystemExit("%s carries no build stamp; run tools/build_manuscript.py "
                         "first so the .docx can be named after the text it contains"
                         % path)
    return m.group(1)


def reference_doc(path):
    """Pandoc's default reference document, with a real page setup written into it."""
    work = path + ".dir"
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    # Pandoc writes this one to a file rather than to stdout; asking for stdout
    # produces something that is not a zip and fails three lines later.
    default = os.path.join(work, "default.docx")
    subprocess.run(["pandoc", "-o", default,
                    "--print-default-data-file", "reference.docx"], check=True)
    with zipfile.ZipFile(default) as z:
        z.extractall(work)
    os.remove(default)

    doc = os.path.join(work, "word", "document.xml")
    with open(doc, encoding="utf-8") as fh:
        text = fh.read()
    if "<w:sectPr />" in text:
        text = text.replace("<w:sectPr />", PORTRAIT)
    elif "<w:sectPr" not in text:
        text = text.replace("</w:body>", PORTRAIT + "</w:body>")
    else:
        raise SystemExit("the reference document already carries a page setup this "
                         "script did not write; refusing to overwrite it blindly.")
    with open(doc, "w", encoding="utf-8") as fh:
        fh.write(text)

    if os.path.exists(path):
        os.remove(path)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(work):
            for name in files:
                full = os.path.join(root, name)
                z.write(full, os.path.relpath(full, work))
    shutil.rmtree(work)
    return path


def widen_wide_tables(path):
    """Put every table of LANDSCAPE_MIN_COLUMNS columns or more on its own landscape page."""
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        blobs = {i.filename: z.read(i.filename) for i in items}
    doc = blobs["word/document.xml"].decode("utf-8")

    spans = [(m.start(), m.end()) for m in TABLE.finditer(doc)]
    wide = [(a, b) for a, b in spans
            if doc[a:b].count("<w:gridCol") >= LANDSCAPE_MIN_COLUMNS]

    # Rebuilt back to front so that every offset stays valid while editing.
    for a, b in reversed(wide):
        doc = (doc[:a]
               + "<w:p><w:pPr>" + PORTRAIT + "</w:pPr></w:p>"
               + doc[a:b]
               + "<w:p><w:pPr>" + LANDSCAPE + "</w:pPr></w:p>"
               + doc[b:])
    if "<w:sectPr>" not in doc.split("</w:body>")[-2][-400:]:
        doc = doc.replace("</w:body>", PORTRAIT + "</w:body>")

    blobs["word/document.xml"] = doc.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for i in items:
            z.writestr(i, blobs[i.filename])

    return [doc[a:b].count("<w:gridCol") for a, b in wide], len(spans)


# Pandoc's smart typography rewrites some characters on the way into the document.
# Each one here is a substitution: a plain character disappears and a typographic
# one takes its place, one for one. They are declared so that the audit can tell a
# substitution from a corruption, and so that a NEW kind of rewrite -- which would
# be neither -- fails the build instead of passing unnoticed.
SUBSTITUTIONS = {
    "’": "'",   # right single quote, standing in for the typewriter apostrophe
    "“": '"',   # opening double quote
    "”": '"',   # closing double quote
}

# Pandoc also inserts non-breaking spaces, after an abbreviation that is followed by
# a citation or a number -- "Cui et al.<nbsp>[C1]", "pp.<nbsp>61-74" -- so the two do
# not break across a line. Nothing is consumed in exchange, so these cannot be
# balanced against anything; they are counted and reported instead of being ignored.
INSERTED = {" ": "non-breaking space, inserted after an abbreviation"}


def audit(source, path, tables):
    """Check the built file against the manuscript it was built from.

    A conversion that drops a table or a minus sign fails quietly: the file opens,
    the text reads, and the missing thing is only noticed by a reader -- or by a
    reviewer, which is worse. So the things that can go missing are counted on both
    sides.

    Counted, not merely listed. An earlier version of this function asked only
    whether each non-ASCII character still occurred somewhere in the document, which
    would have passed a build that turned 60 minus signs into 59. It also called
    pandoc's typographic rewrites a loss of nothing without checking that each one
    is paid for: 127 apostrophes become 127 right single quotes, and if those two
    numbers differ then something other than typography happened.
    """
    with open(source, encoding="utf-8") as fh:
        md = fh.read()
    with zipfile.ZipFile(path) as z:
        doc = z.read("word/document.xml").decode("utf-8")
        got_media = len([n for n in z.namelist() if n.startswith("word/media/")])
    text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", doc))

    problems, notes = [], []
    md_tables = len([l for l in md.split("\n")
                     if re.match(r"^\s*\|[\s:|-]+\|\s*$", l)])
    if tables != md_tables:
        problems.append("the manuscript has %d tables and the document has %d"
                        % (md_tables, tables))
    md_media = len(re.findall(r"!\[", md))
    if got_media != md_media:
        problems.append("the manuscript has %d images and the document embeds %d"
                        % (md_media, got_media))

    before, after = collections.Counter(md), collections.Counter(text)

    # 1. Nothing the manuscript carries may be thinned out.
    for ch in sorted(set(c for c in md if ord(c) > 127), key=ord):
        if after[ch] < before[ch]:
            problems.append("U+%04X %r occurs %d times in the manuscript and %d "
                            "times in the document"
                            % (ord(ch), ch, before[ch], after[ch]))

    # 2. Anything the document gained must be a declared substitution, and the
    #    substitution must balance: as many gained as the plain form lost.
    owed = collections.Counter()
    for ch in sorted(set(c for c in text if ord(c) > 127), key=ord):
        gained = after[ch] - before[ch]
        if gained <= 0:
            continue
        if ch in SUBSTITUTIONS:
            owed[SUBSTITUTIONS[ch]] += gained
        elif ch in INSERTED:
            notes.append("U+%04X inserted %d time(s): %s"
                         % (ord(ch), gained, INSERTED[ch]))
        else:
            problems.append("U+%04X %r appears %d time(s) in the document and not "
                            "in the manuscript, and is not a declared substitution"
                            % (ord(ch), ch, gained))
    for plain, gained in sorted(owed.items()):
        spent = before[plain] - after[plain]
        if gained != spent:
            problems.append("%r: the document gained %d typographic form(s) but the "
                            "manuscript's plain form fell by %d; a substitution that "
                            "does not balance is not a substitution"
                            % (plain, gained, spent))
        else:
            notes.append("%r -> typographic form, %d time(s), balanced" % (plain, gained))

    return problems, notes


# The stamp the builder writes at the foot of the manuscript. It is read by four
# tools -- build_pdf.py names the file from it, master_file.py takes the build id and
# word count, check_generated.py treats it as the volatile line, snapshot.py stamps a
# bundle with it -- so it stays in MANUSCRIPT.md and is removed here instead. It is
# the repository's own bookkeeping and not a sentence of the paper.
# No leading `^---\n\n`: the horizontal rules were removed from the manuscript on
# 8 October 2026 and the stamp no longer has one above it. The rest of the pattern is
# unchanged, and the check below still refuses to build if the stamp is not found at
# all, which is what stops a repository build stamp reaching a journal.
STAMP = re.compile(r"(?m)^\*Build [0-9a-f]+ · .*\n\*Rebuild:.*$")


def without_build_stamp(source, work_dir):
    """A copy of the manuscript with the build stamp removed, for pandoc to read."""
    with open(source, encoding="utf-8") as fh:
        md = fh.read()
    stripped = STAMP.sub("", md).rstrip() + "\n"
    if stripped == md:
        raise SystemExit("the build stamp was not found at the foot of %s. It is "
                         "written by tools/build_manuscript.py; if its wording changed, "
                         "change STAMP here rather than leaving the stamp in a file that "
                         "goes to a journal." % source)
    path = os.path.join(work_dir, ".manuscript-without-stamp.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(stripped)
    return path


def keep_tables_together(path):
    """Stop a table being broken across a page boundary where it need not be.

    Two settings, both of them Word's own: a row may not split across pages, and the
    paragraph before a table is kept with what follows it. Together they stop the
    caption and the first row being stranded at the foot of a page while the rest of
    the table starts the next one, which is what Table 6 did on 4 October 2026.

    A row's properties live in one <w:trPr>, and the schema allows a row exactly one
    of them. So a row that already has one is given the setting INSIDE it, and only a
    row without one is given a new one. Until 7 October 2026 this function added a
    <w:trPr> to every row unconditionally, which left the 25 header rows -- the ones
    pandoc had already given a <w:trPr> to carry <w:tblHeader> -- holding two, and
    reported 177 "rows" for a document of 152. LibreOffice tolerated it, so the defect
    survived the PDF built on 4 October; it was found by a test asserting the row count.
    """
    with zipfile.ZipFile(path) as z:
        items = z.infolist()
        blobs = {i.filename: z.read(i.filename) for i in items}
    doc = blobs["word/document.xml"].decode("utf-8")

    rows = doc.count("<w:trPr>")
    doc = doc.replace("<w:trPr>", "<w:trPr><w:cantSplit/>")
    # Rows with no properties of their own still need the setting, and only those:
    # the lookahead skips every row the line above has already served.
    bare = len(BARE_ROW.findall(doc))
    doc = BARE_ROW.sub("<w:tr><w:trPr><w:cantSplit/></w:trPr>", doc)

    blobs["word/document.xml"] = doc.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for i in items:
            z.writestr(i, blobs[i.filename])
    return rows + bare


def run(out_dir, label="Manuscript"):
    source = os.path.join(HERE, MANUSCRIPT)
    if not os.path.exists(source):
        raise SystemExit("%s does not exist" % MANUSCRIPT)
    with open(source, encoding="utf-8") as fh:
        bid = build_id(fh.read(), MANUSCRIPT)
    stamp = datetime.date.today().isoformat()
    name = "%s_BSPC_%s_build_%s.docx" % (label, stamp, bid)

    out_dir = os.path.join(HERE, out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)

    ref = reference_doc(os.path.join(out_dir, ".reference.docx"))
    feed = without_build_stamp(source, out_dir)
    # implicit_figures turns an image's alt text into a caption of its own, which this
    # manuscript already supplies as the paragraph below each figure. Left on, every
    # figure is captioned twice -- in the .docx and, since 3 October 2026, in the PDF.
    cmd = ["pandoc", feed, "-o", out, "--standalone", "--reference-doc", ref,
           "--from", "markdown-implicit_figures",
           "--resource-path", os.pathsep.join(
               [HERE, os.path.dirname(source), os.path.join(HERE, "figures")])]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        os.remove(ref)
        os.remove(feed)
        raise SystemExit("pandoc failed:\n" + (proc.stderr or proc.stdout))
    for line in (proc.stderr or "").splitlines():
        print("  pandoc:", line)

    widened, total = widen_wide_tables(out)
    rows_kept = keep_tables_together(out)
    os.remove(ref)

    print("wrote %s" % os.path.relpath(out, HERE))
    print("  build %s · %s" % (bid, stamp))
    print("  page setup       A4, 2 cm margins, from a generated reference document")
    print("  tables           %d, of which %d put on a landscape page (%s columns)"
          % (total, len(widened),
             ", ".join(str(w) for w in widened) if widened else "none"))
    print("  rows             %d set not to split across a page" % rows_kept)

    problems, notes = audit(feed, out, total)
    os.remove(feed)
    for n in notes:
        print("  typography       %s" % n)
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        print("The file was written but does not match the manuscript. Do not submit it.")
        return 1
    print("  audit            every table, every image and every non-ASCII character "
          "is present in the same number as in the manuscript")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="docx",
                    help="where to write the .docx (default: docx/)")
    args = ap.parse_args(argv)
    return run(args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
