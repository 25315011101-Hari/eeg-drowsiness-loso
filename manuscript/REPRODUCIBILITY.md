# Which file is the paper, and how every number in it is checked

*Status page, 18 September 2026. Not part of the manuscript.*

Six reviews of this work have now each quoted at least one sentence from a
superseded draft and reported an error that a later draft had already fixed. That
is not a filing inconvenience; it costs a real audit its accuracy. This page exists
so that question has one answer.

---

## 1. The manuscript

**`Manuscript_BSPC_<date>_build_<id>.pdf`** — built, not edited. It is the only file
to review or to cite a page of.

**It is not the file to submit.** The guide for authors says "A PDF is not an
acceptable source file" and asks for `.doc`, `.docx` or `.tex`, so the file that goes
to the journal is `Manuscript_BSPC_<date>_build_<id>.docx`, built by
`tools/build_docx.py` from the same twelve section files and carrying the same build
id. Section 1 said "the only file to review, cite or submit" until 7 October 2026 —
written before that sentence of the guide was read, and corrected here rather than
quietly, because a wrong statement about which file is the paper is exactly the
confusion this page exists to end. The guide's sentence, and the fact that it has one
source and one reading, is recorded in `tools/journal_requirements.json`.

Both files are built from `manuscript/MANUSCRIPT.md`, so the build id is the one
thing to compare between them: a .docx and a .pdf with the same id are the same paper.

**The build id is in the filename and printed at the end of the last page.** Every
build used to carry the same filename, so a downloads folder filled with
`… (1).pdf`, `… (2).pdf` and reviewers repeatedly read a superseded copy and
reported corrections the current text already had. Before reviewing any copy,
compare its build id against what the repository produces:

```
python3 tools/build_manuscript.py manuscript manuscript/MANUSCRIPT.md
```

Same id, same paper. A different id means the copy is not current, and the right
move is to rebuild rather than to report against it.

**The PDF is built by a command too, since 3 October 2026:**

```
python3 tools/build_pdf.py                  # the article, into pdf/
python3 tools/build_pdf.py --supplementary  # the supplementary document
python3 tools/build_pdf.py --out-dir <dir>  # somewhere other than pdf/
```

It reads the build id out of the manuscript's own stamp rather than recomputing it,
so a PDF cannot be named after an id its text does not carry, and it writes
`<Manuscript|Supplementary>_BSPC_<date>_build_<id>.pdf`. Before that date the
filename convention above was documented and the PDFs were made by hand outside the
repository, which is the same gap the number registry and the figure provenance
trail were built to close.

Two behaviours of that script are worth knowing before changing it:

- **The font is FreeSerif**, because it is the one available font that covers every
  non-ASCII character the manuscript uses. DejaVu Serif has no U+26A0 and Liberation
  Serif is missing two superscript digits as well. Changing the font means checking
  the manuscript's character set again, not assuming.
- **A dropped glyph fails the build.** XeLaTeX reports an uncovered character as a
  warning and silently omits it. The script scans the TeX log for
  `Missing character`, and if it finds any it **deletes the PDF it just wrote** and
  exits non-zero, naming the characters. A paper this careful about values must not
  ship with holes where characters were.

One transform is applied to the Markdown before pandoc sees it, and it lives in the
script rather than in the manuscript: a heading inside a block quote becomes bold
text, because LaTeX cannot open a list after a sectioning command inside a quote
environment. The script prints a note whenever it fires.

It is assembled by `tools/build_manuscript.py` from the twelve section files below,
in submission order, with the Hindi glosses, the "notes for the next pass"
sections and the blocks marked `<!-- not-for-submission -->` removed — the last of
those covers the front-matter preamble and the superseded title drafts, which are
editorial matter a reviewer should never see. The former data-availability blocker
notice referred to a repository placeholder that has since been removed after the
repository URL was recorded. **The body text is never edited in the manuscript**; it is edited
in a section file and the manuscript is rebuilt. Anything wrong in the PDF is wrong
in a section file.

