# Handoff — cleanup pass

**To:** Codex
**From:** Claude Code session on `agi-playground`
**Repos in scope:** `agi-playground` (items 2–4), `rehearse` (item 1)

Four issues, each with the evidence I actually gathered rather than an
impression. Where I could not establish the answer, I say so instead of
guessing — item 1 in particular contains a contradiction I could not resolve
and you should settle before changing anything.

---

## 1. shadcn/ui is still present in `rehearse`, contrary to expectation

**Repo:** `~/maestro/projects/rehearse`

**The contradiction.** The product owner states the app is no longer on
shadcn/ui. The working tree disagrees:

```
components.json                    present (shadcn CLI config)
src/components/ui/                 18 components (button, card, dialog, …)
package.json                       12 @radix-ui/* dependencies
```

`src/app/globals.css` also still carries the full shadcn token contract
(`--background`, `--card`, `--popover`, `--destructive`, `--ring`, `--chart-1..5`)
inside a Tailwind v4 `@theme inline` block.

**Do not act on the assumption that these are dead.** I nearly recommended
deleting the `--color-*` tokens after a scan showed no `var(--color-primary)`
references anywhere. That scan was wrong: Tailwind v4 compiles `@theme` entries
into utility classes, and `bg-primary` / `text-muted-foreground` /
`border-border` are used **285 times** across `src/`. Removing them would break
the app's styling wholesale.

**Establish first, then decide:**

1. Are the 18 `src/components/ui/*` components actually imported? Count real
   import sites per component; some may be genuinely orphaned while the rest
   are load-bearing.
2. Is there a newer component layer that was meant to replace them? If a
   migration is partially done, the half-migrated state is the bug, not the
   presence of shadcn itself.
3. Which of the 12 Radix packages are reachable from a rendered route?

**Then:** either finish the migration (remove only what is provably unimported,
one component per commit, with the build and a visual check per step), or
conclude the app is still shadcn-based and correct the docs that claim
otherwise. Both are acceptable outcomes; a half-state is not.

**Docs that assert the stack** and must end up consistent with reality:
`README.md`, `CLAUDE.md`, `AGENTS.md`,
`docs/superpowers/specs/2026-03-16-interview-training-platform-design.md`.

**Acceptance:** `rg "shadcn|radix" --type md` in `rehearse` returns only
statements that match the built application, and the app renders unchanged
before and after.

**Coupling you must not break:** `agi-playground/site/src/css/brand.css`
mirrors these tokens so the curriculum at `rehearse.maestro.onl/playground`
matches the product. If the token names or values change, that file needs the
same change in the same commit, or the two halves of one domain drift apart
visually.

---

## 2. Chinese and English are mixed in `agi-playground` content

**Repo:** `~/maestro/projects/agi-playground`

The repository is English-first. Three files break that, and they are not all
the same case:

| File | Occurrence | Recommendation |
|---|---|---|
| `README.md:7` | Tagline: `从基础设施出发，组合泛 AI 能力，交付可衡量的业务结果。` | **Keep.** Deliberate bilingual positioning line, directly under the English tagline. |
| `missions/02-personalized-discovery/README.md` | 5 occurrences: `粗排`, `精排`, `价值树` in a diagram and three headings | **Decide and apply consistently** (see below). |
| `missions/01-language-model-agent/01-tokenizer/core/bpe.py:438` | Default CLI test string `"Hello world! 你好，世界。 1234567"` | **Keep.** It is the test payload proving byte-level BPE has no `<UNK>` for non-Latin text. Removing it would delete the demonstration. |

**The mission 02 case is a real judgment call, not an oversight.** `粗排` /
`精排` / `价值树` are the industry-standard terms in Chinese recommender
practice, and a reader who has worked on such a system will recognise them
faster than "pre-rank" / "fine-rank" / "value tree". But an English-first repo
cannot have untranslated terms in headings.

**Recommended:** English as the heading term, with the Chinese given once in
parentheses at first use and not repeated — `**Pre-rank**` in the heading, and
in the body "pre-ranking (粗排 in Chinese practice)". Apply the same treatment
in the Mermaid diagram: English labels only.

Check for regressions with:

```bash
rg '[\p{Han}]' --glob '*.md' --glob '*.py' --glob '*.tsx' \
   foundations platform capabilities missions standards site/src
```

---

