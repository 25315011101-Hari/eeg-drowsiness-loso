"""Single source of truth for every constant in the study.

Nothing else in this repository hard-codes a path, a hyperparameter or an
expected count.  If a number appears in the paper it is either in this file,
computed from the raw result files, or recorded in MASTER_NUMBERS.csv.

Hari Singh Jatav, Centre for AI, MANIT Bhopal.
"""

import math as _math
import os

# --------------------------------------------------------------------------
# Paths.  Override any of these with an environment variable of the same name.
# --------------------------------------------------------------------------
EDF_DIR = os.environ.get("EDF_DIR", "data/edf")
DATA_DIR = os.environ.get("DATA_DIR", "data/windows")
RESULT_DIR = os.environ.get("RESULT_DIR", "results")
REGISTRY_CSV = os.environ.get("REGISTRY_CSV", os.path.join(RESULT_DIR, "MASTER_NUMBERS.csv"))

# --------------------------------------------------------------------------
# Signal processing.  These define the window construction and must not be
# changed without rebuilding every arm, because they change the prevalence.
# --------------------------------------------------------------------------
FS = 128.0                  # Hz, the recording rate of DD-Database
WIN_SEC = 10.0
WIN = int(WIN_SEC * FS)     # 1280 samples per window
BAND = (0.5, 40.0)          # band-pass corner frequencies, Hz
BAND_ORD = 4                # Butterworth order
NOTCH_HZ = 50.0             # mains
NOTCH_Q = 30.0
ALERT_GAP_SEC = 20.0        # an alert window's centre must be this far from every event
WANT = ["O1", "O2", "C3", "C4"]     # output channel order is forced to this
PREP_SEED = 42              # seed for the class-balancing subsample

# --------------------------------------------------------------------------
# The three dataset constructions.
#
#   trim     'shortest' cuts every recording to the length of the shortest one,
#            keeping the END so the event-rich later portion survives;
#            'none' leaves the recordings at full length.
#   balance  'keep_drowsy' retains every drowsy window and fills the rest of the
#            subject's quota with alert windows; 'proportional' keeps each
#            subject's own class ratio.
#
# The counts below were measured off the EDF files, not copied from a document.
# preprocess.py re-derives them from its own measurements and then compares, so
# a PASS means the pipeline was reproduced rather than that a number was echoed.
# --------------------------------------------------------------------------
ARMS = {
    "A": dict(
        key="A_trimmed_keep_drowsy",
        trim="shortest",
        balance="keep_drowsy",
        npz="drowsy_windows_trimmed_keep_drowsy.npz",
        n_windows=9260,
        n_per_subject=926,
        n_drowsy=770,
        per_subject_drowsy={"S1": 82, "S2": 58, "S3": 178, "S4": 79, "S5": 60,
                            "S6": 50, "S7": 238, "S8": 11, "S9": 5, "S10": 9},
        label="trimmed, every drowsy window kept",
    ),
    "B": dict(
        key="B_untrimmed_proportional",
        trim="none",
        balance="proportional",
        npz="drowsy_windows_untrimmed_proportional.npz",
        n_windows=9920,
        n_per_subject=992,
        n_drowsy=688,
        per_subject_drowsy={"S1": 67, "S2": 46, "S3": 163, "S4": 68, "S5": 47,
                            "S6": 38, "S7": 239, "S8": 8, "S9": 5, "S10": 7},
        label="untrimmed, subject's own class ratio",
    ),
    "C": dict(
        key="C_trimmed_proportional",
        trim="shortest",
        balance="proportional",
        npz="drowsy_windows_trimmed_proportional.npz",
        n_windows=9260,
        n_per_subject=926,
        n_drowsy=673,
        per_subject_drowsy={"S1": 65, "S2": 43, "S3": 164, "S4": 63, "S5": 46,
                            "S6": 37, "S7": 238, "S8": 8, "S9": 3, "S10": 6},
        label="trimmed, subject's own class ratio",
    ),
}

SUBJECTS = ["S%d" % i for i in range(1, 11)]
N_SUBJECTS = len(SUBJECTS)

# --------------------------------------------------------------------------
# Training protocol.  Identical for every architecture and every arm.
# --------------------------------------------------------------------------
SEEDS = (42, 1, 2, 3, 4)
EPOCHS = 60
BATCH = 64
PATIENCE = 8                # early stopping on validation PR-AUC
N_VAL = 2                   # validation subjects drawn from the nine non-test subjects
LR = 1e-3

MODELS = ["EEGNet", "ShallowConvNet", "CNN", "DeepConvNet", "CNN-BiLSTM"]

