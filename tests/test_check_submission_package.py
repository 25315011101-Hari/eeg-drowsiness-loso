"""Checks on the package check -- above all, that its collision detector works.

    python -m pytest tests/test_check_submission_package.py -q

tools/check_submission_package.py exists because of one defect: on 7 October 2026 the
supplementary PDF printed "DeepConvNet8,212", a model name on top of the next column's
number, eight times across two tables, and every automated check in this repository
passed on that file. The detector written to catch it is therefore the thing most
worth testing, and it has a history: two earlier versions of it reported "no
collisions" on the defective file, and a third reported one on a clean file.

  * the first looked only for overlapping word boxes. Poppler reports some of these
    pairs as touching rather than overlapping, so it found nothing.
  * the second looked only for a merged token. Poppler splits some of these pairs back
    into two words, so it found nothing either.
  * the third looked for a letter followed by any digit, and reported "python3", which
    is in the manuscript's own commands.

So this file builds small documents that collide and small documents that do not, and
checks the detector against both. A detector that only ever says "clean" passes no
test here.

WHAT IS NOT TESTED HERE, AND WHY

The whole command end to end. Running it needs all four built files, and building the
article PDF takes far longer than the rest of this suite put together. The command is
the pre-submission step; these tests are what make its answer worth reading.

Needs pandoc and xelatex for the two small builds, and pdftotext. Without them the
module skips, visibly.
"""

import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import check_submission_package as P  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (shutil.which("pandoc") and shutil.which("xelatex") and shutil.which("pdftotext")),
    reason="needs pandoc, xelatex and pdftotext to build and read the small documents")


def build(tmp, name, markdown):
    src = os.path.join(tmp, name + ".md")
    out = os.path.join(tmp, name + ".pdf")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    p = subprocess.run(["pandoc", src, "-o", out, "--pdf-engine=xelatex",
                        "-V", "mainfont=FreeSerif",
                        "-V", "geometry:a4paper,margin=2.5cm",
                        "-V", "fontsize=10pt"], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-400:]
    return out


# Nine equal columns, the same shape as Table S2, and a name with nothing to break at.
COLLIDES = """\
| Arm | Model | TN | FP | FN | TP | Recall | Precision | Accuracy |
|---|---|---|---|---|---|---|---|---|
| A | ShallowConvNet | 7,090 | 1,400 | 158 | 612 | 0.794 | 0.304 | 83.17 % |
| A | DeepConvNet | 8,212 | 278 | 395 | 375 | 0.487 | 0.574 | 92.73 % |
"""

# The same table with the model column given room, which is the fix under test.
CLEAN = """\
| Arm | Model | TN | FP | FN | TP | Recall | Precision | Accuracy |
|---|--------|---|---|---|---|-----|---|------|
| A | ShallowConvNet | 7,090 | 1,400 | 158 | 612 | 0.794 | 0.304 | 83.17 % |
| A | DeepConvNet | 8,212 | 278 | 395 | 375 | 0.487 | 0.574 | 92.73 % |
"""

# Two things that look like collisions to a careless detector and are not.
INNOCENT = """\
Rebuild it with `python3 tools/build_pdf.py`, which writes into pdf/.

The recordings were collected by Garcés Correa, Cañadas and Müller-Wittig, and the
windows are 1280 samples long.
"""


@pytest.fixture(scope="module")
def docs(tmp_path_factory):
    tmp = str(tmp_path_factory.mktemp("pdfs"))
    return {"collides": build(tmp, "collides", COLLIDES),
            "clean": build(tmp, "clean", CLEAN),
            "innocent": build(tmp, "innocent", INNOCENT)}


# ----------------------------------------------------------- the detector bites
def test_a_colliding_table_is_caught(docs):
    hits, merged = P.pdf_collisions(docs["collides"])
    assert hits or merged, "the detector reported a clean file; it is the defect itself"
    names = " ".join(hits + merged)
    assert "ShallowConvNet" in names or "DeepConvNet" in names, names


def test_each_half_of_the_detector_is_doing_work(docs):
    """Both halves must fire, and each on the row only it can see.

    This table was chosen so that poppler produces one of each: ShallowConvNet and its
    number come back as two boxes that overlap, DeepConvNet and its number come back as
    the single token "DeepConvNet8,212". An earlier version of these tests asserted
    only "hits or merged", which passed with either half of the detector deleted --
    the exact failure the detector's history is made of. Asserting each separately is
    what pins both.
    """
    hits, merged = P.pdf_collisions(docs["collides"])
    assert hits, "the overlapping-box half found nothing; poppler reports one here"
    assert merged, "the merged-token half found nothing; poppler reports one here"
    assert any("ShallowConvNet" in h for h in hits), hits
    assert any(m.startswith("DeepConvNet") for m in merged), merged


def test_the_same_table_with_room_is_clean(docs):
    hits, merged = P.pdf_collisions(docs["clean"])
    assert (hits, merged) == ([], []), (hits, merged)


# -------------------------------------------------- the detector does not cry wolf
def test_a_command_name_is_not_a_collision(docs):
    """python3 and 1280 are not model names printed on top of numbers."""
    hits, merged = P.pdf_collisions(docs["innocent"])
    assert "python3" not in " ".join(merged), merged
    assert (hits, merged) == ([], []), (hits, merged)


