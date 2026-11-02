import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const html = await readFile('dist/index.html', 'utf8');
const embedded = JSON.parse(html.match(/<script id="snapshot" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const feed = JSON.parse(await readFile('dist/briefing.json', 'utf8'));
assert.deepEqual(feed, embedded, 'Notification feed must match the deployed page');
const expected = JSON.parse(await readFile('data.json', 'utf8'));
expected.refresh = JSON.parse(await readFile('refresh-status.json', 'utf8'));
assert.deepEqual(feed, expected);
for (const edition of feed.editions) {
  for (const id of edition.articleIds) {
    assert.ok(feed.articles.some(article => article.id === id), `Missing article ${id}`);
  }
}
console.log('Verified feed equals page snapshot and all edition article IDs resolve.');
