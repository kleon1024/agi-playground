# Run — teacher-error inheritance audit

## Command

```bash
cd 01-language-model/03-sft/distillation/when-the-teacher-is-wrong/core
uv run --group torch python3 teacher_error_audit.py
```

## Hardware and software

| | |
|---|---|
| CPU | Apple M1 Pro (local lane) |
| GPU | none — `torch.cuda.is_available()` is `False` in this environment |
| OS | macOS 15.6.1, Darwin 24.6.0 |
| torch | 2.10.0 |
| Data | tinyshakespeare (`karpathy/char-rnn`), character-level tokenizer, 65 symbols |
| Total wall-clock | ~9 min for the full script (two 600-step teacher trainings dominate) |
| Cost | \$0 (local CPU lane) |

## Models and corruption

```
teacher: 3 layers, d_model=192, n_head=3, n_kv_head=3 -> ~1.2M params
student: 2 layers, d_model=96,  n_head=2, n_kv_head=2 ->   227,904 params
```

`teacher-good` trains 600 steps on clean text. `teacher-noisy` trains 600
steps on text where every `e` is replaced by `x` (deterministic, seeded) —
a systematically wrong belief about one letter class. `teacher-random` is
untrained. Each student trains 300 steps on that teacher's temperature-1.0
sampled completions of 200 held-out clean prompts (96 continuation tokens
each), with the prompt masked out of the loss — path-one distillation on
the parent chapter's recipe.

```
teacher-good train:  600 steps, final loss 1.52xx, wall-clock ~86s
teacher-noisy train: 600 steps, final loss 1.5242, wall-clock ~86s
each distill:        300 steps, wall-clock ~10s
```

## Result table

```
model                  clean CE   x rate   e rate
-------------------------------------------------
teacher-good              1.520     0.0%    10.3%
teacher-noisy             2.614    10.4%     0.0%
teacher-random            4.322     0.0%     5.0%
student-from-good         3.119     0.0%     8.9%
student-from-noisy        3.386    15.7%     0.0%
student-from-random       5.840     4.6%     5.5%
base student (no teacher) 4.209     0.0%     5.0%
```

`clean CE` is average next-token cross-entropy on clean held-out text (32
batches of 8, block 128, seeded). `x rate` / `e rate` are the letter rates
in the model's own greedy completions of 20 held-out clean prompts (96
tokens each) — the swap signature: a clean lineage writes `e` at the
natural rate and essentially no `x`; the corrupted lineage swaps them.

## Sample completions on a held-out clean prompt

```
prompt: 'ald, Kate? O, put me in thy books!\n\nKATHARINA:\nWhat is your crest? a coxcomb?\n\nP'
teacher-good        : 'ETRUCHIO:\nI will the world the world the'
teacher-noisy       : 'OLIXENES:\nWhat is thx sxxms\nThat shx hat'
student-from-good   : 'r we we inges inght we a singht ha susin'
student-from-noisy  : 'ENENIUS:\nThxrxin hxrxin hxr do thx do th'
```

The `e`-to-`x` swap is visible in every line of the noisy lineage and absent
from the clean one.

## Verdict

The teacher's systematic error is carved into its output distribution
(`x` 10.4%, `e` 0.0%; clean CE 2.614 vs 1.520), the student inherits it
(`x` 15.7%, `e` 0.0%; clean CE 3.386 vs 3.119), and a teacher with no
signal transfers nothing but confident garbage — student-from-random lands
at 5.840, *worse* than the untrained base student at 4.209.

## Evidence boundary

Mechanism demo at char scale on a toy corpus, per the evidence-scale rule:
it proves the inheritance mechanism exists and measures its shape; the
specific rates do not carry to real distillation, where teacher error is
not a clean letter swap. Sequence-level (path one) distillation only;
logit-level distillation would soften the swap, not remove it. The
factuality-ceiling magnitude is cited to Gudibande et al. (ICLR 2024,
arXiv:2305.15717) and Stanton et al. (NeurIPS 2021, arXiv:2106.05945) in
the chapter README rather than reproduced here.
