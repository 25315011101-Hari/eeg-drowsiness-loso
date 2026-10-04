"""Measure each figure against the journal's artwork requirements.

    python3 tools/check_print_ready.py

The requirements are not written here. They are quotations in
tools/journal_requirements.json under not_enforced_here.figure_resolution, taken from
the guide for authors on the date recorded there. This reads the files that exist and
compares them.

What it fails on:

  * a paper figure with no vector PDF. The PDF is what is submitted, and a missing
    one is the whole artwork requirement unmet;
  * a PDF that is not really vector -- one that merely wraps a bitmap, which is what
    happens when a figure is exported through a raster step by accident;
  * a PNG rendered at a dpi other than the one config.py declares. A figure whose
    resolution is not the declared resolution makes the declaration worthless;
  * a PNG below the guide's 300 dpi photograph minimum, which nothing here should be.

What it reports without failing: every figure's width against the 1000 dpi
line-drawing minimum of 3,543 pixels for a single column and 7,480 for a full page.
These figures are line drawings and the PNGs do not reach those widths. That is not a
defect while the submitted artwork is the PDF, because the raster minima are minima
for raster artwork and vector artwork is exempt -- but it is exactly the fact someone
will need at the moment a production editor asks for a TIFF, so it is printed on every
run rather than rediscovered then.

The one figure that is not a paper figure, the repository's own module diagram, is
excluded from the same declaration the split map uses.
"""

import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import config as C  # noqa: E402

FIGDIR = os.path.join(HERE, "figures")
REQUIREMENTS = os.path.join(HERE, "tools", "journal_requirements.json")
SPLIT_MAP = os.path.join(HERE, "tools", "split_map.json")

INCH_PER_METRE = 0.0254


def requirements():
    with open(REQUIREMENTS) as fh:
        data = json.load(fh)
    entry = data["not_enforced_here"]["figure_resolution"]
    return entry["value"], entry["quote"], data["verified"]["date"]


def paper_figures():
    with open(SPLIT_MAP) as fh:
        declared = json.load(fh)["figures"]
    figs, excluded = {}, set()
    for num, e in declared.items():
        if num.startswith("_") or not isinstance(e, dict):
            continue
        (excluded.add(e["file"]) if e.get("dest") == "REPOSITORY"
         else figs.__setitem__(num, e["file"]))
    return figs, excluded


def png_pixels_and_dpi(path):
    """Width, height and dpi from the PNG itself: IHDR for size, pHYs for density.

    Read here rather than through an imaging library because this check must be able
    to run in the bare environment that builds a snapshot, and because the question
    is about the bytes that will be sent to the journal rather than about what a
    library would reconstruct from them.
    """
    w = h = dpi = None
    with open(path, "rb") as fh:
        if fh.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("%s is not a PNG" % path)
        while True:
            head = fh.read(8)
            if len(head) < 8:
                break
            length, kind = struct.unpack(">I4s", head)
            body = fh.read(length)
            fh.read(4)                                   # the chunk's CRC
            if kind == b"IHDR":
                w, h = struct.unpack(">II", body[:8])
            elif kind == b"pHYs":
                px, py, unit = struct.unpack(">IIB", body[:9])
                if unit == 1:                            # pixels per metre
                    dpi = round(px * INCH_PER_METRE)
            elif kind == b"IDAT":
                break                                    # past every header chunk
    return w, h, dpi


