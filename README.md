# EEG driver-drowsiness detection under leave-one-subject-out evaluation

Code for the study of five convolutional and recurrent-convolutional
architectures on the four-channel DD-Database montage, evaluated with
leave-one-subject-out cross-validation and five seeds on **three constructions
of the same ten recordings** — 750 folds in total.

Hari Singh Jatav, Centre for AI, Maulana Azad National Institute of Technology,
Bhopal. Guide: Mitul Kumar Ahirwal.

---

## What this repository is for

Two different readers want two different things from it, and they need very
different amounts of hardware.

**A reviewer who wants to check the numbers** needs four packages and about two
minutes. The released result files already contain every per-fold metric, so the
whole analysis — tables, statistics, registry — reruns without a GPU and without
the recordings:

```bash
pip install numpy pandas scipy scikit-learn
python run_all.py --from aggregate --result-dir results
```

**Someone who wants to rebuild the study from the recordings** needs the EDF
files, `mne`, TensorFlow and a GPU, and about three hours per arm:

```bash
pip install -r requirements.txt
git clone https://github.com/vlawhern/arl-eegmodels arl && export PYTHONPATH=$PWD/arl
python run_all.py --edf-dir /path/to/dd-database
```

`run_all.py --dry-run` prints the plan without doing anything.

---

## The three arms

The same ten recordings are windowed three ways. Two choices are involved —
whether recordings are trimmed to a common length, and how the class ratio is
handled — and the three arms are three of their four combinations.

| Arm | Trimming | Balancing | Windows | Drowsy | Prevalence | Brier reference |
|---|---|---|---|---|---|---|
| A | to the shortest recording | every drowsy window kept | 9,260 | 770 | 8.32 % | 0.0762 |
| B | none | the subject's own ratio | 9,920 | 688 | 6.94 % | 0.0645 |
| C | to the shortest recording | the subject's own ratio | 9,260 | 673 | 7.27 % | 0.0674 |

**Arms A and C differ in exactly one factor**, so their comparison isolates the
balancing rule; **Arms B and C** both preserve each subject's class ratio and differ
only in trimming, so their comparison isolates trimming. The fourth cell —
untrimmed with every drowsy window kept — was not run.

The Brier reference is π(1 − π), the Brier score of a constant predictor that
ignores the input and always emits the class prior. An architecture *above* it
produces probabilities that are worse than that constant predictor. The
three-against-two partition of the five architectures about this reference is
the same on all three arms, and that is the study's central result.

Everything about an arm lives in one place, `config.ARMS`. Nothing else in the
repository hard-codes a window count, a prevalence or a reference value.

---

## Layout

```
config.py              every constant: paths, arms, protocol, references
run_all.py             the orchestrator; stages can be run singly or from a point
src/
  preprocess.py        EDF -> windowed .npz, with two independent checks
  models.py            the five architectures and their two input layouts
  train_loso.py        LOSO x 5 seeds, resume-safe, per-fold output
  calibrate.py         out-of-subject Platt and isotonic recalibration
  thresholds.py        out-of-subject threshold selection
  repro.py             compares two executions of the same arm
  aggregate.py         per-seed files -> ALL_FOLDS.csv, ALL_POOLED.csv
  stats.py             every statistic the paper reports
  registry.py          -> MASTER_NUMBERS.csv, the list of citable values
  scan.py              finds numbers in a draft that are not in the registry
  tables.py            emits the Results tables as markdown
kaggle/                the same pipeline as three notebook cells
tests/                 self-checks; no GPU, no EDF files, no trained model
```

Stage order, and what each one needs:

```
preprocess -> train -> aggregate -> calibrate -> repro -> registry -> tables
 (EDF, mne)   (GPU)    (seconds)    thresholds   (opt.)   (seconds)   (seconds)
```

`run_all.py --from aggregate` runs everything after the GPU stages; on the
released bundle it takes about twelve seconds.

---

## The decisions the code encodes

These are the places where a plausible-looking shortcut would change the
results, so they are enforced in code rather than left to discipline.

**Calibrators and thresholds are fitted out of subject.** For every
leave-one-subject-out fold a *separate* calibrator is fitted on the other nine
subjects of the same seed and applied to the held-out one — fifty calibrators
per architecture per arm. Fitting one calibrator on all the predictions at once
would leak the test subject into its own correction. `calibrate.py` and
`thresholds.py` both do it the same way.