| Section file | Becomes |
|---|---|
| `ABSTRACT.md` | Title, abstract, highlights, keywords, declarations |
| `INTRODUCTION.md` | 1. Introduction |
| `RELATED_WORK.md` | 2. Related Work |
| `RESEARCH_GAP.md` | 3. Research Gap |
| `METHODOLOGY.md` | 4. Methodology |
| `ARCHITECTURES.md` | 5. Architectures |
| `EXPERIMENTAL_SETUP.md` | 6. Experimental Setup |
| `RESULTS.md` | 7. Results |
| `DISCUSSION.md` | 8. Discussion, including 8.10 Limitations |
| `CONCLUSION.md` | 9. Conclusion |
| `CODE_AVAILABILITY.md` | Code and Data Availability |
| `REFERENCES.md` | References |

**The structure changed on 19 September 2026**, to the nine-section order the
supervisor set: Research Gap and Architectures became sections of their own, the
merged Methods file split into Methodology and Experimental Setup, and Limitations
became Section 8.10 rather than a section of its own. `tools/renumber.py` applied
the whole map in one pass — 129 substitutions across ten files — and
`check_crossrefs.py` verified that nothing points at a section that no longer
exists.

Rebuild with:

```
python3 tools/build_manuscript.py manuscript manuscript/MANUSCRIPT.md
```

There is **one copy** of each section file, in the repository's `manuscript/`. The
working folder reaches them by symlink, so there is no second copy that can drift
out of step — which is the same failure, at file level, as the superseded PDFs.

## 2. Everything else

**`snapshots/`** holds one zip per build, named
`snapshot_<build id>_<snapshot id>.zip`, written by `tools/snapshot.py`. The build id
identifies the manuscript inside it and the snapshot id the whole bundle, so a
snapshot can be matched to the text it contains. Superseded snapshots record how the
paper changed and several of them contain claims this paper has since withdrawn:
**nothing is quoted, reviewed or released from an old snapshot.**

**`pdf/`** holds the built PDFs. Each is reproducible from the command above, so a
PDF whose build id is not the current one is regenerated rather than reasoned about.

An earlier version of this section described an `archive/` folder of twenty
superseded draft PDFs, and per-section PDFs in the working folder. Neither exists in
this repository; the description was removed on 3 October 2026 rather than left to
mislead a reader looking for folders that are not there.

The review documents — `Audit_16sep2026.pdf`, `Checklist_Review.pdf`,
`Structure_Review.pdf`, `Guide_Briefing_Hindi.pdf` — are working documents about the
paper, not parts of it.

## 3. Where the numbers come from

Every number in the manuscript must exist in `MASTER_NUMBERS.csv`, which is
regenerated from the released result files and never edited by hand. Figures quoted
from other papers live in `LITERATURE_NUMBERS.csv`, each with the URL it was verified
from. `scan.py` reads both and reports any number in the text that is in neither.

**The registry row count changes on every rebuild.** Documents that quote it are
synchronised automatically:

```
python3 tools/check_registry_count.py --fix results/MASTER_NUMBERS.csv <docs>
```

A stale row count was reported as an error three times before this was automated.

## 4. One command decides whether it is green

```
python3 tools/preflight.py
```

No argument is needed: the manuscript sources live in the repository, at
`manuscript/`, so a fresh extract of the release reproduces the verdict on its own.
An earlier layout kept them outside the repository, which meant an extracted package
could run only the five checks that touch code and reported the other six as missing
files — a reviewer was being handed a claim rather than a check. Pass a directory to
override.

**Building the audit bundle.** `python3 tools/snapshot.py` writes one zip holding
the manuscript, the registry and every released table, all seven figures, the whole
of `src/`, `tools/` and `tests/`, the audit history, and this build's own preflight
and test output captured at the moment the snapshot was made. It is stamped with the
manuscript's own build id, and its manifest gives the three-step test for whether a
given copy belongs to that build. Snapshots were assembled by hand until
25 September 2026 and each was missing something the audit of it then needed; that
is what the script exists to stop.

