"""Fail if a withdrawn phrase has reappeared, in a source file or a built PDF.

    python3 tools/check_withdrawn.py manuscript/WITHDRAWN.md manuscript/*.md
    python3 tools/check_withdrawn.py manuscript/WITHDRAWN.md some_manuscript.pdf

Over this paper's revision history the same handful of corrections was reported
several times. Each time the phrase had already been removed and the report came
from a superseded copy — but "that is already fixed" is an assertion, and the whole
point of this repository is that assertions about the text are checkable.

So the removals are now data. `manuscript/WITHDRAWN.md` lists every phrase the paper
has retired and why. This script reads that list and fails if any of them is back.
It accepts .md and .pdf, so the same command answers both "is the source clean?" and
"is this PDF in my downloads the current one?".

Matching ignores case and collapses all whitespace, so a phrase split across two
lines, or across a PDF line break, is still caught.
"""

import os
import re
import sys


def phrases(path):
    """Read the withdrawn list: one phrase per '- ' line, notes ignored."""
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("- ") and line[2:].strip():
                out.append(line[2:].strip())
    return out


def text_of(path):
    """The document's text, whitespace collapsed. Handles .md and .pdf."""
    if path.lower().endswith(".pdf"):
        try:
            import pypdf
        except ImportError:
            print("pypdf is needed to read a PDF; skipping", path)
            return None
        reader = pypdf.PdfReader(path)
        raw = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        with open(path) as fh:
            raw = fh.read()
    return " ".join(raw.split())


QUOTES = "\"'\u201c\u201d\u2018\u2019"

# A quoted span: an opening mark, then anything but a line break, then a closing
# mark. Curly pairs are matched to their partners; straight marks to themselves.
QUOTED = re.compile(r"\u201c[^\u201c\u201d\n]{0,400}\u201d"
                    r"|\u2018[^\u2018\u2019\n]{0,400}\u2019"
                    r"|\"[^\"\n]{0,400}\""
                    r"|~~[^~\n]{0,400}~~")


def _display_spans(body):
    """(start, end) of every region where text is displayed, not asserted."""
    return [(m.start(), m.end()) for m in QUOTED.finditer(body)]


def _asserted_somewhere(body, low, needle):
    """True if the phrase occurs otherwise than as a quotation or a strikethrough.

    This paper documents its own corrections, so it quotes several withdrawn
    phrases on purpose -- "an earlier draft said X, which was false" is the
    honesty, not a regression. A phrase wrapped in quotation marks, or struck
    through in Markdown, is being displayed rather than asserted, and does not
    count. Every other occurrence does.
    """
    spans = _display_spans(body)
    start = 0
    while True:
        at = low.find(needle, start)
        if at == -1:
            return False
        end = at + len(needle)
        # Inside a quoted or struck-through span, anywhere inside it -- the
        # earlier version required the quote marks to sit immediately either
        # side, which missed "self-reported button presses" because the closing
        # quote falls two letters past the end of the listed phrase.
        if not any(a <= at and end <= b for a, b in spans):
            return True
        start = at + 1



# Words that carry no content: a paraphrase may drop or swap any of these without
# changing what the sentence claims.
_FILLER = {"a", "an", "and", "any", "are", "as", "at", "be", "been", "by", "for",
           "from", "in", "is", "it", "its", "of", "on", "or", "that", "the",
           "their", "them", "this", "to", "was", "were", "with"}
_WORD = re.compile(r"[a-z0-9]+")


def _content(text):
    """The words of a phrase that carry its claim, lowercased."""
    return [w for w in _WORD.findall(text.lower()) if w not in _FILLER]


def _near_misses(body, phrase):
    """Spans that assert a withdrawn claim in different words.

    An exact-substring guard is defeated by one word. The claim "beaten on every
    metric reported in this paper" was retired, reappeared in a Results summary as
    "beaten on every metric in this paper" -- one word shorter -- and the checker
    reported the file clean for three drafts.

    So this looks for the phrase's CONTENT words appearing in order, close
    together, allowing one of them to be missing. It reports rather than fails:
    a near miss is a question for a human ("is this the retired claim in new
    words?"), not a regression a script may decide.
    """
    want = _content(phrase)
    if len(want) < 4:
        # Three content words match too much: "the cleanest ablation in the study"
        # fired on a sentence that says the opposite, and "need not agonise" fired
        # on unrelated prose. A report nobody reads is not a guard.
        return []
    allowed_gap = max(1, round(len(want) * 0.2))
    words = [(m.group(0), m.start(), m.end()) for m in _WORD.finditer(body.lower())]
    limit = len(want) + allowed_gap + 4          # how many words the span may span
    spans = _display_spans(body)
    out = []
    for i in range(len(words)):
        if words[i][0] != want[0]:
            continue
        j, matched, last = i, 0, i
        for w in want:
            k = j
            while k < min(len(words), i + limit):
                if words[k][0] == w:
                    matched += 1
                    last = k
                    j = k + 1
                    break
                k += 1
            else:
                continue
        # The first and last content words must both be present: a paraphrase of a
        # claim keeps its subject and its object, and anchoring on them removes the
        # loose middle matches that made this report unreadable.
        anchored = words[i][0] == want[0] and words[last][0] == want[-1]
        if anchored and matched >= len(want) - allowed_gap:
            a, b = words[i][1], words[last][2]
            if matched == len(want) and body.lower()[a:b] == " ".join(want):
                continue                       # the exact check already owns this
            if any(x <= a and b <= y for x, y in spans):
                continue                       # quoted, so displayed not asserted
            out.append((a, b))
            break                              # one report per phrase per file
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    wanted = phrases(argv[0])
    if not wanted:
        print("no phrases found in", argv[0])
        return 2
    norm = [(p, " ".join(p.split()).lower()) for p in wanted]

    print("%d withdrawn phrase(s) to check\n" % len(wanted))
    hits, checked, nearby = [], 0, []
    for path in argv[1:]:
        if not os.path.exists(path) or os.path.abspath(path) == os.path.abspath(argv[0]):
            continue
        body = text_of(path)
        if body is None:
            continue
        checked += 1
        low = body.lower()
        found = [original for original, needle in norm
                 if _asserted_somewhere(body, low, needle)]
        near = []
        for original, needle in norm:
            if original in found:
                continue
            for a, b in _near_misses(body, original):
                near.append((original, body[max(0, a - 40):b + 40]))
        verdict = "clean" if not found else "%d REAPPEARED" % len(found)
        if near:
            verdict += "  (%d near miss%s)" % (len(near), "" if len(near) == 1 else "es")
        print("  %-34s %s" % (os.path.basename(path), verdict))
        for original, context in near:
            nearby.append((path, original))
            print("      NEAR MISS of \"%s\"" % original)
            print("       ...%s..." % " ".join(context.split()))
        for original in found:
            hits.append((path, original))
            # Show where, so the fix does not need a second search.
            at = low.find(" ".join(original.split()).lower())
            print("      \"%s\"" % original)
            print("       ...%s..." % body[max(0, at - 70):at + len(original) + 70])

    print("\n%d file(s) checked, %d withdrawn phrase(s) reappeared, "
          "%d near miss(es)" % (checked, len(hits), len(nearby)))
    if nearby:
        print("\nA near miss is the retired claim's content words, in order, with at\n"
              "most one missing. It is not failed automatically -- read it and decide\n"
              "whether it is the withdrawn claim wearing different words.")
    if hits:
        print("\nA withdrawn phrase is back in the text. Either the edit was lost in a\n"
              "rebuild, or this file is an older copy. Check the build stamp before\n"
              "editing anything.")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
