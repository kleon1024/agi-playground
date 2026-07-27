/**
 * Why continuous batching is a scheduling change, not "bigger batches."
 *
 * Static batching fixes a batch at admission time and runs every slot in
 * lock-step until the slowest sequence in that batch finishes — a slot whose
 * sequence hit EOS after two tokens still sits reserved, doing nothing, for
 * as long as the batch's longest sequence keeps going. Continuous (aka
 * iteration-level) batching makes the admit/evict decision every forward
 * pass instead of every batch: the moment a slot frees, the next waiting
 * request takes it, one iteration later. Same GPU, same slot count — the
 * only thing that changed is how often the scheduler is allowed to say yes.
 */
import React, { useEffect, useMemo, useState } from 'react';

const SLOTS = 6;
const TICK_MS = 480;
const ITER_CAP = 40;

interface Req {
  id: number;
  arrive: number;
  len: number;
}

// Fixed, deterministic arrival stream: six requests land together at t=0
// (enough to fill every slot), the rest trickle in afterward.
const REQUESTS: Req[] = [
  { id: 1, arrive: 0, len: 3 },
  { id: 2, arrive: 0, len: 6 },
  { id: 3, arrive: 0, len: 2 },
  { id: 4, arrive: 0, len: 8 },
  { id: 5, arrive: 0, len: 4 },
  { id: 6, arrive: 0, len: 5 },
  { id: 7, arrive: 2, len: 3 },
  { id: 8, arrive: 3, len: 4 },
  { id: 9, arrive: 5, len: 2 },
  { id: 10, arrive: 7, len: 6 },
];

interface SlotSnap {
  id: number;
  remaining: number;
}

interface Frame {
  slots: (SlotSnap | null)[];
  util: number;
  completed: number;
}

type Mode = 'static' | 'continuous';

/** Runs one scheduler for `iterations` forward passes and records every slot's state. */
function simulate(mode: Mode, iterations: number): Frame[] {
  const queue = [...REQUESTS].sort((a, b) => a.arrive - b.arrive || a.id - b.id);
  let qi = 0;
  const arrived: Req[] = [];
  const slotArr: (SlotSnap | null)[] = new Array(SLOTS).fill(null);
  const frames: Frame[] = [];
  const completed = new Set<number>();

  const admitOne = (slotIndex: number) => {
    const next = arrived.shift();
    if (next) slotArr[slotIndex] = { id: next.id, remaining: next.len };
  };

  for (let t = 0; t < iterations; t++) {
    while (qi < queue.length && queue[qi].arrive <= t) {
      arrived.push(queue[qi]);
      qi++;
    }

    if (mode === 'continuous') {
      // Iteration-level: any empty slot gets refilled right now.
      for (let s = 0; s < SLOTS; s++) {
        if (slotArr[s] === null) admitOne(s);
      }
    } else {
      // Batch-level: only refill once every slot in the batch has retired.
      const everFilled = slotArr.some((s) => s !== null);
      const allDone = slotArr.every((s) => s === null || s.remaining <= 0);
      if (!everFilled || allDone) {
        for (let s = 0; s < SLOTS; s++) slotArr[s] = null;
        for (let s = 0; s < SLOTS; s++) admitOne(s);
      }
    }

    const snapshot = slotArr.map((s) => (s ? { ...s } : null));
    const running = snapshot.filter((s) => s && s.remaining > 0).length;
    for (let s = 0; s < SLOTS; s++) {
      const cur = slotArr[s];
      if (cur && cur.remaining > 0) {
        cur.remaining -= 1;
        if (cur.remaining <= 0) completed.add(cur.id);
        // Continuous frees the slot the instant it's done; static leaves the
        // finished sequence sitting there (remaining=0) as a held, idle slot.
        if (mode === 'continuous' && cur.remaining <= 0) slotArr[s] = null;
      }
    }
    frames.push({
      slots: snapshot,
      util: (running / SLOTS) * 100,
      completed: completed.size,
    });
  }
  return frames;
}

function trimLength(a: Frame[], b: Frame[]): number {
  let last = 0;
  for (let i = 0; i < a.length; i++) {
    if (a[i].util > 0 || b[i].util > 0) last = i;
  }
  return last + 1;
}

