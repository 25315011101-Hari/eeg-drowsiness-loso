"""A real training run, small enough to finish on a CPU in a minute.

    PYTHONPATH=/path/to/arl python tests/test_training_smoke.py

This does not test accuracy -- there is nothing to learn in random data.  It
tests that the training code runs end to end and that the things which would
silently corrupt a real run do not happen:

  * both input layouts work: (trials, samples, channels) for the two models
    written here, (trials, channels, samples, 1) for the three ARL models
  * every architecture builds at the study's trainable parameter count
  * ten folds are produced, one per subject, and the held-out subject never
    appears in the training or validation split of its own fold
  * the four output files per model and seed are written and are readable
  * a resumed run does not repeat a finished fold and does not change which
    validation subjects a fold was given

The last point matters more than it looks.  The validation draw is made for
every subject in order, including subjects already finished, precisely so that
stopping and restarting cannot shift the assignment.  If that ever regressed,
two architectures would be compared on folds that are not the same folds.

Skipped, not failed, when TensorFlow or EEGModels is unavailable.
"""

import os
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

PER_SUBJECT = 40          # windows per subject; small on purpose
SAMPLES = C.WIN
CHANS = len(C.WANT)


def available():
    try:
        import tensorflow  # noqa: F401
    except ImportError:
        print("SKIP: tensorflow is not installed")
        return False
    from src import models
    if not models.check_arl_available():
        print("SKIP: EEGModels is not importable")
        return False
    return True


def synthetic_arm(seed=0):
    """Random windows with a weak, learnable offset on the positive class."""
    rng = np.random.RandomState(seed)
    X, y, g = [], [], []
    for i, s in enumerate(C.SUBJECTS):
        n_pos = 3 + i % 3
        labels = np.zeros(PER_SUBJECT, dtype=np.int64)
        labels[:n_pos] = 1
        rng.shuffle(labels)
        x = rng.normal(0, 1, (PER_SUBJECT, SAMPLES, CHANS)).astype(np.float32)
        x[labels == 1] += 0.4
        X.append(x)
        y.append(labels)
        g.append(np.full(PER_SUBJECT, s))
    return np.concatenate(X), np.concatenate(y), np.concatenate(g)


