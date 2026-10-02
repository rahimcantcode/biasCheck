import assert from "node:assert/strict";
import test from "node:test";
import { MAX_ARTICLE_CHARACTERS, readArticleUpload } from "../lib/upload";

function file(text: string, name = "article.txt") {
  const bytes = new TextEncoder().encode(text);
  return { name, size: bytes.byteLength, arrayBuffer: async () => bytes.buffer };
}

test("UTF-8 text upload preserves original text, emoji, CRLF, whitespace, and BOM", async () => {
  const text = "\uFEFF  🐈 my cafe\u0301 is pretty\r\n\r\nand taxing the rich is good\t\r\n";
  assert.equal(await readArticleUpload(file(text, "ARTICLE.TXT")), text);
});

test("uploads are bounded by Unicode code points rather than UTF-16 code units", async () => {
  const text = "🐈".repeat(MAX_ARTICLE_CHARACTERS);
  assert.equal(await readArticleUpload(file(text)), text);
  await assert.rejects(readArticleUpload(file("a".repeat(MAX_ARTICLE_CHARACTERS + 1))), /too long/);
});

test("oversize files are rejected before reading", async () => {
  let read = false;
  await assert.rejects(readArticleUpload({
    name: "large.txt", size: MAX_ARTICLE_CHARACTERS * 4 + 1,
    arrayBuffer: async () => { read = true; return new ArrayBuffer(0); },
  }), /too large/);
  assert.equal(read, false);
});

test("PDF, Word, empty, and invalid UTF-8 uploads have actionable errors", async () => {
  await assert.rejects(readArticleUpload(file("content", "article.pdf")), /PDF and Word uploads are not supported/);
  await assert.rejects(readArticleUpload(file("content", "article.docx")), /PDF and Word uploads are not supported/);
  await assert.rejects(readArticleUpload(file("\r\n  \t")), /empty/);
  const invalid = Uint8Array.from([0xc3, 0x28]);
  await assert.rejects(readArticleUpload({ name: "invalid.txt", size: 2, arrayBuffer: async () => invalid.buffer }), /UTF-8/);
});

test("file read failure does not return partial text", async () => {
  await assert.rejects(readArticleUpload({
    name: "article.txt", size: 20, arrayBuffer: async () => { throw new Error("Read failed"); },
  }), /could not be read/);
});
