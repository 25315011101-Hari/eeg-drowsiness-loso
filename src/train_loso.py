"""Leave-one-subject-out training for one architecture on one arm.

    python -m src.train_loso --arm C --model EEGNet
    python -m src.train_loso --arm C                  # all five

Protocol, identical everywhere:

  * ten folds, one per subject.  The held-out subject is never seen in any form.
  * of the nine remaining subjects, N_VAL are drawn as the validation set with a
    per-seed RandomState, and the other seven train the model.  The draw is made
    for every subject in order, including subjects already finished on a resumed
    run, so resuming cannot change which validation pair a fold gets.
  * z-score statistics come from the training subjects only.
  * class weights come from the training fold only.
  * early stopping on validation PR-AUC, patience config.PATIENCE, best weights
    restored.
  * five seeds, so 50 folds per architecture per arm.

Outputs, per model and seed, under RESULT_DIR/<arm>/:

  folds_<model>_seed<n>.csv    one row per fold: the subject-level metrics
  preds_<model>_seed<n>.csv    per-window predictions, used to resume
  probs_<model>_seed<n>.npz    per-window predictions, used by calibrate.py
  pooled_<model>_seed<n>.csv   metrics over all ten folds concatenated

The per-fold CSV is rewritten after every fold, so an interrupted run loses at
most one fold.  Re-running the same command resumes.

A fold in which the model predicts no drowsy window at 0.5 is degenerate: F1 is
0 and balanced accuracy is 0.500 by construction.  These are kept, not dropped.
Dropping them would silently improve every threshold-dependent number.
"""

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from src import models  # noqa: E402


def load_arm(arm, data_dir=None):
    """Load an arm's npz and refuse to proceed unless it is the arm it claims to be."""
    spec = C.ARMS[arm]
    path = os.path.join(data_dir or C.DATA_DIR, spec["npz"])
    if not os.path.exists(path):
        raise FileNotFoundError(
            "%s not found. Build it first:  python -m src.preprocess --arm %s"
            % (path, arm))
    d = np.load(path, allow_pickle=True)
    X, y, groups = d["X"], d["y"], d["groups"]

    if int(y.sum()) != spec["n_drowsy"]:
        raise ValueError("arm %s expects %d drowsy windows, file has %d"
                         % (arm, spec["n_drowsy"], int(y.sum())))
    if X.shape[0] != spec["n_windows"]:
        raise ValueError("arm %s expects %d windows, file has %d"
                         % (arm, spec["n_windows"], X.shape[0]))
    if "balance_mode" in d.files:
        if str(d["balance_mode"]) != spec["balance"] or str(d["trim_mode"]) != spec["trim"]:
            raise ValueError("file is trim=%s balance=%s, arm %s is trim=%s balance=%s"
                             % (d["trim_mode"], d["balance_mode"], arm,
                                spec["trim"], spec["balance"]))
    got = {s: int(y[groups == s].sum()) for s in spec["per_subject_drowsy"]}
    if got != spec["per_subject_drowsy"]:
        raise ValueError("per-subject drowsy counts differ from arm %s: %s" % (arm, got))
    print("using %s | X %s | drowsy %d (%.2f %%)"
          % (path, X.shape, int(y.sum()), 100 * y.mean()), flush=True)
    return X, y, groups


def fold_metrics(name, seed, subject, y_true, prob, epochs, val_subs):
    """Subject-level metrics for one fold. ROC-AUC and PR-AUC need both classes."""
    pred = (prob >= C.FIXED_THRESHOLD).astype(int)
    has_pos = y_true.sum() > 0
    return dict(model=name, seed=seed, subject=subject,
                n_drowsy=int(y_true.sum()),
                auc=roc_auc_score(y_true, prob) if has_pos else np.nan,
                pr_auc=average_precision_score(y_true, prob) if has_pos else np.nan,
                bal_acc=balanced_accuracy_score(y_true, pred),
                f1=f1_score(y_true, pred, zero_division=0),
                precision=precision_score(y_true, pred, zero_division=0),
                recall=recall_score(y_true, pred, zero_division=0),
                epochs=epochs,
                val_subs="+".join(val_subs))


