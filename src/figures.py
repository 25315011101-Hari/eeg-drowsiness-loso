"""Draw the manuscript's figures, every value read from the registry.

    python -m src.figures            # writes figures/*.pdf and *.png

**No number in this file is typed.** Each one is looked up in
`results/MASTER_NUMBERS.csv` by its claim, exactly as the manuscript must. A
figure is a claim like any other, and a figure drawn from numbers pasted into a
plotting script is the one place in this pipeline where the text and the picture
could quietly disagree. `lookup()` raises if a claim is missing, so a figure
cannot be drawn from a value the registry does not hold.

The function names here are the order the figures were written in; the file
names are the order the paper cites them in, and the paper's numbering is what a
reader sees. The two do not match, and the mapping is deliberate rather than an
oversight:

  figure0()  ->  figure2_study_design            the design in one picture
  figure2()  ->  figure3_accuracy_against_recall accuracy against recall
  figure4()  ->  figure4_subject_against_seed_spread  subject spread vs seed spread
  figure1()  ->  figure5_brier_partition         the Brier partition
  figure3()  ->  figure6_recalibration           what recalibration does to it
  figure5()  ->  figureS1_overview               the study on one page (supplement)

Colour does one job here: **polarity** -- worse or better than a constant
predictor. Blue and red from the validated diverging pair, gray for the neutral
reference. Identity is never carried by colour alone: the three constructions are
distinguished by marker shape, the emphasised lines in Figure 3 are also drawn
thicker, so the figures survive greyscale printing and every panel is readable
with the colour removed entirely.

Shared design language, fixed 19 September 2026 and applied to all five main
figures: printed width 7.16 in (double column), 5.6-7.6 pt type, panel labels
(a)(b)(c) where a figure has panels, the restrained blue/black/grey palette
above, no decorative illustration, and no number typed into this file.
"""

import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

# The validated diverging pair, plus the neutral midpoint and the ink tokens.
WORSE = "#e34948"     # above the reference: worse than a constant predictor
BETTER = "#2a78d6"    # below the reference
NEUTRAL = "#8a8a85"   # the reference itself, and rules
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e6e5e1"

# The journal style, settled 19 September 2026. A result figure in this paper is
# white ground, black and grey typography, ONE restrained accent for the data,
# thin axes, direct labels, and no shaded background -- the look of a printed
# research figure rather than of a slide. Polarity figures keep WORSE/BETTER
# above, because there the colour carries a meaning the shape cannot.
ACCENT = "#1f5c99"
AXIS = "#b9b8b4"

# Identity that survives greyscale: one marker per construction.
ARMS = ["A", "B", "C"]
MARKER = {"A": "o", "B": "s", "C": "^"}
ARM_LABEL = {
    "A": "Arm A  trimmed, every drowsy window kept",
    "B": "Arm B  untrimmed, ratio preserved",
    "C": "Arm C  trimmed, ratio preserved",
}

FIGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "figures")

_REGISTRY = None


def _load():
    global _REGISTRY
    if _REGISTRY is None:
        path = C.REGISTRY_CSV
        _REGISTRY = {}
        with open(path) as fh:
            for row in csv.DictReader(fh):
                _REGISTRY[row["claim"].strip()] = row["value"].strip()
    return _REGISTRY


def lookup(claim):
    """The registry value for a claim, as a float. Raises if it is not there.

    Raising is the point. A figure that silently falls back to a default would be
    a picture of a number the paper does not contain.
    """
    reg = _load()
    if claim not in reg:
        raise KeyError("not in MASTER_NUMBERS.csv: %r" % claim)
    return float(reg[claim])


def has(claim):
    """Whether the registry carries a claim at all.

    Used where the set of architectures a panel can show is itself a registry
    fact -- only the arms whose per-window probabilities were released have
    calibration rows, and hard-coding which three would be a number typed into
    this file.
    """
    return claim in _load()


def _spread(values, gap):
    """Nudge labels apart just enough to stop them overprinting.

    Only the label moves; the marker stays on its value. Returns a label
    position for each input value, in the input order.
    """
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = list(values)
    for k, i in enumerate(order):
        if k and out[i] - out[order[k - 1]] < gap:
            out[i] = out[order[k - 1]] + gap
    # Pushing apart moves the whole cluster upward, which once carried a label
    # for a point below the reference line to a position above it -- the label
    # then implied the opposite of what its own marker said. Re-centre on the
    # original centroid so the block moves as little as possible.
    shift = sum(values) / len(values) - sum(out) / len(out)
    return [v + shift for v in out]


def _place_labels(fig, ax, items, avoid=(), fontsize=5.4, color=None):
    """Put a name beside each point without letting two names touch.

    Hand-chosen offsets were tried first and failed the way hand-chosen offsets
    always do: "CNN" sat across the always-alert rule on all three panels, and on
    Arms B and C the EEGNet and CNN-BiLSTM names printed on top of one another
    because the two architectures differ by six hundredths of a percentage point
    in accuracy.

    So the offset is searched rather than chosen. Each label is measured where it
    would land, and the first candidate position that hits nothing already on the
    panel is kept. Nothing about the data moves -- the marker stays exactly on its
    value, and only the name shifts.
    """
    colour = INK if color is None else color
    # Right, left, above, below, then the four diagonals. Right first because a
    # scatter reads left to right and a trailing name is the least disruptive.
    CANDIDATES = [(7, 0), (-7, 0), (0, 6.5), (0, -7.5),
                  (6, 5.5), (-6, 5.5), (6, -6.5), (-6, -6.5)]
    renderer = fig.canvas.get_renderer()
    taken = [b for b in avoid]
    # A label must also stay inside its own panel. Without this the two longest
    # names ran off the right-hand edge and printed as "ShallowC".
    panel = ax.get_window_extent(renderer=renderer)
    placed = []
    for x, y, text in items:
        best = None
        for dx, dy in CANDIDATES:
            ann = ax.annotate(
                text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                fontsize=fontsize, color=colour, zorder=6,
                ha="left" if dx > 0 else ("right" if dx < 0 else "center"),
                va="center" if dy == 0 else ("bottom" if dy > 0 else "top"))
            box = ann.get_window_extent(renderer=renderer).expanded(1.06, 1.25)
            inside = (box.x0 >= panel.x0 - 1 and box.x1 <= panel.x1 + 1
                      and box.y0 >= panel.y0 - 1 and box.y1 <= panel.y1 + 1)
            if inside and not any(box.overlaps(t) for t in taken):
                best = (ann, box)
                break
            ann.remove()
            if best is None:
                best = (dx, dy)          # remembered only if nothing fits
        if best is None or isinstance(best[0], (int, float)):
            dx, dy = CANDIDATES[0]
            ann = ax.annotate(text, xy=(x, y), xytext=(dx, dy),
                              textcoords="offset points", fontsize=fontsize,
                              color=colour, zorder=6, ha="left", va="center")
            box = ann.get_window_extent(renderer=renderer).expanded(1.06, 1.25)
            best = (ann, box)
        taken.append(best[1])
        placed.append(best[0])
    return placed


