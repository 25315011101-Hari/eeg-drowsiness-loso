"""Self-checks that need no EDF file, no GPU and no trained model.

    python -m pytest tests -q
    python tests/test_pipeline.py          # same checks without pytest

What is covered:

  config        the three arms are internally consistent and their reference
                values are what the paper prints
  preprocess    window geometry, the balancing arithmetic, and the internal
                check that gates every save -- all on synthetic counts
  calibrate     ECE and Brier on cases whose answers can be worked out by hand;
                Platt and isotonic are monotone, so ROC-AUC cannot move
  thresholds    the selection rule finds a threshold that is genuinely optimal
  stats         the confusion-matrix reconstruction inverts exactly, the paired
                test is applied to ten values and not fifty, and the two recall
                conventions differ in the direction the paper says
  scan          a number outside the registry is caught and one inside is not

The point of the calibration tests is the property the paper leans on: a
monotone map cannot change the ordering.  If that ever broke, the central claim
would break with it, so it is asserted rather than assumed.

That property is about the map, not about our data.  What the map actually did to
the released folds is a separate, measured question, because the implementation
clips probabilities before taking the logit and a clip can tie scores that were
distinct.  tools/check_monotonicity.py refits all 150 Arm A calibrators and
reports it, and test_every_platt_fit_on_arm_a_is_strictly_increasing below checks
the part of it the argument needs: every fitted slope is positive.
"""

import os
import shutil
import sys
import tempfile

import numpy as np
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src import aggregate, calibrate, preprocess, scan, stats, thresholds  # noqa: E402


# ------------------------------------------------------------------- config
def test_arm_definitions_are_consistent():
    for arm, spec in C.ARMS.items():
        assert spec["n_windows"] == spec["n_per_subject"] * C.N_SUBJECTS, arm
        assert sum(spec["per_subject_drowsy"].values()) == spec["n_drowsy"], arm
        assert set(spec["per_subject_drowsy"]) == set(C.SUBJECTS), arm
        for s, n in spec["per_subject_drowsy"].items():
            assert 0 <= n <= spec["n_per_subject"], (arm, s)


def test_reference_values_match_the_paper():
    want = {"A": (0.0762, 0.0832, 91.68),
            "B": (0.0645, 0.0694, 93.06),
            "C": (0.0674, 0.0727, 92.73)}
    for arm, (brier, pr, acc) in want.items():
        r = C.arm_reference(arm)
        assert r["brier"] == brier, (arm, r["brier"])
        assert r["pr_auc"] == pr, (arm, r["pr_auc"])
        assert abs(r["accuracy"] - acc) < 0.01, (arm, r["accuracy"])


def test_fold_counts():
    assert C.folds_per_arm() == 250
    assert C.total_folds() == 750


# --------------------------------------------------------------- preprocess
def test_drowsy_window_ends_at_the_event():
    """A drowsy window covers the ten seconds BEFORE the press, not after it."""
    n = 100 * C.WIN
    wins = preprocess.windows_for_recording(n, [600.0])
    drowsy = [st for st, lab in wins if lab == 1]
    assert len(drowsy) == 1
    start = drowsy[0]
    assert start + C.WIN == int(round(600.0 * C.FS))


def test_events_in_the_first_ten_seconds_are_dropped():
    """There is no room for a preceding window, so the event yields nothing."""
    wins = preprocess.windows_for_recording(50 * C.WIN, [1.0])
    assert not [st for st, lab in wins if lab == 1]


def test_no_window_uses_a_sample_twice():
    n = 200 * C.WIN
    rng = np.random.RandomState(0)
    events = np.sort(rng.uniform(20, n / C.FS - 20, size=40))
    wins = preprocess.windows_for_recording(n, events)
    spans = sorted((st, st + C.WIN) for st, _ in wins)
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        assert a1 <= b0, ((a0, a1), (b0, b1))


def test_alert_windows_keep_their_distance_from_events():
    n = 200 * C.WIN
    events = [300.0, 900.0]
    wins = preprocess.windows_for_recording(n, events)
    ev = np.round(np.asarray(events) * C.FS)
    for st, lab in wins:
        if lab == 0:
            centre = st + C.WIN / 2.0
            assert np.min(np.abs(centre - ev)) >= C.ALERT_GAP_SEC * C.FS


def test_balancing_arithmetic():
    # keep_drowsy retains every drowsy window
    assert preprocess.keep_drowsy_count(178, 1200, 926, "keep_drowsy") == 178
    # proportional keeps the subject's own ratio, and never more than it has
    assert preprocess.keep_drowsy_count(178, 1200, 926, "proportional") == round(926 * 178 / 1200)
    assert preprocess.keep_drowsy_count(3, 1000, 926, "proportional") <= 3
    try:
        preprocess.keep_drowsy_count(1, 10, 5, "sometimes")
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown balance mode must raise")


def test_internal_check_rejects_a_tampered_array():
    """The gate that stands between a wrong pipeline and a saved file."""
    raw_counts = {s: dict(total=1000, drowsy=100, alert=900) for s in C.SUBJECTS}
    exp = preprocess.derive_expected(raw_counts, "proportional")
    X, y, g = [], [], []
    for s, (n_total, n_drowsy) in exp.items():
        y.append(np.array([1] * n_drowsy + [0] * (n_total - n_drowsy)))
        g.append(np.full(n_total, s))
        X.append(np.zeros((n_total, C.WIN, len(C.WANT)), dtype=np.float32))
    X, y, g = np.concatenate(X), np.concatenate(y), np.concatenate(g)
    assert preprocess.check_internal(X, y, g, raw_counts, "proportional", verbose=False)

    y_bad = y.copy()
    y_bad[np.flatnonzero(y_bad == 1)[0]] = 0        # one drowsy window quietly lost
    assert not preprocess.check_internal(X, y_bad, g, raw_counts, "proportional",
                                         verbose=False)


# ---------------------------------------------------------------- calibrate
def test_ece_is_zero_for_a_perfectly_calibrated_predictor():
    # 100 windows at p = 0.30, exactly 30 of them positive
    p = np.full(100, 0.30)
    y = np.array([1] * 30 + [0] * 70)
    assert calibrate.expected_calibration_error(p, y) < 1e-9


def test_ece_equals_the_gap_for_a_single_bin():
    p = np.full(100, 0.90)
    y = np.array([1] * 40 + [0] * 60)
    assert abs(calibrate.expected_calibration_error(p, y) - 0.50) < 1e-9


def test_brier_of_the_constant_prior_is_the_reference():
    """pi*(1-pi) is not a convention; it is what the constant predictor scores."""
    for arm, spec in C.ARMS.items():
        pi = spec["n_drowsy"] / spec["n_windows"]
        y = np.zeros(spec["n_windows"])
        y[:spec["n_drowsy"]] = 1
        got = calibrate.brier(np.full(spec["n_windows"], pi), y)
        assert abs(got - pi * (1 - pi)) < 1e-9, arm
        assert round(got, 4) == C.arm_reference(arm)["brier"], arm


def test_platt_and_isotonic_cannot_change_the_ordering():
    """The property the recalibration argument rests on."""
    from sklearn.metrics import roc_auc_score
    rng = np.random.RandomState(7)
    y_fit = rng.binomial(1, 0.08, 4000)
    p_fit = np.clip(rng.beta(2, 6, 4000) + 0.25 * y_fit, 1e-4, 1 - 1e-4)
    y_in = rng.binomial(1, 0.08, 500)
    p_in = np.clip(rng.beta(2, 6, 500) + 0.25 * y_in, 1e-4, 1 - 1e-4)

    before = roc_auc_score(y_in, p_in)

    # A Platt fit with a positive slope is strictly increasing, so on scores that
    # are all distinct it leaves ROC-AUC where it was. That is the property the
    # recalibration argument rests on, and it is asserted here on synthetic data.
    #
    # It is NOT the same statement as "Platt scaling cannot change ROC-AUC on our
    # data", and the paper does not make that stronger claim. The implementation
    # clips probabilities away from 0 and 1 before taking the logit, which can tie
    # scores that were distinct; tools/check_monotonicity.py measures what that
    # costs on all 150 released Arm A folds, and the paper reports the result as
    # unchanged AT THE REPORTED PRECISION rather than as algebraic invariance.
    q = calibrate.fit_apply_platt(p_fit, y_fit, p_in)
    assert abs(roc_auc_score(y_in, q) - before) < 1e-6
    order = np.argsort(p_in)
    assert np.all(np.diff(q[order]) > -1e-12)

    # Isotonic is only WEAKLY increasing: its flat regions merge distinct scores
    # into ties, which can lower ROC-AUC but can never raise it. No
    # ranking-invariance claim is made for isotonic at any precision.
    q = calibrate.fit_apply_isotonic(p_fit, y_fit, p_in)
    assert roc_auc_score(y_in, q) <= before + 1e-9
    assert np.all(np.diff(q[np.argsort(p_in)]) >= -1e-9)


def test_platt_actually_improves_a_miscalibrated_score():
    rng = np.random.RandomState(11)
    y = rng.binomial(1, 0.08, 6000)
    # scores that rank well but are far too confident
    p = np.clip(0.5 + 0.45 * (2 * y - 1) + rng.normal(0, 0.15, 6000), 1e-4, 1 - 1e-4)
    split = 4000
    q = calibrate.fit_apply_platt(p[:split], y[:split], p[split:])
    assert calibrate.brier(q, y[split:]) < calibrate.brier(p[split:], y[split:])


# --------------------------------------------------------------- thresholds
def test_selected_threshold_is_optimal_on_the_data_it_saw():
    rng = np.random.RandomState(3)
    y = rng.binomial(1, 0.1, 2000)
    p = np.clip(0.2 + 0.4 * y + rng.normal(0, 0.15, 2000), 0, 1)
    for metric in ("f1", "bal_acc"):
        t = thresholds.best_threshold(y, p, metric)
        best = thresholds.score_at(y, p, t)[0 if metric == "bal_acc" else 1]
        for other in thresholds.grid():
            got = thresholds.score_at(y, p, other)[0 if metric == "bal_acc" else 1]
            assert got <= best + 1e-12


