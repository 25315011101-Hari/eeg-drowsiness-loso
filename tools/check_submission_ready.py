"""Answer, as a command, whether the pre-submission items have actually been settled.

    python3 tools/check_submission_ready.py

`preflight.py` checks that the paper is internally consistent: that every number
is registered, that the manuscript rebuilds, that no withdrawn phrase is back. It
cannot check the things that are nobody's arithmetic and everybody's memory --
whether the repository is public, whether the two authors have confirmed their
CRediT roles, whether the licence is the one the institute intends. Those live in
prose on a status page, and a status page is a claim.

This makes them a verdict. Each author decision is detected by the draft marker that
sits in the file until a human removes it, so **confirming a decision is the act
of deleting the note that says it is unconfirmed.** There is no second file to keep
in step, and nothing can be marked done by accident.

  repository   the placeholder is gone from the submitted sections and
               CITATION.cff carries a real https:// address
  CRediT       the CREDIT-DRAFT marker is gone from the author contribution
               statement in ABSTRACT.md
  licence      the "NOTE TO THE AUTHORS BEFORE PUBLISHING" block is gone from
               LICENSE, and README names the same licence

Two further items are not author decisions but they age the same way, so they are
answered here rather than remembered:

  training smoke  the one test that builds real models has recorded a pass, and
                  recorded it after the last change to the training code
  journal guide   the journal's limits in tools/journal_requirements.json were
                  read at the source recently enough to still be evidence

It exits non-zero while any of them is pending, so it can gate a release script.
It is reported by preflight on every run, but does not fail it: preflight answers
"is the paper green?", and a paper can be internally perfect and still not be
anyone's to submit yet.

What this cannot check, and no script can: that the URL resolves to a public
repository, that the roles listed are the roles performed, that the institute
agrees about the licence. It checks that a human has said so, not that the human
was right.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECTIONS = ["ABSTRACT.md", "INTRODUCTION.md", "RELATED_WORK.md",
            "RESEARCH_GAP.md", "METHODOLOGY.md", "ARCHITECTURES.md",
            "EXPERIMENTAL_SETUP.md", "RESULTS.md", "DISCUSSION.md",
            "CONCLUSION.md", "CODE_AVAILABILITY.md"]
# CODE_AVAILABILITY.md was added on 4 October 2026, when the front-matter data
# availability statement was merged into it. Until then the placeholder was in two
# places and only one of them was on this list, so the omission was invisible. After
# the merge it would have meant this check reporting the repository item settled while
# <repository URL> was still printed in the paper.

PLACEHOLDER = "<repository URL>"
CREDIT_DRAFT = "CREDIT-DRAFT:"
LICENCE_DRAFT = "NOTE TO THE AUTHORS BEFORE PUBLISHING"
URL_IN_CFF = re.compile(r"^repository-code:[ \t]*(.+?)[ \t]*$", re.M)
# Matching a licence name by substring is how "MIT" was found inside "submitted"
# and "MPL" inside "example". Each entry is a canonical name and a case-sensitive
# pattern with word boundaries, and only the TITLE of the LICENSE file is searched
# for it -- the body names CC0 and the ARL licence as third-party terms, which are
# not this repository's licence and must not be mistaken for it.
LICENCES = [
    ("MIT", re.compile(r"\bMIT\b")),
    ("Apache-2.0", re.compile(r"\bApache\b")),
    ("BSD", re.compile(r"\bBSD\b")),
    ("GPL", re.compile(r"\bGPL\b|GENERAL PUBLIC LICENSE")),
    ("MPL", re.compile(r"\bMPL\b|Mozilla Public License")),
    ("CC BY", re.compile(r"\bCC[ -]BY\b")),
    ("CC0", re.compile(r"\bCC0\b")),
]


def _read(*parts):
    path = os.path.join(HERE, *parts)
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return fh.read()


def check_repository():
    """The address is filled in everywhere, and it is an address."""
    problems = []
    for name in SECTIONS:
        text = _read("manuscript", name)
        if text and PLACEHOLDER in text:
            problems.append("%s still has the placeholder" % name)

    cff = _read("CITATION.cff")
    if cff is None:
        problems.append("CITATION.cff is missing")
    else:
        m = URL_IN_CFF.search(cff)
        if not m:
            problems.append("CITATION.cff has no repository-code line")
        elif not m.group(1).startswith("https://"):
            problems.append("CITATION.cff repository-code is %r, not a URL"
                            % m.group(1))
    return problems


def check_credit():
    """Both authors have signed off on the role lists."""
    text = _read("manuscript", "ABSTRACT.md")
    if text is None:
        return ["ABSTRACT.md is missing"]
    if CREDIT_DRAFT in text:
        return ["the CRediT statement is still marked as a proposal awaiting "
                "confirmation"]
    return []


def check_licence():
    """The licence is chosen, and the two files that name it agree."""
    problems = []
    lic = _read("LICENSE")
    if lic is None:
        return ["LICENSE is missing"]
    if LICENCE_DRAFT in lic:
        problems.append("LICENSE still carries the draft note")

    # The title, not the whole file: the body names the dataset's CC0 terms and
    # the ARL licence, neither of which is this repository's licence.
    title = "\n".join(lic.strip().splitlines()[:3])
    chosen = [name for name, pat in LICENCES if pat.search(title)]
    if not chosen:
        problems.append("LICENSE does not name a recognised licence in its "
                        "first three lines")
    elif not problems:
        # Only meaningful once the draft note is gone: the note itself names the
        # proposed licence, so before that this would compare a draft to a draft.
        name = chosen[0]
        pat = dict(LICENCES)[name]
        readme = _read("README.md") or ""
        if not pat.search(readme):
            problems.append("LICENSE is %s but README.md does not name it" % name)
    return problems


def check_training_smoke():
    """Has the training smoke test been run, against the code as it stands now?

    It is the only test that runs real model builds and checks that a held-out
    subject never reaches its own fold's training or validation split. It needs
    TensorFlow and the ARL reference implementation, so it skips in environments
    without them -- visibly, but a visible skip is still a skip. This reads the
    record the test leaves when it passes and compares its time with the sources it
    exercises: a pass recorded before the last change to the training loop or the
    models is no evidence about the code that will be submitted.
    """
    import datetime
    stamp = os.path.join(HERE, "results", "smoke_test_passed.txt")
    if not os.path.exists(stamp):
        return ["never recorded a pass; run  python3 tests/test_training_smoke.py  "
                "in an environment with TensorFlow and the ARL implementation"]
    when = os.path.getmtime(stamp)
    stale = []
    for rel in ("src/train_loso.py", "src/models.py", "config.py"):
        full = os.path.join(HERE, rel)
        if os.path.exists(full) and os.path.getmtime(full) > when:
            stale.append(rel)
    if stale:
        return ["last pass was %s, before changes to %s; run it again"
                % (datetime.datetime.fromtimestamp(when).date().isoformat(),
                   ", ".join(stale))]
    return []


def check_journal_guide():
    """Were the journal's limits read at the source recently enough to rely on?

    The abstract, highlights and keyword limits are quotations in
    tools/journal_requirements.json, each stamped with the day the guide for
    authors was read. A guide for authors changes without notice and without a
    version number, so "verified" has a shelf life. This does not and cannot
    check that the limits are still right -- only a human opening the URL can do
    that. It checks that a human did so recently, and holds the item open once
    the record is older than the interval that file itself declares.
    """
    sys.path.insert(0, os.path.join(HERE, "tools"))
    try:
        import check_frontmatter as cf
        data = cf.requirements()
    except SystemExit as exc:
        return ["tools/journal_requirements.json cannot be read: %s" % exc]

    days = cf.age_in_days(data)
    if days is None:
        return ["tools/journal_requirements.json has no readable verification date"]
    if cf.stale(data):
        return ["the guide for authors was last read on %s, %d days ago; re-read "
                "%s and update tools/journal_requirements.json"
                % (data["verified"]["date"], days, data["source"]["url"])]
    return []


def main(argv=None):
    checks = [("repository", check_repository),
              ("CRediT roles", check_credit),
              ("licence", check_licence),
              ("training smoke", check_training_smoke),
              ("journal guide", check_journal_guide)]

    print("what is not the paper's to settle, and what the paper cannot check here\n")
    pending = 0
    for label, fn in checks:
        problems = fn()
        print("  %-14s %s" % (label, "CONFIRMED" if not problems else "PENDING"))
        for p in problems:
            print("      " + p)
        pending += 1 if problems else 0

    print("")
    if pending:
        print("%d of %d still open. manuscript/DECISION_SHEET.md is the one page "
              "they settle from." % (pending, len(checks)))
    else:
        print("All %d confirmed. Nothing here blocks submission." % len(checks))
    return 1 if pending else 0


if __name__ == "__main__":
    raise SystemExit(main())
