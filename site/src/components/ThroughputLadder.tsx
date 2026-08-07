/**
 * Five flags, one at a time, on an unchanged model and an unchanged batch.
 *
 * Every number is measured, from
 * 01-language-model/02-pretrain/throughput/runs/2026-07-28-throughput-ladder.md, at
 * micro-batch 16 over 30 timed steps following 10 discarded warm-up steps.
 *
 * The learner turns each flag on and off and reads the consequence for
 * throughput, MFU, and peak memory. Two things the ladder is built to make
 * visible: the flags that matter are the ones attacking memory traffic rather
 * than arithmetic, and the fp32 rung reported a number for a configuration
 * that did not fit in VRAM.
 */
import React, { useState } from 'react';

const CARD_MEMORY_MB = 24_564;

type Rung = {
  key: string;
  label: string;
  tokensPerSecond: number;
  mfu: number;
  stepMs: number;
  peakMb: number;
  gain: string;
  note: string;
};

/* Cumulative: each entry is the measured result of every flag up to and
   including this one. Index 0 is the baseline, so it has no toggle. */
const LADDER: Rung[] = [
  {
    key: 'fp32',
    label: 'fp32, eager, math attention',
    tokensPerSecond: 11_521,
    mfu: 4.5,
    stepMs: 1422.1,
    peakMb: 27_708.7,
    gain: 'baseline',
    note: 'The whole step in fp32, no fusion, attention computed by materialising the full score matrix. This configuration needs more memory than the card has.',
  },
  {
    key: 'bf16',
    label: 'bf16 autocast',
    tokensPerSecond: 32_463,
    mfu: 12.6,
    stepMs: 504.7,
    peakMb: 23_565.1,
    gain: '2.82x',
    note: 'Half the bytes per activation. Read the caution below before crediting bf16 with all of this: at a micro-batch that fits both dtypes, the same swap is worth 1.28x.',
  },
  {
    key: 'flash',
    label: 'flash attention',
    tokensPerSecond: 95_328,
    mfu: 37.1,
    stepMs: 171.9,
    peakMb: 13_303.1,
    gain: '8.27x',
    note: 'The largest single win, and it is not a faster matrix multiply. The same attention is computed without ever writing the sequence-by-sequence score matrix to memory.',
  },
  {
    key: 'fusedadam',
    label: 'fused AdamW',
    tokensPerSecond: 98_246,
    mfu: 38.3,
    stepMs: 166.8,
    peakMb: 13_303.2,
    gain: '8.53x',
    note: 'Worth 1.03x, which at this size is nearly noise: the optimizer touches 88M parameters once per step against 16.8M tokens of forward and backward work.',
  },
  {
    key: 'compile',
    label: 'torch.compile',
    tokensPerSecond: 169_230,
    mfu: 65.9,
    stepMs: 96.8,
    peakMb: 8685.7,
    gain: '14.69x',
    note: 'Chains of small elementwise operations become single fused kernels. The profiler shows the matmuls unchanged at 275.8ms and 277.5ms across this boundary — 341ms of everything else disappeared.',
  },
];

/* Not cumulative with the rest: it is a trade, not an improvement, and is
   measured on top of the full stack above. */
const CHECKPOINTING: Rung = {
  key: 'recompute',
  label: 'activation checkpointing',
  tokensPerSecond: 140_748,
  mfu: 54.8,
  stepMs: 116.4,
  peakMb: 3410.4,
  gain: '12.22x',
  note: 'Blocks run twice instead of holding their activations. It costs 17% of throughput and returns 2.5x the memory, which is worth taking only if that memory buys a larger batch.',
};

export default function ThroughputLadder(): React.ReactElement {
  const [level, setLevel] = useState(LADDER.length - 1);
  const [recompute, setRecompute] = useState(false);

  const current = recompute && level === LADDER.length - 1 ? CHECKPOINTING : LADDER[level];
  const baseline = LADDER[0];
  const overflows = current.peakMb > CARD_MEMORY_MB;

  return (
    <div className="learning-widget">
      <p>
        Same 88,197,888-parameter model, same micro-batch of 16 sequences of 1,024
        tokens, same card. Add one flag at a time and watch what it is worth.
      </p>

      <label>
        Flags enabled
        <input
          type="range"
          min={0}
          max={LADDER.length - 1}
          step={1}
          value={level}
          onChange={(event) => {
            setLevel(Number(event.target.value));
            if (Number(event.target.value) !== LADDER.length - 1) setRecompute(false);
          }}
          aria-label="How many flags are enabled, cumulatively"
        />
      </label>

      <ol className="ladder-flags">
        {LADDER.slice(1).map((rung, index) => (
          <li key={rung.key} data-on={index + 1 <= level}>
            {rung.label}
          </li>
        ))}
        <li data-on={recompute}>{CHECKPOINTING.label}</li>
      </ol>

      <label>
        <input
          type="checkbox"
          checked={recompute}
          disabled={level !== LADDER.length - 1}
          onChange={(event) => setRecompute(event.target.checked)}
        />
        Trade throughput for memory (activation checkpointing, needs every flag on)
      </label>

      <div className="objective-readout">
        <div>
          <span>Tokens per second</span>
          <strong>{current.tokensPerSecond.toLocaleString()}</strong>
        </div>
        <div>
          <span>Model FLOPs Utilization</span>
          <strong>{current.mfu.toFixed(1)}%</strong>
        </div>
        <div>
          <span>Time per step</span>
          <strong>{current.stepMs.toFixed(1)}ms</strong>
        </div>
        <div>
          <span>Peak memory</span>
          <strong>{(current.peakMb / 1000).toFixed(1)}GB</strong>
        </div>
      </div>

      <p className="objective-note">
        Against the baseline: <strong>{current.gain}</strong> the throughput of fp32 eager
        with math attention, which sustained {baseline.tokensPerSecond.toLocaleString()}{' '}
        tokens per second at {baseline.mfu.toFixed(1)}% MFU.
      </p>

      <div className="widget-swap">
        {[...LADDER, CHECKPOINTING].map((rung) => (
          <p className="widget-caption" key={rung.key} data-shown={rung.key === current.key}>
            {rung.note}
          </p>
        ))}
      </div>

      <div className="widget-swap">
        <p className="objective-note" data-shown={overflows}>
          <strong>This configuration does not fit.</strong> Peak memory is{' '}
          {(current.peakMb / 1000).toFixed(1)}GB against the card&rsquo;s 24.6GB, and it
          still produced a number, because this host pages GPU allocations into system
          memory rather than raising out-of-memory. Part of what looks like slow fp32
          arithmetic is traffic across the bus.
        </p>
        <p className="objective-note" data-shown={!overflows}>
          Peak memory is {(current.peakMb / 1000).toFixed(1)}GB against the card&rsquo;s
          24.6GB, so this configuration is resident and its throughput means what it
          appears to mean.
        </p>
      </div>

      <p>
        Measured on one 24GB card, 30 timed steps after 10 discarded warm-up steps, in{' '}
        <code>01-language-model/02-pretrain/throughput/runs/2026-07-28-throughput-ladder.md</code>.
        MFU is computed against a published 165 TFLOP/s bf16 figure, so it is comparable
        across this repository&rsquo;s runs and not against numbers using a different
        denominator.
      </p>
    </div>
  );
}
