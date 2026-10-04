"""Fail if a generated manuscript file has been edited by hand.

    python3 tools/check_generated.py

Some files under manuscript/ are not written by a person. They are produced by a
tool, and that tool is re-run by tools/preflight.py on every invocation. Editing
such a file directly appears to work -- the text is there, the diff looks right --
and then the next preflight run silently overwrites it.

This happened on 2 October 2026. `manuscript/MASTER_FILE.md` carried the sentence
"The deposit documents neither who made the marks nor against what criterion",
which the dataset README had just been shown to contradict. The sentence was
corrected in the generated file. tools/master_file.py was not touched, so the next
preflight regenerated the old sentence back into the manuscript -- and preflight
reported ALL CHECKS PASS while a withdrawn claim sat in the text. The existing
"master file" check only asserted that the generator *ran*; nothing compared what it
produced against what was on disk.

So the rule is now checkable rather than remembered: for every declared
(generated file, generator) pair, run the generator and compare. A difference means
somebody edited the output instead of the source, and names the file to edit instead.

The check is non-destructive. The original bytes are restored whether it passes or
fails, so running it never changes the repository.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Every manuscript file that a tool writes, and the command that writes it.
#
# To add one: name the file, the command that regenerates it from its real source,
# and where the edit belongs instead. A file absent from this list is treated as
# hand-written, which is the safe default -- a generated file left undeclared is the
# failure this check exists to prevent, so declare it when you add the generator.
#
# The generators have an order among themselves, and running them in the wrong one
# makes this check fail on a repository nobody edited by hand. MASTER_FILE.md and
# SPLIT_MAP.md are both derived from the section files, and MANUSCRIPT.md is assembled
# from them, so after editing a section the order is:
#
#     build_manuscript.py  ->  master_file.py  ->  check_split_map.py --write
#
# tools/preflight.py already runs them in an order that leaves the repository
# consistent; this note is for anyone regenerating by hand, which is where the mistake
# was made twice on 3 October 2026.
GENERATED = [
    {
        "path": "manuscript/MASTER_FILE.md",
        "command": ["tools/master_file.py"],
        "source": "tools/master_file.py -- the prose is written by w(...) calls there",
    },
    {
        "path": "manuscript/SPLIT_MAP.md",
        "command": ["tools/check_split_map.py", "--write"],
        "source": "tools/split_map.json for the data, tools/check_split_map.py for the layout",
    },
    {
        "path": "manuscript/MANUSCRIPT.md",
        "command": ["tools/build_manuscript.py", "manuscript", "manuscript/MANUSCRIPT.md"],
        "source": "the twelve section files under manuscript/ that the builder assembles",
    },
]

# The build stamp carries today's date and the assembled word count, so the built
# manuscript is not byte-stable from one day to the next. Its digest is taken over
# the body above the stamp, which is the part this check cares about.
VOLATILE = re.compile(r"(?m)^\*Build [0-9a-f]+ · .*$|^\*Rebuild: .*$")


def normalise(text):
    return VOLATILE.sub("", text)


def check_one(entry):
    """Run one generator and report whether its output matches what is on disk."""
    path = os.path.join(HERE, entry["path"])
    if not os.path.exists(path):
        return ["%s does not exist, and %s is declared to write it"
                % (entry["path"], " ".join(entry["command"]))]

    with open(path, "rb") as fh:
        before = fh.read()
    try:
        proc = subprocess.run([sys.executable] + entry["command"], cwd=HERE,
                              capture_output=True, text=True)
        with open(path, "rb") as fh:
            after = fh.read()
    finally:
        # Always put back exactly what was there. A check that mutates the thing it
        # is checking cannot be run twice with the same meaning.
        with open(path, "wb") as fh:
            fh.write(before)

    problems = []
    # A generator that cannot run at all is a separate failure from drift, and the
    # split-map writer exits non-zero when the map itself has problems, so a
    # non-zero code is only reported when nothing was written.
    if before == after and proc.returncode != 0 and not after:
        problems.append("%s failed to run: %s"
                        % (" ".join(entry["command"]),
                           (proc.stderr or proc.stdout).strip().splitlines()[-1:]))
    if normalise(before.decode("utf-8")) != normalise(after.decode("utf-8")):
        # Two causes look identical from here, and the remedy differs, so both are
        # named rather than one guessed at. The second cause is the common one and was
        # misdiagnosed by an earlier version of this message, which assumed a hand
        # edit when the real history was a source edit without a regeneration.
        problems.append(
            "%s is generated by %s, and regenerating it changes it. Either it was "
            "edited by hand -- in which case make the change in %s instead, because "
            "the next regeneration discards it -- or a source it is built from has "
            "changed and the generator has not been re-run since, in which case run "
            "the command above. The agreed order is: edit the source, regenerate, then "
            "test."
            % (entry["path"], " ".join(entry["command"]), entry["source"]))
    return problems


def main():
    problems = []
    print("generated files, compared against their generators")
    for entry in GENERATED:
        found = check_one(entry)
        print("  %-28s %s" % (entry["path"],
                              "in step with its generator" if not found else "DRIFTED"))
        problems += found
    print("")
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        print("%d problem(s)" % len(problems))
        return 1
    print("every generated file matches what its generator produces, so no hand edit "
          "is waiting to be overwritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