def test_sweep_matches_the_direct_computation():
    """The vectorised sweep is a speed change, not a method change."""
    from sklearn.metrics import balanced_accuracy_score, f1_score
    rng = np.random.RandomState(5)
    for _ in range(3):
        n = int(rng.randint(200, 1200))
        y = rng.binomial(1, float(rng.uniform(0.02, 0.3)), n)
        p = np.clip(rng.beta(2, 6, n) + 0.3 * y, 0, 1)
        g, f1, ba = thresholds.sweep(y, p)
        for i, t in enumerate(g):
            pred = (p >= t).astype(int)
            assert abs(f1_score(y, pred, zero_division=0) - f1[i]) < 1e-12
            assert abs(balanced_accuracy_score(y, pred) - ba[i]) < 1e-12


def test_threshold_grid_matches_the_config():
    g = thresholds.grid()
    assert len(g) == C.THRESHOLD_GRID_N
    assert abs(g[0] - 0.01) < 1e-12 and abs(g[-1] - 0.99) < 1e-12


# -------------------------------------------------------------------- stats
def _synthetic_folds(arm="C", seed=0):
    """Fold rows whose confusion matrices are known exactly, so the
    reconstruction in stats.pooled_confusion can be checked against truth."""
    spec = C.ARMS[arm]
    rng = np.random.RandomState(seed)
    rows, truth = [], {}
    for model in C.MODELS:
        tp_tot = fp_tot = 0.0
        for s in C.SEEDS:
            for subj in C.SUBJECTS:
                nd = spec["per_subject_drowsy"][subj]
                tp = int(rng.randint(0, nd + 1))
                fp = int(rng.randint(0, 40))
                recall = tp / nd if nd else 0.0
                precision = tp / (tp + fp) if (tp + fp) else 0.0
                f1 = (2 * precision * recall / (precision + recall)
                      if precision + recall else 0.0)
                rows.append(dict(model=model, seed=s, subject=subj, n_drowsy=nd,
                                 auc=0.5 + 0.4 * rng.rand(),
                                 pr_auc=rng.rand(), bal_acc=rng.rand(), f1=f1,
                                 precision=precision, recall=recall, epochs=20,
                                 val_subs="S1+S2", arm=spec["key"]))
                tp_tot += tp
                fp_tot += fp
        truth[model] = (tp_tot / len(C.SEEDS), fp_tot / len(C.SEEDS))
    df = pd.DataFrame(rows)
    df["ar"] = arm
    return df, truth


def test_confusion_is_exact_when_recorded_false_positives_are_supplied():
    folds, truth = _synthetic_folds()
    pooled = pd.DataFrame([dict(model=m, seed=s, auc=0.8, pr_auc=0.4, bal_acc=0.7,
                                brier=0.09, fp=truth[m][1],
                                arm=C.ARMS["C"]["key"], ar="C")
                           for m in C.MODELS for s in C.SEEDS])
    cm = stats.pooled_confusion(folds, "C", pooled).set_index("model")
    for model, (tp, fp) in truth.items():
        assert abs(cm.loc[model, "tp"] - tp) < 1e-6, model
        assert abs(cm.loc[model, "fp"] - fp) < 1e-6, model
        assert cm.loc[model, "fp_source"] == "recorded", model
        total = cm.loc[model, ["tn", "fp", "fn", "tp"]].sum()
        assert abs(total - C.ARMS["C"]["n_windows"]) < 1e-6, model


def test_reconstructed_false_positives_are_a_lower_bound():
    """Without the recorded count, a fold with no true positive hides its false
    positives, because TP / precision is undefined when precision is zero. The
    reconstruction must therefore never overstate them."""
    folds, truth = _synthetic_folds()
    cm = stats.pooled_confusion(folds, "C").set_index("model")
    for model, (tp, fp) in truth.items():
        assert abs(cm.loc[model, "tp"] - tp) < 1e-6, model
        assert cm.loc[model, "fp"] <= fp + 1e-6, model
        assert cm.loc[model, "fp_source"] == "reconstructed", model


def test_paired_test_uses_ten_values_not_fifty():
    folds, _ = _synthetic_folds()
    r = stats.paired(folds, "C", "EEGNet", "CNN", "auc")
    assert r["n"] == C.N_SUBJECTS
    assert r["p"] >= C.P_FLOOR_WILCOXON_10 - 1e-12


def test_subject_means_are_in_subject_order():
    folds, _ = _synthetic_folds()
    s = stats.subject_means(folds, "C", "EEGNet", "auc")
    assert list(s.index) == C.SUBJECTS


def test_pooled_recall_exceeds_subject_averaged_when_small_subjects_fail():
    """The mechanism behind the paper's two-conventions section, in miniature."""
    spec = C.ARMS["C"]
    rows = []
    for s in C.SEEDS:
        for subj in C.SUBJECTS:
            nd = spec["per_subject_drowsy"][subj]
            recall = 0.0 if nd < 20 else 0.8        # the sparse subjects fail
            rows.append(dict(model="EEGNet", seed=s, subject=subj, n_drowsy=nd,
                             auc=0.8, pr_auc=0.4, bal_acc=0.7,
                             f1=recall, precision=0.5, recall=recall,
                             epochs=20, val_subs="S1+S2", arm=spec["key"]))
    folds = pd.DataFrame(rows)
    folds["ar"] = "C"
    r = stats.recall_conventions(folds, "C").iloc[0]
    assert r.pooled > r.subject_averaged
    assert r.difference > 0.1


def test_assert_consistent_catches_a_missing_arm():
    folds, _ = _synthetic_folds()
    pooled = pd.DataFrame([dict(model=m, seed=s, auc=0.8, pr_auc=0.4, bal_acc=0.7,
                                brier=0.09, fp=100, arm=C.ARMS["C"]["key"], ar="C")
                           for m in C.MODELS for s in C.SEEDS])
    try:
        stats.assert_consistent(folds, pooled)
    except AssertionError as e:
        assert "750" in str(e) or "missing" in str(e)
    else:
        raise AssertionError("a one-arm table must not pass the consistency check")


# --------------------------------------------------------------------- scan
def test_scan_flags_only_the_unregistered_number():
    tmp = tempfile.mkdtemp()
    try:
        reg = os.path.join(tmp, "MASTER_NUMBERS.csv")
        pd.DataFrame([dict(section="results", claim="Arm C EEGNet ROC-AUC",
                           value=0.8831, note="")]).to_csv(reg, index=False)
        draft = os.path.join(tmp, "draft.md")
        with open(draft, "w") as fh:
            fh.write("EEGNet reaches 0.883 on Arm C, while the CNN reaches 0.777.\n")
        flagged = scan.check(draft, scan.registry_values(reg))
        literals = [f[1] for f in flagged]
        assert "0.777" in literals
        assert "0.883" not in literals
    finally:
        shutil.rmtree(tmp)


def test_scan_matches_a_negative_correlation():
    tmp = tempfile.mkdtemp()
    try:
        reg = os.path.join(tmp, "MASTER_NUMBERS.csv")
        pd.DataFrame([dict(section="stats", claim="rho", value=-0.9, note="")]
                     ).to_csv(reg, index=False)
        draft = os.path.join(tmp, "draft.md")
        with open(draft, "w") as fh:
            fh.write("The correlation is -0.900 on Arm A.\n")
        assert not scan.check(draft, scan.registry_values(reg))
    finally:
        shutil.rmtree(tmp)


def test_scan_ignores_urls_and_dois():
    """A DOI is an identifier, not a measurement, and must not be flagged."""
    tmp = tempfile.mkdtemp()
    try:
        reg = os.path.join(tmp, "MASTER_NUMBERS.csv")
        pd.DataFrame([dict(section="data", claim="x", value=1.0, note="")]
                     ).to_csv(reg, index=False)
        draft = os.path.join(tmp, "draft.md")
        with open(draft, "w") as fh:
            fh.write("Available at https://doi.org/10.5061/dryad.5tb2rbp9c and\n"
                     "mirrored at https://zenodo.org/records/8284057, "
                     "doi:10.1002/hbm.23730.\n")
        assert not scan.check(draft, scan.registry_values(reg))
    finally:
        shutil.rmtree(tmp)


def test_scan_ignores_code_spans_and_headings():
    tmp = tempfile.mkdtemp()
    try:
        reg = os.path.join(tmp, "MASTER_NUMBERS.csv")
        pd.DataFrame([dict(section="data", claim="x", value=1.0, note="")]
                     ).to_csv(reg, index=False)
        draft = os.path.join(tmp, "draft.md")
        with open(draft, "w") as fh:
            fh.write("## 6.3 A heading with 9999 in it\n\n"
                     "See `run_all.py --seed 4242` and Section 7.4 below.\n")
        assert not scan.check(draft, scan.registry_values(reg))
    finally:
        shutil.rmtree(tmp)


