// One guard per input or analysis stream. Invalidating prevents an older async
// result from changing UI state; it does not claim to cancel the underlying work.
export function createRequestGuard() {
  let generation = 0;
  return {
    begin: () => ++generation,
    invalidate: () => { generation += 1; },
    isCurrent: (request: number) => request === generation,
  };
}
