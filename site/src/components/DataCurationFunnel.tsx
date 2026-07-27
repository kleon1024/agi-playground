import React, { useMemo, useState } from 'react';

interface Stage {
  label: string;
  count: number;
  note: string;
}

export default function DataCurationFunnel(): React.ReactElement {
  const [languageKeep, setLanguageKeep] = useState(73);
  const [qualityKeep, setQualityKeep] = useState(70);
  const [dedupKeep, setDedupKeep] = useState(95);
  const input = 40000;

  const stages = useMemo<Stage[]>(() => {
    const language = Math.round(input * languageKeep / 100);
    const quality = Math.round(language * qualityKeep / 100);
    const dedup = Math.round(quality * dedupKeep / 100);
    return [
      { label: 'Raw crawl', count: input, note: 'The acquisition boundary' },
      { label: 'Language', count: language, note: `${100 - languageKeep}% rejected` },
      { label: 'Quality', count: quality, note: `${100 - qualityKeep}% of survivors rejected` },
      { label: 'Deduplicate', count: dedup, note: `${100 - dedupKeep}% of survivors rejected` },
    ];
  }, [languageKeep, qualityKeep, dedupKeep]);

  const final = stages[stages.length - 1].count;

  return (
    <div className="learning-widget funnel-lab">
      <header className="lab-header">
        <div>
          <span className="lab-eyebrow">Change one gate</span>
          <strong>Which filter actually controls the final corpus size?</strong>
        </div>
        <output>{final.toLocaleString()} kept · {(final / input * 100).toFixed(1)}%</output>
      </header>

      <div className="lab-controls lab-controls--three">
        <label>
          <span>Language keep <strong>{languageKeep}%</strong></span>
          <input type="range" min={40} max={100} value={languageKeep} onChange={(event) => setLanguageKeep(Number(event.target.value))} />
        </label>
        <label>
          <span>Quality keep <strong>{qualityKeep}%</strong></span>
          <input type="range" min={30} max={100} value={qualityKeep} onChange={(event) => setQualityKeep(Number(event.target.value))} />
        </label>
        <label>
          <span>Dedup keep <strong>{dedupKeep}%</strong></span>
          <input type="range" min={60} max={100} value={dedupKeep} onChange={(event) => setDedupKeep(Number(event.target.value))} />
        </label>
      </div>

      <div className="funnel-lab__stages">
        {stages.map((stage, index) => (
          <div className="funnel-lab__stage" key={stage.label}>
            <div className="funnel-lab__stage-label">
              <span>{stage.label}</span>
              <strong>{stage.count.toLocaleString()}</strong>
            </div>
            <div className="funnel-lab__track">
              <span style={{ transform: `scaleX(${stage.count / input})` }} />
            </div>
            <small>{stage.note}</small>
            {index < stages.length - 1 && <i aria-hidden="true">↓</i>}
          </div>
        ))}
      </div>

      <p>
        The gates multiply; they do not add. A strict upstream filter shrinks
        every downstream opportunity, so “keep more documents” is not a quality
        objective. Each rejection gate needs its own sampled false-positive audit.
      </p>
    </div>
  );
}