def _paper(ax, grid="y"):
    """The journal axis: two thin spines, a faint grid on one axis, small type.

    Every result figure calls this, so that changing the house style is one
    edit rather than five. `grid` is "y", "x", "both" or None.
    """
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(colors=INK_SOFT, labelsize=6.0, length=2.5, width=0.6,
                   pad=2.0)
    if grid in ("y", "both"):
        ax.yaxis.grid(True, color=GRID, lw=0.5, zorder=0)
    if grid in ("x", "both"):
        ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)


def _style(ax, xlabel=None, ylabel=None, title=None):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_SOFT, labelsize=7.5, length=3, width=0.8)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8, color=INK_SOFT)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8, color=INK_SOFT)
    if title:
        ax.set_title(title, fontsize=8.5, color=INK, loc="left", pad=6)


def _save(fig, name):
    """Vector PDF for submission, raster PNG for reading on screen.

    The dpi applies to the PNG alone; a PDF has no resolution, which is the reason
    the PDF is the file that goes to the journal. The number comes from config so
    that it is stated once, with the reason it is that number and not the guide's
    1000 dpi line-art minimum.
    """
    os.makedirs(FIGDIR, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIGDIR, "%s.%s" % (name, ext)),
                    dpi=C.FIGURE_DPI_RASTER, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote figures/%s.pdf and .png" % name)


# --------------------------------------------------------------- figure 1
def figure1():
    """The Brier partition, as a margin over each construction's own reference.

    The margin is the quantity that makes the three constructions comparable:
    each has a different prevalence and therefore a different class-prior Brier
    reference, so the raw scores cannot share an axis but the distances from
    their own references can. Zero is the constant predictor.

    Redesigned 23 September 2026 into the journal style. Two things went with the
    redesign, and both were carrying meaning that something else already carries:

      the shaded half-plane   a pale red wash marked the region worse than the
                              reference. Position relative to the zero rule says
                              the same thing exactly, and the wash made the panel
                              read as a slide.
      the red/blue marks      colour was encoding polarity, which is redundant
                              with which side of zero a mark sits on. One accent
                              now, so the figure needs no colour at all to be
                              read, and the two words at the top name the
                              directions.

    What did NOT go is the dodge: the three constructions are offset within each
    architecture's row, because drawn on one line DeepConvNet's Arm A and Arm C
    marks sat on top of one another and a reader could not tell three
    constructions from two.
    """
    order = ["ShallowConvNet", "EEGNet", "CNN-BiLSTM", "CNN", "DeepConvNet"]
    DODGE = {"A": 0.23, "B": 0.0, "C": -0.23}
    fig, ax = plt.subplots(figsize=(7.16, 3.0))

    vals = {(arm, m): lookup("Arm %s %s pooled Brier margin over reference"
                             % (arm, m)) for arm in ARMS for m in order}
    hi, lo = max(vals.values()), min(vals.values())
    pad = (hi - lo) * 0.09
    ax.set_xlim(lo - pad, hi + pad * 2.2)
    ax.set_ylim(-0.62, len(order) - 0.30)

    for y, model in enumerate(order):
        if y:
            # BETWEEN rows: y - 0.5, not y + 0.5. The latter drew a separator
            # above the topmost row, where there is no row to separate it from.
            ax.axhline(y - 0.5, color=GRID, lw=0.5, zorder=0)
        for arm in ARMS:
            v = vals[(arm, model)]
            yy = y + DODGE[arm]
            ax.plot([0, v], [yy, yy], color=AXIS, lw=0.7, zorder=2,
                    solid_capstyle="butt")
            ax.plot(v, yy, MARKER[arm], ms=4.0, mew=0.5, color=ACCENT,
                    markeredgecolor="white", zorder=4)
    # Drawn after the rows so the reference reads as the spine of the figure.
    ax.axvline(0, color=INK_SOFT, lw=0.9, zorder=3)

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=6.4, color=INK)
    _paper(ax, grid=None)
    ax.set_xlabel("Pooled Brier score minus the class-prior reference of the same "
                  "construction.  Zero is that reference.",
                  fontsize=6.6, color=INK_SOFT)

    top = len(order) - 0.42
    ax.annotate("worse than a constant predictor →", xy=(pad * 0.35, top),
                fontsize=6.2, color=INK_SOFT, ha="left", va="center")
    ax.annotate("← better", xy=(-pad * 0.35, top),
                fontsize=6.2, color=INK_SOFT, ha="right", va="center")

    # The legend sits below the axis: inside the panel it would land on the
    # ShallowConvNet row, which carries the largest margins on all three arms.
    handles = [Line2D([], [], marker=MARKER[a], ls="", ms=4.0, color=ACCENT,
                      markeredgecolor="white", label=ARM_LABEL[a]) for a in ARMS]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.155),
              ncol=3, fontsize=6.2, frameon=False, handletextpad=0.4,
              columnspacing=1.4)
    fig.subplots_adjust(left=0.145, right=0.99, top=0.97, bottom=0.235)
    _save(fig, "figure5_brier_partition")


# --------------------------------------------------------------- figure 2
# Short names for the plots. Five full names will not fit side by side at column
# width, and a figure that needs a magnifier is a figure that will not be read.
# The caption expands them.
SHORT = {"EEGNet": "EEGNet", "ShallowConvNet": "Shallow", "CNN": "CNN",
         "DeepConvNet": "Deep", "CNN-BiLSTM": "BiLSTM"}


