"""DD-Database EDF files -> a windowed .npz for one arm.

    python -m src.preprocess --arm C

Two checks run before anything is written, and both must pass:

  1. INTERNAL   recomputes what the balancing step must produce from the counts
                THIS run measured off the EDF files, then compares.  It needs no
                outside numbers, so it cannot be satisfied by a typo.
  2. REFERENCE  compares against the counts in config.ARMS, per subject as well
                as in total.  Those counts were themselves measured off the EDF
                files when each arm was first built.

A reference mismatch is a refusal to save, not a warning.  The per-subject table
printed alongside it shows which subjects differ, which usually identifies the
cause immediately.

Window construction, stated once:

  drowsy  the 10 s window ENDING at an annotation onset, so it covers the ten
          seconds before the event.  Candidates that would overlap a window
          already claimed are discarded, so no sample is used twice.
  alert   grid-aligned non-overlapping 10 s windows whose centre is at least
          ALERT_GAP_SEC from every event.

This asymmetry is a design choice with consequences for the prevalence and is
reported as such in the paper; it is not a neutral preprocessing step.
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, iirnotch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402


def norm_ch(name):
    """'EEG O1-A2' / 'O1-Ref' / 'EEG O1' / 'O1' -> 'O1'."""
    s = name.strip().upper()
    s = re.sub(r"^EEG\s+", "", s)
    return s.split("-")[0].strip()


def pick_channels(raw):
    """Return the data as (4, n) in the fixed order O1, O2, C3, C4."""
    table = {}
    for i, ch in enumerate(raw.ch_names):
        table.setdefault(norm_ch(ch), i)
    missing = [w for w in C.WANT if w not in table]
    if missing:
        raise RuntimeError("channels not found: %s (have %s)" % (missing, sorted(table)))
    return raw.get_data()[[table[w] for w in C.WANT]]


def build_filters():
    bn, an = iirnotch(C.NOTCH_HZ, C.NOTCH_Q, C.FS)
    bb, ab = butter(C.BAND_ORD, [C.BAND[0] / (C.FS / 2), C.BAND[1] / (C.FS / 2)],
                    btype="band")
    return (bn, an), (bb, ab)


def windows_for_recording(n_samples, events):
    """Return [(start_sample, label), ...] for one recording.

    Pure integer geometry, so it is unit-testable without any EDF file.
    """
    ev_s = np.round(np.asarray(events, dtype=float) * C.FS).astype(int)
    out, used = [], []

    def overlaps(a0, a1):
        return any(not (a1 <= b0 or a0 >= b1) for b0, b1 in used)

    for e in np.sort(ev_s):
        st = e - C.WIN
        if st < 0 or e > n_samples:
            continue
        if overlaps(st, e):
            continue
        used.append((st, e))
        out.append((st, 1))

    gap = C.ALERT_GAP_SEC * C.FS
    for st in range(0, n_samples - C.WIN + 1, C.WIN):
        centre = st + C.WIN / 2.0
        if len(ev_s) and np.min(np.abs(centre - ev_s)) < gap:
            continue
        if overlaps(st, st + C.WIN):
            continue
        out.append((st, 0))

    return out


def load_all(edf_dir, trim_mode, verbose=True):
    """Read every signal EDF, filter it, and cut windows. Returns per-recording tuples."""
    try:
        import mne
        mne.set_log_level("ERROR")
    except ImportError:
        raise RuntimeError("mne is required to read the EDF files: pip install mne")

    sig = sorted(f for f in glob.glob(os.path.join(edf_dir, "**", "*.edf"), recursive=True)
                 if "_annotations" not in os.path.basename(f))
    if not sig:
        raise RuntimeError("no .edf signal files under " + edf_dir)
    if verbose:
        print("signal files:", len(sig))

    lengths = {p: mne.io.read_raw_edf(p, preload=False, verbose="ERROR").n_times
               for p in sig}
    shortest = min(lengths.values())
    if verbose:
        print("recording lengths: %d to %d samples (%.3f to %.3f h)"
              % (min(lengths.values()), max(lengths.values()),
                 min(lengths.values()) / C.FS / 3600, max(lengths.values()) / C.FS / 3600))
        if trim_mode == "shortest":
            print("trimming every recording to %d samples (%.4f h), keeping the END"
                  % (shortest, shortest / C.FS / 3600))

    (bn, an), (bb, ab) = build_filters()
    per_rec = []

    for k, p in enumerate(sig, 1):
        base = os.path.basename(p)[:-4]                    # e.g. 01M_1
        subj = "S%d" % int(base[:2])
        ann = os.path.join(os.path.dirname(p), base + "_annotations.edf")

        raw = mne.io.read_raw_edf(p, preload=True, verbose="ERROR")
        x = pick_channels(raw)

        ev = np.array([])
        if os.path.exists(ann):
            ev = np.asarray(mne.read_annotations(ann).onset, dtype=float)

        # Trim from the START, keeping the END, and shift the event times by the
        # same amount so that a window still ends exactly at its own event.
        if trim_mode == "shortest":
            off = x.shape[1] - shortest
            if off > 0:
                x = x[:, off:]
                ev = ev - off / C.FS
                ev = ev[ev >= 0]

        # Zero-phase filtering.  Windows are cut at exact event times, so a
        # causal filter's group delay would shift the signal against its label.
        x = filtfilt(bn, an, x, axis=1)
        x = filtfilt(bb, ab, x, axis=1)

        wins = windows_for_recording(x.shape[1], ev)
        per_rec.append((subj, x.astype(np.float32), wins))
        if verbose:
            print("[%2d/%d] %-8s %-4s events=%3d  windows=%4d  drowsy=%3d"
                  % (k, len(sig), base, subj, len(ev), len(wins),
                     sum(l for _, l in wins)))

    return per_rec


def equalise(per_rec, balance_mode, verbose=True):
    """Concatenate both trials per subject, then give every subject the same total."""
    rng = np.random.RandomState(C.PREP_SEED)

    bysub = {}
    for subj, x, wins in per_rec:
        bysub.setdefault(subj, []).append((x, wins))
    subs = sorted(bysub, key=lambda s: int(s[1:]))

    pool, raw_counts = {}, {}
    for s in subs:
        Xs, ys = [], []
        for x, wins in bysub[s]:
            for st, lab in wins:
                Xs.append(x[:, st:st + C.WIN].T)
                ys.append(lab)
        Xs = np.stack(Xs)
        ys = np.array(ys, dtype=np.int64)
        pool[s] = (Xs, ys)
        raw_counts[s] = dict(total=len(ys), drowsy=int(ys.sum()),
                             alert=int((ys == 0).sum()))

    target = min(c["total"] for c in raw_counts.values())
    if verbose:
        print("\n" + "=" * 62)
        print("BEFORE EQUALISATION")
        print("=" * 62)
        print("%-5s %8s %8s %8s %10s" % ("sub", "total", "drowsy", "alert", "prev"))
        for s in subs:
            c = raw_counts[s]
            print("%-5s %8d %8d %8d %9.2f%%"
                  % (s, c["total"], c["drowsy"], c["alert"],
                     100 * c["drowsy"] / c["total"]))
        print("smallest subject total = %d  -> target windows per subject" % target)

    X_out, y_out, g_out = [], [], []
    for s in subs:
        Xs, ys = pool[s]
        di = np.flatnonzero(ys == 1)
        ai = np.flatnonzero(ys == 0)
        keep_d = keep_drowsy_count(len(di), len(ys), target, balance_mode)
        keep_a = min(target - keep_d, len(ai))
        sel = np.concatenate([rng.choice(di, keep_d, replace=False),
                              rng.choice(ai, keep_a, replace=False)])
        sel.sort()
        X_out.append(Xs[sel])
        y_out.append(ys[sel])
        g_out.append(np.full(len(sel), s))

    X = np.concatenate(X_out).astype(np.float32)
    y = np.concatenate(y_out)
    g = np.concatenate(g_out)
    return X, y, g, raw_counts


def keep_drowsy_count(n_drowsy, n_total, target, balance_mode):
    """How many drowsy windows a subject keeps. The one place the arms differ."""
    if balance_mode == "keep_drowsy":
        return n_drowsy
    if balance_mode == "proportional":
        return min(int(round(target * n_drowsy / n_total)), n_drowsy)
    raise ValueError("unknown balance mode: %r" % (balance_mode,))


def derive_expected(raw_counts, balance_mode):
    """What equalisation must produce, recomputed from THIS run's own counts."""
    target = min(c["total"] for c in raw_counts.values())
    exp = {}
    for s, c in raw_counts.items():
        keep_d = keep_drowsy_count(c["drowsy"], c["total"], target, balance_mode)
        exp[s] = (keep_d + min(target - keep_d, c["alert"]), keep_d)
    return exp


