/**
 * A chart frame that draws at 1:1 pixels, with d3 scales instead of hand-rolled
 * value-to-coordinate arithmetic.
 *
 * Every chart here used to draw into a fixed `viewBox`, which the browser then
 * scaled to fit the column. Scaling a drawing scales its type: a label declared
 * at 13px inside a 600-unit viewBox arrives at 7px in a 322px phone column and
 * at 20px on a laptop. That made the readable-type floor something each
 * component had to counteract by hand, and it made axis gutters — also in user
 * units — clip their own labels at one width while wasting space at another.
 * Both defects were found by measurement in components that built and rendered
 * without a warning.
 *
 * This frame measures its container and hands the caller real pixel dimensions.
 * A font size is then the size it says, and a 44px gutter is 44px at every
 * viewport. Callers get `scaleLinear` and friends from d3-scale, so ticks,
 * domains and nice-rounding are not re-derived per component.
 *
 * Server rendering has no container to measure, so the first paint uses
 * FALLBACK_WIDTH and a ResizeObserver corrects it on mount. The statically
 * rendered HTML is therefore a real chart at a plausible width rather than an
 * empty box, which keeps the no-JavaScript reading order intact.
 */
import React, { useEffect, useRef, useState } from 'react';

export interface Padding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface Frame {
  /** Full rendered width of the SVG, in CSS pixels. */
  width: number;
  /** Full rendered height of the SVG, in CSS pixels. */
  height: number;
  padding: Padding;
  /** Plot area, i.e. the frame minus its padding. */
  innerWidth: number;
  innerHeight: number;
  /** True once the container has actually been measured. */
  measured: boolean;
}

const FALLBACK_WIDTH = 640;

const DEFAULT_PADDING: Padding = { top: 16, right: 16, bottom: 34, left: 44 };

interface ChartProps {
  /** Rendered height in CSS pixels. Fixed, because vertical space is a design
   *  decision rather than something that should track the column width. */
  height: number;
  padding?: Partial<Padding>;
  /** Describes the chart for a reader who cannot see it. */
  label: string;
  children: (frame: Frame) => React.ReactNode;
  svgProps?: React.SVGProps<SVGSVGElement>;
  /**
   * Called with the pointer's x position inside the plot area, in pixels, or
   * null when the pointer leaves it. Reading a curve by pointing at it is the
   * interaction several charts share, and it was the same rect arithmetic —
   * plus the same mouse-only event handlers, unusable on a phone — in each of
   * them. Pointer events cover mouse and touch alike.
   */
  onPointerAt?: (x: number | null, frame: Frame) => void;
}

/** Measures an element's content-box width, starting from a server-safe guess. */
export function useMeasuredWidth<T extends HTMLElement>(): [
  React.RefObject<T | null>,
  number,
  boolean,
] {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(FALLBACK_WIDTH);
  const [measured, setMeasured] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect.width ?? 0;
      if (next > 0) {
        setWidth(next);
        setMeasured(true);
      }
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return [ref, width, measured];
}

export default function Chart({
  height,
  padding,
  label,
  children,
  svgProps,
  onPointerAt,
}: ChartProps): React.ReactElement {
  const [ref, width, measured] = useMeasuredWidth<HTMLDivElement>();
  const pad: Padding = { ...DEFAULT_PADDING, ...padding };

  const frame: Frame = {
    width,
    height,
    padding: pad,
    innerWidth: Math.max(0, width - pad.left - pad.right),
    innerHeight: Math.max(0, height - pad.top - pad.bottom),
    measured,
  };

  const report = (event: React.PointerEvent<SVGSVGElement>) => {
    if (!onPointerAt) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left - pad.left;
    onPointerAt(x < 0 || x > frame.innerWidth ? null : x, frame);
  };

  const pointerProps = onPointerAt
    ? {
        onPointerMove: report,
        onPointerDown: report,
        onPointerLeave: () => onPointerAt(null, frame),
        /* A vertical swipe still scrolls the page; a horizontal drag reads the
           chart. Without this a touch drag never reaches the handler at all. */
        style: { touchAction: 'pan-y' as const, cursor: 'crosshair' },
      }
    : {};

  return (
    <div ref={ref} className="chart">
      <svg
        className="chart__svg"
        width={width}
        height={height}
        role="img"
        aria-label={label}
        {...pointerProps}
        {...svgProps}
        style={{ ...pointerProps.style, ...svgProps?.style }}
      >
        {children(frame)}
      </svg>
    </div>
  );
}
