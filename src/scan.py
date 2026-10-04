"""Scan a manuscript draft for numbers that are not in MASTER_NUMBERS.csv.

    python -m src.scan RESULTS.md DISCUSSION.md

A clean scan means every printed figure traces back to a value computed from the
raw result files.  It does NOT mean the draft is correct: the scanner checks
numbers, not claims.  A sentence can pass the scan and still misdescribe what
its numbers show, which is why the scan is a floor and not a substitute for
reading.

Matching rule.  A literal passes if some registry value is within half of its
own last printed decimal place, so "0.884" matches 0.88395 and "0.8840" does
not match 0.8836.  Both signs are tried, because a draft prints a negative
correlation as "-0.900" while the registry stores -0.9.

Two registries are consulted: MASTER_NUMBERS.csv for this study's own
measurements, and LITERATURE_NUMBERS.csv for figures quoted from other papers,
each recorded with the URL it was verified from. A number that appears in
neither has no source, which is the thing this script exists to catch.

Deliberately ignored:
  * anything inside backticks, which is code or a filename
  * anything inside a URL or DOI, where the digits are an identifier and not a
    measurement -- a DOI such as 10.5061/dryad.5tb2rbp9c otherwise reads as the
    number 10.5061
  * numbers in headings and after the word "Section", which are cross-references
  * integers below 1000 that are not on the small whitelist, since these are
    counts of subjects, folds and comparisons rather than measurements
"""

import argparse
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

# Structural numbers that are not measurements. Everything else must be registered.
WHITELIST = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13",
    "14", "15", "16", "17", "18", "20", "25", "30", "40", "50", "60", "100",
    "128", "150", "0.5", "1.5", "2.5", "1.96", "0.05",
    "2018", "2021", "2024", "2025", "2026",
}

SKIP_BEFORE = re.compile(r"(Section|Sections|section|§)\s*$")
NUMBER = re.compile(r"(?<![\w.])(\d+(?:,\d{3})*(?:\.\d+)?)")

# A plural cross-reference names more than one section, and only the first of them
# follows the word. "Sections 7.3 and 7.5" left the 7.5 to be read as a measurement,
# and it was reported as a number with no source; it passed in the manuscript only
# where the second number happened also to be a registered value. So the whole run of
# section numbers is found as one thing and blanked before any number is read.
#
# A member must look like a section number -- at most two digits per part, and ending
# cleanly -- which is what keeps "Section 7.1, 0.0049 ..." from swallowing the 0.0049:
# that literal has a four-digit part, so it is not a member and stays scannable.
_SECTION_NUMBER = r"\d{1,2}(?:\.\d{1,2}){0,3}(?!\.?\d)"
SECTION_RUN = re.compile(
    r"(?:§|\b[Ss]ections?\b)\s*" + _SECTION_NUMBER
    + r"(?:\s*(?:,|and|to|&|–|—|-)\s*" + _SECTION_NUMBER + r")*"
)


def _mask_section_runs(text):
    """Blank every section cross-reference, keeping every other position intact.

    Newlines survive the blanking, because the caller turns a position into a line
    number by counting them.
    """
    return SECTION_RUN.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def registry_values(path=None, extra=None):
    """Read one or more registries and return their numeric values.

    A manuscript cites two kinds of number: its own measurements, which come
    from MASTER_NUMBERS.csv, and figures taken from other papers, which come
    from LITERATURE_NUMBERS.csv and carry the URL each was verified from. Both
    must be traceable, so both are loaded here. A number in neither is a number
    with no source.
    """
    paths = [path or C.REGISTRY_CSV]
    if extra:
        paths += list(extra)
    else:
        default = os.path.join(os.path.dirname(os.path.abspath(paths[0])),
                               "LITERATURE_NUMBERS.csv")
        if os.path.exists(default):
            paths.append(default)

    vals = []
    for p in paths:
        if not os.path.exists(p):
            raise FileNotFoundError("%s not found; run python -m src.registry" % p)
        for v in pd.read_csv(p).value:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
    return np.array(sorted(set(vals)))


def _line_starts(text):
    lines = text.split("\n")
    return np.cumsum([0] + [len(l) + 1 for l in lines])


def _context(text, pos, width=95):
    a, b = max(0, pos - width), min(len(text), pos + width)
    return " ".join(text[a:b].split())


# "3.973 x 10^-5" as the manuscript prints it, in either ASCII or the typeset
# superscript form. A mantissa is not a number the registry holds on its own, so
# without this the scanner flags the mantissa of every value written in scientific
# notation and the author's only escape is to stop using scientific notation.
SUPERS = str.maketrans("\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079",
                       "-0123456789")
