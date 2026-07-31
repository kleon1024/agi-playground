import React, { useState } from 'react';

type Outcome = 'FAIL' | 'PASS' | 'DID_NOT_RUN';
const OUTCOMES: Outcome[] = ['FAIL', 'PASS', 'DID_NOT_RUN'];

const CELL_NOTES: Record<string, string> = {
  'FAIL,PASS': 'admits the task -- the one cell that does',
  'PASS,PASS': "site/docs early-return case: f(base)=PASS always (the guard returns before checking anything), rejected here because the first half already fails",
  'FAIL,DID_NOT_RUN':
    'exit-code-5 case, before the fix: pytest.importorskip("torch") skipped collection, f(gold) was DID_NOT_RUN but got read as FAIL by collapsing to returncode==0',
};

export default function TestOutcomeTruth(): React.ReactElement {
  const [base, setBase] = useState<Outcome>('FAIL');
  const [gold, setGold] = useState<Outcome>('PASS');
  const admits = base === 'FAIL' && gold === 'PASS';
  const key = `${base},${gold}`;
  const note = CELL_NOTES[key];
  return (
    <div className="learning-widget">
      <label>
        f(base){' '}
        <select value={base} onChange={(e) => setBase(e.target.value as Outcome)}>
          {OUTCOMES.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </label>{' '}
      <label>
        f(gold){' '}
        <select value={gold} onChange={(e) => setGold(e.target.value as Outcome)}>
          {OUTCOMES.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </label>
      <p style={{ marginTop: '0.5rem' }}>
        <strong>{admits ? 'admits' : 'rejects'}</strong> the candidate
        {note ? ` -- ${note}` : ''}
      </p>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 'var(--type-sm)', marginTop: '0.5rem' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid var(--rehearse-rule)', padding: '0.4rem' }}>f(base) \ f(gold)</th>
            {OUTCOMES.map((g) => (
              <th key={g} style={{ border: '1px solid var(--rehearse-rule)', padding: '0.4rem' }}>{g}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {OUTCOMES.map((b) => (
            <tr key={b}>
              <th style={{ border: '1px solid var(--rehearse-rule)', padding: '0.4rem' }}>{b}</th>
              {OUTCOMES.map((g) => {
                const cellAdmits = b === 'FAIL' && g === 'PASS';
                const selected = b === base && g === gold;
                return (
                  <td
                    key={g}
                    style={{
                      border: selected ? '2px solid var(--brand-chart-positive)' : '1px solid var(--rehearse-rule)',
                      padding: '0.4rem',
                      background: cellAdmits ? 'var(--brand-chart-positive-fill)' : undefined,
                    }}
                  >
                    {CELL_NOTES[`${b},${g}`] ?? ''}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.6rem' }}>
        A candidate is admitted iff f(base)=FAIL and f(gold)=PASS. Both of this chapter's real
        historical rejections are the same failure: collapsing DID_NOT_RUN into FAIL or PASS.
      </p>
    </div>
  );
}
