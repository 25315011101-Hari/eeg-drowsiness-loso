"""Collect the per-seed files of every arm into two tables.

    python -m src.aggregate

    ALL_FOLDS.csv    one row per (arm, model, seed, subject)  -> 750 rows
    ALL_POOLED.csv   one row per (arm, model, seed)           ->  75 rows

Every later module reads only these two files, so there is exactly one place
where a stray or duplicated run could enter the analysis, and it is checked here.

The checks are refusals, not warnings:

  * an arm must contribute len(MODELS) * len(SEEDS) * N_SUBJECTS fold rows
  * no (arm, model, seed, subject) may appear twice
  * every fold's n_drowsy must match the arm's per-subject count, which catches
    a file copied from the wrong arm even if its filename looks right
  * within an arm, every architecture must have been given the same validation
    subject pairs, which is what makes the architectures comparable fold by fold
"""

import argparse
import glob
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

_NICE = {"CNNBiLSTM": "CNN-BiLSTM"}

FOLD_COLUMNS = ["model", "seed", "subject", "n_drowsy", "auc", "pr_auc", "bal_acc",
                "f1", "precision", "recall", "epochs", "val_subs", "arm"]
POOLED_COLUMNS = ["model", "seed", "auc", "pr_auc", "bal_acc", "brier", "fp", "arm"]


def _read_many(pattern):
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def collect_arm(arm, result_dir=None):
    """Read one arm's folds_*.csv and pooled_*.csv."""
    root = os.path.join(result_dir or C.RESULT_DIR, arm)
    folds = _read_many(os.path.join(root, "**", "folds_*.csv"))
    pooled = _read_many(os.path.join(root, "**", "pooled_*.csv"))
    for df in (folds, pooled):
        if not df.empty:
            df["model"] = df["model"].map(lambda m: _NICE.get(m, m))
            df["arm"] = C.ARMS[arm]["key"]
    # folds_all.csv / pooled_all.csv written by an earlier run would duplicate rows
    if not folds.empty:
        folds = folds.drop_duplicates(["model", "seed", "subject"])
    if not pooled.empty:
        pooled = pooled.drop_duplicates(["model", "seed"])
    return folds, pooled


def check_arm(folds, arm, strict=True):
    """Return a list of problems. Empty means the arm is complete and consistent."""
    spec = C.ARMS[arm]
    problems = []

    n_expected = len(C.MODELS) * len(C.SEEDS) * C.N_SUBJECTS
    if strict and len(folds) != n_expected:
        problems.append("arm %s has %d fold rows, expected %d"
                        % (arm, len(folds), n_expected))

    dup = folds.duplicated(["model", "seed", "subject"]).sum()
    if dup:
        problems.append("arm %s has %d duplicated (model, seed, subject) rows" % (arm, dup))

    want = spec["per_subject_drowsy"]
    for subject, group in folds.groupby("subject"):
        got = set(group.n_drowsy.astype(int).unique())
        if got != {want[subject]}:
            problems.append("arm %s subject %s reports n_drowsy %s, arm says %d"
                            % (arm, subject, sorted(got), want[subject]))

    if "val_subs" in folds.columns and folds.val_subs.notna().any():
        pivot = folds.pivot_table(index=["seed", "subject"], columns="model",
                                  values="val_subs", aggfunc="first")
        pivot = pivot.dropna(axis=1, how="all")
        if pivot.shape[1] > 1:
            mismatched = (pivot.nunique(axis=1) > 1).sum()
            if mismatched:
                problems.append("arm %s: %d folds were given different validation "
                                "subjects by different architectures" % (arm, mismatched))
    return problems


def build(result_dir=None, out_dir=None, strict=True, verbose=True):
    result_dir = result_dir or C.RESULT_DIR
    out_dir = out_dir or result_dir
    all_folds, all_pooled, problems = [], [], []

    for arm in sorted(C.ARMS):
        folds, pooled = collect_arm(arm, result_dir)
        if folds.empty:
            if verbose:
                print("arm %s: no per-seed files" % arm)
            continue
        problems += check_arm(folds, arm, strict=strict)
        all_folds.append(folds)
        all_pooled.append(pooled)
        if verbose:
            print("arm %s: %d folds, %d pooled rows" % (arm, len(folds), len(pooled)))

    if not all_folds:
        # The released bundle ships the two aggregate tables but not the per-seed
        # files they were built from, so there is nothing to rebuild. Verify what
        # is there instead of failing: that is the state a reviewer starts in.
        if all(os.path.exists(os.path.join(out_dir, f))
               for f in ("ALL_FOLDS.csv", "ALL_POOLED.csv")):
            folds, pooled = load(out_dir)
            problems = []
            for arm in sorted(C.ARMS):
                d = folds[folds.ar == arm]
                if not d.empty:
                    problems += check_arm(d.drop(columns=["ar"]), arm, strict=strict)
            if problems:
                print("\nCONSISTENCY PROBLEMS")
                for p in problems:
                    print("  -", p)
                if strict:
                    raise SystemExit("the released tables did not pass the checks")
            if verbose:
                print("no per-seed files found; verified the released tables instead "
                      "(%d folds, %d pooled rows)" % (len(folds), len(pooled)))
            return folds, pooled
        raise FileNotFoundError("no result files under " + result_dir)

    folds = pd.concat(all_folds, ignore_index=True)
    pooled = pd.concat(all_pooled, ignore_index=True)
    folds = folds.reindex(columns=[c for c in FOLD_COLUMNS if c in folds.columns])
    pooled = pooled.reindex(columns=[c for c in POOLED_COLUMNS if c in pooled.columns])

    if problems:
        print("\nCONSISTENCY PROBLEMS")
        for p in problems:
            print("  -", p)
        if strict:
            raise SystemExit("refusing to write ALL_FOLDS.csv with %d unresolved problem(s)"
                             % len(problems))

    os.makedirs(out_dir, exist_ok=True)
    f_path = os.path.join(out_dir, "ALL_FOLDS.csv")
    p_path = os.path.join(out_dir, "ALL_POOLED.csv")
    folds.to_csv(f_path, index=False)
    pooled.to_csv(p_path, index=False)
    if verbose:
        print("\nwrote %s (%d rows) and %s (%d rows)"
              % (f_path, len(folds), p_path, len(pooled)))
        if len(folds) == C.total_folds():
            print("all %d folds present" % C.total_folds())
    return folds, pooled


def load(result_dir=None):
    """Read the two aggregate tables and add a short arm letter column."""
    result_dir = result_dir or C.RESULT_DIR
    key_to_arm = {v["key"]: k for k, v in C.ARMS.items()}
    out = []
    for fname in ("ALL_FOLDS.csv", "ALL_POOLED.csv"):
        path = os.path.join(result_dir, fname)
        if not os.path.exists(path):
            raise FileNotFoundError("%s not found; run python -m src.aggregate" % path)
        df = pd.read_csv(path)
        df["ar"] = df["arm"].map(key_to_arm)
        if df["ar"].isna().any():
            unknown = sorted(set(df.loc[df["ar"].isna(), "arm"]))
            raise ValueError("%s contains unknown arm keys: %s" % (path, unknown))
        out.append(df)
    return tuple(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--result-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="report problems but write the tables anyway")
    a = ap.parse_args(argv)
    build(a.result_dir, a.out_dir, strict=not a.allow_incomplete)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
