// The site knows nothing about any particular skill. It discovers `../skills/*/`
// here (for the sidebar) and in scripts/sync-skills.mjs (for the pages), so a
// new skill directory in the repository appears on the site with no edits.
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { BASE, REPO, SITE } from './site.constants.mjs';

const SKILLS_DIR = new URL('../skills/', import.meta.url).pathname;

/** One sidebar group per skill: Overview, References, then CLI and Templates when the skill has them. */
function skillSidebar() {
  return readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(SKILLS_DIR, entry.name, 'SKILL.md')))
    .map((entry) => entry.name)
    .sort()
    .map((name) => {
      const has = (sub) => existsSync(join(SKILLS_DIR, name, sub));
      const items = [{ label: 'Overview', slug: name }];
      if (has('references')) items.push({ label: 'References', items: [{ autogenerate: { directory: `${name}/references` } }] });
      if (has('scripts')) items.push({ label: 'CLI', slug: `${name}/cli` });
      if (has('assets/templates')) items.push({ label: 'Templates', slug: `${name}/templates` });
      return { label: titleCase(name), items };
    });
}

function titleCase(slug) {
  return slug.split('-').map((word) => word[0].toUpperCase() + word.slice(1)).join(' ');
}

export default defineConfig({
  site: SITE,
  base: BASE,
  integrations: [
    starlight({
      title: 'Skills',
      description: 'Agent skills by Swarup Donepudi, in the Agent Skills format.',
      social: [{ icon: 'github', label: 'GitHub', href: REPO }],
      // Per-page `editUrl` (written by the sync script) points every page at
      // its real source under skills/, never at the generated copy.
      editLink: { baseUrl: `${REPO}/edit/main/skills/` },
      sidebar: skillSidebar(),
      customCss: ['./src/styles/custom.css'],
      plugins: [starlightLinksValidator()],
    }),
  ],
});
