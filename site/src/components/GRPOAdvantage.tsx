/**
 * Group-relative advantage — the one idea GRPO actually contributes.
 *
 * PPO needs a learned value model to know whether a reward was "good for this
 * prompt," because a critic is what turns a raw reward into an advantage.
 * GRPO's trick is to skip the critic entirely: sample a group of completions
 * for the same prompt, and let the group's own mean and standard deviation
 * supply the baseline. Advantage becomes Aᵢ = (rᵢ − mean(r)) / (std(r) + ε) —
 * pure arithmetic over the group, no second network, no separate training run.
 *
 * The misconception this kills is that GRPO is "PPO but simpler for free."
 * It is simpler, but the simplification has a real cost: if every completion
 * in a group gets the same reward — a prompt that is trivially easy or
 * hopelessly hard for the current policy, common with binary correctness
 * rewards — the standard deviation is zero, every advantage collapses to
 * zero, and that group contributes no learning signal at all. Set all the
 * sliders below to the same value to see it happen.
 */
import React, { useMemo, useState } from 'react';

const DEFAULT_REWARDS = [0.8, 0.3, 0.9, 0.1, 0.6, 0.4, 0.7, 0.2];
const EPS = 1e-8;

export default function GRPOAdvantage(): React.ReactElement {
  const [groupSize, setGroupSize] = useState(4);
  const [rewards, setRewards] = useState<number[]>(DEFAULT_REWARDS);
  const [collapseDemo, setCollapseDemo] = useState(false);
  const [sharedReward, setSharedReward] = useState(0.5);

  const active = collapseDemo
    ? Array(groupSize).fill(sharedReward)
    : rewards.slice(0, groupSize);

  const { mean, std, advantages } = useMemo(() => {
    const m = active.reduce((a, x) => a + x, 0) / active.length;
    const variance = active.reduce((a, x) => a + (x - m) ** 2, 0) / active.length;
    const s = Math.sqrt(variance);
    const adv = active.map((x) => (x - m) / (s + EPS));
    return { mean: m, std: s, advantages: adv };
  }, [active]);

  const maxAbs = Math.max(...advantages.map((a) => Math.abs(a)), 1e-9);
  const collapsed = std < 1e-6;

  function setReward(i: number, value: number) {
    setRewards((prev) => {
      const next = [...prev];
      next[i] = value;
      return next;
    });
  }

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div
        style={{
          display: 'flex',
          gap: '1.5rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: '1rem',
        }}
      >
        <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <span style={{ minWidth: '7.5rem' }}>
            group size G = <strong>{groupSize}</strong>
          </span>
          <input
            type="range"
            min={2}
            max={8}
            step={1}
            value={groupSize}
            onChange={(e) => setGroupSize(Number(e.target.value))}
            style={{ width: 150 }}
          />
        </label>
        <label style={{ cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={collapseDemo}
            onChange={(e) => setCollapseDemo(e.target.checked)}
          />{' '}
          make all rewards identical (collapse demo)
        </label>
        {collapseDemo && (
          <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
            <span>shared r = <strong>{sharedReward.toFixed(2)}</strong></span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={sharedReward}
              onChange={(e) => setSharedReward(Number(e.target.value))}
              style={{ width: 120 }}
            />
          </label>
        )}
      </div>

      <div style={{ display: 'grid', gap: '0.4rem', marginBottom: '1.1rem' }}>
        {active.map((r, i) => (
          <label
            key={i}
            style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', opacity: collapseDemo ? 0.5 : 1 }}
          >
            <span style={{ minWidth: '4.5rem', fontSize: '0.85rem' }}>
              r<sub>{i + 1}</sub> = <strong>{r.toFixed(2)}</strong>
            </span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={r}
              disabled={collapseDemo}
              onChange={(e) => setReward(i, Number(e.target.value))}
              style={{ width: 200 }}
            />
          </label>
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 170, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: '50%',
            borderTop: '1px solid var(--ifm-color-emphasis-400)',
          }}
        />
        {advantages.map((a, i) => {
          const h = collapsed ? 0 : Math.round((Math.abs(a) / maxAbs) * 78);
          return (
            <div key={i} style={{ flex: 1, textAlign: 'center', position: 'relative', height: '100%' }}>
              <div
                title={`r=${active[i].toFixed(2)} → A=${a.toFixed(2)}`}
                style={{
                  position: 'absolute',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '60%',
                  maxWidth: 34,
                  height: Math.max(h, 2),
                  top: a >= 0 ? `calc(50% - ${Math.max(h, 2)}px)` : '50%',
                  background: a >= 0 ? '#5eead4' : '#fca5a5',
                  borderRadius: 3,
                  transition: 'height 150ms, top 150ms, background 150ms',
                }}
              />
              <div style={{ position: 'absolute', bottom: -20, left: 0, right: 0, fontSize: '0.65rem', opacity: 0.65 }}>
                {a.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          display: 'flex',
          gap: '1.4rem',
          fontSize: '0.85rem',
          marginTop: '1.6rem',
          flexWrap: 'wrap',
        }}
      >
        <span>mean(r) <strong>{mean.toFixed(3)}</strong></span>
        <span>std(r) <strong>{std.toFixed(3)}</strong></span>
        <span>A<sub>i</sub> = (r<sub>i</sub> − mean) / (std + ε)</span>
      </div>
      <p style={{ color: collapsed ? '#fbbf24' : 'inherit', fontSize: '0.85rem', marginTop: '0.4rem' }}>
        {collapsed
          ? 'σ ≈ 0 — every advantage collapses to zero. This group teaches the model nothing, which is exactly what happens on prompts every sampled completion gets equally right or equally wrong.'
          : 'a real spread of advantages — the group has something to teach the policy'}
      </p>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.75rem' }}>
        There is no value model anywhere in this computation — the baseline
        that PPO would spend a second network learning is just mean(r) over
        the group sampled for this one prompt. That is the entire trick and
        the entire limitation: it only works because you can afford to sample
        several completions per prompt, and it produces no signal at all when
        the group fails to disagree with itself.
      </p>
    </div>
  );
}
