"""Checks on the separate highlights file the submission system asks for.

    python -m pytest tests/test_build_highlights.py -q

The highlights are uploaded on their own, away from the paper, so nothing about the
article protects them: a bullet lost, duplicated or silently reworded on the way into
the .docx would be published exactly as received. tools/build_highlights.py therefore
reads them from manuscript/MANUSCRIPT.md and audits what it wrote, and this file
checks that the audit is not decoration.

THE RULE EVERY NEGATIVE CONTROL HERE OBEYS

    corrupt -> ASSERT the corruption actually changed something -> ASSERT it is caught

The assertion in the middle is not ceremony. On 4 October 2026 a control written for
tools/build_docx.py corrupted the SOURCE rather than the output, so the document was
rebuilt from it, both sides agreed and the audit passed -- correctly, having measured
nothing. On 7 October 2026, while this script was being checked by hand, a second
control searched for `<w:t>Highlights</w:t>` when pandoc writes
`<w:t xml:space="preserve">Highlights</w:t>`; the search matched nothing, the file was
never corrupted, the audit stayed silent and the control looked like a failure of the
audit. It was not. Both mistakes are invisible without the middle assertion, and both
are the same mistake: a control that did nothing, counted as evidence.

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
from tools import build_highlights as B  # noqa: E402
from tools import check_frontmatter as C  # noqa: E402

HERE = B.HERE
MANUSCRIPT = os.path.join(HERE, B.MANUSCRIPT)

pytestmark = pytest.mark.skipif(
    shutil.which("pandoc") is None,
    reason="pandoc is not installed, so the .docx cannot be built here")


def manuscript_text():
    with open(MANUSCRIPT, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def bullets():
    return B.bullets_from(manuscript_text())


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("highlights")
    code = B.run(str(out_dir))
    names = [n for n in os.listdir(out_dir) if n.endswith(".docx")]
    assert code == 0, "the build reported a problem"
    assert len(names) == 1, names
    return os.path.join(out_dir, names[0])


def document_xml(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def visible_text(path):
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", document_xml(path)))


def paragraphs(path):
    """Every non-empty paragraph, in the order Word will show them."""
    out = []
    for m in re.finditer(r"<w:p[ >].*?</w:p>", document_xml(path), re.S):
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", m.group(0)))
        if text.strip():
            out.append(text)
    return out


# ------------------------------------------------------------------- happy path
def test_the_filename_names_the_file_and_carries_the_manuscripts_build_id(built):
    bid = B.build_docx.build_id(manuscript_text(), B.MANUSCRIPT)
    name = os.path.basename(built)
    # The journal asks for the highlights as a file of their own; a reader of a
    # downloads folder has only the name to go on.
    assert name.startswith("Highlights_BSPC_"), name
    assert name.endswith("_build_%s.docx" % bid), name
    assert re.search(r"_BSPC_\d{4}-\d{2}-\d{2}_build_", name), name


def test_it_is_a_real_editable_docx(built):
    with zipfile.ZipFile(built) as z:
        names = z.namelist()
    assert "word/document.xml" in names
    assert "[Content_Types].xml" in names


def test_every_bullet_arrives_unaltered(built, bullets):
    body = paragraphs(built)
    assert body[0] == B.HEADING, body[:1]
    assert body[1:] == bullets, "the document's bullets are not the manuscript's"


def test_there_is_one_list_item_per_bullet_and_nothing_else(built, bullets):
    doc = document_xml(built)
    assert doc.count("<w:numPr>") == len(bullets)
    assert len(paragraphs(built)) == len(bullets) + 1, "an extra paragraph is present"


def test_the_file_carries_no_other_content(built):
    """No table, no figure, no abstract: this file is the highlights and nothing else."""
    doc = document_xml(built)
    assert doc.count("<w:tbl>") == 0
    with zipfile.ZipFile(built) as z:
        assert [n for n in z.namelist() if n.startswith("word/media/")] == []


def test_the_limits_are_read_from_the_guide_and_not_from_this_code(bullets):
    L = C.limits(C.requirements())
    assert L["highlights_min"] <= len(bullets) <= L["highlights_max"]
    for b in bullets:
        assert len(b) <= L["highlight_chars"], b


# --------------------------------------------------- controls: a bad SOURCE
def test_a_sixth_bullet_is_refused(bullets):
    tampered = bullets + ["A sixth highlight nobody approved"]
    assert tampered != bullets
    with pytest.raises(SystemExit):
        B.within_the_guides_limits(tampered)


def test_too_few_bullets_are_refused(bullets):
    tampered = bullets[:2]
    assert len(tampered) < len(bullets)
    with pytest.raises(SystemExit):
        B.within_the_guides_limits(tampered)


def test_one_character_over_the_limit_is_refused(bullets):
    limit = C.limits(C.requirements())["highlight_chars"]
    tampered = bullets[:-1] + ["x" * (limit + 1)]
    assert len(tampered[-1]) == limit + 1
    with pytest.raises(SystemExit):
        B.within_the_guides_limits(tampered)


def test_a_renamed_heading_is_refused_rather_than_guessed():
    text = manuscript_text()
    tampered = text.replace("## Highlights", "## Key points")
    assert tampered != text, "the corruption did not fire"
    with pytest.raises(SystemExit):
        B.bullets_from(tampered)


def test_a_section_without_bullets_is_refused():
    text = manuscript_text()
    tampered = re.sub(r"(## Highlights\n)(.*?)(\n---)", r"\1\n\3", text, flags=re.S)
    assert tampered != text, "the corruption did not fire"
    with pytest.raises(SystemExit):
        B.bullets_from(tampered)


def test_a_manuscript_without_a_build_stamp_is_refused():
    text = manuscript_text()
    tampered = re.sub(r"(?m)^\*Build .*$", "", text)
    assert tampered != text, "the corruption did not fire"
    with pytest.raises(SystemExit):
        B.build_docx.build_id(tampered, B.MANUSCRIPT)


# --------------------------------------------- controls: a corrupted OUTPUT
def corrupted(src, dest, change):
    """A copy of the built file with word/document.xml put through `change`.

    Refuses to return a file the change did not alter. A control that corrupts
    nothing proves nothing, and this is where that is enforced once for all four.
    """
    with zipfile.ZipFile(src) as z:
        items = z.infolist()
        blobs = {i.filename: z.read(i.filename) for i in items}
    before = blobs["word/document.xml"].decode("utf-8")
    after = change(before)
    assert after != before, "the corruption did not fire; this control proves nothing"
    blobs["word/document.xml"] = after.encode("utf-8")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for i in items:
            z.writestr(i, blobs[i.filename])
    return dest


def test_the_audit_passes_the_file_it_built(built, bullets):
    assert B.audit(bullets, built) == []


def test_a_removed_heading_is_caught(built, bullets, tmp_path):
    bad = corrupted(built, str(tmp_path / "noheading.docx"),
                    lambda d: re.sub(r"<w:t[^>]*>%s</w:t>" % B.HEADING,
                                     "<w:t>Overview</w:t>", d, count=1))
    assert B.HEADING not in visible_text(bad), "the heading is still there"
    problems = B.audit(bullets, bad)
    assert any(B.HEADING in p for p in problems), problems


def test_a_deleted_bullet_is_caught(built, bullets, tmp_path):
    gone = bullets[2]
    bad = corrupted(built, str(tmp_path / "missing.docx"),
                    lambda d: d.replace(gone, "", 1))
    assert visible_text(bad).count(gone) == 0, "the bullet is still there"
    problems = B.audit(bullets, bad)
    assert any("appears 0 time(s)" in p for p in problems), problems


def test_a_duplicated_bullet_is_caught(built, bullets, tmp_path):
    twice = bullets[0]
    bad = corrupted(built, str(tmp_path / "twice.docx"),
                    lambda d: d.replace(
                        "</w:body>",
                        "<w:p><w:r><w:t>%s</w:t></w:r></w:p></w:body>" % twice, 1))
    assert visible_text(bad).count(twice) == 2, "the bullet was not duplicated"
    problems = B.audit(bullets, bad)
    assert any("appears 2 time(s)" in p for p in problems), problems


def test_a_reworded_bullet_is_caught(built, bullets, tmp_path):
    """The quietest corruption of all: the file still reads, and says something else."""
    original = bullets[3]
    reworded = original.replace("unchanged", "improved")
    assert reworded != original, "pick a bullet the rewording actually changes"
    bad = corrupted(built, str(tmp_path / "reworded.docx"),
                    lambda d: d.replace(original, reworded, 1))
    assert reworded in visible_text(bad)
    problems = B.audit(bullets, bad)
    assert any("appears 0 time(s)" in p for p in problems), problems


def test_a_lost_list_item_is_caught(built, bullets, tmp_path):
    bad = corrupted(built, str(tmp_path / "unlisted.docx"),
                    lambda d: d.replace("<w:numPr>", "<w:numPrX>", 1))
    assert document_xml(bad).count("<w:numPr>") == len(bullets) - 1
    problems = B.audit(bullets, bad)
    assert any("list item(s)" in p for p in problems), problems


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-rs"]))