SCI = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:\u00d7|x|\*)\s*10\s*(?:\^|\*\*)?\s*"
    r"(\u207b?[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]+|[-\u2212]?\d+)")


def _fold_scientific(text):
    """Rewrite scientific notation into a plain float literal, in place.

    The replacement is padded to the original length so that every position
    reported afterwards still points at the right line.
    """
    def sub(m):
        exp = m.group(2).translate(SUPERS).replace("\u2212", "-")
        try:
            x = float(m.group(1)) * (10.0 ** int(exp))
        except (ValueError, OverflowError):
            return m.group(0)
        # Fixed point, not repr(): repr would give "3.973e-05" and the number
        # pattern would then stop at the "e" and flag the mantissa all over again.
        value = ("%.12f" % x).rstrip("0")
        if value.endswith("."):
            value += "0"
        return (value + " " * len(m.group(0)))[:max(len(m.group(0)), len(value))]
    return SCI.sub(sub, text)


def find_numbers(text):
    """Yield (literal, position) for every candidate number outside code spans."""
    text = re.sub(r"`[^`]*`", " ", text)          # inline code and filenames
    text = re.sub(r"(?:https?://|doi:|www\.)\S+", " ", text)   # URLs and DOIs
    text = re.sub(r"\b10\.\d{4,9}/\S+", " ", text)           # bare DOIs
    text = _mask_section_runs(text)               # "Sections 7.3 and 7.5", both
    text = _fold_scientific(text)
    for m in NUMBER.finditer(text):
        start = m.start()
        if SKIP_BEFORE.search(text[max(0, start - 12):start]):
            continue
        line_start = text.rfind("\n", 0, start) + 1
        if text[line_start:start + 1].startswith("#"):
            continue
        yield m.group(1), start
    return


def check(path, values, stop_at=None):
    """Return [(line, literal, context), ...] for unregistered numbers.

    `stop_at` is a heading after which scanning stops, used for the reference
    list. Bibliographic numbers -- years, volumes, page ranges, arXiv identifiers,
    article numbers -- are not results and do not belong in a results registry;
    they are verified against publisher records instead, and REFERENCES.md carries
    the URL each was checked from. Scanning them here produces nothing but noise,
    and a check that cries wolf is one people stop reading.
    """
    with open(path) as fh:
        text = fh.read()
    if stop_at:
        cut = text.find(stop_at)
        if cut != -1:
            text = text[:cut]
    starts = _line_starts(text)
    flagged = []

    for literal, pos in find_numbers(text):
        if literal in WHITELIST:
            continue
        raw = literal.replace(",", "")
        try:
            x = float(raw)
        except ValueError:
            continue

        if "." not in raw:
            if x in set(C.PARAMS.values()):
                continue
            if any(x in (s["n_windows"], s["n_per_subject"], s["n_drowsy"])
                   for s in C.ARMS.values()):
                continue
            if x in (C.total_folds(), C.folds_per_arm(), C.WIN):
                continue
            if x < 1000:
                continue
            decimals = 0
        else:
            decimals = len(raw.split(".")[1])

        tol = 0.5 * (10 ** -decimals) if decimals else 0.5
        if np.any(np.abs(values - x) <= tol + 1e-12):
            continue
        if np.any(np.abs(values + x) <= tol + 1e-12):     # printed as a negative
            continue

        line = int(np.searchsorted(starts, pos, side="right"))
        flagged.append((line, literal, _context(text, pos)))
    return flagged


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--registry", default=None)
    ap.add_argument("--also", action="append", default=None,
                    help="an additional registry, e.g. LITERATURE_NUMBERS.csv; "
                         "that file is picked up automatically if it sits beside "
                         "the main registry")
    ap.add_argument("--stop-at", default=None,
                    help="stop scanning at this heading, e.g. '# References'; "
                         "bibliographic numbers are verified against publisher "
                         "records, not against the results registry")
    a = ap.parse_args(argv)

    values = registry_values(a.registry, a.also)
    total = 0
    for path in a.paths:
        flagged = check(path, values, a.stop_at)
        total += len(flagged)
        print("\n" + "=" * 100)
        print("%s -> %d number(s) not in the registry" % (path, len(flagged)))
        print("=" * 100)
        for line, literal, ctx in flagged:
            print("  line %-4d  %-10s  ...%s..." % (line, literal, ctx))
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