def test_an_accented_letter_is_not_a_collision(docs):
    """Garcés and Müller-Wittig print as a letter box touching its mark."""
    hits, _merged = P.pdf_collisions(docs["innocent"])
    assert not any("Garc" in h or "ller" in h or "ada" in h for h in hits), hits


# ------------------------------------------------------- the package's own rules
def test_a_file_from_an_older_build_is_not_accepted(tmp_path):
    """The whole point of the build id is that a stale package cannot pass quietly."""
    for name in ("Manuscript_BSPC_2026-10-07_build_aaaaaaaaaaaa.docx",
                 "Highlights_BSPC_2026-10-07_build_aaaaaaaaaaaa.docx"):
        (tmp_path / name).write_text("", encoding="utf-8")
    hits = P.find(str(tmp_path), P.EXPECTED["manuscript docx"][0], "bbbbbbbbbbbb")
    assert len(hits) == 1, hits
    carried = hits[0].rsplit("_build_", 1)[1].split(".")[0]
    assert carried != "bbbbbbbbbbbb", "a stale id must be visible to the caller"


def test_the_two_docx_files_are_not_confused_with_each_other(tmp_path):
    for name in ("Manuscript_BSPC_2026-10-07_build_abc123abc123.docx",
                 "Highlights_BSPC_2026-10-07_build_abc123abc123.docx"):
        (tmp_path / name).write_text("", encoding="utf-8")
    m = P.find(str(tmp_path), P.EXPECTED["manuscript docx"][0], "abc123abc123")
    h = P.find(str(tmp_path), P.EXPECTED["highlights docx"][0], "abc123abc123")
    assert m == ["Manuscript_BSPC_2026-10-07_build_abc123abc123.docx"], m
    assert h == ["Highlights_BSPC_2026-10-07_build_abc123abc123.docx"], h


def test_the_pdf_and_the_docx_are_not_confused(tmp_path):
    for name in ("Manuscript_BSPC_2026-10-07_build_abc123abc123.docx",
                 "Manuscript_BSPC_2026-10-07_build_abc123abc123.pdf"):
        (tmp_path / name).write_text("", encoding="utf-8")
    assert P.find(str(tmp_path), P.EXPECTED["manuscript docx"][0], "abc") == \
        ["Manuscript_BSPC_2026-10-07_build_abc123abc123.docx"]
    assert P.find(str(tmp_path), P.EXPECTED["manuscript pdf"][0], "abc") == \
        ["Manuscript_BSPC_2026-10-07_build_abc123abc123.pdf"]


def test_the_declarations_are_named_rather_than_counted():
    """Five headings, each spelled out, because a count cannot say which one went."""
    assert len(P.DECLARATIONS) == len(set(P.DECLARATIONS))
    for d in P.DECLARATIONS:
        assert isinstance(d, str) and len(d) > 4, d
    # The two the journal is strictest about must be among them.
    assert "Declaration of competing interest" in P.DECLARATIONS
    assert "Data availability" in P.DECLARATIONS


def built_docx_with(tmp, text):
    """The smallest thing missing_declarations() will read: a .docx holding `text`."""
    import zipfile
    path = os.path.join(tmp, "m.docx")
    body = "".join("<w:p><w:r><w:t>%s</w:t></w:r></w:p>" % t for t in text)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml",
                   '<?xml version="1.0"?><w:document xmlns:w="w"><w:body>'
                   + body + "</w:body></w:document>")
    return path


def test_a_document_carrying_every_declaration_passes(tmp_path):
    path = built_docx_with(str(tmp_path), P.DECLARATIONS)
    assert P.missing_declarations(path) == []


def test_a_declaration_missing_from_the_submitted_file_is_caught(tmp_path):
    """Drop each one in turn; each time, that one and only that one must be named."""
    for dropped in P.DECLARATIONS:
        kept = [d for d in P.DECLARATIONS if d != dropped]
        assert dropped not in " ".join(kept), "the corruption did not fire for %r" % dropped
        path = built_docx_with(str(tmp_path), kept)
        assert P.missing_declarations(path) == [dropped], dropped


def test_the_real_submitted_file_carries_them_all():
    """Against the package in docx/, if it has been built. Skipped if it has not."""
    import glob
    hits = glob.glob(os.path.join(P.HERE, "docx", "Manuscript_*.docx")) or \
        glob.glob(os.path.join(P.HERE, "pkg", "Manuscript_*.docx"))
    if not hits:
        pytest.skip("no built package to check; run the builders first")
    assert P.missing_declarations(hits[0]) == []


def test_a_missing_directory_is_refused_rather_than_passed(tmp_path):
    with pytest.raises(SystemExit):
        P.main([str(tmp_path / "there-is-no-such-directory")])


def test_a_hand_named_file_does_not_count(tmp_path):
    """"Manuscript.docx" is what somebody renames a copy to; it carries no build id."""
    (tmp_path / "Manuscript.docx").write_text("", encoding="utf-8")
    (tmp_path / "Manuscript_final_v2.docx").write_text("", encoding="utf-8")
    assert P.find(str(tmp_path), P.EXPECTED["manuscript docx"][0], "abc") == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-rs"]))
