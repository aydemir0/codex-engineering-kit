import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../src/index.ts', import.meta.url), 'utf8');
assert.match(source, /export function add/);
assert.match(source, /return left \+ right/);
console.log('sample smoke test passed');
