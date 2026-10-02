export const MAX_ARTICLE_CHARACTERS = 100_000;

type TextUpload = Pick<File, "name" | "size" | "arrayBuffer">;

export async function readArticleUpload(file: TextUpload): Promise<string> {
  if (!file.name.toLowerCase().endsWith(".txt")) {
    throw new Error("Choose a UTF-8 .txt file. PDF and Word uploads are not supported.");
  }
  // Four bytes is the largest UTF-8 representation of one Unicode code point.
  if (file.size > MAX_ARTICLE_CHARACTERS * 4) {
    throw new Error("This file is too large. Upload an article with 100,000 characters or fewer.");
  }
  let text: string;
  try {
    // Preserve the exact decoded text, including newlines, whitespace, and BOM.
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(await file.arrayBuffer());
  } catch {
    throw new Error("This file could not be read as UTF-8 text. Save it as a UTF-8 .txt file and try again.");
  }
  if (Array.from(text).length > MAX_ARTICLE_CHARACTERS) {
    throw new Error("This article is too long. Upload an article with 100,000 characters or fewer.");
  }
  if (!text.trim()) throw new Error("This file is empty. Choose a .txt file containing article text.");
  return text;
}
