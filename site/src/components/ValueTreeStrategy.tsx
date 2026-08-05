/**
 * The weight IS the strategy: combination functions on the stage's item set.
 *
 * Stage 05's core makes three claims in prose: weights reorder the slate,
 * additive treats objectives as substitutes while multiplicative treats
 * them as requirements, and the click-shaped item collapses under a product.
 * This widget runs those claims live on the recorded item set (12 items,
 * seed 42 — the same set the combination-sweep run used), with the
 * satisfaction-vs-click weight and the combination function as the controls.
 * Only the ranking arithmetic is live; the item predictions are the run's.
 */
import React, { useMemo, useState } from 'react';

const ITEMS = [
  { id: 'item_0', click: 0.86, completion: 0.105, satisfaction: 0.105 },
  { id: 'item_1', click: 0.195, completion: 0.821, satisfaction: 0.803 },
  { id: 'item_2', click: 0.612, completion: 0.33, satisfaction: 0.448 },
  { id: 'item_3', click: 0.31, completion: 0.377, satisfaction: 0.477 },
  { id: 'item_4', click: 0.707, completion: 0.14, satisfaction: 0.18 },
  { id: 'item_5', click: 0.259, completion: 0.666, satisfaction: 0.777 },
  { id: 'item_6', click: 0.583, completion: 0.302, satisfaction: 0.582 },
  { id: 'item_7', click: 0.544, completion: 0.419, satisfaction: 0.354 },
  { id: 'item_8', click: 0.939, completion: 0.167, satisfaction: 0.069 },
  { id: 'item_9', click: 0.169, completion: 0.854, satisfaction: 0.781 },
  { id: 'item_10', click: 0.582, completion: 0.555, satisfaction: 0.488 },
  { id: 'item_11', click: 0.641, completion: 0.432, satisfaction: 0.493 },
];

export default function ValueTreeStrategy(): React.ReactElement {
  const [wSat, setWSat] = useState(0.5);
  const [mode, setMode] = useState<'additive' | 'multiplicative'>('additive');

  const weights = { click: 1 - wSat, completion: 0.0, satisfaction: wSat };
  const ranked = useMemo(() => {
    const scored = ITEMS.map((it) => {
      let value: number;
      if (mode === 'additive') {
        const total = weights.click * it.click + weights.satisfaction * it.satisfaction;
        value = total / (weights.click + weights.satisfaction);
      } else {
        value =
          Math.pow(it.click, weights.click) *
          Math.pow(it.satisfaction, weights.satisfaction);
      }
      return { id: it.id, value };
    });
    return scored.sort((a, b) => b.value - a.value);
  }, [wSat, mode]);

  const clickRank = ranked.findIndex((r) => r.id === 'item_0') + 1;

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0 }}>
        Satisfaction weight{' '}
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={wSat}
          aria-label="satisfaction weight"
          onChange={(e) => setWSat(Number(e.target.value))}
        />{' '}
        {wSat.toFixed(2)} (click weight {weights.click.toFixed(2)}) —{' '}
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as 'additive' | 'multiplicative')}
          aria-label="combination function"
        >
          <option value="additive">weighted sum</option>
          <option value="multiplicative">weighted product</option>
        </select>
      </p>
      <ol style={{ margin: '0.5rem 0' }}>
        {ranked.slice(0, 3).map((r) => (
          <li key={r.id}>
            {r.id} — score {r.value.toFixed(3)}
          </li>
        ))}
      </ol>
      <p style={{ margin: '0 0 0.25rem', color: 'var(--rehearse-copy-muted)' }}>
        Click-shaped item (item_0) rank: {clickRank}/12 under the{' '}
        {mode === 'additive' ? 'weighted sum' : 'weighted product'}.
      </p>
      <p style={{ margin: 0, color: 'var(--rehearse-copy-muted)' }}>
        A product punishes its near-zero satisfaction far harder than a sum —
        the click-shaped item collapses under multiplication.
      </p>
    </div>
  );
}
