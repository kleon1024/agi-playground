# Rehearse Playground site

The Docusaurus site renders the repository curriculum at
`/playground`. Source lessons remain in the repository root; `sync-docs.py`
copies them into the ignored `site/docs/` build directory and converts
`<!-- interactive: ComponentName -->` markers into React imports.

Use the repository sources for content changes. Do not edit `site/docs/`.

```bash
npm install
npm run start
npm run typecheck
npm run build
```

`prestart` and `prebuild` run the sync step automatically. The shared visual
contract lives in `src/css/brand.css` and `src/css/widgets.css`.