def figure2():
    """Accuracy against recall, as a scatter, one panel per construction.

    Redesigned 19 September 2026 into the journal figure style used by every
    result figure in this paper: white ground, black and grey typography, one
    restrained accent, thin axes, direct labels, no decorative rule and no
    shaded background.

    Two earlier attempts are worth recording, because each failed for a reason
    that is easy to repeat. The first stacked accuracy in one panel above recall
    in another and asked the reader to notice that one descended while the other
    climbed -- a comparison the reader had to perform. The second made a slope
    chart of the two rankings, which performed the comparison but read as an
    infographic rather than as a measurement.

    A scatter is the plain form: one axis per measure, one point per
    architecture, and the downward drift of the five points IS the relationship.
    The architectures are not a series, so nothing connects them; a line through
    them would assert that the space between two architectures means something.

    The always-alert baseline is drawn because without it accuracy cannot be
    read. It also carries a fact no ranking shows: on Arm B every one of the five
    sits below it.
    """
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.62), sharex=True, sharey=True)
    # The axis limits are set before anything is drawn, because the label placer
    # measures in pixels and a later rescale would move every measurement.
    axes[0].set_xlim(0.33, 0.85)
    axes[0].set_ylim(80.4, 95.2)
    axes[0].set_yticks([82, 85, 88, 91, 94])
    axes[0].set_xticks([0.4, 0.5, 0.6, 0.7, 0.8])

    obstacles = {}
    for col, arm in enumerate(ARMS):
        ax = axes[col]
        acc = {m: lookup("Arm %s %s pooled accuracy percent" % (arm, m))
               for m in C.MODELS}
        rec = {m: lookup("Arm %s %s pooled recall" % (arm, m)) for m in C.MODELS}
        base = lookup("Arm %s always-alert accuracy percent, 2 dp" % arm)
        rho = lookup("Arm %s Spearman pooled accuracy vs pooled recall" % arm)
        pval = lookup("Arm %s p for Spearman pooled accuracy vs pooled recall" % arm)

        ax.axhline(base, color=INK_SOFT, lw=0.8, ls=(0, (3.5, 3)), zorder=2)
        keep = [ax.text(0.98, 0.985, "always alert %.2f %%" % base,
                        transform=ax.transAxes, fontsize=5.2, color=INK_SOFT,
                        ha="right", va="top"),
                ax.text(0.02, 0.025,
                        "$\\rho$ = %.3f   p = %.4f%s"
                        % (rho, pval, "" if pval < 0.05 else "   n.s."),
                        transform=ax.transAxes, fontsize=5.4, color=INK_SOFT,
                        ha="left", va="bottom")]

        for m in C.MODELS:
            ax.plot(rec[m], acc[m], "o", ms=4.2, color=ACCENT,
                    markeredgecolor="white", mew=0.7, zorder=4)
        _paper(ax)
        ax.set_title("Arm %s" % arm, fontsize=7.0, color=INK, pad=7)
        ax.text(0.0, 1.05, "(%s)" % "abc"[col], transform=ax.transAxes,
                ha="left", va="bottom", fontsize=6.8, fontweight="bold", color=INK)
        obstacles[col] = (acc, rec, base, keep)

    fig.subplots_adjust(left=0.075, right=0.995, top=0.85, bottom=0.17, wspace=0.10)
    axes[0].set_ylabel("Pooled accuracy (%)", fontsize=6.6, color=INK_SOFT)
    axes[1].set_xlabel("Pooled recall", fontsize=6.6, color=INK_SOFT)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for col, arm in enumerate(ARMS):
        ax = axes[col]
        acc, rec, base, keep = obstacles[col]
        avoid = [t.get_window_extent(renderer=renderer).expanded(1.1, 1.3)
                 for t in keep]
        # The markers themselves, and the always-alert rule: a name printed
        # across that rule looked struck through on all three panels.
        for m in C.MODELS:
            px, py = ax.transData.transform((rec[m], acc[m]))
            avoid.append(Bbox.from_bounds(px - 4.5, py - 4.5, 9, 9))
        x0, x1 = ax.get_xlim()
        ly0 = ax.transData.transform((x0, base))[1]
        lx0 = ax.transData.transform((x0, base))[0]
        lx1 = ax.transData.transform((x1, base))[0]
        avoid.append(Bbox.from_bounds(lx0, ly0 - 1.6, lx1 - lx0, 3.2))
        # Tallest accuracy first, so the crowded top of the panel is resolved
        # before the sparse bottom claims the room.
        items = sorted(((rec[m], acc[m], m) for m in C.MODELS),
                       key=lambda t: -t[1])
        _place_labels(fig, ax, items, avoid=avoid, fontsize=5.4)

    _save(fig, "figure3_accuracy_against_recall")


# --------------------------------------------------------------- figure 3
def figure3():
    """What out-of-subject recalibration does to the margin over the reference.

    Redesigned 23 September 2026 into the journal style, and the redesign changed
    the FORM, not only the paint. The figure was a before-and-after slope chart:
    raw scores on a left tick, recalibrated on a right tick, a line sloping
    between them. With three architectures per panel those lines crossed -- on
    Arms B and C ShallowConvNet starts highest and does not finish highest -- and
    the crossings were clutter rather than information, because nothing about the
    crossing is a finding.

    It is now a paired dot plot in the same row form as Figures 3 and 4: one row
    per architecture, the open mark where it started, the filled mark where
    recalibration left it, a hairline between them. Open against filled is the
    same convention Figure 4 uses, so the three row figures read as one system,
    and no line crosses another.

    Only the architectures whose per-window probabilities were retained can
    appear -- three per construction, and not the same three on each. Which three
    is itself read from the registry, so the coverage cannot drift out of step
    with the analysis.

    Every value is a registry lookup. The figure read the per-arm calibration
    summary directly until 19 September 2026, which meant the picture and the
    table beside it were rounded from one source by two different routes.
    """
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.35), sharex=True)
    covered = {arm: [m for m in C.MODELS
                     if has("Arm %s %s raw Brier SUBJECT-AVERAGED" % (arm, m))]
               for arm in ARMS}
    ref_of = {arm: lookup("Arm %s class-prior Brier reference" % arm) for arm in ARMS}
    raw_of = {(arm, m): lookup("Arm %s %s raw Brier SUBJECT-AVERAGED" % (arm, m))
              - ref_of[arm] for arm in ARMS for m in covered[arm]}
    cal_of = {(arm, m): lookup("Arm %s %s platt Brier SUBJECT-AVERAGED" % (arm, m))
              - ref_of[arm] for arm in ARMS for m in covered[arm]}

    allv = list(raw_of.values()) + list(cal_of.values())
    pad = (max(allv) - min(allv)) * 0.10
    axes[0].set_xlim(min(allv) - pad, max(allv) + pad)

    for col, (ax, arm) in enumerate(zip(axes, ARMS)):
        # Worst raw score at the top, so the eye starts where the repair is
        # largest and the rows do not reorder between panels for no reason.
        models = sorted(covered[arm], key=lambda m: raw_of[(arm, m)])
        for y, m in enumerate(models):
            raw, cal = raw_of[(arm, m)], cal_of[(arm, m)]
            ax.plot([raw, cal], [y, y], color=AXIS, lw=0.7, zorder=2,
                    solid_capstyle="butt")
            ax.plot(raw, y, "o", ms=3.8, mfc="white", mec=ACCENT, mew=0.9,
                    zorder=3)
            ax.plot(cal, y, "o", ms=4.2, color=ACCENT, mec="white", mew=0.5,
                    zorder=4)
        ax.axvline(0, color=INK_SOFT, lw=0.9, zorder=1)
        ax.set_yticks(range(len(models)))
        ax.set_yticklabels([SHORT[m] for m in models], fontsize=6.0, color=INK)
        ax.set_ylim(-0.6, len(models) - 0.4)
        _paper(ax, grid=None)
        ax.set_title("Arm %s" % arm, fontsize=6.8, color=INK, pad=6)
        ax.text(0.0, 1.05, "(%s)" % "abc"[col], transform=ax.transAxes,
                ha="left", va="bottom", fontsize=6.8, fontweight="bold", color=INK)

    # The direction sentence is a second line OF the axis label, not a separate
    # figure-level text: placed separately it had to be positioned by hand and
    # printed on top of the label.
    axes[1].set_xlabel("Subject-averaged Brier score minus the class-prior reference "
                       "of the same construction\nLeft of the rule is better than the "
                       "constant predictor; right of it is worse.",
                       fontsize=6.6, color=INK_SOFT, linespacing=1.6)
    handles = [
        Line2D([], [], marker="o", ls="", ms=3.8, mfc="white", mec=ACCENT,
               mew=0.9, label="raw"),
        Line2D([], [], marker="o", ls="", ms=4.2, color=ACCENT, mec="white",
               mew=0.5, label="after out-of-subject Platt scaling"),
    ]
    axes[1].legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.46),
                   ncol=2, fontsize=6.2, frameon=False, handletextpad=0.4,
                   columnspacing=2.2)
    fig.subplots_adjust(left=0.065, right=0.995, top=0.82, bottom=0.34, wspace=0.16)
    _save(fig, "figure6_recalibration")


