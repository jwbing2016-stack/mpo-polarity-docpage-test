import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSource, syncArticle } from '../scripts/sync_dev.mjs';

const raw = '# LC guide\n\nOrder details and [contact](https://cablefam.com/contact-us.html).';
const source = parseSource(raw);
const post = (id = 11) => ({ id, title: source.title, body_markdown: source.body,
  body_html: '<a href="https://cablefam.com/contact-us.html">contact</a>',
  url: 'https://dev.to/cablefam_fiber_optic/lc-guide-x',
  published_at: '2026-11-12T00:00:00Z', user: { username: 'cablefam_fiber_optic' } });
const initial = () => ({ articles: { lc: { id: 11, url: post().url } } });
const save = async () => {};

test('existing article is adopted without any publication request; legacy H1 is preserved remotely', async () => {
  const state = initial();
  const calls = [];
  const api = async (method, path) => { calls.push([method, path]); return { ...post(), body_markdown: raw }; };
  const result = await syncArticle('lc', source, state, api, save);
  assert.equal(result.mode, 'unchanged');
  assert.deepEqual(calls, [['GET', '/articles/11']]);
  assert.equal(state.articles.lc.source_sha256, source.sha256);
});

test('each article updates its own ID and leaves the other mapping unchanged', async () => {
  const state = initial();
  state.articles.mpo = { id: 22, url: 'preserve' };
  await syncArticle('lc', source, state, async () => post(), save);
  const changed = parseSource(raw.replace('Order details', 'New order details'));
  const calls = [];
  const api = async (method, path, payload) => { calls.push([method, path]);
    if (method === 'PUT') { assert.equal(payload.article.body_markdown, changed.body); return post(); }
    return calls.some(x => x[0] === 'PUT') ? { ...post(), body_markdown: changed.body } : post(); };
  assert.equal((await syncArticle('lc', changed, state, api, save)).mode, 'updated');
  assert.deepEqual(calls, [['GET', '/articles/11'], ['PUT', '/articles/11'], ['GET', '/articles/11']]);
  assert.deepEqual(state.articles.mpo, { id: 22, url: 'preserve' });
});

test('new source creates once and saves its new ID before verification', async () => {
  const state = { articles: {} }; let saves = 0; const methods = [];
  const api = async (method) => { methods.push(method); if (method === 'POST') return post(33);
    return methods.includes('POST') ? post(33) : []; };
  const result = await syncArticle('new', source, state, api, async () => { saves++; assert.equal(state.articles.new.id, 33); });
  assert.equal(result.mode, 'created'); assert.equal(saves, 2);
  assert.deepEqual(methods, ['GET', 'POST', 'GET']);
});

test('rerun after an uncommitted POST recovers by title without another POST', async () => {
  const methods = []; const state = { articles: {} };
  const result = await syncArticle('new', source, state, async (method, path) => {
    methods.push(method); return path.startsWith('/articles/me/all') ? [post()] : post();
  }, save);
  assert.equal(result.mode, 'adopted'); assert.deepEqual(methods, ['GET', 'GET']);
});

test('wrong owner, external edits and ambiguous titles stop without writing', async () => {
  const state = initial();
  await assert.rejects(syncArticle('lc', source, state, async () => ({ ...post(), user: { username: 'other' } }), save), /owner/);
  await syncArticle('lc', source, state, async () => post(), save);
  await assert.rejects(syncArticle('lc', source, state, async () => ({ ...post(), body_markdown: 'manual edit' }), save), /outside GitHub/);
  await assert.rejects(syncArticle('new', source, { articles: {} }, async () => [post(), post(12)], save), /Duplicate DEV/);
});

test('check-only never creates, updates or persists state', async () => {
  let writes = 0; const state = initial();
  await syncArticle('lc', source, state, async () => post(), async () => { writes++; }, true);
  assert.equal(writes, 0); assert.equal(state.articles.lc.source_sha256, undefined);
  await assert.rejects(syncArticle('new', source, state, async () => { throw Error('must not call API'); }, save, true), /Check only/);
  await assert.rejects(syncArticle('lc', source, state, async () => ({ ...post(), body_markdown: 'different' }), save, true), /Check only/);
});

test('missing website hyperlinks fail before publication', () => {
  assert.throws(() => parseSource('# Heading\n\nNo website link'), /hyperlink/);
});
