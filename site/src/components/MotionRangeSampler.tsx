import React, { useState } from 'react';

const DIRECTIONS = ['right', 'left', 'down', 'up', 'down_right', 'down_left', 'up_right', 'up_left'] as const;
const HALF_SIZES = [3, 4, 5] as const;
const WIDTH = 32;
const N_FRAMES = 8;
const SPEED = 2;

const UNIT: Record<(typeof DIRECTIONS)[number], [number, number]> = {
  right: [1, 0], left: [-1, 0], down: [0, 1], up: [0, -1],
  down_right: [1, 1], down_left: [-1, 1], up_right: [1, -1], up_left: [-1, -1],
};

function startRange(unitComponent: number, half: number, span: number): [number, number] {
  const travel = unitComponent !== 0 ? (N_FRAMES - 1) * SPEED * Math.abs(unitComponent) : 0;
  const lo = half;
  const hi = span - half - 1;
  if (unitComponent > 0) return [lo, hi - travel];
  if (unitComponent < 0) return [lo + travel, hi];
  return [lo, hi];
}

export default function MotionRangeSampler(): React.ReactElement {
  const [direction, setDirection] = useState<(typeof DIRECTIONS)[number]>('right');
  const [half, setHalf] = useState<(typeof HALF_SIZES)[number]>(3);
  const [dx, dy] = UNIT[direction];
  const [xLo, xHi] = startRange(dx, half, WIDTH);
  const [yLo, yHi] = startRange(dy, half, WIDTH);
  const validXCount = Math.max(0, xHi - xLo + 1);
  const validYCount = Math.max(0, yHi - yLo + 1);
  return (
    <div className="learning-widget">
      <label>
        direction{' '}
        <select value={direction} onChange={(e) => setDirection(e.target.value as (typeof DIRECTIONS)[number])}>
          {DIRECTIONS.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </label>{' '}
      <label>
        half-size{' '}
        <select value={half} onChange={(e) => setHalf(Number(e.target.value) as (typeof HALF_SIZES)[number])}>
          {HALF_SIZES.map((h) => (
            <option key={h} value={h}>{h}</option>
          ))}
        </select>
      </label>
      <p>valid start x range: [{xLo}, {xHi}] ({validXCount} positions)</p>
      <p>valid start y range: [{yLo}, {yHi}] ({validYCount} positions)</p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Larger shapes and diagonal motion shrink the valid start range, since the shape must
        clear the canvas edge for all 8 frames. This is the same bounds arithmetic
        `_start_range()` uses -- not a separately-derived renderer.
      </p>
    </div>
  );
}
