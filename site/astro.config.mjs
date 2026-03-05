import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://mlorentedev.github.io',
  base: '/pdf-modifier-mcp',
  integrations: [
    starlight({
      title: 'pdf-modifier-mcp',
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/mlorentedev/pdf-modifier-mcp',
        },
      ],
      sidebar: [
        { label: 'Home', slug: '' },
        { label: 'Getting Started', slug: 'getting-started' },
      ],
    }),
  ],
});