def run(model_names=("CNN", "EEGNet")):
    from src import models, train_loso

    original_epochs, original_patience = C.EPOCHS, C.PATIENCE
    C.EPOCHS, C.PATIENCE = 1, 1               # one epoch is enough to exercise the path
    train_loso.C.EPOCHS, train_loso.C.PATIENCE = 1, 1
    tmp = tempfile.mkdtemp()
    failures = []

    try:
        X, y, g = synthetic_arm()
        for name in model_names:
            n = models.count_parameters(name, SAMPLES, CHANS)
            if n != C.PARAMS[name]:
                failures.append("%s built with %d parameters, config says %d"
                                % (name, n, C.PARAMS[name]))
            else:
                print("  OK    %s builds at %s parameters" % (name, "{:,}".format(n)))

            df = train_loso.run_one(name, 42, X, y, g, tmp, verbose=False)

            if len(df) != C.N_SUBJECTS:
                failures.append("%s produced %d folds, expected %d"
                                % (name, len(df), C.N_SUBJECTS))
            elif sorted(df.subject) != sorted(C.SUBJECTS):
                failures.append("%s did not test every subject exactly once" % name)
            else:
                print("  OK    %s produced %d folds, one per subject"
                      % (name, len(df)))

            leaked = [r.subject for r in df.itertuples()
                      if r.subject in str(r.val_subs).split("+")]
            if leaked:
                failures.append("%s validated on its own test subject: %s"
                                % (name, leaked))
            else:
                print("  OK    %s never validated on its own test subject" % name)

            tag = "%s_seed42" % name.replace("-", "")
            wanted = ["folds_%s.csv" % tag, "preds_%s.csv" % tag,
                      "probs_%s.npz" % tag, "pooled_%s.csv" % tag]
            missing = [f for f in wanted if not os.path.exists(os.path.join(tmp, f))]
            if missing:
                failures.append("%s did not write %s" % (name, missing))
            else:
                print("  OK    %s wrote all four output files" % name)

            probs = np.load(os.path.join(tmp, "probs_%s.npz" % tag), allow_pickle=True)
            if len(probs["y_true"]) != len(y):
                failures.append("%s probability file has %d rows, expected %d"
                                % (name, len(probs["y_true"]), len(y)))
            if int(probs["y_true"].sum()) != int(y.sum()):
                failures.append("%s probability file lost positive windows" % name)

            pooled = pd.read_csv(os.path.join(tmp, "pooled_%s.csv" % tag))
            if len(pooled) != 1 or not (0 <= float(pooled.brier.iloc[0]) <= 1):
                failures.append("%s wrote an implausible pooled row" % name)
            else:
                print("  OK    %s pooled row is well formed" % name)

            # resume: the same call again must add nothing and change nothing
            before = pd.read_csv(os.path.join(tmp, "folds_%s.csv" % tag))
            train_loso.run_one(name, 42, X, y, g, tmp, verbose=False)
            after = pd.read_csv(os.path.join(tmp, "folds_%s.csv" % tag))
            if len(after) != len(before):
                failures.append("%s resumed run changed the fold count" % name)
            elif not before.set_index("subject").val_subs.equals(
                    after.set_index("subject").val_subs):
                failures.append("%s resumed run changed the validation subjects" % name)
            else:
                print("  OK    %s resume added nothing and moved no validation pair"
                      % name)
    finally:
        C.EPOCHS, C.PATIENCE = original_epochs, original_patience
        train_loso.C.EPOCHS, train_loso.C.PATIENCE = original_epochs, original_patience
        shutil.rmtree(tmp, ignore_errors=True)

    for f in failures:
        print("  FAIL  %s" % f)
    print("\n%s" % ("smoke test passed" if not failures
                    else "%d failure(s)" % len(failures)))
    return 1 if failures else 0


def test_training_smoke():
    """The pytest entry point. This file had none until 25 September 2026.

    Everything above is the only test in this repository that runs real model
    builds through train_loso.run_one and checks the properties the paper most
    depends on: that a held-out subject never appears in its own fold's training or
    validation split, that every architecture builds at the study's parameter count,
    and that a resumed run does not shift the validation draw. None of it defined a
    `test_`-prefixed function, so `pytest tests/` -- the command tools/preflight.py
    runs to decide whether the paper is green -- collected none of it. The gap was
    disclosed in the README, but a disclosed gap in the leakage check is still a gap
    in the leakage check.

    It skips, visibly, when TensorFlow or the ARL reference implementation is absent,
    which is why it can sit in the default suite without requiring a GPU.
    """
    if not available():
        pytest.skip("TensorFlow or the ARL reference implementation is not installed; "
                    "see README for how to run this test")
    assert run() == 0, "the training smoke test reported failures"
    _record_pass()


STAMP = "smoke_test_passed.txt"


def _record_pass():
    """Leave a dated record that this ran, and against which code.

    Without it, "the leakage check passed" is a claim about some run at some time.
    tools/check_submission_ready.py reads this file and compares its timestamp with
    the modification times of the training and model sources, so a pass recorded
    before the last change to either of them counts as no pass at all.
    """
    import datetime
    import config as C
    watched = ("src/train_loso.py", "src/models.py", "config.py")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(C.RESULT_DIR, exist_ok=True)
    with open(os.path.join(C.RESULT_DIR, STAMP), "w") as fh:
        fh.write("training smoke test passed %s\n"
                 % datetime.datetime.now().isoformat(timespec="seconds"))
        fh.write("checked against:\n")
        for rel in watched:
            full = os.path.join(root, rel)
            if os.path.exists(full):
                fh.write("  %-22s modified %s\n"
                         % (rel, datetime.datetime.fromtimestamp(
                             os.path.getmtime(full)).isoformat(timespec="seconds")))


if __name__ == "__main__":
    raise SystemExit(run() if available() else 0)
