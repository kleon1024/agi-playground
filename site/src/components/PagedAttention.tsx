/**
 * Why the KV cache benefits from OS-style paging — and what it costs.
 *
 * The naive allocator reserves max_seq_len contiguous slots per request up
 * front, because it doesn't know how long a generation will actually run.
 * Almost every request finishes well short of that ceiling, so most of the
 * reservation sits allocated and empty for the request's entire life —
 * internal fragmentation, and it also blocks admission: a request that
 * would easily fit in the memory that's actually free can't be scheduled
 * because none of that free memory is *contiguous*. PagedAttention instead
 * hands out fixed-size blocks on demand, tracked per sequence by a block
 * table, so waste is bounded by less than one block per request. That
 * indirection is not free: every attention read now chases a block table
 * to a scattered physical block instead of striding through one contiguous
 * buffer, so paging cannot ride a stock attention kernel — it needs one
 * written to gather non-contiguous blocks.
 */
import React, { useEffect, useMemo, useState } from 'react';

const TOTAL_CAPACITY = 64; // tokens of physical memory, both schemes share this budget
const BLOCK_SIZE = 4;
const TOTAL_BLOCKS = TOTAL_CAPACITY / BLOCK_SIZE;
const TICK_MS = 550;
const MAX_REQUESTS = 16;

const COLORS = ['var(--brand-chart-positive-fill)', 'var(--brand-chart-danger-fill)', 'var(--brand-chart-warning-fill)', 'var(--brand-chart-action-fill)', 'var(--brand-chart-danger-fill)', 'var(--brand-chart-signal)'];
const TEMPLATES = [
  { maxLen: 32, finishLen: 10 },
  { maxLen: 32, finishLen: 27 },
  { maxLen: 16, finishLen: 15 },
  { maxLen: 24, finishLen: 6 },
  { maxLen: 20, finishLen: 19 },
  { maxLen: 32, finishLen: 13 },
];

interface ReqDef {
  id: number;
  maxLen: number;
  finishLen: number;
  color: string;
}
interface ContigActive extends ReqDef {
  curLen: number;
}
interface PagedActive extends ReqDef {
  curLen: number;
  blocks: number[];
}
interface ContigState {
  admitted: ContigActive[];
  waiting: ReqDef[];
}
interface PagedState {
  admitted: PagedActive[];
  waiting: ReqDef[];
  freeBlocks: number[];
}

function tickContiguous(state: ContigState): ContigState {
  let admitted = state.admitted
    .map((r) => ({ ...r, curLen: Math.min(r.finishLen, r.curLen + 1) }))
    .filter((r) => r.curLen < r.finishLen); // reaching finishLen = EOS, frees the whole reservation

  const waiting = [...state.waiting];
  let reserved = admitted.reduce((s, r) => s + r.maxLen, 0);
  while (waiting.length > 0 && reserved + waiting[0].maxLen <= TOTAL_CAPACITY) {
    const next = waiting.shift() as ReqDef;
    admitted = [...admitted, { ...next, curLen: 0 }];
    reserved += next.maxLen;
  }
  return { admitted, waiting };
}

function tickPaged(state: PagedState): PagedState {
  const freeBlocks = [...state.freeBlocks];
  const grown = state.admitted.map((r) => {
    const curLen = Math.min(r.finishLen, r.curLen + 1);
    const needed = Math.ceil(curLen / BLOCK_SIZE);
    let blocks = r.blocks;
    while (blocks.length < needed && freeBlocks.length > 0) {
      blocks = [...blocks, freeBlocks.shift() as number];
    }
    return { ...r, curLen, blocks };
  });

  const admitted: PagedActive[] = [];
  for (const r of grown) {
    if (r.curLen >= r.finishLen) freeBlocks.push(...r.blocks); // EOS: give the exact blocks back
    else admitted.push(r);
  }

  const waiting = [...state.waiting];
  while (waiting.length > 0 && freeBlocks.length > 0) {
    const next = waiting.shift() as ReqDef;
    admitted.push({ ...next, curLen: 0, blocks: [] });
  }
  return { admitted, waiting, freeBlocks };
}

