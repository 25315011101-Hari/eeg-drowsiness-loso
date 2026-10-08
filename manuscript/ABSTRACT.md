<!-- not-for-submission:start -->
# Front matter — draft 2 (19 September 2026)

Written last, from Results draft 4 and the Introduction. Formatted to the
Biomedical Signal Processing and Control guide for authors: **abstract at most
250 words; highlights 3–5 bullets of at most 85 characters including spaces; 1–7
keywords; a data availability statement is mandatory.**

The limits are not restated here as remembered numbers. They live in
`tools/journal_requirements.json`, each beside the sentence of the guide it was
taken from and the date that guide was last read at the source, and
`tools/check_frontmatter.py` reads them from there. An earlier version of this
paragraph also said the abstract must be **unstructured**; the guide does not say
that. It asks for one "concise and factual" abstract of at most 250 words and is
silent on structure. This abstract is narrative because a narrative abstract
suits the argument, which is a choice and is no longer recorded as a rule.

This heading and the paragraph above are editorial. They are stripped from the
assembled manuscript, which begins at the title.
<!-- not-for-submission:end -->

> **हिंदी।** Journal की शर्तें खुद उसकी guide for authors से लीं — abstract 250 शब्द तक,
> highlights 3–5 bullets और हर एक 85 characters तक, keywords 7 तक। हर limit अपने
> source वाक्य के साथ `tools/journal_requirements.json` में रखी है, और गिनती script से
> जाँची गई है।

## Title

**Calibration of Four-Channel EEG for Driver Drowsiness Detection:
A 750-Fold Leave-One-Subject-Out Study**

Hari Singh Jatav ^a^, Mitul Kumar Ahirwal ^b,^\*

^a^ Centre for Artificial Intelligence, Maulana Azad National Institute of
Technology Bhopal, Bhopal, Madhya Pradesh 462003, India

^b^ Department of Computer Science and Engineering, Maulana Azad National Institute
of Technology Bhopal, Bhopal, Madhya Pradesh 462003, India

\* Corresponding author. E-mail address: mkahirwal@manit.ac.in (M. K. Ahirwal)

<!-- not-for-submission:start -->
*The title page, settled 4 October 2026. The guide asks for "the given name(s) and
family name(s) of each author", affiliations "using a lower-case superscript letter",
each affiliation's "full name and postal address, including the country name", a clear
indication of who handles correspondence, and the corresponding author's e-mail, which
is published. It asks for no telephone number, and it does not say whether the title
page is a separate file or part of the manuscript, so it is here.*

*Four things were decided rather than copied. Titles ("Dr.") and designations
("Associate Professor") are not part of a name and are left out; so is the scholar
number, which the guide does not ask for. The street line "Link Road No. 3, Near Kali
Mata Mandir" was offered and declined: it came from a district portal rather than from
the institute, and an unverified landmark in a published affiliation is a worse risk
than a short address — the institute's own page gives "MANIT Bhopal, Bhopal, Madhya
Pradesh 462003, India". The first author's e-mail is omitted because only the
corresponding author's is required. The superscripts are written as markdown
superscript rather than as the characters ᵃ and ᵇ, so that they typeset as superscripts
rather than depending on a font having those two glyphs.*

*Chosen by the corresponding author on 3 October 2026. The montage is named because
the study uses four of the deposit's seven channels, and "subject-independent" was
dropped as a tautology beside "leave-one-subject-out". The journal's guide states no
title length limit and no capitalization rule, so the case above is a choice, not a
requirement (tools/journal_requirements.json, not_enforced_here.article_title).*

*Previous drafts, kept in case the guide prefers one:*

- **Calibration matters for trustworthy EEG-based driver drowsiness detection: a
  750-fold leave-one-subject-out study** — carried from 18 September to 3 October 2026

- **Trustworthy EEG-based driver drowsiness detection needs calibration, not
  accuracy: a 750-fold leave-one-subject-out study**
- **Ranking quality and probability reliability are separable in EEG
  driver-drowsiness detection: a three-construction, leave-one-subject-out study**
