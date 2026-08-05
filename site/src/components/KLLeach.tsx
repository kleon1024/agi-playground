/**
 * The GRPO KL leash: the k3 estimator, live on the probability drift.
 *
 * GRPO's update pays a KL toll against the frozen reference policy so it
 * stays close to where it started. The leash uses Schulman's k3 estimator —
 * kl = exp(-d) + d - 1 with d = new_logp - ref_logp — which is always
 * non-negative and asymmetric: reducing probability mass costs more than
 * increasing it, and the naive d goes negative (the sign-flipping gradient
 * k3 exists to remove). The slider moves new/ref; the numbers match the
 * run (the-kl-leash, beta 0.04).
 */
import React, { useMemo, useState } from 'react';

const BETA = 0.04;

export default function KLLeach(): React.ReactElement {
  const [ratio, setRatio] = useState(1.0);
  const { d, k3, naive, toll } = useMemo(() => {
    const dd = Math.log(ratio);
    const kk = Math.exp(-dd) + dd - 1;
    return { d: dd, k3: kk, naive: dd, toll: BETA * kk };
  }, [ratio]);

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0 }}>
        New probability / reference probability{' '}
        <input
          type="range"
          min={0.2}
          max={3}
          step={0.05}
          value={ratio}
          aria-label="new over reference probability"
          onChange={(e) => setRatio(Number(e.target.value))}
        />{' '}
        {ratio.toFixed(2)}
      </p>
      <p style={{ margin: '0.5rem 0' }}>
        d (log drift): <strong>{d.toFixed(3)}</strong> — naive d:{' '}
        <strong style={{ color: d < 0 ? 'var(--rehearse-caution)' : 'inherit' }}>
          {naive.toFixed(3)}
        </strong>{' '}
        (negative = sign-flipping gradient)
      </p>
      <p style={{ margin: '0.5rem 0' }}>
        k3 KL: <strong>{k3.toFixed(4)}</strong> (always {'>='} 0) — toll at beta{' '}
        {BETA}: <strong>{toll.toFixed(4)}</strong>
      </p>
      <p style={{ margin: 0, color: 'var(--rehearse-copy-muted)' }}>
        Reducing mass (new/ref &lt; 1) costs more than increasing it
        (new/ref &gt; 1): at half the probability the KL is 0.307, at double
        it is 0.193 — the asymmetry is the leash&apos;s design.
      </p>
    </div>
  );
}