Twenty-five checks, one verdict. This list is the one `tools/preflight.py` prints, and `tests/test_pipeline.py` fails if the two ever disagree:

| Check | What fails it |
|---|---|
| tests | any test in `tests/`. The count below is of `test_pipeline.py` alone — any of the 76 tests there — and is held to the suite by `test_the_reproducibility_page_states_the_size_of_the_suite_it_describes`, which fails if the two drift apart. The builders' own suites (`test_build_docx.py`, `test_build_highlights.py`, `test_check_submission_package.py`) run in the same command and are not in that count |
| registry | the registry cannot be rebuilt from the result files |
| row counts | a document claims a registry size the registry does not have |
| scan | a number in a section is in neither registry |
| cross-references | a "Section N" points at a section that does not exist |
| front matter | abstract words, highlight characters or keyword count out of range, against the limits quoted in `tools/journal_requirements.json` |
| release | `ALL_FOLDS.csv` does not hold exactly 750 folds |
| duplicate keys | two registry rows share a (section, claim) key |
| manuscript | the manuscript cannot be rebuilt from the sections, or a Hindi gloss survives the strip |
| manuscript scan | a number in the assembled manuscript is in neither registry |
| figures | a figure cannot be redrawn, or plots a value the registry does not hold |
| figure placement | a figure is not embedded at all, is embedded twice, has come apart from its caption, or is drawn somewhere other than the section that first cites it |
| print ready | a paper figure has no vector PDF, has a PDF that is only a bitmap in a wrapper, or has a PNG whose actual resolution is not the one `config.py` declares |
| provenance | the figure-to-registry trail cannot be regenerated |
| master file | the single-source-of-truth file cannot be regenerated from the registry |
| generated files | a file written by a tool has been edited by hand, so the next regeneration will discard the edit |
| withdrawn | a phrase the paper has retired has reappeared (`manuscript/WITHDRAWN.md`) |
| released scores | a released probability file does not come from the execution the paper tabulates, undisclosed |
| ranking invariance | a subject-averaged ROC-AUC or PR-AUC moves at the reported precision after out-of-subject Platt scaling |
| table marks | a table's emphasised cells are not the ones its caption's rule selects |
| literature | the borrowed-number registry disagrees with `REFERENCES.md`, or a row has no source |
| multiplicity | the released multiplicity table disagrees with a fresh run, a Holm ceiling is not what Section 6.5.1 states, or a one-family BY survivor comes from outside the prevalence family |
| split map | a section, table or figure exists that nobody has classified as main-article, supplementary or repository material, or something leaves the article without saying what the article keeps (`tools/split_map.json`) |
| placeholders | *reports* — does not fail — every `<placeholder>` still in the text |
| decisions | *reports* — does not fail — which pre-submission item is still pending |

The last two report rather than fail, and for the same reason: neither is a
property of the paper. A placeholder means somebody is about to fill something in,
and an unmade decision means two people have not yet agreed on something that is
theirs to agree on. Both are printed on every run, because the alternative to
printing them is remembering them.

What is not the paper's to settle, plus the one check it cannot run without a GPU environment, have their own command and their own page:

```
python3 tools/check_submission_ready.py
```

Each author decision is confirmed by deleting the draft note that says it is not —
so there is no second file to keep in step, and nothing can be marked done by
accident. `manuscript/DECISION_SHEET.md` sets them out, including what each CRediT
role means and the two roles the proposal considered and declined.

