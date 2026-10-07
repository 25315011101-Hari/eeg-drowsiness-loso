"""Checks on the .docx the journal will actually receive.

    python -m pytest tests/test_build_docx.py -q

The guide for authors does not accept a PDF as a source file, so tools/build_docx.py
builds the editable manuscript instead, and its audit is the only thing standing
between a silent conversion loss and a reviewer. A conversion that drops a table or
thins sixty minus signs to fifty-nine produces a file that opens, reads and is wrong.

So these tests are in two halves, and the second half is the one that matters:

  the build works     the command runs clean, the filename carries the manuscript's
                      own build id, exactly the wide tables are landscape, no table
                      row may split across a page, and the repository's build stamp
                      does not travel to the journal

  the audit bites     four corruptions are applied TO THE BUILT DOCUMENT and each
                      one must be caught

The second half exists because of a mistake made on 4 October 2026 while this script
was being written. The first negative control corrupted the SOURCE markdown, so the
document was rebuilt from the corrupted source, both sides agreed, and the audit
passed -- correctly. A negative control that corrupts the input of a comparison tests
nothing. The corruption has to be applied to the output, after the build, with the
source left alone. All four below do that.

Needs pandoc. Without it the whole module skips, visibly: tools/preflight.py runs
pytest with -rs so a skip is printed rather than counted as a pass.
"""

import os
import re
import shutil
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import build_docx  # noqa: E402

HERE = build_docx.HERE
MANUSCRIPT = os.path.join(HERE, build_docx.MANUSCRIPT)

pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc is not installed, so the .docx cannot be built here")


