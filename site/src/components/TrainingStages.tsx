/**
 * Why "hundreds of billions of tokens" is a pretraining-scale number and a
 * rounding error at the same time, depending what it's compared against.
 *
 * The chapter's argument (section 1) is that mid-training is enormous next to
 * SFT's millions of tokens. That comparison is easy to state and easy to
 * misread as "so mid-training is basically pretraining." It isn't, quite:
 * inside a full pipeline, mid-training's own token budget is still a small
 * slice of general pretraining's. Both things are true because "large" only
 * means something relative to what it's being measured against.
 *
 * Each programme below is drawn only from its own published stage counts —
 * nothing here is invented or interpolated. AgentFounder-30B's report gives
 * two mid-training stages and no pretraining total for its base model, so its
 * view shows only what was published. GLM-5's report gives both, so its view
 * makes the ratio in section 3 checkable directly: sum the mid-training bars,
 * divide by the pretraining bar.
 *
 * Bars are scaled within one programme's own largest stage, never across
 * programmes — the comparison this widget teaches is "how does one pipeline
 * divide its own budget," not "whose numbers are bigger."
 */
import React, { useMemo, useState } from 'react';

interface Stage {
  label: string;
  tokens: number;
  pretraining?: boolean;
}

interface Programme {
  stages: Stage[];
  source: string;
  note?: string;
}

const PROGRAMMES: Record<string, Programme> = {
  'GLM-5': {
    stages: [
      { label: 'general + code pretraining', tokens: 28.5e12, pretraining: true },
      { label: 'mid-training @ 32K context', tokens: 1e12 },
      { label: 'mid-training @ 128K context', tokens: 500e9 },
      { label: 'mid-training @ 200K context', tokens: 50e9 },
    ],
    source: 'Kili Technology, "Data Story: GLM Model Family" (2026)',
  },
  'Agentic CPT (AgentFounder-30B)': {
    stages: [
      { label: 'mid-training @ 32K context', tokens: 200e9 },
      { label: 'mid-training @ 128K context', tokens: 100e9 },
    ],
    source: 'Su et al., "Agentic Continual Pre-training," arXiv:2509.13310 (2025)',
    note:
      'No published pretraining total for this checkpoint’s base model — ' +
      'bars show the two mid-training stages only.',
  },
};

function fmtTokens(n: number): string {
  const units: [number, string][] = [
    [1e12, 'T'],
    [1e9, 'B'],
    [1e6, 'M'],
  ];
  for (const [scale, suffix] of units) {
    if (n >= scale) {
      const rounded = Math.round((n / scale) * 100) / 100;
      return `${rounded}${suffix}`;
    }
  }
  return `${n}`;
}

export default function TrainingStages(): React.ReactElement {
  const [programmeKey, setProgrammeKey] = useState<keyof typeof PROGRAMMES>('GLM-5');
  const programme = PROGRAMMES[programmeKey];

  const { max, total, midShare } = useMemo(() => {
    const stageMax = Math.max(...programme.stages.map((s) => s.tokens));
    const totalTokens = programme.stages.reduce((sum, s) => sum + s.tokens, 0);
    const preTokens = programme.stages
      .filter((s) => s.pretraining)
      .reduce((sum, s) => sum + s.tokens, 0);
    const midTokens = totalTokens - preTokens;
    return {
      max: stageMax,
      total: totalTokens,
      midShare: preTokens > 0 ? midTokens / preTokens : null,
    };
  }, [programme]);

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        {Object.keys(PROGRAMMES).map((key) => {
          const active = key === programmeKey;
          return (
            <button
              key={key}
              type="button"
              aria-pressed={active}
              onClick={() => setProgrammeKey(key as keyof typeof PROGRAMMES)}
              style={{
                borderColor: active ? 'var(--rehearse-action)' : undefined,
                background: active ? 'var(--rehearse-action-soft)' : undefined,
                color: active ? 'var(--rehearse-action-strong)' : undefined,
              }}
            >
              {key}
            </button>
          );
        })}
      </div>

      <div style={{ display: 'grid', gap: '0.55rem' }}>
        {programme.stages.map((stage) => {
          const pct = Math.max((stage.tokens / max) * 100, 1);
          return (
            <div
              key={stage.label}
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(9rem, 12rem) 1fr auto',
                gap: '0.6rem',
                alignItems: 'center',
              }}
            >
              <span style={{ fontSize: 'var(--type-sm)' }}>{stage.label}</span>
              <div
                style={{
                  height: 20,
                  background: 'var(--ifm-color-emphasis-200)',
                  borderRadius: 4,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: '100%',
                    background: stage.pretraining
                      ? 'var(--brand-chart-action-fill)'
                      : 'var(--brand-chart-positive-fill)',
                    transition: 'width 250ms ease-out',
                  }}
                />
              </div>
              <strong style={{ fontSize: 'var(--type-sm)', fontVariantNumeric: 'tabular-nums' }}>
                {fmtTokens(stage.tokens)}
              </strong>
            </div>
          );
        })}
      </div>

      <div
        style={{
          display: 'flex',
          gap: '1.2rem',
          flexWrap: 'wrap',
          fontSize: 'var(--type-sm)',
          marginTop: '0.8rem',
        }}
      >
        <span>
          total shown <strong>{fmtTokens(total)}</strong>
        </span>
        {midShare !== null && (
          <span>
            mid-training / pretraining <strong>{(midShare * 100).toFixed(1)}%</strong>
          </span>
        )}
      </div>

      {programme.note && (
        <p style={{ fontSize: 'var(--type-xs)', opacity: 0.75, marginTop: '0.6rem' }}>
          {programme.note}
        </p>
      )}

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.7rem' }}>
        Source: {programme.source}. Every bar is scaled to the largest stage in
        the selected programme, not against the other programme — the point is
        how one pipeline divides its own token budget, not whose total is
        bigger.
      </p>
    </div>
  );
}
