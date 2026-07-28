/**
 * Why a rule engine has to report an empty candidate set instead of just
 * returning one.
 *
 * The sixteen items below are the same synthetic candidate set stage 07's
 * `core/rule_engine.py` builds by hand: ten licensed only in the EU, all
 * ten also carrying a safety flag (a content category held back pending a
 * compliance review); six licensed only in the US, split evenly across
 * three creators, none flagged. Toggle a rule and the ladder below shows how
 * many candidates survive after each rung, in the fixed precedence order —
 * blocks, then a boost, then the cap — because a fired block is terminal
 * regardless of what a boost would have added, and a cap only means anything
 * once the keep order beneath it is fixed.
 *
 * Set the region to EU: the regional block alone leaves ten candidates, and
 * the safety block alone would remove ten of the sixteen — neither rule is
 * unreasonable by itself. Applied together against this request, they
 * remove all ten of what the region left, because in this catalogue every
 * EU-licensed item happens to be safety-flagged. That intersection, not a
 * single rule, is what empties the set — and the banner below reports it
 * with each rule's solo effect rather than returning nothing and moving on.
 *
 * All sixteen items and their attributes are the fixed synthetic set stage
 * 07 constructs by hand; nothing here is sampled, so this reproduces
 * identically to a run of `core/rule_engine.py --region EU`.
 */
import React, { useMemo, useState } from 'react';

type Region = 'US' | 'EU';
type CapSetting = 'off' | 2 | 1;

interface Candidate {
  id: string;
  creatorId: string;
  region: 'US' | 'EU';
  safetyFlag: boolean;
  editorial: boolean;
  score: number;
}

// Identical construction to core/rule_engine.py's build_items(): ten EU
// items (all safety-flagged), six US items (three creators, two each).
const CANDIDATES: Candidate[] = [
  ...['c1', 'c1', 'c2', 'c2', 'c3', 'c3', 'c4', 'c4', 'c5', 'c5'].map((creatorId, i) => ({
    id: `eu_${i}`,
    creatorId,
    region: 'EU' as const,
    safetyFlag: true,
    editorial: i === 0,
    score: 0.5 + 0.03 * i,
  })),
  ...['c1', 'c1', 'c2', 'c2', 'c3', 'c3'].map((creatorId, i) => ({
    id: `us_${i}`,
    creatorId,
    region: 'US' as const,
    safetyFlag: false,
    editorial: i === 0,
    score: 0.6 + 0.02 * i,
  })),
];

type Status = 'kept' | 'removed-region' | 'removed-safety' | 'capped';

interface Row {
  c: Candidate;
  status: Status;
  score: number;
  boosted: boolean;
}

function evaluate(
  region: Region,
  safetyOn: boolean,
  editorialOn: boolean,
  cap: CapSetting
): { rows: Row[]; afterRegion: number; afterSafety: number; afterCap: number } {
  const decided = new Map<string, Row>();

  // Rung 1: regional block. Always active -- every request is for some region.
  const survivedRegion: Candidate[] = [];
  for (const c of CANDIDATES) {
    if (c.region !== region) {
      decided.set(c.id, { c, status: 'removed-region', score: c.score, boosted: false });
    } else {
      survivedRegion.push(c);
    }
  }

  // Rung 2: safety block, toggleable -- this is the rule a policy
  // conversation might actually argue about disabling.
  const survivedSafety: Candidate[] = [];
  for (const c of survivedRegion) {
    if (safetyOn && c.safetyFlag) {
      decided.set(c.id, { c, status: 'removed-safety', score: c.score, boosted: false });
    } else {
      survivedSafety.push(c);
    }
  }

  // Rung 3: editorial boost -- annotates score, removes nothing.
  const boosted = survivedSafety.map((c) => ({
    c,
    score: editorialOn && c.editorial ? c.score + 0.08 : c.score,
    boosted: editorialOn && c.editorial,
  }));
  boosted.sort((a, b) => b.score - a.score);

  // Rung 4: per-creator cap -- order-dependent, runs last, on the boosted order.
  const keptPerCreator = new Map<string, number>();
  const finalKept: Row[] = [];
  for (const { c, score, boosted: wasBoosted } of boosted) {
    const already = keptPerCreator.get(c.creatorId) ?? 0;
    if (cap !== 'off' && already >= cap) {
      decided.set(c.id, { c, status: 'capped', score, boosted: wasBoosted });
    } else {
      keptPerCreator.set(c.creatorId, already + 1);
      const row: Row = { c, status: 'kept', score, boosted: wasBoosted };
      decided.set(c.id, row);
      finalKept.push(row);
    }
  }

  const rows = CANDIDATES.map((c) => decided.get(c.id)!);
  return {
    rows,
    afterRegion: survivedRegion.length,
    afterSafety: survivedSafety.length,
    afterCap: finalKept.length,
  };
}

