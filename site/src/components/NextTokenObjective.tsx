/**
 * What the training objective actually asks for, and what a loss value means.
 *
 * "Validation loss 3.0984" is the headline number of the pretraining run and
 * it is opaque until you can convert it back into a statement about
 * probability. This widget does that conversion in the one direction that
 * matters: move how much score the model gives the correct token over the
 * alternatives, and read off the probability, the cross-entropy, and the
 * perplexity together.
 *
 * The reference lines are measured, from
 * missions/01-language-model-agent/02-pretrain/runs/2026-07-28-pretrain-3b.md:
 * the uniform floor ln(16,512) = 9.712, the observed step-0 loss of 9.8697,
 * and the best validation loss of 3.0689. The scoring model itself is a
 * deliberate simplification and is labelled as one on the page: a real model
 * does not give every wrong token the same score.
 */
import React, { useMemo, useState } from 'react';

const VOCAB = 16512;

/* The sentence stage 02 sampled from the trained checkpoint, tokenised the way
   a byte-level BPE tends to: common words whole, rarer ones in pieces. */
const TOKENS = ['Photo', 'synthesis', ' is', ' the', ' process', ' by', ' which', ' plants'];

const MEASURED = {
  uniform: Math.log(VOCAB), // 9.7117 — what an untrained model must score
  step0: 9.8697, // observed on this run before any update
  best: 3.0689, // best validation loss, step 21,000
};

/** Cross-entropy when the correct token is `margin` nats above every other. */
function lossFromMargin(margin: number): number {
  return Math.log(Math.exp(margin) + VOCAB - 1) - margin;
}

/** The inverse, by bisection: which margin produces this loss. */
function marginFromLoss(loss: number): number {
  let low = 0;
  let high = 20;
  for (let i = 0; i < 60; i += 1) {
    const mid = (low + high) / 2;
    if (lossFromMargin(mid) > loss) low = mid;
    else high = mid;
  }
  return (low + high) / 2;
}

export default function NextTokenObjective(): React.ReactElement {
  const [margin, setMargin] = useState(() => marginFromLoss(MEASURED.best));

  const { loss, probability, perplexity } = useMemo(() => {
    const value = lossFromMargin(margin);
    return {
      loss: value,
      probability: Math.exp(-value),
      perplexity: Math.exp(value),
    };
  }, [margin]);

  const atBest = Math.abs(loss - MEASURED.best) < 0.02;
  const atFloor = Math.abs(loss - MEASURED.uniform) < 0.02;

  /* Position on a 0-to-uniform scale, so the bar reads as "distance travelled
     away from knowing nothing". */
  const travelled = Math.max(0, Math.min(1, 1 - loss / MEASURED.uniform));

  return (
    <div className="learning-widget">
      <p>
        The objective is one rule applied at every position: given everything up to
        here, put probability on the token that actually comes next. The input is the
        sequence shifted left by one, so a single forward pass supplies a target at
        every position at once.
      </p>

      <div className="objective-strip" role="group" aria-label="Input and target alignment">
        {TOKENS.map((token, index) => (
          <div className="objective-strip__column" key={`${token}-${index}`}>
            <code className="objective-strip__cell" data-role="input">
              {token.replace(/ /g, '·')}
            </code>
            <span className="objective-strip__arrow" aria-hidden="true">
              {index < TOKENS.length - 1 ? '↓' : ''}
            </span>
            <code className="objective-strip__cell" data-role="target">
              {index < TOKENS.length - 1 ? TOKENS[index + 1].replace(/ /g, '·') : '—'}
            </code>
          </div>
        ))}
      </div>
      <p className="objective-note">
        Top row: what the model reads. Bottom row: what it is scored against. A middle
        dot marks a leading space, which is part of the token. The last position has no
        target, so it contributes nothing to the loss.
      </p>

      <label>
        How much score the correct token gets over the alternatives
        <input
          type="range"
          min={0}
          max={10}
          step={0.05}
          value={margin}
          onChange={(event) => setMargin(Number(event.target.value))}
          aria-label="Score margin for the correct token, in nats"
        />
      </label>

      <div className="objective-readout">
        <div>
          <span>Probability on the correct token</span>
          <strong>{(probability * 100).toFixed(2)}%</strong>
        </div>
        <div>
          <span>Cross-entropy loss</span>
          <strong>{loss.toFixed(4)}</strong>
        </div>
        <div>
          <span>Perplexity</span>
          <strong>{perplexity.toFixed(1)}</strong>
        </div>
      </div>

      <svg viewBox="0 0 100 10" width="100%" height="30" role="img" aria-label={`Loss ${loss.toFixed(2)} against a uniform floor of ${MEASURED.uniform.toFixed(3)}`}>
        <rect x="0" y="3" width="100" height="4" fill="var(--rehearse-rule)" />
        <rect x="0" y="3" width={travelled * 100} height="4" fill="var(--rehearse-action)" />
        <line
          x1={(1 - MEASURED.best / MEASURED.uniform) * 100}
          y1="0"
          x2={(1 - MEASURED.best / MEASURED.uniform) * 100}
          y2="10"
          stroke="var(--rehearse-ink)"
          strokeWidth="0.6"
        />
      </svg>
      <p className="objective-note">
        Left edge is a model that knows nothing. The vertical mark is where this run
        finished.
      </p>

      <p>
        {atFloor ? (
          <>
            This is the floor. Spreading probability evenly across all {VOCAB.toLocaleString()}{' '}
            tokens costs exactly <strong>ln({VOCAB.toLocaleString()}) = {MEASURED.uniform.toFixed(4)}</strong>{' '}
            nats — which is why a correctly initialised model must start there, and why
            this run&rsquo;s measured step 0 of {MEASURED.step0} was the check that its
            wiring was right.
          </>
        ) : atBest ? (
          <>
            This is what the run achieved: a best validation loss of{' '}
            <strong>{MEASURED.best}</strong>. Converted back, the model puts roughly{' '}
            <strong>{(probability * 100).toFixed(1)}%</strong> of its probability on the
            token that actually comes next — about one in {perplexity.toFixed(0)}. That is
            the whole meaning of the headline number, and it is a long way from knowing
            what it is talking about.
          </>
        ) : (
          <>
            At this margin the model is right about {(probability * 100).toFixed(1)}% of the
            time in the only sense the loss measures. For comparison the run measured{' '}
            {MEASURED.step0} before any update and {MEASURED.best} at its best.
          </>
        )}
      </p>

      <p>
        Simplified, deliberately: this treats every wrong token as equally wrong, so one
        number describes the whole distribution. A trained model concentrates its
        mistakes — asked to continue &ldquo;Photosynthesis is the process by&rdquo;, it
        will rank &ldquo;which&rdquo; far above a random token even when it gets the
        answer wrong. The arithmetic connecting loss, probability, and perplexity is
        exact; the flat alternative distribution is a teaching device.
      </p>
    </div>
  );
}
