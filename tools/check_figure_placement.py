"""Check that every figure is actually placed where it is needed.

    python3 tools/check_figure_placement.py

Until 30 September 2026 this repository drew seven figures, numbered them in order of
first citation, listed where each belonged in a table on the status page, wrote a
caption for each one at that point in the text -- and embedded none of them. The
assembled manuscript contained zero images. Every statement about where the figures
go was true, and a reader of the manuscript saw no figure at all.

That is why this check reads the images and not the sentences about them. For each
paper figure it requires:

  1. exactly one embed, across the section sources, of the form
     ![alt](../figures/<stem>.png)  -- one embed, so a figure cannot be silently
     shown twice at two different points in the argument;
  2. the embed's file exists;
  3. the caption ">  **Figure N. ...**" is the next non-blank line after it, so the
     picture and the words that explain it cannot drift apart;
  4. every caption has an embed, and every embed has a caption;
  5. the figure appears in the section its first prose citation is in, because
     "Figure 4" written in Section 7.5 and drawn in Section 8 is a figure the reader
     does not have when the sentence needs it.

`fig6_code_structure` is not a paper figure -- it documents this repository's own
module layout and lives in the README -- so it is excluded by name, from the same
declaration the split map uses.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import build_manuscript as bm  # noqa: E402

EMBED = re.compile(r"^!\[(?P<alt>[^\]]*)\]\(\.\./figures/(?P<stem>[^)]+)\.png\)$")
CAPTION = re.compile(r"^> \*\*Figure (?P<num>S?\d+)\.\s")
CITATION = re.compile(r"\*\*Figure (S?\d+)\*\*|(?<!\*)\bFigure (S?\d+)\b")
HEADING = re.compile(r"^#{1,3} +(.*?)\s*$")


def paper_figures():
    """The figures the paper has, and the one file that is not one of them."""
    with open(os.path.join(HERE, "tools", "split_map.json")) as fh:
        declared = json.load(fh)["figures"]
    figs, excluded = {}, {}
    for num, entry in declared.items():
        if num.startswith("_") or not isinstance(entry, dict):
            continue
        if entry.get("dest") == "REPOSITORY":
            excluded[entry["file"]] = entry["reason"]
        else:
            figs[num] = entry["file"]
    return figs, excluded


SUPPLEMENT_FILE = "SUPPLEMENTARY.md"


def figure_destinations():
    """Where the split map says each paper figure belongs: MAIN or SUPPLEMENTARY.

    Until 1 October 2026 this script read only the article's section sources, so a
    figure the split map sent to the supplement still had to be embedded in the
    article to pass. Figure S1 was therefore numbered as supplementary, described in
    the text as being "in the supplementary material", and drawn in Section 7 -- and
    the check reported no problem. A destination that nothing verifies is a comment.
    """
    with open(os.path.join(HERE, "tools", "split_map.json")) as fh:
        declared = json.load(fh)["figures"]
    return {num: entry.get("dest", "MAIN")
            for num, entry in declared.items()
            if not num.startswith("_") and isinstance(entry, dict)
            and entry.get("dest") != "REPOSITORY"}


def read_sections(names=None):
    """Each named source, as lines, in the order the builder assembles them."""
    for name in (bm.SECTION_FILES if names is None else names):
        path = os.path.join(HERE, "manuscript", name)
        if os.path.exists(path):
            yield name, open(path).read().splitlines()


def survey(names=None):
    """Where every embed, caption and citation is, by source file and heading."""
    embeds, captions, cites = {}, {}, {}
    for name, lines in read_sections(names):
        head = ""
        for i, line in enumerate(lines):
            h = HEADING.match(line)
            if h:
                head = h.group(1)
            m = EMBED.match(line.strip())
            if m:
                nxt = next((l for l in lines[i + 1:] if l.strip()), "")
                c = CAPTION.match(nxt.strip())
                embeds.setdefault(m.group("stem"), []).append(
                    dict(file=name, line=i + 1, head=head, alt=m.group("alt"),
                         caption_follows=c.group("num") if c else None))
                continue
            c = CAPTION.match(line.strip())
            if c:
                captions.setdefault(c.group("num"), []).append(
                    dict(file=name, line=i + 1, head=head))
                continue
            for a, b in CITATION.findall(line):
                cites.setdefault(a or b, []).append(dict(file=name, head=head))
    return embeds, captions, cites


def order_of(embeds, stem):
    """Where a figure sits in the assembled paper: (section index, line number).

    The section index comes from the builder's own order, so this is the order a
    reader meets the figures in and not the order the source files happen to sit in
    on disk.
    """
    place = embeds[stem][0]
    return (bm.SECTION_FILES.index(place["file"])
            if place["file"] in bm.SECTION_FILES else 99, place["line"])


def main():
    figs, excluded = paper_figures()
    dest = figure_destinations()
    article = survey()                        # the article's own section sources
    supplement = survey([SUPPLEMENT_FILE])    # the supplementary document
    embeds, captions, cites = article
    s_embeds, s_captions, _s_cites = supplement
    problems = []

    # A figure is checked where its destination says it lives, and is required to be
    # absent from the other document. Both directions matter: a supplementary figure
    # drawn in the article is an S-numbered figure in the submitted paper, and a main
    # figure drawn in the supplement is a figure the reader never reaches.
    for num, stem in sorted(figs.items(), key=lambda kv: (kv[0].startswith("S"), kv[0])):
        if dest.get(num) == "SUPPLEMENTARY":
            if stem in embeds:
                problems.append(
                    "Figure %s is supplementary in the split map and is drawn in the "
                    "article at %s:%d; the submitted article would carry an S-numbered "
                    "figure" % (num, embeds[stem][0]["file"], embeds[stem][0]["line"]))
            if stem not in s_embeds:
                problems.append(
                    "Figure %s is supplementary in the split map and is drawn nowhere "
                    "in %s; the supplementary document would not contain the figure "
                    "the article sends the reader to" % (num, SUPPLEMENT_FILE))
            elif len(s_embeds[stem]) > 1:
                problems.append("Figure %s is placed %d times in %s"
                                % (num, len(s_embeds[stem]), SUPPLEMENT_FILE))
            if stem in s_embeds and s_embeds[stem][0]["caption_follows"] != num:
                problems.append("%s places Figure %s and the next non-blank line is not "
                                "its caption" % (SUPPLEMENT_FILE, num))
            if num not in s_captions:
                problems.append("Figure %s has no caption in %s" % (num, SUPPLEMENT_FILE))
            # The article must still send the reader there, or the supplement carries a
            # figure nothing cites.
            if num not in cites:
                problems.append("Figure %s is in the supplement and the article never "
                                "cites it" % num)
        elif stem in s_embeds:
            problems.append("Figure %s belongs in the article and is drawn in %s"
                            % (num, SUPPLEMENT_FILE))

    for num, stem in sorted(figs.items(), key=lambda kv: (kv[0].startswith("S"), kv[0])):
        if dest.get(num) == "SUPPLEMENTARY":
            continue
        here = embeds.get(stem, [])
        if not here:
            problems.append("Figure %s (%s) is never placed: no ![](../figures/%s.png) "
                            "in any section source" % (num, stem, stem))
        elif len(here) > 1:
            problems.append("Figure %s is placed %d times, at %s; a figure belongs at "
                            "one point in the argument"
                            % (num, len(here),
                               ", ".join("%s:%d" % (e["file"], e["line"]) for e in here)))
        for e in here:
            if not os.path.exists(os.path.join(HERE, "figures", stem + ".png")):
                problems.append("%s:%d places figures/%s.png, which does not exist"
                                % (e["file"], e["line"], stem))
            if e["caption_follows"] != num:
                problems.append("%s:%d places Figure %s and the next non-blank line is "
                                "%s; the picture and its caption have come apart"
                                % (e["file"], e["line"], num,
                                   "Figure %s's caption" % e["caption_follows"]
                                   if e["caption_follows"] else "not a figure caption"))
        cap = captions.get(num, [])
        if not cap:
            problems.append("Figure %s has no caption" % num)
        elif len(cap) > 1:
            problems.append("Figure %s has %d captions, at %s"
                            % (num, len(cap),
                               ", ".join("%s:%d" % (c["file"], c["line"]) for c in cap)))

        # Placed where it is needed: in the section that first cites it.
        first = cites.get(num, [{}])[0].get("head")
        if here and first and here[0]["head"] != first:
            problems.append("Figure %s is first cited in %r and drawn in %r; it is not "
                            "where the reader needs it"
                            % (num, first, here[0]["head"]))

    # Numbered in the order they appear. Until 30 September 2026 the architecture
    # drawing was Figure 6 and sat in Section 5.3, so the first figure a reader met
    # was numbered last -- true of every statement about it, and wrong on the page.
    # A number out of appearance order is a production query at best, so it is now a
    # failure rather than a thing to notice. Supplementary figures are numbered in
    # their own S-sequence and are checked separately for the same property.
    for label, wanted, where in (
            ("", [n for n in figs if dest.get(n) != "SUPPLEMENTARY"], embeds),
            ("supplementary ", [n for n in figs if dest.get(n) == "SUPPLEMENTARY"],
             s_embeds)):
        appearing = []
        for n in wanted:
            places = where.get(figs[n])
            if not places:
                continue
            at = (order_of(embeds, figs[n]) if where is embeds
                  else (0, places[0]["line"]))
            appearing.append((at, n))
        appearing.sort()
        seen = [int(n.lstrip("S")) for _pos, n in appearing]
        if seen != sorted(seen):
            problems.append(
                "the %sfigures appear in the order %s, so they are not numbered in "
                "order of appearance; renumber with tools/renumber_figures.py rather "
                "than by hand"
                % (label, ", ".join("Figure %s" % n for _p, n in appearing)))

    for stem, places in embeds.items():
        if stem in excluded:
            problems.append("figures/%s.png is placed in the paper at %s, and the split "
                            "map says it is not a paper figure: %s"
                            % (stem, places[0]["file"], excluded[stem]))
        elif stem not in figs.values():
            problems.append("figures/%s.png is placed in the paper and is in no "
                            "figure list" % stem)

    for num in list(captions) + list(s_captions):
        if num not in figs:
            problems.append("a caption exists for Figure %s, which is in no figure list"
                            % num)

    print("figure placement")
    for num, stem in sorted(figs.items(), key=lambda kv: (kv[0].startswith("S"), kv[0])):
        where = s_embeds if dest.get(num) == "SUPPLEMENTARY" else embeds
        e = where.get(stem, [{}])[0]
        print("  Figure %-3s %-38s %-12s %s%s"
              % (num, stem, dest.get(num, "MAIN"),
                 "%s:%s" % (e.get("file", "NOT PLACED"), e.get("line", "-")),
                 "  in %r" % e["head"] if e.get("head") else ""))
    for stem, reason in excluded.items():
        print("  (not a paper figure: %s)" % stem)
    print("")
    for p in problems:
        print("PROBLEM:", p)
    print("%d problem(s)" % len(problems) if problems
          else "every figure is placed once, beside its caption, in the document its "
               "destination names, and the article's figures sit in the section that "
               "first cites each")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
