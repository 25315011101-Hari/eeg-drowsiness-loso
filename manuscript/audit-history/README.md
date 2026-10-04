# Audit history

**Not current manuscript status.** Everything in this folder is a record of an audit
as it was written, on the date it was written, and is deliberately left that way.

Each file states counts — of tests, of pre-submission checks, of open findings — and
sentences like "nothing has been written into the manuscript". Those were true when
the entry was made. They are not a description of the repository now: most of what is
recorded here has since been acted on, and acting on it changed those counts.

Read these to answer *what was found, when, and on what evidence*. Do not read them
to answer *what the paper says now*. For that:

| Question | Where the answer is |
|---|---|
| What does the paper say? | `manuscript/MANUSCRIPT.md`, and its build stamp identifies the version |
| What number backs a claim? | `results/MASTER_NUMBERS.csv` |
| Is the paper green? | `python3 tools/preflight.py` |
| What does each check enforce? | `manuscript/REPRODUCIBILITY.md` |

These files sat beside the manuscript sources until 25 September 2026, where their
stale counts were repeatedly mistaken for current status during review. Moving them
here is the fix; the banner at the top of each is the second line of defence.
