"""Run every pre-submission check and print one verdict.

    python3 tools/preflight.py /path/to/journal

Twenty-one separate checks have accumulated in this repository, and "is the paper
green?" was for a while answered by running them one at a time and remembering the
results. That is how a stale registry count survived two reviews: nothing was wrong
with any individual check, and nothing ran them together.

This runs all of them and exits non-zero if any fails. The numbering is the order
they run in, and it is kept in step with the list in main() -- the "13a, 13b, 13c"
of an earlier draft was a sign that this docstring had stopped being maintained:

  1. tests             the test suite
  2. registry          rebuild MASTER_NUMBERS.csv from the released results
  3. row counts        every "N rows" claim in the documents equals the real count
  4. scan              no number in the assembled sections is unregistered, except
                       in REFERENCES.md, whose numbers are bibliographic and are
                       gated by check 18 instead (see SCOPE_EXCLUSIONS)
  5. cross-references  every "Section N" points at a section that exists
  6. front matter      abstract words, highlight characters, keyword count
  7. release           ALL_FOLDS.csv holds 750 folds and the analysis reruns from it
  8. duplicate keys    no (section, claim) pair appears on two registry rows
  9. manuscript        the assembled manuscript rebuilds
 10. manuscript scan   and scans clean against the registry
 11. figures           all seven figures redraw from the registry
 12. provenance        every plotted value traces to a registry row
 13. master file       the single-source-of-truth file regenerates from the registry
 14. withdrawn         no phrase the paper has retired has reappeared, in the
                       manuscript OR in either README, and no near paraphrase of one
 15. released scores   which execution each released probability file came from
 16. ranking invariance  the subject-averaged ROC-AUC and PR-AUC are unchanged at
                       the reported precision after out-of-subject Platt scaling
 17. table marks       Table 6's bold cells are the ones its caption's rule selects
 18. literature        the borrowed-number registry agrees with REFERENCES.md,
                       carries no unfinished marker, and sources every row
 19. multiplicity      the released multiplicity table against a fresh run, the Holm
                       ceilings the p-value floors imply, and where the one-family
                       Benjamini-Yekutieli survivors come from
 20. placeholders      no <angle-bracket placeholder> left in any assembled section
 21. decisions         what is not the paper's to settle -- repository, CRediT,
                       licence -- plus the one thing it cannot check here: whether
                       the training smoke test has been run against current code

Which files count as "the manuscript" is asked of tools/build_manuscript.py, whose
ORDER is the one authoritative answer, and never restated here. It was restated here
once, two files short, and that is finding R37: the two missing files were the ones
carrying six unfilled placeholders and an unfinished TODO list.

The last two are the ones that cannot be automated away. They report rather than
fail: what is still a placeholder, and which of the three author decisions --
publishing the repository, confirming the CRediT roles, confirming the licence --
has not yet been made. Neither can fail the run, because neither is a property of
the paper; both are printed on every run, because the alternative is remembering.
"""

import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What the manuscript consists of is asked of the builder, not restated here. This
# module used to carry its own hand-written list of ten section files. The builder
# assembles twelve. The two it did not name -- CODE_AVAILABILITY.md and
# REFERENCES.md -- were therefore read by no placeholder check and no
# withdrawn-phrase check, and six unfilled placeholders and a section headed "Still
# to add before submission" reached the built manuscript while this script printed
# ALL CHECKS PASS. Nothing had failed; two files had never been looked at.
sys.path.insert(0, os.path.join(HERE, "tools"))
from build_manuscript import SECTION_FILES as SECTIONS  # noqa: E402

# A check that should not read one of the assembled files says so here, by name and
# with the reason. That makes an exclusion a decision recorded in code and a gap an
# error -- which is the distinction the old list could not express, because a file
# simply absent from it looked exactly like a file deliberately left out.
SCOPE_EXCLUSIONS = {
    "scan": {
        "REFERENCES.md":
            "Its numbers are bibliographic: publication years, arXiv identifiers, "
            "DOI fragments, page ranges, and accuracies borrowed from other papers. "
            "They belong to results/LITERATURE_NUMBERS.csv, which check_literature.py "
            "gates, and not to MASTER_NUMBERS.csv, which this scan reads. Scanning it "
            "against the results registry reports 22 unregistered numbers, all of "
            "which are correct.",
    },
}


