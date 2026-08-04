---
status: draft
level: reference
---

# Supervised fine-tuning: landscape

Source: `reference/research/synthesis.md` anchor table, "SFT/PEFT" and "RM/DPO family"
rows.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| TRL `SFTTrainer`, torchtune's clean training loops | axolotl, LLaMA-Factory, unsloth (kernel-level speedups) | TRL and torchtune are readable enough to teach from directly and are genuinely used in production. axolotl and LLaMA-Factory add config-driven recipe management for teams running many fine-tunes; unsloth adds custom kernels for speed on constrained hardware — relevant on the single-GPU lane specifically. |
| TRL trainers, used as "diff the loss function" exercises across DPO/IPO/KTO/ORPO/SimPO | open-instruct (the Tulu 3 recipe implementation) | The synthesis's anchor table lists a single production reference here — open-instruct/Tulu 3 is the most thoroughly documented open preference-tuning recipe, not the only one that exists. Treat it as the reference recipe to read end-to-end (see the Tulu 3 walkthrough noted in the design doc), not as a single point of dependency: the loss functions themselves are implemented in TRL, which is vendor-independent of the recipe. |

**Single-vendor-rot note:** the SFT/PEFT row names three alternatives beyond
the toy. The RM/DPO row has one named production reference in the synthesis;
we mitigate single-vendor dependency by keeping the loss implementations in
TRL (shared, not open-instruct-specific) and treating open-instruct as a
recipe to study, not infrastructure to depend on.