**Paired tests use ten values, not fifty.** Folds from the same subject are not
independent, so every significance test operates on the ten subject-level
differences. The smallest p-value this can return is 2/2¹⁰ = 0.00195, and
several results in the paper sit exactly there. `stats.paired` takes subject
means; there is no code path that tests fifty folds.

**Subject-averaged and pooled are never mixed.** A subject-averaged value
weights each subject equally; a pooled value weights each subject by its window
count. Pooled recall exceeds subject-averaged recall by 0.13 to 0.25 for every
architecture on every arm, so a silent mixture would be a large error. Every
function in `stats.py` states which convention it uses, and `tables.py` labels
every column.

**Degenerate folds are kept.** A fold in which the model predicts no drowsy
window at 0.5 has F1 = 0 and balanced accuracy = 0.500 by construction. They are
common here — up to 20 of 50 for one architecture on Arm C — and dropping them
would silently improve every threshold-dependent number.

**False positives come from the recorded count, not a reconstruction.** A
fold's predicted-positive total is TP / precision, which is undefined whenever
precision is zero, and precision is zero for every degenerate fold — including
folds that predicted some windows drowsy and got all of them wrong. Recovering
false positives from the per-fold summaries therefore *under-counts* them, by up
to 17 windows per architecture on this data. `stats.pooled_confusion` takes them
from `ALL_POOLED.csv`, where they were counted directly from the predictions,
and marks the result `fp_source="recorded"`. Without that table it falls back to
the reconstruction and marks it `"reconstructed"`, which is a lower bound.

**Two executions are compared, not assumed identical.** `repro.py` refuses the
comparison if the validation-subject assignments differ anywhere, and flags any
architecture whose folds are all bit-identical — that means its rows were carried
over rather than re-run, and it must not be counted as evidence of
reproducibility. On this data that flag correctly excludes CNN and CNN-BiLSTM,
leaving the three architectures the paper says the check covers.

**Every number in the manuscript must be in the registry.** `registry.py`
recomputes `MASTER_NUMBERS.csv` from the raw result files; `scan.py` reads a
draft and reports any figure that is not in it. A clean scan does not mean the
draft is right — the scanner checks numbers, not claims — but a dirty one always
means something is wrong.

---

## Preprocessing, stated once

A **drowsy** window is the ten seconds *ending* at an annotated time mark, so it
covers the ten seconds before the mark. The deposit documents only that the files
carry time marks, so no annotation procedure is asserted here; the label is a
geometric relation to the mark and nothing more. Candidates that would overlap a window
already claimed are discarded, so no sample is used twice, and an event in the
first ten seconds of a recording yields nothing.

An **alert** window is grid-aligned and non-overlapping, and its centre must be
at least 20 s from every event.

The two are built differently, which is a design choice with consequences for
the prevalence and is reported as such in the paper rather than presented as a
neutral preprocessing step.

Filtering is a 50 Hz notch and a 0.5–40 Hz fourth-order Butterworth band-pass,
both applied zero-phase. Windows are cut at exact event times, so a causal
filter's group delay would shift the signal against its own label.

Trimming, where it applies, cuts from the *start* and keeps the end, and shifts
the event times by the same amount so a window still ends exactly at its event.

`preprocess.py` will not write a file unless two checks pass. The **internal**
check recomputes what the balancing step must produce from the counts that run
measured off the EDF files — it uses no outside numbers, so it cannot be
satisfied by a typo. The **reference** check compares against the counts in
`config.ARMS`, per subject as well as in total. A mismatch is a refusal to save,
and the per-subject table printed alongside it usually identifies the cause.

---

## Training protocol

Identical for every architecture and every arm: ten folds, one per subject; two
validation subjects drawn from the nine non-test subjects with a per-seed
`RandomState`; the other seven train. Z-score statistics and class weights come
from the training fold only. Adam at 1e-3, binary cross-entropy, batch 64, at
most 60 epochs, early stopping on validation PR-AUC with patience 8 and best
weights restored. Five seeds: 42, 1, 2, 3, 4.

No hyperparameter search was run. Each architecture is used at its published
configuration, which keeps the comparison controlled and avoids fitting a search
to ten subjects — at the cost that the comparison is between published
configurations rather than between architectures at their respective best.

