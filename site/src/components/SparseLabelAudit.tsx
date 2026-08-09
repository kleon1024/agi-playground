import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'aggregate',
    carries: 'buy AUC 0.769',
    label: 'Aggregate AUC',
    owns: 'The single number the dashboard ships: one AUC over the whole test cohort.',
    handoff: 'Looks decided — but it is a weighted average of slices with very different label density.',
  },
  {
    id: 'density',
    carries: 'a per-slice report',
    label: 'Label-density report',
    owns: 'Counting positives per slice: head 30/659 (0.0455), cold-user 21/681 (0.0308), cold-item 2/260 (0.0077).',
    handoff: 'The cold-item slice has a handful of positives — too few to decide anything alone.',
  },
  {
    id: 'intervals',
    carries: 'bootstrap 5-95%',
    label: 'Interval read',
    owns: 'Bootstrapping per-slice buy AUC: cold-item 0.773 with a 0.500-0.957 interval that spans chance.',
    handoff: 'The number that ships is a head-and-cold-user number; the cold-item slice cannot stand on its own.',
  },
  {
    id: 'gate',
    carries: 'a different signal',
    label: 'Gate the sparse slice',
    owns: 'Switching the cold-item slice to a surrogate/exposure/content signal instead of a dense AUC claim.',
    handoff: 'Report per slice with its interval, and do not let the aggregate claim density the sparse slice never had.',
  },
];

export default function SparseLabelAudit(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One AUC, three label densities"
      question="Why is the aggregate AUC a dense-slice number?"
      steps={STEPS}
      loop="The aggregate buy AUC is 0.769, but the cold-item slice carries two positives and its 5-95% interval spans chance. The verdict of the recorded audit is that the number that ships is a head-and-cold-user number: report per slice with its interval, and gate the cold-item slice on a different signal — surrogate, exposure, or content."
    />
  );
}
