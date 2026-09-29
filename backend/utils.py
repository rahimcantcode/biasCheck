"""Bounded article extraction and sentence offsets in the returned text."""
import ipaddress
import re
import socket
from urllib.parse import urlparse, urljoin
import pysbd
import requests
import trafilatura
from bs4 import BeautifulSoup
try:
    from .config import get_settings
except ImportError:
    from config import get_settings

MAX_DOWNLOAD = 3_000_000

def clean_text(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'[ \t]+', ' ', text)).strip()


def looks_like_url(value):
    p = urlparse(value.strip())
    return p.scheme in {'http', 'https'} and bool(p.netloc)


def validate_public_url(url):
    p = urlparse(url)
    if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password:
        raise ValueError('Please provide a public HTTP or HTTPS article URL.')
    if p.port not in (None,80,443):
        raise ValueError('Only standard web ports are supported.')
    addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme=='https' else 80), type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ValueError('Only public article URLs are supported.')


def extract_article_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(['script','style','noscript','nav','footer','aside','form']):
        node.decompose()
    articles = soup.find_all('article')
    if articles:
        body = max(articles, key=lambda n: len(n.get_text(' ',strip=True)))
        paragraphs = [p.get_text(' ',strip=True) for p in body.find_all('p') if p.get_text(strip=True)]
        text = '\n\n'.join(paragraphs) if paragraphs else body.get_text(' ',strip=True)
    else:
        text = trafilatura.extract(str(soup), include_comments=False, include_tables=False, favor_precision=True) or ''
    text = clean_text(text)
    if len(text.split()) < 20:
        raise ValueError('Could not extract enough article text. Please paste the article instead.')
    if len(text) > 100_000:
        raise ValueError('Extracted article is too long.')
    return text


def fetch_article_text(url):
    # Also restrict private-network egress at the deployment boundary; DNS prechecks
    # alone cannot eliminate DNS rebinding with an unrestricted network client.
    for _ in range(5):
        validate_public_url(url)
        with requests.get(url, timeout=get_settings().request_timeout,
                          headers={'User-Agent':'BiasChecker/0.2'}, stream=True, allow_redirects=False) as response:
            if response.is_redirect:
                location = response.headers.get('Location')
                if not location:
                    raise ValueError('Article redirect has no destination.')
                url = urljoin(url, location)
                continue
            response.raise_for_status()
            if not any(t in response.headers.get('Content-Type','').lower() for t in ('text/html','application/xhtml+xml')):
                raise ValueError('The URL must point to an HTML article.')
            chunks, total = [], 0
            for chunk in response.iter_content(65536):
                total += len(chunk)
                if total > MAX_DOWNLOAD:
                    raise ValueError('Article page exceeds download limit. Please paste the text.')
                chunks.append(chunk)
            return extract_article_html(b''.join(chunks))
    raise ValueError('Too many article redirects.')


def segment_spans(text, mode):
    if mode == 'article':
        return [(0,len(text))] if text else []
    if mode == 'sentence':
        segmenter = pysbd.Segmenter(language='en', clean=False, char_span=True)
        candidates = [(s.start,s.end) for s in segmenter.segment(text)]
    elif mode == 'paragraph':
        candidates = [(m.start(),m.end()) for m in re.finditer(r'[^\n]+(?:\n(?!\s*\n)[^\n]+)*',text)]
    else:
        raise ValueError('Unsupported analysis mode')
    spans = []
    for start,end in candidates:
        while start < end and text[start].isspace(): start += 1
        while end > start and text[end-1].isspace(): end -= 1
        if end > start: spans.append((start,end))
    return spans


def split_into_sentences(text):
    text = clean_text(text)
    return [text[a:b] for a,b in segment_spans(text,'sentence')]


def segment_text(text,mode):
    text = clean_text(text)
    return [text[a:b] for a,b in segment_spans(text,mode)]


def resolve_input(raw_input):
    value = raw_input.strip()
    return ('url',fetch_article_text(value)) if looks_like_url(value) else ('text',clean_text(value))
