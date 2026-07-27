/**
 * Why a perfect ranker cannot rank an item recall never retrieved.
 *
 * Each retrieval queue below is given the same job — surface a fixed set of
 * "target" items a user should see — but each was built to find a different
 * quarter of that set: one by semantic similarity, one by an exact keyword,
 * one by nearest neighbour of something the user just engaged with, one by
 * freshness. Uncheck a queue and its quarter of the target set falls out of
 * the union. The other queues recover a little of it by incidental overlap —
 * that is what "not by design" looks like — but never all of it. Nothing a
 * downstream ranker does can bring back a target the union never contained.
 *
 * All numbers here come from a small deterministic synthetic generator
 * (mulberry32, seeded), not from any measured run — they are illustrative,
 * and are labeled that way throughout. The business queue is included as a
 * toggle because a real system runs it in parallel with the rest, but it is
 * not assigned any of the personalized targets below: it is a policy queue,
 * not a statistical one, so toggling it never moves the coverage number.
 */
import React, { useMemo, useState } from 'react';

type QueueKey = 'two_tower' | 'lexical' | 'item_to_item' | 'freshness' | 'business';

const PERSONALIZED_QUEUES: QueueKey[] = ['two_tower', 'lexical', 'item_to_item', 'freshness'];

const QUEUE_LABELS: Record<QueueKey, string> = {
  two_tower: 'Two-tower (semantic)',
  lexical: 'Lexical (keyword)',
  item_to_item: 'Item-to-item',
  freshness: 'Freshness',
  business: 'Business (editorial)',
};

const TARGETS_PER_QUEUE = 25;
const OVERLAP_CHANCE = 0.12; // chance another queue incidentally also reaches a target

function mulberry32(seed: number): () => number {
  let state = seed;
  return () => {
    state |= 0;
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

interface Target {
  primary: QueueKey;
  secondary: QueueKey[];
}

// Built once, with a fixed seed, so the demo is stable across renders and
// across reloads -- the same "catalogue" every time this file is loaded.
const TARGETS: Target[] = (() => {
  const rand = mulberry32(20260726);
  const targets: Target[] = [];
  for (const primary of PERSONALIZED_QUEUES) {
    for (let i = 0; i < TARGETS_PER_QUEUE; i++) {
      const secondary = PERSONALIZED_QUEUES.filter((q) => q !== primary && rand() < OVERLAP_CHANCE);
      targets.push({ primary, secondary });
    }
  }
  return targets;
})();

function countFound(targets: Target[], enabled: Record<QueueKey, boolean>): number {
  let found = 0;
  for (const target of targets) {
    if (enabled[target.primary] || target.secondary.some((q) => enabled[q])) {
      found += 1;
    }
  }
  return found;
}

export default function RecallQueues(): React.ReactElement {
  const [enabled, setEnabled] = useState<Record<QueueKey, boolean>>({
    two_tower: true,
    lexical: true,
    item_to_item: true,
    freshness: true,
    business: true,
  });

  const toggle = (key: QueueKey) => setEnabled((prev) => ({ ...prev, [key]: !prev[key] }));

  const perQueue = useMemo(
    () =>
      PERSONALIZED_QUEUES.map((key) => {
        const owned = TARGETS.filter((t) => t.primary === key);
        const found = countFound(owned, enabled);
        return { key, owned: owned.length, found };
      }),
    [enabled]
  );

  const totalTargets = TARGETS.length;
  const totalFound = useMemo(() => countFound(TARGETS, enabled), [enabled]);
  const coveragePct = (totalFound / totalTargets) * 100;

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0, marginBottom: '0.9rem' }}>
        Before toggling anything: predict what happens to total coverage if you
        uncheck <strong>Lexical</strong>. Then check it.
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem 1.1rem', marginBottom: '1rem' }}>
        {(Object.keys(QUEUE_LABELS) as QueueKey[]).map((key) => (
          <label
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '2.75rem',
              cursor: 'pointer',
            }}
          >
            <input type="checkbox" checked={enabled[key]} onChange={() => toggle(key)} />
            <span>
              {QUEUE_LABELS[key]}
              {key === 'business' && (
                <span style={{ opacity: 0.65, fontSize: 'var(--type-xs)' }}> (no personalized target below)</span>
              )}
            </span>
          </label>
        ))}
      </div>

      <div style={{ display: 'grid', gap: '0.5rem', marginBottom: '1rem' }}>
        {perQueue.map(({ key, owned, found }) => {
          const pct = (found / owned) * 100;
          const isOff = !enabled[key];
          return (
            <div key={key} style={{ display: 'grid', gridTemplateColumns: 'minmax(8rem, 0.9fr) 1fr 3.5rem', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: 'var(--type-sm)', opacity: isOff ? 0.6 : 1 }}>
                {QUEUE_LABELS[key]}
                {isOff ? ' (off)' : ''}
              </span>
              <div
                style={{
                  height: '0.85rem',
                  border: '1px solid var(--rehearse-rule)',
                  background: 'var(--rehearse-paper)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: '100%',
                    background: isOff ? 'var(--brand-chart-danger-fill)' : 'var(--brand-chart-positive-fill)',
                    transition: 'width 220ms cubic-bezier(0.16, 1, 0.3, 1), background-color 220ms',
                  }}
                />
              </div>
              <span style={{ fontSize: 'var(--type-xs)', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {found}/{owned}
              </span>
            </div>
          );
        })}
      </div>

      <div
        style={{
          display: 'flex',
          gap: '1.2rem',
          flexWrap: 'wrap',
          alignItems: 'baseline',
          fontSize: 'var(--type-sm)',
          paddingTop: '0.6rem',
          borderTop: '1px solid var(--rehearse-rule)',
        }}
      >
        <span>
          union coverage of target set:{' '}
          <strong style={{ color: coveragePct < 100 ? 'var(--brand-chart-danger)' : 'inherit' }}>
            {totalFound}/{totalTargets} ({coveragePct.toFixed(0)}%)
          </strong>
        </span>
        <span style={{ opacity: 0.75 }}>illustrative, synthetic — not a measured run</span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.9rem' }}>
        Each row's own quarter of the target set collapses toward zero the
        moment its queue is unchecked, and the small amount that survives is
        incidental overlap from the remaining queues, not coverage by design.
        A downstream ranker sees only the union at the bottom — whatever
        recall never put there, ranking can never recover.
      </p>
    </div>
  );
}