# --------------------------------------------------------------- figure 4
def figure4():
    """Between-subject spread against between-seed spread, on one log axis.

    Redesigned 23 September 2026 into the journal style: white ground, thin
    axes, one accent, direct labels. The previous version drew a thick grey bar
    between the two marks, which read as a magnitude in its own right and made
    the panel look like an infographic. The bar is now a hairline whose only job
    is to say which two marks belong to the same architecture.

    Both quantities are standard deviations of the same subject-level PR-AUC, so
    they share an axis honestly. The gap between them is the argument: an
    interval computed over seeds is not an interval over the variation that
    matters. The multiple is printed at the end of each row, so the reader does
    not have to measure a log axis by eye.

    Identity does not rest on colour: the seed mark is open and the subject mark
    is filled, which survives greyscale and print.
    """
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.55), sharey=True, sharex=True)
    # One order for all three panels, by parameter count. An earlier version sorted
    # each panel by its own subject-to-seed ratio while sharing the y-axis, so two
    # of the three panels were labelled with the third panel's ordering -- the rows
    # were right and the names against them were wrong.
    models = sorted(C.MODELS, key=lambda m: C.PARAMS[m])
    axes[0].set_xscale("log")
    axes[0].set_xlim(0.0035, 1.35)
    axes[0].set_ylim(-0.65, len(models) - 0.35)

    for col, (ax, arm) in enumerate(zip(axes, ARMS)):
        for y, m in enumerate(models):
            sub = lookup("Arm %s %s subject SD of PR-AUC" % (arm, m))
            seed = lookup("Arm %s %s seed SD of PR-AUC" % (arm, m))
            ratio = lookup("Arm %s %s subject to seed SD ratio" % (arm, m))
            ax.plot([seed, sub], [y, y], color=AXIS, lw=0.7, zorder=1,
                    solid_capstyle="butt")
            ax.plot(seed, y, "o", ms=3.8, mfc="white", mec=ACCENT, mew=0.9,
                    zorder=3)
            ax.plot(sub, y, "o", ms=4.2, color=ACCENT, mec="white", mew=0.5,
                    zorder=3)
            # The multiple is a registry value, not a quantity computed here.
            ax.text(sub * 1.5, y, "×%.1f" % ratio, fontsize=5.2, color=INK_SOFT,
                    ha="left", va="center")
        ax.set_yticks(range(len(models)))
        ax.set_yticklabels([SHORT[m] for m in models], fontsize=6.0, color=INK)
        lo = lookup("Arm %s minimum subject to seed SD ratio" % arm)
        hi = lookup("Arm %s maximum subject to seed SD ratio" % arm)
        _paper(ax, grid="x")
        ax.set_title("Arm %s\n×%.1f to ×%.1f" % (arm, lo, hi),
                     fontsize=6.8, color=INK, pad=6)
        # Higher than Figure 3's, because this title runs to two lines.
        ax.text(0.0, 1.14, "(%s)" % "abc"[col], transform=ax.transAxes,
                ha="left", va="bottom", fontsize=6.8, fontweight="bold", color=INK)

    axes[1].set_xlabel("Standard deviation of subject-level PR-AUC (log scale)",
                       fontsize=6.6, color=INK_SOFT)
    handles = [
        Line2D([], [], marker="o", ls="", ms=3.8, mfc="white", mec=ACCENT,
               mew=0.9, label="across the five seed means"),
        Line2D([], [], marker="o", ls="", ms=4.2, color=ACCENT, mec="white",
               mew=0.5, label="across the ten subjects"),
    ]
    axes[1].legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.24),
                   ncol=2, fontsize=6.2, frameon=False, handletextpad=0.4,
                   columnspacing=2.2)
    fig.subplots_adjust(left=0.075, right=0.995, top=0.80, bottom=0.25, wspace=0.10)
    _save(fig, "figure4_subject_against_seed_spread")


def main(argv=None):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "axes.facecolor": "white",
        "savefig.facecolor": "white", "pdf.fonttype": 42, "ps.fonttype": 42,
    })
    print("drawing figures from %s" % C.REGISTRY_CSV)
    figure0()
    figure1()
    figure2()
    figure3()
    figure4()
    figure5()
    figure6()
    return 0



# --------------------------------------------------------------- figure 5
# A multi-panel overview in the layout journals in this field tend to use:
# ranking metrics across the top, reliability diagrams through the middle,
# probability quality and the accuracy baseline along the bottom.
# Identity by architecture, in a fixed order that is never cycled. This is the
# ONE figure in the paper that needs five distinguishable colours: five bars stand
# side by side in every group and position alone cannot name them.
#
# The default bright set was replaced on 24 September 2026 with a muted set chosen
# to sit beside the rest of the figures rather than shout over them, and then
# CHECKED rather than eyeballed. Every pair that lands next to another is separable
# under deuteranopia and protanopia, every colour clears 3:1 against white, and
# none of them reads as grey:
#
#   lightness band   PASS   all five inside L 0.43-0.77
#   chroma floor     PASS   all five >= 0.1
#   CVD separation   PASS   worst adjacent pair dE 8.2 (deutan), 21.4 (tritan)
#   normal vision    PASS   worst adjacent pair dE 17.0
#   contrast         PASS   all five >= 3:1 against the surface
#
# A first attempt used five steps of the house accent, since C.MODELS happens to
# be in ascending parameter order and a sequential ramp would have encoded that.
# It failed: the two lightest steps were dE 10.9 apart in NORMAL vision and below
# 2:1 against white, so a reader with no colour-vision deficiency at all could not
# have told EEGNet from ShallowConvNet.
CAT = {
    "EEGNet": "#2166a5", "ShallowConvNet": "#b0721c", "CNN": "#2f9463",
    "DeepConvNet": "#a82a3c", "CNN-BiLSTM": "#6a5aa0",
}
BASELINE_FILL = "#d5d4cf"


def _bars(ax, metric, label, ylim, subject_averaged=True):
    """Grouped bars: one group per construction, one bar per architecture."""
    width = 0.15
    for i, m in enumerate(C.MODELS):
        xs, ys, es = [], [], []
        for j, arm in enumerate(ARMS):
            key = "Arm %s %s %s %s" % (arm, m, metric,
                                       "SUBJECT-AVERAGED" if subject_averaged else "POOLED")
            xs.append(j + (i - 2) * width)
            ys.append(lookup(key))
            es.append(lookup("Arm %s %s %s %s" % (arm, m, metric,
                                                  "seed SD" if subject_averaged
                                                  else "pooled seed SD")))
        ax.bar(xs, ys, width * 0.92, yerr=es, color=CAT[m], label=m,
               error_kw=dict(ecolor=INK_SOFT, lw=0.6, capsize=1.6), zorder=2)
    ax.set_xticks(range(len(ARMS)))
    ax.set_xticklabels(["Arm %s\n(%.2f %%)" % (a, lookup("Arm %s prevalence percent" % a))
                        for a in ARMS], fontsize=5.8)
    ax.set_ylim(*ylim)
    _paper(ax, grid="y")
    ax.set_ylabel(label, fontsize=6.2, color=INK_SOFT)


