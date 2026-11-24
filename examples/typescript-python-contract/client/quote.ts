import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

type Quote = { totalCents: number } | { error: 'invalid-quantity' };

const service = fileURLToPath(new URL('../service/quote.py', import.meta.url));

export function quote(quantity: number): Quote {
  const result = spawnSync(process.env.CEK_EXAMPLE_PYTHON ?? 'python', [service], {
    input: JSON.stringify({ quantity }),
    encoding: 'utf8',
    timeout: 5_000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error('Quote service failed');
  const value: unknown = JSON.parse(result.stdout);
  if (typeof value === 'object' && value !== null) {
    if ('totalCents' in value && typeof value.totalCents === 'number'
        && Number.isSafeInteger(value.totalCents)) {
      return { totalCents: value.totalCents };
    }
    if ('error' in value && value.error === 'invalid-quantity') {
      return { error: value.error };
    }
  }
  throw new Error('Unexpected quote response');
}
