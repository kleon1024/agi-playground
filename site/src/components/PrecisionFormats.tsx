/**
 * fp32 vs fp16 vs bf16: same 16 bits, a completely different trade-off.
 *
 * It's tempting to treat fp16 and bf16 as interchangeable "half precision"
 * options — same storage cost, so pick whichever the framework defaults to.
 * They spend their 16 bits in opposite places. fp16 keeps 10 mantissa bits
 * but only 5 exponent bits, so it's relatively precise near 1.0 but has a
 * tiny dynamic range — it overflows to ±Infinity above 65504, which is why
 * fp16 training needs loss scaling to keep small gradients from underflowing
 * to zero before they even reach that ceiling. bf16 keeps fp32's 8-bit
 * exponent and gives up mantissa bits instead (only 7): it spans fp32's
 * entire dynamic range and never overflows in the ranges training sees, but
 * it can't tell 1.0 from 1.0 plus a small update. That's why an fp32 master
 * copy of the weights exists at all — the accumulated update has to live
 * somewhere with enough mantissa bits to survive being added many times.
 */
import React, { useMemo, useState } from 'react';

const SIGN_COLOR = '#c4b5fd';
const EXP_COLOR = '#93c5fd';
const MANT_COLOR = '#5eead4';
const WARN_COLOR = '#fca5a5';

function floatToFp32Bits(v: number): number {
  const buf = new ArrayBuffer(4);
  new Float32Array(buf)[0] = v;
  return new Uint32Array(buf)[0];
}
function fp32BitsToValue(bits: number): number {
  const buf = new ArrayBuffer(4);
  new Uint32Array(buf)[0] = bits >>> 0;
  return new Float32Array(buf)[0];
}

/** Round-to-nearest-even truncation of fp32's top 16 bits — that's all bf16 is. */
function toBf16Bits(v: number): number {
  const fp32bits = floatToFp32Bits(v);
  const lsb = (fp32bits >>> 16) & 1;
  const roundBit = (fp32bits >>> 15) & 1;
  const sticky = (fp32bits & 0x7fff) !== 0 ? 1 : 0;
  let bf16bits = fp32bits >>> 16;
  if (roundBit && (sticky || lsb)) bf16bits = (bf16bits + 1) >>> 0;
  return bf16bits & 0xffff;
}
function bf16BitsToValue(bf16bits: number): number {
  return fp32BitsToValue(bf16bits << 16);
}

/** IEEE-754 binary16: 1 sign / 5 exponent / 10 mantissa, round-to-nearest-even. */
function fp32BitsToFp16Bits(fp32bits: number): number {
  const sign = (fp32bits >>> 16) & 0x8000;
  const exp = (fp32bits >>> 23) & 0xff;
  let mantissa = fp32bits & 0x7fffff;
  if (exp === 0xff) return sign | 0x7c00 | (mantissa ? 0x200 : 0);
  const newExp = exp - 127 + 15;
  if (newExp >= 0x1f) return sign | 0x7c00; // overflow -> Infinity
  if (newExp <= 0) {
    if (newExp < -10) return sign; // underflows to zero
    mantissa |= 0x800000;
    const shift = 14 - newExp;
    let halfMantissa = mantissa >>> shift;
    const remainder = mantissa & ((1 << shift) - 1);
    const halfway = 1 << (shift - 1);
    if (remainder > halfway || (remainder === halfway && (halfMantissa & 1))) halfMantissa += 1;
    return sign | halfMantissa;
  }
  let halfMantissa = mantissa >>> 13;
  const remainder = mantissa & 0x1fff;
  const halfway = 0x1000;
  let result = sign | (newExp << 10) | halfMantissa;
  if (remainder > halfway || (remainder === halfway && (halfMantissa & 1))) result += 1;
  return result & 0xffff;
}
function fp16BitsToValue(bits: number): number {
  const sign = bits & 0x8000 ? -1 : 1;
  const exp = (bits >>> 10) & 0x1f;
  const mantissa = bits & 0x3ff;
  if (exp === 0) return sign * mantissa * 2 ** -24;
  if (exp === 0x1f) return mantissa ? NaN : sign * Infinity;
  return sign * (1 + mantissa / 1024) * 2 ** (exp - 15);
}

function bitsToBinary(bits: number, width: number): string {
  return (bits >>> 0).toString(2).padStart(width, '0');
}

