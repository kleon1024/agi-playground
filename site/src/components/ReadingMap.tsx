import React from 'react';
import READING_COST from '../reading-cost.generated.json';

type MapLink = {
  href: string;
  label: string;
  note: string;
};

/* Reading minutes come from sync-docs.py, which derives them from the same
   word count that prints the badge on each page. Nothing here is typed by
   hand, so a route's declared cost cannot drift away from its chapters. */
const COST: Record<string, { level: string; minutes: number }> = READING_COST;

function minutesFor(href: string): number {
  const path = href.replace(/^\/playground\//, '').replace(/\/$/, '');
  return COST[path]?.minutes ?? 0;
}

function totalMinutes(hrefs: string[]): number {
  return hrefs.reduce((sum, href) => sum + minutesFor(href), 0);
}

type Step = MapLink & {
  /** Support chapters this stage sends you to, and what each returns.
   *  Rendered as branches off the step, never as steps of their own — the
   *  spine used to open with two foundations chapters before the mission
   *  started, so the reader met "first training loop" as step 02 and then
   *  doubled back to "corpus" as step 03.
   *
   *  These are listed here and not only inside the chapter because a platform
   *  chapter nobody links to from the path is a chapter nobody reads. */
  detours?: Array<{ href: string; label: string; returns: string }>;
  /** Companion chapters that continue this stage's own argument. A stage can
   *  have more than one: 05-serve owns both the paging mechanism and the
   *  concurrency result, and neither is a detour into another section. */
  companions?: Array<{ href: string; label: string }>;
};

const MISSION = '/playground/01-language-model';

/* Eight stages, and only the eight stages. Anything that is not a stage is a
   branch hanging off one, because a reader following this list top to bottom
   must never be sent backwards. */
const BUILD_PATH: Step[] = [
  {
    href: `${MISSION}/00-corpus/`,
    label: 'Corpus',
    note: 'Turn raw web text into a training-ready shard you can defend.',
    detours: [
      {
        href: '/playground/foundations/05-is-the-difference-real/',
        label: 'Is the difference real',
        returns: 'why one run per arm cannot rank two data mixtures',
      },
    ],
    companions: [
      { href: `${MISSION}/00-corpus/what-a-release-needs/`, label: 'What a release needs' },
    ],
  },
  {
    href: `${MISSION}/01-tokenizer/`,
    label: 'Tokenizer',
    note: 'Build the vocabulary that fixes every later token ID.',
    companions: [
      { href: `${MISSION}/01-tokenizer/is-it-the-same-tokenizer/`, label: 'Is it the same tokenizer' },
    ],
  },
  {
    href: `${MISSION}/02-pretrain/`,
    label: 'Pretrain',
    note: 'Train the decoder and produce a resumable checkpoint.',
    detours: [
      {
        href: '/playground/foundations/00-attention/',
        label: 'The decoder block',
        returns: "the forward path, and this model's parameter count derived from its own formulas",
      },
      {
        href: '/playground/foundations/04-distributed-training/',
        label: 'Distributed training',
        returns: 'a sharding strategy and what its communication actually costs',
      },
    ],
    companions: [
      { href: `${MISSION}/02-pretrain/verifying-the-run/`, label: 'Verifying the run' },
      { href: `${MISSION}/02-pretrain/architecture-ablations/`, label: 'Architecture ablations' },
      { href: `${MISSION}/02-pretrain/throughput/`, label: 'Throughput' },
      { href: `${MISSION}/02-pretrain/upcycling/`, label: 'Upcycling' },
      { href: `${MISSION}/02-pretrain/when-the-curve-goes-wrong/`, label: 'When the curve goes wrong' },
      { href: `${MISSION}/02-pretrain/latent-reasoning/`, label: 'Latent reasoning' },
    ],
  },
  {
    href: `${MISSION}/03-sft/`,
    label: 'SFT',
    note: 'Teach the checkpoint to answer, with loss on assistant turns only.',
    detours: [
      {
        href: '/playground/01-language-model/02-pretrain/mid-training/',
        label: 'Mid-training',
        returns: 'why agentic trajectories enter the corpus before SFT, and in what format',
      },
    ],
    companions: [
      { href: `${MISSION}/03-sft/what-it-costs/`, label: 'What it costs' },
      { href: `${MISSION}/03-sft/beyond-demonstrations/`, label: 'Beyond demonstrations' },
      { href: `${MISSION}/03-sft/distillation/`, label: 'Distillation' },
    ],
  },
  {
    href: `${MISSION}/04-rl/`,
    label: 'RL',
    note: 'Improve behavior only where a verifiable reward exists.',
    detours: [
      {
        href: '/playground/01-language-model/04-rl/rollout-concurrency/',
        label: 'Rollout concurrency',
        returns: 'why an update step waits on its slowest trajectory',
      },
    ],
    companions: [
      { href: `${MISSION}/04-rl/reward-went-up/`, label: 'Did the model get better?' },
      { href: `${MISSION}/04-rl/what-a-real-loop-adds/`, label: 'What a real loop adds' },
    ],
  },
  {
    href: `${MISSION}/05-serve/`,
    label: 'Serve',
    note: 'Measure decoding, cache use, batching, and concurrency.',
    companions: [
      { href: `${MISSION}/05-serve/paging-the-cache/`, label: 'Paging the cache' },
      { href: `${MISSION}/05-serve/why-concurrency-pays/`, label: 'Why concurrency pays' },
      { href: `${MISSION}/05-serve/graph-execution/`, label: 'Graph execution' },
      { href: `${MISSION}/05-serve/quantization/`, label: 'Quantization' },
      {
        href: `${MISSION}/05-serve/speculative-decoding/`,
        label: 'Speculative decoding',
      },
    ],
  },
  {
    href: `${MISSION}/06-agent/`,
    label: 'Agent',
    note: 'Put the model inside a bounded tool loop.',
    companions: [
      { href: `${MISSION}/06-agent/what-fits-in-context/`, label: 'What fits in context' },
      { href: `${MISSION}/06-agent/what-stops-it/`, label: 'What stops it' },
      {
        href: `${MISSION}/06-agent/would-a-second-agent-help/`,
        label: 'Would a second agent help',
      },
    ],
  },
  {
    href: `${MISSION}/07-eval/`,
    label: 'Evaluate',
    note: 'Decide what the complete system earned the right to claim.',
    detours: [
      {
        href: '/playground/foundations/06-significance/',
        label: 'Statistical significance',
        returns: 'whether the gap you measured survives its own noise',
      },
    ],
    companions: [
      { href: `${MISSION}/07-eval/whose-harness/`, label: 'Whose harness produced it' },
      { href: `${MISSION}/07-eval/why-believe-the-number/`, label: 'Why believe the number' },
      { href: `${MISSION}/07-eval/metric-gaming/`, label: 'Metric gaming' },
      { href: `${MISSION}/07-eval/who-decides-to-ship/`, label: 'Who decides to ship' },
      { href: `${MISSION}/07-eval/eval-gates/`, label: 'Evaluation gates' },
      { href: `${MISSION}/07-eval/red-teaming/`, label: 'Red-teaming' },
    ],
  },
];

const DECISION_PATHS: Array<{
  href: string;
  index: string;
  title: string;
  question: string;
  route: string;
}> = [
  {
    href: '/playground/01-language-model/vision/',
    index: '01',
    title: 'Vision-language pathway',
    question: 'A sub-path of the language-model topic: does a self-trained vision pathway beat a hosted VLM and a text-only baseline?',
    route: 'image+question task → vision fusion → report → real-photo task → real-photo fusion → real-photo report → warmup stability',
  },
  {
    href: '/playground/02-personalized-discovery/',
    index: '02',
    title: 'Personalized discovery',
    question: 'Can a ranking system help a user find something worth their attention?',
    route: 'interactions → recall → rank → value → mix → rules → serve → report',
  },
  {
    href: '/playground/03-quantitative-research/',
    index: '03',
    title: 'Quantitative research',
    question: 'Can a candidate signal survive leakage, search bias, costs, and capacity?',
    route: 'market data → signal search → rank → walk-forward → costs → report',
  },
  {
    href: '/playground/04-agentic-platform/',
    index: '04',
    title: 'Agentic platform',
    question: 'Is a merged patch from an autonomous agent worth what it costs, per task?',
    route: 'task set → no-harness baseline → agent loop → cheap-or-expensive routing → failure modes → report → closing the loop',
  },
  {
    href: '/playground/05-game-ai/',
    index: '05',
    title: 'Game-playing policy',
    question: 'Does RL against a verifiable game reward beat a fixed baseline, and at what cost?',
    route: 'gridworld baselines → GRPO → report → fixing collapse → MiniGrid → report → tool-use RL',
  },
  {
    href: '/playground/07-multimodal-generation/',
    index: '07',
    title: 'Multimodal generation',
    question: 'Does this repository\'s compute discipline survive sound and moving images — and does one codebook lesson transfer across both?',
    route: 'voice: codec → streaming decode → report → real speech and network → multi-speaker → codebook reset · video: synthetic dataset → tokenizer → generation model → report → longer sequences → multi-object',
  },
  {
    href: '/playground/08-bio-pharma-modeling/',
    index: '08',
    title: 'Molecular property prediction',
    question: 'Can a small from-scratch model beat a descriptor baseline on a real toxicity endpoint?',
    route: 'dataset and property → descriptor baseline and model → report → second endpoint → third endpoint → cross-endpoint analysis',
  },
  {
    href: '/playground/09-autonomous-driving/',
    index: '09',
    title: 'Autonomous driving',
    question: 'Can a policy that only imitated an expert in a simulator still drive in the loop?',
    route: 'scenario simulator → perception baseline → expert policy → behavior cloning → closed-loop eval → harder scenarios → report',
  },
];

const REFERENCE_LAYERS: MapLink[] = [
  {
    href: '/playground/foundations/',
    label: 'Foundations',
    note: 'Mechanism that holds regardless of which topic you are running.',
  },
  {
    href: '/playground/foundations/04-distributed-training/',
    label: 'Machine chapters',
    note: 'Networking, storage, orchestration, and GPU-cluster concepts; compute lanes live in reference.',
  },
  {
    href: '/playground/reference/standards/',
    label: 'Standards',
    note: 'Check the lesson, run, topic, and evidence contracts.',
  },
];

export function BuildPath(): React.ReactElement {
  const spine = totalMinutes(BUILD_PATH.map((step) => step.href));
  const companions = totalMinutes(
    BUILD_PATH.flatMap((step) => step.companions ?? []).map((c) => c.href),
  );
  const detours = totalMinutes(
    BUILD_PATH.flatMap((step) => step.detours ?? []).map((d) => d.href),
  );
  return (
    <nav className="reading-map" aria-label="Language-model system reading path">
      <p className="reading-map__budget">
        <strong>{BUILD_PATH.length} stages, {spine} minutes.</strong> Read only the
        numbered stages and you have the whole build. The companions add {companions} min
        and answer the question each stage raises but does not settle; the detours add{' '}
        {detours} min and each returns something the next stage consumes.
      </p>
      <ol className="reading-map__spine">
        {BUILD_PATH.map((step, index) => (
          <li key={step.href} className="reading-map__step">
            <a href={step.href}>
              <span className="reading-map__index">{String(index).padStart(2, '0')}</span>
              <span className="reading-map__step-copy">
                <span className="reading-map__step-heading">
                  <strong>{step.label}</strong>
                </span>
                <span>{step.note}</span>
                <span className="reading-map__minutes">{minutesFor(step.href)} min</span>
              </span>
            </a>
            {(step.detours || step.companions) && (
              <ul className="reading-map__branches">
                {step.detours?.map((detour) => (
                  <li className="reading-map__branch" data-kind="detour" key={detour.href}>
                    <a href={detour.href}>
                      <strong>{detour.label}</strong>
                    </a>
                    <span> — return with {detour.returns}.</span>
                  </li>
                ))}
                {step.companions?.map((companion) => (
                  <li className="reading-map__branch" data-kind="companion" key={companion.href}>
                    <a href={companion.href}>
                      Then: <strong>{companion.label}</strong>
                    </a>
                    <span className="reading-map__minutes"> {minutesFor(companion.href)} min</span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function DecisionPaths(): React.ReactElement {
  return (
    <nav className="mission-branches" aria-label="Decision-system reading paths">
      {DECISION_PATHS.map((path) => (
        <a className="mission-branch" href={path.href} key={path.href}>
          <span className="mission-branch__index">Topic {path.index}</span>
          <strong>{path.title}</strong>
          <span className="mission-branch__question">{path.question}</span>
          <span className="mission-branch__route">{path.route}</span>
        </a>
      ))}
    </nav>
  );
}

export function ReferenceLayers(): React.ReactElement {
  return (
    <nav className="reference-layers" aria-label="Curriculum reference layers">
      {REFERENCE_LAYERS.map((layer) => (
        <a href={layer.href} key={layer.href}>
          <strong>{layer.label}</strong>
          <span>{layer.note}</span>
        </a>
      ))}
    </nav>
  );
}
