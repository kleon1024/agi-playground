"""The same continuous-thought loop against a real `transformers` model.

`../core/` splits `embed` from `forward` by hand, because that is the clearest
way to see that a latent thought is a plumbing change and not a new kind of
network. Nothing about that is bespoke: every causal LM in `transformers`
accepts `inputs_embeds` in place of `input_ids`, and returns hidden states when
asked. So the identical loop runs on a real checkpoint with no surgery:

    out = model(inputs_embeds=embeds, output_hidden_states=True)
    thought = out.hidden_states[-1][:, -1]          # the model's own state
    embeds = torch.cat([embeds, thought[:, None]], 1)   # ...becomes the next input

That is the whole mechanism. What the reference implementation adds beyond it
is the training machinery this file does not attempt: the staged curriculum,
the `<bot>`/`<eot>` markers that tell the model where thinking begins and ends,
and multiple sampled thought sequences per problem.

Two things worth knowing before reaching for this on a real model:

- **A KV cache and a rewritten input do not compose for free.** Appending a
  computed embedding is fine, because the prefix is unchanged and the cache
  stays valid. *Overwriting* a slot inside the sequence — what `../core/`'s
  training pass does — invalidates every cached key and value after it, which
  is why training a latent arm costs one forward pass per thought.
- **There is nothing to decode.** A thought has no token, so it does not appear
  in the output text and cannot be read, logged, or checked by a human. Whatever
  interpretability you had from a written chain of thought is gone by
  construction, which is a property of the method rather than a limitation of
  this implementation.

Requires: `pip install transformers torch`.

Usage:
    python hf_latent.py --model HuggingFaceTB/SmolLM2-135M --thoughts 4 \
        --prompt "A is north of B. B is north of C. Is A north of C?"
"""

from __future__ import annotations

import argparse

import torch


def generate_with_thoughts(model_name: str, prompt: str, n_thought: int, max_new: int) -> str:
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32).eval()

    ids = tokenizer(prompt, return_tensors="pt").input_ids
    embeds = model.get_input_embeddings()(ids)

    # Think, without committing to any token.
    for _ in range(n_thought):
        out = model(inputs_embeds=embeds, output_hidden_states=True)
        thought = out.hidden_states[-1][:, -1:]
        embeds = torch.cat([embeds, thought], dim=1)

    # Then speak, from a context that now contains those thoughts.
    generated = []
    for _ in range(max_new):
        out = model(inputs_embeds=embeds)
        next_id = out.logits[:, -1].argmax(-1, keepdim=True)
        generated.append(int(next_id))
        if next_id.item() == tokenizer.eos_token_id:
            break
        embeds = torch.cat([embeds, model.get_input_embeddings()(next_id)], dim=1)

    return tokenizer.decode(generated)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM2-135M")
    ap.add_argument("--prompt", default="A is north of B. B is north of C. Is A north of C?")
    ap.add_argument("--thoughts", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=32)
    args = ap.parse_args()

    print(f"prompt:   {args.prompt}")
    print(f"thoughts: {args.thoughts} continuous steps, no tokens emitted")
    print(f"output:   {generate_with_thoughts(args.model, args.prompt, args.thoughts, args.max_new)}")
    print(
        "\nThis demonstrates the interface, not a capability. An off-the-shelf "
        "checkpoint was never trained to use continuous thoughts, so the "
        "thoughts here are unlikely to carry anything useful — that is what "
        "../core/'s curriculum exists to fix, and what its run record measures."
    )


if __name__ == "__main__":
    main()