def check_internal(X, y, g, raw_counts, balance_mode, verbose=True):
    """Structural check. Expectations derived from this run, no outside numbers."""
    exp = derive_expected(raw_counts, balance_mode)
    got = {s: (int((g == s).sum()), int(y[g == s].sum())) for s in exp}
    bad = {s: (got[s], exp[s]) for s in exp if got[s] != exp[s]}
    sane = (X.dtype == np.float32
            and bool(np.isfinite(X).all())
            and set(np.unique(y).tolist()) <= {0, 1}
            and X.shape[1:] == (C.WIN, len(C.WANT))
            and X.shape[0] == len(y) == len(g)
            and len(exp) == C.N_SUBJECTS)
    ok = not bad and sane
    if verbose:
        print("\nINTERNAL CHECK (got, derived): %s | sanity %s -> %s"
              % (bad or "all %d match" % len(exp), "OK" if sane else "FAIL",
                 "PASS" if ok else "FAIL"))
    return ok


def write_arm_counts(X, y, g, arm, result_dir=None):
    """Record the per-subject counts this arm was actually built with.

    Arm B is independently checkable from the released raw_window_counts.csv,
    because it is untrimmed: applying the proportional rule to those numbers
    reproduces its per-subject drowsy counts exactly, and registry.py asserts it.
    Arms A and C are built from TRIMMED recordings, and no released file carried
    their post-trim counts -- so their totals could only be checked against
    config.ARMS, which is where they came from. That is a circular check, and it
    covered two of the three arms, including the one whose probability files are
    released.

    This closes it for anyone who reruns preprocessing from the recordings. It
    cannot close it for a reader who has only the released bundle, because the
    recordings are not redistributed; the documentation says so plainly rather
    than implying otherwise.
    """
    result_dir = result_dir or C.RESULT_DIR
    subs = sorted(set(g.tolist()), key=lambda s: int(s[1:]))
    frame = pd.DataFrame([
        dict(subject=s, windows=int((g == s).sum()), drowsy=int(y[g == s].sum()))
        for s in subs])
    frame["alert"] = frame.windows - frame.drowsy
    os.makedirs(result_dir, exist_ok=True)
    path = os.path.join(result_dir, "window_counts_arm_%s.csv" % arm)
    frame.to_csv(path, index=False)
    return path


