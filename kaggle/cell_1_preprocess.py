ARM = "C"

import os, sys, glob, subprocess
if not glob.glob("/kaggle/working/eeg-drowsiness-loso"):
    for p in glob.glob("/kaggle/input/**/eeg-drowsiness-loso", recursive=True):
        subprocess.run(["cp", "-r", p, "/kaggle/working/"], check=True)
        break
sys.path.insert(0, "/kaggle/working/eeg-drowsiness-loso")

import config as C
C.EDF_DIR = "/kaggle/input"
C.DATA_DIR = "/kaggle/working"

from src import preprocess
X, y, g, path = preprocess.build_arm(ARM, edf_dir=C.EDF_DIR, out_dir=C.DATA_DIR)
print("saved:", path)
