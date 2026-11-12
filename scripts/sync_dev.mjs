import { createHash } from 'node:crypto';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const USERNAME = 'cablefam_fiber_optic';
const normalized = text => text.replace(/\r\n/g, '\n').trim();
const hash = text => createHash('sha256').update(text).digest('hex');

export function parseSource(raw) {
  const text = normalized(raw.replace(/^\uFEFF/, ''));
  if (!text.startsWith('# ')) throw Error('Article must begin with an H1 title');
  const newline = text.indexOf('\n');
  if (newline < 0) throw Error('Article body is missing');
  const title = text.slice(2, newline).trim();
  const body = text.slice(newline).trim();
  const links = [...body.matchAll(/\]\((https:\/\/cablefam\.com\/[^\s)]+)(?:\s+"[^"]*")?\)/g)].map(x => x[1]);
  if (!title || !body || !links.length) throw Error('Title, body or Cablefam hyperlink missing');
  return { title, body, links, sha256: hash(JSON.stringify({ title, body })) };
}

function remoteHash(post) {
  // The legacy publisher included the H1 in body_markdown; ignore that duplicate title.
  let body = normalized(post.body_markdown || '');
  const heading = '# ' + post.title;
  if (body === heading || body.startsWith(heading + '\n')) body = body.slice(heading.length).trim();
  return hash(JSON.stringify({ title: post.title, body }));
}

function validatePost(post, id) {
  if (post.id !== Number(id) || post.user?.username !== USERNAME || !post.published_at
      || !post.url?.startsWith('https://dev.to/' + USERNAME + '/')) {
    throw Error('DEV article ID, owner or published status mismatch');
  }
}

function verifyContent(post, source) {
  if (remoteHash(post) !== source.sha256) throw Error('DEV content readback mismatch; inspect saved ID before retrying');
  for (const link of source.links) {
    if (!(post.body_html || '').includes('href="' + link.replaceAll('&', '&amp;') + '"')
        && !(post.body_html || '').includes('href="' + link + '"')) {
      throw Error('DEV Cablefam hyperlink readback mismatch');
    }
  }
}

export async function syncArticle(key, source, state, api, save, checkOnly = false) {
  let entry = state.articles[key];
  let post;
  let mode = 'unchanged';
  if (entry) {
    post = await api('GET', '/articles/' + entry.id);
    validatePost(post, entry.id);
    if (entry.url !== post.url) throw Error('Mapped DEV URL changed; inspect mapping');
    const current = remoteHash(post);
    if (current !== source.sha256) {
      if (checkOnly) throw Error('Check only: article differs; nothing published');
      if (!entry.remote_sha256 || current !== entry.remote_sha256) {
        throw Error('Remote article changed outside GitHub; reconcile before updating');
      }
      post = await api('PUT', '/articles/' + entry.id,
        { article: { title: source.title, body_markdown: source.body, published: true } });
      validatePost(post, entry.id);
      mode = 'updated';
    }
  } else {
    if (checkOnly) throw Error('Check only: new article is unmapped; nothing published');
    // Recover a successful POST whose ID was not committed. Never blindly repeat creation.
    const owned = await api('GET', '/articles/me/all?per_page=1000');
    if (!Array.isArray(owned) || owned.length >= 1000) throw Error('Article list incomplete; creation stopped');
    const matches = owned.filter(p => p.title === source.title);
    if (matches.length > 1) throw Error('Duplicate DEV titles; map the intended ID explicitly');
    if (matches.length) {
      post = await api('GET', '/articles/' + matches[0].id);
      validatePost(post, matches[0].id);
      verifyContent(post, source);
      mode = 'adopted';
    } else {
      post = await api('POST', '/articles',
        { article: { title: source.title, body_markdown: source.body, published: true } });
      if (!Number.isSafeInteger(post.id) || post.id <= 0) throw Error('DEV did not return an article ID; inspect DEV before retrying');
      mode = 'created';
    }
    entry = state.articles[key] = { id: post.id, url: post.url };
    await save(); // Persist the ID even if public verification fails.
  }
  if (mode === 'created' || mode === 'updated') post = await api('GET', '/articles/' + entry.id);
  validatePost(post, entry.id);
  verifyContent(post, source);
  if (!checkOnly) {
    state.articles[key] = { id: post.id, url: post.url, source_sha256: source.sha256, remote_sha256: remoteHash(post) };
    await save();
  }
  return { article: key, mode, id: post.id, url: post.url, cablefam_links: source.links.length };
}

export function createApi(key) {
  return async (method, path, payload) => {
    let response;
    try {
      response = await fetch('https://dev.to/api' + path, {
        method, headers: { 'api-key': key, Accept: 'application/vnd.forem.api-v1+json', 'Content-Type': 'application/json' },
        ...(payload ? { body: JSON.stringify(payload) } : {}), signal: AbortSignal.timeout(25000),
      });
    } catch {
      throw Error('DEV request did not complete; inspect existing articles before retrying any creation');
    }
    if (!response.ok) throw Error('DEV API HTTP ' + response.status + '; no automatic retry');
    return response.json();
  };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.some(x => x !== '--check')) throw Error('Only --check is supported');
  const checkOnly = args.includes('--check');
  const secret = process.env.DEV_API_KEY;
  if (!secret) throw Error('Missing DEV_API_KEY; nothing published');
  const api = createApi(secret);
  const user = await api('GET', '/users/me');
  if (user.username !== USERNAME) throw Error('DEV_API_KEY belongs to the wrong account');
  const statePath = resolve(ROOT, 'dev/publish-state.json');
  const state = JSON.parse(await readFile(statePath, 'utf8'));
  if (state.username !== USERNAME || !state.articles || Array.isArray(state.articles)) throw Error('Invalid DEV state');
  const ids = Object.values(state.articles).map(x => x.id);
  if (ids.some(x => !Number.isSafeInteger(x) || x <= 0) || new Set(ids).size !== ids.length) throw Error('Missing or duplicate mapped DEV IDs');
  const directory = resolve(ROOT, 'dev/articles');
  const files = (await readdir(directory)).filter(x => x.endsWith('.md')).sort();
  const sources = new Map();
  for (const file of files) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*\.md$/.test(file)) throw Error('Use a stable lowercase article filename');
    sources.set(file.slice(0, -3), parseSource(await readFile(resolve(directory, file), 'utf8')));
  }
  if (!sources.size || Object.keys(state.articles).some(key => !sources.has(key))) throw Error('Mapped source missing; article deletion is not automatic');
  const titles = [...sources.values()].map(x => x.title);
  if (new Set(titles).size !== titles.length) throw Error('Duplicate source titles');
  const save = () => writeFile(statePath, JSON.stringify(state, null, 2) + '\n', 'utf8');
  for (const [key, source] of sources) console.log(JSON.stringify(await syncArticle(key, source, state, api, save, checkOnly)));
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
