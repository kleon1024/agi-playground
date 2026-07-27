import React, { useEffect, useMemo, useRef, useState } from 'react';

export interface ProcessStep {
  id: string;
  label: string;
  owns: string;
  handoff: string;
}

interface ProcessDiagramProps {
  eyebrow: string;
  question: string;
  steps: ProcessStep[];
  loop?: string;
}

export default function ProcessDiagram({
  eyebrow,
  question,
  steps,
  loop,
}: ProcessDiagramProps): React.ReactElement {
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  const rootRef = useRef<HTMLElement>(null);
  const startedRef = useRef(false);
  const current = steps[active];

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const stop = () => {
      if (reduced.matches) setPlaying(false);
    };
    reduced.addEventListener('change', stop);
    if (reduced.matches || startedRef.current) {
      return () => reduced.removeEventListener('change', stop);
    }

    const start = () => {
      if (startedRef.current) return;
      startedRef.current = true;
      setPlaying(true);
    };
    if (!('IntersectionObserver' in window)) {
      start();
      return () => reduced.removeEventListener('change', stop);
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          start();
          observer.disconnect();
        }
      },
      { threshold: 0.45 },
    );
    if (rootRef.current) observer.observe(rootRef.current);
    return () => {
      observer.disconnect();
      reduced.removeEventListener('change', stop);
    };
  }, []);

  useEffect(() => {
    if (!playing) return undefined;
    const timer = window.setInterval(() => {
      setActive((previous) => {
        if (previous >= steps.length - 1) {
          setPlaying(false);
          return previous;
        }
        return previous + 1;
      });
    }, 1100);
    return () => window.clearInterval(timer);
  }, [playing, steps.length]);

  const stepStyle = useMemo(
    () => ({ '--process-step-count': steps.length }) as React.CSSProperties,
    [steps.length],
  );

  const replay = () => {
    setActive(0);
    setPlaying(true);
  };

  return (
    <figure ref={rootRef} className="learning-widget process-diagram" style={stepStyle}>
      <header className="process-diagram__header">
        <div>
          <div className="process-diagram__eyebrow">{eyebrow}</div>
          <strong className="process-diagram__question">{question}</strong>
        </div>
        <button
          type="button"
          className="process-diagram__play"
          onClick={() => (active === steps.length - 1 && !playing ? replay() : setPlaying((value) => !value))}
          aria-label={playing ? 'Pause process animation' : 'Play process animation'}
        >
          {playing ? 'Pause' : active === steps.length - 1 ? 'Replay' : 'Play'}
        </button>
      </header>

      <ol className="process-diagram__track" aria-label={question}>
        {steps.map((step, index) => (
          <li key={step.id} className="process-diagram__step">
            <button
              type="button"
              className="process-diagram__node"
              data-active={index === active}
              data-passed={index < active}
              aria-pressed={index === active}
              onClick={() => {
                setActive(index);
                setPlaying(false);
              }}
            >
              <span className="process-diagram__index">{String(index + 1).padStart(2, '0')}</span>
              <span>{step.label}</span>
            </button>
          </li>
        ))}
      </ol>

      <div className="process-diagram__explanation" aria-live="polite">
        <div>
          <span>Owns</span>
          <strong>{current.owns}</strong>
        </div>
        <div>
          <span>Hands off</span>
          <strong>{current.handoff}</strong>
        </div>
      </div>

      {loop && <figcaption>{loop}</figcaption>}
    </figure>
  );
}
