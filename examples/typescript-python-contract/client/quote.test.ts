import { deepStrictEqual } from 'node:assert/strict';
import { test } from 'node:test';
import { quote } from './quote.ts';

test('the client receives the discounted total in cents', () => {
  deepStrictEqual(quote(3), { totalCents: 3375 });
});

test('the client preserves a service validation error', () => {
  deepStrictEqual(quote(0), { error: 'invalid-quantity' });
});