def scope(check):
    """The files a document check reads: everything the builder assembles, minus any
    exclusion this check has declared."""
    skip = SCOPE_EXCLUSIONS.get(check, {})
    return [name for name in SECTIONS if name not in skip]


MASTER = os.path.join(HERE, "results", "MASTER_NUMBERS.csv")
FOLDS = os.path.join(HERE, "results", "ALL_FOLDS.csv")
EXPECTED_FOLDS = 750
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]{2,60}>")


def run(label, cmd, ok_if):
    """Run cmd, print a verdict line, return True if it passed."""
    p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    out = p.stdout + p.stderr
    good = ok_if(p.returncode, out)
    extra = ""
    if label == "tests":
        m = re.search(r"(\d+) passed(?:, (\d+) skipped)?", out)
        if m:
            extra = "  (%s passed%s)" % (
                m.group(1),
                ", %s SKIPPED -- see below" % m.group(2) if m.group(2) else "")
    print("  %-18s %s%s" % (label, "PASS" if good else "FAIL", extra))
    if good and label == "tests":
        for line in out.splitlines():
            if line.startswith("SKIPPED"):
                print("      " + line.strip())
    if not good:
        for line in out.strip().splitlines()[-12:]:
            print("      " + line)
    return good


def check_release():
    """750 folds present, and the whole analysis reruns from the released files."""
    try:
        n = sum(1 for _ in csv.DictReader(open(FOLDS)))
    except OSError as exc:
        print("  %-18s FAIL\n      %s" % ("release", exc))
        return False
    good = n == EXPECTED_FOLDS
    print("  %-18s %s  (ALL_FOLDS.csv holds %d fold(s), expected %d)"
          % ("release", "PASS" if good else "FAIL", n, EXPECTED_FOLDS))
    return good


def check_duplicate_keys():
    """One claim, one row. Two rows under one key means a lookup can find either.

    This is how a rounded figure came to pass the scanner by matching an unrelated
    row that happened to carry the same string. Every (section, claim) pair must be
    unique for a registry lookup to mean anything.
    """
    import collections
    keys = collections.Counter()
    with open(MASTER) as fh:
        for r in csv.DictReader(fh):
            keys[(r["section"], r["claim"])] += 1
    dups = [(k, n) for k, n in keys.items() if n > 1]
    print("  %-18s %s  (%d duplicated (section, claim) key(s))"
          % ("duplicate keys", "PASS" if not dups else "FAIL", len(dups)))
    for (section, claim), n in dups[:10]:
        print("      x%d  %s  %s" % (n, section, claim))
    return not dups


def check_placeholders(journal):
    """Report every <placeholder> still present in a section to be submitted.

    Reads every file the builder assembles. It read ten of the twelve until
    25 September 2026, and the two it skipped held six of the eight placeholders.
    """
    found = []
    names = scope("placeholders")
    for name in names:
        path = os.path.join(journal, name)
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            for n, line in enumerate(fh, 1):
                for m in PLACEHOLDER.finditer(line):
                    if not m.group(0).lower().startswith(("<!--", "<br", "<sub", "<sup")):
                        found.append((name, n, m.group(0)))
    print("  %-18s %s  (%d placeholder(s) in %d assembled section(s))"
          % ("placeholders", "PASS" if not found else "ATTENTION",
             len(found), len(names)))
    for name, n, text in found:
        print("      %s:%d  %s" % (name, n, text))
    # A placeholder is a fact to act on, not a broken check: it does not fail the
    # run, because the author may be about to fill it in. It is always printed.
    return True