# --------------------------------------------------------------- the build works
@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One build, reused by every test below. It takes about a second."""
    out_dir = tmp_path_factory.mktemp("docx")
    code = build_docx.run(str(out_dir))
    names = [n for n in os.listdir(out_dir) if n.endswith(".docx")]
    assert code == 0, "the build reported a problem"
    assert len(names) == 1, names
    return os.path.join(out_dir, names[0])


def document_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def visible_text(path):
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", document_xml(path)))


def test_the_filename_carries_the_manuscripts_own_build_id(built):
    with open(MANUSCRIPT, encoding="utf-8") as fh:
        bid = build_docx.build_id(fh.read(), build_docx.MANUSCRIPT)
    name = os.path.basename(built)
    assert name.endswith("_build_%s.docx" % bid), name
    assert name.startswith("Manuscript_BSPC_"), name


def test_build_id_is_read_and_not_invented():
    with pytest.raises(SystemExit):
        build_docx.build_id("a manuscript with no stamp at its foot\n", "x.md")


def test_exactly_the_wide_tables_are_on_a_landscape_page(built):
    doc = document_xml(built)
    tables = [m.group(0) for m in build_docx.TABLE.finditer(doc)]
    wide = [t for t in tables
            if t.count("<w:gridCol") >= build_docx.LANDSCAPE_MIN_COLUMNS]
    assert tables, "the manuscript has tables; the document has none"
    # One landscape section is opened per wide table and nothing else opens one.
    assert doc.count('w:orient="landscape"') == len(wide)
    # The threshold is a measurement, not a preference: no narrow table may be
    # dragged onto a landscape page by a rule that counts something else.
    for t in tables:
        if t.count("<w:gridCol") < build_docx.LANDSCAPE_MIN_COLUMNS:
            assert 'w:orient="landscape"' not in t


def test_no_table_row_may_split_across_a_page(built):
    """Every row carries the setting, in exactly one properties element.

    Both halves are needed. "Every row has it" alone passed a document in which the
    25 header rows carried two <w:trPr> each -- which the schema does not allow and
    LibreOffice did not complain about, so it reached a built PDF on 4 October 2026
    unnoticed. "One each" alone would pass a document where no row has the setting.
    """
    doc = document_xml(built)
    rows = len(re.findall(r"<w:tr[ >]", doc))
    assert rows, "the manuscript has tables; the document has no rows"
    assert doc.count("<w:trPr>") == rows, "a row has no properties, or has two"
    assert doc.count("<w:cantSplit/>") == rows
    assert not re.search(r"<w:tr>(?!<w:trPr>)", doc), "a row was left without the setting"
    assert not re.search(r"</w:trPr>\s*<w:trPr>", doc), "a row carries two <w:trPr>"


def test_the_repositorys_build_stamp_does_not_go_to_the_journal(built):
    text = visible_text(built)
    assert "Rebuild:" not in text
    assert not re.search(r"Build [0-9a-f]{6,}", text)


def test_the_stamp_is_required_rather_than_quietly_tolerated(tmp_path):
    plain = tmp_path / "no-stamp.md"
    plain.write_text("# A manuscript that was never stamped\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        build_docx.without_build_stamp(str(plain), str(tmp_path))


# ---------------------------------------------------------------- the audit bites
@pytest.fixture(scope="module")
def feed(tmp_path_factory):
    """The manuscript as pandoc saw it: the same file the audit compares against."""
    work = tmp_path_factory.mktemp("feed")
    return build_docx.without_build_stamp(MANUSCRIPT, str(work))


def rewritten(src, dest, change):
    """A copy of the built document with word/document.xml put through `change`."""
    with zipfile.ZipFile(src) as z:
        items = z.infolist()
        blobs = {i.filename: z.read(i.filename) for i in items}
    blobs["word/document.xml"] = change(
        blobs["word/document.xml"].decode("utf-8")).encode("utf-8")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for i in items:
            z.writestr(i, blobs[i.filename])
    return dest


def table_count(path):
    return len(build_docx.TABLE.findall(document_xml(path)))


def test_the_audit_passes_the_document_it_was_built_from(built, feed):
    problems, _notes = build_docx.audit(feed, built, table_count(built))
    assert problems == []


def test_a_single_dropped_non_ascii_character_is_caught(built, feed, tmp_path):
    """One of sixty minus signs removed from the document must fail the audit.

    The character has to be chosen from the MANUSCRIPT, not from the document. An
    earlier version of this test took the document's first non-ASCII character, which
    is U+00A0 -- a non-breaking space pandoc inserts and the manuscript never had.
    Removing one of those is not a loss, the audit was right to stay silent, and the
    test was measuring nothing.
    """
    with open(feed, encoding="utf-8") as fh:
        source = fh.read()
    pool = [c for c in set(source) if ord(c) > 127
            and c not in build_docx.SUBSTITUTIONS and c not in build_docx.INSERTED]
    lost = max(pool, key=source.count)
    text = visible_text(built)
    assert text.count(lost) == source.count(lost), "chosen before anything was dropped"
    bad = rewritten(built, str(tmp_path / "dropped.docx"),
                    lambda doc: doc.replace(lost, "", 1))
    # the corruption did what the test claims it did
    assert visible_text(bad).count(lost) == text.count(lost) - 1
    problems, _ = build_docx.audit(feed, bad, table_count(bad))
    assert any("U+%04X" % ord(lost) in p for p in problems), problems


def test_a_character_the_manuscript_never_had_is_caught(built, feed, tmp_path):
    bad = rewritten(built, str(tmp_path / "gained.docx"),
                    lambda doc: doc.replace("</w:t>", "€</w:t>", 1))
    problems, _ = build_docx.audit(feed, bad, table_count(bad))
    assert any("not a declared substitution" in p for p in problems), problems


def test_a_lost_table_is_caught(built, feed, tmp_path):
    bad = rewritten(built, str(tmp_path / "untabled.docx"),
                    lambda doc: build_docx.TABLE.sub("", doc, count=1))
    assert table_count(bad) == table_count(built) - 1
    problems, _ = build_docx.audit(feed, bad, table_count(bad))
    assert any("tables and the document has" in p for p in problems), problems


def test_a_lost_figure_is_caught(built, feed, tmp_path):
    dest = str(tmp_path / "unfigured.docx")
    with zipfile.ZipFile(built) as z:
        items = z.infolist()
        blobs = {i.filename: z.read(i.filename) for i in items}
    media = [n for n in blobs if n.startswith("word/media/")]
    assert media, "the manuscript embeds figures; the document embeds none"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for i in items:
            if i.filename != media[0]:
                z.writestr(i, blobs[i.filename])
    problems, _ = build_docx.audit(feed, dest, table_count(dest))
    assert any("images and the document embeds" in p for p in problems), problems


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-rs"]))
