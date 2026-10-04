# 5 Architectures — draft 1

The five models evaluated. Three are reference implementations published by their
authors and used unmodified; two were prespecified for this study. They span two
orders of magnitude in trainable parameter count, which is the point: the study
asks what that range buys, and the answer is not what parameter count alone
predicts.

## 5.1 The five models

The five architectures and their trainable parameter counts are given in **Table 2**.

**Table 2. The five architectures evaluated, and their trainable parameter counts.**
They span two orders of magnitude. Three are reference implementations used
unmodified apart from the output-layer change described in Section 5.2; two were
prespecified for this study.

| Architecture | Parameters | Family |
|---|---|---|
| EEGNet | 1,809 | compact depthwise-separable convolution |
| ShallowConvNet | 14,121 | shallow temporal–spatial convolution |
| CNN | 44,705 | one-dimensional convolutional trunk |
| DeepConvNet | 150,226 | deep convolutional stack |
| CNN-BiLSTM | 180,641 | the same trunk with a recurrent block |

## 5.2 Reference implementations, and the one change made to them

EEGNet, ShallowConvNet and DeepConvNet were taken from the reference
implementations without architectural modification, with one necessary exception.
These implementations terminate in a softmax over `nb_classes` units; with
`nb_classes = 1` a softmax over a length-one axis returns 1.0 for every input and
nothing can be learned. The final softmax was therefore replaced by a sigmoid on
the same penultimate layer, which is the standard single-output form and leaves
every learned layer untouched.

## 5.3 The two prespecified models

The **CNN** is a one-dimensional convolutional trunk: three blocks of convolution
(32 filters of length 7, then 64 of length 5, then 128 of length 3, each with same
padding and ReLU), each followed by max-pooling of stride 2, batch normalisation
and dropout of 0.3; then global average pooling over time, a 64-unit dense layer
with dropout 0.4, and a single sigmoid output.

The **CNN-BiLSTM** is that identical trunk with the global average pooling replaced
by two bidirectional LSTM layers (64 units returning sequences, then 32 units), each
with dropout 0.4 on its inputs, followed by the same head. The dropout is Keras's
`dropout` argument and not its `recurrent_dropout`: the recurrent connections are not
dropped. The two are separate arguments with different behaviour, and a
reimplementation that set the second would not be this model. The two models therefore
share their convolutional trunk exactly and differ only in the component that
reduces the time axis, which makes the comparison between them far tighter than a
comparison of two unrelated networks. It is **not** capacity-controlled: replacing
global average pooling with the recurrent block adds 135,936 trainable parameters,
taking the model from 44,705 to 180,641. The recurrent layers themselves account for
more than that difference, and the head for the rest of it in the other direction:
the dense head is the same definition in both models but not the same size, because
global average pooling delivers 128 features to it and the second bidirectional
layer delivers 64. Anyone recomputing these counts should treat the two heads
separately. Any effect observed is the effect of that
substitution as a whole, and the contributions of recurrence and of added capacity
are not separable within it.

**Figure 1** draws both models against each other. The trunk is drawn once, spanning
both columns, because it is the same trunk: that is what makes this the study's one
controlled architectural comparison. Only the block beneath it differs.

![Figure 1. The two prespecified models, and the single component that separates](../figures/figure1_cnn_against_cnn_bilstm.png)

> **Figure 1. The two prespecified models, and the single component that separates
> them.** The three convolution blocks above the rule are shared exactly, each
> halving the time axis, so the 1,280-sample window reaches the branch as 160 steps.
> Below the rule the CNN reduces that axis by global average pooling and the
> CNN-BiLSTM by two bidirectional LSTM layers; the dense head is again shared. The
> figure is generated from the layer definitions in `src/models.py` and the
> parameter counts in `config.py`, so it cannot disagree with the models that were
> trained. Both branches end in the same single sigmoid unit, so each model emits one
> drowsy probability in [0, 1] per window; every measurement in this paper is computed
> from that number, at a threshold where a decision is needed and from the probability
> itself where it is not. Dropout on the LSTM layers is applied to their inputs, not
> to their recurrent connections.

## 5.4 Input shape

Inputs are shaped to each family's convention — (1,280 × 4) for the
one-dimensional models, (4 × 1,280 × 1) for the EEGNet family — but the underlying
windows are identical.