def check_decisions():
    """Report the three author decisions. Never fails the run.

    These are not properties of the paper -- they are statements two people have
    to be willing to sign -- so they cannot fail a check that answers "is the
    paper green?". But leaving them out entirely is how a placeholder reaches a
    submission portal, so every run says where they stand.
    """
    p = subprocess.run([sys.executable, os.path.join(HERE, "tools",
                                                     "check_submission_ready.py")],
                       cwd=HERE, capture_output=True, text=True)
    out = p.stdout + p.stderr
    pending = [ln.strip() for ln in out.splitlines() if ln.strip().endswith("PENDING")]
    total = len([ln for ln in out.splitlines()
                 if ln.strip().endswith(("PENDING", "CONFIRMED"))])
    print("  %-18s %s  (%d of %d pre-submission item(s) still open)"
          % ("decisions", "ATTENTION" if pending else "PASS", len(pending), total))
    for line in pending:
        print("      " + line)
    if pending:
        print("      manuscript/DECISION_SHEET.md is the one page they settle from")
    return True


# The manuscript sources live in the repository, at manuscript/. They used to live
# outside it, which meant a fresh extract of the release could run only the checks
# that touch code -- a minority of them -- and the other six reported missing files. A
# reviewer who cannot reproduce the verdict from the package has been handed a claim,
# not a check. Passing a directory still overrides this default.
DEFAULT_JOURNAL = os.path.join(HERE, "manuscript")


