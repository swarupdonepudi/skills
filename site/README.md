# Site

The documentation site for the skills in this repository, published to [swarupdonepudi.github.io/skills](https://swarupdonepudi.github.io/skills/) by `.github/workflows/pages.yml` on every push to `main`.

Nothing in `site/` is a source of truth. `scripts/sync-skills.mjs` runs before `dev` and `build`, discovers every `../skills/*/` directory, and writes the pages into `src/content/docs/<skill>/` (gitignored): the skill's `SKILL.md` as the overview, each reference as a page, a CLI page generated from `--help`, and a Templates page. To change the docs, edit the skill. The only hand-written page is the landing page, `src/content/docs/index.mdx`.

## Run it locally

```bash
cd site
npm ci
npm run dev
```

`npm run build` runs the sync, builds to `dist/`, and fails on any broken internal link.