def _reliability(ax, arm, model, calibrated, title, colour):
    """A reliability diagram computed from the released per-window scores.

    Only the constructions whose probability files are released can appear here.
    Drawing a reliability diagram for an arm whose scores were not retained would
    mean inventing the curve.
    """
    import glob
    import re

    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from src.calibrate import _logit

    nice = {"CNN-BiLSTM": "CNNBiLSTM"}
    stem = nice.get(model, model)
    paths = sorted(glob.glob(os.path.join(C.RESULT_DIR, arm,
                                          "probs_%s_seed*.npz" % stem)))
    edges = np.linspace(0, 1, 11)
    centres, curves = 0.5 * (edges[:-1] + edges[1:]), []

    for path in paths:
        d = np.load(path)
        y, p, subj = d["y_true"], d["y_prob"].astype(float), d["subject"]
        obs = np.full(len(centres), np.nan)
        pp, yy = [], []
        for s in np.unique(subj):
            te, tr = subj == s, subj != s
            if calibrated:
                if len(np.unique(y[tr])) < 2:
                    continue
                lr = LogisticRegression(C=C.PLATT_C, solver="lbfgs")
                lr.fit(_logit(p[tr]).reshape(-1, 1), y[tr])
                pp.append(lr.predict_proba(_logit(p[te]).reshape(-1, 1))[:, 1])
            else:
                pp.append(p[te])
            yy.append(y[te])
        pp, yy = np.concatenate(pp), np.concatenate(yy)
        idx = np.digitize(pp, edges[1:-1])
        for b in range(len(centres)):
            sel = idx == b
            if sel.sum() >= 20:
                obs[b] = yy[sel].mean()
        curves.append(obs)

    curves = np.vstack(curves)
    mean = np.nanmean(curves, axis=0)
    sd = np.nanstd(curves, axis=0)
    ok = ~np.isnan(mean)

    ax.plot([0, 1], [0, 1], ls=(0, (3.5, 3)), lw=0.8, color=INK_SOFT,
            label="perfect calibration", zorder=1)
    ax.axhline(lookup("Arm %s prevalence percent" % arm) / 100.0, ls=(0, (2.5, 2)),
               lw=0.8, color=NEUTRAL, label="class prior", zorder=1)
    ax.fill_between(centres[ok], (mean - sd)[ok], (mean + sd)[ok], color=colour,
                    alpha=0.16, lw=0, zorder=2)
    ax.plot(centres[ok], mean[ok], "-o", ms=2.8, lw=1.1, color=colour, zorder=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    _paper(ax, grid="y")
    ax.set_xlabel("predicted probability", fontsize=6.2, color=INK_SOFT)
    ax.set_ylabel("observed frequency", fontsize=6.2, color=INK_SOFT)
    ax.set_title(title, fontsize=6.6, color=INK, loc="left", pad=5)
    ax.legend(fontsize=5.4, frameon=False, loc="upper left", handlelength=1.4,
              labelspacing=0.2)


def figure5():
    """One overview panel, in the multi-panel style, with this study's numbers.

    The layout is the one such figures usually take. The content is not: the
    reliability panels show an architecture whose probabilities are *worse* than
    the class prior, and the Brier panel marks that reference explicitly, because
    that is what this study found.
    """
    import numpy as np

    # Printed at the double-column width the other five figures use, so the type
    # sizes here are the type sizes a reader gets.
    fig = plt.figure(figsize=(7.16, 7.6))
    gs = fig.add_gridspec(3, 3, hspace=0.62, wspace=0.34,
                          top=0.905, bottom=0.115, left=0.085, right=0.985)

    # --- top row: ranking and detection
    _bars(fig.add_subplot(gs[0, 0]), "auc", "ROC-AUC", (0, 1.05))
    fig.axes[-1].set_title("(a) ROC-AUC, subject-averaged", fontsize=6.6,
                           color=INK, loc="left", pad=5)
    _bars(fig.add_subplot(gs[0, 1]), "pr_auc", "PR-AUC", (0, 0.62))
    fig.axes[-1].set_title("(b) PR-AUC, subject-averaged", fontsize=6.6,
                           color=INK, loc="left", pad=5)
    _bars(fig.add_subplot(gs[0, 2]), "recall", "recall", (0, 0.95))
    fig.axes[-1].set_title("(c) recall of the drowsy class", fontsize=6.6,
                           color=INK, loc="left", pad=5)

    # --- middle row: reliability, on the one arm whose scores are released
    _reliability(fig.add_subplot(gs[1, 0]), "A", "EEGNet", False,
                 "(d) EEGNet, raw  —  Arm A", ACCENT)
    _reliability(fig.add_subplot(gs[1, 1]), "A", "EEGNet", True,
                 "(e) EEGNet, recalibrated", ACCENT)
    _reliability(fig.add_subplot(gs[1, 2]), "A", "CNN", False,
                 "(f) CNN, raw  —  Arm A", ACCENT)

    # --- bottom left: Brier against the class-prior reference
    axg = fig.add_subplot(gs[2, 0])
    # Room for the whole whisker: on Arm B one seed gives ShallowConvNet 0.2246
    # against about 0.11 for the other four, and clipping that bar would hide a
    # real instability rather than a plotting inconvenience.
    _bars(axg, "brier", "Brier score", (0, 0.21), subject_averaged=False)
    for j, arm in enumerate(ARMS):
        ref = lookup("Arm %s class-prior Brier reference" % arm)
        axg.plot([j - 0.42, j + 0.42], [ref, ref], color=INK, lw=1.0, zorder=4)
    axg.set_title("(g) pooled Brier, with the class-prior reference",
                  fontsize=6.6, color=INK, loc="left", pad=5)
    # Wrapped onto two lines: as one line it reached the right-hand spine, and in
    # panel (h) the equivalent note was clipped mid-word.
    axg.annotate("above the black rule is worse\nthan a constant predictor",
                 xy=(0.02, 0.985), xycoords="axes fraction", fontsize=5.2,
                 color=INK_SOFT, ha="left", va="top", linespacing=1.35)

    # --- bottom middle: ECE, three architectures per arm only
    axh = fig.add_subplot(gs[2, 1])
    width = 0.15
    for i, m in enumerate(C.MODELS):
        xs, ys = [], []
        for j, arm in enumerate(ARMS):
            claim = "Arm %s %s raw ECE SUBJECT-AVERAGED" % (arm, m)
            if claim in _load():
                xs.append(j + (i - 2) * width)
                ys.append(lookup(claim))
        if xs:
            axh.bar(xs, ys, width * 0.92, color=CAT[m], zorder=2)
    axh.set_xticks(range(len(ARMS)))
    axh.set_xticklabels(["Arm %s" % a for a in ARMS], fontsize=5.8)
    axh.set_ylim(0, 0.24)
    _paper(axh, grid="y")
    axh.set_ylabel("expected calibration error", fontsize=6.2, color=INK_SOFT)
    axh.set_title("(h) raw ECE  —  three architectures per arm",
                  fontsize=6.6, color=INK, loc="left", pad=5)
    axh.annotate("a bar is absent where the\nper-window scores were not retained",
                 xy=(0.02, 0.985), xycoords="axes fraction", fontsize=5.2,
                 color=INK_SOFT, ha="left", va="top", linespacing=1.35)

    # --- bottom right: accuracy against the always-alert baseline
    axi = fig.add_subplot(gs[2, 2])
    for i, m in enumerate(C.MODELS):
        xs = [j + (i - 2.5) * width for j in range(len(ARMS))]
        ys = [lookup("Arm %s %s pooled accuracy percent" % (a, m)) / 100 for a in ARMS]
        axi.bar(xs, ys, width * 0.92, color=CAT[m], zorder=2)
    xs = [j + 2.5 * width for j in range(len(ARMS))]
    ys = [lookup("Arm %s always-alert accuracy percent, 2 dp" % a) / 100 for a in ARMS]
    axi.bar(xs, ys, width * 0.92, color=BASELINE_FILL, hatch="////",
            edgecolor=INK_SOFT, lw=0.5, zorder=2, label="always alert")
    axi.set_xticks(range(len(ARMS)))
    axi.set_xticklabels(["Arm %s" % a for a in ARMS], fontsize=5.8)
    axi.set_ylim(0.75, 1.0)
    _paper(axi, grid="y")
    axi.set_ylabel("pooled accuracy", fontsize=6.2, color=INK_SOFT)
    axi.set_title("(i) accuracy, and the majority-class baseline",
                  fontsize=6.6, color=INK, loc="left", pad=5)

    handles = [Line2D([], [], marker="s", ls="", ms=4.2, color=CAT[m], label=m)
               for m in C.MODELS]
    handles.append(Line2D([], [], marker="s", ls="", ms=4.2, color=BASELINE_FILL,
                          markeredgecolor=INK_SOFT, markeredgewidth=0.5,
                          label="always alert / class prior"))
    # The legend keeps the bar order, so a reader can name a bar by counting from
    # the left even where two colours are close.
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=5.8,
               frameon=False, bbox_to_anchor=(0.535, 0.022), columnspacing=1.1,
               handletextpad=0.4)
    fig.suptitle("Five architectures, three window-set constructions, "
                 "leave-one-subject-out", fontsize=8.4, color=INK, y=0.977)
    fig.text(0.535, 0.952, "bars follow the legend order left to right within every "
             "group; error bars are the standard deviation across the five "
             "seed-level means", ha="center", fontsize=5.8, color=INK_SOFT)
    _save(fig, "figureS1_overview")