function fmtVal(x: number): string {
  if (x === Infinity) return '+Infinity';
  if (x === -Infinity) return '-Infinity';
  if (Number.isNaN(x)) return 'NaN';
  if (x === 0) return '0';
  const abs = Math.abs(x);
  if (abs >= 1e5 || abs < 1e-4) return x.toExponential(4);
  return String(Number(x.toPrecision(8)));
}

function fmtError(decoded: number, truth: number): string {
  if (!isFinite(decoded)) return 'overflow — value is unrepresentable';
  if (truth === 0) return `${fmtVal(decoded - truth)} absolute`;
  const rel = Math.abs((decoded - truth) / truth);
  return `${rel === 0 ? 'exact' : `${(rel * 100).toExponential(2)}%`} relative`;
}

interface Segment {
  widthBits: number;
  color: string;
  bitString: string;
  label: string;
}
function Bar({ segments }: { segments: Segment[] }): React.ReactElement {
  const total = segments.reduce((a, s) => a + s.widthBits, 0);
  return (
    <div style={{ display: 'flex', width: '100%', height: 22, borderRadius: 4, overflow: 'hidden' }}>
      {segments.map((s, i) => (
        <div
          key={i}
          title={`${s.label}: ${s.widthBits} bit${s.widthBits === 1 ? '' : 's'}`}
          style={{
            flexGrow: s.widthBits,
            flexBasis: 0,
            background: s.color,
            color: '#111318',
            fontSize: total > 20 ? '0.55rem' : '0.65rem',
            fontFamily: 'var(--ifm-font-family-monospace)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            letterSpacing: s.widthBits > 12 ? '-0.5px' : 'normal',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
          }}
        >
          {s.bitString}
        </div>
      ))}
    </div>
  );
}

const PRESETS = [1, 3.14159, 100000, 0.001, 65504];