def test_scan_reads_every_member_of_a_plural_section_reference():
    """"Sections 7.3 and 7.5" names two sections, and neither is a measurement.

    Only the first number followed the word, so the second was read as a value and
    reported as having no source. The global audit of 1 October 2026 found two such
    references in the manuscript; both passed only because their second number was
    also a registered value, so the guard was not in fact protecting them. The
    negative half of this test matters as much as the positive half: a real
    measurement beside a section reference must still be scanned, and blanking the
    reference must not move any line number.
    """
    tmp = tempfile.mkdtemp()
    try:
        reg = os.path.join(tmp, "MASTER_NUMBERS.csv")
        pd.DataFrame([dict(section="data", claim="x", value=1.0, note="")]
                     ).to_csv(reg, index=False)
        draft = os.path.join(tmp, "draft.md")
        with open(draft, "w") as fh:
            fh.write("Pooled values are used in Sections 7.3 and 7.5.\n"
                     "The arms are isolated in Sections 7.1.1, 7.1.2 and 7.2.\n"
                     "See Sections 5 and 6, and Section 8.10, and also §7.6.\n")
        assert not scan.check(draft, scan.registry_values(reg))

        with open(draft, "w") as fh:
            fh.write("Line one.\n"
                     "In Sections 7.3 and 7.5 the value is 0.98765 here.\n"
                     "And 0.54321 on this one.\n")
        flagged = [(f[0], f[1]) for f in scan.check(draft, scan.registry_values(reg))]
        assert flagged == [(2, "0.98765"), (3, "0.54321")], (
            "a measurement beside a plural section reference must still be flagged, "
            "on its own line; got %r" % (flagged,))
    finally:
        shutil.rmtree(tmp)


# ---------------------------------------------------------------- aggregate
def test_aggregate_rejects_a_fold_from_the_wrong_arm():
    folds, _ = _synthetic_folds()
    folds = folds.drop(columns=["ar"])
    assert not aggregate.check_arm(folds, "C")
    bad = folds.copy()
    bad.loc[bad.index[0], "n_drowsy"] = 999
    problems = aggregate.check_arm(bad, "C")
    assert problems and "n_drowsy" in problems[0]


def test_aggregate_rejects_mismatched_validation_subjects():
    folds, _ = _synthetic_folds()
    folds = folds.drop(columns=["ar"])
    bad = folds.copy()
    bad.loc[bad.model == "CNN", "val_subs"] = "S3+S4"
    problems = aggregate.check_arm(bad, "C")
    assert any("validation subjects" in p for p in problems)


# --------------------------------------------- calibration recomputed from raw
def test_arm_a_calibration_recomputes_from_probability_files():
    """The published Arm A summary must fall out of the released raw scores.

    Every other calibration check in this suite compares a registry row against a
    summary file. Both of those are outputs of the same run, so agreeing proves
    only that the file was copied faithfully. This test starts from the per-window
    probability files and refits every calibrator, which is the only check that
    would catch a summary that no longer matches the scores it claims to describe.

    It is skipped, not failed, when the probability files are absent, because they
    are released for Arm A only.
    """
    import glob
    import numpy as np
    import pandas as pd
    from src import calibrate

    root = os.path.join(C.RESULT_DIR, "A")
    if not glob.glob(os.path.join(root, "probs_*.npz")):
        return  # not released for this arm; nothing to check

    published = pd.read_csv(os.path.join(root, "calibration_summary.csv"))
    recomputed = calibrate.summarise(calibrate.calibrate_arm("A", verbose=False), "A")
    assert len(recomputed) == len(published), (
        "recomputation covered %d architectures, the published summary has %d"
        % (len(recomputed), len(published)))

    pub = published.set_index("model")
    rec = recomputed.set_index("model")
    for model in pub.index:
        for col in ("ece_raw", "brier_raw", "ece_platt", "brier_platt",
                    "ece_isotonic", "brier_isotonic", "brier_reference"):
            a, b = float(pub.loc[model, col]), float(rec.loc[model, col])
            assert abs(a - b) < 5e-6, (
                "Arm A %s %s: published %.8f, recomputed from raw scores %.8f"
                % (model, col, a, b))


def test_every_platt_fit_on_arm_a_is_strictly_increasing():
    """The manuscript's ranking-invariance claim rests on a positive slope.

    A logistic map preserves ROC-AUC only when its fitted slope is positive; a
    negative one reverses the ranking. The claim was in the text before anything
    recorded the slopes, so this pins it to the data. Skipped when the probability
    files are absent.
    """
    import glob
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from src.calibrate import _logit

    root = os.path.join(C.RESULT_DIR, "A")
    paths = sorted(glob.glob(os.path.join(root, "probs_*.npz")))
    if not paths:
        return

    checked = 0
    for path in paths:
        d = np.load(path)
        y, p, subj = d["y_true"], d["y_prob"].astype(float), d["subject"]
        for s in np.unique(subj):
            tr = subj != s
            if len(np.unique(y[tr])) < 2:
                continue
            lr = LogisticRegression(C=C.PLATT_C, solver="lbfgs")
            lr.fit(_logit(p[tr]).reshape(-1, 1), y[tr])
            slope = float(lr.coef_[0][0])
            assert slope > 0, ("non-positive Platt slope %.4f in %s for subject %s "
                               "— the map reorders and the invariance claim fails"
                               % (slope, os.path.basename(path), s))
            checked += 1
    assert checked > 0, "probability files present but no fold was checked"


# ------------------------------------------------------------------- figures
def test_every_figure_value_comes_from_the_registry():
    """No figure may plot a number the registry does not hold.

    `src.figures.lookup` raises on a missing claim, so drawing all four figures is
    itself the check: if any claim name drifts -- a renamed registry row, an arm
    that stops being measured -- the draw fails rather than producing a picture of
    a number the paper does not contain.
    """
    from src import figures

    figures.main()

    # And the claims really are the registry's, not a local dict that shadows it.
    with pytest.raises(KeyError):
        figures.lookup("Arm A EEGNet a claim that does not exist")


def test_figure_files_are_written_in_both_formats():
    """A vector PDF for the journal, a PNG for reading in a browser."""
    from src import figures

    # Named by their place in the paper, not by the order they were drawn in:
    # Figures 1-5 are the main paper, S1 is supplementary.
    expected = ["figure2_study_design", "figure3_accuracy_against_recall",
                "figure4_subject_against_seed_spread", "figure5_brier_partition",
                "figure6_recalibration", "figureS1_overview"]
    for name in expected:
        for ext in ("pdf", "png"):
            path = os.path.join(figures.FIGDIR, "%s.%s" % (name, ext))
            assert os.path.exists(path), "missing figure file: %s" % path
            assert os.path.getsize(path) > 2000, "suspiciously small: %s" % path


def test_figure_5_partition_matches_the_results_section():
    """The picture must show the same three-against-two split the text claims.

    Figure 5 places an architecture right of zero when its pooled Brier score
    exceeds the class-prior reference. (It was Figure 1 until the figures were
    renumbered into citation order on 19 September 2026; Figure 1 is now the study
    design, and this test kept the old name for five days.) The manuscript says that split is three
    above and two below, identically on all three constructions, and names them.
    If the registry ever disagreed, the figure would quietly tell a different
    story than the sentence beside it.
    """
    from src import figures

    above_expected = {"EEGNet", "ShallowConvNet", "CNN-BiLSTM"}
    below_expected = {"CNN", "DeepConvNet"}
    for arm in ("A", "B", "C"):
        above, below = set(), set()
        for model in C.MODELS:
            margin = figures.lookup(
                "Arm %s %s pooled Brier margin over reference" % (arm, model))
            (above if margin > 0 else below).add(model)
        assert above == above_expected, (
            "Arm %s: above the reference is %s, the manuscript says %s"
            % (arm, sorted(above), sorted(above_expected)))
        assert below == below_expected, (
            "Arm %s: below the reference is %s, the manuscript says %s"
            % (arm, sorted(below), sorted(below_expected)))


def test_figure_3_shows_the_two_most_accurate_with_the_lowest_recall():
    """The claim the second figure exists to show, asserted on the same numbers.

    This is the finding that holds on all three constructions without needing a
    p-value, and it is the one the figure is arranged around.
    """
    from src import figures

    for arm in ("A", "B", "C"):
        acc = {m: figures.lookup("Arm %s %s pooled accuracy percent" % (arm, m))
               for m in C.MODELS}
        rec = {m: figures.lookup("Arm %s %s pooled recall" % (arm, m))
               for m in C.MODELS}
        most_accurate = set(sorted(C.MODELS, key=lambda m: -acc[m])[:2])
        lowest_recall = set(sorted(C.MODELS, key=lambda m: rec[m])[:2])
        assert most_accurate == lowest_recall, (
            "Arm %s: two most accurate %s, two lowest recall %s"
            % (arm, sorted(most_accurate), sorted(lowest_recall)))


def test_only_arm_b_has_no_architecture_above_the_always_alert_baseline():
    """The second claim the second figure now carries, on the same numbers.

    Figure 3 draws each construction's always-alert accuracy as a rule and its
    caption says that on Arm B every architecture falls below it, as Section 7.3
    does. That sentence is true of these numbers by a margin of six hundredths of
    a percentage point -- CNN reaches 92.998 against a baseline of 93.06 -- which
    is exactly the size of gap that a re-run could close without anyone noticing
    the caption had gone wrong.
    """
    from src import figures

    expected = {"A": True, "B": False, "C": True}
    for arm in ("A", "B", "C"):
        base = figures.lookup("Arm %s always-alert accuracy percent, 2 dp" % arm)
        best = max(figures.lookup("Arm %s %s pooled accuracy percent" % (arm, m))
                   for m in C.MODELS)
        assert (best > base) == expected[arm], (
            "Arm %s: best accuracy %.4f against always-alert %.2f -- the "
            "manuscript says an architecture does%s exceed it"
            % (arm, best, base, "" if expected[arm] else " not"))


