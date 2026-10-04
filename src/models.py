"""The five architectures, each at its published configuration.

No hyperparameter search was run.  Every model is compiled identically -- Adam
at config.LR, binary cross-entropy, ROC-AUC and PR-AUC as monitored metrics --
so that the comparison is between architectures rather than between tuning
budgets.

Two of the five share a trunk on purpose.  CNN and CNN-BiLSTM use the same three
convolution-pooling blocks and the same dense head, and differ only in how the
time axis is reduced: global average pooling against two bidirectional LSTM
layers.  That pair is the one controlled architectural comparison in the study.

Input shapes differ between families and this is handled here rather than at the
call site:

    CNN, CNN-BiLSTM, ShallowConvNet, DeepConvNet   (trials, samples, channels)
    EEGNet                                         (trials, channels, samples, 1)

EEGNet, ShallowConvNet and DeepConvNet come from the ARL EEGModels reference
implementation, which must be importable.  Their softmax head is replaced with a
sigmoid: with nb_classes=1 a softmax over a length-one axis returns 1.0 for every
input and nothing is learned.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402

ARL_REPO = "https://github.com/vlawhern/arl-eegmodels"


def _tf():
    import tensorflow as tf
    return tf


def _compile(model):
    tf = _tf()
    model.compile(optimizer=tf.keras.optimizers.Adam(C.LR),
                  loss="binary_crossentropy",
                  metrics=[tf.keras.metrics.AUC(name="auc"),
                           tf.keras.metrics.AUC(name="prauc", curve="PR")])
    return model


# The two prespecified models, written once as data. The layers used to be spelled
# out inside the builders, which meant the architecture figure and the Architectures
# section were each a separate retyping of them -- and a retyping drifts. It did:
# the manuscript described the LSTM dropout as "recurrent dropout" until
# 25 September 2026, where the code passes Keras's `dropout` argument and never
# touches `recurrent_dropout`. They are different arguments, and a reimplementation
# that set the second would not be this model.
#
# Everything downstream now reads these tuples: the builders below, the figure in
# src/figures.py, and a test that fails if the prose disagrees with them. Change the
# architecture here and the picture and the check follow; change it in one of them
# alone and the test says so.
CONV_TRUNK = (
    ("conv", 32, 7), ("pool", 2), ("batchnorm",), ("dropout", 0.3),
    ("conv", 64, 5), ("pool", 2), ("batchnorm",), ("dropout", 0.3),
    ("conv", 128, 3), ("pool", 2), ("batchnorm",), ("dropout", 0.3),
)
RECURRENT_BLOCK = (
    # (units, return_sequences, input dropout). NOT recurrent_dropout.
    ("bilstm", 64, True, 0.4),
    ("bilstm", 32, False, 0.4),
)
HEAD = (("dense", 64, "relu"), ("dropout", 0.4), ("dense", 1, "sigmoid"))
CONV_ACTIVATION = "relu"
CONV_PADDING = "same"


def trainable_parameters(name, samples=None, chans=None):
    """Trainable parameters of a prespecified model, derived from the spec above.

    Not a lookup and not a retyping: the arithmetic is done here from the same
    tuples the builders construct from, so config.PARAMS can be checked rather than
    trusted. Only "CNN" and "CNN-BiLSTM" are defined in this file; the other three
    architectures are reference implementations and their counts are measured, not
    derived.

    The one place this is easy to get wrong is the head. Both models end in the same
    HEAD tuple, but "the same head" means the same layer definition and NOT the same
    parameter count: the CNN's Dense(64) receives 128 features from global average
    pooling over 128 channels, while the CNN-BiLSTM's receives 64 -- the second
    bidirectional layer's 32 units in each direction. That is a difference of
    (128 - 64) x 64 = 4,096 parameters, and assuming the two heads cost the same is
    how an independent check of these numbers came out 4,096 too high.
    """
    if name not in ("CNN", "CNN-BiLSTM"):
        raise ValueError("%s is a reference implementation; its count is measured, "
                         "not derived from a spec in this file" % name)
    chans = len(C.WANT) if chans is None else chans

    total, features = 0, chans
    for item in CONV_TRUNK:
        if item[0] == "conv":
            total += item[2] * features * item[1] + item[1]   # kernel, bias
            features = item[1]
        elif item[0] == "batchnorm":
            total += 2 * features                             # gamma and beta
    if name == "CNN":
        pass                                                  # pooling has none
    else:
        for item in RECURRENT_BLOCK:
            units = item[1]
            total += 2 * 4 * (features * units + units * units + units)
            features = 2 * units                              # both directions
    for item in HEAD:
        if item[0] == "dense":
            total += features * item[1] + item[1]
            features = item[1]
    return total


def _layers(spec):
    """Turn the tuples above into Keras layers. One reading, one meaning."""
    L = _tf().keras.layers
    out = []
    for item in spec:
        kind = item[0]
        if kind == "conv":
            out.append(L.Conv1D(item[1], item[2], activation=CONV_ACTIVATION,
                                padding=CONV_PADDING))
        elif kind == "pool":
            out.append(L.MaxPooling1D(item[1]))
        elif kind == "batchnorm":
            out.append(L.BatchNormalization())
        elif kind == "dropout":
            out.append(L.Dropout(item[1]))
        elif kind == "dense":
            out.append(L.Dense(item[1], activation=item[2]))
        elif kind == "bilstm":
            out.append(L.Bidirectional(
                L.LSTM(item[1], return_sequences=item[2], dropout=item[3])))
        else:
            raise ValueError("unknown layer spec: %r" % (item,))
    return out


def _conv_trunk(input_shape):
    """The three convolution-pooling blocks shared by CNN and CNN-BiLSTM."""
    return [_tf().keras.layers.Input(shape=input_shape)] + _layers(CONV_TRUNK)


def _head():
    """The dense head shared by CNN and CNN-BiLSTM."""
    return _layers(HEAD)


def build_cnn(samples, chans):
    tf = _tf()
    return _compile(tf.keras.models.Sequential(
        _conv_trunk((samples, chans))
        + [tf.keras.layers.GlobalAveragePooling1D()]
        + _head()))


def build_cnn_bilstm(samples, chans):
    tf = _tf()
    return _compile(tf.keras.models.Sequential(
        _conv_trunk((samples, chans))
        + _layers(RECURRENT_BLOCK)
        + _head()))


def _sigmoid_head(base):
    """Replace the ARL softmax classification head with a sigmoid."""
    tf = _tf()
    out = tf.keras.layers.Activation("sigmoid")(base.layers[-2].output)
    return _compile(tf.keras.Model(base.input, out))


def build_eegnet(samples, chans):
    from EEGModels import EEGNet
    return _sigmoid_head(EEGNet(nb_classes=1, Chans=chans, Samples=samples,
                                dropoutRate=0.5, kernLength=64, F1=8, D=2, F2=16,
                                dropoutType="Dropout"))


def build_shallowconvnet(samples, chans):
    from EEGModels import ShallowConvNet
    return _sigmoid_head(ShallowConvNet(nb_classes=1, Chans=chans, Samples=samples,
                                        dropoutRate=0.5))


def build_deepconvnet(samples, chans):
    from EEGModels import DeepConvNet
    return _sigmoid_head(DeepConvNet(nb_classes=1, Chans=chans, Samples=samples,
                                     dropoutRate=0.5))


BUILDERS = {
    "CNN": build_cnn,
    "CNN-BiLSTM": build_cnn_bilstm,
    "EEGNet": build_eegnet,
    "ShallowConvNet": build_shallowconvnet,
    "DeepConvNet": build_deepconvnet,
}

# Architectures taken from the ARL reference implementation.  They want
# (trials, channels, samples, 1); the two written here want (trials, samples, channels).
ARL_MODELS = ("EEGNet", "ShallowConvNet", "DeepConvNet")


def build(name, samples, chans):
    if name not in BUILDERS:
        raise ValueError("unknown model %r; expected one of %s" % (name, C.MODELS))
    return BUILDERS[name](samples, chans)


def shape_for(name, A):
    """Put a (trials, samples, channels) array into the layout this model wants."""
    A = np.asarray(A)
    return A.transpose(0, 2, 1)[..., None] if name in ARL_MODELS else A


def norm_axes(name):
    """Axes to average over when computing the training-fold z-score statistics.

    Both cases reduce to per-channel mean and standard deviation over trials and
    time; only the axis order differs with the layout.
    """
    return (0, 2) if name in ARL_MODELS else (0, 1)


def count_parameters(name, samples=None, chans=None):
    """Trainable parameter count. Used by the test suite to verify config.PARAMS."""
    tf = _tf()
    samples = C.WIN if samples is None else samples
    chans = len(C.WANT) if chans is None else chans
    tf.keras.backend.clear_session()
    m = build(name, samples, chans)
    return int(sum(int(tf.size(w)) for w in m.trainable_weights))


def check_arl_available():
    """Explain what is missing rather than failing with a bare ImportError."""
    try:
        import EEGModels  # noqa: F401
        return True
    except ImportError:
        print("EEGModels not importable. Clone the ARL reference implementation and "
              "put it on sys.path:\n  git clone %s arl\n  export PYTHONPATH=$PWD/arl"
              % ARL_REPO)
        return False


if __name__ == "__main__":
    if check_arl_available():
        for name in C.MODELS:
            n = count_parameters(name)
            flag = "OK" if n == C.PARAMS[name] else "MISMATCH (config says %d)" % C.PARAMS[name]
            print("%-16s %9s  %s" % (name, "{:,}".format(n), flag))
