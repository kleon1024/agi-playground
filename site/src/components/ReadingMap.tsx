import React from 'react';

type MapLink = {
  href: string;
  label: string;
  note: string;
};

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
  /** A companion chapter that continues this stage's own argument. */
  companion?: { href: string; label: string };
};

const MISSION = '/playground/missions/01-language-model-agent';

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
        href: '/playground/platform/data/',
        label: 'Platform / data',
        returns: 'a manifest and per-stage rejection reasons',
      },
    ],
  },
  {
    href: `${MISSION}/01-tokenizer/`,
    label: 'Tokenizer',
    note: 'Build the vocabulary that fixes every later token ID.',
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
        href: '/playground/platform/training/03-throughput/',
        label: 'Throughput',
        returns: '14.69x between the slowest and fastest run of the same model',
      },
      {
        href: '/playground/platform/training/02-architecture-ablations/',
        label: 'Architecture ablations',
        returns: 'six design choices measured, and the two everyone argues about flipping sign between seeds',
      },
      {
        href: '/playground/platform/training/05-upcycling/',
        label: 'Upcycling',
        returns: 'a converted checkpoint that starts at its parent’s loss',
      },
    ],
    companion: { href: `${MISSION}/02-pretrain/verifying-the-run/`, label: 'Verifying the run' },
  },
  {
    href: `${MISSION}/03-sft/`,
    label: 'SFT',
    note: 'Teach the checkpoint to answer, with loss on assistant turns only.',
    detours: [
      {
        href: '/playground/platform/adaptation/distillation/',
        label: 'Distillation',
        returns: 'a target format, and the tokenizer constraint that decides it',
      },
    ],
    companion: { href: `${MISSION}/03-sft/what-it-costs/`, label: 'What it costs' },
  },
  {
    href: `${MISSION}/04-rl/`,
    label: 'RL',
    note: 'Improve behavior only where a verifiable reward exists.',
    detours: [
      {
        href: '/playground/platform/adaptation/reinforcement-learning/',
        label: 'Reinforcement learning',
        returns: 'the condition under which the gradient is non-zero at all',
      },
    ],
    companion: { href: `${MISSION}/04-rl/reward-went-up/`, label: 'Did the model get better?' },
  },
  {
    href: `${MISSION}/05-serve/`,
    label: 'Serve',
    note: 'Measure decoding, cache use, batching, and concurrency.',
    detours: [
      {
        href: '/playground/platform/serving/',
        label: 'Platform / serving',
        returns: 'the cost model for one request',
      },
      {
        href: '/playground/platform/serving/01-graph-execution/',
        label: 'Graph execution',
        returns: 'which of three bottlenecks the decode step actually has, and roughly 3x from fixing it',
      },
    ],
    companion: { href: `${MISSION}/05-serve/why-concurrency-pays/`, label: 'Why concurrency pays' },
  },
  {
    href: `${MISSION}/06-agent/`,
    label: 'Agent',
    note: 'Put the model inside a bounded tool loop.',
    detours: [
      {
        href: '/playground/capabilities/act-coordinate/',
        label: 'Act and coordinate',
        returns: 'a permission and stop-condition contract',
      },
    ],
    companion: { href: `${MISSION}/06-agent/what-stops-it/`, label: 'What stops it' },
  },
  {
    href: `${MISSION}/07-eval/`,
    label: 'Evaluate',
    note: 'Decide what the complete system earned the right to claim.',
    detours: [
      {
        href: '/playground/platform/evaluation-observability/',
        label: 'Evaluation and observability',
        returns: 'variance, and the disclosure a result has to carry',
      },
    ],
    companion: { href: `${MISSION}/07-eval/why-believe-the-number/`, label: 'Why believe the number' },
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
    href: '/playground/missions/02-personalized-discovery/',
    index: '02',
    title: 'Personalized discovery',
    question: 'Can a ranking system help a user find something worth their attention?',
    route: 'interactions → recall → rank → value → mix → rules → serve → report',
  },
  {
    href: '/playground/missions/03-quantitative-research/',
    index: '03',
    title: 'Quantitative research',
    question: 'Can a candidate signal survive leakage, search bias, costs, and capacity?',
    route: 'market data → signal search → rank → walk-forward → costs → report',
  },
];

const REFERENCE_LAYERS: MapLink[] = [
  {
    href: '/playground/platform/',
    label: 'Platform',
    note: 'Data, training, adaptation, serving, evaluation, and safety.',
  },
  {
    href: '/playground/capabilities/',
    label: 'Capabilities',
    note: 'Reusable mechanisms only after more than one mission needs them.',
  },
  {
    href: '/playground/infra/',
    label: 'Infrastructure',
    note: 'Choose the local or cloud compute lane and reproduce the runtime.',
  },
  {
    href: '/playground/standards/',
    label: 'Standards',
    note: 'Check the lesson, run, mission, and evidence contracts.',
  },
];

export function BuildPath(): React.ReactElement {
  return (
    <nav className="reading-map" aria-label="Language-model system reading path">
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
              </span>
            </a>
            {(step.detours || step.companion) && (
              <ul className="reading-map__branches">
                {step.detours?.map((detour) => (
                  <li className="reading-map__branch" data-kind="detour" key={detour.href}>
                    <a href={detour.href}>
                      <strong>{detour.label}</strong>
                    </a>
                    <span> — return with {detour.returns}.</span>
                  </li>
                ))}
                {step.companion && (
                  <li className="reading-map__branch" data-kind="companion">
                    <a href={step.companion.href}>
                      Then: <strong>{step.companion.label}</strong>
                    </a>
                  </li>
                )}
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
          <span className="mission-branch__index">Mission {path.index}</span>
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
