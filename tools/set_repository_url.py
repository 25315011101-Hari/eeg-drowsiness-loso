"""Fill the repository address into every file that promises it, then re-check.

    python3 tools/set_repository_url.py https://github.com/<user>/<repo>
    python3 tools/set_repository_url.py https://github.com/<user>/<repo> \
        --doi 10.5281/zenodo.0000000

The data-availability statement is a promise: it tells a reader where to fetch
files that reproduce every table in the paper. Until the repository is published
that promise points at `<repository URL>`, a placeholder that preflight reports on
every run. This script is what closes it.

It does three things and refuses to do any of them carelessly:

  1. Rejects an address that is not a plausible public repository URL, so that a
     typo or a leftover angle-bracket cannot be written into the paper.
  2. Replaces the placeholder everywhere it appears -- the manuscript sections,
     the status page, CITATION.cff -- rather than in the one place somebody
     remembers.
  3. Removes the blocker notice from the data-availability section, because a
     reminder to publish the repository is not a sentence to publish once it is
     published.

It does NOT check that the URL actually resolves, that the repository is public,
or that what is there matches what is here. No script can check that from inside
the package it is checking. Do it by hand, from a fresh clone, and the reminder
this script prints says so.

Add --doi when the repository is also archived (Zenodo mints a DOI from a GitHub
release). Elsevier prefers a permanent identifier over a bare repository address,
because a GitHub repository can be renamed, made private or deleted and a DOI
cannot.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACEHOLDER = "<repository URL>"
BLOCKER = re.compile(
    r"<!-- repository-url-blocker:start -->.*?"
    r"<!-- repository-url-blocker:end -->\n\n?",
    re.S)

# Files that carry the promise -- the places where the placeholder IS the address
# the paper undertakes to publish. Prose that merely talks about the placeholder
# (README, REPRODUCIBILITY, DECISION_SHEET) deliberately does not contain the
# token: substituting a real URL there would turn "the statement carries a
# placeholder address" into a sentence calling a real address a placeholder. That
# was a bug in the first version of this script, found by checking the shipped
# package rather than trusting the list.
#
# MASTER_FILE.md and MANUSCRIPT.md are generated, and are rewritten here only so
# that a copy already on disk is not left stale before the next rebuild.
TARGETS = [
    "manuscript/ABSTRACT.md",
    "manuscript/CODE_AVAILABILITY.md",
    "manuscript/MASTER_FILE.md",
    "manuscript/MANUSCRIPT.md",
    "CITATION.cff",
]

URL_OK = re.compile(r"^https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+$")
DOI_OK = re.compile(r"^10\.\d{4,9}/\S+$")


def complain(message):
    print("REFUSED: " + message)
    return 2


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 1

    url = argv[0].strip().rstrip("/")
    doi = None
    if "--doi" in argv:
        at = argv.index("--doi")
        if at + 1 >= len(argv):
            return complain("--doi given with no DOI after it.")
        doi = argv[at + 1].strip()

    # The checks are deliberately blunt. Every one of them exists because the
    # alternative is a wrong address printed in a published paper.
    if url.startswith("<") or url.endswith(">"):
        return complain("that still has angle brackets around it: %r" % url)
    if not URL_OK.match(url):
        return complain("%r does not look like a public repository URL. It must "
                        "start https:// and have a path." % url)
    if url.endswith(".git"):
        return complain("%r is a clone address. Use the page a human can open, "
                        "without the .git suffix." % url)
    if "localhost" in url or "127.0.0.1" in url:
        return complain("%r is not reachable by a reader." % url)
    if doi is not None:
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]
        if not DOI_OK.match(doi):
            return complain("%r does not look like a DOI (10.xxxx/...)." % doi)

    changed, missing = [], []
    for rel in TARGETS:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            missing.append(rel)
            continue
        with open(path) as fh:
            before = fh.read()
        # The placeholder is written in backticks so that it reads as a slot
        # rather than as text. A real URL is not code and should not keep them,
        # or the typeset article prints a monospace address inside a sentence.
        after = before.replace("`" + PLACEHOLDER + "`", url)
        after = after.replace(PLACEHOLDER, url)
        after = BLOCKER.sub("", after)
        if after != before:
            with open(path, "w") as fh:
                fh.write(after)
            changed.append((rel, before.count(PLACEHOLDER)))

    if missing:
        print("MISSING (expected to be here):")
        for rel in missing:
            print("  " + rel)
        return 2

    print("repository URL set to %s\n" % url)
    for rel, n in changed:
        print("  %-34s %d occurrence(s)" % (rel, n))
    if not changed:
        print("  nothing to do -- no file still held the placeholder.")

    if doi:
        print("\nArchive DOI given: %s" % doi)
        print("It is NOT written into the files automatically, because where a DOI")
        print("belongs in the data-availability sentence is an editorial choice.")
        print("The sentence to use:")
        print("\n  ... is available at %s and archived at" % url)
        print("  https://doi.org/%s ." % doi)

    print("\nRe-checking the paper against the change.")
    rc = subprocess.call([sys.executable, os.path.join(HERE, "tools", "preflight.py")],
                         cwd=HERE)

    print("\nWhat this script could not check, and you must, from a FRESH clone:")
    print("  1. the repository is public -- open it in a signed-out browser")
    print("  2. results/ALL_FOLDS.csv there holds 750 rows")
    print("  3. python3 tools/preflight.py passes there")
    print("The data-availability statement now promises all three.")
    print("\nTwo pages still describe the repository as unpublished, because they")
    print("are about the decision rather than the statement. Update them by hand:")
    print("  manuscript/REPRODUCIBILITY.md  section 5, the red row")
    print("  manuscript/DECISION_SHEET.md   section 1")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
