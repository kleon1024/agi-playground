# LLM Pretraining & Data Pipeline Tooling — Mid-2026 Landscape

> Research pass conducted 2026-07-24 with parallel web-research agents; sources linked inline.

## (a) Pretraining Reference Implementations

**Best to learn from (single-GPU friendly):**
- **nanoGPT** (karpathy) — still the canonical minimal transformer-pretraining reference: ~300 lines, one file, fully readable. Best starting point for teaching the training loop itself.
- **nanochat** (karpathy, Oct 2025) — the new benchmark for a *teaching repo*: ~8,000 lines, full-stack (tokenizer → pretrain → midtrain → SFT → RL → web UI), "$100/4-hours to a working ChatGPT clone," ~12 hours to beat GPT-2 CORE metric on an 8×H100 box, but scales down to fewer GPUs. This is arguably the single best template for a repo like the one you're designing, since it demonstrates the *entire* pipeline, not just pretraining.
- **modded-nanoGPT** — a "speedrun" fork of nanoGPT that gamifies optimization (Muon optimizer, FlashAttention, architecture tweaks); records have fallen from 45 min to ~1.35 min on 8×H100. Excellent for teaching optimization/systems intuition after the basics are understood.
- **minbpe** — companion tokenizer repo, minimal BPE implementation with a `basic`/`regex`/`gpt4` progression and paired lecture; the standard "build your own tokenizer" teaching artifact.
- **llm.c** — actively maintained (not archived; ~1,536 commits, active issues/PRs). Raw C/CUDA reproduction of GPT-2/3, explicitly supports a "1 GPU, fp32-only" quick start. Good for teaching *what PyTorch is hiding* (kernels, memory layout) but not the first thing to teach — better as a second-pass "look under the hood" module.

**Production-standard / cloud-scale (needs Modal/multi-node):**
- **torchtitan** (Meta/PyTorch) — the reference "one-stop PyTorch-native" production pretraining stack: FSDP2, native 4D parallelism, torch.compile, meant to be read as *patterns to copy*, not a dependency to import. Good as an advanced module showing how nanoGPT-style code scales to production.
- **nanotron** (Hugging Face) — 3D-parallelism (DP/TP/PP) library used for HF's own large runs; FP8 and ZeRO-3/FSDP are still on the roadmap as of 2026. Good second production example, more "library-like" than torchtitan.
- **Megatron-LM** (NVIDIA) — the original heavyweight production framework; requires TransformerEngine and model surgery, doesn't integrate cleanly with FSDP. Both Megatron-LM and DeepSpeed OOM readily on a single RTX 4090/3090 even at small batch sizes — treat as read-only reference, not something to run locally.
- **Meta Lingua** — clean, hackable Meta research codebase, sits conceptually between nanoGPT and torchtitan; useful as a mid-complexity example of research-grade (not consumer-grade) code.
- **OLMo / OLMo 2 / OLMo-core (AI2)** — the most important 2025–2026 development for "fully open" pretraining: open data (Dolma, OLMo-Mix-1124 ~3.9T tokens, Dolmino-Mix ~843B tokens), open code, open checkpoints, and reproducible recipes at 7B/13B/32B scale (OLMo 2 32B was the first fully-open model to beat GPT-3.5-Turbo/GPT-4o-mini). **OLMo-core** (the rewritten pretraining engine) is the best "real lab" reference for how a serious open pretraining stack is organized end-to-end — use it as the capstone reading after nanochat/nanoGPT, not as something to execute on a 4090.
- **TinyLlama / RedPajama** — TinyLlama (1.1B, trained on SlimPajama+StarCoder) is the best concrete precedent for "small model, real data mix, single-node-feasible in spirit" even though the original run used 16×A100s; still actively referenced in 2026. RedPajama-v2 (30T tokens, quality signals + metadata) is the standard large open web corpus underlying it.

**4090 (24GB) vs Modal cutoff:** nanoGPT/nanochat/modded-nanoGPT/minbpe/llm.c all run meaningfully on a single 4090 (small-scale GPT-2-124M–350M class runs, hours-to-a-day). Anything invoking torchtitan/nanotron/Megatron's actual parallelism features, or OLMo/TinyLlama-scale runs, needs Modal (multi-GPU/multi-node) — treat those as "read the code, run on Modal for the real experience."

## (b) Data Pipeline / Curation Tooling

- **datatrove** (Hugging Face) — the canonical, actively maintained pipeline library; it *is* the reference implementation of the FineWeb and FineWeb-Edu pipelines (extraction, MinHash/near-dup filtering, quality heuristics, classifier-based filtering all documented and reproducible). This is the best "teach from" tool since students can literally rerun the published pipeline stages.
- **FineWeb / FineWeb-Edu** — 15T-token web corpus + educational-quality-filtered subset; the classifier-based quality filtering approach (train a small classifier on LLM-judged educational value, then filter at scale) is now a standard teaching pattern for "quality filtering beyond heuristics."
- **Dolma toolkit** (AI2) — companion to OLMo; strong for teaching provenance/attribution tracking and mixture-based dataset construction (3T tokens, feeds OLMo 2).
- **DCLM / DataComp-LM** — a benchmark-style framework (fix compute, vary the dataset-construction recipe) rather than a single pipeline; best used to teach the *experimental methodology* of data curation (ablating filtering choices) rather than as a tool to run.
- **RedPajama-Data** — dataset-prep code for reproducing the LLaMA-style corpus; still widely cited, feeds Snowflake Arctic, XGen, OLMo lineages.
- **NeMo Curator (NVIDIA)** — the production/GPU-accelerated standard: RAPIDS/cuDF/Dask-backed exact (MD5), fuzzy (MinHash+LSH, ~16× faster on GPU), and semantic (embedding) dedup, plus 30+ quality heuristics, PII/NSFW filtering; recent releases (26.02, 26.04) moved to a Ray-based pipeline for text/image/video/audio uniformly. This is the "production standard" to name-check but not something to run meaningfully on a 4090 — it wants an 8×H100 node or Modal.
- **Fit:** datatrove pipelines on small Common Crawl shards run fine locally on a 4090 (CPU-bound mostly, GPU only helps for classifier inference); NeMo Curator's GPU dedup at scale is a Modal-cloud exercise.

