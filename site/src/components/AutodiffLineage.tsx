/** The lineage behind `.backward()`, on a scaled axis. Dates and claims come
 *  from foundations/03-backpropagation's own cited history; nothing is added. */
import React from 'react';
import Timeline, { Moment } from './timeline/Timeline';

const MOMENTS: Moment[] = [
  {
    year: 1970,
    label: 'Reverse-mode autodiff is described',
    source: "Seppo Linnainmaa, master's thesis, University of Helsinki (1970)",
    what:
      'The first published description of accumulating local derivatives through a '
      + 'computational graph in reverse — the exact mechanism this chapter implements, '
      + 'written under the general study of automatic differentiation rather than neural networks.',
  },
  {
    year: 1986,
    label: 'The same mechanism is pointed at neural networks',
    source: 'Rumelhart, Hinton and Williams, "Learning representations by back-propagating errors" (Nature, 1986)',
    what:
      'Applies reverse-mode differentiation specifically to training multi-layer neural '
      + 'networks. This is the paper that gave the technique the name most people know it by.',
  },
  {
    year: 2010,
    label: 'A library differentiates the graph for you',
    source: 'Theano, Université de Montréal (first released 2010)',
    what:
      'An early widely-used library that builds a symbolic computation graph and '
      + 'differentiates it automatically, ahead of the boom that made this a default '
      + 'expectation rather than a research tool.',
  },
  {
    year: 2015,
    label: 'Define-by-run: the graph is built as the code runs',
    source: 'Chainer (Preferred Networks, 2015) and autograd (HIPS, 2015)',
    what:
      'Popularize building the graph dynamically as ordinary code executes — exactly how '
      + 'the Value class above works — rather than requiring a separate symbolic '
      + 'graph-construction step first.',
  },
  {
    year: 2017,
    label: 'Define-by-run becomes the default',
    source: 'PyTorch, Meta (first released 2017)',
    what:
      'Adopts define-by-run autodiff as its default execution model, which is why the '
      + 'first training loop can call .backward() on ordinary Python control flow with no '
      + 'separate graph-compilation step.',
  },
];

export default function AutodiffLineage(): React.ReactElement {
  return (
    <Timeline
      moments={MOMENTS}
      lead={
        'Select an entry to see what it made possible that the one before it did not. '
        + 'The spacing is the point: the distance between two entries is the years between them.'
      }
      close={
        'The mechanism came first and waited. Sixteen years passed before anyone pointed '
        + 'reverse-mode differentiation at a neural network, and another twenty-four before a '
        + 'library made it something you never have to think about. Nothing in the derivation '
        + 'changed across that span — what changed is who had to write the backward pass.'
      }
    />
  );
}