function Panel({
  title,
  frames,
  currentT,
}: {
  title: string;
  frames: Frame[];
  currentT: number;
}): React.ReactElement {
  let sum = 0;
  for (let i = 0; i <= currentT; i++) sum += frames[i].util;
  const avg = sum / (currentT + 1);

  return (
    <div style={{ flex: 1, minWidth: 280 }}>
      <div style={{ fontSize: 'var(--type-sm)', fontWeight: 600, marginBottom: '0.4rem' }}>{title}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3, overflowX: 'auto' }}>
        {Array.from({ length: SLOTS }).map((_, slotIdx) => (
          <div key={slotIdx} style={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <span style={{ width: 38, flexShrink: 0, fontSize: 'var(--type-xs)', opacity: 0.6 }}>
              slot {slotIdx + 1}
            </span>
            {frames.map((f, t) => {
              const cell = f.slots[slotIdx];
              const running = !!cell && cell.remaining > 0;
              const idle = !!cell && !running;
              const revealed = t <= currentT;
              return (
                <div
                  key={t}
                  title={cell ? `req #${cell.id}${running ? '' : ' — finished, slot still held'}` : 'empty'}
                  style={{
                    width: 18,
                    height: 20,
                    flexShrink: 0,
                    borderRadius: 3,
                    background: running
                      ? 'var(--brand-chart-positive-fill)'
                      : idle
                        ? 'var(--brand-chart-warning-fill)'
                        : 'var(--ifm-color-emphasis-200)',
                    outline: t === currentT ? '2px solid var(--ifm-font-color-base)' : 'none',
                    outlineOffset: -1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 'var(--type-xs)',
                    color: 'var(--rehearse-ink)',
                    opacity: revealed ? 1 : 0.15,
                    transition: 'background 150ms, opacity 150ms',
                  }}
                >
                  {cell && revealed ? cell.id : ''}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div style={{ fontSize: 'var(--type-sm)', marginTop: '0.5rem' }}>
        completed <strong>{frames[currentT].completed}/{REQUESTS.length}</strong> · GPU utilization now{' '}
        <strong>{frames[currentT].util.toFixed(0)}%</strong> · average so far{' '}
        <strong>{avg.toFixed(0)}%</strong>
      </div>
    </div>
  );
}

export default function ContinuousBatching(): React.ReactElement {
  const { continuous, staticF, steps } = useMemo(() => {
    const c = simulate('continuous', ITER_CAP);
    const s = simulate('static', ITER_CAP);
    const n = trimLength(c, s);
    return { continuous: c.slice(0, n), staticF: s.slice(0, n), steps: n };
  }, []);

  const [currentT, setCurrentT] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setCurrentT((t) => (t + 1) % steps);
    }, TICK_MS);
    return () => clearInterval(id);
  }, [playing, steps]);

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.9rem' }}>
        <button
          onClick={() => setPlaying((p) => !p)}
          style={{ padding: '0.25rem 0.7rem', borderRadius: 6, cursor: 'pointer' }}
        >
          {playing ? 'Pause' : 'Play'}
        </button>
        <span style={{ fontSize: 'var(--type-sm)', opacity: 0.7 }}>
          iteration {currentT + 1} / {steps}
        </span>
      </div>

      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <Panel title="static batching" frames={staticF} currentT={currentT} />
        <Panel title="continuous batching" frames={continuous} currentT={currentT} />
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.9rem' }}>
        Same six requests, same six slots, same GPU. In static batching (top),
        request 3 finishes after two iterations but its slot stays{' '}
        <span style={{ color: 'var(--brand-chart-warning)' }}>amber</span> — reserved and idle —
        until request 4, the slowest in that batch, finally finishes. In
        continuous batching (bottom) that slot goes{' '}
        <span style={{ color: 'var(--brand-chart-positive)' }}>green</span> again on the very next
        iteration, handed to whichever request is next in line. Continuous
        batching is not a bigger batch size — it is the scheduler deciding
        per forward pass instead of per batch, which is what turns idle,
        reserved capacity into throughput.
      </p>
    </div>
  );
}
