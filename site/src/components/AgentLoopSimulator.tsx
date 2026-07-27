import React, { useEffect, useState } from 'react';

const STATES = [
  {
    label: 'Reason',
    owns: 'Choose the next action from the current observation.',
    event: 'Need the repository state before editing.',
  },
  {
    label: 'Propose tool',
    owns: 'Emit a structured call, not a fabricated result.',
    event: 'read_file(path="config.ts")',
  },
  {
    label: 'Validate',
    owns: 'Check schema, permission, and sandbox policy.',
    event: 'Read is allowed; path is inside the workspace.',
  },
  {
    label: 'Observe',
    owns: 'Inject the real tool result at a hard generation boundary.',
    event: 'config.ts returned 84 lines.',
  },
  {
    label: 'Decide',
    owns: 'Stop, repair, or begin another grounded cycle.',
    event: 'Evidence is sufficient; propose the smallest edit.',
  },
];

export default function AgentLoopSimulator(): React.ReactElement {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return undefined;
    const timer = window.setInterval(() => {
      setStep((current) => {
        if (current >= STATES.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 900);
    return () => window.clearInterval(timer);
  }, [playing]);

  const reset = () => {
    setStep(0);
    setPlaying(false);
  };

  return (
    <div className="learning-widget agent-loop">
      <header className="lab-header">
        <div>
          <span className="lab-eyebrow">Grounded trajectory</span>
          <strong>Where must generation stop and the harness take control?</strong>
        </div>
        <div className="lab-actions">
          <button
            type="button"
            onClick={() => {
              if (step === STATES.length - 1 && !playing) {
                setStep(0);
                setPlaying(true);
                return;
              }
              setPlaying((value) => !value);
            }}
          >
            {playing ? 'Pause' : step === STATES.length - 1 ? 'Replay' : 'Play'}
          </button>
          <button type="button" onClick={reset}>Reset</button>
        </div>
      </header>

      <ol className="agent-loop__rail">
        {STATES.map((state, index) => (
          <li key={state.label} data-active={index === step} data-passed={index < step}>
            <button
              type="button"
              aria-pressed={index === step}
              onClick={() => {
                setStep(index);
                setPlaying(false);
              }}
            >
              <span>{index + 1}</span>
              {state.label}
            </button>
          </li>
        ))}
      </ol>

      <div className="agent-loop__event" aria-live="polite">
        <span>Harness event</span>
        <strong>{STATES[step].event}</strong>
        <p>{STATES[step].owns}</p>
      </div>

      <p>
        The dangerous transition is tool proposal → observation. If sampling
        continues through that boundary, the model can invent an observation.
        The harness must stop generation, validate and execute the call, then
        append the real result before the next reasoning step.
      </p>
    </div>
  );
}
