import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'featurize', carries: 'one SMILES string', label: 'Featurize', owns: 'Turning one molecule into two parallel representations from the same SMILES string.', handoff: 'Ten fixed RDKit descriptors for the baseline path; a character-level token sequence for the trained-model path.' },
  { id: 'descriptor-path', carries: 'standardized descriptors', label: 'Descriptor baseline', owns: 'Logistic regression (batch gradient descent, no sklearn) fit on the ten descriptors, standardized against the train split’s own mean/std.', handoff: 'A baseline test ROC-AUC, one per seed.' },
  { id: 'model-path', carries: 'a token sequence', label: 'Trained model', owns: 'A 4-block causal transformer — Config/Block/RMSNorm reused unmodified from mission 01’s pretraining core — reading the character-level SMILES sequence.', handoff: 'A trained-model test ROC-AUC, one per seed.' },
  { id: 'held-out-eval', carries: 'two ROC-AUC values', label: 'Held-out eval', owns: 'The scaffold split stage 00 measured at 0.0 train/test overlap — no near-duplicate structure crosses sides.', handoff: 'Three seeds’ worth of test ROC-AUC for each path.' },
  { id: 'compare', carries: 'a verdict', label: 'Compare', owns: 'Whether the trained model’s mean beats the descriptor baseline’s mean by more than either one’s own seed-to-seed spread.', handoff: 'A result: beats, or an honest no-result — never a gap smaller than the spread rounded into a claim.' },
];

export default function MoleculePropertyComparison(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Descriptor baseline vs. trained model"
      question="Does the gap beat the seed spread, or is it noise?"
      steps={STEPS}
      loop="On SR-MMP the descriptor baseline wins outright: 0.8142 mean (spread 0.0010) against the trained model's 0.7312 mean (spread 0.0159) — training one was not worth it for this endpoint. On the second, more imbalanced endpoint (NR-PPAR-gamma), the two paths land within 1/17th of the trained model's own seed spread — a genuine no-result, reported as inconclusive rather than rounded into a claim either way."
    />
  );
}
