"""Collect a tiny, unlabeled development intake, never training or test gold.

Only two explicitly reviewed revision IDs are supported. Full source snapshots
stay under an ignored data directory; the publication summary contains no body.
Pinned page revisions do not pin transcluded templates. Exact retrieved bytes
and extracted text are hashed. Human extraction and rights review are required.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

SEEDS = {
    5004396: "White House deletes Truth Social post portraying Obamas as apes",
    5013866: "Former Major League Baseball pitcher Julio Teherán retires",
}
POLICY = "https://en.wikinews.org/w/index.php?title=Wikinews:Copyright&oldid=4991371"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
MAX_BYTES = 4_000_000
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def digest(value):
    return hashlib.sha256(value).hexdigest()


class Paragraphs(HTMLParser):
    """Conservative top-level paragraphs before the first section heading.

    This deliberately does not promise a universal full-article extractor.
    Candidate source text must be visually checked before annotation.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.paragraphs, self.current = [], [], None
        self.root_depth = None
        self.root_closed = False
        self.publication_dates, self.embedded_rights = set(), set()
        self.skip_paragraph, self.stopped = False, False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.root_depth is None and tag == "div" and "mw-parser-output" in attrs.get("class", "").split():
            self.root_depth = len(self.stack)
        if attrs.get("id") == "publishDate" and attrs.get("title"):
            self.publication_dates.add(attrs["title"])
        for value in parse_qs(attrs.get("title", "")).get("rft.rights", []):
            self.embedded_rights.add(value)
        if (not self.root_closed and self.root_depth is not None
                and len(self.stack) > self.root_depth
                and tag in {"h1", "h2", "h3", "h4", "h5", "h6"}):
            self.stopped = True
        if (tag == "p" and not self.stopped and self.root_depth is not None
                and len(self.stack) == self.root_depth + 1):
            self.current, self.skip_paragraph = [], False
        if self.current is not None:
            if "published" in attrs.get("class", "").split():
                self.skip_paragraph = True
            if tag == "br":
                self.current.append(" ")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "p" and self.current is not None:
            text = re.sub(r"\s+", " ", "".join(self.current)).strip()
            if text and not self.skip_paragraph:
                self.paragraphs.append(text)
            self.current = None
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            if index == self.root_depth and tag == "div":
                self.root_closed, self.stopped, self.current = True, True, None
            del self.stack[index:]

    def handle_data(self, data):
        if self.current is not None and not any(t in self.stack for t in ("script", "style")):
            self.current.append(data)


