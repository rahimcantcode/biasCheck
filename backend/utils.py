"""Bounded article extraction and sentence offsets in the returned text."""
import ipaddress
import http.client
import ssl
import time
import re
import socket
from urllib.parse import urlparse, urljoin, quote
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
    try:
        addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme=='https' else 80), type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError('Could not resolve the article host. Please paste its text.') from exc
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise ValueError('Only public article URLs are supported.')
    return addresses[0]


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


class PublicConnection(http.client.HTTPConnection):
    """Connect to the checked address, retaining the hostname for TLS and Host."""
    def __init__(self, host, port, address, secure, timeout):
        super().__init__(host, port=port, timeout=timeout)
        self.address = address
        self.secure = secure

    def connect(self):
        family, socktype, proto, _, sockaddr = self.address
        sock = socket.socket(family, socktype, proto)
        try:
            sock.settimeout(self.timeout)
            sock.connect(sockaddr)
            if self.secure:
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=self.host)
            self.sock = sock
        except BaseException:
            sock.close()
            raise


def fetch_article_text(url):
    deadline = time.monotonic() + get_settings().request_timeout
    for _ in range(5):
        address = validate_public_url(url)
        parsed = urlparse(url)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError('Article download timed out. Please paste its text.')
        connection = PublicConnection(parsed.hostname.encode('idna').decode('ascii'),
                                      parsed.port or (443 if parsed.scheme == 'https' else 80),
                                      address, parsed.scheme == 'https', remaining)
        response = None
        try:
            target = quote(parsed.path or '/', safe='/%:@!$&\'()*+,;=-._~')
            if parsed.query:
                target += '?' + quote(parsed.query, safe='/%?:@!$&\'()*+,;=-._~')
            connection.request('GET', target, headers={'User-Agent': 'BiasChecker/0.3', 'Accept-Encoding': 'identity'})
            active_socket = connection.sock
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                if not location:
                    raise ValueError('Article redirect has no destination.')
                url = urljoin(url, location)
                continue
            if response.status >= 400:
                raise ValueError('Article host refused the request. Please paste its text.')
            if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
                raise ValueError('Article host returned unsupported compression. Please paste its text.')
            if not any(t in response.getheader('Content-Type', '').lower() for t in ('text/html', 'application/xhtml+xml')):
                raise ValueError('The URL must point to an HTML article.')
            chunks, total = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError('Article download timed out. Please paste its text.')
                active_socket.settimeout(remaining)
                chunk = response.read1(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD:
                    raise ValueError('Article page exceeds download limit. Please paste the text.')
                chunks.append(chunk)
            return extract_article_html(b''.join(chunks))
        except (OSError, http.client.HTTPException) as exc:
            raise requests.RequestException('Could not retrieve article') from exc
        finally:
            if response is not None:
                response.close()
            connection.close()
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