export default function PagedAttention(): React.ReactElement {
  const [nextId, setNextId] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [contig, setContig] = useState<ContigState>({ admitted: [], waiting: [] });
  const [paged, setPaged] = useState<PagedState>({
    admitted: [],
    waiting: [],
    freeBlocks: Array.from({ length: TOTAL_BLOCKS }, (_, i) => i),
  });

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setContig((s) => tickContiguous(s));
      setPaged((s) => tickPaged(s));
    }, TICK_MS);
    return () => clearInterval(id);
  }, [playing]);

  const addRequest = () => {
    if (nextId >= MAX_REQUESTS) return;
    const t = TEMPLATES[nextId % TEMPLATES.length];
    const def: ReqDef = { id: nextId, maxLen: t.maxLen, finishLen: t.finishLen, color: COLORS[nextId % COLORS.length] };
    setContig((s) => ({ ...s, waiting: [...s.waiting, def] }));
    setPaged((s) => ({ ...s, waiting: [...s.waiting, def] }));
    setNextId((n) => n + 1);
  };

  const finish = (id: number) => {
    setPaged((p) => {
      const removed = p.admitted.find((r) => r.id === id);
      return {
        admitted: p.admitted.filter((r) => r.id !== id),
        waiting: p.waiting.filter((r) => r.id !== id),
        freeBlocks: removed ? [...p.freeBlocks, ...removed.blocks] : p.freeBlocks,
      };
    });
    setContig((s) => ({
      admitted: s.admitted.filter((r) => r.id !== id),
      waiting: s.waiting.filter((r) => r.id !== id),
    }));
  };

  const reset = () => {
    setContig({ admitted: [], waiting: [] });
    setPaged({ admitted: [], waiting: [], freeBlocks: Array.from({ length: TOTAL_BLOCKS }, (_, i) => i) });
    setNextId(0);
  };

  const roster = useMemo(() => {
    const map = new Map<number, ReqDef>();
    const add = (r: ReqDef) => map.set(r.id, r);
    contig.admitted.forEach(add);
    contig.waiting.forEach(add);
    paged.admitted.forEach(add);
    paged.waiting.forEach(add);
    return Array.from(map.values()).sort((a, b) => a.id - b.id);
  }, [contig, paged]);

  const contigUsed = contig.admitted.reduce((s, r) => s + r.curLen, 0);
  const contigReserved = contig.admitted.reduce((s, r) => s + r.maxLen, 0);
  const contigUtil = (contigUsed / TOTAL_CAPACITY) * 100;

  const pagedUsed = paged.admitted.reduce((s, r) => s + r.curLen, 0);
  const pagedUtil = (pagedUsed / TOTAL_CAPACITY) * 100;

  const unit = 4.6; // px per token, for the contiguous bar
  const blockOwner: (PagedActive | null)[] = new Array(TOTAL_BLOCKS).fill(null);
  paged.admitted.forEach((r) => r.blocks.forEach((b) => { blockOwner[b] = r; }));

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button onClick={addRequest} disabled={nextId >= MAX_REQUESTS}
                style={{ padding: '0.25rem 0.7rem', borderRadius: 6, cursor: nextId >= MAX_REQUESTS ? 'default' : 'pointer' }}>
          + add request
        </button>
        <button onClick={() => setPlaying((p) => !p)} style={{ padding: '0.25rem 0.7rem', borderRadius: 6, cursor: 'pointer' }}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <button onClick={reset} style={{ padding: '0.25rem 0.7rem', borderRadius: 6, cursor: 'pointer' }}>
          reset
        </button>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {roster.map((r) => (
            <span key={r.id} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 'var(--type-xs)',
                                       padding: '0.1rem 0.4rem', borderRadius: 999, background: 'var(--ifm-color-emphasis-100)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.color, display: 'inline-block' }} />
              #{r.id}
              <button onClick={() => finish(r.id)} title="finish early (simulated EOS / cancel)"
                      style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 0, fontSize: 'var(--type-xs)', opacity: 0.7 }}>
                Remove
              </button>
            </span>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 300 }}>
          <div style={{ fontSize: 'var(--type-sm)', fontWeight: 600, marginBottom: '0.4rem' }}>
            contiguous pre-allocation (reserves max_seq_len)
          </div>
          <div style={{ display: 'flex', height: 26, borderRadius: 5, overflow: 'hidden', width: TOTAL_CAPACITY * unit }}>
            {contig.admitted.map((r) => (
              <div key={r.id} style={{ display: 'flex', width: r.maxLen * unit }} title={`#${r.id}: ${r.curLen}/${r.maxLen} reserved`}>
                <div style={{ width: r.curLen * unit, background: r.color, transition: 'width 200ms' }} />
                <div style={{ width: (r.maxLen - r.curLen) * unit, background: r.color, opacity: 0.25,
                              borderRight: '1px dashed var(--ifm-background-color)', transition: 'width 200ms' }} />
              </div>
            ))}
            <div style={{ flex: 1, background: 'var(--ifm-color-emphasis-200)' }} />
          </div>
          <div style={{ fontSize: 'var(--type-sm)', marginTop: '0.5rem' }}>
            utilization <strong>{contigUtil.toFixed(0)}%</strong> · reserved {contigReserved}/{TOTAL_CAPACITY}
            {contig.waiting.length > 0 && (
              <span style={{ color: 'var(--brand-chart-danger)' }}> · {contig.waiting.length} waiting, no contiguous room</span>
            )}
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 300 }}>
          <div style={{ fontSize: 'var(--type-sm)', fontWeight: 600, marginBottom: '0.4rem' }}>
            paged (block size {BLOCK_SIZE}, on demand)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, width: TOTAL_CAPACITY * unit }}>
            {blockOwner.map((owner, i) => (
              <div key={i} title={owner ? `#${owner.id}'s block` : 'free block'}
                   style={{ width: BLOCK_SIZE * unit - 3, height: 22, borderRadius: 3,
                            background: owner ? owner.color : 'var(--ifm-color-emphasis-200)',
                            transition: 'background 200ms' }} />
            ))}
          </div>
          <div style={{ fontSize: 'var(--type-sm)', marginTop: '0.5rem' }}>
            utilization <strong>{pagedUtil.toFixed(0)}%</strong> · {TOTAL_BLOCKS - paged.freeBlocks.length}/{TOTAL_BLOCKS} blocks used
            {paged.waiting.length > 0 && (
              <span style={{ color: 'var(--brand-chart-danger)' }}> · {paged.waiting.length} waiting, no free block</span>
            )}
          </div>
        </div>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.9rem' }}>
        Add a handful of requests: contiguous pre-allocation fills its bar
        with pale, wasted padding for every request that finishes well short
        of its reserved max_seq_len, and eventually refuses new requests
        outright — not because memory is full, but because no single
        contiguous stretch is free. The paged grid on the right keeps
        handing out whichever physical blocks are free, scattered wherever
        they land, so it sustains far higher utilization on the identical
        memory budget. The gap between the two is the cost usually left out
        of the pitch: those scattered blocks mean the attention kernel walks
        a block table and gathers from non-contiguous memory instead of
        striding through one buffer, which is why PagedAttention shipped
        with its own kernel rather than reusing a standard one.
      </p>
    </div>
  );
}
