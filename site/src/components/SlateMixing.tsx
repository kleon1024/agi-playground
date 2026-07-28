import React, { useMemo, useState } from 'react';

const ITEMS = [
  ['A', 'sports', 0.91], ['B', 'sports', 0.87], ['C', 'sports', 0.82],
  ['D', 'music', 0.79], ['E', 'cooking', 0.75], ['F', 'news', 0.71],
];
const WEIGHTS = [1, 0.631, 0.5, 0.431, 0.387];

export default function SlateMixing(): React.ReactElement {
  const [cap, setCap] = useState(2);
  const [adLoad, setAdLoad] = useState(1);
  const [beamWidth, setBeamWidth] = useState(2);
  const slate = useMemo(() => {
    const counts: Record<string, number> = {};
    const organic = ITEMS.filter((item) => {
      const category = item[1] as string;
      counts[category] = (counts[category] ?? 0) + 1;
      return counts[category] <= cap;
    }).slice(0, 5 - adLoad);
    const ads = Array.from({ length: adLoad }, (_, i) => [`Sponsored ${i + 1}`, 'ad', 0.72 - i * 0.06]);
    return [...organic, ...ads].sort((a, b) => (b[2] as number) - (a[2] as number)).slice(0, 5);
  }, [cap, adLoad]);
  const organicValue = slate.reduce((sum, row, index) => sum + ((row[1] === 'ad' ? 0 : row[2]) as number) * WEIGHTS[index], 0);
  const revenue = slate.filter((row) => row[1] === 'ad').reduce((sum, _row, index) => sum + 0.24 * WEIGHTS[index], 0);
  return <div className="learning-widget">
    <label>beam width <strong>{beamWidth}</strong><input type="range" min="1" max="6" value={beamWidth} onChange={(e) => setBeamWidth(Number(e.target.value))} aria-label="Beam width" /></label>
    <label>category cap <select value={cap} onChange={(e) => setCap(Number(e.target.value))}><option value="1">1</option><option value="2">2</option><option value="3">3</option></select></label>
    <label>ad load <select value={adLoad} onChange={(e) => setAdLoad(Number(e.target.value))}><option value="0">0</option><option value="1">1</option><option value="2">2</option></select></label>
    <ol>{slate.map((row, index) => <li key={String(row[0])}>{index + 1}. <strong>{row[0]}</strong> — {row[1]}, value {(row[2] as number).toFixed(2)}, slot weight {WEIGHTS[index].toFixed(3)}</li>)}</ol>
    <p>Illustrative slate. Beam width controls retained prefixes in the core algorithm; this small display exposes the resulting policy controls. Organic user value: {organicValue.toFixed(3)}. Expected ad revenue: ${revenue.toFixed(3)}. Raising ad load exposes the displacement trade.</p>
  </div>;
}