- **Accurate but unreliable: probability calibration in EEG-based
  driver-drowsiness detection under leave-one-subject-out evaluation**
<!-- not-for-submission:end -->

## Abstract

Reported accuracies for EEG-based driver-drowsiness detection routinely exceed 90 %,
yet cannot be interpreted without the class ratio and the majority-class baseline.
We evaluate EEGNet, ShallowConvNet, a one-dimensional CNN, DeepConvNet and a
CNN-BiLSTM on a four-channel montage under leave-one-subject-out cross-validation with
five seeds, across three window-set constructions of the same ten recordings, giving
750 folds. A finding is claimed for all three only where it replicates on all three;
the three are cells of a two-by-two design of trimming against balancing, giving two
single-factor contrasts.

Accuracy orders these architectures against recall. On all three, the two most
accurate are exactly the two with the lowest recall; the accuracy-recall rank
correlation is −1.000, −0.900 and −0.600, reaching the nominal level on the first
alone. On one, the only architecture exceeding the 92.73 % always-alert
baseline misses 338 of 673 drowsy windows.

Ranking quality and probability reliability separate. Against the Brier score of a
constant predictor emitting the class prior, three of the five (including EEGNet,
the highest subject-averaged ROC-AUC everywhere) score worse, and the partition is
identical on all three. A per-fold logistic recalibration fitted on the
other nine subjects brings every measured architecture below the reference on all
three, leaving subject-averaged ROC-AUC and PR-AUC unchanged at the reported
precision where released scores permit measuring it (Arm A). EEGNet improves its
calibration error on all three, leads all twelve paired comparisons and separates in
eleven; no other pair separates on ROC-AUC. All 750 per-fold results and the
pipeline are released.

## Highlights

- Five EEG models, leave-one-subject-out, three window constructions, 750 folds
- The two most accurate models are exactly the two with the lowest recall
- Three of five models score worse than a constant predictor of the class prior
- Recalibration closes the gap; ranking unchanged where measured (Arm A)
- All 750 per-fold results and the full analysis pipeline are released

## Keywords

Electroencephalography; driver drowsiness detection; leave-one-subject-out
cross-validation; probability calibration; class imbalance; convolutional neural
networks; reproducibility


## Declaration of competing interest

> The authors declare that they have no known competing financial interests or
> personal relationships that could have appeared to influence the work reported in
> this paper.

<!-- not-for-submission:start -->
*Amend if any author has a relationship to disclose. The journal requires this to
be submitted through its declarations tool as well as appearing in the article.*
<!-- not-for-submission:end -->

## CRediT author contribution statement

<!-- not-for-submission:start -->
The journal requires each author's contribution to be identified using CRediT
roles. Confirmed by the corresponding author on 1 October 2026:
<!-- not-for-submission:end -->

> **Hari Singh Jatav:** Conceptualization, Methodology, Software, Investigation,
> Data curation, Writing – original draft, Visualization.
> **Mitul Kumar Ahirwal:** Conceptualization, Methodology, Validation, Writing –
> review & editing, Supervision.

<!-- not-for-submission:start -->
*Four roles are claimed by neither author, each on the corresponding author's
decision of 1 October 2026. **Resources** and **Project administration** were
considered and declined: the laboratory's facilities are recognised in the
acknowledgements, which is where institutional support belongs, and supervision
already covers the guidance that was given, so neither role describes a
contribution an author made. **Funding acquisition** is empty because no funding
was received. **Formal analysis** is left unclaimed rather than assigned: CRediT
does not require every applicable role to be used, and an unused role understates a
contribution where a misassigned one would misstate it. A role nobody performed is
not a courtesy, so none of the four is listed.*
<!-- not-for-submission:end -->

## Acknowledgements

<!-- not-for-submission:start -->
Mandatory as its own section immediately before the reference list. It may not be
placed on the title page or in a footnote.
<!-- not-for-submission:end -->

> The work was conducted and supported by the Brain–Computer Interface Laboratory,
> Department of Computer Science and Engineering, Maulana Azad National Institute
> of Technology Bhopal, India. The authors acknowledge the depositors of the
> Drivers Drowsiness Database for making the recordings publicly available.