def run_one(name, seed, X, y, groups, out_dir, verbose=True):
    """One architecture, one seed, ten folds. Resume-safe."""
    import tensorflow as tf

    subjects = sorted(set(groups.tolist()), key=lambda s: int(s[1:]))
    samples, chans = X.shape[1], X.shape[2]
    tag = "%s_seed%d" % (name.replace("-", ""), seed)
    f_folds = os.path.join(out_dir, "folds_%s.csv" % tag)
    f_preds = os.path.join(out_dir, "preds_%s.csv" % tag)

    rows, yt, pp, sub, done = [], [], [], [], set()
    if os.path.exists(f_folds) and os.path.exists(f_preds):
        rows = pd.read_csv(f_folds).to_dict("records")
        prev = pd.read_csv(f_preds)
        yt, pp, sub = prev.y_true.tolist(), prev.y_prob.tolist(), prev.subject.tolist()
        done = {r["subject"] for r in rows}
        if verbose:
            print("  resume %s: %d folds already done" % (tag, len(done)), flush=True)

    rng = np.random.RandomState(seed)
    for test_sub in subjects:
        train_subs = [s for s in subjects if s != test_sub]
        # Draw for every subject, finished or not, so the validation assignment
        # of a fold does not depend on where a previous run stopped.
        val_subs = [str(v) for v in rng.choice(train_subs, C.N_VAL, replace=False)]
        if test_sub in done:
            continue

        va = np.isin(groups, val_subs)
        tr = np.isin(groups, [s for s in train_subs if s not in val_subs])
        te = groups == test_sub

        sh = lambda A: models.shape_for(name, A)          # noqa: E731
        ax = models.norm_axes(name)
        Xtr, ytr = sh(X[tr]), y[tr]
        mu = Xtr.mean(axis=ax, keepdims=True)
        sd = Xtr.std(axis=ax, keepdims=True) + 1e-8
        Xtr = (Xtr - mu) / sd
        Xva, yva = (sh(X[va]) - mu) / sd, y[va]
        Xte, yte = (sh(X[te]) - mu) / sd, y[te]

        # Weight the minority class by the training fold's own imbalance ratio.
        cw = {0: 1.0, 1: int((ytr == 0).sum()) / max(int(ytr.sum()), 1)}

        tf.keras.backend.clear_session()
        tf.keras.utils.set_random_seed(seed)
        model = models.build(name, samples, chans)
        es = tf.keras.callbacks.EarlyStopping(monitor="val_prauc", mode="max",
                                              patience=C.PATIENCE,
                                              restore_best_weights=True)
        h = model.fit(Xtr, ytr, validation_data=(Xva, yva), epochs=C.EPOCHS,
                      batch_size=C.BATCH, class_weight=cw, callbacks=[es],
                      shuffle=True, verbose=0)
        prob = model.predict(Xte, verbose=0).ravel()

        yt.extend(yte.tolist())
        pp.extend(prob.tolist())
        sub.extend([test_sub] * len(yte))
        rows.append(fold_metrics(name, seed, test_sub, yte, prob,
                                 len(h.history["loss"]), val_subs))
        if verbose:
            r = rows[-1]
            print("  %-15s %-4s seed %-3d AUC=%.3f PR-AUC=%.3f (%d ep) val=%s"
                  % (name, test_sub, seed, r["auc"], r["pr_auc"], r["epochs"],
                     r["val_subs"]), flush=True)

        pd.DataFrame(rows).to_csv(f_folds, index=False)
        pd.DataFrame(dict(subject=sub, y_true=yt, y_prob=pp)).to_csv(f_preds, index=False)

    write_pooled(name, seed, np.array(yt), np.array(pp), np.array(sub), out_dir, tag)
    return pd.DataFrame(rows)


def write_pooled(name, seed, yt, pp, sub, out_dir, tag):
    """Concatenate the ten folds of one seed and score them once.

    Pooling weights each subject by its window count, which is why the paper
    keeps pooled and subject-averaged values in separate tables.
    """
    yp = (pp >= C.FIXED_THRESHOLD).astype(int)
    np.savez(os.path.join(out_dir, "probs_%s.npz" % tag),
             y_true=yt, y_prob=pp, subject=sub)
    pd.DataFrame([dict(model=name, seed=seed,
                       auc=roc_auc_score(yt, pp),
                       pr_auc=average_precision_score(yt, pp),
                       bal_acc=balanced_accuracy_score(yt, yp),
                       brier=float(np.mean((pp - yt) ** 2)),
                       fp=int(confusion_matrix(yt, yp)[0, 1]))]
                 ).to_csv(os.path.join(out_dir, "pooled_%s.csv" % tag), index=False)


def run_arm(arm, model_names=None, data_dir=None, result_dir=None, verbose=True):
    out_dir = os.path.join(result_dir or C.RESULT_DIR, arm)
    os.makedirs(out_dir, exist_ok=True)
    X, y, groups = load_arm(arm, data_dir)

    for name in (model_names or C.MODELS):
        t0 = time.time()
        for seed in C.SEEDS:
            tag = "%s_seed%d" % (name.replace("-", ""), seed)
            if os.path.exists(os.path.join(out_dir, "pooled_%s.csv" % tag)):
                if verbose:
                    print("skip (already done): %s seed %d" % (name, seed), flush=True)
                continue
            run_one(name, seed, X, y, groups, out_dir, verbose=verbose)
        if verbose:
            print(">>> %s finished in %.1f min\n" % (name, (time.time() - t0) / 60),
                  flush=True)
    return out_dir


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True, choices=sorted(C.ARMS))
    ap.add_argument("--model", action="append", choices=C.MODELS,
                    help="repeatable; default is all five")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--result-dir", default=None)
    a = ap.parse_args(argv)
    if not models.check_arl_available():
        return 1
    run_arm(a.arm, a.model, a.data_dir, a.result_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