def test_five_point_correlations_use_the_exact_permutation_p():
    """No five-point p-value may come from the t-approximation.

    Section 6.5 states a hard floor of 2/120 = 0.0167 for a rank correlation
    across five architectures. The approximation returns values below that floor
    -- 0.0374 for rho = -0.900, and 0.0000 for rho = 1.000 -- so a single
    reverted import would put the paper back into the state where its Methods
    section and its numbers described different tests.

    Checked three ways: the helper is exact at n = 5, it agrees with a full
    enumeration, and no p-value registered for a five-point correlation lies
    below the floor.
    """
    import csv
    import itertools
    import math

    from src import stats

    # 1. the helper reports itself exact at five points, and lands on the floor
    #    for a perfect correlation rather than on zero
    rho, p, exact = stats.spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])
    assert exact, "five-point correlation did not use the exact route"
    assert abs(p - C.P_FLOOR_SPEARMAN_5) < 1e-12, (
        "perfect reversal gave p = %r, expected the floor %r"
        % (p, C.P_FLOOR_SPEARMAN_5))

    # 2. the null distribution matches an independent enumeration
    base = list(range(5))
    for other in ([1, 2, 3, 4, 5], [2, 1, 3, 4, 5], [3, 1, 4, 2, 5]):
        rho, p, _ = stats.spearman(base, other)
        hits = sum(1 for perm in itertools.permutations(base)
                   if abs(_rho5(base, perm)) >= abs(rho) - 1e-9)
        assert abs(p - hits / math.factorial(5)) < 1e-12, (
            "exact p %r disagrees with enumeration %r" % (p, hits / 120))

    # 3. nothing registered for a five-point correlation is below the floor
    five_point = ("Spearman pooled accuracy vs pooled recall",
                  "p for parameters vs ROC-AUC",
                  "p for ROC-AUC (pooled) vs pooled Brier",
                  "p for ROC-AUC (subject_averaged) vs pooled Brier")
    with open(C.REGISTRY_CSV) as fh:
        for row in csv.DictReader(fh):
            if not row["claim"].startswith("Arm "):
                continue
            if not any(k in row["claim"] for k in five_point):
                continue
            if " p for " not in row["claim"] and "p for" not in row["claim"]:
                continue
            value = float(row["value"])
            assert value >= C.P_FLOOR_SPEARMAN_5 - 1e-9, (
                "%s is %r, below the attainable floor %r -- a five-point p-value "
                "cannot be smaller than 2/120"
                % (row["claim"], value, C.P_FLOOR_SPEARMAN_5))


def _rho5(a, b):
    """Spearman's rho for two orderings of five untied ranks."""
    d2 = sum((x - y) ** 2 for x, y in zip(a, b))
    return 1.0 - 6.0 * d2 / (5 * (5 * 5 - 1))


def test_no_generated_manuscript_file_has_been_edited_by_hand():
    """A correction made in a generated file is a correction that disappears.

    On 2 October 2026 the sentence "The deposit documents neither who made the marks
    nor against what criterion" was corrected in manuscript/MASTER_FILE.md, which the
    dataset README had just been shown to contradict. That file is written by
    tools/master_file.py, which tools/preflight.py re-runs every time; the generator
    was not changed, so the next preflight put the withdrawn sentence back into the
    manuscript and still printed ALL CHECKS PASS. The "master file" check asserted
    only that the generator had run, never that its output matched the file on disk.

    This test closes that gap for every declared generated file, and names the source
    to edit instead. It restores the original bytes, so running it changes nothing.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_generated as cg
    assert cg.GENERATED, "no generated files are declared"
    for entry in cg.GENERATED:
        problems = cg.check_one(entry)
        assert not problems, problems[0]


# ------------------------------------------------------------------- runner
def _all_tests():
    g = globals()
    return [(n, g[n]) for n in sorted(g) if n.startswith("test_")]


# ---------------------------------------------------------------------------
# Audit scope: what counts as the manuscript, and what reads it
#
# Finding R37. tools/preflight.py carried its own hand-written list of ten section
# files. tools/build_manuscript.py assembles twelve. The two absent from the list --
# CODE_AVAILABILITY.md and REFERENCES.md -- were therefore read by no placeholder
# check and no withdrawn-phrase check, and six unfilled placeholders and a section
# headed "Still to add before submission" reached the built manuscript while preflight
# printed ALL CHECKS PASS. Nothing failed. Two files were never looked at.
#
# These tests do not assert today's twelve filenames, because that is the same
# hand-maintained list one layer further out, and the register already contains a
# finding (R31) about exactly that failure. They assert the mechanism: that the scope
# is derived from the builder and not restated, that every exclusion is named with a
# reason, and -- the one that closes the class -- that a file newly added to the
# builder's ORDER lands inside every check's scope without anyone remembering to add
# it. A future thirteenth section cannot be silently unaudited.
# ---------------------------------------------------------------------------

def test_every_pooled_column_that_is_reported_carries_a_seed_dispersion():
    """Table 4's three pooled quantities have a seed SD, and the means are unchanged.

    They were bare point estimates while every column of the Section 7.5 tables
    beside them carried a seed SD, which hid the largest instability in the study.
    """
    from src import aggregate, stats
    folds, pooled = aggregate.load()
    for arm in ("A", "B", "C"):
        spread = stats.pooled_confusion_spread(folds, arm, pooled)
        averaged = stats.pooled_confusion(folds, arm, pooled).set_index("model")
        for r in spread.itertuples():
            assert int(r.n_seeds) == len(C.SEEDS)
            # Adding dispersion must not move a single reported value.
            ref = averaged.loc[r.model]
            # Recall and accuracy are LINEAR in the tabulated counts, so the mean of
            # the five seeds equals the value read off the seed-mean counts and a
            # seed SD pairs with the printed figure exactly.
            assert abs(r.accuracy_mean - ref.accuracy) < 1e-9
            assert abs(r.recall_mean - ref.recall) < 1e-9
            for col in ("accuracy", "recall", "precision"):
                lo = getattr(r, "%s_min" % col)
                hi = getattr(r, "%s_max" % col)
                mean = getattr(r, "%s_mean" % col)
                assert lo <= mean <= hi
                assert getattr(r, "%s_sd" % col) >= 0.0

    # The specific case the section now names. If this ever stops being the least
    # stable cell in the accuracy column, the sentence about it has to change.
    spread = stats.pooled_confusion_spread(folds, "B", pooled).set_index("model")
    worst = spread.accuracy_sd.idxmax()
    assert worst == "ShallowConvNet", worst
    assert round(float(spread.loc[worst, "accuracy_sd"]), 2) == 6.22
    others = [float(stats.pooled_confusion_spread(folds, a, pooled)
                    .set_index("model").loc[m, "accuracy_sd"])
              for a in ("A", "B", "C") for m in C.MODELS
              if not (a == "B" and m == "ShallowConvNet")]
    assert max(others) < 1.55, max(others)


def test_precision_is_a_ratio_and_so_carries_no_seed_dispersion_in_table_5():
    """Why precision has no ± where recall and accuracy do.

    Table 4's precision is TP/(TP+FP) read off its own seed-mean counts. The mean of
    the five seeds' own precisions is a different number, because precision is a
    ratio of two varying quantities: the two differ at the third decimal for fourteen
    of the fifteen rows and by up to 0.023. Pairing the printed value with a ± taken
    over the per-seed ratios would put an interval around the wrong centre, so the
    caption states the convention instead. If these two ever coincide, the caption is
    over-explaining and can be simplified -- which is why this is a test.
    """
    from src import aggregate, stats
    folds, pooled = aggregate.load()
    differing, largest = 0, 0.0
    for arm in ("A", "B", "C"):
        spread = stats.pooled_confusion_spread(folds, arm, pooled).set_index("model")
        averaged = stats.pooled_confusion(folds, arm, pooled).set_index("model")
        for m in C.MODELS:
            ratio_of_means = float(averaged.loc[m, "precision"])
            mean_of_ratios = float(spread.loc[m, "precision_mean"])
            largest = max(largest, abs(ratio_of_means - mean_of_ratios))
            if round(ratio_of_means, 3) != round(mean_of_ratios, 3):
                differing += 1
    assert differing == 14, differing
    assert 0.022 < largest < 0.023, largest


def test_a_dispersion_may_not_be_built_from_reconstructed_false_positives():
    """The approximate fallback must not silently set the width of an interval."""
    from src import aggregate, stats
    folds, _pooled = aggregate.load()
    with pytest.raises(ValueError):
        stats.pooled_confusion_by_seed(folds, "A", None)


def test_the_reproducibility_page_lists_every_check_preflight_runs():
    """The status page drifted four checks behind the tool it describes.

    That page exists because "six reviews of this work have now each quoted at least
    one sentence from a superseded draft". It had become the superseded draft for
    exactly the fact it was written to pin down, so the agreement is now a test.
    """
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source = open(os.path.join(root, "tools", "preflight.py")).read()
    # The labels preflight prints, taken from the calls that produce them.
    labels = set(re.findall(r'run\("([^"]+)"', source))
    labels |= {"release", "duplicate keys", "placeholders", "decisions"}
    page = open(os.path.join(root, "manuscript", "REPRODUCIBILITY.md")).read()
    listed = {line.split("|")[1].strip()
              for line in page.splitlines() if line.startswith("| ")}
    missing = sorted(labels - listed)
    assert not missing, "REPRODUCIBILITY.md does not list: %s" % missing


def test_every_figure_is_placed_where_the_text_first_needs_it():
    """Seven figures were drawn, numbered, captioned, tabulated -- and never embedded.

    The assembled manuscript contained zero images while every sentence about where
    the figures belonged was true. Citing a figure, drawing a figure and showing a
    figure are three different things, and only the third is what a reader gets.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_figure_placement as cfp
    figs, excluded = cfp.paper_figures()
    dest = cfp.figure_destinations()
    embeds, captions, _cites = cfp.survey()
    s_embeds, _s_caps, _s_cites = cfp.survey([cfp.SUPPLEMENT_FILE])
    assert figs, "no paper figures are declared"
    for num, stem in figs.items():
        # Each figure is drawn in the document its split-map destination names, and
        # only there. Figure S1 was supplementary in the map, described in the text as
        # being in the supplementary material, and drawn in Section 7 -- so a check
        # that looked only at the article could not see the contradiction.
        where = s_embeds if dest.get(num) == "SUPPLEMENTARY" else embeds
        other = embeds if dest.get(num) == "SUPPLEMENTARY" else s_embeds
        assert len(where.get(stem, [])) == 1, (
            "Figure %s (%s) is %s in the split map and is placed %d time(s) there"
            % (num, stem, dest.get(num, "MAIN"), len(where.get(stem, []))))
        assert stem not in other, (
            "Figure %s is %s in the split map and is also drawn in the other document"
            % (num, dest.get(num, "MAIN")))
        assert where[stem][0]["caption_follows"] == num, (
            "Figure %s is not followed by its own caption" % num)
    for stem in excluded:
        assert stem not in embeds, "%s is not a paper figure and is in the paper" % stem


