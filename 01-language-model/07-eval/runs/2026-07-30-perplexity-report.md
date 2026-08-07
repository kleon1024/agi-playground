# perplexity report — 2026-07-30T08:46:03+00:00

checkpoint   /home/ding/agi-playground/stage02/ckpt/ckpt.pt  (sha256 ffd32ce920c4...)
tokenizer    /home/ding/agi-playground/stage01/tokenizer.json  (sha256 0b2ce230b496...)
context      1024 tokens, stride 1024
windows      4882
perplexity   21.677  (mean NLL 3.0762 +/- 0.3214)
baseline     uniform distribution over vocab = 9.712 nats (ln(16512))  (01-language-model/02-pretrain/README.md, ln(vocab_size))

does not prove:
  - Comparable only to another run that used the identical tokenizer (matching sha256 above) and the identical context length; perplexity is not a cross-tokenizer or cross-context-length metric.
  - A held-out split drawn from the same source distribution as training does not establish generalization to a different domain or a live workload.