def extract(raw, revision):
    if type(revision) is not int or revision not in SEEDS:
        raise ValueError("Only the two reviewed development revisions are supported")
    if len(raw) > MAX_BYTES:
        raise ValueError("Source snapshot exceeds bounded size")
    result = json.loads(raw.decode("utf-8"))
    page = result.get("parse", {})
    if page.get("revid") != revision or page.get("title") != SEEDS[revision]:
        raise ValueError("Source revision/title mismatch or API error")
    html = page.get("text")
    if not isinstance(html, str):
        raise ValueError("Rendered source text is missing")
    parser = Paragraphs()
    parser.feed(html)
    if len(parser.publication_dates) != 1:
        raise ValueError("Exactly one publication date is required")
    publication_date = next(iter(parser.publication_dates))
    date = datetime.strptime(publication_date, "%Y-%m-%d").date()
    if date <= datetime(2024, 12, 16).date():
        raise ValueError("Pre-transition article is outside this intake")
    body = "\n\n".join(parser.paragraphs)
    if not 100 <= len(body) <= 100_000:
        raise ValueError("No plausible article body extracted")
    text = page["title"] + "\n\n" + body
    embedded = sorted(parser.embedded_rights)
    return text, {
        "id": f"wikinews-{revision}", "title": page["title"],
        "source_revision": revision,
        "source_url": f"https://en.wikinews.org/w/index.php?oldid={revision}",
        "publication_date": publication_date, "source": "Wikinews contributors",
        "raw_response_sha256": digest(raw), "text_sha256": digest(text.encode("utf-8")),
        "text_context": "title_and_extracted_top_level_paragraphs",
        "paragraph_count": len(parser.paragraphs), "character_count": len(text),
        "word_count": len(text.split()), "split": "development", "label": None,
        "human_review_count": 0, "annotation_status": "unreviewed",
        "extraction_review_status": "pending_human_comparison_with_source",
        "rights": {
            "policy_url": POLICY, "policy_indicated_license": "CC-BY-4.0",
            "license_url": LICENSE, "embedded_rights_observed": embedded,
            "review_status": "pending_page_specific_rights_review",
            "metadata_conflict": bool(embedded and embedded != ["CC-BY 4.0"]),
            "approved_uses": [],
            "attribution": f"{page['title']} by Wikinews contributors; revision {revision}.",
            "modification_notice": "HTML stripped; title and top-level paragraphs retained; whitespace normalized; date, navigation, images, references and later sections omitted.",
        },
        "final_test_eligible": False, "training_approved": False,
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected source redirect")


def retrieve(revision):
    if type(revision) is not int or revision not in SEEDS:
        raise ValueError("Unknown source revision")
    query = urlencode(dict(action="parse", format="json", formatversion=2,
                           oldid=revision, prop="text|revid|displaytitle",
                           disableeditsection=1, disabletoc=1))
    request = Request("https://en.wikinews.org/w/api.php?" + query,
                      headers={"User-Agent": "BiasCheckResearch/0.1 (https://github.com/rahimcantcode/biasCheck)",
                               "Accept": "application/json"})
    with build_opener(NoRedirect()).open(request, timeout=30) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Source snapshot exceeds bounded size")
    return raw


def collect(output, snapshot_directory=None):
    output = Path(output)
    if output.exists():
        raise ValueError("Use a fresh output directory; source records must not be overwritten")
    prepared = []
    for revision in SEEDS:
        raw = ((Path(snapshot_directory) / f"{revision}.json").read_bytes()
               if snapshot_directory else retrieve(revision))
        text, metadata = extract(raw, revision)
        prepared.append((revision, raw, text, metadata))
    output.mkdir(parents=True)
    for revision, raw, text, metadata in prepared:
        (output / f"{revision}.json").write_bytes(raw)
        (output / f"{revision}.txt").write_text(text, encoding="utf-8")
    summary = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Unlabeled archival source intake only; not a benchmark or training corpus",
        "retrieval_mode": "saved_api_snapshots" if snapshot_directory else "live_api",
        "extraction_version": "top_level_paragraphs_before_heading_v1",
        "limitations": ["Two convenience-selected articles from one source; no class balance or representativeness",
                        "Page revision does not freeze transcluded templates; raw response hash binds actual bytes",
                        "Rights and extraction review pending; no model or human labels generated",
                        "Examples inspected by the research team are permanently development material"],
        "items": [p[3] for p in prepared], "release_approved": False,
    }
    # This local adapter is deliberately incomplete for evaluation: reviewers,
    # rights resolution, an independent corpus and a frozen protocol are absent.
    manifest = {
        "schema_version": "biascheck-dataset-intake-v1",
        "dataset_id": "wikinews-two-article-development-intake-20261003",
        "task": {"id": "article_author_framing", "version": "proposed-v1",
                 "scope": "Author framing in supplied title and extracted text; human labeling pending",
                 "label_source": "human_text_annotation"},
        "development_only": True, "final_test_eligible": False,
        "exposure_ledger": [], "records": [], "release_approved": False,
    }
    for revision, raw, text, metadata in prepared:
        manifest["records"].append({
            "id": metadata["id"], "task": "article_author_framing", "kind": "natural",
            "split": "development", "text": text, "text_sha256": metadata["text_sha256"],
            "story_group": f"provisional-wikinews-episode-{revision}", "duplicate_group": None,
            "development_only": True, "final_test_eligible": False, "label": None,
            "exposure": {"pilot": False, "training": False, "development": True,
                         "model_selection": False, "calibration": False},
            "source": {"url": metadata["source_url"], "publisher": "Wikinews contributors",
                       "acquired_at": summary["created_at"], "rights_status": "unresolved",
                       "rights_basis": "Post-transition policy and embedded metadata differ; page-specific review pending",
                       "rights_reference": POLICY, "allowed_uses": []},
            "review": {"status": "pending"},
        })
    (output / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "intake_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshots", type=Path, help="Replay saved API responses without network access")
    parser.add_argument("--public-summary", type=Path, help="Optional metadata-only publication path")
    args = parser.parse_args()
    summary = collect(args.output, args.snapshots)
    if args.public_summary:
        args.public_summary.parent.mkdir(parents=True, exist_ok=True)
        with args.public_summary.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"items": len(summary["items"]), "labeled_items": 0,
                      "rights_cleared_items": 0, "release_approved": False}))


if __name__ == "__main__":
    main()
