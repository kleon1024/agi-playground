/**
 * Two ways to read a molecule, drawn side by side.
 *
 * Mission 09's model is two representations of the same molecule: ten RDKit
 * descriptors into a convex logistic regression, or the SMILES string into
 * a 696,065-parameter character transformer. The toggle switches which path
 * the reader traces; every number is the recorded stage-01 run's own
 * (SR-MMP, 3 seeds per arm, one scaffold split).
 */
import React, { useState } from 'react';

const PATHS: Record<
  string,
  { label: string; summary: string; params: string; auc: string; spread: string; time: string }
> = {
  descriptor: {
    label: 'Descriptor path',
    summary: 'RDKit computes ten physicochemical numbers; a convex logistic regression maps them to a toxicity probability.',
    params: '~10 + intercept',
    auc: '0.8142',
    spread: '0.0010',
    time: '~2s/seed',
  },
  smiles: {
    label: 'SMILES path',
    summary: 'The molecule string is tokenized into characters; a 4-layer transformer learns which sequences predict toxicity.',
    params: '696,065',
    auc: '0.7312',
    spread: '0.0159',
    time: '~105s/seed',
  },
};

const PATH_STEPS: Record<string, string[]> = {
  descriptor: ['molecule', '10 RDKit numbers', 'logistic regression', 'p(toxic)'],
  smiles: ['molecule', 'SMILES string', 'character tokens', '4-layer transformer', 'p(toxic)'],
};

export default function RepresentationAnatomy(): React.ReactElement {
  const [path, setPath] = useState('descriptor');
  const p = PATHS[path];
  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Path</span>
        <select aria-label="Representation path" value={path} onChange={(e) => setPath(e.target.value)}>
          {Object.entries(PATHS).map(([key, v]) => (
            <option key={key} value={key}>
              {v.label}
            </option>
          ))}
        </select>
      </label>
      <ol
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.4rem',
          paddingLeft: '0',
          listStyle: 'none',
          margin: '1rem 0',
        }}
      >
        {PATH_STEPS[path].map((step, i) => (
          <li
            key={step}
            style={{
              border: '1px solid var(--rehearse-rule)',
              padding: '0.4rem 0.6rem',
              fontSize: 'var(--type-xs)',
              background: i === PATH_STEPS[path].length - 1 ? 'var(--rehearse-action-soft)' : 'var(--rehearse-paper)',
            }}
          >
            {step}
          </li>
        ))}
      </ol>
      <p style={{ margin: '0.5rem 0' }}>{p.summary}</p>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(8rem, 1fr))',
          gap: '0.7rem',
        }}
      >
        <span>Parameters<br /><strong>{p.params}</strong></span>
        <span>Mean ROC-AUC<br /><strong>{p.auc}</strong></span>
        <span>Seed spread<br /><strong>{p.spread}</strong></span>
        <span>Wall-clock<br /><strong>{p.time}</strong></span>
      </div>
      <p>
        Recorded stage-01 numbers on SR-MMP. The descriptor is a fixed,
        human-chosen summary — cheap and stable; the transformer is a learned
        representation — expressive and noisy. On this endpoint stability
        beats capacity, which is the bias/variance trade the mission&apos;s
        three-endpoint verdict sits on.
      </p>
    </div>
  );
}
