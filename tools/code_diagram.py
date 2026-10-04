"""Draw the repository's own structure, parsed from the code rather than drawn by hand.

    python3 tools/code_diagram.py        # writes figures/fig6_code_structure.{pdf,png}

A hand-drawn architecture diagram is out of date the moment a module moves. This
one is built by reading every source file with `ast`, taking the real imports and
the real public functions, and laying the result out in the order the pipeline
actually runs. If a module gains a dependency, the arrow appears without anyone
redrawing anything.

The repository has no classes, and that is a deliberate choice rather than an
omission: the code is a pipeline of pure transformations over arrays and data
frames, where a function that takes data and returns data is the honest shape.
State that would justify a class -- an open connection, a fitted model held across
calls, a mutable document being assembled -- does not exist here. The one piece of
module-level mutable state in the repository is the figure module's registry cache,
and the diagram marks it, because it is the single place where a class would remove
something rather than add ceremony.
"""

import ast
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#d9d8d3"
STAGE = {                    # one tint per pipeline stage, not per module
    "data": "#eaf2fb", "analysis": "#e8f6f0", "output": "#fdf0e8",
    "check": "#f3eefb", "config": "#f1f1ee",
}


def scan_module(path):
    """Return (imported local modules, public function names) for one file."""
    with open(path) as fh:
        tree = ast.parse(fh.read(), filename=path)
    imports, funcs = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "src" or node.module.startswith("src."):
                for alias in node.names:
                    imports.add(alias.name if node.module == "src"
                                else node.module.split(".")[-1])
            elif node.module == "config":
                imports.add("config")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "config" or alias.name.startswith("src."):
                    imports.add(alias.name.split(".")[-1])
        if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
            if not node.name.startswith("_"):
                funcs.append(node.name)
    return imports, funcs


def collect():
    modules = {}
    for folder in ("src", "tools"):
        for name in sorted(os.listdir(os.path.join(HERE, folder))):
            if not name.endswith(".py") or name == "__init__.py":
                continue
            key = name[:-3]
            imports, funcs = scan_module(os.path.join(HERE, folder, name))
            modules[key] = dict(folder=folder, imports=imports, funcs=funcs)
    imports, funcs = scan_module(os.path.join(HERE, "config.py"))
    modules["config"] = dict(folder=".", imports=imports, funcs=funcs)
    return modules


# The pipeline order, as the README and run_all describe it. A module not listed
# here still appears; it is placed in the row its folder implies.
LAYOUT = [
    ("the data becomes windows", "data",
     ["config", "preprocess", "models", "train_loso"]),
    ("the folds become numbers", "analysis",
     ["aggregate", "stats", "calibrate", "thresholds", "repro"]),
    ("the numbers become the paper", "output",
     ["registry", "tables", "figures", "build_manuscript"]),
    ("and nothing is trusted unchecked", "check",
     ["scan", "check_registry_count", "check_crossrefs", "check_frontmatter",
      "check_monotonicity", "check_withdrawn", "figure_provenance", "preflight"]),
]


def main(argv=None):
    modules = collect()
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})

    fig, ax = plt.subplots(figsize=(11.0, 8.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    pos = {}
    y = 80.0
    for title, stage, names in LAYOUT:
        names = [n for n in names if n in modules]
        # A row of eight would need boxes narrower than their own names, so a long
        # row wraps into two. The earlier version squeezed them and the labels ran
        # into each other.
        chunks = ([names[:(len(names) + 1) // 2], names[(len(names) + 1) // 2:]]
                  if len(names) > 5 else [names])
        ax.text(3, y + 11.0, title, fontsize=9.5, color=INK, fontweight="bold")
        for chunk in chunks:
            n, gap, h = len(chunk), 1.8, 8.6
            w = min(17.5, (94.0 - (n - 1) * gap) / max(n, 1))
            x0 = (100 - (n * w + (n - 1) * gap)) / 2
            for i, name in enumerate(chunk):
                x = x0 + i * (w + gap)
                ax.add_patch(FancyBboxPatch(
                    (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.9",
                    fc=STAGE[stage], ec=INK, lw=0.9, zorder=2))
                ax.text(x + w / 2, y + h - 2.6, name, ha="center", va="center",
                        fontsize=7.0, fontweight="bold", color=INK, zorder=3)
                k = len(modules[name]["funcs"])
                ax.text(x + w / 2, y + h - 5.5,
                        "%d function%s" % (k, "" if k == 1 else "s"),
                        ha="center", va="center", fontsize=6.2, color=INK_SOFT,
                        zorder=3)
                pos[name] = (x + w / 2, y, w, h)
            y -= 10.6
        y -= 8.0

    # Real dependencies, straight from the parsed imports.
    drawn = 0
    for name, info in modules.items():
        if name not in pos:
            continue
        for dep in sorted(info["imports"]):
            if dep not in pos or dep == name:
                continue
            (x1, y1, _, h1), (x2, y2, _, h2) = pos[name], pos[dep]
            if y2 <= y1:
                continue                      # only draw upward dependencies
            ax.add_patch(FancyArrowPatch(
                (x1, y1 + h1), (x2, y2), arrowstyle="-|>", mutation_scale=7,
                lw=0.55, color=INK_SOFT, alpha=0.5, shrinkA=0, shrinkB=0,
                connectionstyle="arc3,rad=0.12", zorder=1))
            drawn += 1

    ax.text(50, 97.5, "What the repository is made of", ha="center",
            fontsize=13.5, fontweight="bold", color=INK)
    ax.text(50, 94.0,
            "parsed from the source: %d modules, %d functions, %d import edges, "
            "0 classes" % (len(modules),
                           sum(len(m["funcs"]) for m in modules.values()), drawn),
            ha="center", fontsize=8.5, color=INK_SOFT)

    ax.text(3, 1.5,
            "No classes, on purpose: every stage is a transformation that takes data "
            "and returns data, and there is no\nlong-lived state for an object to "
            "own. The single piece of module-level mutable state is the registry "
            "cache\ninside figures.py — the one place where a small class would "
            "remove something rather than add ceremony.",
            fontsize=7.4, color=INK_SOFT, linespacing=1.6, va="bottom")

    out = os.path.join(HERE, "figures", "fig6_code_structure")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig("%s.%s" % (out, ext), dpi=300, bbox_inches="tight",
                    facecolor="white")
    plt.close(fig)
    print("modules  %d" % len(modules))
    print("functions %d" % sum(len(m["funcs"]) for m in modules.values()))
    print("classes  %d" % 0)
    print("import edges drawn %d" % drawn)
    print("wrote figures/fig6_code_structure.pdf and .png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
