"""A multi-hop reasoning task small enough that a small model can actually
learn it, and hard enough that it has to reason to.

Testing latent reasoning on a general 88M language model would answer nothing.
That model cannot do multi-step reasoning in tokens either, so "latent thoughts
did not help" would be indistinguishable from "there was no reasoning here to
move". The comparison only means something on a task where the token-chain
baseline genuinely works.

So the task is synthetic and generated fresh: reachability in a small directed
graph, which is the same shape as the ProsQA benchmark the continuous-thought
paper used, reduced until it fits a model that trains in minutes.

One example, as token ids:

    <edges> a>b  c>d  b>e  f>g  d>h  <q> a ? e  <cot> a>b b>e  <a> yes <eos>

The edge list is shuffled, so the path is never contiguous in the input. The
question asks whether the target is reachable from the source. Half the
examples are unreachable, and an unreachable question is built by walking a
*different* chain of the same length, so a model cannot answer from surface
statistics like "did both names appear".

The one thing that makes this a reasoning task rather than a lookup: **the
answer needs `hops` sequential steps that each depend on the previous one.**
Nothing in the input says which edge to follow second until the first has been
followed.
"""

from __future__ import annotations

import numpy as np

# Vocabulary: control tokens first, then one id per entity.
PAD, EDGES, ARROW, Q, MARK, COT, ANS, YES, NO, EOS, THOUGHT = range(11)
N_CONTROL = 11
CONTROL_NAMES = {
    PAD: "<pad>", EDGES: "<edges>", ARROW: ">", Q: "<q>", MARK: "?",
    COT: "<cot>", ANS: "<a>", YES: "yes", NO: "no", EOS: "<eos>",
    # Never predicted and never read from the embedding table during latent
    # decoding; it exists so the input sequence has a slot to overwrite.
    THOUGHT: "<thought>",
}


class GraphTask:
    """Generates reachability problems over `n_entity` nodes."""

    def __init__(self, n_entity: int = 40, hops: int = 4, n_distractor_edge: int = 12):
        self.n_entity = n_entity
        self.hops = hops
        self.n_distractor_edge = n_distractor_edge
        self.vocab_size = N_CONTROL + n_entity

    def entity(self, i: int) -> int:
        return N_CONTROL + i

    def sample(self, rng: np.random.Generator) -> tuple[list[int], list[int], bool]:
        """One example, returned as (prefix, chain, answer).

        `prefix` is the edge list and the question. `chain` is the sequence of
        edges a solver must follow, which the token-chain arm is trained to
        write out and the latent arm never sees. Splitting them here means both
        arms are built from the identical problem.
        """
        names = rng.permutation(self.n_entity)
        path = names[: self.hops + 1]
        # A second, disjoint chain. An unreachable question asks about its end,
        # so both entities are equally present in the edge list and equally
        # far into it.
        decoy = names[self.hops + 1 : 2 * self.hops + 2]

        edges = [(path[i], path[i + 1]) for i in range(self.hops)]
        edges += [(decoy[i], decoy[i + 1]) for i in range(self.hops)]
        pool = names[2 * self.hops + 2 :]
        for _ in range(self.n_distractor_edge):
            a, b = rng.choice(pool, size=2, replace=False)
            edges.append((a, b))
        rng.shuffle(edges)

        reachable = bool(rng.integers(2))
        source, target = path[0], (path[-1] if reachable else decoy[-1])

        prefix = [EDGES]
        for a, b in edges:
            prefix += [self.entity(int(a)), ARROW, self.entity(int(b))]
        prefix += [Q, self.entity(int(source)), MARK, self.entity(int(target))]

        # The chain is the *work*, not the answer: it is the walk out from the
        # source, identical in both classes. A reachable question ends at that
        # walk's endpoint; an unreachable one ends somewhere else, and the
        # solver finds that out by comparing. Writing the chain therefore leaks
        # nothing about the label, which is what makes the token-chain arm a
        # fair baseline rather than a hint.
        chain = []
        for i in range(self.hops):
            chain += [self.entity(int(path[i])), ARROW, self.entity(int(path[i + 1]))]

        return prefix, chain, reachable

    def encode(self, prefix: list[int], chain: list[int], answer: bool, mode: str,
               n_latent: int) -> tuple[list[int], list[int]]:
        """Build one training sequence and its loss mask for a given arm.

        Returns `(tokens, supervised)`, where `supervised[i]` is 1 where the
        model is scored on predicting `tokens[i]`. Everything before `<a>` in
        the direct and latent arms is context, not a target: the arms differ in
        what they are *given*, and are scored on exactly the same thing.
        """
        answer_token = YES if answer else NO
        if mode == "direct":
            tokens = [*prefix, ANS, answer_token, EOS]
            supervised = [0] * (len(prefix) + 1) + [1, 1]
        elif mode == "cot":
            tokens = [*prefix, COT, *chain, ANS, answer_token, EOS]
            supervised = ([0] * (len(prefix) + 1) + [1] * len(chain) + [0] + [1, 1])
        elif mode == "latent":
            # `n_latent` is the curriculum position, not a fixed setting. Each
            # thought replaces one three-token reasoning step; whatever steps
            # remain are still written and still supervised. n_latent=0 is
            # exactly the token-chain arm and n_latent=hops writes nothing,
            # so one parameter sweeps the whole curriculum.
            rest = chain[3 * n_latent :]
            tokens = [*prefix, COT, *([THOUGHT] * n_latent), *rest, ANS, answer_token, EOS]
            supervised = (
                [0] * (len(prefix) + 1 + n_latent) + [1] * len(rest) + [0] + [1, 1]
            )
        else:
            raise ValueError(f"unknown mode {mode!r}")
        return tokens, supervised

    def batch(self, rng: np.random.Generator, size: int, mode: str, n_latent: int):
        """A padded batch of `size` examples, plus the latent-slot positions."""
        rows = [self.sample(rng) for _ in range(size)]
        encoded = [self.encode(p, c, a, mode, n_latent) for p, c, a in rows]
        width = max(len(t) for t, _ in encoded)
        tokens = np.full((size, width), PAD, dtype=np.int64)
        supervised = np.zeros((size, width), dtype=np.int64)
        for i, (t, s) in enumerate(encoded):
            tokens[i, : len(t)] = t
            supervised[i, : len(s)] = s
        return tokens, supervised


def describe(tokens: list[int], task: GraphTask) -> str:
    """Render a sequence for reading, so the data can be checked by eye."""
    out = []
    for t in tokens:
        if t in CONTROL_NAMES:
            out.append(CONTROL_NAMES[t])
        else:
            out.append(f"e{t - N_CONTROL}")
    return " ".join(out)


if __name__ == "__main__":
    task = GraphTask()
    rng = np.random.default_rng(0)
    for _ in range(2):
        prefix, chain, answer = task.sample(rng)
        print(f"vocab {task.vocab_size}, {task.hops} hops, answer={'yes' if answer else 'no'}")
        for mode in ("direct", "cot", "latent"):
            tokens, supervised = task.encode(prefix, chain, answer, mode, n_latent=task.hops)
            scored = sum(supervised)
            print(f"  {mode:<7} len {len(tokens):>3}, scored on {scored} tokens")
        print("  " + describe([*prefix, COT, *chain, ANS, YES if answer else NO, EOS], task))
        print()
