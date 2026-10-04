import os, sys, glob, re, shutil
sys.path.insert(0, "/kaggle/working/eeg-drowsiness-loso")

import numpy as np
import config as C

C.RESULT_DIR = "/kaggle/working/results"
ARM_BY_DROWSY = {C.ARMS[a]["n_drowsy"]: a for a in C.ARMS}

staged = 0
for f in sorted(glob.glob("/kaggle/input/**/probs_*.npz", recursive=True)
                + glob.glob("/kaggle/working/**/probs_*.npz", recursive=True)):
    if re.match(r"probs_(.+)_seed(\d+)\.npz", os.path.basename(f)) is None:
        continue
    arm = ARM_BY_DROWSY.get(int(np.load(f, allow_pickle=True)["y_true"].sum()))
    if arm is None:
        continue
    dst = os.path.join(C.RESULT_DIR, arm, os.path.basename(f))
    if os.path.abspath(f) != os.path.abspath(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(f, dst)
    staged += 1
print("probability files staged:", staged)

from src import calibrate, thresholds
calibrate.main(["--result-dir", C.RESULT_DIR])
thresholds.main(["--result-dir", C.RESULT_DIR])
