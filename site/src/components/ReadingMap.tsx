import React from 'react';

type MapLink = {
  href: string;
  label: string;
  note: string;
};

const BUILD_PATH: MapLink[] = [
  {
    href: '/playground/foundations/',
    label: 'Mechanism',
    note: 'Follow one token through attention, residual updates, and logits.',
  },
  {
    href: '/playground/foundations/01-first-training-loop/',
    label: 'First training loop',
    note: 'Make the forward pass, loss, gradients, and update visible.',
  },
  {
    href: '/playground/missions/01-language-model-agent/00-corpus/',
    label: 'Corpus',
    note: 'Turn raw web text into a training-ready shard.',
  },
  {
    href: '/playground/missions/01-language-model-agent/01-tokenizer/',
    label: 'Tokenizer',
    note: 'Build the vocabulary that fixes every later token ID.',
  },
  {
    href: '/playground/missions/01-language-model-agent/02-pretrain/',
    label: 'Pretrain',
    note: 'Train the decoder and produce a resumable checkpoint.',
  },
  {
    href: '/playground/missions/01-language-model-agent/03-sft/',
    label: 'SFT',
    note: 'Teach the checkpoint to answer with assistant-only loss.',
  },
  {
    href: '/playground/missions/01-language-model-agent/04-rl/',
    label: 'RL',
    note: 'Improve behavior only where a verifiable reward exists.',
  },
  {
    href: '/playground/missions/01-language-model-agent/05-serve/',
    label: 'Serve',
    note: 'Measure decoding, cache use, batching, and concurrency.',
  },
  {
    href: '/playground/missions/01-language-model-agent/06-agent/',
    label: 'Agent',
    note: 'Put the model inside a bounded tool loop.',
  },
  {
    href: '/playground/missions/01-language-model-agent/07-eval/',
    label: 'Evaluate',
    note: 'Decide what the complete system earned the right to claim.',
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
              <span className="reading-map__index">{String(index + 1).padStart(2, '0')}</span>
              <span className="reading-map__step-copy">
                <span className="reading-map__step-heading">
                  <strong>{step.label}</strong>
                </span>
                <span>{step.note}</span>
              </span>
            </a>
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