export default function PrecisionFormats(): React.ReactElement {
  const [inputText, setInputText] = useState('3.14159');

  const parsed = parseFloat(inputText);
  const value = Number.isFinite(parsed) ? parsed : 0;

  const { fp32, fp16, bf16 } = useMemo(() => {
    const fp32bits = floatToFp32Bits(value);
    const fp16bits = fp32BitsToFp16Bits(fp32bits);
    const bf16bits = toBf16Bits(value);

    const fp32Value = fp32BitsToValue(fp32bits);
    const fp16Value = fp16BitsToValue(fp16bits);
    const bf16Value = bf16BitsToValue(bf16bits);

    return {
      fp32: {
        value: fp32Value,
        segments: [
          { widthBits: 1, color: SIGN_COLOR, bitString: bitsToBinary((fp32bits >>> 31) & 1, 1), label: 'sign' },
          { widthBits: 8, color: EXP_COLOR, bitString: bitsToBinary((fp32bits >>> 23) & 0xff, 8), label: 'exponent' },
          { widthBits: 23, color: MANT_COLOR, bitString: bitsToBinary(fp32bits & 0x7fffff, 23), label: 'mantissa' },
        ],
      },
      fp16: {
        value: fp16Value,
        overflow: !isFinite(fp16Value) && isFinite(value),
        segments: [
          { widthBits: 1, color: SIGN_COLOR, bitString: bitsToBinary((fp16bits >>> 15) & 1, 1), label: 'sign' },
          { widthBits: 5, color: EXP_COLOR, bitString: bitsToBinary((fp16bits >>> 10) & 0x1f, 5), label: 'exponent' },
          { widthBits: 10, color: MANT_COLOR, bitString: bitsToBinary(fp16bits & 0x3ff, 10), label: 'mantissa' },
        ],
      },
      bf16: {
        value: bf16Value,
        segments: [
          { widthBits: 1, color: SIGN_COLOR, bitString: bitsToBinary((bf16bits >>> 15) & 1, 1), label: 'sign' },
          { widthBits: 8, color: EXP_COLOR, bitString: bitsToBinary((bf16bits >>> 7) & 0xff, 8), label: 'exponent' },
          { widthBits: 7, color: MANT_COLOR, bitString: bitsToBinary(bf16bits & 0x7f, 7), label: 'mantissa' },
        ],
      },
    };
  }, [value]);

  // The concrete "why fp32 master weights exist" demo — independent of the input above.
  const demoInput = 1.0 + 1e-7;
  const demoFp32 = Math.fround(demoInput);
  const demoBf16 = bf16BitsToValue(toBf16Bits(demoInput));
  const demoFp16 = fp16BitsToValue(fp32BitsToFp16Bits(floatToFp32Bits(demoInput)));

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.8rem' }}>
        <input
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          spellCheck={false}
          style={{
            width: 160, padding: '0.4rem 0.6rem', borderRadius: 6,
            border: '1px solid var(--ifm-color-emphasis-300)',
            background: 'var(--ifm-background-surface-color)',
            color: 'var(--ifm-font-color-base)',
            fontFamily: 'var(--ifm-font-family-monospace)', fontSize: '0.9rem',
          }}
        />
        {PRESETS.map((p) => (
          <button
            key={p}
            onClick={() => setInputText(String(p))}
            style={{ padding: '0.25rem 0.6rem', borderRadius: 6, cursor: 'pointer', fontSize: '0.8rem' }}
          >
            {p}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.75rem', marginBottom: '0.6rem', opacity: 0.75 }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, background: SIGN_COLOR, borderRadius: 2, marginRight: 4 }} />sign</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, background: EXP_COLOR, borderRadius: 2, marginRight: 4 }} />exponent</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, background: MANT_COLOR, borderRadius: 2, marginRight: 4 }} />mantissa</span>
      </div>

      <div style={{ display: 'grid', gap: '0.7rem' }}>
        <div>
          <div style={{ fontSize: '0.8rem', marginBottom: 3 }}>
            <strong>fp32</strong> <span style={{ opacity: 0.6 }}>— 32 bits (1 / 8 / 23)</span>
          </div>
          <Bar segments={fp32.segments} />
          <div style={{ fontSize: '0.78rem', marginTop: 3, opacity: 0.85 }}>
            stores <strong>{fmtVal(fp32.value)}</strong> — {fmtError(fp32.value, value)}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.8rem', marginBottom: 3 }}>
            <strong>fp16</strong> <span style={{ opacity: 0.6 }}>— 16 bits (1 / 5 / 10)</span>
          </div>
          <Bar segments={fp16.segments} />
          <div style={{ fontSize: '0.78rem', marginTop: 3, color: fp16.overflow ? WARN_COLOR : 'inherit', opacity: fp16.overflow ? 1 : 0.85 }}>
            stores <strong>{fmtVal(fp16.value)}</strong> — {fmtError(fp16.value, value)}
            {fp16.overflow && ' — magnitude exceeds 65504, this is why fp16 training needs loss scaling'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.8rem', marginBottom: 3 }}>
            <strong>bf16</strong> <span style={{ opacity: 0.6 }}>— 16 bits (1 / 8 / 7)</span>
          </div>
          <Bar segments={bf16.segments} />
          <div style={{ fontSize: '0.78rem', marginTop: 3, opacity: 0.85 }}>
            stores <strong>{fmtVal(bf16.value)}</strong> — {fmtError(bf16.value, value)}
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: '1.1rem',
          padding: '0.7rem 0.9rem',
          borderRadius: 8,
          background: 'var(--ifm-color-emphasis-100)',
          fontSize: '0.82rem',
        }}
      >
        <strong>why fp32 master weights exist:</strong> compute 1.0 + 1e-7 in each format.
        <div style={{ display: 'flex', gap: '1.4rem', flexWrap: 'wrap', marginTop: '0.4rem' }}>
          <span>fp32 → <strong>{demoFp32.toPrecision(10)}</strong> {demoFp32 !== 1.0 ? '(update survives)' : ''}</span>
          <span style={{ color: demoBf16 === 1.0 ? WARN_COLOR : 'inherit' }}>
            bf16 → <strong>{fmtVal(demoBf16)}</strong> {demoBf16 === 1.0 ? '(update vanished)' : ''}
          </span>
          <span style={{ color: demoFp16 === 1.0 ? WARN_COLOR : 'inherit' }}>
            fp16 → <strong>{fmtVal(demoFp16)}</strong> {demoFp16 === 1.0 ? '(update vanished)' : ''}
          </span>
        </div>
      </div>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.75rem' }}>
        Type a value like <code>100000</code> above and watch fp16 overflow to
        Infinity while bf16, borrowing fp32&apos;s 8-bit exponent, represents it
        fine (with a coarser mantissa than fp32, but no overflow). Now look at
        the box above: a weight near 1.0 nudged by a gradient update of 1e-7
        keeps that update in fp32 — there's just enough mantissa — but loses
        it completely in both 16-bit formats, whose mantissas are too short to
        distinguish 1.0 from 1.0000001. That's why mixed-precision training
        keeps an fp32 copy of the weights: updates accumulate there, where
        they don't get rounded away, and a 16-bit copy is derived from it only
        for the matmuls.
      </p>
    </div>
  );
}
