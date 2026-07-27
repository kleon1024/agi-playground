/**
 * The DPO family as one plot, not three unrelated papers.
 *
 * DPO, IPO, and SimPO get taught as separate algorithms with separate names,
 * which hides how close together they actually sit: each is a loss function
 * over the same quantity — an implicit reward margin between a preferred and
 * a dispreferred completion — and they differ by what shape that loss takes,
 * not by what they are optimising for. DPO runs the margin through a
 * log-sigmoid (unbounded, pushes the margin toward +∞ forever). IPO replaces
 * that with a bounded quadratic that targets a finite margin instead of
 * infinity, which is precisely the fix for DPO's tendency to overfit preference
 * pairs. SimPO drops the reference model from the margin itself and shifts
 * the same log-sigmoid by a target-margin threshold γ. Same family, one knob
 * of difference each time.
 *
 * The second misconception this kills: DPO is not "RL without RL." It is the
 * closed-form solution to the KL-regularised reward-maximisation objective,
 * derived under a specific assumption — that preferences follow a
 * Bradley-Terry model and that the implicit reward is exactly β · log(π/π_ref).
 * That assumption is where DPO's limits come from: violate it (noisy labels,
 * non-transitive preferences, rewards that were never pairwise to begin with)
 * and the closed form is quietly solving the wrong problem, RL loop or not.
 */
import React, { useMemo, useState } from 'react';

const TEAL = '#5eead4';
const PINK = '#f0abfc';
const AMBER = '#fbbf24';

const X_MIN = -4;
const X_MAX = 4;
const Y_MAX = 6;
const W = 340;
const H = 210;
const PAD_L = 34;
const PAD_R = 10;
const PAD_T = 10;
const PAD_B = 24;
const PLOT_W = W - PAD_L - PAD_R;
const PLOT_H = H - PAD_T - PAD_B;

function sigmoid(z: number): number {
  return 1 / (1 + Math.exp(-z));
}

function safeLog(p: number): number {
  return Math.log(Math.max(p, 1e-6));
}

function xToPx(x: number): number {
  return PAD_L + ((x - X_MIN) / (X_MAX - X_MIN)) * PLOT_W;
}

function yToPx(y: number): number {
  const clipped = Math.min(Math.max(y, 0), Y_MAX);
  return PAD_T + (1 - clipped / Y_MAX) * PLOT_H;
}

function buildPath(fn: (x: number) => number): string {
  const steps = 80;
  const pts: string[] = [];
  for (let i = 0; i <= steps; i++) {
    const x = X_MIN + ((X_MAX - X_MIN) * i) / steps;
    pts.push(`${i === 0 ? 'M' : 'L'}${xToPx(x).toFixed(1)},${yToPx(fn(x)).toFixed(1)}`);
  }
  return pts.join(' ');
}

export default function DPOLossFamily(): React.ReactElement {
  const [beta, setBeta] = useState(1);
  const [gamma, setGamma] = useState(0.5);

  const dpo = (h: number) => -safeLog(sigmoid(beta * h));
  const ipo = (h: number) => (beta * h - 1) ** 2;
  const simpo = (h: number) => -safeLog(sigmoid(beta * h - gamma));

  const paths = useMemo(
    () => ({ dpo: buildPath(dpo), ipo: buildPath(ipo), simpo: buildPath(simpo) }),
    [beta, gamma],
  );

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
          <span style={{ minWidth: '4.5rem' }}>
            β = <strong>{beta.toFixed(1)}</strong>
          </span>
          <input
            type="range"
            min={0.1}
            max={5}
            step={0.1}
            value={beta}
            onChange={(e) => setBeta(Number(e.target.value))}
            style={{ width: 170 }}
          />
        </label>
        <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>
            SimPO γ = <strong>{gamma.toFixed(1)}</strong>
          </span>
          <input
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={gamma}
            onChange={(e) => setGamma(Number(e.target.value))}
            style={{ width: 170 }}
          />
        </label>
      </div>

      <svg width={W} height={H} style={{ maxWidth: '100%' }}>
        {/* axes */}
        <line x1={PAD_L} y1={PAD_T} x2={PAD_L} y2={H - PAD_B} stroke="var(--ifm-color-emphasis-400)" />
        <line x1={PAD_L} y1={H - PAD_B} x2={W - PAD_R} y2={H - PAD_B} stroke="var(--ifm-color-emphasis-400)" />
        <line
          x1={xToPx(0)}
          y1={PAD_T}
          x2={xToPx(0)}
          y2={H - PAD_B}
          stroke="var(--ifm-color-emphasis-300)"
          strokeDasharray="3,3"
        />
        <text x={PAD_L - 6} y={PAD_T + 4} fontSize={9} textAnchor="end" fill="var(--ifm-font-color-base)" opacity={0.6}>
          {Y_MAX}
        </text>
        <text x={PAD_L - 6} y={H - PAD_B} fontSize={9} textAnchor="end" fill="var(--ifm-font-color-base)" opacity={0.6}>
          0
        </text>
        <text x={xToPx(0)} y={H - PAD_B + 12} fontSize={9} textAnchor="middle" fill="var(--ifm-font-color-base)" opacity={0.6}>
          h=0
        </text>
        <text x={W - PAD_R} y={H - PAD_B + 12} fontSize={9} textAnchor="end" fill="var(--ifm-font-color-base)" opacity={0.6}>
          margin h →
        </text>

        <path d={paths.dpo} fill="none" stroke={TEAL} strokeWidth={2} />
        <path d={paths.ipo} fill="none" stroke={PINK} strokeWidth={2} />
        <path d={paths.simpo} fill="none" stroke={AMBER} strokeWidth={2} />
      </svg>

      <div style={{ display: 'grid', gap: '0.35rem', fontSize: '0.8rem', marginTop: '0.6rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ width: 10, height: 10, borderRadius: 5, background: TEAL, display: 'inline-block' }} />
          DPO: L(h) = −log σ(β·h)
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ width: 10, height: 10, borderRadius: 5, background: PINK, display: 'inline-block' }} />
          IPO: L(h) = (β·h − 1)²
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ width: 10, height: 10, borderRadius: 5, background: AMBER, display: 'inline-block' }} />
          SimPO: L(h) = −log σ(β·h − γ)
        </div>
      </div>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.9rem' }}>
        h is the implicit margin between the preferred and dispreferred
        completion — for DPO and IPO that is β times a log-probability ratio
        difference against a frozen reference model; SimPO computes the same
        kind of margin with no reference model at all, then subtracts its own
        target γ before the sigmoid. Raise β and all three curves sharpen,
        because β is the knob controlling how hard any of them punishes a
        small margin. Notice DPO's teal curve keeps falling forever as h
        grows — nothing stops it from pushing the margin to infinity, which is
        the overfitting behaviour IPO's bounded pink bowl is built to prevent.
        (IPO's actual paper parameterises its target margin as 1/(2β) in raw
        log-ratio space; it is plotted here on the same β-scaled axis as the
        other two so the three curves stay directly comparable.) None of this
        is "RL without RL" — it is RL's closed-form solution under the
        Bradley-Terry assumption, and everywhere that assumption breaks is
        exactly where DPO-family methods break too.
      </p>
    </div>
  );
}
