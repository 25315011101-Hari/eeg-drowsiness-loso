"""Check the main-article / supplementary / repository map against the manuscript.

    python3 tools/check_split_map.py [--long] [--by-section]

The map is declared in tools/split_map.json. This reads the assembled manuscript,
enumerates every unit the map is supposed to cover, and answers four questions:

  1. Is every heading, table and figure in the manuscript classified? An unclassified
     unit is the failure mode this whole exercise exists to prevent: a section nobody
     decided about, cut or kept by whoever happens to be editing.
  2. Does the map classify anything that is not in the manuscript? A stale entry is a
     decision about a section that no longer exists, and it hides the fact that the
     real section is unclassified under its new name.
  3. Does every unit leaving the main article declare what the main article retains?
     This is the corresponding author's rule -- scientific evidence is not hidden in
     the supplementary material -- made checkable. A move with no main_retains is
     refused.
  4. What does the map project? Word counts are read from the manuscript, never
     declared in the map, so the projection cannot drift from the paper.

It does not cut anything and never edits the manuscript. Until the map is applied,
every projected number is a target and the audited word counts are the real ones.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(HERE, "tools", "split_map.json")
MANUSCRIPT = os.path.join(HERE, "manuscript", "MANUSCRIPT.md")
SUPPLEMENT = os.path.join(HERE, "manuscript", "SUPPLEMENTARY.md")

HEADING = re.compile(r"^(#{1,3}) +(.*?)\s*$")
TABLE_CAPTION = re.compile(r"^\*\*Table\s+(\d+[a-z]?)\.\s")
FIGURE_FILE = re.compile(r"^(figure[0-9S][A-Za-z0-9_]*)\.png$")
LEAVES_MAIN = ("SUPPLEMENTARY", "REPOSITORY")


def load_map(path=MAP):
    with open(path) as fh:
        data = json.load(fh)
    for key in ("sections", "tables", "figures", "destinations", "target"):
        if key not in data:
            raise SystemExit("split_map.json has no %r section" % key)
    return data


def units(path=MANUSCRIPT):
    """Every unit of the manuscript the map must cover, with its own word count.

    A section's words are the words between its heading and the next heading of any
    level, so a parent section is not credited with its children's text and no word
    is counted twice. The totals therefore add up, which is the only reason a
    projection from them means anything.
    """
    lines = open(path).read().splitlines()
    heads = [(i, m.group(1), m.group(2)) for i, l in enumerate(lines)
             for m in [HEADING.match(l)] if m]
    sections, order = {}, []
    for k, (i, hashes, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        key = re.sub(r"\s+", " ", title).strip()
        # An image's alt text is an accessibility attribute, not prose the reader
        # reads, so it is not counted. Counting it would make placing the figures
        # look like writing 74 more words of article.
        body = [l for l in lines[i + 1:end] if not l.lstrip().startswith("![")]
        words = len([t for t in " ".join(body).split() if re.search(r"[0-9A-Za-z]", t)])
        if key in sections:                    # two headings with one title
            sections[key]["words"] += words
            sections[key]["repeats"] += 1
        else:
            sections[key] = dict(level=len(hashes), words=words, line=i + 1, repeats=1)
            order.append(key)
    tables = sorted({m.group(1) for l in lines for m in [TABLE_CAPTION.match(l.strip())]
                     if m}, key=lambda s: (len(s), s))
    return sections, order, tables


def _in_supplement(needle, path=SUPPLEMENT):
    """Is this exact string in the supplementary document?"""
    return os.path.exists(path) and needle in open(path).read()


def supplement_headings(path=SUPPLEMENT):
    """The headings of the supplementary document, or none if it does not exist."""
    if not os.path.exists(path):
        return set()
    return {HEADING.match(l).group(2).strip()
            for l in open(path).read().splitlines() if HEADING.match(l)}


def article_tables(path=MANUSCRIPT):
    """The table numbers the ARTICLE actually carries, in order of appearance."""
    lines = open(path).read().splitlines()
    out = []
    for l in lines:
        m = TABLE_CAPTION.match(l.strip())
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def figures(root=HERE):
    """Figures by the files that exist, not by the numbers the prose happens to cite.

    A figure cited nowhere and a figure drawn but never cited are both errors the
    map should surface, and only the file list sees the second one.
    """
    out = {}
    d = os.path.join(root, "figures")
    for name in sorted(os.listdir(d)):
        m = FIGURE_FILE.match(name)
        if not m:
            continue
        stem = m.group(1)
        n = re.match(r"figure(S?\d+)", stem)
        out[n.group(1) if n else stem] = stem
    return out


def check(data, sections, order, tables, figs):
    problems = []

    declared = data["sections"]
    for key in order:
        if key not in declared:
            problems.append("section %r is in the manuscript and not in the map "
                            "(line %d, %d words)"
                            % (key, sections[key]["line"], sections[key]["words"]))
    # A unit the map sends out of the article is not missing when it is absent from
    # the article -- it is absent because it was moved. It must then be PRESENT in
    # the supplementary document, under the heading the map says it becomes. Checking
    # only the article would let a move that deleted its unit pass silently, which is
    # the one failure this whole exercise exists to prevent.
    supp = supplement_headings()
    for key, entry in declared.items():
        if key in sections:
            continue
        dest = entry.get("dest")
        if dest == "SUPPLEMENTARY":
            becomes = entry.get("becomes")
            if not becomes:
                problems.append("section %r has left the article and the map does not "
                                "say what it became in the supplement" % key)
            elif becomes not in supp:
                problems.append("section %r was moved out of the article and is not in "
                                "manuscript/SUPPLEMENTARY.md as %r; it may have been "
                                "deleted rather than moved" % (key, becomes))
        elif dest == "REPOSITORY":
            pass                       # it belongs to neither document, by decision
        else:
            problems.append("the map classifies %r as %s, which is not a heading in "
                            "the manuscript; it was renamed or removed" % (key, dest))

    for num in tables:
        if num not in data["tables"]:
            problems.append("Table %s has a caption in the manuscript and no entry "
                            "in the map" % num)
    for num, entry in data["tables"].items():
        if num.startswith("_") or not isinstance(entry, dict):
            continue
        if num in tables:
            continue
        if entry.get("dest") == "SUPPLEMENTARY":
            becomes = entry.get("becomes")
            if not becomes or not _in_supplement("**%s." % becomes):
                problems.append("Table %s was moved out of the article and its "
                                "caption is not in manuscript/SUPPLEMENTARY.md as "
                                "%r" % (num, becomes))
        else:
            problems.append("the map classifies Table %s as %s, which has no caption "
                            "in the manuscript" % (num, entry.get("dest")))

    # The article's own tables must run 1, 2, 3 ... with no gap. Moving Table 1 to the
    # supplement left the article starting at Table 2, which is the same defect the
    # figures had on 30 September and the same thing a production editor queries.
    nums = [int(n) for n in article_tables() if n.isdigit()]
    if nums and nums != list(range(1, len(nums) + 1)):
        problems.append("the article's tables are numbered %s; after the move they "
                        "must be renumbered to run from 1 with no gap"
                        % ", ".join(str(n) for n in nums))

    mapped_files = {e.get("file") for e in data["figures"].values()
                    if isinstance(e, dict)}
    for num, stem in figs.items():
        if stem not in mapped_files:
            problems.append("figures/%s.png exists and is not in the map" % stem)
    for num, entry in data["figures"].items():
        if num.startswith("_"):
            continue
        stem = entry.get("file")
        if stem and stem not in figs.values():
            # A figure the map places but no file backs. fig6_code_structure is a
            # repository diagram and is matched here by name rather than by the
            # figure pattern, so allow a REPOSITORY entry to name a file that the
            # figure pattern does not match but that does exist.
            if not os.path.exists(os.path.join(HERE, "figures", stem + ".png")):
                problems.append("the map places %r, and no such figure file exists"
                                % stem)

    # The author's rule, made checkable.
    for group, label in ((data["sections"], "section"), (data["tables"], "Table"),
                         (data["figures"], "Figure"),
                         (data.get("fragments", {}), "fragment")):
        for key, entry in group.items():
            if key.startswith("_") or not isinstance(entry, dict):
                continue
            dest = entry.get("dest")
            if dest is None:
                problems.append("%s %s declares no destination" % (label, key))
                continue
            if dest not in data["destinations"]:
                problems.append("%s %s has destination %r, which is not one of %s"
                                % (label, key, dest, sorted(data["destinations"])))
            if not entry.get("reason"):
                problems.append("%s %s gives no reason" % (label, key))
            if dest in LEAVES_MAIN and not entry.get("main_retains"):
                problems.append("%s %s leaves the main article and does not say what "
                                "the main article retains; the author's rule is that "
                                "scientific evidence is not hidden in the "
                                "supplementary material" % (label, key))
            if dest == "BOTH" and not entry.get("main_form"):
                problems.append("%s %s is split across both documents and does not "
                                "say what the reduced form in the article shows"
                                % (label, key))
            if dest in ("MAIN", "BOTH") and label == "section":
                target = entry.get("target_words")
                now = sections.get(key, {}).get("words", 0)
                if target is None:
                    problems.append("section %s stays in the article and declares no "
                                    "target length" % key)
                elif not data.get("applied") and target > now:
                    problems.append("section %s targets %d words and currently has "
                                    "%d; a target above the current length is not a "
                                    "reduction" % (key, target, now))
                elif data.get("applied") and now > target:
                    problems.append("the map is marked applied, and section %s is %d "
                                    "words against its target of %d"
                                    % (key, now, target))

    # Every fragment must hang off a section that exists and stays classified.
    for key, entry in data.get("fragments", {}).items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        host = entry.get("host")
        if host not in sections:
            problems.append("fragment %s names host %r, which is not a heading in "
                            "the manuscript" % (key, host))
    return problems


def project(data, sections, order):
    """Current against projected words, by destination. Nothing here is declared."""
    rows, totals = [], {}
    for key in order:
        entry = data["sections"].get(key, {})
        dest = entry.get("dest", "UNCLASSIFIED")
        now = sections[key]["words"]
        after = entry.get("target_words", 0) if dest in ("MAIN", "BOTH") else 0
        rows.append((key, sections[key]["level"], dest, now, after))
        t = totals.setdefault(dest, [0, 0])
        t[0] += now
        t[1] += after
    return rows, totals


def body_only(rows):
    """Sections 1-9: what the journal's length guidance is about.

    Front matter, the availability statement and the reference list are excluded,
    because 'about 5,000 words' is guidance about the article's body and counting
    the reference list into it would make the figure mean nothing.
    """
    inside, now, after = False, 0, 0
    for key, _level, dest, n, a in rows:
        if re.match(r"^1\. ", key):
            inside = True
        if key in ("Code and Data Availability", "References"):
            inside = False
        if inside:
            now += n
            after += a
    return now, after


PAGE_HEADER = """# Main article, supplementary material, repository

