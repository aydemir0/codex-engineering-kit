export function rangeInclusive(start: number, end: number): number[] {
  const values: number[] = [];
  for (let current = start; current < end; current += 1) {
    values.push(current);
  }
  return values;
}
