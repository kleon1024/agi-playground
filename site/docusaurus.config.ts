import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import routeRedirects from './route-redirects.json';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  // KaTeX renders each formula twice — visual HTML plus MathML for screen
  // readers — and relies on its stylesheet to hide the MathML layer. Without
  // this, every equation appears twice: once typeset, once as mangled text.
  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
      type: 'text/css',
      integrity:
        'sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+',
      crossorigin: 'anonymous',
    },
  ],
  title: 'Rehearse Playground',
  tagline: 'Build AI systems from infrastructure to measurable outcomes',
  favicon: 'img/rehearse-mark.svg',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://rehearse.maestro.onl',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/playground/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'kleon1024', // Usually your GitHub org/user name.
  projectName: 'agi-playground', // Usually your repo name.

  onBrokenLinks: 'throw',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // A chapter that changes owners changes its URL. Somebody has the old one
  // bookmarked, and a search engine has it indexed, so the old one has to keep
  // working -- `onBrokenLinks: 'throw'` above only protects links inside this
  // site. The map lives in its own file so a move is a data edit, and the
  // plugin validates every `to` against the built routes, so a redirect cannot
  // silently start pointing at nothing.
  plugins: [
    [
      '@docusaurus/plugin-client-redirects',
      {redirects: routeRedirects.redirects},
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          numberPrefixParser: false,
          admonitions: true,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          // Lessons live in the curriculum repo, not here — the sync step
          // copies them in, so "edit this page" must point at the source.
          editUrl: 'https://github.com/kleon1024/agi-playground/edit/main/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'light',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      // The logo stays inside the Playground. It used to point at the
      // marketing home, so the only way back to this site's own landing page
      // was the sidebar -- and "Practice" appeared twice, once as a link and
      // once as the call to action beside it.
      title: 'Rehearse Playground',
      logo: {
        alt: 'Rehearse Playground',
        src: 'img/rehearse-mark.svg',
        href: '/',
        target: '_self',
      },
      items: [
        {
          href: 'https://rehearse.maestro.onl/pricing',
          label: 'Pricing',
          position: 'right',
        },
        {
          href: 'https://github.com/kleon1024/agi-playground',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://rehearse.maestro.onl/practice',
          label: 'Start practice',
          position: 'right',
          className: 'navbar-cta',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Project',
          items: [
            {label: 'GitHub', href: 'https://github.com/kleon1024/agi-playground'},
          ],
        },
        {
          title: 'Maestro',
          items: [
            {label: 'Studio', href: 'https://maestro.onl'},
            {label: 'Rehearse — interview practice', href: 'https://rehearse.maestro.onl'},
          ],
        },
      ],
      copyright: `Built by Maestro — Singapore AI product studio. MIT licensed.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
