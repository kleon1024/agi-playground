/**
 * Rotary position encoding, on the repo's own head geometry.
 *
 * RoPE rotates a query by m * theta^(-2i/d) radians per dimension and a key
 * by the same rule at position n, so the score depends only on delta = m - n
 * (translational invariance — measured exactly in the run) and the rotation
 * speed per dimension sets how fast the score changes with distance.
 * rope_theta is the long-context knob: it stretches the wavelength of every
 * dimension except dim 0, whose frequency is theta-independent.
 *
 * The score curve uses the exact fixed (q, k) pair and rotation arithmetic
 * from the recorded run (foundations/00-attention/rope, d_head 64); only the
 * theta is live. Wavelengths are computed from the config formula.
 */
import React, { useMemo, useState } from 'react';

const D_HEAD = 64;

const Q = [0.114979,0.132477,0.006414,0.000173,0.036911,0.041096,-0.08382,0.015447,-0.079715,-0.134268,0.280427,-0.064638,-0.334547,-0.193036,0.143353,-0.046638,0.011623,0.117793,-0.338999,0.303089,-0.109627,0.092595,0.165602,-0.128046,0.191501,0.058205,-0.146611,0.058401,-0.04268,0.083901,0.016828,-0.067043,0.007897,0.126686,-0.00529,0.051129,-0.190615,0.024521,-0.079776,0.117295,0.049518,0.100567,0.0583,-0.023156,0.037021,-0.027936,0.039959,0.092062,0.062438,0.012507,-0.059973,0.081023,0.157735,0.085596,0.084529,0.328081,-0.103879,0.054107,-0.019568,-0.049941,0.082296,-0.055184,0.032659,-0.150774];
const K = [-0.271572,0.112076,-0.103201,0.176509,0.142519,0.075377,-0.044391,-0.007801,-0.013921,-0.100344,-0.064001,0.00646,0.28994,0.067223,0.073356,-0.021556,-0.086902,-0.024162,-0.034405,-0.256939,0.133719,0.029223,-0.027498,0.021991,-0.162435,0.123095,-0.037155,-0.246869,-0.109008,0.029572,-0.042221,-0.13616,-0.084004,-0.041197,0.035434,0.227288,0.019072,-0.062392,-0.161684,0.090001,-0.054477,0.015462,-0.154248,0.072364,0.013806,-0.055888,-0.157989,0.286956,0.150405,0.191333,-0.132078,0.141206,-0.114396,0.194941,-0.259499,-0.04992,-0.121094,0.008875,-0.093548,-0.024594,-0.067485,0.069968,0.0379,0.085045];

const THETAS = [1000, 10000, 100000, 500000, 1000000];

function scoreAt(q: number[], k: number[], delta: number, theta: number): number {
  let total = 0;
  for (let i = 0; i < D_HEAD; i += 2) {
    const freq = Math.pow(theta, -2 * (i / 2) / D_HEAD);
    const aq = delta * freq;
    const ak = 0 * freq;
    const q0 = q[i];
    const q1 = q[i + 1];
    const k0 = k[i];
    const k1 = k[i + 1];
    const rq0 = q0 * Math.cos(aq) - q1 * Math.sin(aq);
    const rq1 = q0 * Math.sin(aq) + q1 * Math.cos(aq);
    const rk0 = k0 * Math.cos(ak) - k1 * Math.sin(ak);
    const rk1 = k0 * Math.sin(ak) + k1 * Math.cos(ak);
    total += rq0 * rk0 + rq1 * rk1;
  }
  return total;
}

export default function RoPEDecay(): React.ReactElement {
  const [theta, setTheta] = useState(10000);
  const curve = useMemo(
    () => Array.from({ length: 64 }, (_, d) => scoreAt(Q, K, d + 1, theta)),
    [theta],
  );
  const maxAbs = Math.max(...curve.map((s) => Math.abs(s)), 1e-6);
  const wavelengths = useMemo(() => {
    const out: { dim: number; positions: number }[] = [];
    for (let dim = 0; dim < D_HEAD / 2; dim++) {
      const freq = Math.pow(theta, -2 * dim / D_HEAD);
      out.push({ dim, positions: (2 * Math.PI) / freq });
    }
    return out;
  }, [theta]);

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0 }}>
        rope_theta{' '}
        <select value={theta} onChange={(e) => setTheta(Number(e.target.value))} aria-label="rope theta">
          {THETAS.map((t) => (
            <option key={t} value={t}>
              {t >= 1000 ? `${t / 1000}k` : t}
            </option>
          ))}
        </select>{' '}
        — fixed (q, k) pair from the recorded run, d_head 64.
      </p>

      <p style={{ margin: '0 0 0.25rem', color: 'var(--rehearse-copy-muted)' }}>
        Score vs relative distance (delta 1..64)
      </p>
      <div
        role="img"
        aria-label="score vs relative distance under rotary encoding"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '1px', height: '5rem' }}
      >
        {curve.map((s, d) => (
          <div
            key={d}
            title={`delta ${d + 1}: ${s.toFixed(4)}`}
            style={{
              flex: 1,
              height: `${Math.max((Math.abs(s) / maxAbs) * 100, 2)}%`,
              background: s >= 0 ? 'var(--rehearse-action)' : 'var(--rehearse-caution)',
            }}
          />
        ))}
      </div>

      <p style={{ margin: '0.7rem 0 0.25rem', color: 'var(--rehearse-copy-muted)' }}>
        Positions per full rotation, per dimension (log scale)
      </p>
      <div
        role="img"
        aria-label="wavelength per dimension"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '1px', height: '4.5rem' }}
      >
        {wavelengths.map((w) => (
          <div
            key={w.dim}
            title={`dim ${w.dim}: ${w.positions.toFixed(0)} positions/cycle`}
            style={{
              flex: 1,
              height: `${Math.min(Math.log10(w.positions + 1) / 7, 1) * 100}%`,
              background: 'var(--rehearse-emphasis-soft)',
            }}
          />
        ))}
      </div>
      <p style={{ margin: '0.5rem 0 0', color: 'var(--rehearse-copy-muted)' }}>
        Translational invariance (measured): delta 3 scores identically at
        positions (5,2), (100,97), and (1000,997). Dim 0 rotates at one radian
        per position for every theta — the wavelength bars always start at 6.3.
      </p>
    </div>
  );
}