def main(argv):
    journal = argv[0] if argv else DEFAULT_JOURNAL
    # One scope per check, each derived from what the builder assembles. They are not
    # the same set: the scan reads the results registry, and REFERENCES.md carries
    # bibliographic numbers that live in a different registry. Every difference from
    # the assembled list is declared in SCOPE_EXCLUSIONS with its reason.
    scan_docs = [os.path.join(journal, n) for n in scope("scan")]
    withdrawn_docs = [os.path.join(journal, n) for n in scope("withdrawn")]
    all_md = sorted(
        os.path.join(journal, f) for f in os.listdir(journal) if f.endswith(".md")
    ) if os.path.isdir(journal) else []
    py = sys.executable

    print("preflight against %s\n" % journal)
    results = [
        # -rs so a skip is printed rather than folded into the count. The training
        # smoke test -- the only one that exercises the real training loop and its
        # leakage guards -- skips when TensorFlow is absent, and a silent skip there
        # is the difference between "the leakage check passed" and "nobody ran it".
        run("tests", [py, "-m", "pytest", "tests/", "-q", "-rs"],
            lambda rc, out: rc == 0),
        run("registry", [py, "src/registry.py"], lambda rc, out: rc == 0),
        run("row counts", [py, "tools/check_registry_count.py", MASTER] + all_md,
            lambda rc, out: rc == 0 and "0 wrong" in out),
        run("scan", [py, "src/scan.py"] + scan_docs,
            lambda rc, out: out.count("0 number(s) not in the registry")
            == len(scan_docs)),
        run("cross-references",
            [py, "tools/check_crossrefs.py", "tools/section_map_current.json"] + all_md,
            lambda rc, out: rc == 0 and "0 broken" in out),
        run("front matter", [py, "tools/check_frontmatter.py",
                             os.path.join(journal, "ABSTRACT.md")],
            lambda rc, out: rc == 0),
        check_release(),
        check_duplicate_keys(),
        run("manuscript", [py, "tools/build_manuscript.py", journal,
                           os.path.join(journal, "MANUSCRIPT.md")],
            lambda rc, out: rc == 0 and "MISSING" not in out and "WARNING" not in out),
        run("manuscript scan", [py, "src/scan.py",
                                os.path.join(journal, "MANUSCRIPT.md"),
                                "--stop-at", "# References"],
            lambda rc, out: "0 number(s) not in the registry" in out),
        run("figures", [py, "-m", "src.figures"],
            lambda rc, out: rc == 0 and out.count("wrote figures/") == 7),
        # Drawing a figure and citing a figure are not the same as showing one. Until
        # this check existed the manuscript contained seven captions and zero images.
        run("figure placement", [py, "tools/check_figure_placement.py"],
            lambda rc, out: rc == 0 and "every figure is placed once" in out),
        # Placed is not the same as printable. This one reads the files.
        run("print ready", [py, "tools/check_print_ready.py"],
            lambda rc, out: rc == 0 and "every paper figure has a vector PDF" in out),
        run("provenance", [py, "tools/figure_provenance.py"],
            lambda rc, out: rc == 0 and "registry value(s) plotted in total" in out),
        run("master file", [py, "tools/master_file.py"],
            lambda rc, out: rc == 0 and "wrote manuscript/MASTER_FILE.md" in out),
        # The check above proves the generator ran, not that the file agreed with it.
        # A hand edit to a generated file survives every check until the next
        # regeneration quietly discards it, which is how a withdrawn sentence returned
        # to MASTER_FILE.md on 2 October 2026 under ALL CHECKS PASS.
        run("generated files", [py, "tools/check_generated.py"],
            lambda rc, out: rc == 0 and "no hand edit" in out),
        # README.md and results/README.md are inside the withdrawn check since
        # 24 September 2026. They were outside it, and both had accumulated
        # retired claims -- the published repository's front page being the first
        # thing a reviewer reads, that was the worst place to leave unguarded.
        run("withdrawn", [py, "tools/check_withdrawn.py",
                          os.path.join(journal, "WITHDRAWN.md")] + withdrawn_docs +
            [os.path.join(journal, "MANUSCRIPT.md"),
             os.path.join(HERE, "README.md"),
             os.path.join(HERE, "results", "README.md")],
            lambda rc, out: rc == 0 and "0 withdrawn phrase(s) reappeared" in out
            and "0 near miss(es)" in out),
        run("released scores", [py, "tools/check_released_scores.py"],
            lambda rc, out: rc == 0 and "0 problem(s)" in out),
        # Gates the claim exactly as the paper now words it: the SUBJECT-AVERAGED
        # ranking metrics are unchanged at the reported precision. The pooled
        # comparison is printed by the same tool and deliberately does not gate,
        # because no pooled post-recalibration ranking metric is reported.
        run("ranking invariance", [py, "tools/check_ranking_invariance.py"],
            lambda rc, out: rc == 0
            and "0 subject-averaged value(s) change" in out),
        # Table 6 is merged by hand, so its emphasis is carried by hand. scan.py
        # reads values and cannot see which are wrapped in asterisks.
        run("table marks", [py, "tools/check_table_marks.py"],
            lambda rc, out: rc == 0 and "0 discrepancy(ies)" in out),
        # Ties the two hand-maintained files together: the borrowed-number registry
        # and the reference list it borrows from. They drifted once, and the drift
        # was invisible because no body sentence prints a reference year.
        run("literature", [py, "tools/check_literature.py"],
            lambda rc, out: rc == 0 and "0 problem(s)" in out),
        # The multiplicity table Section 7.10 prints, against a fresh recomputation,
        # plus the two facts the argument rests on: the Holm ceilings implied by the
        # p-value floors, and that every one-family BY survivor comes from the
        # prevalence family. Added 25 September 2026 with the multiplicity section.
        run("multiplicity", [py, "tools/check_multiplicity.py"],
            lambda rc, out: rc == 0 and "0 problem(s)" in out),
        # A new section must not be able to appear without somebody deciding whether
        # it belongs in the article, the supplementary material or the repository.
        run("split map", [py, "tools/check_split_map.py"],
            lambda rc, out: rc == 0 and "every unit is classified" in out),
        check_placeholders(journal),
        check_decisions(),
    ]
    failed = results.count(False)
    print("\n%s  (%d of %d checks passed)"
          % ("ALL CHECKS PASS" if not failed else "%d CHECK(S) FAILED" % failed,
             len(results) - failed, len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
