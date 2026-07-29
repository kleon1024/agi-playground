---
status: draft
level: foundation
---

> **[Read this online](https://rehearse.maestro.onl/playground/foundations)**.

# What do you need to hold before a mission stops being magic?

Two things, and they are smaller than the word "foundations" suggests. You need
to know what a decoder block computes, and you need to have watched a model's
loss go down because of an update you can point at.

These are **language-model foundations**, not prerequisites for intelligence in
general. Attention, decoder blocks, and a first training loop are what you need
to reason about the next decision in
[the language-model system](../missions/01-language-model-agent/) — nothing here
claims to be the base of a broader pyramid, and **nothing here has to be read
before you start a mission**. Come when a mission sends you, or come first if
you would rather build the mental model before the artifact.

| Chapter | The question it answers | It returns |
|---|---|---|
| [The decoder block](00-attention/) | How does one token find the context it needs, transform it, and still leave a path for learning? | the forward path, and the 88M model's parameter count reconstructed from its own formulas |
| [The first training loop](01-first-training-loop/) | What actually happens between a loss number and a changed weight? | the backward path, on a model small enough to run on a laptop |

Read them in that order if you are reading both: the second chapter trains the
thing the first chapter describes.

## Where these go next

[Pretraining](../platform/training/) joins both paths to real data and a token
budget. [Data](../platform/data/) supplies the distribution that budget is spent
on. Neither is a foundation — they are decisions with costs, and they assume you
already know what is being trained.

Every mechanism in these two chapters has a production implementation that
computes the same thing faster.
[The foundations landscape](LANDSCAPE.md) pairs them off, so you know which of
these files you would keep and which you would delete the moment the model has
to be fast.
