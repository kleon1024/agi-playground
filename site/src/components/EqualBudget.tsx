/**
 * The same four architectures, ranked three different ways.
 *
 * "RMSNorm beat LayerNorm" or "MoE beats dense" is not a fact until you say
 * what stayed fixed while everything else changed. Fixing total parameters,
 * total training FLOPs, and total wall-clock time are all defensible
 * choices, and they routinely rank the same variants in a different order: a
 * design that spends more compute per parameter (looping the same block)
 * looks best when parameters are held equal; a design that adds parameters
 * cheaply relative to compute (sparse expert routing) looks best when FLOPs
 * are held equal; whatever already has mature, optimized kernels — usually
 * the plain dense block — looks best when wall-clock is held equal. Nothing
 * about any model changes between the three views; only which resource the
 * comparison was normalized against does.
 *
 * The scores below are illustrative, not measured — no ladder in this
 * chapter has actually run one architecture against another yet (see the
 * README's evidence boundary). They exist only to make the reordering
 * itself visible, the way the README's prose describes it in words.
 */
import React, { useMemo, useState } from 'react';

type Budget = 'params' | 'flops' | 'wallclock';

interface BudgetDef {
  id: Budget;
  label: string;
  held: string;
}

const BUDGETS: BudgetDef[] = [
  { id: 'params', label: 'Equal parameters', held: 'same total parameter count' },
  { id: 'flops', label: 'Equal FLOPs', held: 'same total training compute' },
  { id: 'wallclock', label: 'Equal wall-clock', held: 'same measured runtime' },
];

interface Variant {
  name: string;
  scores: Record<Budget, number>;
}

// Illustrative only — see the docstring above and the README's section 1.
const VARIANTS: Variant[] = [
  { name: 'Dense baseline', scores: { params: 62, flops: 68, wallclock: 88 } },
  { name: 'Looped / recurrent-depth', scores: { params: 90, flops: 48, wallclock: 40 } },
  { name: 'Mixture-of-experts', scores: { params: 78, flops: 92, wallclock: 52 } },
  { name: 'Wide-and-shallow', scores: { params: 55, flops: 80, wallclock: 74 } },
];

export default function EqualBudget(): React.ReactElement {
  const [budget, setBudget] = useState<Budget>('params');

  const ranked = useMemo(
    () => [...VARIANTS].sort((a, b) => b.scores[budget] - a.scores[budget]),
    [budget],
  );
  const active = BUDGETS.find((b) => b.id === budget) as BudgetDef;

  return (
    <div className="learning-widget">
      <header className="lab-header">
        <div>
          <span className="lab-eyebrow">Change what is held equal</span>
          <strong>Which architecture wins depends on which budget you fix.</strong>
        </div>
        <output>#1: {ranked[0].name}</output>
      </header>

      <div
        role="group"
        aria-label="Budget definition"
        style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.1rem' }}
      >
        {BUDGETS.map((b) => {
          const pressed = b.id === budget;
          return (
            <button
              key={b.id}
              type="button"
              aria-pressed={pressed}
              onClick={() => setBudget(b.id)}
              style={{
                background: pressed ? 'var(--rehearse-action)' : 'var(--rehearse-warm-white)',
                color: pressed ? 'var(--rehearse-surface)' : 'var(--rehearse-ink)',
                borderColor: pressed ? 'var(--rehearse-action)' : 'var(--rehearse-ink)',
              }}
            >
              {b.label}
            </button>
          );
        })}
      </div>

      <p style={{ fontSize: 'var(--type-xs)', opacity: 0.75, marginBottom: '0.75rem' }}>
        Illustrative scores, not measured — holding {active.held}.
      </p>

      <div style={{ display: 'grid', gap: '0.6rem' }}>
        {ranked.map((variant, index) => (
          <div
            key={variant.name}
            style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.4rem 0.75rem' }}
          >
            <span style={{ display: 'flex', gap: '0.5rem', alignItems: 'baseline', minWidth: '11rem' }}>
              <span style={{ opacity: 0.55, fontVariantNumeric: 'tabular-nums' }}>{index + 1}.</span>
              <span>{variant.name}</span>
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1 1 8rem', minWidth: '8rem' }}>
              <div
                style={{
                  flex: 1,
                  height: 14,
                  background: 'var(--rehearse-paper)',
                  border: '1px solid var(--rehearse-rule)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${variant.scores[budget]}%`,
                    height: '100%',
                    background:
                      index === 0 ? 'var(--brand-chart-positive-fill)' : 'var(--brand-chart-action-fill)',
                    transition: 'width 240ms ease-out, background 240ms ease-out',
                  }}
                />
              </div>
              <strong style={{ width: '2.25rem', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                {variant.scores[budget]}
              </strong>
            </div>
          </div>
        ))}
      </div>

      <p>
        Switch the definition and the number-one spot changes hands, three
        times, without any variant's underlying quality changing. Looped
        depth and mixture-of-experts lead under equal parameters, because
        both spend compute a parameter count alone cannot see. Mixture-of-experts
        and wide-and-shallow lead under equal FLOPs, because both add
        parameters a FLOP count alone cannot see. The dense baseline leads
        under equal wall-clock, because its kernels are the most mature — not
        because its architecture is the best one here. That is the whole
        argument for stating a budget definition on every run record, not
        after the fact.
      </p>
    </div>
  );
}