def check_reference(X, y, g, arm, verbose=True):
    """Compare against the counts measured when this arm was first built."""
    spec = C.ARMS[arm]
    subs = sorted(set(g.tolist()), key=lambda s: int(s[1:]))
    got = {s: int(y[g == s].sum()) for s in subs}

    if verbose:
        print("\n" + "=" * 62)
        print("AFTER EQUALISATION   arm=%s  trim=%s  balance=%s"
              % (arm, spec["trim"], spec["balance"]))
        print("=" * 62)
        print("X %s   drowsy %d (%.2f%%)   alert %d"
              % (X.shape, int(y.sum()), 100 * y.mean(), int((y == 0).sum())))
        print("%-5s %8s %8s %10s" % ("sub", "windows", "drowsy", "prev"))
        for s in subs:
            m = g == s
            print("%-5s %8d %8d %9.2f%%" % (s, m.sum(), got[s], 100 * got[s] / m.sum()))

    ok_n = X.shape[0] == spec["n_windows"]
    ok_d = int(y.sum()) == spec["n_drowsy"]
    want = spec["per_subject_drowsy"]
    bad = {s: (got.get(s), want[s]) for s in want if got.get(s) != want[s]}
    passed = ok_n and ok_d and not bad

    if verbose:
        print("\n" + "=" * 62)
        print("REFERENCE CHECK against the measured counts for arm %s" % arm)
        print("=" * 62)
        print("  windows  %6d  expected %6d   %s"
              % (X.shape[0], spec["n_windows"], "OK" if ok_n else "MISMATCH"))
        print("  drowsy   %6d  expected %6d   %s"
              % (int(y.sum()), spec["n_drowsy"], "OK" if ok_d else "MISMATCH"))
        if bad:
            print("  per-subject mismatches (got, expected):")
            for s, v in bad.items():
                print("     %-4s %s" % (s, v))
        else:
            print("  per-subject   all %d match" % len(want))
        print("\n  RESULT:", "PASS - this run reproduces the published arm" if passed
              else "FAIL - do not use this output; the pipeline differs")
        if not passed:
            print(REFERENCE_FAIL_HINT)
    return passed


