// Sync every skill under ../skills into the site's content collection.
//
// Runs before `astro dev` and `astro build` (see package.json). The output is
// gitignored; the skill directories are the only source of truth. For each
// skills/<name>/ this writes:
//
//   src/content/docs/<name>/index.md              from SKILL.md
//   src/content/docs/<name>/references/<file>.md  from references/*.md
//   src/content/docs/<name>/cli.md                from `python3 scripts/*.py --help`
//   src/content/docs/<name>/templates.md          from assets/templates/*.md
//   src/data/skills.json                          name + description per skill (landing cards)
//
// Rules the sync follows so the site never lies about the skill:
//   * Every page carries an `editUrl` pointing at its real source file on
//     GitHub (or `editUrl: false` for generated pages), so "Edit this page"
//     never lands on a generated copy.
//   * Relative markdown links between skill files are rewritten to
//     root-relative page URLs under BASE (from site.constants.mjs), which the
//     links validator checks on every build. Links to files that are not
//     pages (scripts, templates) go to GitHub.
//   * References appear in the sidebar in the order SKILL.md first links
//     them; the skill's own reading order is the site's order.

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, posix } from 'node:path';
import { fileURLToPath } from 'node:url';
import { BASE, REPO as GITHUB } from '../site.constants.mjs';

const SITE_DIR = dirname(dirname(fileURLToPath(import.meta.url)));
const SKILLS_DIR = join(SITE_DIR, '..', 'skills');
const DOCS_DIR = join(SITE_DIR, 'src', 'content', 'docs');
const DATA_FILE = join(SITE_DIR, 'src', 'data', 'skills.json');

const MARKDOWN_LINK = /\]\(([^)\s]+)\)/g;

// ---------------------------------------------------------------------------
// Markdown helpers
// ---------------------------------------------------------------------------

