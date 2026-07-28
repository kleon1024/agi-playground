/**
 * One motion policy for every animated explanation in the curriculum.
 *
 * An animation that explains a causal transition is only useful if the reader
 * can stop it, restart it, and never receives it against their stated
 * preference. Rather than repeat that logic per widget, both the pipeline
 * grammar and the architecture drawing take their clock from here.
 *
 * The animation starts once, when the widget is actually on screen, and only if
 * the reader has not asked for reduced motion. Any interaction hands control
 * back to the reader permanently.
 */
import { useEffect, useRef, useState } from 'react';

export function useAutoplayOnView<T extends HTMLElement>(): {
  ref: React.RefObject<T | null>;
  playing: boolean;
  setPlaying: React.Dispatch<React.SetStateAction<boolean>>;
} {
  const ref = useRef<T>(null);
  const startedRef = useRef(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const stop = () => {
      if (reduced.matches) setPlaying(false);
    };
    reduced.addEventListener('change', stop);
    if (reduced.matches || startedRef.current) {
      return () => reduced.removeEventListener('change', stop);
    }

    const start = () => {
      if (startedRef.current) return;
      startedRef.current = true;
      setPlaying(true);
    };
    if (!('IntersectionObserver' in window)) {
      start();
      return () => reduced.removeEventListener('change', stop);
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          start();
          observer.disconnect();
        }
      },
      { threshold: 0.45 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => {
      observer.disconnect();
      reduced.removeEventListener('change', stop);
    };
  }, []);

  return { ref, playing, setPlaying };
}

/**
 * Calls `onFrame` with elapsed milliseconds while `playing` is true. The
 * callback is held in a ref so the loop is not torn down and rebuilt on every
 * render, and a frame is clamped to 64ms so a backgrounded tab does not
 * fast-forward the explanation on return.
 */
export function useFrameLoop(playing: boolean, onFrame: (dtMs: number) => void): void {
  const callback = useRef(onFrame);
  callback.current = onFrame;

  useEffect(() => {
    if (!playing) return undefined;
    let frame = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = Math.min(now - last, 64);
      last = now;
      callback.current(dt);
      frame = window.requestAnimationFrame(tick);
    };
    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [playing]);
}