const STATUS_LABEL: Record<Status, string> = {
  kept: 'kept',
  'removed-region': 'blocked: region',
  'removed-safety': 'blocked: safety',
  capped: 'capped',
};

export default function ConstraintLadder(): React.ReactElement {
  const [region, setRegion] = useState<Region>('US');
  const [safetyOn, setSafetyOn] = useState(true);
  const [editorialOn, setEditorialOn] = useState(true);
  const [cap, setCap] = useState<CapSetting>(2);

  const { rows, afterRegion, afterSafety, afterCap } = useMemo(
    () => evaluate(region, safetyOn, editorialOn, cap),
    [region, safetyOn, editorialOn, cap]
  );

  const total = CANDIDATES.length;
  const emptiedAtSafety = afterRegion > 0 && afterSafety === 0;

  const rungs = [
    { label: 'regional block', remaining: afterRegion, emptied: afterRegion === 0 },
    { label: 'safety block', remaining: afterSafety, emptied: emptiedAtSafety },
    { label: 'per-creator cap', remaining: afterCap, emptied: afterSafety > 0 && afterCap === 0 },
  ];

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '1.1rem', flexWrap: 'wrap', marginBottom: '0.9rem', alignItems: 'center' }}>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          region
          <select value={region} onChange={(e) => setRegion(e.target.value as Region)}>
            <option value="US">US</option>
            <option value="EU">EU</option>
          </select>
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input type="checkbox" checked={safetyOn} onChange={() => setSafetyOn((v) => !v)} />
          safety block
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input type="checkbox" checked={editorialOn} onChange={() => setEditorialOn((v) => !v)} />
          editorial boost
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          per-creator cap
          <select
            value={String(cap)}
            onChange={(e) => setCap(e.target.value === 'off' ? 'off' : (Number(e.target.value) as CapSetting))}
          >
            <option value="off">off</option>
            <option value="2">2</option>
            <option value="1">1</option>
          </select>
        </label>
      </div>

      <div style={{ display: 'grid', gap: '0.4rem', marginBottom: '1rem' }}>
        {rungs.map((rung, i) => (
          <div
            key={rung.label}
            style={{
              display: 'grid',
              gridTemplateColumns: '1.4rem minmax(7rem, 1fr) 5.5rem',
              alignItems: 'center',
              gap: '0.6rem',
              fontSize: 'var(--type-sm)',
            }}
          >
            <span style={{ opacity: 0.65 }}>{i + 1}</span>
            <span>{rung.label}</span>
            <span
              style={{
                textAlign: 'right',
                fontVariantNumeric: 'tabular-nums',
                color: rung.emptied ? 'var(--brand-chart-danger)' : 'inherit',
                fontWeight: rung.emptied ? 600 : 400,
              }}
            >
              {rung.remaining}/{total} left
            </span>
          </div>
        ))}
      </div>

      {emptiedAtSafety && (
        <p
          style={{
            fontSize: 'var(--type-sm)',
            padding: '0.6rem 0.8rem',
            border: '1px solid var(--brand-chart-danger)',
            color: 'var(--brand-chart-danger)',
            marginBottom: '1rem',
          }}
        >
          Region {region} and the safety block jointly emptied the candidate set. Alone, the region
          filter left {afterRegion}/{total} and the safety block would remove up to 10/{total} of the
          full set — neither is unreasonable by itself. Reported here, not returned as a silent empty
          slate.
        </p>
      )}

      <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: '0.3rem' }}>
        {rows.map((row) => (
          <li
            key={row.c.id}
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(4.5rem, 1fr) minmax(6rem, 1.4fr) 3.5rem',
              alignItems: 'center',
              gap: '0.6rem',
              fontSize: 'var(--type-xs)',
              opacity: row.status === 'kept' ? 1 : 0.55,
            }}
          >
            <span>
              {row.c.id} <span style={{ opacity: 0.6 }}>({row.c.creatorId})</span>
            </span>
            <span style={{ color: row.status === 'kept' ? 'inherit' : 'var(--brand-chart-danger)' }}>
              {STATUS_LABEL[row.status]}
              {row.boosted ? ' (+boost)' : ''}
            </span>
            <span style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
              {row.status === 'kept' ? row.score.toFixed(3) : '—'}
            </span>
          </li>
        ))}
      </ol>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.9rem' }}>
        Blocks are terminal and run first, so no boost can rescue a blocked item. Tighten the cap to 1
        and watch the second item from every two-item creator move to "capped" with its own line in
        the list, not just a smaller count. Every number here matches a run of
        `core/rule_engine.py`; nothing is illustrative.
      </p>
    </div>
  );
}
