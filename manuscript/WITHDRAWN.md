# Phrases this paper has withdrawn

*Machine-checked. Not part of the manuscript.*

Each line below is a phrase that once appeared in a draft and was removed because it
was false, unsupported, or stronger than the evidence. `tools/check_withdrawn.py`
fails if any of them reappears in a section file or in a built manuscript.

This file exists because the same corrections kept being re-reported. A phrase was
removed, a superseded PDF was read, the correction was requested again, and the
answer "that is already fixed" is worth nothing without a check anyone can run. Now
there is one.

**Format:** one phrase per line, after `- `. Lines beginning with `#` or `>` are
notes. Matching ignores case and collapses whitespace, so a phrase broken across
lines is still caught.

---

## Ranking invariance stated too strongly

> Platt scaling preserves the ranking only when the fitted slope is positive, and
> the ε-clip before the logit creates ties that move ROC-AUC by up to 0.0000397267.
> "By construction" and "incapable" are therefore both false as implemented.

- unchanged by construction
- incapable of changing any ranking metric
- leaves ROC-AUC and PR-AUC intact
- cannot change ROC-AUC or PR-AUC at all
- Because Platt scaling is monotone it leaves
- claims exact invariance for Platt scaling
- unable to alter ROC-AUC or PR-AUC
- therefore monotone and unable to alter

## Construction robustness stated as a guarantee

> Three constructions of one set of recordings are not external replication.

- a weaker but still meaningful guarantee
- meaningful but limited guarantee
- which is to say almost all of them, cannot offer

## Claims of dominance across measures

> DeepConvNet beats EEGNet on pooled Brier and pooled precision on Arm C.

- beaten on every metric reported in this paper
- loses to the best architecture on every other measure
- wrong model on every measure
- better than every alternative tested

## Claims that a search proves absence

> A search that finds nothing establishes nothing.

- The first report, to our knowledge
- no survey of this field has yet asked for it
- No paper using DD-Database was found in a targeted search
- no pair in this study isolates trimming
- Trimming is not isolated by any pair

## Annotation protocol asserted without a source

> The deposit documents only that the files carry time marks.

- self-reported button press
- the participant's own report
- transition into self-reported drowsiness
- annotation onset

## Overstated or informal wording

- are uninterpretable without
- The reviews also agree
- still be useless for the task
- need not agonise
- actively inverted
- close to backwards
- the cleanest ablation in the study
- every architecture at its published configuration
- same protocol, same family
