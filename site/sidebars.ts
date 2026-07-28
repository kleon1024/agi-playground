import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// Written by sync-docs.py. Autogeneration walked every directory, so each
// lesson's runs/, core/ and prod/ folders became nav categories and the
// sidebar read "Evidence, Evidence, Evidence" between chapters. Generating it
// alongside the pages keeps the tree to chapters only, in curriculum order.
import generated from './sidebars.generated.json';

const sidebars: SidebarsConfig = {
  curriculum: generated as SidebarsConfig['curriculum'],
};

export default sidebars;
