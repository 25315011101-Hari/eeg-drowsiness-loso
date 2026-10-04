"""Check the abstract, highlights and keywords against the journal's limits.

    python3 tools/check_frontmatter.py ABSTRACT.md

The limits are NOT written here. They live in tools/journal_requirements.json,
each one beside the sentence of the guide for authors it was taken from, and
beside the date that guide was last read. This script reads them.

Why the separation. The limits used to be a dict in this file under a comment
saying "checked 16 September 2026". That comment was the only record of where
250 came from, it aged silently, and a reader had no way to tell a verified
limit from a remembered one. A date inside a checker is not evidence; it is a
claim the checker makes about itself. Moving the numbers out turns each limit
into a quotation with a provenance, and makes re-verification an edit to one
data file rather than an edit to code.

This script therefore owns the COUNTING and nothing else. If you are submitting
elsewhere, replace the json -- do not touch the counting rules below.

Counting rules, stated because they are where a "249 words" claim usually goes
wrong. A word is a whitespace-separated token after markdown emphasis markers
are stripped; an em dash surrounded by spaces is not a word; a percentage sign
standing alone is not a word. Characters in a highlight are counted including
spaces, exactly as the guide specifies.
"""

import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(HERE, "journal_requirements.json")

SECTION = re.compile(r"^##\s+(.*?)\s*$", re.M)


def requirements(path=REQUIREMENTS):
    """Load the journal's limits, refusing to guess if they are not there.

    A missing or malformed file is an error and not a default. Falling back to
    built-in numbers would recreate exactly the thing this file exists to remove:
    a limit in the code with no source attached to it.
    """
    if not os.path.exists(path):
        raise SystemExit("%s is missing; the journal's limits are not this "
                         "script's to remember" % os.path.basename(path))
    with open(path) as fh:
        data = json.load(fh)
    for key in ("limits", "source", "verified"):
        if key not in data:
            raise SystemExit("%s has no %r section" % (os.path.basename(path), key))
    for name, entry in data["limits"].items():
        if not entry.get("quote"):
            raise SystemExit("limit %r carries no quotation from the guide" % name)
    return data


def limits(data):
    return {name: entry["value"] for name, entry in data["limits"].items()}


def age_in_days(data, today=None):
    """How long ago the guide was read. None if the date is unreadable."""
    try:
        when = datetime.date.fromisoformat(data["verified"]["date"])
    except (KeyError, ValueError):
        return None
    today = today or datetime.date.today()
    return (today - when).days


def stale(data, today=None):
    """True once the recorded verification is older than the recheck interval."""
    days = age_in_days(data, today)
    window = data.get("verified", {}).get("recheck_after_days")
    if days is None or not window:
        return True
    return days > window


def sections(text):
    out, marks = {}, list(SECTION.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(1).lower()] = text[m.end():end].strip()
    return out


def count_words(block):
    block = re.sub(r"\*+", "", block)
    tokens = [t for t in block.split() if re.search(r"[0-9A-Za-z]", t)]
    return len(tokens)


def main(path):
    data = requirements()
    L = limits(data)
    days = age_in_days(data)

    print("limits: %s, %s" % (data["journal"]["name"], data["source"]["document"]))
    print("read at the source on %s%s"
          % (data["verified"]["date"],
             "" if days is None else " (%d days ago)" % days))
    print("        %s" % data["source"]["url"])
    print("")

    text = open(path).read()
    sec = sections(text)
    problems = []

    abstract = sec.get("abstract", "")
    words = count_words(abstract)
    print("abstract: %d words (limit %d)" % (words, L["abstract_words"]))
    if words > L["abstract_words"]:
        problems.append("abstract is %d words over" % (words - L["abstract_words"]))

    bullets = [l[2:].strip() for l in sec.get("highlights", "").splitlines()
               if l.startswith("- ")]
    print("highlights: %d bullets (allowed %d to %d)"
          % (len(bullets), L["highlights_min"], L["highlights_max"]))
    if not L["highlights_min"] <= len(bullets) <= L["highlights_max"]:
        problems.append("highlight count out of range")
    for b in bullets:
        n = len(b)
        flag = "" if n <= L["highlight_chars"] else "  <-- TOO LONG"
        print("  %3d  %s%s" % (n, b, flag))
        if n > L["highlight_chars"]:
            problems.append("highlight %d characters over: %r"
                            % (n - L["highlight_chars"], b[:40]))

    # keywords are separated by semicolons; line wrapping is not a separator
    kw_block = " ".join(sec.get("keywords", "").split())
    kw = [k.strip() for k in kw_block.split(";") if k.strip()]
    print("keywords: %d (allowed %d to %d)"
          % (len(kw), L["keywords_min"], L["keywords_max"]))
    if len(kw) > L["keywords_max"]:
        problems.append("too many keywords")
    if len(kw) < L["keywords_min"]:
        problems.append("too few keywords")

    print("")
    for p in problems:
        print("PROBLEM:", p)
    print("front matter is within the journal's limits" if not problems
          else "%d problem(s)" % len(problems))

    # Reported, never fatal here. Whether the guide has since changed is not a
    # property of the manuscript, and a paper that is green today should not turn
    # red at midnight. tools/check_submission_ready.py holds this as a gate,
    # because re-reading the guide is a pre-submission act.
    if stale(data):
        print("")
        print("NOTE: the guide was last read %s. Re-read it before submitting; "
              "tools/check_submission_ready.py holds this open until you do."
              % data["verified"]["date"])
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "ABSTRACT.md"))
