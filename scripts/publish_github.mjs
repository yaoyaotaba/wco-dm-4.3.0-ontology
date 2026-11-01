#!/usr/bin/env node
/**
 * Publish the project to GitHub without a system git binary.
 *
 * - Creates the repository through the GitHub REST API (idempotent).
 * - Commits with isomorphic-git, excluding WCO raw files (see .gitignore).
 * - Pushes main to the remote with the provided token.
 *
 * Usage:
 *   GH_TOKEN=... node scripts/publish_github.mjs --owner yaoyaotaba --repo wco-dm-4.3.0-ontology
 * Options:
 *   --private   create a private repository (default: public)
 *   --message   commit message
 *   --dry-run   do everything except create/push
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(__dirname);

let git;
try {
  git = await import('isomorphic-git');
  git = git.default || git;
} catch {
  console.error('isomorphic-git is required: npm install isomorphic-git');
  process.exit(1);
}

const args = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = args.indexOf('--' + name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};
const flag = name => args.includes('--' + name);

const owner = opt('owner', 'yaoyaotaba');
const repo = opt('repo', 'wco-dm-4.3.0-ontology');
const isPrivate = flag('private');
const dryRun = flag('dry-run');
const message = opt('message', 'Publish WCO DM 4.3.0 ontology knowledge base');
const token = process.env.GH_TOKEN || '';
const author = {
  name: opt('author-name', 'yaoyaotaba'),
  email: opt('author-email', `${owner}@users.noreply.github.com`),
};

const GITHUB_API = 'https://api.github.com';
const EXCLUDE = ['sources/package', 'sources/xlsx', 'node_modules', '.chrome', '__pycache__', 'npm-cache'];

function fsEntries() {
  const out = [];
  const walk = dir => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const abs = path.join(dir, entry.name);
      const rel = path.relative(ROOT, abs).split(path.sep).join('/');
      if (EXCLUDE.some(prefix => rel === prefix || rel.startsWith(prefix + '/'))) continue;
      if (entry.name === '.git') continue;
      if (entry.isDirectory()) walk(abs);
      else if (entry.isFile()) out.push(rel);
    }
  };
  walk(ROOT);
  return out.sort();
}

async function api(method, urlPath, body) {
  const res = await fetch(GITHUB_API + urlPath, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'wco-dm-ontology-publisher',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch { json = { raw: text }; }
  return { status: res.status, ok: res.ok, json };
}

async function ensureRepo() {
  const existing = await api('GET', `/repos/${owner}/${repo}`);
  if (existing.ok) {
    console.log(`repository exists: ${existing.json.html_url}`);
    return existing.json;
  }
  if (existing.status !== 404) {
    throw new Error(`cannot read repository: ${existing.status} ${JSON.stringify(existing.json).slice(0, 300)}`);
  }
  const created = await api('POST', '/user/repos', {
    name: repo,
    private: isPrivate,
    description: 'OWL 2 DL ontology, SKOS code lists, SHACL shapes and an interactive explorer for the WCO Data Model 4.3.0 (derived work).',
    homepage: 'https://datamodel.wcoomd.org/',
    auto_init: false,
    has_issues: true,
    has_wiki: false,
  });
  if (!created.ok) {
    throw new Error(`create repository failed: ${created.status} ${JSON.stringify(created.json).slice(0, 400)}`);
  }
  console.log(`repository created: ${created.json.html_url}`);
  return created.json;
}

async function commitAndPush() {
  await git.init({ fs, dir: ROOT, defaultBranch: 'main' });
  const files = fsEntries();
  for (const file of files) {
    await git.add({ fs, dir: ROOT, filepath: file });
  }
  const status = await git.statusMatrix({ fs, dir: ROOT });
  const changed = status.filter(([, head, work, stage]) => head !== 1 || work !== stage);
  if (changed.length === 0) {
    console.log('nothing to commit');
  } else {
    const sha = await git.commit({ fs, dir: ROOT, message, author });
    console.log(`committed ${changed.length} changes: ${sha}`);
  }
  const remote = `https://${token}@github.com/${owner}/${repo}.git`;
  const remotes = await git.listRemotes({ fs, dir: ROOT });
  if (remotes.some(r => r.remote === 'origin')) {
    await git.setConfig({ fs, dir: ROOT, path: 'remote.origin.url', value: remote });
  } else {
    await git.addRemote({ fs, dir: ROOT, remote: 'origin', url: remote });
  }
  const result = await git.push({
    fs,
    dir: ROOT,
    remote: 'origin',
    ref: 'main',
    force: false,
    onAuth: () => ({ username: token, password: 'x-oauth-basic' }),
  });
  console.log('push:', result.ok ? 'ok' : JSON.stringify(result.error || result));
  console.log(`files pushed: ${files.length}`);
}

async function main() {
  if (!token) {
    console.error('GH_TOKEN is not set');
    process.exit(2);
  }
  const who = await api('GET', '/user');
  if (!who.ok) throw new Error(`token rejected: ${who.status}`);
  if (who.json.login.toLowerCase() !== owner.toLowerCase()) {
    throw new Error(`token belongs to ${who.json.login}, expected ${owner}`);
  }
  console.log(`authenticated as ${who.json.login}`);
  if (dryRun) {
    console.log(`dry run: ${fsEntries().length} files would be committed`);
    return;
  }
  await ensureRepo();
  await commitAndPush();
}

main().catch(err => { console.error(err.message || err); process.exit(1); });