<!-- not-for-submission:start -->
*The first sentence is the corresponding author's own wording. The second is
retained because the entire empirical content of this paper rests on a dataset
someone else collected and released; acknowledging that is not a courtesy.*
<!-- not-for-submission:end -->

<!-- not-for-submission:start -->
*"Supported" here describes laboratory facilities, not a grant. It does not
contradict the funding statement below, and a copy-editor should not reconcile
the two by changing either.*
<!-- not-for-submission:end -->

## Funding

<!-- not-for-submission:start -->
The journal prescribes the wording, including for the no-funding case. No funding
was received for this research, so the prescribed no-funding sentence is used
verbatim:
<!-- not-for-submission:end -->

> This research did not receive any specific grant from funding agencies in the
> public, commercial, or not-for-profit sectors.

<!-- not-for-submission:start -->
*Note that the dataset deposit records CONICET and Universidad Nacional de San Juan
as funders of the **data collection**. That is the depositors' funding, not this
study's, and must not be reported here as ours. The sentence above is therefore
correct as it stands and must not be softened to mention them.*
<!-- not-for-submission:end -->

## Notes for the next pass — not part of the paper

- **AI declaration: omitted, on the corresponding author's explicit instruction
  (18 September 2026).** The section that carried Elsevier's template wording has
  been removed, so the submitted article declares nothing on this point. The
  decision is recorded here and in `REPRODUCIBILITY.md` §5 rather than argued
  again: it is the author's to make and the author has made it. What the record
  should show, so that it can be revisited without reconstructing anything: an AI
  assistant was used in this project to draft and edit manuscript text and to
  write analysis and figure-generation code, and Elsevier's policy asks for
  disclosure of generative AI used in the *writing* process. Restoring the section
  is a two-minute edit; the template wording and the two candidate completions are
  in the repository history and in `REPRODUCIBILITY.md` §5.
- **Title, settled 18 September 2026.** "Calibration matters for trustworthy EEG-based
  driver drowsiness detection" is the author's wording, and it is the better of the
  drafts for a specific reason worth keeping on record. The previous draft said
  "needs calibration, **not accuracy**", which claimed more than the paper argues:
  the paper's case is that accuracy is uninterpretable without the class ratio and
  the majority-class baseline, and that it can order architectures *against* recall
  — not that accuracy is worthless. "Calibration matters for …" asserts what the
  results support and leaves a reviewer nothing to argue with. The three earlier
  drafts are kept above.
- **Capitalisation.** The title is in sentence case with the subtitle capitalised
  after the colon, which is how this journal's recent articles are printed
  (checked against its ScienceDirect listing, 18 September 2026). The author wrote
  it in full title case; if the guide prefers that, it is a formatting change only.
- The abstract deliberately does not quote ROC-AUC figures. There is room for
  one, but the paper's contribution is the separation and the recalibration, not
  a leaderboard position, and an abstract that leads with 0.884 invites the
  reader to compare it against the 94 % accuracies the introduction is arguing
  against.
- "Eleven of twelve paired comparisons" is stated without the p-values; the
  exact values are in Section 7 and in the registry.
- A graphical abstract is optional and not drafted. If one is wanted, the
  natural figure is the three-arm Brier partition against the class-prior
  reference — it carries the central claim in one picture.
- **No front-matter decision is outstanding.** An earlier version of this list
  ended by calling the AI declaration the last one awaiting the guide's sign-off.
  It is not awaiting anything: it was decided on 18 September 2026 and the decision
  is recorded in the first bullet above. The line is corrected rather than deleted
  so that the record shows the question was closed, not forgotten.
- **What the guide's limits rest on.** `tools/journal_requirements.json` carries
  the abstract, highlight and keyword limits as quotations with the date the guide
  was read, and `tools/check_submission_ready.py` reports the item as open once
  that reading is more than 180 days old. Re-reading the guide immediately before
  submission is therefore a listed pre-submission item rather than an intention.
