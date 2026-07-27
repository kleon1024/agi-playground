import React, { useMemo, useState } from 'react';

const TOKENS = [
  { text: '<user>', role: 'prompt' },
  { text: 'What', role: 'prompt' },
  { text: 'is', role: 'prompt' },
  { text: 'LoRA?', role: 'prompt' },
  { text: '<assistant>', role: 'prompt' },
  { text: 'A', role: 'answer' },
  { text: 'low-rank', role: 'answer' },
  { text: 'adapter.', role: 'answer' },
  { text: '<end>', role: 'answer' },
] as const;

export default function AssistantLossMask(): React.ReactElement {
  const [trainPrompts, setTrainPrompts] = useState(false);
  const trained = useMemo(
    () => TOKENS.filter((token) => trainPrompts || token.role === 'answer').length,
    [trainPrompts],
  );

  return (
    <div className="learning-widget loss-mask-lab">
      <header className="lab-header">
        <div>
          <span className="lab-eyebrow">Supervision boundary</span>
          <strong>Which tokens should contribute to the SFT loss?</strong>
        </div>
        <output>{trained}/{TOKENS.length} targets active</output>
      </header>

      <button
        type="button"
        aria-pressed={trainPrompts}
        onClick={() => setTrainPrompts((value) => !value)}
      >
        {trainPrompts ? 'Mask prompt tokens' : 'Also train on prompt tokens'}
      </button>

      <div className="loss-mask-lab__sequence" aria-label="Conversation token loss mask">
        {TOKENS.map((token, index) => {
          const active = trainPrompts || token.role === 'answer';
          return (
            <div key={`${token.text}-${index}`} data-active={active}>
              <span>{token.text}</span>
              <small>{active ? 'target' : '−100'}</small>
            </div>
          );
        })}
      </div>

      <p>
        Assistant content and its closing token are targets. User and role
        markers are context the harness supplies, so their labels are −100.
        Turning prompt loss on spends gradient budget reproducing the prompt and
        teaches the model that generating both sides of the conversation is valid.
      </p>
    </div>
  );
}
