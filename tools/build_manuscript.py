"""Assemble the one submission manuscript from the section files.

    python3 tools/build_manuscript.py /path/to/journal /path/to/out.md

Thirty-one draft PDFs accumulated in the working folder, and every review of this
paper so far has at some point quoted a sentence from a superseded one. That is not
a filing problem — it is a correctness problem, because a reviewer reading draft 3
reports errors that draft 5 already fixed, and time goes into re-checking text that
no longer exists.

The fix is that there is exactly one manuscript, it is built rather than edited,
and everything else is visibly an input or an archive. This script builds it.

It concatenates the sections in submission order and removes the four kinds of
content that belong to the working drafts rather than to the paper:

  * Hindi glosses, the `> **हिंदी।** ...` blockquotes
  * "Notes for the next pass" sections, which are explicitly not part of the paper
  * each section file's own draft header, replaced by one manuscript header
  * anything between `<!-- not-for-submission:start -->` and its `:end` marker --
    the front-matter preamble reciting the journal's limits, the superseded title
    drafts, and anything else editorial that sits mid-section

One piece of editorial matter is deliberately kept: the blocker notice on the data
availability statement, because the placeholder it warns about is still in the
built text until the repository is published.

It does not rewrite a single sentence of the body. Anything wrong in the output is
wrong in the section file, which is where it should be fixed.
"""

import os
import re
import sys

ORDER = [
    ("ABSTRACT.md", None),
    ("INTRODUCTION.md", "1. Introduction"),
    ("RELATED_WORK.md", "2. Related Work"),
    ("RESEARCH_GAP.md", "3. Research Gap"),
    ("METHODOLOGY.md", "4. Methodology"),
    ("ARCHITECTURES.md", "5. Architectures"),
    ("EXPERIMENTAL_SETUP.md", "6. Experimental Setup"),
    ("RESULTS.md", "7. Results"),
    ("DISCUSSION.md", "8. Discussion"),
    ("CONCLUSION.md", "9. Conclusion"),
    ("CODE_AVAILABILITY.md", "Code and Data Availability"),
    ("REFERENCES.md", "References"),
]

# ORDER is the one authoritative statement of what the manuscript consists of, and
# this is the name other tools import to ask that question. It existed as a
# hand-written copy inside tools/preflight.py until 25 September 2026, and the copy
# was two files short: CODE_AVAILABILITY.md and REFERENCES.md are assembled into the
# submitted document and were read by no placeholder check and no withdrawn-phrase
# check. Six unfilled placeholders and a section headed "Still to add before
# submission" rode into the built manuscript under a green twenty-of-twenty verdict.
#
# A scope is now derived from this list rather than restated beside it. A check that
# should not read one of these files declares that exclusion, by name and with a
# reason; a file absent from a scope for any other cause is a bug.
SECTION_FILES = [name for name, _label in ORDER]

HINDI = re.compile(r"^>\s*\*\*हिंदी।?\*\*")
# The per-entry verification notes in REFERENCES.md. Each records the URL an entry
# was checked against, and often several paragraphs of the authors' reasoning about
# what the source does and does not license the paper to claim. That is exactly the
# material a co-author needs and a reviewer should never see in a reference list.
# Until 25 September 2026 all of it was copied into the submitted document, because
# the builder stripped only Hindi glosses and this file carried no marker.
VERIFIED = re.compile(r"^>\s*Verified from\b")
NOTES = re.compile(r"^#{1,3}\s*(Notes for the next pass|Notes\b.*not part of the paper)",
                   re.I)
ANY_HEADING = re.compile(r"^#{1,6}\s")

# Editorial matter that lives in a section file so the authors can see it, but
# that no reviewer should ever read: the front-matter preamble reciting the
# journal's limits, the list of superseded title drafts. A "Notes for the next
# pass" heading is the blunt version of this; these markers are the precise one,
# for a block that sits mid-section and cannot be given a heading of its own.
#
# The repository-url blocker is deliberately NOT stripped. It is the one piece of
# editorial matter that belongs in the built manuscript, because the thing it warns
# about -- a placeholder where the data-availability address should be -- is still
# in the built manuscript until the repository is published. A build carrying a
# bare <repository URL> and no warning is worse than one carrying both.
DROP = re.compile(
    r"<!-- not-for-submission:start -->.*?<!-- not-for-submission:end -->\n?",
    re.S)


def strip(text):
    """Drop Hindi glosses, 'notes for the next pass' sections and draft headers."""
    text = DROP.sub("", text)
    out, lines = [], text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]

        if NOTES.match(line):
            # Skip to the next heading at the same or a higher level.
            level = len(line) - len(line.lstrip("#"))
            i += 1
            while i < n:
                if ANY_HEADING.match(lines[i]):
                    here = len(lines[i]) - len(lines[i].lstrip("#"))
                    if here <= level:
                        break
                i += 1
            continue

        if HINDI.match(line) or VERIFIED.match(line):
            # Skip the whole blockquote, including its continuation lines.
            while i < n and (lines[i].startswith(">") or lines[i].strip() == ">"):
                i += 1
            continue

        out.append(line)
        i += 1

    text = "\n".join(out)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"\A(?:\s*---\s*\n)+", "", text.strip())
    return text.strip() + "\n"


def main(argv):
    journal = argv[0] if argv else "/tmp/journal"
    out_path = argv[1] if len(argv) > 1 else os.path.join(journal, "MANUSCRIPT.md")

    parts, missing = [], []
    for name, label in ORDER:
        path = os.path.join(journal, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        with open(path) as fh:
            body = fh.read()
        # Drop the file's own top-level draft header line; the manuscript has one.
        body = re.sub(r"\A#\s[^\n]*\n", "", body)
        body = strip(body)
        if label:
            parts.append("\n\n---\n\n# %s\n\n%s" % (label, body))
        else:
            parts.append(body)

    text = "".join(parts)

    # A build stamp, so that a copy in someone's downloads folder says what it is.
    # Every build has carried the same filename, so reviewers have repeatedly read
    # a superseded PDF and reported corrections that the current text already had.
    # The digest is of the assembled body, so two builds with the same digest are
    # the same paper and a different digest means the text moved.
    import csv as _csv
    import datetime
    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    registry = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results", "MASTER_NUMBERS.csv")
    try:
        with open(registry) as fh:
            rows = sum(1 for _ in _csv.DictReader(fh))
    except OSError:
        rows = 0
    stamp = ("\n\n---\n\n*Build %s · %s · %d words · registry %d rows.*\n"
             "*Rebuild: `python3 tools/build_manuscript.py manuscript "
             "manuscript/MANUSCRIPT.md`. A copy whose build id differs from the one "
             "the repository produces is not the current manuscript.*\n"
             % (digest, datetime.date.today().isoformat(), len(text.split()), rows))
    text = text + stamp

    with open(out_path, "w") as fh:
        fh.write(text)

    words = len(text.split())
    print("wrote %s" % out_path)
    print("  build %s" % digest)
    print("  %d section(s), %d words, %d lines" % (len(ORDER) - len(missing),
                                                   words, text.count("\n") + 1))
    if missing:
        print("  MISSING: %s" % ", ".join(missing))
    left = [m.group(0) for m in re.finditer(r"हिंदी", text)]
    if left:
        print("  WARNING: %d Hindi gloss marker(s) survived the strip" % len(left))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