def test_no_editorial_apparatus_survives_into_the_submitted_article():
    """The drafting scaffolding must not reach a reviewer.

    Six section sources carry a "Notes for the next pass" block, a draft header with
    a date, a Hindi gloss or a not-for-submission span. Every one of those says, in
    its own words, that it is not part of the paper -- and the builder strips them.
    That was true but untested, so a change to the stripper, or a note written under
    a heading spelt slightly differently, would have put editorial apparatus into the
    submitted article with nothing to catch it.

    The test is on the ASSEMBLED manuscript, because that is the artefact that gets
    submitted; the sources are expected to keep their notes and are not checked.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    built = open(os.path.join(root, "manuscript", "MANUSCRIPT.md")).read()
    for marker, what in (
            ("Notes for the next pass", "a notes-for-the-next-pass block"),
            ("not-for-submission", "a not-for-submission marker"),
            ("— draft ", "a draft header"),
            ("हिंदी", "a Hindi gloss"),
            ("Verified from", "a verification blockquote")):
        assert marker not in built, (
            "the assembled manuscript contains %s (%r); the builder's stripper has "
            "stopped catching it, and this text would be submitted" % (what, marker))

    # And the sources really do still carry them, so the test is not passing because
    # the notes were deleted at source instead of stripped at build time.
    sources = [n for n in os.listdir(os.path.join(root, "manuscript"))
               if n.endswith(".md")]
    carried = [n for n in sources
               if "Notes for the next pass"
               in open(os.path.join(root, "manuscript", n)).read()]
    assert carried, ("no section source carries a notes block any more, so this test "
                     "is no longer checking that the stripper works")


def test_the_assembled_manuscript_actually_contains_its_figures():
    """Checked on the built article, not on the sources it was built from."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_figure_placement as cfp
    figs, _excluded = cfp.paper_figures()
    dest = cfp.figure_destinations()
    text = open(os.path.join(root, "manuscript", "MANUSCRIPT.md")).read()
    supp = open(os.path.join(root, "manuscript", cfp.SUPPLEMENT_FILE)).read()
    for num, stem in figs.items():
        # The built article shows its own figures; the supplementary document shows
        # the supplementary ones. A figure in neither is a figure no reader sees.
        shown_in, name = ((supp, cfp.SUPPLEMENT_FILE)
                          if dest.get(num) == "SUPPLEMENTARY"
                          else (text, "MANUSCRIPT.md"))
        assert "](../figures/%s.png)" % stem in shown_in, (
            "%s does not show Figure %s; the builder dropped the image line, or it "
            "was never in the source" % (name, num))
        if dest.get(num) == "SUPPLEMENTARY":
            assert "](../figures/%s.png)" % stem not in text, (
                "the built article shows Figure %s, which is supplementary" % num)
    # And the path resolves from where the manuscript sits, which is what makes the
    # image render rather than show as a broken link.
    for _num, stem in figs.items():
        assert os.path.exists(os.path.join(root, "manuscript", "..", "figures",
                                           stem + ".png"))


def test_the_architecture_figure_may_only_call_its_output_a_probability():
    """The terminal box added on 30 September 2026, and the condition on it.

    The figure now ends at "Drowsy probability (0-1)" rather than at a layer. That
    label is a claim about the model: it is true because the head's last layer is one
    sigmoid unit. Change the head to two units, or to a linear output, and the label
    becomes wrong while still looking fine -- so the drawing code raises instead, and
    this checks that it really does.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    from src import models as M
    from src import figures as F
    assert M.HEAD[-1] == ("dense", 1, "sigmoid"), (
        "the head no longer ends in a single sigmoid unit; the figure's output label "
        "and the manuscript sentence beside it both have to change")
    saved = M.HEAD
    try:
        M.HEAD = (("dense", 64, "relu"), ("dropout", 0.4), ("dense", 3, "softmax"))
        with pytest.raises(ValueError):
            F.figure6()
    finally:
        M.HEAD = saved
        F.figure6()          # redraw the real one, so the suite leaves no wrong file


def test_the_figures_are_numbered_in_order_of_their_appearance():
    """The defect fixed on 30 September 2026, and the guard against its return.

    The architecture drawing is cited in Section 5.3 and every other figure in
    Section 7, so under the old numbering the first figure a reader met was Figure 6
    and the last was Figure 1. This asserts the live state is in order, and then
    swaps two entries to confirm the checker would actually notice -- a guard that
    passes on correct input and also passes on incorrect input is not a guard.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_figure_placement as cfp
    figs, _excluded = cfp.paper_figures()
    embeds, _caps, _cites = cfp.survey()

    def sequence(mapping):
        main = [n for n in mapping if not n.startswith("S")]
        appearing = sorted((cfp.order_of(embeds, mapping[n]), n) for n in main
                           if embeds.get(mapping[n]))
        return [int(n) for _pos, n in appearing]

    live = sequence(figs)
    assert live == sorted(live), (
        "the figures appear in the order %s; they are not numbered in order of "
        "appearance" % live)
    assert live, "no figure is placed anywhere"

    swapped = dict(figs)
    swapped["1"], swapped[str(max(live))] = figs[str(max(live))], figs["1"]
    out_of_order = sequence(swapped)
    assert out_of_order != sorted(out_of_order), (
        "swapping the first and last figure numbers still looks ordered, so the "
        "ordering check cannot be detecting anything")


def test_every_paper_figure_is_vector_at_the_declared_resolution():
    """The artwork requirement, read off the files rather than off the prose.

    The instruction was 360 dpi. That number is only worth something if the files are
    actually at it, and it is only sufficient because the submitted artwork is vector
    PDF -- the guide's raster minimum for line drawings is 1000 dpi and 3,543 pixels,
    which a 360 dpi render of a 7-inch figure does not reach. This test holds both
    halves: the PNGs are at the declared dpi, and every figure has a real vector PDF
    beside it, so the exemption the 360 relies on is a fact and not an assumption.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_print_ready as pr
    import config as cfg
    figs, _excluded = pr.paper_figures()
    assert figs, "no paper figures are declared"
    for num, stem in figs.items():
        png = os.path.join(root, "figures", stem + ".png")
        pdf = os.path.join(root, "figures", stem + ".pdf")
        assert os.path.exists(pdf), "Figure %s has no vector PDF to submit" % num
        _w, _h, dpi = pr.png_pixels_and_dpi(png)
        assert dpi == cfg.FIGURE_DPI_RASTER, (
            "Figure %s is %s dpi and config declares %d"
            % (num, dpi, cfg.FIGURE_DPI_RASTER))
        strokes, _has_image = pr.pdf_is_vector(pdf)
        assert strokes >= 20, (
            "Figure %s's PDF carries %d drawing operator(s): it is a bitmap in a "
            "wrapper, and the raster minima the vector exemption waives would apply "
            "to it after all" % (num, strokes))


def test_the_raster_dpi_is_declared_with_the_minimum_it_does_not_meet():
    """360 is a decision, and a decision has to record what it decided against."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    import config as cfg
    assert cfg.FIGURE_DPI_RASTER == 360
    assert cfg.FIGURE_DPI_LINE_ART_MINIMUM == 1000
    assert cfg.FIGURE_DPI_RASTER < cfg.FIGURE_DPI_LINE_ART_MINIMUM
    source = open(os.path.join(root, "config.py")).read()
    where = source.split("FIGURE_DPI_RASTER")[0][-1400:]
    for needed in ("1000 dpi", "vector", "submitted"):
        assert needed in where, (
            "config.py sets the raster dpi without the comment saying %r; the number "
            "then looks like a default rather than a choice made against a known "
            "requirement" % needed)


def test_the_article_and_the_supplement_carry_the_same_title():
    """The title lives in four files, and on 3 October 2026 one of them was missed.

    When the title changed, ABSTRACT.md and CITATION.cff were updated and
    SUPPLEMENTARY.md was not, so the supplementary document -- which is submitted with
    the article and published exactly as received -- carried the superseded title. No
    check looked at it, because the supplement is not one of the twelve files the
    builder assembles, so every manuscript check had already passed.

    ABSTRACT.md deliberately keeps earlier titles inside its not-for-submission block;
    this test reads the title each document asserts, not every string in it.
    """
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def asserted_title(name, pattern):
        text = open(os.path.join(root, "manuscript", name)).read()
        text = re.sub(r"<!-- not-for-submission:start -->.*?"
                      r"<!-- not-for-submission:end -->", "", text, flags=re.S)
        text = re.sub(r"## Notes for the next pass.*", "", text, flags=re.S)
        m = re.search(pattern, text, re.S)
        assert m, "%s states no title where one is expected" % name
        return " ".join(m.group(1).split())

    article = asserted_title("ABSTRACT.md", r"## Title\s*\n+\*\*(.+?)\*\*")
    supplement = asserted_title("SUPPLEMENTARY.md",
                                r"# Supplementary Material\s*\n+\*\*(.+?)\*\*")
    assert article == supplement, (
        "the article's title is %r and the supplement's is %r; the supplement is "
        "submitted with the article and published exactly as received, so the two "
        "must agree" % (article, supplement))

    # CITATION.cff cites the article, so its preferred-citation must match too. Read
    # as YAML rather than by pattern: the file's own indentation is what distinguishes
    # the software title from the article's, and a regex gets that wrong.
    import yaml
    cff = yaml.safe_load(open(os.path.join(root, "CITATION.cff")))
    cited = " ".join(cff["preferred-citation"]["title"].split())
    assert cited == article, (
        "CITATION.cff's preferred-citation title is %r and the article's is %r"
        % (cited, article))