# Trainable parameter counts, verified by models.count_parameters().
PARAMS = {
    "EEGNet": 1809,
    "ShallowConvNet": 14121,
    "CNN": 44705,
    "DeepConvNet": 150226,
    "CNN-BiLSTM": 180641,
}

# --------------------------------------------------------------------------
# Evaluation.
# --------------------------------------------------------------------------
ECE_BINS = 10                                # equal-width bins
THRESHOLD_GRID_N = 197                       # np.linspace(0.01, 0.99, 197)
THRESHOLD_GRID = (0.01, 0.99, THRESHOLD_GRID_N)
PLATT_C = 1e6                                # effectively unpenalised logistic fit
FIXED_THRESHOLD = 0.5

# Figure output. Every figure is drawn as vector PDF and as a raster PNG, and only
# the PNG has a resolution at all -- a PDF has no dpi, which is why Elsevier asks for
# vector artwork in the first place and why the PDF is the file that gets submitted.
#
# 360 dpi is the corresponding author's instruction of 30 September 2026 for the PNG.
# It matters what that number is and is not. The guide for authors sets two raster
# minima, quoted in tools/journal_requirements.json: 300 dpi for photographs and
# 1000 dpi for bitmapped line drawings. These figures are line drawings, so 360 dpi
# clears the photograph minimum and does NOT clear the line-drawing minimum. That is
# not a defect while the PDF is what is submitted -- the minima apply to raster
# artwork, and vector artwork is exempt and preferred. It would become a defect the
# moment a PNG were submitted in a PDF's place, so the number is declared here with
# its reason rather than buried in a savefig call.
FIGURE_DPI_RASTER = 360
FIGURE_DPI_LINE_ART_MINIMUM = 1000   # the guide's minimum, for the check to compare against

# The two floors below belong to two DIFFERENT tests and are not interchangeable.
# They once sat here as adjacent bare numbers and were read across during review,
# so each now says which test it governs and each is computed rather than typed.
#
# Wilcoxon signed-rank, two-sided, on the TEN subject-level differences.
P_FLOOR_WILCOXON_10 = 2.0 / 2 ** 10               # 2 / 2^10  = 0.001953125
# Spearman rank correlation, two-sided, across the FIVE architectures: two of the
# 5! = 120 orderings are at least as extreme as a perfect correlation.
P_FLOOR_SPEARMAN_5 = 2.0 / _math.factorial(5)     # 2 / 120   = 0.0166666...

# The nominal level. Declared once, here, because until 25 September 2026 this study
# reported 190 comparisons without naming one anywhere, and a level that is never
# stated cannot be corrected for or argued about.
ALPHA = 0.05

# A floor is not only the smallest p a test can return; it also bounds the largest
# family in which a step-down procedure can reject anything at all. Holm's first
# threshold is ALPHA / m, so a test whose smallest attainable p exceeds ALPHA / m
# cannot reject for ANY dataset once the family reaches that size.
#
#   Wilcoxon on ten pairs     floor 1/512   ->  m <= 25   (1/512 < 1/500, strictly)
#   Wilcoxon on nine pairs    floor 1/256   ->  m <= 12   (1/256 < 1/240, strictly)
#   Spearman on five points   floor 1/60    ->  m <=  3   (1/60 = ALPHA/3, EXACTLY)
#
# The third is an equality, not a near miss: 2/5! and 0.05/3 are both 1/60. The
# study's accuracy-against-recall result therefore sits exactly on the Holm boundary
# for its three-test family, and whether it survives turns on whether the comparison
# is written <= or <. That is why this paper does not use Holm as a decision rule.
def holm_family_ceiling(p_floor, alpha=None):
    """Largest m for which a test with this floor can still reject under Holm."""
    alpha = ALPHA if alpha is None else alpha
    m = 1
    while p_floor <= alpha / (m + 1):
        m += 1
    return m


def arm_reference(arm):
    """The three chance-level references for an arm.

    brier   pi*(1-pi), the Brier score of the constant predictor that always
            emits the class prior.  An architecture ABOVE this is worse than
            that constant predictor when scored as a probability.
    pr_auc  the class prior itself, which is the chance level of PR-AUC.
    acc     the accuracy of always predicting 'alert'.
    """
    a = ARMS[arm]
    pi = a["n_drowsy"] / a["n_windows"]
    return dict(prevalence=pi,
                brier=round(pi * (1 - pi), 4),
                pr_auc=round(pi, 4),
                accuracy=100.0 * (a["n_windows"] - a["n_drowsy"]) / a["n_windows"])


def folds_per_arm():
    return len(MODELS) * len(SEEDS) * N_SUBJECTS        # 250


def total_folds():
    return folds_per_arm() * len(ARMS)                  # 750
