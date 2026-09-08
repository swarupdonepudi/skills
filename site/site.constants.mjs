// The three facts the site is built around, in one place. astro.config.mjs and
// scripts/sync-skills.mjs both import them, so a custom domain later is a
// change to BASE here (to '') plus a CNAME file in public/.
export const SITE = 'https://swarupdonepudi.github.io';
export const BASE = '/skills';
export const REPO = 'https://github.com/swarupdonepudi/skills';
