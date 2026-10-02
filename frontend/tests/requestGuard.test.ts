import assert from "node:assert/strict";
import test from "node:test";
import { createRequestGuard } from "../lib/requestGuard";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

test("invalidating on input, upload, mode change, or Clear prevents a pending result from publishing", async () => {
  for (const change of ["edit input", "upload new input", "change mode", "Clear"]) {
    const guard = createRequestGuard();
    const pending = deferred<string>();
    const sequence = guard.begin();
    let result: string | null = null;
    const completion = pending.promise.then(value => { if (guard.isCurrent(sequence)) result = value; });
    guard.invalidate();
    pending.resolve("article A");
    await completion;
    assert.equal(result, null, change);
  }
});

test("a late A result cannot replace a newer B result", async () => {
  const guard = createRequestGuard();
  const first = deferred<string>();
  const second = deferred<string>();
  let result: string | null = null;
  const analyze = (pending: ReturnType<typeof deferred<string>>) => {
    const sequence = guard.begin();
    return pending.promise.then(value => { if (guard.isCurrent(sequence)) result = value; });
  };
  const a = analyze(first);
  guard.invalidate(); // Editing/uploading B invalidates A before submitting B.
  const b = analyze(second);
  second.resolve("article B");
  await b;
  first.resolve("article A");
  await a;
  assert.equal(result, "article B");
});

test("a late error/finalizer cannot overwrite newer request state", async () => {
  const guard = createRequestGuard();
  const pending = deferred<string>();
  const sequence = guard.begin();
  let error: string | null = null;
  let loading = true;
  const completion = pending.promise.catch(reason => {
    if (guard.isCurrent(sequence)) error = reason.message;
  }).finally(() => {
    if (guard.isCurrent(sequence)) loading = false;
  });
  guard.begin();
  pending.reject(new Error("old request failed"));
  await completion;
  assert.equal(error, null);
  assert.equal(loading, true);
});

test("an upload stream has independent generation and can be invalidated by typing/Clear", () => {
  const uploads = createRequestGuard();
  const analyses = createRequestGuard();
  const fileRead = uploads.begin();
  const analysis = analyses.begin();
  uploads.invalidate();
  assert.equal(uploads.isCurrent(fileRead), false);
  assert.equal(analyses.isCurrent(analysis), true);
  const newestRead = uploads.begin();
  assert.equal(uploads.isCurrent(newestRead), true);
});
