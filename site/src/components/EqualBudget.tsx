/**
 * One set of nine training runs, ranked three different ways.
 *
 * "MoE beats dense" is not a fact until you say what stayed fixed while the
 * feed-forward changed. Every loss here is measured, from
 * missions/01-language-model-agent/02-pretrain/architecture-ablations/runs/2026-07-28-moe-rung.md:
 * three arms, three seeds each, 200M tokens per run on one 24GB card.
 *
 * The learner switches the held-equal quantity and watches the same nine runs
 * change their verdict — a clear win, a result too small to read against the
 * seed spread, and a definition with no arm at all. That third state is not a
 * gap in the widget; it is the point. A budget you did not buy is a blank,
 * not a tie.
 *
 * The axis is deliberately zoomed to 3.755-3.870 and labelled as such: at
 * full scale from zero, none of these differences would be visible, and the
 * comparison worth seeing is each gap against the error band beside it.
 */
import React, { useState } from 'react';

const AXIS_MIN = 3.755;
const AXIS_MAX = 3.87;
const pos = (loss: number) => ((loss - AXIS_MIN) / (AXIS_MAX - AXIS_MIN)) * 100;

type Arm = {
  name: string;
  detail: string;
  mean: number;
  lo: number;
  hi: number;
  best: boolean;
};

type Budget = {
  id: string;
  label: string;
  held: string;
  arms: Arm[];
  verdict: string;
  gap: string;
  note: string;
};

const DENSE = { name: 'Dense', mean: 3.8608, lo: 3.8596, hi: 3.8629 };

const BUDGETS: Budget[] = [
  {
    id: 'active',
    label: 'Equal active parameters',
    held: 'each token passes through the same number of parameters',
    arms: [
      { ...DENSE, detail: '33,652,736 active of 33,661,440 stored', best: false },
      {
        name: 'Mixture-of-experts',
        detail: '33,685,504 active of 67,314,176 stored',
        mean: 3.7707,
        lo: 3.7656,
        hi: 3.7778,
        best: true,
      },
    ],
    verdict: 'Mixture-of-experts wins',
    gap: '0.0901 nats, 7.4x the widest seed spread',
    note: 'Twice the stored parameters at matched compute per token, and the gap is far outside the error bands beside it. This is the question mixture-of-experts was invented to answer, and at 33M parameters over 200M tokens the answer is already yes.',
  },
  {
    id: 'total',
    label: 'Equal total parameters',
    held: 'the model stores the same number of parameters',
    arms: [
      { ...DENSE, detail: '33,661,440 stored, all of them active', best: false },
      {
        name: 'Mixture-of-experts',
        detail: '33,694,208 stored, 22,478,848 active',
        mean: 3.8607,
        lo: 3.8595,
        hi: 3.8629,
        best: false,
      },
    ],
    verdict: 'Too close to call',
    gap: '0.0001 nats, against seed spreads of 0.0033 and 0.0034',
    note: 'The two bands sit on top of each other, which does not say the arms are equal — it says this ladder cannot tell them apart. What the MoE arm did buy is on the other axis entirely: the same loss while passing each token through 33.2% fewer parameters.',
  },
  {
    id: 'wallclock',
    label: 'Equal wall-clock',
    held: 'both arms get the same number of seconds on the card',
    arms: [],
    verdict: 'No result',
    gap: 'this arm was never run',
    note: 'Both MoE arms ran at roughly half of dense throughput, so in the 1,645.9 seconds the winning arm above needed, dense would have trained on 391M tokens instead of 200M. Whether it would still have lost was not measured. The 0.0901 nats is not evidence about this question, and a budget definition you did not buy is a blank rather than a tie.',
  },
];

export default function EqualBudget(): React.ReactElement {
  const [id, setId] = useState(BUDGETS[0].id);
  const budget = BUDGETS.find((b) => b.id === id) as Budget;

  return (
    <div className="learning-widget">
      <p>
        The same nine runs — dense against mixture-of-experts, three seeds each, 200M
        tokens apiece — scored under each definition of an equal budget in turn.
      </p>

      <div className="widget-controls" role="group" aria-label="Budget definition">
        {BUDGETS.map((b) => (
          <button key={b.id} type="button" aria-pressed={b.id === id} onClick={() => setId(b.id)}>
            {b.label}
          </button>
        ))}
      </div>

      <p className="widget-controls__status">Holding {budget.held}.</p>

      {budget.arms.length > 0 ? (
        <div className="budget-axis">
          {budget.arms.map((arm) => (
            <div className="budget-axis__row" key={arm.name}>
              <span className="budget-axis__name">
                <strong>{arm.name}</strong>
                <span>{arm.detail}</span>
              </span>
              <span className="budget-axis__track">
                <span
                  className="budget-axis__band"
                  data-best={arm.best}
                  style={{ left: `${pos(arm.lo)}%`, width: `${pos(arm.hi) - pos(arm.lo)}%` }}
                />
                <span className="budget-axis__mean" data-best={arm.best} style={{ left: `${pos(arm.mean)}%` }} />
              </span>
              <span className="budget-axis__value">
                {arm.mean.toFixed(4)}
                <span>
                  {arm.lo.toFixed(4)}&ndash;{arm.hi.toFixed(4)}
                </span>
              </span>
            </div>
          ))}
          <p className="budget-axis__scale">
            Validation loss, lower is better. Axis zoomed to {AXIS_MIN}&ndash;{AXIS_MAX}; the bar
            behind each marker spans that arm&rsquo;s three seeds.
          </p>
        </div>
      ) : (
        <p className="budget-axis__empty">
          No arm was trained under this definition, so there is nothing to plot.
        </p>
      )}

      <div className="objective-readout">
        <div>
          <span>Verdict</span>
          <strong>{budget.verdict}</strong>
        </div>
        <div>
          <span>Margin</span>
          <strong>{budget.gap}</strong>
        </div>
      </div>

      <div className="widget-swap">
        {BUDGETS.map((b) => (
          <p className="widget-caption" key={b.id} data-shown={b.id === id}>
            {b.note}
          </p>
        ))}
      </div>

      <p>
        Nothing about either architecture changes between these three views; only the
        quantity the comparison was normalised against does. That is the whole argument
        for naming a budget definition on the run record rather than after the fact, and
        it is why{' '}
        <code>missions/01-language-model-agent/02-pretrain/architecture-ablations/core/ablate.py</code> will not
        write a result file without one.
      </p>
    </div>
  );
}