## (c) Annotation / Synthetic Data

- **Argilla** (now part of Hugging Face ecosystem) — the standard open-source human-in-the-loop annotation/curation tool with direct Hub push/pull; pairs naturally with distilabel.
- **distilabel** (Argilla) — the canonical synthetic-data/AI-feedback pipeline framework (LLM-as-annotator, verified-paper-based pipelines: self-instruct, UltraFeedback-style, DPO pair generation); this is the best teaching tool for "synthetic data generation" since it packages published techniques as composable steps and can export straight into Argilla for human review.
- **Label Studio** — the broader-scope, most actively updated (2025–2026) general annotation platform, now explicitly covering LLM/RLHF workflows, response grading, side-by-side comparison, and RAG evaluation (Ragas integration); moved to a monorepo. Best when the teaching goal is generic multi-modal labeling rather than LLM-specific synthetic data.
- **Lilac** — **discontinued**: acquired by Databricks (early 2024), repo archived July 2025, folded into Databricks' platform. Do not build teaching material around it; mention only as a historical note.

## (d) Tokenizers

- **tiktoken** — encode-only, fastest (3–6× alternatives), powers OpenAI + Llama 3/4 + Mistral's Tekken; cannot train a tokenizer, only run one.
- **Hugging Face tokenizers** — Rust-backed, full training support (BPE/WordPiece/Unigram), the practical default for anyone training a custom vocabulary and wanting Hub/Transformers integration.
- **SentencePiece** — raw-byte-stream training, no pretokenization, low memory footprint, standard for multilingual models (Gemini/Gemma family).
- **minbpe** — not for production, but the correct teaching artifact: shows *why* BPE works before students touch the production libraries above.

## 2025–2026 Developments Worth Flagging

1. **nanochat** (Oct 2025) reset the bar for "minimal full-stack teaching repo" — design your curriculum's spine around its progression (tokenize → pretrain → mid-train → SFT → RL) rather than nanoGPT alone.
2. **OLMo 2 / OLMo-core** cemented "fully open" (data+code+checkpoints+recipe) as the credible standard against which everything else should be compared.
3. **NeMo Curator's Ray-based multi-modal rewrite** (early 2026) signals GPU-native curation is now expected even for text-only pipelines.
4. **Lilac's death** is a cautionary tale worth including explicitly: don't anchor a curriculum on a single-vendor tool that can be acquired and archived.
5. Muon-optimizer-driven speedrun records (sub-2-minutes to GPT-2 quality on 8×H100, per modded-nanoGPT lineage) show optimizer/systems tricks now matter as much as architecture for a teaching module on efficiency.

## Sources

[karpathy/nanochat](https://github.com/karpathy/nanochat), [karpathy/llm.c](https://github.com/karpathy/llm.c), [karpathy/minbpe](https://github.com/karpathy/minbpe), [TorchTitan paper](https://arxiv.org/html/2410.06511v3), [huggingface/nanotron](https://github.com/huggingface/nanotron/blob/main/docs/docs.md), [Ai2 OLMo 2 blog](https://allenai.org/blog/olmo2), [OLMo 2 32B blog](https://allenai.org/blog/olmo2-32b), [Spheron: NeMo Curator/Datatrove/FineWeb guide](https://www.spheron.network/blog/ai-pretraining-data-curation-nemo-curator-datatrove-fineweb-gpu-cloud/), [NVIDIA-NeMo/Curator](https://github.com/NVIDIA-NeMo/Curator), [NeMo Curator dedup docs](https://docs.nvidia.com/nemo/curator/curate-text/process-data/deduplication), [Together RedPajama blog](https://www.together.ai/blog/redpajama), [TinyLlama paper](https://arxiv.org/html/2401.02385v2), [Argilla distilabel intro](https://argilla.io/blog/introducing-distilabel-1/), [argilla-io/distilabel](https://github.com/argilla-io/distilabel), [Label Studio](https://labelstud.io/), [Databricks Lilac acquisition](https://www.databricks.com/blog/lilac-joins-databricks-simplify-unstructured-data-evaluation-generative-ai), [tiktoken/SentencePiece/HF tokenizer comparison](https://www.bestaiweb.ai/how-to-train-and-choose-a-custom-tokenizer-with-tiktoken-sentencepiece-and-hf-tokenizers-in-2026/), [MegaCpp framework survey](https://megacpp.com/blog/framework-survey-fsdp-vs-megatron-vs-deepspeed/).