REFERENCE_FAIL_HINT = """
  A mismatch does not necessarily mean the signal processing is wrong. The most
  likely causes, in order:
    1. which windows the random subsample picks (seed or draw order)
    2. how the proportional split rounds when it lands on .5
    3. whether events in the first 10 s of a recording are usable
    4. annotation onsets read differently than in the original script
  The per-subject table above shows which subjects differ, which usually points
  straight at the cause."""


def save(path, X, y, g, arm):
    """Write the npz with its provenance stamped inside it."""
    spec = C.ARMS[arm]
    subs = sorted(set(g.tolist()), key=lambda s: int(s[1:]))
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    np.savez(path, X=X, y=y, groups=g,
             arm=arm, arm_key=spec["key"],
             trim_mode=spec["trim"], balance_mode=spec["balance"],
             subjects=np.array(subs),
             per_subject_drowsy=np.array([int(y[g == s].sum()) for s in subs]))
    return path


def build_arm(arm, edf_dir=None, out_dir=None, save_output=True, verbose=True):
    """Build one arm end to end. Returns (X, y, groups, path_or_None)."""
    if arm not in C.ARMS:
        raise ValueError("unknown arm %r; expected one of %s" % (arm, sorted(C.ARMS)))
    spec = C.ARMS[arm]
    edf_dir = edf_dir or C.EDF_DIR
    out_dir = out_dir or C.DATA_DIR

    per_rec = load_all(edf_dir, spec["trim"], verbose=verbose)
    X, y, g, raw_counts = equalise(per_rec, spec["balance"], verbose=verbose)

    internal = check_internal(X, y, g, raw_counts, spec["balance"], verbose=verbose)
    reference = check_reference(X, y, g, arm, verbose=verbose)
    # Written before the save gate, and whether or not the reference check passed:
    # if this run does NOT reproduce the published arm, the counts it did produce are
    # exactly what someone diagnosing the difference needs.
    counts_path = write_arm_counts(X, y, g, arm)
    if verbose:
        print("internal %s | reference %s" % (internal, reference))
        print("wrote %s" % counts_path)

    path = None
    if save_output and internal and reference:
        path = save(os.path.join(out_dir, spec["npz"]), X, y, g, arm)
        if verbose:
            print("saved: %s  (%d windows, %d drowsy)" % (path, X.shape[0], int(y.sum())))
    elif verbose:
        print("NOT saved.")
    return X, y, g, path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True, choices=sorted(C.ARMS))
    ap.add_argument("--edf-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="run every check but write nothing")
    a = ap.parse_args(argv)
    _, _, _, path = build_arm(a.arm, a.edf_dir, a.out_dir, save_output=not a.dry_run)
    return 0 if (path or a.dry_run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