That command also answers two items that are nobody's decision but age in the same
way. The training smoke test is the only test that builds real models, and it needs
TensorFlow, so the check reads the record of its last pass and reports the item
open if that pass predates the last change to the training code. The journal's
front-matter limits are quotations in `tools/journal_requirements.json` carrying
the date the guide for authors was last read at the source; the check reports the
item open once that reading is more than 180 days old. Neither can establish that
the answer is still right — only that somebody looked recently enough for the
answer to be evidence rather than recollection.

**Final submission package audit.** The four files that go to the journal are built
from this repository but are not part of it -- `docx/` is ignored, for the same reason
`pdf/` is -- so no check that runs here can see them. Build them and check them
together, on the day:

```
python3 tools/build_docx.py
python3 tools/build_highlights.py
python3 tools/build_pdf.py
python3 tools/build_pdf.py --supplementary
python3 tools/check_submission_package.py
```

The gate is `PACKAGE READY  (10 of 10 checks passed)`. It checks that all four files
exist under the naming convention, that every one carries the build id the manuscript
currently stamps itself with, that the .docx still holds every table, image and
non-ASCII character the manuscript does, that the highlights are this manuscript's and
within the guide's quoted limits, that every supplementary item the article cites is in
the supplement with its caption, that no placeholder survives into either built
document, and that no two words are printed on top of each other.

That last one is there for a reason. On 7 October 2026 the supplementary PDF printed
"DeepConvNet8,212" -- a model name over the next column's number -- eight times across
two tables, and every check in this repository passed on that file. It was found by a
person reading it. A check only a person can perform is a check that will eventually
not be performed.

It is deliberately NOT part of `preflight.py`. Preflight checks the repository and
runs on every change; this needs four built artefacts that the repository does not
keep, and making them a precondition of the daily check would couple the two for no
gain. It is a pre-submission step, and it is written down here so that it is a step
rather than an intention.

## 5. What is still open

| | Item | Whose decision |
|---|---|---|
| 🟠 | Supplementary structure: whether Tables S5, S2 and S4 each get a Supplementary Note of their own. They follow Note 3 without second-level headings of their own, although they concern different analyses; Note 3 presents Table S3 as its coverage table. A structural question, not a demonstrated error. The numbering is not to be changed before it is answered. `DECISION_SHEET.md` §5 | Both authors |
| 🟠 | `CITATION.cff` leaves the article DOI, volume, pages and both ORCID iDs empty because none of them exists yet. Fill in on acceptance. | Corresponding author |
| 🟠 | Structure: eight sections, or nine with Architectures separate (72 cross-references, checker exists) | Supervisor |

**Which figures the submission carries, and in what order, is settled** — this row was
still listed as open until 7 October 2026, which was wrong by then. Six figures in the
article and one in the supplement, each placed once beside its caption in the section
that first cites it, the article's running 1 to 6 in citation order; the eighth file,
`fig6_code_structure`, is the repository's own module diagram and not a paper figure.
The table in section 8 lists all of them, `tools/check_figure_placement.py` checks the
placement, `tools/check_print_ready.py` checks the artwork against the guide's
quotations, and `figures/PROVENANCE.txt` traces every plotted value to the registry.
None of that was in doubt; only this row said otherwise.

Settled on 18 September 2026, by the corresponding author:

**Acknowledgements.** "The work is conducted and supported by the Brain–Computer
Interface Laboratory at Computer Science and Engineering Department, Maulana Azad
National Institute of Technology Bhopal, India", followed by the existing
acknowledgement of the DD-Database depositors. "Supported" there means facilities,
not a grant, and does not contradict the funding statement.

**Funding.** None received. The journal's prescribed no-funding sentence is used
verbatim. The CONICET and Universidad Nacional de San Juan grants recorded in the
dataset deposit funded the *data collection* and are the depositors', not ours.