## 3. Lesson lengths are unbalanced by roughly 19×

**Repo:** `~/maestro/projects/agi-playground`

Measured line counts of every lesson `README.md`:

```
 23  standards/README.md
 30  missions/01-language-model-agent/02-pretrain/README.md
 37  missions/01-language-model-agent/06-agent/prod/README.md
 50  platform/safety-governance/README.md
 53  missions/01-language-model-agent/README.md
138  missions/01-language-model-agent/01-tokenizer/README.md
…
336  platform/training/README.md
377  platform/serving/README.md
444  capabilities/act-coordinate/README.md
```

**The short ones are the actual problem.** They are stubs left behind when the
surrounding work moved faster than they did:

- `missions/01-language-model-agent/02-pretrain/README.md` (30 lines) is the
  worst offender. Its stage has a finished model, data pipeline, training loop
  and a recorded run, but the lesson never got written. It should look like
  `01-tokenizer/README.md` (138 lines).
- `standards/README.md` (23) is an index and can stay short.
- `missions/01-language-model-agent/README.md` (53) should carry the mission
  narrative, not just a stage table.
- `platform/safety-governance/README.md` (50) is honestly marked as not yet
  built; leave it until a mission needs it.

**The long ones are mostly fine.** `capabilities/act-coordinate` at 444 lines
covers harness engineering, which the research identified as the least-served
topic in the field — length there is the point. Do not trim for symmetry.
**However**, the product owner's instruction was explicit: *do not shorten
paragraphs and do not add headings.* Where a long lesson is hard going, the fix
is an interactive widget or diagram carrying part of the load, not cuts.

**Target:** no built lesson under ~120 lines; length above that governed by
subject, not by a quota.

---

## 4. Hard-coded dates in prose

**Repo:** `~/maestro/projects/agi-playground`

14 occurrences of `2026-07-2X`. **They are not all the same, and the
distinction matters — stripping them uniformly would destroy the repository's
core mechanism.**

**Must keep — dates are evidence:**

```
foundations/01-first-training-loop/runs/2026-07-26-tiny-shakespeare.md
platform/training/01-distributed/runs/2026-07-27-cpu-simulation.md
missions/01-language-model-agent/01-tokenizer/runs/2026-07-26-bpe-16k.md
missions/01-language-model-agent/02-pretrain/runs/2026-07-26-loop-mechanics.md
missions/01-language-model-agent/00-corpus/runs/2026-07-26-core-vs-datatrove.md
docs/superpowers/specs/2026-07-24-agi-playground-design.md
```

Every published number in this repository must trace to a run record naming the
command, hardware, wall-clock and date — see
[`standards/lesson-and-run-contract.md`](../../standards/lesson-and-run-contract.md).
An undated run record is not evidence. Filenames and the `verified:` frontmatter
field stay.

**Should remove — dates in teaching prose:**

- `verified: 2026-07-26` is fine in frontmatter, but sentences like "Run
  2026-07-24 from a macOS dev box" inside lesson bodies date the material
  without adding anything; link the run record instead.
- `platform/data/README.md` and `missions/.../01-tokenizer/README.md` reference
  dates inline where a link to `runs/` would serve better.
- Research documents under `research/` are dated surveys and should keep their
  "conducted 2026-07-24" provenance line — that one is a scoping fact, not
  clutter.

**Rule to apply:** a date belongs in a run record, a filename, frontmatter, or a
survey provenance line. It does not belong mid-sentence in a lesson.

---

## Working notes

- Repo gates: `uv run ruff check .` and `uv run pytest -q` from the repo root.
  Both must pass. Run them **from the root** — a stale `cd` into a subdirectory
  makes pytest collect nothing and report success, which cost me a bad commit.
- The docs site generates `site/docs/` from repository markdown at build time
  and is git-ignored. Never edit it; edit the source markdown. Build with
  `npm run build` in `site/`, never `npx docusaurus build`, which skips the sync
  step and silently builds stale content.
- Admonition titles must use MDX 3 bracket syntax — `:::note[Title]`. The older
  `:::note Title` does not error; it renders as a literal paragraph. The sync
  step normalises this, but hand-written `.mdx` under `site/` is not covered.
- Lesson markdown can embed an interactive widget with
  `<!-- interactive: ComponentName -->`, which GitHub renders as nothing and the
  site turns into a live React component.