def test_the_reproducibility_page_states_how_many_checks_preflight_runs():
    """A prose count of the checks drifts exactly as the prose count of the tests did."""
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    page = open(os.path.join(root, "manuscript", "REPRODUCIBILITY.md")).read()
    words = {"Nineteen": 19, "Twenty": 20, "Twenty-one": 21, "Twenty-two": 22,
             "Twenty-three": 23, "Twenty-four": 24, "Twenty-five": 25}
    m = re.search(r"\b(%s) checks, one verdict" % "|".join(words), page)
    assert m, "REPRODUCIBILITY.md no longer states how many checks there are"
    # The table it introduces, from just after its header row to the blank line that
    # ends it. The split consumes the header, and the |---|---| rule does not begin
    # with "| ", so what is left counted this way is exactly the data rows.
    listed = page.split("Check | What fails it")[1].split("\n\n")[0]
    n = len([l for l in listed.splitlines() if l.startswith("| ")])
    assert words[m.group(1)] == n, (
        "REPRODUCIBILITY.md says %s checks and then lists %d" % (m.group(1), n))


# The split map. Sections 1-9 of the assembled paper run to about 28,500 words
# against a guide for authors that says a full paper "should normally be about 5,000".
# The plan is to move the audit apparatus to supplementary material -- and the danger
# in any such move is that a number, a test or a piece of reproducibility evidence
# leaves the article without anyone noticing. The corresponding author's rule is that
# scientific evidence is not hidden in the supplementary material. These tests hold it.

def _split_map():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_split_map as csm
    return csm, csm.load_map()


def test_every_unit_of_the_manuscript_is_classified_by_the_split_map():
    """No heading, table or figure may exist that nobody has decided about."""
    csm, data = _split_map()
    sections, order, tables = csm.units()
    problems = csm.check(data, sections, order, tables, csm.figures())
    assert not problems, "\n".join(problems)


def test_nothing_may_leave_the_article_without_saying_what_the_article_keeps():
    """The author's rule, exercised against a violation rather than asserted."""
    csm, data = _split_map()
    sections, order, tables = csm.units()
    victim = next(k for k, e in data["sections"].items()
                  if e.get("dest") == "SUPPLEMENTARY")
    kept = data["sections"][victim].pop("main_retains")
    try:
        problems = csm.check(data, sections, order, tables, csm.figures())
        assert any("does not say what the main article retains" in p
                   for p in problems), (
            "a section was moved out of the article with no statement of what stays "
            "behind, and the checker allowed it")
    finally:
        data["sections"][victim]["main_retains"] = kept


def test_an_unclassified_new_section_is_caught_rather_than_silently_kept():
    """The failure this map exists to prevent, reproduced."""
    csm, data = _split_map()
    sections, order, tables = csm.units()
    fake = "9.1 A section added by test_pipeline"
    sections[fake] = dict(level=2, words=400, line=1, repeats=1)
    order = order + [fake]
    problems = csm.check(data, sections, order, tables, csm.figures())
    assert any(fake in p and "not in the map" in p for p in problems), (
        "a new section appeared and no one was asked where it belongs")


def test_the_split_map_is_a_plan_until_it_says_it_is_applied():
    """While it is a plan, a target above the current length is a contradiction.

    Once applied, the test reverses: the map then holds the article's length rather
    than recording an intention about it. Getting this backwards would let the map
    pass both before and after the cutting while meaning nothing in either state.
    """
    csm, data = _split_map()
    sections, order, tables = csm.units()
    assert data["applied"] is False, (
        "the map says it has been applied; if the cutting really is done, this test "
        "should be updated deliberately and not to make a suite go green")
    victim = next(k for k, e in data["sections"].items()
                  if e.get("dest") == "MAIN" and e.get("target_words"))
    was = data["sections"][victim]["target_words"]
    try:
        data["sections"][victim]["target_words"] = sections[victim]["words"] + 1
        problems = csm.check(data, sections, order, tables, csm.figures())
        assert any("not a reduction" in p for p in problems)
    finally:
        data["sections"][victim]["target_words"] = was


def _markdown_grids(path):
    """Every markdown grid in a file, as (header, rows)."""
    lines = open(path).read().splitlines()
    out, i = [], 0
    while i < len(lines):
        rule = (i + 1 < len(lines)
                and set(lines[i + 1].replace("|", "").strip()) <= set("-: "))
        if lines[i].startswith("|") and rule:
            header = [c.strip() for c in lines[i].strip("|").split("|")]
            j, rows = i + 2, []
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip("|").split("|")])
                j += 1
            out.append((header, rows))
            i = j
        else:
            i += 1
    return out


def test_a_table_split_across_both_documents_loses_no_cell():
    """Tables 4 and 6 are reduced in the article and complete in the supplement.

    The danger in reducing a table is that it stops being a reduction: a column is
    dropped from the article and never lands anywhere, or the two copies drift and
    the article prints one number while the supplement prints another. This checks
    both halves — the supplement has strictly more columns and the same rows, and
    every cell the article keeps is the same cell in the supplement.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art = _markdown_grids(os.path.join(root, "manuscript", "RESULTS.md"))
    sup = _markdown_grids(os.path.join(root, "manuscript", "SUPPLEMENTARY.md"))

    def find(grids, lead):
        hits = [g for g in grids if g[0][:len(lead)] == lead]
        assert hits, "no grid starting %s" % lead
        return hits[0]

    for lead_a, lead_s, label in ((["Arm", "Model", "Recall"],
                                   ["Arm", "Model", "TN"], "Table 4 / S2"),
                                  (["Arm", "Model", "Brier raw"],
                                   ["Arm", "Model", "ECE raw"], "Table 6 / S4")):
        small, big = find(art, lead_a), find(sup, lead_s)
        assert len(big[0]) > len(small[0]), "%s: the supplement is not the fuller one"
        assert len(big[1]) == len(small[1]), (
            "%s: %d rows in the article and %d in the supplement"
            % (label, len(small[1]), len(big[1])))
        si = {c: k for k, c in enumerate(small[0])}
        bi = {c: k for k, c in enumerate(big[0])}
        for rs, rb in zip(small[1], big[1]):
            for c in small[0]:
                assert rs[si[c]] == rb[bi[c]], (
                    "%s: column %r reads %r in the article and %r in the supplement"
                    % (label, c, rs[si[c]], rb[bi[c]]))


def test_the_projected_article_still_carries_every_main_finding_table_or_figure():
    """The five figures and the tables the headline claims are read from stay in.

    Not a style preference: each of these is the sole place a reported claim can be
    checked. If one moves, the claim that cites it has to move with it, and the map
    is then making a scientific decision under the cover of a formatting one.
    """
    _csm, data = _split_map()
    # Renumbered on 30 September 2026, when Tables 1, 8 and 9 moved to the
    # supplement and the article's own tables were closed up to run from 1.
    # 1 the three constructions, 2 the architectures, 3 ranking quality, 5 the
    # Brier partition: each is the sole place a headline claim can be checked.
    for num in ("1", "2", "3", "5"):
        assert data["tables"][num]["dest"] == "MAIN", (
            "Table %s is where a headline claim is read from" % num)
    # 4 the confusion matrices and 6 the calibration table: too wide for a
    # two-column page in full, so reduced in the article and complete in the
    # supplement -- and the reduced form must say what it shows.
    for num in ("4", "6"):
        assert data["tables"][num]["dest"] == "BOTH" and data["tables"][num]["main_form"]
    for num in ("S1", "S3", "S5"):
        assert data["tables"][num]["dest"] == "SUPPLEMENTARY"
        assert data["tables"][num]["main_retains"], (
            "Table %s left the article without saying what the article keeps" % num)
    # Six main figures, numbered in order of first appearance: the architecture
    # drawing is cited in 5.3 and so is Figure 1, and the author's decision of
    # 30 September 2026 is that it stays in the article rather than moving to
    # supplementary. Only the multi-panel overview is supplementary.
    for num in ("1", "2", "3", "4", "5", "6"):
        assert data["figures"][num]["dest"] == "MAIN", "Figure %s must stay" % num
    assert data["figures"]["S1"]["dest"] == "SUPPLEMENTARY"
    assert not any(e.get("becomes", "").startswith("Figure S2")
                   for e in data["figures"].values() if isinstance(e, dict)), (
        "something is still scheduled to become Figure S2; the proposal to move the "
        "architecture drawing out of the article was withdrawn on 30 September 2026")


def test_the_two_parameter_counts_are_derived_from_the_layer_spec_not_typed():
    """config.PARAMS for the two prespecified models, against the arithmetic.

    An independent check of these numbers on 25 September 2026 came out at 184,737
    for the CNN-BiLSTM against the registered 180,641 -- a difference of exactly
    4,096 -- by assuming both models end in the same head. They end in the same
    HEAD *tuple*, but the CNN's Dense(64) receives 128 features from global average
    pooling while the CNN-BiLSTM's receives 64, the second bidirectional layer's 32
    units in each direction. (128 - 64) x 64 = 4,096.

    The registered numbers were right. They were also typed, which is why an hour
    went into establishing that. They are now derived from the same tuples the
    builders use, so the next check of them is this test.
    """
    from src import models as M
    for name in ("CNN", "CNN-BiLSTM"):
        assert M.trainable_parameters(name) == C.PARAMS[name], name
    assert (C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"]) == 135936

    # The head asymmetry itself, since it is the thing that misleads.
    trunk_out = [i[1] for i in M.CONV_TRUNK if i[0] == "conv"][-1]
    bilstm_out = 2 * M.RECURRENT_BLOCK[-1][1]
    dense_units = [i for i in M.HEAD if i[0] == "dense"][0][1]
    assert (trunk_out - bilstm_out) * dense_units == 4096

    # A reference implementation has no spec here and must refuse rather than guess.
    for name in ("EEGNet", "ShallowConvNet", "DeepConvNet"):
        with pytest.raises(ValueError):
            M.trainable_parameters(name)


def test_the_audit_snapshot_carries_the_sources_an_audit_needs():
    """Everything a claim can be checked against, in one bundle.

    Six snapshots were assembled by hand on 24-25 September 2026 and each was missing
    something the audit of it then needed: a figure and a registry from different
    days, then src/models.py (so the parameter counts had to be checked against the
    prose instead of the code, and came out 4,096 high), then tools/master_file.py
    and the tests (so a generator that had just been corrected could not be read).
    Curating a bundle by hand is the same failure as typing a number by hand.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import snapshot

    trees = {name for name, _ in snapshot.TREES}
    for needed in ("src", "tools", "tests"):
        assert needed in trees, "%s is not in the snapshot" % needed
    for needed in ("results/MASTER_NUMBERS.csv", "manuscript/MANUSCRIPT.md",
                   "manuscript/MASTER_FILE.md", "config.py"):
        assert needed in snapshot.FILES, needed

    # Named individually because each was the specific thing an audit could not read.
    for tree, suffixes in snapshot.TREES:
        if tree in ("src", "tools", "tests"):
            assert ".py" in suffixes, tree
    assert os.path.exists(os.path.join(root, "tools", "master_file.py"))
    assert os.path.exists(os.path.join(root, "src", "models.py"))

    # Every input the bundled checks read must travel with them. Running
    # check_submission_ready.py inside a snapshot that lacked LICENSE, CITATION.cff
    # and the section sources reported all four items PENDING -- which says nothing
    # about the repository, and is worse than not running it.
    sys.path.insert(0, os.path.join(root, "tools"))
    import build_manuscript as bm
    for name in bm.SECTION_FILES:
        assert "manuscript/" + name in snapshot.FILES, name
    for needed in ("LICENSE", "CITATION.cff", "manuscript/WITHDRAWN.md",
                   "manuscript/DECISION_SHEET.md"):
        assert needed in snapshot.FILES, needed


