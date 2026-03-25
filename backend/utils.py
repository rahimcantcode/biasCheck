import re
from typing import List, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
try:
    from .config import get_settings
except ImportError:  # pragma: no cover - supports `uvicorn main:app` from backend/
    from config import get_settings


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)

def looks_like_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def fetch_article_text(url: str) -> str:
    response = requests.get(
        url,
        timeout=get_settings().request_timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    paragraphs = []
    for node in soup.find_all(["p", "article"]):
        text = node.get_text(" ", strip=True)
        if len(text.split()) >= 8:
            paragraphs.append(text)

    if not paragraphs:
        body_text = soup.get_text("\n", strip=True)
        paragraphs = [line.strip() for line in body_text.splitlines() if len(line.split()) >= 8]

    article_text = "\n\n".join(dict.fromkeys(paragraphs))
    if not article_text.strip():
        raise ValueError("Could not extract readable article text from the provided URL.")

    return clean_text(article_text)


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    normalized = clean_text(text)
    if not normalized:
        return []

    # Splits on sentence punctuation while avoiding many common abbreviations.
    pattern = re.compile(
        r"(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)"
        r"(?<!\bSr)(?<!\bJr)(?<!\bSt)(?<!\bvs)(?<!\betc)"
        r"(?<=[.!?])\s+(?=[\"'“”‘’]?[A-Z0-9])"
    )
    parts = pattern.split(normalized)
    return [part.strip() for part in parts if part.strip()]


def split_into_paragraphs(text: str) -> List[str]:
    normalized = clean_text(text)
    blocks = re.split(r"\n\s*\n|\n(?=[A-Z0-9\"'])", normalized)
    return [block.strip() for block in blocks if block.strip()]


def segment_text(text: str, mode: str) -> List[str]:
    if mode == "article":
        return [clean_text(text)] if clean_text(text) else []
    if mode == "sentence":
        return split_into_sentences(text)
    if mode == "paragraph":
        return split_into_paragraphs(text)
    raise ValueError(f"Unsupported mode: {mode}")


def resolve_input(raw_input: str) -> Tuple[str, str]:
    value = raw_input.strip()
    if looks_like_url(value):
        return "url", fetch_article_text(value)
    return "text", clean_text(value)