def pdf_is_vector(path):
    """Does the PDF carry drawing operators, or only a pasted image?

    A matplotlib PDF is a stream of path and text operators. A PDF produced by
    wrapping a bitmap has an /Image XObject and essentially no path operators, and it
    satisfies no artwork requirement that a PNG would not. The test is therefore for
    the presence of drawing, not for the absence of images: a legitimate figure may
    contain both.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    text = b""
    for m in re.finditer(rb"stream\r?\n", raw):
        chunk = raw[m.end():m.end() + 200000]
        end = chunk.find(b"endstream")
        try:
            text += zlib.decompress(chunk[:end if end > 0 else None])
        except zlib.error:
            text += chunk[:end if end > 0 else None]
        if len(text) > 400000:
            break
    # 'm' moveto and 'l' lineto or 'c' curveto as whole tokens: the marks of drawing.
    strokes = len(re.findall(rb"(?:^|\s)[0-9.]+ [0-9.]+ m(?:\s|$)", text))
    return strokes, b"/Subtype /Image" in raw or b"/Subtype/Image" in raw


def main():
    spec, quotes, verified = requirements()
    figs, excluded = paper_figures()
    problems, notes = [], []

    print("artwork against the guide for authors, read at the source on %s" % verified)
    for q in (quotes if isinstance(quotes, list) else [quotes]):
        print("  %s" % q)
    print("  submitted artwork is the PDF; the PNG is for reading. "
          "config.FIGURE_DPI_RASTER = %d" % C.FIGURE_DPI_RASTER)
    print("")
    print("  %-4s %-38s %11s %6s %9s %s"
          % ("Fig", "file", "PNG px", "dpi", "PDF", "single-column line-art minimum"))

    for num, stem in sorted(figs.items(), key=lambda kv: (kv[0].startswith("S"), kv[0])):
        png = os.path.join(FIGDIR, stem + ".png")
        pdf = os.path.join(FIGDIR, stem + ".pdf")
        if not os.path.exists(png):
            problems.append("Figure %s has no PNG" % num)
            continue
        w, h, dpi = png_pixels_and_dpi(png)

        if not os.path.exists(pdf):
            problems.append("Figure %s has no vector PDF, which is the file that is "
                            "submitted" % num)
            verdict = "MISSING"
        else:
            strokes, has_image = pdf_is_vector(pdf)
            if strokes < 20:
                problems.append("Figure %s's PDF carries %d drawing operator(s); it "
                                "looks like a bitmap in a PDF wrapper, which meets no "
                                "artwork requirement a PNG would not"
                                % (num, strokes))
                verdict = "RASTER?"
            else:
                verdict = "vector"

        if dpi is None:
            problems.append("Figure %s's PNG records no pixel density, so its "
                            "resolution cannot be verified from the file" % num)
        elif abs(dpi - C.FIGURE_DPI_RASTER) > 1:
            problems.append("Figure %s's PNG is %d dpi and config declares %d; a "
                            "declared resolution that is not the rendered one is worse "
                            "than none" % (num, dpi, C.FIGURE_DPI_RASTER))
        if dpi is not None and dpi < spec["photograph_dpi"]:
            problems.append("Figure %s's PNG is %d dpi, below the guide's %d dpi "
                            "minimum for any raster artwork"
                            % (num, dpi, spec["photograph_dpi"]))

        need = spec["line_art_px_single_column"]
        short = need - w
        print("  %-4s %-38s %5d x%5d %6s %9s %s"
              % (num, stem, w, h, dpi if dpi else "?", verdict,
                 "meets %d px" % need if short <= 0
                 else "%d px short of %d" % (short, need)))
        if short > 0:
            notes.append("Figure %s: the PNG is %d px wide against the %d px "
                         "line-drawing minimum. The submitted PDF is vector, so the "
                         "minimum does not apply to it; %d dpi at this printed width "
                         "would be needed if a raster file were ever asked for."
                         % (num, w, need, int(round(need / (w / float(dpi or 1))))))

    for stem in sorted(excluded):
        print("  %-4s %-38s %s" % ("--", stem, "not a paper figure"))

    if notes:
        print("")
        print("reported, not failed -- the raster minima apply to raster artwork:")
        for n in notes:
            print("  " + n)

    print("")
    for p in problems:
        print("PROBLEM:", p)
    print("%d problem(s)" % len(problems) if problems
          else "every paper figure has a vector PDF at the declared raster resolution")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
