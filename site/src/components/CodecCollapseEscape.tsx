import React, { useState } from 'react';

const HISTORY = [
  { step: 0, recon_loss: 0.349, vq_loss: 0.0113 },
  { step: 50, recon_loss: 0.3251, vq_loss: 0.0000138 },
  { step: 100, recon_loss: 0.3249, vq_loss: 0.0000055 },
  { step: 150, recon_loss: 0.2962, vq_loss: 4.1832 },
  { step: 200, recon_loss: 0.2473, vq_loss: 2.2475 },
  { step: 300, recon_loss: 0.1103, vq_loss: 1.1366 },
  { step: 400, recon_loss: 0.0407, vq_loss: 0.4154 },
  { step: 550, recon_loss: 0.0145, vq_loss: 0.0624 },
];

function phase(vqLoss: number): string {
  if (vqLoss < 0.001) return 'still at the silence floor';
  if (vqLoss > 1) return 'escaping -- codebook disagreement';
  return 're-converged, encoding real shape';
}

export default function CodecCollapseEscape(): React.ReactElement {
  const [idx, setIdx] = useState(0);
  const h = HISTORY[idx];
  return (
    <div className="learning-widget">
      <label>
        training step{' '}
        <input type="range" min={0} max={HISTORY.length - 1} step={1} value={idx} onChange={(e) => setIdx(Number(e.target.value))} />
        <strong> {h.step}</strong>
      </label>
      <p>recon_loss: <strong>{h.recon_loss.toFixed(4)}</strong></p>
      <p>vq_loss: <strong>{h.vq_loss.toFixed(4)}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>{phase(h.vq_loss)}</p>
    </div>
  );
}
