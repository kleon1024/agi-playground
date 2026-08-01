import React, { useState } from 'react';

const SCALES = {
  demo: {
    label: 'Demo scale (600 -> 60, k=10, seed=42)',
    cheapOverall: 0.6,
    cheapLongTail: 0.2,
    popOverall: 0.4,
    popLongTail: 0.0,
    note: "The cheap proxy's long-tail surface rate is never zero across all four demo seeds (0.111-0.200), because content_sim gives it real signal on cold items. Popularity-only's long-tail surface rate is 0.000 on every one of those seeds -- not luck, a structural blind spot: a cold item's popularity is noise by construction.",
  },
  funnel: {
    label: 'Funnel-realistic scale (2000 -> 150, k=20, seed=42)',
    cheapOverall: 0.15,
    cheapLongTail: 0.0,
    popOverall: 0.1,
    popLongTail: 0.0,
    note: "At this wider, more production-realistic cut ratio, both proxies hit 0.000 on long-tail surface. The cheap proxy's structural advantage is a capability, not a guarantee at every catalogue-size-to-keep ratio -- this is a real, unflattering data point from the same run, not cherry-picked away.",
  },
} as const;

type Scale = keyof typeof SCALES;

export default function PreRankSurfaceRate(): React.ReactElement {
  const [scale, setScale] = useState<Scale>('demo');
  const s = SCALES[scale];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={scale === 'demo'} onChange={() => setScale('demo')} /> Demo scale
      </label>{' '}
      <label>
        <input type="radio" checked={scale === 'funnel'} onChange={() => setScale('funnel')} /> Funnel-realistic scale
      </label>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>{s.label}</p>
      <p>cheap proxy surface rate: overall <strong>{s.cheapOverall.toFixed(3)}</strong>, long-tail <strong>{s.cheapLongTail.toFixed(3)}</strong></p>
      <p>popularity-only surface rate: overall <strong>{s.popOverall.toFixed(3)}</strong>, long-tail <strong>{s.popLongTail.toFixed(3)}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>{s.note}</p>
    </div>
  );
}
