"""Run the whole study end to end, or any stage of it.

    python run_all.py                       # everything, in order
    python run_all.py --from aggregate      # skip the GPU stages
    python run_all.py --stage tables
    python run_all.py --dry-run             # print the plan and stop

Stages, in dependency order:

  preprocess   EDF files          -> data/windows/*.npz          (needs mne)
  train        windows            -> results/<arm>/*             (needs a GPU; hours)
  aggregate    per-seed files     -> ALL_FOLDS.csv, ALL_POOLED.csv
  calibrate    probability files  -> calibration_*.csv           (CPU, minutes)
  thresholds   probability files  -> threshold_*.csv             (CPU, minutes)
  registry     the above          -> MASTER_NUMBERS.csv
  tables       the above          -> tables.md

Only the first two need special hardware.  Everything from `aggregate` onward
runs on a laptop in a couple of minutes, which is the part a reviewer is most
likely to want to reproduce.  --from aggregate is the entry point for that.

The stages are separate processes in spirit but plain function calls here, so a
failure stops the run rather than leaving a half-built registry behind.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402

STAGES = ["preprocess", "train", "aggregate", "calibrate", "thresholds",
          "repro", "registry", "tables"]

NEEDS = {
    "preprocess": "the EDF recordings and mne",
    "train": "a GPU; about 3 hours per arm for all five architectures",
}


def stage_preprocess(args):
    from src import preprocess
    for arm in args.arms:
        print("\n=== preprocess arm %s ===" % arm)
        preprocess.build_arm(arm, edf_dir=args.edf_dir, out_dir=args.data_dir)


def stage_train(args):
    from src import models, train_loso
    if not models.check_arl_available():
        raise SystemExit("EEGModels is required for the training stage")
    for arm in args.arms:
        print("\n=== train arm %s ===" % arm)
        train_loso.run_arm(arm, args.models, args.data_dir, args.result_dir)


def stage_aggregate(args):
    from src import aggregate
    print("\n=== aggregate ===")
    aggregate.build(args.result_dir, strict=not args.allow_incomplete)


def stage_calibrate(args):
    from src import calibrate
    print("\n=== calibrate ===")
    rc = calibrate.main(["--result-dir", args.result_dir])
    if rc:
        print("  no probability files found; calibration skipped")


def stage_thresholds(args):
    from src import thresholds
    print("\n=== thresholds ===")
    rc = thresholds.main(["--result-dir", args.result_dir])
    if rc:
        print("  no probability files found; threshold selection skipped")


def stage_repro(args):
    """Optional: compare two executions of the same arm. Skipped if the earlier
    run's fold table was not released."""
    from src import repro
    print("\n=== repro ===")
    ran = False
    for arm in args.arms:
        path = args.run1 or os.path.join(args.result_dir, "backup",
                                         "ALL_FOLDS_arm%s_run1.csv" % arm)
        if not os.path.exists(path):
            continue
        repro.main(["--arm", arm, "--run1", path, "--result-dir", args.result_dir])
        ran = True
    if not ran:
        print("  no earlier run found to compare against; skipped")


def stage_registry(args):
    from src import registry
    print("\n=== registry ===")
    registry.build(args.result_dir, args.registry)


def stage_tables(args):
    from src import tables
    print("\n=== tables ===")
    out = args.tables_out or os.path.join(args.result_dir, "tables.md")
    tables.main(["--result-dir", args.result_dir, "--out", out])


RUNNERS = {
    "preprocess": stage_preprocess,
    "train": stage_train,
    "aggregate": stage_aggregate,
    "calibrate": stage_calibrate,
    "thresholds": stage_thresholds,
    "repro": stage_repro,
    "registry": stage_registry,
    "tables": stage_tables,
}


def plan(args):
    if args.stage:
        return list(args.stage)
    start = STAGES.index(args.start) if args.start else 0
    end = STAGES.index(args.until) + 1 if args.until else len(STAGES)
    return STAGES[start:end]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", action="append", choices=STAGES,
                    help="run only these stages; repeatable")
    ap.add_argument("--from", dest="start", choices=STAGES)
    ap.add_argument("--until", choices=STAGES)
    ap.add_argument("--arm", dest="arms", action="append", choices=sorted(C.ARMS))
    ap.add_argument("--model", dest="models", action="append", choices=C.MODELS)
    ap.add_argument("--edf-dir", default=C.EDF_DIR)
    ap.add_argument("--data-dir", default=C.DATA_DIR)
    ap.add_argument("--result-dir", default=C.RESULT_DIR)
    ap.add_argument("--registry", default=C.REGISTRY_CSV)
    ap.add_argument("--tables-out", default=None)
    ap.add_argument("--run1", default=None,
                    help="an earlier run's fold table, for the repro stage")
    ap.add_argument("--allow-incomplete", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    args.arms = args.arms or sorted(C.ARMS)

    todo = plan(args)
    print("arms:   %s" % ", ".join(args.arms))
    print("models: %s" % ", ".join(args.models or C.MODELS))
    print("stages: %s" % " -> ".join(todo))
    for s in todo:
        if s in NEEDS:
            print("  note: %s needs %s" % (s, NEEDS[s]))
    if args.dry_run:
        return 0

    for s in todo:
        t0 = time.time()
        RUNNERS[s](args)
        print("--- %s done in %.1f s" % (s, time.time() - t0))
    print("\nall requested stages complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
