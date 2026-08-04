/** Consistent hashing, from web-cache hot spots to shard placement.
 *  Dates and claims come from infra/02-storage's own cited history. */
import React from 'react';
import Timeline, { Moment } from './timeline/Timeline';

const MOMENTS: Moment[] = [
  {
    year: 1997,
    label: 'A ring, to relieve web-cache hot spots',
    source: 'Karger et al., "Consistent Hashing and Random Trees" (STOC 1997)',
    what:
      'Introduces consistent hashing to relieve hot spots in web caching — the mechanism '
      + "behind Akamai's original CDN request routing. It predates distributed storage "
      + 'entirely.',
  },
  {
    year: 2007,
    label: 'The ring bounds remap cost for key-value storage',
    source: 'DeCandia et al., Dynamo (2007)',
    what:
      'Adapts the same ring construction specifically to bound the remap-on-resize cost this '
      + 'chapter measures for key-value storage placement.',
  },
  {
    year: 2008,
    label: "Dynamo's ring, on a different storage engine",
    source: 'Cassandra (2008)',
    what:
      "Inherits Dynamo's ring directly — the same \"who owns which shard\" question this "
      + "chapter's core/ answers, under a different storage engine.",
  },
];

export default function ConsistentHashLineage(): React.ReactElement {
  return (
    <Timeline
      moments={MOMENTS}
      lead={
        'Select an entry to see what it carried forward. The first gap is a decade; the second '
        + 'is a year.'
      }
      close={
        'The placement rule this chapter implements was solved once, for a different problem, '
        + 'and then adopted twice in quick succession as storage systems hit the same constraint. '
        + 'That shape — a long wait, then two adoptions in consecutive years — is what it looks '
        + 'like when an existing result turns out to answer a question a new field is asking.'
      }
    />
  );
}
