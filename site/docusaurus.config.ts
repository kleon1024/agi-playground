import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  markdown: { mermaid: true },

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
  themes: ['@docusaurus/theme-mermaid'],
  title: 'Rehearse Playground',
  tagline: 'Build AI systems from infrastructure to measurable outcomes',
  favicon: 'img/favicon.ico',

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
    mermaid: {
      theme: {light: 'base', dark: 'base'},
      options: {
        fontFamily: "'Inter', ui-sans-serif, system-ui, sans-serif",
        fontSize: 14,
        flowchart: {curve: 'basis', padding: 18, nodeSpacing: 44, rankSpacing: 52, useMaxWidth: true},
        sequence: {useMaxWidth: true, actorMargin: 60},
        themeVariables: {
          primaryColor: '#e7ebff',
          primaryTextColor: '#171b19',
          primaryBorderColor: '#2457f5',
          lineColor: '#52605a',
          secondaryColor: '#e5f5ea',
          tertiaryColor: '#ffffff',
          mainBkg: '#f7f8f4',
          nodeBorder: '#d9ddd7',
          clusterBkg: '#fffdf8',
          clusterBorder: '#d9ddd7',
          edgeLabelBackground: '#ffffff',
          titleColor: '#171b19',
          fontSize: '14px',
        },
      },
    },

    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'light',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'Rehearse',
      logo: {
        alt: 'Rehearse',
        src: 'img/logo.svg',
        href: 'https://rehearse.maestro.onl',
        target: '_self',
      },
      items: [
        {
          to: '/',
          label: 'Playground',
          position: 'left',
        },
        {
          href: 'https://rehearse.maestro.onl/practice',
          label: 'Practice',
          position: 'right',
        },
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