**Title.** "Calibration of Four-Channel EEG for Driver Drowsiness Detection: A
750-Fold Leave-One-Subject-Out Study", settled 3 October 2026. Four earlier drafts
are kept in `ABSTRACT.md`, and `SUPPLEMENTARY.md` carries the same title as the
article. The one it replaced, "Calibration matters for trustworthy EEG-based driver
drowsiness detection", was dropped because "trustworthy" invited a reading the paper
does not support: this study measures probability reliability, not clinical
trustworthiness. The montage is named because the study uses four of the deposit's
seven channels, and "subject-independent" was not added alongside
"leave-one-subject-out", which already says it. The present title asserts only what
the results support.

**AI declaration.** Omitted, on the author's explicit instruction. The section
carrying Elsevier's template wording has been removed and the submitted article
declares nothing on this point.

This last one is recorded rather than argued, because it is the author's decision
and it has been made. What the record should show, so a later reader is not left
reconstructing it: an AI assistant was used in this project to draft and edit
manuscript text and to write analysis and figure-generation code, and Elsevier's
policy asks for disclosure of generative AI used in the *writing* process. If the
decision is revisited, the template is:

> During the preparation of this work the author(s) used `<NAME OF TOOL>` in order
> to `<REASON>`. After using this tool/service, the author(s) reviewed and edited
> the content as needed and take(s) full responsibility for the content of the
> published article.

with `<REASON>` as either "draft and edit sections of the manuscript text" or
"draft and edit sections of the manuscript text and to write analysis and
figure-generation code". Restoring the section into `ABSTRACT.md` is a two-minute
edit.

`[P5]` and `[P6]` were on this list until 18 September 2026 and are now verified;
`[P5]` was wrong and changed. See §10.

## 6. What the release contains, exactly

Stated precisely because the data-availability statement is a promise.

| | Released | Recomputable from the release |
|---|---|---|
| Per-fold results, all 750 folds | yes | — |
| Every table and significance test | — | yes, in seconds, no GPU, no recordings |
| Arm A per-window probabilities | yes, 15 files, 3.2 MB | — |
| Arm A calibration | yes | **yes, from raw scores** — a test refits all 150 calibrators and asserts the published summary is reproduced |
| Arm B and C calibration, thresholds | summaries only | no — needs re-running training, for which the code is provided |
| The EEG recordings | no | from Dryad, CC0 1.0 |

## 7. Measurements that back specific sentences

Two claims in the manuscript were checked by measurement rather than argument, after
review pointed out they rested on theory alone. Both are regenerated by released
tools and registered in `MASTER_NUMBERS.csv`.

**Platt scaling preserves the ranking.** True only if every fitted slope is positive.
`tools/check_monotonicity.py` refits all 150 Arm A calibrators: all 150 slopes are
positive (0.3243 to 1.3312); ROC-AUC moves by at most 4 × 10⁻⁵ and PR-AUC by at most
0.0034; the residual is the ε-clip before the logit tying scores together, on 10 folds
and at most 95 ties on one. The manuscript accordingly claims *unchanged at the
reported precision*, not algebraic invariance.

**Isotonic regression can cost ranking.** On the same 150 folds it lowers ROC-AUC on
123 and PR-AUC on 144, and cuts the median distinct scores per fold from 926 to 25.

## 8. The figures

Seven drawn by `python3 -m src.figures` into `figures/` as vector PDF for the journal
and PNG for reading, plus one drawn by `python3 tools/code_diagram.py` that is not
part of the paper.

**The PDF is the file that is submitted, and this is the reason.** A PDF has no
resolution, so the guide's raster minima — 300 dpi for photographs, 1000 dpi for
bitmapped line drawings — do not apply to it, and Elsevier asks for vector artwork
first. The PNG is rendered at `config.FIGURE_DPI_RASTER`, **360 dpi** on the
corresponding author's instruction of 30 September 2026, which puts the widest figure
at about 2,630 pixels. That clears the photograph minimum and does **not** clear the
1000 dpi line-drawing minimum, whose single-column width requirement is 3,543 pixels:
reaching it would need roughly 495 dpi at this printed width, and the full-page
requirement of 7,480 pixels would need about 1,045. None of that is a defect while
the PDF is what is submitted; it would become one the moment a PNG were sent in a
PDF's place, which is why `config.py` states the number with its reason and
`tools/check_print_ready.py` prints the comparison on every run. **Every value is looked up in `MASTER_NUMBERS.csv` by its claim;
none is typed into the plotting code.** `lookup()` raises on a missing claim, so a
figure cannot be drawn from a number the paper does not contain, and a renamed
registry row breaks the draw instead of producing a quietly wrong picture.