The validation draw is made for **every** subject in order, including subjects
already finished on a resumed run. That is deliberate: it means stopping and
restarting cannot shift which validation pair a fold was given, so two
architectures are always compared on the same folds. `aggregate.py` checks this
across architectures and refuses to build the tables if it was ever violated.

The three ARL architectures want `(trials, channels, samples, 1)` and the two
written here want `(trials, samples, channels)`. `models.shape_for` and
`models.norm_axes` handle that, so the training loop never branches on the model
name. The ARL softmax head is replaced with a sigmoid: with `nb_classes=1` a
softmax over a length-one axis returns 1.0 for every input and nothing is
learned.

---

## Tests

```bash
python tests/test_pipeline.py                                   # no GPU needed
PYTHONPATH=/path/to/arl python tests/test_training_smoke.py     # ~1 min on CPU
```

`test_pipeline.py` covers the window geometry, the balancing arithmetic, the
internal check that gates every save, ECE and Brier on cases whose answers can
be worked out by hand, the threshold search, the confusion reconstruction, and
the scanner. It asserts the property the paper's calibration argument rests on: a
Platt fit with a positive slope is strictly increasing, so on distinct scores it
leaves ROC-AUC where it was, while isotonic regression is only weakly increasing
— its flat regions create ties, so it can lower ROC-AUC and never raise it.

That is a property of the map, not a claim about our folds, and the two are kept
apart deliberately. The implementation clips probabilities before taking the
logit, and a clip can tie scores that were distinct, so what recalibration did on
the released data is measured rather than deduced:

```bash
python tools/check_monotonicity.py        # refits all 150 Arm A calibrators
```

All 150 fitted slopes are positive (0.3243 to 1.3312); ROC-AUC moves by at most
4 × 10⁻⁵ and PR-AUC by at most 0.0034, with ties from the clip on 10 folds. The
paper therefore reports Platt-recalibrated ranking metrics as **unchanged at the
reported precision**, and makes no algebraic-invariance claim for either method.
A separate test asserts the part the argument actually needs — that every one of
those 150 slopes is positive.

`test_training_smoke.py` runs a real one-epoch LOSO on random data to prove the
training path works for both input layouts, that every architecture builds at
the study's parameter count, that no fold validates on its own test subject, and
that a resumed run neither repeats a fold nor moves a validation pair.

---

## Reproducibility, honestly

Arm B was executed twice under identical preprocessing, seeds and validation
assignments, differing only in GPU non-determinism. EEGNet reproduced to four
decimal places, with a largest single-fold ROC-AUC difference of 0.0002 and 27
of 50 folds identical to full floating-point precision. ShallowConvNet and
DeepConvNet did not: largest single-fold differences of 0.2219 and 0.2020, with
1 of 50 and 0 of 50 folds identical.

For those two architectures the standard deviation across five seeds
**understates** the true run-to-run uncertainty, because those seeds share a
single execution. Arm A was repeated for EEGNet only, and by a weaker check — that
earlier run did not record its validation-subject assignments — while Arm C was not
repeated at all, so their ± should be read the same way. Arm C additionally ran on a different GPU configuration (T4 × 2) from
Arms A and B, which is why it is not part of the repeated-execution check.

Setting a seed does not make a GPU run deterministic, and this repository does
not claim otherwise.

---

## Data and third-party code

The recordings are the DD-Database driver-drowsiness EDF dataset; they are **not
included here**, and the citation and licence terms in the paper's data
availability statement apply. Ten subjects, seven male and three female,
identified from the recording filenames. Two recordings per subject at 128 Hz,
channels O1, O2, C3 and C4.

`EEGNet`, `ShallowConvNet` and `DeepConvNet` come from the ARL reference
implementation at <https://github.com/vlawhern/arl-eegmodels>, used under its own
licence and cited in the paper. It is cloned separately rather than vendored, so
that the version used is whatever the clone command pins.

---

## What is released, and what it does and does not let you rerun

`results/` contains the two aggregate tables for all 750 folds, the per-fold
calibration and threshold files for the arms where they survived, the earlier Arm
B execution used by the reproducibility check, the generated tables, and the
registry.

It also contains **Arm A's per-window probability files** — 15 `probs_*.npz`, 3.2 MB,
three architectures across five seeds. Those are what make Arm A's calibration
recomputable rather than merely reported: a test refits all 150 calibrators from
those raw scores and asserts the published summary comes back.

