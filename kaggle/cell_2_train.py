ARM = "C"
MODELS = ["EEGNet", "ShallowConvNet", "DeepConvNet", "CNN", "CNN-BiLSTM"]

import os, sys, glob, subprocess
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
sys.path.insert(0, "/kaggle/working/eeg-drowsiness-loso")

if not os.path.exists("/kaggle/working/arl/EEGModels.py"):
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/vlawhern/arl-eegmodels",
                    "/kaggle/working/arl"], check=True)
sys.path.insert(0, "/kaggle/working/arl")

import config as C
C.DATA_DIR = "/kaggle/working"
C.RESULT_DIR = "/kaggle/working/results"

src = glob.glob("/kaggle/working/" + C.ARMS[ARM]["npz"])
if not src:
    found = glob.glob("/kaggle/input/**/" + C.ARMS[ARM]["npz"], recursive=True)
    assert found, "run cell 1 first, or attach the npz as an input"
    subprocess.run(["cp", found[0], "/kaggle/working/"], check=True)

from src import train_loso
train_loso.run_arm(ARM, MODELS, C.DATA_DIR, C.RESULT_DIR)