**Numbered on 19 September 2026 in order of first citation**, and the files are
named for their place in the paper rather than the order they were written in.

**Corrected on 30 September 2026, because that numbering was not in order of first
citation.** The architecture drawing is cited in Section 5.3 and every other figure
in Section 7, so the first figure a reader met was the one numbered 6. Every sentence
about the numbering was true and the page was wrong, which is the same failure as a
caption with no picture under it. The figures were rotated into true appearance order
— the architecture drawing became Figure 1 and the other five each moved up one — by
`python3 tools/renumber_figures.py`, in one pass over citations, captions, alt text,
file names, the provenance listing, the split map and the tests, with the two
sentences that record the *previous* numbering protected from rewriting so that this
history stays readable. `tools/check_figure_placement.py` now fails if the numbers
are ever again out of appearance order, so this cannot recur quietly.

| | File | Where |
|---|---|---|
| Figure 1 | `figure1_cnn_against_cnn_bilstm` | Architectures §5.3 |
| Figure 2 | `figure2_study_design` | Results, opening |
| Figure 3 | `figure3_accuracy_against_recall` | Results §7.3 |
| Figure 4 | `figure4_subject_against_seed_spread` | Results §7.4 |
| Figure 5 | `figure5_brier_partition` | Results §7.5, and Discussion §8.5 |
| Figure 6 | `figure6_recalibration` | Results §7.6, and Discussion §8.6 |
| Figure S1 | `figureS1_overview` | Supplementary |
| — | `fig6_code_structure` | Repository README only; not a paper figure |

**Figure 1 stays in the main article**, on the corresponding author's decision of
30 September 2026. An earlier draft of `tools/split_map.json` proposed moving it to
the supplementary material as Figure S2 to hold the article to five figures; that
proposal is withdrawn. The CNN baseline against the CNN-BiLSTM is a named
contribution, and the drawing is the one place a reader sees what the recurrent block
replaces. The article carries six figures and one supplementary figure.

Figure S1 is supplementary on a scientific ground, not to save space: its
reliability panels can be drawn only for Arm A, the one construction whose
per-window scores are released, and this paper reports findings where they
replicate on all three.

Colour does one job, polarity — worse or better than the constant predictor — using
the blue/red diverging pair, validated for colour-vision deficiency. Identity is
never colour alone: the constructions are marker shapes, and where a figure
emphasises particular lines those lines are also drawn thicker, so the figures read
in greyscale and in print.

**Redesigned 19 September 2026.** All five main figures were redrawn to one design
language: printed at 7.16 in, the double-column width, so nothing is scaled at
typesetting; 5.6–7.6 pt type throughout; panel labels (a)(b)(c) wherever a figure
has panels; no decorative illustration. Three defects were removed in the process
rather than styled over — Figure 5's three constructions overlapped on a single row
and are now offset within it; Figure 6's labels overprinted one another and now
name each line at both ends; and Figure 6 read its values from
`results/<arm>/calibration_summary.csv` while the table beside it read them from
the registry, so the figure now goes through the registry like every other. **No
value, statistic, or claim changed.**

`figures/PROVENANCE.txt` lists **every value every figure plots, with the registry
claim it was read from**. It is generated, not written: `tools/figure_provenance.py`
instruments the lookup and records each access while the figures are drawn. If a
number is on a chart it is on that list, and if it is on that list it is a row of
`MASTER_NUMBERS.csv`.