def test_the_capacity_ratios_in_the_prose_are_the_ratios_the_counts_give():
    """A derived ratio drifts exactly like a derived count.

    Three places said the recurrent block's 135,936 added parameters were "four
    times the CNN's total". 135,936 / 44,705 is 3.04; it is the CNN-BiLSTM's TOTAL
    that is 4.04 times the CNN. The counts were right and the arithmetic on top of
    them was not, which is the same failure one layer up.
    """
    added = C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"]
    assert round(added / C.PARAMS["CNN"], 2) == 3.04
    assert round(C.PARAMS["CNN-BiLSTM"] / C.PARAMS["CNN"], 2) == 4.04

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("RESULTS.md", "RELATED_WORK.md", "DISCUSSION.md", "MASTER_FILE.md"):
        text = open(os.path.join(root, "manuscript", name)).read()
        where = "{:,} parameters".format(added)
        if where not in text:
            continue
        # Wherever the added figure is quoted with a multiple, it must be 3.04 and
        # the four-times claim must belong to the total.
        assert "four times the CNN" not in text, name
        assert "three times the\nCNN" not in text, name


def test_the_architectures_section_describes_the_model_the_code_builds():
    """The prose against src/models.py's layer spec, item by item.

    The Architectures section said the BiLSTM layers used "recurrent dropout 0.4".
    The code passes Keras's `dropout` argument and never sets `recurrent_dropout`;
    the two drop different things, and a reimplementation from the paper would have
    built a different model. Nothing caught it because the layers were spelled out
    in the builders and retyped in the prose, and a retyping drifts.
    """
    from src import models as M
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prose = open(os.path.join(root, "manuscript", "ARCHITECTURES.md")).read()

    convs = [i for i in M.CONV_TRUNK if i[0] == "conv"]
    assert len(convs) == 3, "the prose says three convolution blocks"
    for _kind, filters, length in convs:
        assert "%d filters of length %d" % (filters, length) in prose or \
               "%d of length %d" % (filters, length) in prose, \
               "no prose for Conv1D(%d, %d)" % (filters, length)
    pools = {i[1] for i in M.CONV_TRUNK if i[0] == "pool"}
    assert pools == {2} and "max-pooling of stride 2" in prose
    drops = {i[1] for i in M.CONV_TRUNK if i[0] == "dropout"}
    assert drops == {0.3} and "dropout of 0.3" in prose
    assert "batch normalisation" in prose

    units = [i[1] for i in M.RECURRENT_BLOCK]
    assert units == [64, 32] and "64 units returning sequences, then 32 units" in prose
    rates = {i[3] for i in M.RECURRENT_BLOCK}
    assert rates == {0.4}, rates
    # The whole point of this test.
    assert "dropout 0.4 on its inputs" in prose
    assert "recurrent dropout 0.4" not in prose, \
        "the code sets `dropout`, not `recurrent_dropout`"

    dense = [i for i in M.HEAD if i[0] == "dense"]
    assert [d[1] for d in dense] == [64, 1]
    assert dense[-1][2] == "sigmoid" and "single sigmoid output" in prose
    head_drop = [i[1] for i in M.HEAD if i[0] == "dropout"]
    assert head_drop == [0.4] and "dropout 0.4" in prose

    # And the parameter counts the section quotes.
    for name in ("CNN", "CNN-BiLSTM"):
        assert "{:,}".format(C.PARAMS[name]) in prose, name
    assert "{:,}".format(C.PARAMS["CNN-BiLSTM"] - C.PARAMS["CNN"]) in prose


def test_pooled_recall_is_nan_without_a_warning_when_no_drowsy_windows_exist():
    """The undefined case is named, not stumbled into.

    Pooled recall weights folds by their drowsy count and is undefined when that
    total is zero. numpy used to divide by zero here, return nan, and print a
    RuntimeWarning on every run of this suite. The value is still nan -- that is the
    honest answer -- but it is now returned deliberately, and no warning is emitted,
    so the next warning this suite prints will be a new one worth reading.
    """
    import warnings
    from src import stats
    empty = pd.DataFrame([
        dict(ar="A", arm=C.ARMS["A"]["key"], model=m, seed=s, subject=sub,
             recall=0.0, n_drowsy=0, auc=0.5, pr_auc=0.1, bal_acc=0.5,
             f1=0.0, precision=0.0, epochs=1, val_subs="S1+S2")
        for m in C.MODELS for s in C.SEEDS for sub in C.SUBJECTS])
    with warnings.catch_warnings():
        warnings.simplefilter("error")          # any warning fails this test
        out = stats.recall_conventions(empty, "A")
    assert len(out) == len(C.MODELS)
    assert out.pooled.isna().all(), "an undefined pooled recall must be nan"


def test_bh_and_by_agree_with_their_definitions_on_hand_cases():
    """The two step-up procedures, on cases whose answer can be worked out."""
    from src import multiplicity as M

    # Nothing below any threshold.
    assert M.bh([0.9, 0.8, 0.7]) == 0
    assert M.by([0.9, 0.8, 0.7]) == 0
    # Everything at zero: both reject all.
    assert M.bh([0.0] * 5) == 5
    assert M.by([0.0] * 5) == 5
    # BH is a step-UP: a large p does not block a small one below it. With m = 3 and
    # alpha = 0.05 the largest threshold is 0.05, so p = 0.04 at rank 3 rejects all
    # three even though the other two are far above their own thresholds.
    assert M.bh([0.04, 0.04, 0.04], alpha=0.05) == 3
    # BY divides by the harmonic number, so it can never reject more than BH.
    for ps in ([0.001, 0.02, 0.3], [0.04, 0.04, 0.04], [0.0001] * 10):
        assert M.by(ps) <= M.bh(ps)


def test_the_multiplicity_universe_is_one_hundred_and_ninety():
    """The denominator, recomputed. It is the one number in R1 that is not a choice.

    Three counts were in circulation before this was measured -- 175-181 from the
    registry rows, 117 and 163 from printed p-values -- none counting the same thing.
    """
    import pandas as pd
    from src import aggregate, multiplicity as M
    folds, pooled = aggregate.load()
    frame = M.table(folds, pooled)
    total = frame[(frame.scope == "summary")
                  & (frame.name == "all registered comparisons")].iloc[0]
    assert int(total.n_tests) == 190, int(total.n_tests)
    families = frame[frame.scope == "family"]
    assert int(families.n_tests.sum()) == 190, "the families must partition the whole"
    # The three summary rows must be a partition too, not overlapping sets.
    prevalence = frame[frame.name == "drowsy-count / prevalence family"].iloc[0]
    remaining = frame[frame.name == "remaining comparisons"].iloc[0]
    assert int(prevalence.n_tests) + int(remaining.n_tests) == 190
    assert int(prevalence.n_nominal) + int(remaining.n_nominal) == int(total.n_nominal)


def test_the_holm_ceiling_for_the_five_point_spearman_floor_is_an_exact_equality():
    """2/5! and alpha/3 are the same rational. Section 6.5.1 rests on this.

    Not a floating-point coincidence: both are 1/60. The accuracy-against-recall
    result therefore sits exactly on the Holm boundary for its three-test family,
    and whether it survives depends on whether the comparison is <= or <. This is
    checked in exact arithmetic so that no rounding can hide it.
    """
    import math as _math
    from fractions import Fraction
    alpha = Fraction(5, 100)
    assert Fraction(2, _math.factorial(5)) == Fraction(1, 60) == alpha / 3
    assert C.holm_family_ceiling(C.P_FLOOR_SPEARMAN_5) == 3
    # The other two floors reach their ceilings strictly, which is why this one is
    # the boundary case and they are not.
    assert C.holm_family_ceiling(C.P_FLOOR_WILCOXON_10) == 25
    assert Fraction(2, 2 ** 10) < alpha / 25
    assert C.holm_family_ceiling(2.0 / 2 ** 9) == 12
    assert Fraction(2, 2 ** 9) < alpha / 12