/** Split a markdown file into { frontmatter: Map, body }. Flat `key: value` only; that is all the skills use. */
function splitFrontmatter(text) {
  const frontmatter = new Map();
  if (!text.startsWith('---\n')) return { frontmatter, body: text };
  const end = text.indexOf('\n---', 4);
  if (end === -1) return { frontmatter, body: text };
  for (const line of text.slice(4, end).split('\n')) {
    const match = /^([A-Za-z_-]+):\s*(.*)$/.exec(line);
    if (match) frontmatter.set(match[1], match[2].replace(/^["']|["']$/g, ''));
  }
  return { frontmatter, body: text.slice(end + 4).replace(/^\n+/, '') };
}

/** Remove the first H1 and return { title, body }. Starlight renders the title itself. */
function liftTitle(body, fallback) {
  const match = /^# (.+)\n+/m.exec(body);
  if (!match || body.indexOf(match[0]) !== 0) return { title: fallback, body };
  return { title: match[1].trim(), body: body.slice(match[0].length) };
}

const yaml = (value) => JSON.stringify(value);

function titleCase(slug) {
  return slug.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');
}

// ---------------------------------------------------------------------------
// Link rewriting
// ---------------------------------------------------------------------------

/**
 * Rewrite the relative links in `body`, which came from `sourcePath` (relative
 * to the skill root). `pages` maps source paths to page paths (relative to the
 * docs root, trailing slash); the result is a root-relative URL under BASE.
 */
function rewriteLinks(body, sourcePath, pages, skillName) {
  return body.replace(MARKDOWN_LINK, (whole, target) => {
    if (/^(https?:|mailto:|#|\/)/.test(target) || target.includes('<')) return whole;
    const [pathPart, anchor] = target.split('#');
    if (!pathPart) return whole;
    const resolved = posix.normalize(posix.join(posix.dirname(sourcePath), pathPart));
    const suffix = anchor ? `#${anchor}` : '';
    if (pages.has(resolved)) return `](${BASE}/${pages.get(resolved)}${suffix})`;
    // Not a page (a script, a template, an asset): send the reader to GitHub,
    // but only if the file exists. A link to nothing is a broken link in the
    // skill itself, and the build must say so rather than hide it behind a URL.
    if (!existsSync(join(SKILLS_DIR, skillName, resolved))) {
      console.error(`sync-skills: ${skillName}/${sourcePath} links to '${target}', which does not exist in the skill`);
      process.exitCode = 1;
      return whole;
    }
    return `](${GITHUB}/blob/main/skills/${skillName}/${resolved}${suffix})`;
  });
}

// ---------------------------------------------------------------------------
// Generated pages
// ---------------------------------------------------------------------------

function cliPage(skillDir, skillName) {
  const scriptsDir = join(skillDir, 'scripts');
  if (!existsSync(scriptsDir)) return null;
  const scripts = readdirSync(scriptsDir).filter((f) => f.endsWith('.py')).sort();
  if (scripts.length === 0) return null;

  const help = (script, ...args) => {
    try {
      return execFileSync('python3', [join(scriptsDir, script), ...args, '--help'], { encoding: 'utf8' }).trimEnd();
    } catch (error) {
      return `(could not run \`${script} ${args.join(' ')} --help\`: ${error.message.split('\n')[0]})`;
    }
  };

  const sections = [
    `---\ntitle: CLI\ndescription: The command line that ships with the ${skillName} skill, as printed by --help.\neditUrl: false\nsidebar:\n  order: 998\n---\n`,
    `This page is generated from the CLI's own \`--help\` output on every build, so it cannot drift from the code. The scripts live in [\`scripts/\`](${GITHUB}/tree/main/skills/${skillName}/scripts) and need only Python 3.9 or newer.\n`,
  ];
  for (const script of scripts) {
    const top = help(script);
    sections.push(`## ${script}\n\n\`\`\`text\n${top}\n\`\`\`\n`);
    // argparse prints subcommands as `{new,move,list}` on the usage line.
    const match = /\{([a-z0-9,-]+)\}/.exec(top);
    if (match) {
      for (const sub of match[1].split(',')) {
        sections.push(`### ${script} ${sub}\n\n\`\`\`text\n${help(script, sub)}\n\`\`\`\n`);
      }
    }
  }
  return sections.join('\n');
}

function templatesPage(skillDir, skillName) {
  const templatesDir = join(skillDir, 'assets', 'templates');
  if (!existsSync(templatesDir)) return null;
  const files = readdirSync(templatesDir).filter((f) => f.endsWith('.md')).sort();
  if (files.length === 0) return null;
  const sections = [
    `---\ntitle: Templates\ndescription: The files the ${skillName} skill writes, exactly as they ship.\neditUrl: false\nsidebar:\n  order: 999\n---\n`,
    `Everything the CLI writes into a project comes from these templates (\`$variables\` are filled at creation). They live in [\`assets/templates/\`](${GITHUB}/tree/main/skills/${skillName}/assets/templates).\n`,
  ];
  for (const file of files) {
    const text = readFileSync(join(templatesDir, file), 'utf8').trimEnd();
    // A four-backtick fence, because the templates themselves contain fences.
    sections.push(`## ${file}\n\n\`\`\`\`md\n${text}\n\`\`\`\`\n`);
  }
  return sections.join('\n');
}

// ---------------------------------------------------------------------------
// One skill
// ---------------------------------------------------------------------------

function syncSkill(skillName) {
  const skillDir = join(SKILLS_DIR, skillName);
  const outDir = join(DOCS_DIR, skillName);
  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(join(outDir, 'references'), { recursive: true });

  const skillMd = readFileSync(join(skillDir, 'SKILL.md'), 'utf8');
  const { frontmatter, body: skillBody } = splitFrontmatter(skillMd);
  const description = frontmatter.get('description') ?? '';

  const referencesDir = join(skillDir, 'references');
  const references = existsSync(referencesDir) ? readdirSync(referencesDir).filter((f) => f.endsWith('.md')).sort() : [];

  // Source path -> page URL (relative to the docs root, trailing slash).
  const pages = new Map([['SKILL.md', `${skillName}/`]]);
  for (const file of references) pages.set(`references/${file}`, `${skillName}/references/${file.replace(/\.md$/, '')}/`);

  // Sidebar order: the order SKILL.md first links each reference.
  const order = new Map();
  for (const match of skillBody.matchAll(MARKDOWN_LINK)) {
    const target = match[1].split('#')[0];
    if (target.startsWith('references/') && !order.has(target)) order.set(target, order.size + 1);
  }

  // Overview page from SKILL.md.
  const { body: overviewBody } = liftTitle(skillBody, titleCase(skillName));
  writeFileSync(
    join(outDir, 'index.md'),
    `---\ntitle: ${yaml(titleCase(skillName))}\ndescription: ${yaml(description)}\neditUrl: ${yaml(`${GITHUB}/edit/main/skills/${skillName}/SKILL.md`)}\n---\n\n` +
      rewriteLinks(overviewBody, 'SKILL.md', pages, skillName),
  );

  // One page per reference.
  for (const file of references) {
    const sourcePath = `references/${file}`;
    const raw = readFileSync(join(referencesDir, file), 'utf8');
    const { body } = splitFrontmatter(raw);
    const { title, body: pageBody } = liftTitle(body, titleCase(file.replace(/\.md$/, '')));
    const position = order.get(sourcePath) ?? order.size + 1 + references.indexOf(file);
    writeFileSync(
      join(outDir, 'references', file),
      `---\ntitle: ${yaml(title)}\neditUrl: ${yaml(`${GITHUB}/edit/main/skills/${skillName}/${sourcePath}`)}\nsidebar:\n  order: ${position}\n---\n\n` +
        rewriteLinks(pageBody, sourcePath, pages, skillName),
    );
  }

  const cli = cliPage(skillDir, skillName);
  if (cli) writeFileSync(join(outDir, 'cli.md'), cli);
  const templates = templatesPage(skillDir, skillName);
  if (templates) writeFileSync(join(outDir, 'templates.md'), templates);

  return { name: skillName, title: titleCase(skillName), description, pages: 1 + references.length + (cli ? 1 : 0) + (templates ? 1 : 0) };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const skills = readdirSync(SKILLS_DIR, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && existsSync(join(SKILLS_DIR, entry.name, 'SKILL.md')))
  .map((entry) => entry.name)
  .sort();

if (skills.length === 0) {
  console.error(`sync-skills: no skills found under ${SKILLS_DIR}`);
  process.exit(1);
}

const summary = skills.map(syncSkill);
mkdirSync(dirname(DATA_FILE), { recursive: true });
writeFileSync(DATA_FILE, JSON.stringify(summary.map(({ name, title, description }) => ({ name, title, description })), null, 2) + '\n');

for (const skill of summary) console.log(`sync-skills: ${skill.name} -> ${skill.pages} pages`);
if (process.exitCode) {
  console.error('sync-skills: a skill contains a link to a file that does not exist; fix the skill, not the site');
  process.exit(process.exitCode);
}