The one place a figure goes past the registry is the three reliability panels of
Figure S1, which bin the released per-window scores directly. That is stated at the
foot of the provenance file, with the files they read.

Two tests go beyond redrawing them. One asserts the partition in Figure 5 is the
same three-against-two split the Results section claims, on each construction; the
other asserts that the two most accurate architectures really are the two with the
lowest recall, which is what Figure 3 is arranged to show. A figure that stopped
matching its own sentence would fail the suite rather than be noticed in proof.

## 8a. The tables

**Numbered 1 to 8 on 19 September 2026**, and each is cited by number at the point
it is discussed. Before that, thirty-six tables carried no numbers at all and none
was cited.

| | Where | Contents |
|---|---|---|
| Table S1 | Supplementary | Windows per subject before any construction rule |
| Table 1 | Methodology §4.4 | The three constructions and the references each implies |
| Table 2 | Architectures §5.1 | The five architectures and their parameter counts |
| Table 3 | Results §7.1 | Subject-averaged ROC-AUC and PR-AUC, all three arms |
| Table 4 | Results §7.3 | Pooled confusion matrices, merged across arms |
| Table 5 | Results §7.5 | Pooled Brier against each class-prior reference |
| Table 6 | Results §7.6 | ECE and Brier, raw and after each recalibration, merged |
| Table S3 | Supplementary | Which construction each analysis covers |

Three groups of three per-arm tables were merged into Tables 5 and 7 with an Arm
column. **The merge moved values; it did not change any.** The rows were extracted
from the existing tables programmatically rather than retyped, and the per-arm
originals are reproduced in the supplementary material.

Table 1 merges what were two overlapping tables — the construction rules in
Methodology and the reference values in the Results overview — so the three
constructions are described once and Results refers back to them.

## 9. Corrections are data, not memory

`manuscript/WITHDRAWN.md` lists every phrase this paper has retired, with the reason.
`tools/check_withdrawn.py` fails if any of them reappears — in a section file, in the
assembled manuscript, or in a PDF handed to it, since it reads both formats. A phrase
quoted inside quotation marks or struck through is being displayed rather than
asserted and does not count; the paper documents several of its own corrections that
way on purpose.

This exists because the same handful of corrections was reported four times, each
time from a superseded copy, and "that is already fixed" is an assertion. Now it is
a command:

```
python3 tools/check_withdrawn.py manuscript/WITHDRAWN.md <any .md or .pdf>
```

## 10. The last two references, and what checking them found

`[P5]` and `[P6]` were the two entries in `REFERENCES.md` still carrying a `VERIFY`
marker. Both are now checked, and one of them was wrong.

**`[P6]` Brier (1950) was right.** *Monthly Weather Review* 78(1), 1–3, DOI
`10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2`. Two catalogue records agree on
every field, and the DOI string itself carries volume 078 and first page 0001. The
publisher's own page refuses automated requests, which is noted in the entry rather
than papered over.

**`[P5]` Platt was wrong in two fields.** The draft cited *Probabilistic outputs for
support vector machines and comparisons to regularized likelihood methods* (1999).
The chapter actually printed at pp. 61–74 of *Advances in Large Margin Classifiers*
is titled **Probabilities for SV Machines**, and the volume is **2000**. The longer
title is how the work is indexed as a 1999 preprint, and it is what most of the
literature cites — which is exactly why the error is easy to inherit and hard to
notice. The entry now gives the printed chapter, with the catalogue records it was
checked against and a note that the start page comes from the contents list while
the end page follows from the next chapter beginning at p. 75.

No sentence in the paper changed: the body cites this work only as `[P5]`. That is
the argument for tag-based citation in a draft — a reference can be corrected
without touching prose, and a wrong year cannot hide inside a sentence.

`REFERENCES.md` states, for every entry, the URL it was verified from, so the next
reader checks a record rather than a habit.