def test_a_tied_subject_lowers_the_effective_n_and_raises_the_floor():
    """scipy discards zero differences, so a tie makes it a nine-pair test.

    Twenty-one comparisons in this study tie on at least one subject and one ties on
    three. A registry note once derived b_wins as n - a_wins, which counts a tie as
    an improvement, and reported 10/10 where the manuscript correctly said 9/10.
    """
    from src import aggregate, stats
    folds, _pooled = aggregate.load()
    r = stats.paired(folds, "C", "CNN", "CNN-BiLSTM", "f1")
    assert r["ties"] == 1
    assert r["n"] == 10 and r["n_effective"] == 9
    assert r["a_wins"] + r["b_wins"] + r["ties"] == r["n"]
    assert r["b_wins"] == 9, "the count the manuscript prints"
    assert abs(r["p_floor"] - 2.0 / 2 ** 9) < 1e-12
    assert r["p_floor"] > C.P_FLOOR_WILCOXON_10, "a tie can only raise the floor"
    # And an untied comparison keeps the ten-pair floor.
    clean = stats.paired(folds, "A", "EEGNet", "CNN", "auc")
    assert clean["ties"] == 0 and clean["n_effective"] == 10
    assert abs(clean["p_floor"] - C.P_FLOOR_WILCOXON_10) < 1e-12


def _preflight():
    """tools/preflight.py as a module, without running it."""
    import importlib
    import sys as _sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (os.path.join(root, "tools"), root):
        if p not in _sys.path:
            _sys.path.insert(0, p)
    return importlib.import_module("preflight")


def test_audit_scope_is_derived_from_the_builder_not_restated():
    """preflight's section list must BE the builder's, not a copy that can drift."""
    pre = _preflight()
    import build_manuscript as bm
    assert pre.SECTIONS == bm.SECTION_FILES, (
        "preflight.SECTIONS has drifted from build_manuscript.SECTION_FILES: %r vs %r"
        % (pre.SECTIONS, bm.SECTION_FILES))
    assert pre.SECTIONS == [name for name, _label in bm.ORDER], (
        "SECTION_FILES no longer matches ORDER")
    # The two files whose omission was R37. Named explicitly, because this is the
    # regression test for a defect that actually shipped.
    for name in ("CODE_AVAILABILITY.md", "REFERENCES.md"):
        assert name in pre.SECTIONS, "%s is assembled but out of audit scope" % name
        assert name in pre.scope("placeholders"), (
            "%s is not placeholder-checked; R37 has come back" % name)
        assert name in pre.scope("withdrawn"), (
            "%s is not withdrawn-checked; R37 has come back" % name)


def test_every_audit_scope_exclusion_is_named_with_a_reason():
    """An exclusion is a decision recorded in code. A gap is a bug. Keep them apart."""
    pre = _preflight()
    assert pre.SCOPE_EXCLUSIONS, "no exclusions declared -- has the mechanism gone?"
    for check, excluded in pre.SCOPE_EXCLUSIONS.items():
        assert isinstance(excluded, dict), "%s: exclusions must be name -> reason" % check
        for name, reason in excluded.items():
            # A stale exclusion for a file the builder no longer assembles is itself a
            # drift, and reads as if the file were still being handled.
            assert name in pre.SECTIONS, (
                "%s excludes %s, which the builder does not assemble"
                % (check, name))
            assert isinstance(reason, str) and len(reason.strip()) >= 40, (
                "%s excludes %s with no usable reason: %r" % (check, name, reason))
            assert name not in pre.scope(check), (
                "%s declares %s excluded but scope() still returns it" % (check, name))


def test_a_new_section_is_audited_without_anyone_remembering_to_add_it():
    """The one that closes the class: inject a section, assert it is in scope."""
    pre = _preflight()
    import build_manuscript as bm

    fake = "ZZ_SYNTHETIC_SECTION_FOR_TEST.md"
    saved_order, saved_files = list(bm.ORDER), list(bm.SECTION_FILES)
    saved_sections = list(pre.SECTIONS)
    try:
        bm.ORDER.append((fake, "Synthetic"))
        bm.SECTION_FILES.append(fake)
        pre.SECTIONS.append(fake)

        for check in ("placeholders", "withdrawn", "scan"):
            assert fake in pre.scope(check), (
                "a new section in ORDER is not read by the %s check -- the scope is "
                "not derived, and R37 can recur" % check)

        # And the converse: once declared excluded, it leaves that one scope and
        # stays in the others. An exclusion must be narrow and visible.
        pre.SCOPE_EXCLUSIONS.setdefault("scan", {})[fake] = (
            "synthetic file used only by test_pipeline to prove the mechanism works")
        assert fake not in pre.scope("scan")
        assert fake in pre.scope("placeholders")
        assert fake in pre.scope("withdrawn")
    finally:
        pre.SCOPE_EXCLUSIONS.get("scan", {}).pop(fake, None)
        bm.ORDER[:] = saved_order
        bm.SECTION_FILES[:] = saved_files
        pre.SECTIONS[:] = saved_sections
    assert fake not in pre.SECTIONS, "the test did not clean up after itself"


# The journal's limits used to be a dict inside tools/check_frontmatter.py under a
# comment reading "checked 16 September 2026". Three things were wrong with that at
# once: the date was the only evidence for 250, it could not age visibly, and the
# same paragraph also asserted that the abstract must be UNSTRUCTURED -- which the
# guide for authors does not say. A limit with no source beside it is a remembered
# number, and this repository's whole discipline is that a number carries its
# provenance. These four tests hold the separation in place.

def _requirements():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tools"))
    import check_frontmatter as cf
    return cf, cf.requirements()


def test_every_journal_limit_carries_the_sentence_it_came_from():
    """No value without its quotation, and every quotation containing its value."""
    _cf, data = _requirements()
    assert data["limits"], "no limits are recorded at all"
    for name, entry in data["limits"].items():
        assert isinstance(entry["value"], int), name
        quote = entry["quote"]
        assert len(quote) > 20, "%s: %r is not a sentence" % (name, quote)
        assert str(entry["value"]) in quote, (
            "%s is %d but the sentence quoted for it does not contain that number, "
            "so one of the two has been edited without the other"
            % (name, entry["value"]))


def test_the_front_matter_checker_holds_no_limits_of_its_own():
    """The numbers are data. If they reappear in the code, the split has failed."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source = open(os.path.join(root, "tools", "check_frontmatter.py")).read()
    body = "\n".join(l for l in source.splitlines()
                     if not l.lstrip().startswith("#"))
    body = body.split('"""', 2)[-1]          # past the module docstring
    for literal in ("250", "85"):
        assert literal not in body, (
            "tools/check_frontmatter.py contains the literal %s; the limits belong "
            "to journal_requirements.json and the script owns only the counting"
            % literal)


def test_a_missing_requirements_file_is_an_error_and_not_a_default():
    """Falling back to built-in numbers would restore the unsourced limit."""
    cf, _data = _requirements()
    with pytest.raises(SystemExit):
        cf.requirements(os.path.join(tempfile.gettempdir(), "no-such-file.json"))


def test_the_recorded_verification_goes_stale_on_its_own_declared_interval():
    """The date is reported, and expires; it is not a standing claim of currency."""
    import datetime
    cf, data = _requirements()
    when = datetime.date.fromisoformat(data["verified"]["date"])
    window = data["verified"]["recheck_after_days"]
    assert window and window <= 365, "a re-read interval of over a year is not one"
    assert not cf.stale(data, today=when + datetime.timedelta(days=window))
    assert cf.stale(data, today=when + datetime.timedelta(days=window + 1))
    # And the submission gate is what holds it open, not the front-matter checker:
    # a paper that is green today must not turn red at midnight.
    import check_submission_ready as sub
    assert sub.check_journal_guide() == [] or cf.stale(data)


def test_the_paper_does_not_state_a_journal_requirement_the_guide_does_not_make():
    """The 'unstructured abstract' claim, specifically, and by name.

    It appeared in two places as a requirement of this journal. It is not one: the
    guide asks for a concise and factual abstract of at most 250 words and says
    nothing about structure. Asserting a rule the journal has not made is the same
    class of error as misreporting one it has.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for rel in ("manuscript/ABSTRACT.md", "tools/check_frontmatter.py"):
        text = open(os.path.join(root, rel)).read()
        for line in text.splitlines():
            low = line.lower()
            if "unstructured" not in low:
                continue
            assert "does not say" in low or "no longer" in low or "also said" in low, (
                "%s calls the abstract unstructured without saying that this is the "
                "paper's choice and not the journal's rule: %r" % (rel, line.strip()))


def test_the_reproducibility_page_states_the_size_of_the_suite_it_describes():
    """It said 37 while the suite held 53. A count in prose is a count that drifts."""
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    page = open(os.path.join(root, "manuscript", "REPRODUCIBILITY.md")).read()
    m = re.search(r"any of the ([0-9]+) tests", page)
    assert m, "REPRODUCIBILITY.md no longer states how many tests there are"
    assert int(m.group(1)) == len(_all_tests()), (
        "REPRODUCIBILITY.md says %s tests; the suite has %d"
        % (m.group(1), len(_all_tests())))


def main():
    failed = []
    for name, fn in _all_tests():
        try:
            fn()
            print("  PASS  %s" % name)
        except Exception as exc:                       # noqa: BLE001
            failed.append((name, exc))
            print("  FAIL  %s: %s" % (name, exc))
    print("\n%d passed, %d failed, %d total"
          % (len(_all_tests()) - len(failed), len(failed), len(_all_tests())))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