*Generated by `python3 tools/check_split_map.py --write` from `tools/split_map.json`.
Do not edit this page: edit the map and regenerate, or the two will disagree and the
page will be the one that is wrong.*

The journal's guidance is that a full paper "should normally be about 5,000 words".
Sections 1–9 of this manuscript are **%(now)d**. This page is the plan for that, made
before any cutting, so that nothing is removed by whoever happens to be editing.

**Status: %(status)s**

**The rule this map is held to.** Scientific evidence is not hidden in the
supplementary material. Every unit that leaves the article states what the article
keeps, so the claim it supports is still made — and still checkable — in the paper a
reader gets. `tools/check_split_map.py` fails if any unit does not, and
`tools/preflight.py` runs it on every build.

| | Now | Projected in the article |
|---|---|---|
| Sections 1–9 | %(now)d words | **%(after)d words** |
| Against the 5,000-word guidance | %(now_x).2f× | %(after_x).2f× |

A reduction of %(cut)d words, %(pct).0f%%, with no reported number leaving the record.

"""


def markdown(data, sections, order, rows, totals):
    """The map as a page, rendered from the map -- never maintained alongside it."""
    now, after = body_only(rows)
    g = float(data["target"]["guidance_words"])
    out = [PAGE_HEADER % dict(
        now=now, after=after, now_x=now / g, after_x=after / g,
        cut=now - after, pct=100.0 * (now - after) / now,
        status={
            "planned": "PLANNED — nothing has been moved or cut yet",
            "moved": "MOVED — every supplementary unit is now in "
                     "`manuscript/SUPPLEMENTARY.md`, the two wide tables are reduced "
                     "in the article and complete there, and the article's tables are "
                     "renumbered 1–6. The sections that stay have **not** been "
                     "condensed yet.",
            "condensed": "CONDENSED — the sections that stay are at their targets",
        }.get(data.get("phase", "planned"), "unknown"))]

    out.append("## Leaving the article\n")
    out.append("| Unit | Goes to | Becomes | Why | What the article keeps |")
    out.append("|---|---|---|---|---|")
    for key, _l, dest, n, _a in rows:
        e = data["sections"][key]
        if dest in LEAVES_MAIN:
            out.append("| %s (%d words) | %s | — | %s | %s |"
                       % (key, n, dest, e["reason"], e.get("main_retains", "")))
    for num in sorted(data["tables"], key=lambda s: (len(s), s)):
        e = data["tables"][num]
        if not isinstance(e, dict) or e["dest"] == "MAIN":
            continue
        out.append("| Table %s. %s | %s | %s | %s | %s |"
                   % (num, e.get("caption", ""), e["dest"], e.get("becomes", "—"),
                      e["reason"], e.get("main_form") or e.get("main_retains", "")))
    for num in data["figures"]:
        e = data["figures"][num]
        if not isinstance(e, dict) or e["dest"] == "MAIN":
            continue
        out.append("| Figure %s (`%s`) | %s | %s | %s | %s |"
                   % (num, e.get("file"), e["dest"], e.get("becomes", "—"),
                      e["reason"], e.get("main_retains", "")))
    for key in data.get("fragments", {}):
        e = data["fragments"][key]
        if not isinstance(e, dict):
            continue
        out.append("| %s, inside %s | %s | — | %s | %s |"
                   % (key.replace("_", " "), e["host"], e["dest"], e["reason"],
                      e.get("main_retains", "")))

    out.append("\n## Staying in the article\n")
    out.append("| Section | Now | Target | Why it stays |")
    out.append("|---|---|---|---|")
    for key, level, dest, n, aft in rows:
        if dest not in ("MAIN", "BOTH"):
            continue
        e = data["sections"][key]
        out.append("| %s%s | %d | %d | %s |"
                   % ("　" * (level - 1), key, n, aft, e["reason"]))

    out.append("\n## If a further reduction is asked for\n")
    for line in data["target"]["tier_2_if_required"]:
        out.append(line)
    out.append("")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--long", action="store_true",
                    help="list every unit, not only the ones leaving the article")
    ap.add_argument("--write", action="store_true",
                    help="regenerate manuscript/SPLIT_MAP.md from the map")
    a = ap.parse_args(argv)

    data = load_map()
    sections, order, tables = units()
    figs = figures()
    problems = check(data, sections, order, tables, figs)
    rows, totals = project(data, sections, order)

    print("main article / supplementary / repository map")
    print("  %d heading(s), %d table(s), %d figure file(s) in the manuscript"
          % (len(order), len(tables), len(figs)))
    phase = data.get("phase", "planned")
    print("  phase: %s" % {
        "planned": "PLANNED -- nothing has been moved or cut yet",
        "moved": "MOVED -- the supplementary units are in SUPPLEMENTARY.md and the "
                 "wide tables are split; the sections that stay are NOT yet condensed",
        "condensed": "CONDENSED -- the sections that stay are at their targets",
    }.get(phase, phase))
    print("  the map is %s"
          % ("APPLIED: the manuscript is expected to be at or below its targets"
             if data.get("applied") else
             "NOT YET APPLIED: the targets below are targets, not measurements"))
    print("")

    moving = [(k, d, n) for k, _l, d, n, _a in rows if d in LEAVES_MAIN]
    print("leaving the main article:")
    for key, dest, now in moving:
        print("  %-14s %5d  %s" % (dest, now, key))
    for num, e in sorted(data["tables"].items()):
        if isinstance(e, dict) and e.get("dest") != "MAIN":
            print("  %-14s        Table %s -> %s" % (e["dest"], num,
                                                     e.get("becomes", "supplementary")))
    for num, e in sorted(data["figures"].items()):
        if isinstance(e, dict) and e.get("dest") != "MAIN":
            print("  %-14s        Figure %s (%s)" % (e["dest"], num, e.get("file")))
    print("")

    if a.long:
        print("every section:")
        for key, level, dest, now, after in rows:
            mark = "" if dest != "MAIN" else ("  (-%d)" % (now - after) if now > after
                                              else "")
            print("  %-14s %5d -> %-5s %s%s"
                  % (dest, now, after if dest in ("MAIN", "BOTH") else "-",
                     "  " * (level - 1) + key, mark))
        print("")

    print("words by destination, read from the manuscript:")
    for dest in sorted(totals):
        now, after = totals[dest]
        print("  %-14s now %6d   projected in article %6d" % (dest, now, after))
    now, after = body_only(rows)
    guidance = data["target"]["guidance_words"]
    print("")
    print("Sections 1-9, which is what the length guidance is about:")
    print("  now       %6d words  (%.2fx the guidance of %d)"
          % (now, now / float(guidance), guidance))
    print("  projected %6d words  (%.2fx)  -- a reduction of %d words, %.0f%%"
          % (after, after / float(guidance), now - after,
             100.0 * (now - after) / now))
    lo, hi = data["target"]["band"]
    print("  target band %d to %d: %s"
          % (lo, hi, "inside" if lo <= after <= hi else "OUTSIDE"))
    if not (lo <= after <= hi):
        problems.append("the projected body is %d words, outside the declared target "
                        "band of %d to %d; either the targets or the band is wrong"
                        % (after, lo, hi))

    page = markdown(data, sections, order, rows, totals)
    page_path = os.path.join(HERE, "manuscript", "SPLIT_MAP.md")
    if a.write:
        with open(page_path, "w") as fh:
            fh.write(page)
        print("")
        print("wrote manuscript/SPLIT_MAP.md")
    elif os.path.exists(page_path) and open(page_path).read() != page:
        problems.append("manuscript/SPLIT_MAP.md is not what the map renders; run "
                        "python3 tools/check_split_map.py --write")

    print("")
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        print("%d problem(s)" % len(problems))
    else:
        print("every unit is classified, every move declares what the article keeps, "
              "and nothing has been cut")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