Arms B and C have **no** probability files here. Everything in `stats.py`,
`registry.py`, `tables.py` and `repro.py` runs without them. `calibrate.py` and
`thresholds.py` need them, so on those two arms they report that none were found;
the published outputs are released as the per-arm `calibration_*.csv` and
`threshold_*.csv` files instead, and the registry reads those, so the manuscript
still scans clean.

Both file counts and the megabyte figure are measured from the release by
`src/registry.py` on every rebuild, not written down here from memory — which is
why this paragraph can be trusted and an earlier version of it, which said no
probability files were released at all, could not.

`aggregate.py` normally rebuilds the two tables from the per-seed files. Those
are not released either, so on the released bundle it verifies the existing
tables against the same checks instead of rebuilding them, and says so.

## One command decides whether the paper is green

```bash
pip install -r requirements.txt   # or the four analysis packages, plus pytest
python3 tools/preflight.py
```

Twenty checks, one verdict, no argument needed: the manuscript sources live in
this repository under `manuscript/`, so a fresh extract reproduces the verdict on
its own. It runs the test suite, rebuilds the registry from the released result
files, rebuilds the manuscript from its twelve section files, redraws all six
registry-driven figures, regenerates the figure-to-registry provenance trail, and
then checks the assembled text against the registry — every number in it must be a
row of `results/MASTER_NUMBERS.csv` or of `results/LITERATURE_NUMBERS.csv`, which
carries the URL each borrowed figure was verified from.

It also fails if a phrase the paper has **withdrawn** reappears. `manuscript/
WITHDRAWN.md` lists every retired claim with its reason, and
`tools/check_withdrawn.py` enforces the list against the section files, the
assembled manuscript and any PDF handed to it. A correction here is data, not
somebody's memory of a correction.

The one check that reports rather than fails is the placeholder check: it prints
every `<placeholder>` still in a submitted section, so the remaining author
decisions are a list instead of a hope.

`manuscript/REPRODUCIBILITY.md` is the status page — which file is the paper, what
each check enforces, and what is still open.

`pytest` is needed for the test check; the four analysis packages alone are enough
for everything else.

---

## Publishing this repository

The data-availability statement in the paper promises files a reader can fetch.
Until they can, the statement carries a placeholder address instead, and preflight
reports it on every run.

This directory is already a git repository with its first commit made, so
publishing is a push:

```bash
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

Then fill the address into the paper — all five files that carry it, in one
command, with the paper re-checked afterwards:

```bash
python3 tools/set_repository_url.py https://github.com/<user>/<repo>
```

It refuses an address with angle brackets left on it, one that is not `https://`,
and a `.git` clone address, because each of those has been written into a
published paper by somebody. It also removes the blocker notice from the
data-availability section, since a reminder to publish is not a sentence to
publish.

For a citable, permanent identifier — which Elsevier prefers, and which survives a
repository being renamed or deleted — archive a GitHub release on Zenodo and pass
the DOI as well:

```bash
python3 tools/set_repository_url.py https://github.com/<user>/<repo> --doi 10.5281/zenodo.<id>
```

**What no script can check, and you must, from a fresh clone:** that the
repository is public (open it signed out), that `results/ALL_FOLDS.csv` there
holds 750 rows, and that `python3 tools/preflight.py` passes there. The statement
promises all three.

---

## Licence and citation

The code, the released result files and the documentation are under the MIT
licence in [`LICENSE`](LICENSE) — **which the authors must confirm before the
repository is made public**; the file says so at its foot and the note is to be
deleted once the choice is settled. The licence covers neither the EEG recordings,
which are not distributed here, nor the ARL model implementations, which are cloned
from their own repository under their own terms.

[`CITATION.cff`](CITATION.cff) holds the machine-readable citation. It deliberately
leaves the article DOI, volume and pages empty, and the ORCID iDs commented out,
because the paper is not yet submitted and none of those values exists yet. They
are to be filled in on acceptance, not guessed now.

---

## Known limitations of this code

* Threshold selection was run on Arms A and C only. The Arm B probability files
  exist; the analysis was not completed on them.
* Per-window probability files were retained for three architectures per arm,
  so `calibrate.py` and `thresholds.py` cover three of five. The Brier partition
  in `stats.py` covers all five, because it needs only the pooled predictions.
* `preprocess.py` needs `mne` and the EDF files; there is no synthetic fallback,
  because a fallback that produced *some* windows would be worse than an error.
