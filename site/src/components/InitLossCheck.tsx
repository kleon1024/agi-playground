/**
 * The cheapest check in pretraining: does step 0 land where it must?
 *
 * A model that has learned nothing can only spread probability evenly over the
 * vocabulary, so its cross-entropy is ln(vocab_size). The measured default is
 * this repository's own stage-02 run — 9.8697 against ln(16,512) = 9.712,
 * recorded in
 * missions/01-language-model-agent/02-pretrain/runs/2026-07-28-pretrain-3b.md.
 * Every other position of the slider is a hypothetical the reader is asked to
 * diagnose, and is labelled as one.
 */
import React, { useMemo, useState } from 'react';

const MEASURED_STEP0 = 9.8697;
const MEASURED_VOCAB = 16512;

const VOCABULARIES = [
  { size: 1024, label: '1,024 (stage 01 smoke tokenizer)' },
  { size: 16512, label: '16,512 (this run)' },
  { size: 50257, label: '50,257 (GPT-2)' },
  { size: 128256, label: '128,256 (Llama 3)' },
];

function diagnose(observed: number, uniform: number) {
  const delta = observed - uniform;
  if (delta < -1.5) {
    return {
      verdict: 'Too low — the model is seeing the answer',
      detail:
        'A model with random weights has no way to beat the uniform guess. A loss this far below it means information about the target is reaching the prediction: labels shifted the wrong way, an attention mask that lets a position read itself, or validation tokens that also appear in training. Stop and find it; five hours will not fix it.',
    };
  }
  if (delta < -0.3) {
    return {
      verdict: 'Slightly low — worth one look',
      detail:
        'Small enough to be an unlucky initialization, large enough that a leak cannot be ruled out. Check the label shift and the mask before committing the budget.',
    };
  }
  if (delta <= 0.5) {
    return {
      verdict: 'Healthy',
      detail:
        'Sitting just above the uniform line is what correctly initialized weights produce: random rather than exactly uniform in their effect. The data path, the model, and the loss agree with each other.',
    };
  }
  if (delta <= 2) {
    return {
      verdict: 'High — suspect initialization',
      detail:
        'The model starts worse than guessing, which means the output layer is actively mis-weighted. Check the initialization scale on the head and whether the final norm is applied before it.',
    };
  }
  return {
    verdict: 'Far too high — something is wrong with the loss itself',
    detail:
      'This is not a bad initialization; it is a different quantity being computed. Check the reduction (sum where it should be mean), whether padding is being scored, and whether targets are aligned to the right positions.',
  };
}

export default function InitLossCheck(): React.ReactElement {
  const [vocab, setVocab] = useState(MEASURED_VOCAB);
  const [observed, setObserved] = useState(MEASURED_STEP0);

  const uniform = useMemo(() => Math.log(vocab), [vocab]);
  const { verdict, detail } = diagnose(observed, uniform);
  const atMeasured = vocab === MEASURED_VOCAB && Math.abs(observed - MEASURED_STEP0) < 1e-6;

  return (
    <div className="learning-widget">
      <label>
        Vocabulary size
        <select
          aria-label="Vocabulary size"
          value={vocab}
          onChange={(event) => setVocab(Number(event.target.value))}
        >
          {VOCABULARIES.map((entry) => (
            <option key={entry.size} value={entry.size}>
              {entry.label}
            </option>
          ))}
        </select>
      </label>

      <p>
        Uniform-guess loss: <strong>ln({vocab.toLocaleString()}) = {uniform.toFixed(3)}</strong>{' '}
        nats. This is the floor an untrained model starts at, and it moves with the vocabulary — a
        step-0 loss of 9.7 is healthy for this run and badly broken for a 1,024-token tokenizer.
      </p>

      <label>
        Observed step-0 loss: {observed.toFixed(4)}
        <input
          type="range"
          aria-label="Observed step-0 loss"
          min={2}
          max={14}
          step={0.05}
          value={observed}
          onChange={(event) => setObserved(Number(event.target.value))}
        />
      </label>

      <p>
        <strong>{verdict}.</strong> {detail}
      </p>

      <p>
        {atMeasured ? (
          <>
            These are the measured values: stage 02 reported <strong>9.8697</strong> at step 0
            against a 16,512-token vocabulary, 0.158 above the uniform line.
          </>
        ) : (
          <>
            Hypothetical position. The measured stage-02 run was <strong>9.8697</strong> at a
            16,512-token vocabulary; move the controls back to read the recorded result.
          </>
        )}
      </p>
    </div>
  );
}
