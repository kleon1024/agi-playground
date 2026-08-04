/**
 * A dated lineage drawn on a real time axis, so the silences between ideas stay
 * visible.
 *
 * A bullet list spaces 1970, 1986, 2010 and 2017 evenly, which is the wrong
 * picture: the mechanism existed for sixteen years before anyone applied it to
 * neural networks, and for another twenty-four before a framework made it the
 * default. Those gaps are the argument a history section is making, and even
 * spacing erases them. Here the distance between two entries is proportional to
 * the years between them. A floor keeps a one-year gap readable and a ceiling
 * keeps a fifty-year gap on screen; where either applies, the axis goes dashed
 * so the stretch is not read as measured.
 *
 * Built in HTML rather than SVG on purpose. A lineage is a list: HTML gives real
 * buttons, real focus order, text that wraps at any width, and type that is the
 * size it says -- none of which an SVG drawing gets for free.
 */
import React, { useState } from 'react';

export interface Moment {
  year: number;
  /** What happened, in the reader's terms rather than the paper's title. */
  label: string;
  /** Author, venue and year, as the chapter already cites it. */
  source: string;
  /** What this made possible that the entry before it did not. */
  what: string;
}

interface TimelineProps {
  moments: Moment[];
  /** The question the reader is holding while they read the lineage. */
  lead: string;
  /** What the shape of the gaps means, once they have seen it. */
  close: string;
}

/** Vertical pixels per year, and the bounds a drawable axis has to respect. */
const PX_PER_YEAR = 4.2;
const MIN_GAP = 20;
const MAX_GAP = 190;

export default function Timeline({ moments, lead, close }: TimelineProps): React.ReactElement {
  const [selected, setSelected] = useState(0);

  const ordered = [...moments].sort((a, b) => a.year - b.year);
  const span = ordered[ordered.length - 1].year - ordered[0].year;
  const active = ordered[selected] ?? ordered[0];
  const previous = selected > 0 ? ordered[selected - 1] : null;

  const rows = ordered.map((moment, index) => {
    const years = index === 0 ? 0 : moment.year - ordered[index - 1].year;
    const trueGap = years * PX_PER_YEAR;
    const gap = index === 0 ? 0 : Math.min(MAX_GAP, Math.max(MIN_GAP, trueGap));
    return { moment, years, gap, toScale: index === 0 || Math.abs(gap - trueGap) < 1 };
  });
  const anyForced = rows.some((row) => !row.toScale);

  return (
    <div className="learning-widget">
      <p>{lead}</p>

      <ol className="timeline">
        {rows.map((row, index) => (
          <li
            key={`${row.moment.year}-${row.moment.label}`}
            className={row.toScale ? 'timeline__item' : 'timeline__item timeline__item--forced'}
          >
            {index > 0 && (
              <span className="timeline__wait" style={{ minHeight: `${row.gap}px` }}>
                {row.years} {row.years === 1 ? 'year' : 'years'}
              </span>
            )}
            <button
              type="button"
              className="timeline__entry"
              aria-pressed={index === selected}
              onClick={() => setSelected(index)}
            >
              <span className="timeline__year">{row.moment.year}</span>
              <span className="timeline__label">{row.moment.label}</span>
            </button>
          </li>
        ))}
      </ol>

      {anyForced && (
        <p className="timeline__legend">
          Solid stretches of the axis are drawn to scale. Dashed ones are too short
          or too long to draw at the same scale and still fit; their year counts
          are exact either way.
        </p>
      )}

      <div className="objective-readout">
        <div>
          <span>Selected</span>
          <strong>{active.year}</strong>
        </div>
        <div>
          <span>{previous ? `Years after ${previous.year}` : 'Earliest here'}</span>
          <strong>{previous ? active.year - previous.year : '—'}</strong>
        </div>
        <div>
          <span>Whole span</span>
          <strong>{span} years</strong>
        </div>
      </div>

      <div className="widget-caption widget-swap" aria-live="polite">
        {ordered.map((moment, index) => (
          <p
            key={`${moment.year}-detail`}
            data-shown={index === selected}
            aria-hidden={index !== selected}
          >
            <strong>{moment.source}</strong> — {moment.what}
          </p>
        ))}
      </div>

      <p>{close}</p>
    </div>
  );
}
