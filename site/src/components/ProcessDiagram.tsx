/**
 * The shared grammar for every pipeline in the curriculum.
 *
 * A pipeline diagram has to answer two questions at once: who owns each stage,
 * and what crosses the boundary between them. Static boxes answer the first and
 * leave the second implicit, which is where the reader's model goes wrong — the
 * artifact is the contract, not the box. So the handoff is animated: an artifact
 * travels the connector, the connector is live only while it is carrying, and
 * the stage that receives it changes state on arrival.
 *
 * Motion here is causal, not decorative. It runs under manual control, stops on
 * interaction, and never starts when the reader has asked for reduced motion.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useAutoplayOnView, useFrameLoop } from './useMotionClock';

export interface ProcessStep {
  id: string;
  label: string;
  owns: string;
  handoff: string;
  /** Short name for the artifact crossing to the next stage. Defaults to `handoff`. */
  carries?: string;
}

interface ProcessDiagramProps {
  eyebrow: string;
  question: string;
  steps: ProcessStep[];
  loop?: string;
}

interface Point {
  x: number;
  y: number;
}

/** How long a stage holds the artifact before releasing it. */
const DWELL_MS = 700;
/** How long the artifact spends on the wire. */
const TRANSIT_MS = 1150;

const useLayout = typeof window === 'undefined' ? useEffect : React.useLayoutEffect;

export default function ProcessDiagram({
  eyebrow,
  question,
  steps,
  loop,
}: ProcessDiagramProps): React.ReactElement {
  const [active, setActive] = useState(0);
  const [transit, setTransit] = useState(0);
  const [centers, setCenters] = useState<Point[]>([]);
  const { ref: rootRef, playing, setPlaying } = useAutoplayOnView<HTMLElement>();

  const trackRef = useRef<HTMLOListElement>(null);
  const nodeRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const activeRef = useRef(0);
  const transitRef = useRef(0);
  const dwellRef = useRef(DWELL_MS);

  const current = steps[active];
  const nextStep = steps[active + 1];
  const flowing = transit > 0 && Boolean(nextStep);
  const artifact = current.carries ?? current.handoff;

  const goTo = useCallback((index: number) => {
    activeRef.current = index;
    transitRef.current = 0;
    dwellRef.current = DWELL_MS;
    setActive(index);
    setTransit(0);
  }, []);

  /* Where the artifact is. Measured rather than assumed, because the track is a
     row on a wide screen and a column on a narrow one, and the same
     interpolation has to carry the artifact in both directions. */
  const measure = useCallback(() => {
    const track = trackRef.current;
    if (!track) return;
    const base = track.getBoundingClientRect();
    setCenters(
      nodeRefs.current.slice(0, steps.length).map((node) => {
        if (!node) return { x: 0, y: 0 };
        const rect = node.getBoundingClientRect();
        return {
          x: rect.left - base.left + rect.width / 2,
          y: rect.top - base.top + rect.height / 2,
        };
      }),
    );
  }, [steps.length]);

  useLayout(() => {
    measure();
    if (typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(measure);
    if (trackRef.current) observer.observe(trackRef.current);
    return () => observer.disconnect();
  }, [measure]);

  /* The clock: hold, carry, arrive, repeat. */
  useFrameLoop(playing, (dt) => {
    if (dwellRef.current > 0) {
      dwellRef.current -= dt;
      return;
    }
    if (activeRef.current >= steps.length - 1) {
      setPlaying(false);
      return;
    }
    const next = transitRef.current + dt / TRANSIT_MS;
    if (next >= 1) {
      activeRef.current += 1;
      transitRef.current = 0;
      dwellRef.current = DWELL_MS;
      setActive(activeRef.current);
      setTransit(0);
      return;
    }
    transitRef.current = next;
    setTransit(next);
  });

  const packet = useMemo(() => {
    const from = centers[active];
    if (!from || (!from.x && !from.y)) return null;
    const to = centers[active + 1];
    if (!flowing || !to) return from;
    return {
      x: from.x + (to.x - from.x) * transit,
      y: from.y + (to.y - from.y) * transit,
    };
  }, [active, centers, flowing, transit]);

  const stepStyle = useMemo(
    () => ({ '--process-step-count': steps.length }) as React.CSSProperties,
    [steps.length],
  );

  const atEnd = active === steps.length - 1 && !flowing;

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
          onClick={() => {
            if (atEnd && !playing) {
              goTo(0);
              setPlaying(true);
              return;
            }
            setPlaying((value) => !value);
          }}
          aria-label={playing ? 'Pause the handoff animation' : 'Play the handoff animation'}
        >
          {playing ? 'Pause' : atEnd ? 'Replay' : 'Play'}
        </button>
      </header>

      <ol ref={trackRef} className="process-diagram__track" aria-label={question}>
        {steps.map((step, index) => (
          <li
            key={step.id}
            className="process-diagram__step"
            data-flowing={flowing && index === active}
          >
            <button
              type="button"
              ref={(node) => {
                nodeRefs.current[index] = node;
              }}
              className="process-diagram__node"
              data-active={index === active}
              data-passed={index < active}
              aria-pressed={index === active}
              onClick={() => {
                setPlaying(false);
                goTo(index);
              }}
            >
              <span className="process-diagram__index">{String(index + 1).padStart(2, '0')}</span>
              <span>{step.label}</span>
            </button>
          </li>
        ))}
        {packet && (
          <span
            className="process-diagram__packet"
            data-flowing={flowing}
            aria-hidden="true"
            style={{ transform: `translate(${packet.x}px, ${packet.y}px)` }}
          />
        )}
      </ol>

      <div className="process-diagram__conduit" data-flowing={flowing}>
        <span className="process-diagram__conduit-label">
          {flowing ? 'In transit' : 'Held by'}
        </span>
        <span className="process-diagram__conduit-artifact">
          {flowing ? artifact : current.label}
        </span>
        <span className="process-diagram__conduit-target">
          {flowing ? `to ${nextStep.label}` : atEnd ? 'end of the chain' : 'not yet released'}
        </span>
        <span className="process-diagram__conduit-bar">
          <i style={{ transform: `scaleX(${flowing ? transit : 0})` }} />
        </span>
      </div>

      <div className="process-diagram__explanation" aria-live="polite">
        <div>
          <span>{current.label} owns</span>
          <strong>{current.owns}</strong>
        </div>
        <div>
          <span>{nextStep ? `Hands off to ${nextStep.label}` : 'Hands off'}</span>
          <strong>{current.handoff}</strong>
        </div>
      </div>

      {loop && <figcaption>{loop}</figcaption>}
    </figure>
  );
}