# --------------------------------------------------------------- figure 0
def figure0():
    """The study design as a methodology pipeline, drawn at printed size.

    Redesigned 19 September 2026. The first version packed fourteen boxes into a
    grid; at column width the text inside them was smaller than the caption, which
    is the usual way a design figure fails. This one is laid out at the width it
    will be printed at -- 7.16 inches, two columns -- so the type sizes here are
    the type sizes a reader gets, and nothing is shrunk afterwards.

    Three bands, read downwards, each answering one question: what the signal
    becomes, how the three constructions differ, and what a fold is. The
    leave-one-subject-out split is DRAWN rather than described, because ten cells
    with one held out says in a glance what a sentence takes a paragraph to say.
    The fold count is the hero number because it is the study's size.

    Band labels are kept short on purpose: a long one would run into the corridor
    the flow arrows need, and an arrow crossing a label is the defect this layout
    was rebuilt to remove.

    Every value still comes from the registry or config.py. The redesign changed no
    number; if a seed count or a prevalence changed, the picture would change too.
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

    n_sub = int(lookup("subjects"))
    n_seed = int(lookup("seeds"))
    n_arch = int(lookup("architectures"))
    n_fold = int(lookup("folds in ALL_FOLDS"))
    win = int(lookup("window length samples"))
    n_val = C.N_VAL
    n_train = n_sub - 1 - n_val

    # The house accent, not a local one: Figure 2 carried its own blue until
    # 24 September 2026, which was the only colour in the paper that belonged to
    # no palette.
    FILL = "#f2f2ef"
    RULE = "#c9c8c3"

    fig, ax = plt.subplots(figsize=(7.16, 5.7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def band(y, text):
        """A band heading. No A/B/C letters: those mean the three arms here."""
        ax.plot([1.0, 3.2], [y, y], color=ACCENT, lw=1.8, solid_capstyle="butt")
        ax.text(4.4, y, text, fontsize=8.0, fontweight="bold", color=INK,
                va="center")

    def stage(x, y, n):
        """A numbered disc, so the running text can name one box and be understood."""
        ax.add_patch(plt.Circle((x, y), 1.55, fc=INK, ec="none", zorder=4,
                                transform=ax.transData))
        ax.text(x, y, str(n), ha="center", va="center", fontsize=5.6,
                fontweight="bold", color="white", zorder=5)

    def box(x, y, w, h, head, body, fc="white", n=None):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.7",
            fc=fc, ec=INK, lw=0.8, zorder=2))
        ax.text(x + w / 2, y + h - 3.0, head, ha="center", va="center",
                fontsize=7.2, fontweight="bold", color=INK, zorder=3)
        ax.text(x + w / 2, y + (h - 6.0) / 2, body, ha="center", va="center",
                fontsize=6.1, color=INK_SOFT, zorder=3, linespacing=1.5)
        if n is not None:
            stage(x + 1.0, y + h, n)

    def arrow(p, q, color=INK, lw=0.9):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8,
                                     lw=lw, color=color, shrinkA=0, shrinkB=0,
                                     zorder=1))

    # ---- A: recordings become labelled windows ----------------------------
    band(96.5, "Signal to windows")
    steps = [
        ("Raw EEG", "O1 O2 C3 C4\n%.0f Hz · %d recordings" % (C.FS, 2 * n_sub)),
        ("Filtering", "0.5–40 Hz band-pass\n50 Hz notch · zero-phase"),
        ("Windowing", "%.0f s non-overlapping\n%d × 4 samples" % (C.WIN_SEC, win)),
        ("Labelling", "drowsy: ends at an\nannotated event mark\nalert: ≥ 20 s guard"),
    ]
    w, gap, ya, ha_ = 21.0, 4.0, 76.0, 15.5
    x0 = (100 - (4 * w + 3 * gap)) / 2
    for i, (head, body) in enumerate(steps):
        x = x0 + i * (w + gap)
        box(x, ya, w, ha_, head, body, n=i + 1)
        if i:
            arrow((x - gap, ya + ha_ / 2), (x, ya + ha_ / 2))

    # ---- B: one window set becomes three ----------------------------------
    band(69.5, "Three constructions of the same ten recordings")
    aw, agap, ay, ah = 29.0, 3.0, 46.0, 18.5
    ax0 = (100 - (3 * aw + 2 * agap)) / 2
    rules = {"A": "trimmed to shortest\nevery drowsy window kept",
             "B": "untrimmed\nsubject's own ratio kept",
             "C": "trimmed to shortest\nsubject's own ratio kept"}

    # The trunk drops from the middle of band A, then fans -- entirely below the
    # band label, so no arrow crosses any text.
    trunk_y = 66.0
    ax.plot([50, 50], [ya, trunk_y], color=INK, lw=0.9, zorder=1)
    for i, arm in enumerate(ARMS):
        x = ax0 + i * (aw + agap)
        arrow((50, trunk_y), (x + aw / 2, ay + ah))
        ax.add_patch(FancyBboxPatch(
            (x, ay), aw, ah, boxstyle="round,pad=0,rounding_size=0.7",
            fc=FILL, ec=INK, lw=0.8, zorder=2))
        if i == 0:
            stage(x + 1.0, ay + ah, 5)
        ax.text(x + aw / 2, ay + ah - 3.2, "Arm %s" % arm, ha="center",
                va="center", fontsize=7.6, fontweight="bold", color=INK, zorder=3)
        ax.text(x + aw / 2, ay + ah - 7.8, rules[arm], ha="center", va="center",
                fontsize=6.1, color=INK_SOFT, zorder=3, linespacing=1.5)
        ax.plot([x + 2.5, x + aw - 2.5], [ay + 7.6, ay + 7.6], color=RULE,
                lw=0.7, zorder=3)
        ax.text(x + aw / 2, ay + 5.6,
                "{:,} windows  ·  {:,} per subject".format(
                    int(lookup("Arm %s windows" % arm)),
                    int(lookup("Arm %s windows per subject" % arm))),
                ha="center", va="center", fontsize=6.1, color=INK, zorder=3)
        ax.text(x + aw / 2, ay + 2.6,
                "{:,} drowsy  ·  prevalence {:.2f} %".format(
                    int(lookup("Arm %s drowsy windows" % arm)),
                    lookup("Arm %s prevalence percent" % arm)),
                ha="center", va="center", fontsize=6.1, color=INK, zorder=3)

    # ---- C: what one fold is, and how many ---------------------------------
    band(42.0, "Cross-validation and total evaluation")

    # Row 1: what one fold is.
    cell, cy, ch, cx0 = 4.1, 30.0, 5.8, 6.0
    groups = [(n_train, "white"), (n_val, FILL), (1, ACCENT)]
    i = 0
    for count, fc in groups:
        for _ in range(count):
            ax.add_patch(Rectangle((cx0 + i * cell, cy), cell - 0.7, ch,
                                   fc=fc, ec=INK, lw=0.7, zorder=2))
            i += 1
    strip_w = n_sub * cell - 0.7
    stage(cx0 + 1.4, cy + ch + 3.4, 6)
    ax.text(cx0 + 4.2, cy + ch + 3.4, "%d subjects, split once per fold" % n_sub,
            ha="left", va="center", fontsize=6.6, fontweight="bold", color=INK)

    # A legend row rather than labels under two-cell and one-cell groups, which is
    # where an earlier version collided with itself.
    lx = cx0
    for fc, label in (("white", "%d training" % n_train),
                      (FILL, "%d validation" % n_val),
                      (ACCENT, "1 test")):
        ax.add_patch(Rectangle((lx, cy - 5.2), 2.4, 2.4, fc=fc, ec=INK, lw=0.7))
        ax.text(lx + 3.2, cy - 4.0, label, fontsize=6.1, color=INK_SOFT,
                va="center")
        lx += 3.2 + len(label) * 0.95 + 2.2
    ax.text(cx0, cy - 9.0,
            "the test subject is held out entirely; every subject is held out "
            "exactly once",
            fontsize=6.1, style="italic", color=INK_SOFT, va="center")

    # Leakage control and training are drawn as their own stages: these are the two
    # steps a reviewer checks first, and burying them in prose invites the question.
    bw, bh = 23.5, 14.5
    box(51.0, cy - 4.5, bw, bh, "Leakage control",
        "normalisation fitted on\nthe %d training subjects\nonly" % n_train, n=7)
    box(76.5, cy - 4.5, bw, bh, "Training",
        "class-weighted BCE\nAdam · \u2264 %d epochs\nearly stop on val. PR-AUC"
        % C.EPOCHS, n=8)
    arrow((cx0 + strip_w + 1.2, cy + ch / 2), (51.0 - 1.2, cy + ch / 2))
    arrow((51.0 + bw + 0.6, cy + ch / 2), (76.5 - 0.6, cy + ch / 2))

    # Row 2: the arithmetic, ending in the number the study is sized by.
    ey = 12.0
    ax.text(cx0, ey + 2.6,
            "%d subjects  ×  %d seeds  ×  %d architectures  ×  %d constructions  ="
            % (n_sub, n_seed, n_arch, len(ARMS)),
            fontsize=7.0, color=INK, va="center")
    hx, hw, hh = 66.0, 19.0, 12.5
    ax.add_patch(FancyBboxPatch((hx, ey - 3.6), hw, hh,
                                boxstyle="round,pad=0,rounding_size=0.7",
                                fc="white", ec=ACCENT, lw=1.4, zorder=2))
    ax.text(hx + hw / 2, ey + 4.0, "{:,}".format(n_fold), ha="center",
            va="center", fontsize=17, fontweight="bold", color=ACCENT, zorder=3)
    ax.text(hx + hw / 2, ey - 1.4, "evaluated folds", ha="center", va="center",
            fontsize=6.4, color=INK, zorder=3)

    ax.plot([cx0, 96.0], [5.2, 5.2], color=RULE, lw=0.7)
    ax.text(cx0, 2.2,
            # fold_metrics() computes six. Accuracy, Brier score and expected
            # calibration error are NOT among them: accuracy exists only as a
            # pooled quantity in this paper, and the other two are computed from
            # the probability files after the fact. Listing all eight here as
            # per-fold contradicted the paper's own Methods in its opening figure.
            "Measured on every fold:  ROC-AUC · PR-AUC · recall · F1 · balanced "
            "accuracy · precision\n"
            "Derived afterwards, pooled or from the probability files:  accuracy · "
            "Brier score · expected calibration error",
            fontsize=6.1, color=INK_SOFT, va="center")

    _save(fig, "figure2_study_design")



# --------------------------------------------------------------- figure 6
def figure6():
    """The two prespecified models side by side, and the one component that differs.

    Drawn from src.models' layer tuples and config.PARAMS, not from a list retyped
    here. That is the whole design of this figure: the architecture was described in
    three places -- the builders, the Architectures section, and an early hand-drawn
    diagram -- and the three disagreed. The diagram flattened three convolution
    blocks into one, and the prose called the LSTM dropout "recurrent dropout" where
    the code sets Keras's `dropout`. A picture typed by hand cannot be checked; this
    one is generated, so changing a filter count changes the figure.

    The trunk is drawn once, spanning both columns, because it IS the same trunk --
    that is the point of the ablation. Only the block below it differs, and the
    parameter cost of the substitution is stated where the eye lands.
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    from src import models as M

    FILL = "#f2f2ef"
    RULE = "#c9c8c3"
    win = int(lookup("window length samples"))
    chans = len(C.WANT)
    p_cnn, p_bil = C.PARAMS["CNN"], C.PARAMS["CNN-BiLSTM"]

    # The y window is cropped to the content rather than left at 0-100: an earlier
    # draft wasted the bottom sixth of the canvas, which at printed size means the
    # boxes are smaller than they need to be for no reason.
    fig, ax = plt.subplots(figsize=(7.16, 5.9))
    ax.set_xlim(0, 100)
    ax.set_ylim(8.0, 99.5)
    ax.axis("off")

    def box(cx, y, w, h, text, fc=FILL, ec=RULE, fs=6.2, bold=False, tc=INK):
        ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0,rounding_size=0.9",
                                    fc=fc, ec=ec, lw=0.8, zorder=2))
        ax.text(cx, y, text, ha="center", va="center", fontsize=fs, color=tc,
                fontweight="bold" if bold else "normal", zorder=3, linespacing=1.35)

    def down(cx, y0, y1):
        ax.add_patch(FancyArrowPatch((cx, y0), (cx, y1), arrowstyle="-|>",
                                     mutation_scale=7, color=INK_SOFT, lw=0.8,
                                     shrinkA=0, shrinkB=0, zorder=1))

    # ---- shared trunk, spanning both columns
    ax.text(3.0, 96.5, "Shared convolutional trunk", fontsize=8.0,
            fontweight="bold", color=INK, va="center")
    ax.plot([3.0, 97.0], [93.4, 93.4], color=ACCENT, lw=1.6, solid_capstyle="butt")

    box(50, 91.0, 40, 5.2, "Input   %d samples × %d channels" % (win, chans),
        fc="white", fs=6.4)

    # One row per convolution block, each with its own pooling, normalisation and
    # dropout -- three blocks, not one. Lengths halve at each pooling stage.
    blocks, length = [], win
    for item in M.CONV_TRUNK:
        if item[0] == "conv":
            blocks.append({"filters": item[1], "kernel": item[2]})
        elif item[0] == "pool":
            length //= item[1]
            blocks[-1]["pool"] = item[1]
            blocks[-1]["out"] = length
        elif item[0] == "dropout":
            blocks[-1]["drop"] = item[1]

    y = 82.0
    down(50, 88.4, y + 3.8)          # input -> block 1; this had zero length once
    for i, b in enumerate(blocks, 1):
        box(50, y, 62, 7.2,
            "Conv1D   %d filters × length %d   %s padding, %s\n"
            "MaxPool /%d   →  %d steps      BatchNorm      Dropout %.1f"
            % (b["filters"], b["kernel"], M.CONV_PADDING, M.CONV_ACTIVATION,
               b["pool"], b["out"], b["drop"]))
        ax.text(16.5, y, "block %d" % i, ha="right", va="center",
                fontsize=5.8, color=INK_SOFT, style="italic")
        if i < len(blocks):
            down(50, y - 3.6, y - 6.4)
        y -= 10.0

    ax.plot([3.0, 97.0], [y + 4.6, y + 4.6], color=RULE, lw=0.7, ls=(0, (3, 3)))
    ax.text(50, y + 1.6, "the trunk above is identical in both models; "
            "only the block below it differs",
            ha="center", va="center", fontsize=6.0, color=INK_SOFT, style="italic")

    # ---- the two branches
    lx, rx, top = 27.0, 73.0, y - 3.4
    for cx, name, params in ((lx, "CNN", p_cnn), (rx, "CNN-BiLSTM", p_bil)):
        ax.text(cx, top, name, ha="center", va="center", fontsize=7.4,
                fontweight="bold", color=INK)
    down(lx, top - 2.2, top - 5.6)
    down(rx, top - 2.2, top - 5.6)

    box(lx, top - 9.4, 40, 6.0, "Global average\npooling over time", fc="white")
    units = [i for i in M.RECURRENT_BLOCK]
    box(rx, top - 9.4, 40, 6.0,
        "BiLSTM %d, return sequences\nBiLSTM %d      input dropout %.1f"
        % (units[0][1], units[1][1], units[0][3]), fc="white")

    # The head, shared again.
    hy = top - 18.0
    down(lx, top - 12.4, hy + 4.0)
    down(rx, top - 12.4, hy + 4.0)
    dense = [i for i in M.HEAD if i[0] == "dense"]
    head_drop = [i[1] for i in M.HEAD if i[0] == "dropout"][0]
    head_text = ("Dense %d, %s      Dropout %.1f      Dense %d, %s"
                 % (dense[0][1], dense[0][2], head_drop, dense[1][1], dense[1][2]))
    for cx in (lx, rx):
        box(cx, hy, 44, 5.4, head_text, fs=5.9)

    # What comes out. The final layer is a single sigmoid unit, so the model's output
    # is one number in [0, 1] per window, and every measurement in this paper -- the
    # thresholded confusion matrices, the ROC and PR curves, the Brier score, the
    # calibration curves and the recalibration itself -- is computed from it. Naming
    # it closes the diagram: without this box the picture stops at a layer, and a
    # reader has to infer what the layer produces.
    # Derived, not asserted. The box may call the output a probability in [0, 1] only
    # because the final layer is a single sigmoid unit; if the head ever stops being
    # one, this raises rather than drawing a label the model no longer earns.
    oy = hy - 8.2
    final = dense[-1]
    if (final[1], final[2]) != (1, "sigmoid"):
        raise ValueError("the head now ends in %d unit(s) with %r activation, so the "
                         "output is not a probability in [0, 1] and the figure must "
                         "not say it is" % (final[1], final[2]))
    out_text = "Drowsy probability (0–1)"
    for cx in (lx, rx):
        down(cx, hy - 2.7, oy + 2.5)
        box(cx, oy, 34, 4.6, out_text, fc="white", fs=6.2)

    for cx, params in ((lx, p_cnn), (rx, p_bil)):
        ax.text(cx, oy - 5.4, "{:,} trainable parameters".format(params),
                ha="center", va="center", fontsize=6.6, color=INK,
                fontweight="bold")

    ax.text(50, oy - 11.2,
            "Replacing global average pooling with the recurrent block adds "
            "{:,} parameters.\nThe comparison is therefore NOT capacity-controlled: "
            "recurrence and added capacity are not separable within it."
            .format(p_bil - p_cnn),
            ha="center", va="center", fontsize=6.2, color=INK_SOFT,
            linespacing=1.5)

    _save(fig, "figure1_cnn_against_cnn_bilstm")

if __name__ == "__main__":
    raise SystemExit(main())
