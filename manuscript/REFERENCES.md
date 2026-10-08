# Verified reference list — draft 2 (18 September 2026)
<!-- not-for-submission:start -->

Every entry below was checked against the publisher, catalogue or repository record.
The URL each was verified from is given so that a co-author can re-check it in one
click. **Nothing in this list was written from memory.**

**No entry is marked `VERIFY` any longer.** The last two — `[P5]` Platt and `[P6]`
Brier — were checked on 18 September 2026, and `[P5]` was wrong: the chapter printed
at pp. 61–74 is *Probabilities for SV Machines* (2000), not the longer 1999 title
most of the literature copies. The entry records both forms so that a reader who
knows the work by its usual citation can see why this one differs.

<!-- not-for-submission:end -->
---

## Dataset

**[D1]** Orosco, L., Garcés, M. A., Cañadas Fragapane, G. E., Dell'Aquila, C.,
Iturrieta Gimeno, J. C., & Laciar Leber, E. (2023). *Drivers Drowsiness Database:
A collection of physiological signals during the use of a driving simulator
(DD-Database)* [Dataset]. Dryad. https://doi.org/10.5061/dryad.5tb2rbp9c
(mirrored at Zenodo, https://doi.org/10.5281/zenodo.8284057)

> Verified from https://datadryad.org/dataset/doi:10.5061/dryad.5tb2rbp9c and
> https://zenodo.org/records/8284057
>
> **Licence: CC0 1.0 Universal.** This is a public-domain dedication, so no
> permission is required to redistribute derived windows — worth stating in the
> data-availability section, because it removes the usual obstacle to releasing a
> reproducible pipeline.
>
> **Confirms, from the record itself:** 10 healthy volunteers, **ages 20–50**;
> two trials of two hours each per volunteer (40 h in total); 4 EEG, 2 EOG and
> 1 ECG channel; EDF format with a separate annotation file per recording
> carrying the time marks of drowsiness events; deposited 25 August 2023;
> funded by CONICET and Universidad Nacional de San Juan.
>
> **This closes the outstanding demographics item.** The age range 20–50 is now
> sourced, not assumed. Sex (7 male, 3 female) comes from the recording
> filenames, which the deposit's own file listing corroborates.
>
> The deposit names no accompanying journal article, so the dataset must be
> cited as a dataset. The same group's earlier methodological work is [R1].
>
> **Independently corroborated 17 September 2026.** The 2026 *Measurement* review
> [S3] cites this deposit as its reference [62], and its entry is the same one:
> "L. Orosco, M.A. Garcés, G.E. Cañadas Fragapane, C. Dell'Aquila, J.C. Iturrieta
> Gimeno, E. Laciar Leber, Drivers drowsiness database … 2023,
> http://dx.doi.org/10.5061/dryad.5tb2rbp9c, Version published Aug 25, 2023.
> Dryad Dataset." Six authors, year, DOI and deposit date all match this entry
> exactly, and that review — like this one — cites the deposit as a dataset rather
> than through a proxy paper. **The review is not an alternative citation for the
> data.** It is a secondary source that describes the dataset; [D1] remains the
> citation for the recordings, and [S3] is cited only where the review's own
> commentary is what is being used.

<!-- not-for-submission:start -->
### Does the dataset have a base paper? No.

**Checked four ways on 16 September 2026, and the answer is that DD-Database has
no accompanying journal article.** It is a standalone data deposit.

1. The Dryad landing page carries no "Related works", "Associated article",
   "Publication" or "Cited by" section. Its **Methods** heading exists but has no
   text beneath it.
2. The Zenodo mirror lists **Related Publications: none**.
3. No data descriptor for it exists in *Data in Brief*, *Scientific Data* or
   equivalent.
4. ~~"No paper using DD-Database was found in a targeted search."~~
   **Corrected 17 September 2026.** This fourth check was wrong, and it is the
   only one of the four that was. A 2026 review in *Measurement* — **[S3]** below
   — cites DD-Database and characterises it in a dataset table, so the deposit is
   not uncited in the literature. The **conclusion is unchanged**: [S3] is a
   review that cites the dataset, not a data descriptor of it, and it adds no
   information about the annotation protocol beyond the deposit's own abstract.
   What the correction removes is a claim this file should never have made — that
   a negative search result establishes absence. Checks 1 to 3 are checks of the
   deposit and of the data-descriptor journals; they stand. Check 4 was a search,
   and a search that finds nothing proves nothing.

The deposit's abstract, which is what the Dryad and Zenodo landing pages show, reads:

> "The DD-Database contains the physiological signals of 4 EEG channels, 2 EOG
> channels and 1 ECG channel as well as annotation files corresponding to 10
> healthy volunteers between 20 and 50 years old. The signals were collected
> during the use of a driving simulator under a protocol designed to induce
> drowsiness. The annotation files have the time marks of subject's drowsiness
> events. The experiment was carried out in 2 trials of 2 hours each, so the
> database contains 40 hours of information. This database is a contribution for
> the development and evaluation of algorithms and/or systems for detecting
> drowsiness in drivers. Data acquired during the use of a driving simulator and
> publicly available, are scarce."

**The README inside the deposit documents more than the abstract, and an earlier
reading of this record stopped at the abstract.** The package's `README.md` carries
Background, Methods, Data description and Usage Notes sections. Two sentences bear
directly on the labels:

> "Additionally, the volunteers were instructed to press an event button when they
> felt drowsy during the test."

> "The annotation files have the time marks (in seconds) of drowsiness. These marks
> correspond to the volunteer's drowsiness feeling, registered by the event push
> button."

The same README states a 16-bit A/D resolution, the EEG channels referred to A1 or A2,
that no hardware or software filter was applied to the raw signals, a sleep-restriction
protocol used to induce drowsiness, and that the file labelling carries volunteer
number, **gender**, trial number and channel -- the last being the source for this
paper's "seven male, three female". Read at the source on 2 October 2026.

**What follows for the manuscript.**

- **Cite the dataset as a dataset** [D1], not via a proxy paper. Elsevier
  supports data citation and a DOI-bearing Dryad deposit is a first-class
  reference. There is no "base paper" to omit, so nothing is missing.
- **The annotation procedure is documented in the deposit README, but not in a
  peer-reviewed descriptor.** The README records the event-button instruction and
  the meaning of the recorded time marks. What it does not establish is whether a
  mark is an episode's onset or a point within it. **This must be stated as a
  limitation**, because it bounds what the labels mean — and it must be stated
  accurately, because a reviewer who opens the package will find the procedure
  there.
- The deposit's last sentence — that publicly available simulator recordings are
  scarce — is quotable in the Introduction as the reason this dataset is worth
  working on despite its size.

<!-- not-for-submission:end -->
**[R1]** Garcés Correa, A., Orosco, L., & Laciar, E. (2014). Automatic detection
of drowsiness in EEG records based on multimodal analysis. *Medical Engineering
& Physics*, 36(2), 244–249. https://doi.org/10.1016/j.medengphy.2013.07.011

> Verified from https://www.sciencedirect.com/science/article/abs/pii/S1350453313001690
>
> **Correction to an earlier note in this file.** This paper was previously
> listed here as the dataset's "methodological predecessor", which overstated the
> link. It shares two authors with [D1] but **does not use the driving-simulator
> recordings at all**: it analyses 16 subjects from the MIT-BIH Polysomnographic
> Database, all male, aged 32–56, on channels C3-O1, C4-A1 and O2-A1 at 250 Hz,
> with sleep stages scored by experts under Rechtschaffen and Kales criteria. It
> reports 87.4 % and 83.6 % correct detection of alertness and drowsiness.
>
> Different data, different montage, different sampling rate, different
> annotation criterion. **Cite it only as prior work by the same group on EEG
> drowsiness detection — never as a description of DD-Database or its protocol.**

## Architectures evaluated

**[A1]** Lawhern, V. J., Solon, A. J., Waytowich, N. R., Gordon, S. M., Hung,
C. P., & Lance, B. J. (2018). EEGNet: a compact convolutional neural network for
EEG-based brain–computer interfaces. *Journal of Neural Engineering*, 15(5),
056013. https://doi.org/10.1088/1741-2552/aace8c

> Verified from https://pubmed.ncbi.nlm.nih.gov/29932424/ and arXiv:1611.08024.
> The reference implementation this study uses is the authors' own release at
> https://github.com/vlawhern/arl-eegmodels — cite both the paper and the
> repository, since the repository is what was actually run.

**[A2]** Schirrmeister, R. T., Springenberg, J. T., Fiederer, L. D. J.,
Glasstetter, M., Eggensperger, K., Tangermann, M., Hutter, F., Burgard, W., &
Ball, T. (2017). Deep learning with convolutional neural networks for EEG
decoding and visualization. *Human Brain Mapping*, 38(11), 5391–5420.
https://doi.org/10.1002/hbm.23730

> Verified from https://onlinelibrary.wiley.com/doi/full/10.1002/hbm.23730 and
> arXiv:1703.05051. This is the source of both ShallowConvNet and DeepConvNet.

## Comparable cross-subject EEG drowsiness work

**[C1]** Cui, J., Lan, Z., Sourina, O., & Müller-Wittig, W. (2022). EEG-based
cross-subject driver drowsiness recognition with an interpretable convolutional
neural network. *IEEE Transactions on Neural Networks and Learning Systems*.
https://doi.org/10.1109/TNNLS.2022.3147208

> Verified from https://arxiv.org/abs/2107.09507. **Cite the preprint alongside the
> DOI.** The published IEEE version is paywalled and was not accessible, so every
> number this paper borrows was read from the preprint. The accuracy figures — 11
> subjects, 78.35 %, the 53.40–72.68 % conventional range and the 71.75–75.19 % deep
> range — are verbatim in the abstract of arXiv v4, dated 18 February 2022, which
> postdates the journal DOI and is therefore very probably the accepted version; that
> is strong evidence and not a check of the published article..
> **11 subjects, leave-one-subject-out, 78.35 % mean accuracy**, against
> conventional baselines at 53.40–72.68 % and earlier deep methods at
> 71.75–75.19 %. Uses separable convolutions, as EEGNet does.
>
> The closest methodological neighbour to this study: **the same leave-one-subject-out
> evaluation protocol**, the same family of architecture, and a comparable subject
> count. It is a **different dataset and a different recording protocol**, so "same
> protocol" must mean the evaluation protocol and nothing more — an earlier wording
> here said "same protocol" without that qualifier and invited the stronger reading.
>
> **Class balance, verified 19 September 2026 from
> https://arxiv.org/pdf/2107.09507.** Their evaluation set holds **2,952 samples
> from 11 subjects, 1,731 alert and 1,221 drowsy** — a drowsy prevalence of 41.4 %
> and an always-alert baseline of 58.6 %. The paper calls it "an unbalanced dataset"
> in those words, and Table I gives the per-subject counts.
>
> This settles an open item, and it settles it against the sentence that was
> withdrawn. An earlier draft claimed "their evaluation set is balanced, so accuracy
> is interpretable there and is not interpretable here". Theirs is **not** balanced
> either — but at 41.4 % drowsy against 6.94–8.32 % here, their 78.35 % clears its
> own 58.6 % baseline by about twenty points, while the most accurate architecture
> in this study barely clears a 92.73 % one. The verified comparison makes the
> paper's point better than the guessed one did: the difference is the class ratio,
> not the method.
>
> Their per-subject counts are uneven enough that a pooled prevalence flatters the
> comparison on some subjects; Related Work says so rather than resting weight on
> the aggregate alone.

## Surveys establishing what the field reports

**[S1]** Hassan, J., Naziullah, S., Rashid, M., Islam, T., Islam, M. N., Islam,
M. S., & Mahmud, S. (2025). Current status and challenges in
electroencephalography (EEG)-based driver fatigue detection: a comprehensive
survey. *Cognitive Neurodynamics*, 19, 142.
https://doi.org/10.1007/s11571-025-10320-3

> Verified from https://link.springer.com/article/10.1007/s11571-025-10320-3.
> PRISMA survey; 267 records screened — "A total of 267 publications were retrieved
> through initial database searches" — and **87 papers analysed**, "Ultimately, 87
> studies met the eligibility criteria and were included in the final systematic
> review".
>
> **Full-text search, 25 September 2026.** *Brier*, *probability calibration*,
> *Platt*, *isotonic*, *expected calibration error* and *reliability diagram* do not
> occur. Neither does any statement about reviewed studies failing to report their
> validation scheme, nor about single-run versus repeated-run reporting, nor about
> class imbalance or a majority-class baseline. The gap sentence in the Introduction
> is licensed for calibration; the other three are **not** licensed by this source. Accuracy is the
> headline metric throughout, with quoted figures including 87–87.9 %, 90 %+,
> 92 % and 99.23 %.

**[S2]** Ghaffari fam, S., Sarbazi, E., Naderian, S., Khazaei, S., Tatli, M., &
Soleimanpour, H. (2026). Driver drowsiness detection using machine learning and
deep learning techniques: a systematic review. *Archives of Academic Emergency
Medicine*, 14(1), e19. https://doi.org/10.22037/aaem.v14i1.2932

> Verified from https://pmc.ncbi.nlm.nih.gov/articles/PMC13265076/.
> **69 studies**, searched to August 2025. Median reported accuracy **94.48 %**
> for deep learning and **91.80 %** for classical machine learning; the range
> across studies runs from 67 % to 100 %. 73.4 % of studies are simulator-based.
> Risk-of-bias assessment rates **27 of 69 studies high risk**, citing "dataset
> construction, labeling procedures, insufficient reporting of ground-truth
> generation, and inadequate validation strategies".
>
> **Full-text search, 25 September 2026.** *Brier*, *probability calibration*,
> *Platt*, *isotonic*, *expected calibration error* and *reliability diagram* do not
> occur. On reporting it does say, and this is the only source that does: "incomplete
> reporting in several studies, including missing details on sample characteristics,
> annotation methods, and validation schemes restricts the reliability of cross-study
> synthesis." It says nothing about single-run reporting. Its exclusion criteria were
> re-read at the same time and confirm the caveat below: it excludes "vehicle
> telemetry, physiological signals without behavioral imaging".
>
> **Scope caveat — do not misdescribe this one.** Its inclusion criteria centre
> on *behavioural* indicators, not EEG. Cite it for what the field reports and
> for the risk-of-bias finding, and cite [S1] for the EEG-specific picture.

**[S3]** Peker, N. Y., Peker, E., & Zengin, A. (2026). A comparative review of
driver drowsiness detection systems: recent advances, applications, challenges,
and future directions. *Measurement*, 279, 121676.
https://doi.org/10.1016/j.measurement.2026.121676

> Verified from https://www.sciencedirect.com/science/article/pii/S0263224126013850
> and from the publisher's own embedded metadata in the article PDF
> (`/Subject` = "Measurement, 279 (2026) 121676", `/doi` =
> 10.1016/j.measurement.2026.121676, `/Creator` = Elsevier). Sakarya University,
> Türkiye. Received 10 November 2025, accepted 26 April 2026, online 8 May 2026.
> **Open access under CC BY 4.0**, so its text may be quoted with attribution.
> 31 pages, 155 numbered references. This is the most recent review of the field at the
> time of writing and the one to cite when the manuscript says "recent".
>
> **Why this reference matters to this paper, in three distinct ways.**
>
> **1. It cites DD-Database, which is why check 4 above is corrected.** The
> dataset is its reference [62], described in its Table 3 — "Driving simulator
> protocol; 4 EEG + 2 EOG + 1 ECG; time marks of drowsiness events (annotation
> files); 10 volunteers, 40 h total" — and in its body text on page 8. Every
> figure in that row agrees with the deposit and with [D1] as recorded in
> `LITERATURE_NUMBERS.csv`; nothing in the row is new information, and it adds
> nothing about who marked the events or against what criterion. The "no base
> paper" conclusion therefore survives: this is a review citing a dataset, not a
> descriptor of it.
>
> **2. It corroborates the label-construction argument independently.** Its own
> words on DD-Database:
>
> > "Its protocol is specifically designed to induce drowsiness under controlled
> > night-driving-like conditions, which is useful for physiological modeling but
> > also introduces protocol-specific bias. In addition, the way event
> > annotations are segmented or converted into window-level learning targets may
> > vary across studies and affect the reported metrics."
>
> That is this paper's motivation for evaluating three window-set constructions,
> stated in a 2026 Elsevier review about this exact dataset, by authors with no
> connection to this work. Cite it in Related Work and beside Limitation 8. It
> also states the general form of the point — "performance metrics are only
> comparable when the acquisition context, label construction, and evaluation
> protocol are aligned or explicitly accounted for" — and, on accuracy under
> imbalance, "Although accuracy is widely reported, it can be misleading in
> imbalanced settings where drowsy samples are relatively rare."
>
> Two of its future-directions statements are close to this paper's position and
> are worth citing as such: that the field should "move beyond accuracy-centered
> comparisons and adopt a broader evaluation perspective", and that "greater
> attention should also be given to subject-independent, cross-vehicle and
> cross-setting, and cross-dataset validation, since strong performance within a
> single dataset does not necessarily indicate reliable generalization to unseen
> drivers or real deployment conditions."
>
> **3. It establishes the gap by its own silence, and this is countable.** A
> full-text search of all 31 pages returns **zero** occurrences of *Brier*,
> *probability calibration*, *calibrated probabilit\**, *reliability diagram*,
> *expected calibration error*, *Platt*, *isotonic*, *majority class*, *class
> prior*, *baseline accuracy* and *leave-one-subject-out*; **two** of *imbalanc\**
> and **two** of *subject-independent*. Its discussion of accuracy, precision,
> recall, specificity and F1 is a discussion of threshold metrics only. Where the
> review does use the word "calibration" — eleven times, checked one by one — it
> means **sensor and setup calibration**, the burden of placing electrodes and
> preparing the montage, not the calibration of predicted probabilities. The
> closest of the eleven is "whether stable performance depends on subject-specific
> calibration, adaptive thresholding, or explicit domain-adaptation procedures",
> which is per-subject model adaptation — still not probability calibration, and
> notably it is raised as an open question rather than answered. **That
> distinction must be stated whenever this reference is used for the gap claim**,
> because a reviewer who greps the same PDF will find the word eleven times and
> must not think the claim was made carelessly.
>
> The gap sentence this licenses, and its exact limits: the most recent
> comparative review of the field does not discuss probability calibration,
> majority-class baselines or Brier scores at all. It does **not** license
> "nobody has ever calibrated an EEG drowsiness model" — one review's silence is
> evidence about the review, and [P1]–[P6] show the machinery is standard
> elsewhere.

## Evaluation methodology

**[E1]** Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more
informative than the ROC plot when evaluating binary classifiers on imbalanced
datasets. *PLoS ONE*, 10(3), e0118432.
https://doi.org/10.1371/journal.pone.0118432

> Verified from https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432

**[E2]** Varoquaux, G. (2018). Cross-validation failure: small sample sizes lead
to large error bars. *NeuroImage*, 180, 68–77.
https://doi.org/10.1016/j.neuroimage.2017.06.061

> Verified from https://pubmed.ncbi.nlm.nih.gov/28655633/ and arXiv:1706.07581.
> Supports the paper's insistence that the interval be taken over subjects.

## Probability calibration

**[P1]** Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration
of modern neural networks. *Proceedings of the 34th International Conference on
Machine Learning*, PMLR 70, 1321–1330.

> Verified from https://proceedings.mlr.press/v70/guo17a.html

**[P2]** Van Calster, B., McLernon, D. J., van Smeden, M., Wynants, L., &
Steyerberg, E. W. (2019). Calibration: the Achilles heel of predictive analytics.
*BMC Medicine*, 17, 230. https://doi.org/10.1186/s12916-019-1466-7

> Verified from https://link.springer.com/article/10.1186/s12916-019-1466-7.
> **The single most load-bearing citation for this paper's central claim.** It
> states directly that discrimination and calibration are separate properties,
> that a model can rank correctly while systematically mis-stating absolute
> probabilities, and that a lower-AUC but better-calibrated model can be the more
> useful one. Our Brier partition is an empirical instance of exactly that.

**[P3]** Naeini, M. P., Cooper, G. F., & Hauskrecht, M. (2015). Obtaining well
calibrated probabilities using Bayesian binning. *Proceedings of the AAAI
Conference on Artificial Intelligence*, 29(1), 2901–2907.

> Verified from https://ojs.aaai.org/index.php/AAAI/article/view/9602 — the
> source of the binned expected calibration error this paper uses.

**[P4]** Zadrozny, B., & Elkan, C. (2002). Transforming classifier scores into
accurate multiclass probability estimates. *Proceedings of the Eighth ACM SIGKDD
International Conference on Knowledge Discovery and Data Mining*, 694–699.
https://doi.org/10.1145/775047.775151

> Verified from https://dl.acm.org/doi/10.1145/775047.775151 — the isotonic
> calibration used as the non-parametric comparison.

**[P5]** Platt, J. C. (2000). Probabilities for SV machines. In A. J. Smola,
P. L. Bartlett, B. Schölkopf, & D. Schuurmans (Eds.), *Advances in Large Margin
Classifiers* (pp. 61–74). Cambridge, MA: MIT Press.

> Verified from the publisher's catalogue record for ISBN 0-262-19448-1
> (https://books.google.com/books/about/Advances_in_Large_Margin_Classifiers.html?id=gOXI3fO3VUwC)
> and the book record at
> https://research.aston.ac.uk/en/publications/advances-in-large-margin-classifiers/.
> **The title and year printed in the book are not the ones this paper was citing.**
> The chapter at pp. 61–74 is titled *Probabilities for SV Machines*, and the
> volume is 2000, not 1999. The longer title this entry previously carried —
> "Probabilistic outputs for support vector machines and comparisons to
> regularized likelihood methods" — is how the work is indexed as a 1999 preprint,
> and is what most of the literature cites; the printed chapter is cited here
> because it is the version with a publisher record. The start page 61 is from the
> contents list; the end page follows from the next chapter beginning at p. 75.
> Two catalogues give the volume title unhyphenated and MIT Press's own chapter
> page gives *Advances in Large-Margin Classifiers*; the unhyphenated form is used
> here and a copy-editor may set it either way.

**[P6]** Brier, G. W. (1950). Verification of forecasts expressed in terms of
probability. *Monthly Weather Review*, 78(1), 1–3.
https://doi.org/10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2

> Verified from https://ui.adsabs.harvard.edu/abs/1950MWRv...78....1B/abstract
> (title, author, journal, year, volume 78, DOI) and
> https://scispace.com/papers/verification-of-forecasts-expressed-in-terms-of-probability-2b2hfncok6
> (issue 1, pp. 1–3). The DOI string itself carries volume 078 and first page
> 0001. The publisher's own page at journals.ametsoc.org refuses automated
> requests and was not reachable in this pass; the two records above agree on
> every field. The Brier score is this paper's reliability measure and this is its
> origin.

<!-- not-for-submission:start -->
---

## Still to add before submission

- **A drowsiness-specific paper that reports accuracy on an imbalanced EEG set
  without its baseline.** The two surveys establish the pattern in aggregate,
  which is the safer way to make the argument; naming individual papers invites a
  reviewer to defend them. Recommend keeping the aggregate framing.
- **A citation for class-weighted training**, if Methods keeps the class-weight
  sentence.
- **TensorFlow and scikit-learn**, if BSPC's style requires software citations.
- The ARL repository [A1] — decide whether it appears as a reference or only as a
  URL in the code-availability statement.
<!-- not-for-submission:end -->
