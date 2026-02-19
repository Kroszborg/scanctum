import asyncio
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode

from bs4 import BeautifulSoup

from app.scanner.http_client import HttpClient
from app.scanner.scope import ScopeValidator

logger = logging.getLogger(__name__)

# Common paths to seed crawl when page has few/no links (same origin only)
COMMON_SEED_PATHS_QUICK = [
    "/", "/login", "/signin", "/register", "/signup", "/admin", "/dashboard",
    "/home", "/index.html", "/about", "/contact", "/user", "/profile",
]
COMMON_SEED_PATHS_FULL = [
    "/", "/login", "/signin", "/register", "/signup", "/admin", "/dashboard",
    "/home", "/index.html", "/about", "/contact", "/user", "/profile",
    "/api", "/api/v1", "/graphql", "/swagger", "/api-docs", "/docs",
    "/logout", "/forgot-password", "/reset-password", "/settings", "/account",
    "/.well-known/security.txt", "/robots.txt", "/sitemap.xml",
    "/manager", "/administrator", "/backend", "/portal", "/app",
]


@dataclass
class FormData:
    action: str
    method: str
    inputs: list[dict] = field(default_factory=list)


@dataclass
class CrawledPage:
    url: str
    status_code: int
    headers: dict
    body: str
    forms: list[FormData] = field(default_factory=list)
    links: list[str] = field(default_factory=list)


class AsyncCrawler:
    """BFS web crawler with dedup, depth control, form extraction, and optional seed paths."""

    def __init__(
        self,
        http_client: HttpClient,
        scope: ScopeValidator,
        max_depth: int = 2,
        max_pages: int = 20,
        concurrency: int = 5,
        extra_seed_urls: list[str] | None = None,
    ):
        self.http = http_client
        self.scope = scope
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(concurrency)
        self.visited: set[str] = set()
        self.pages: list[CrawledPage] = []
        self.extra_seed_urls = extra_seed_urls or []

    async def crawl(self, start_url: str) -> list[CrawledPage]:
        queue: deque[tuple[str, int]] = deque()
        base = urljoin(start_url, "/")
        queue.append((self._normalize(start_url), 0))
        for seed in self.extra_seed_urls:
            u = urljoin(base, seed)
            norm = self._normalize(u)
            if norm not in self.visited and self.scope.is_in_scope(u):
                queue.append((norm, 0))

        while queue and len(self.pages) < self.max_pages:
            batch: list[tuple[str, int]] = []
            while queue and len(batch) < self.semaphore._value:
                url, depth = queue.popleft()
                normalized = self._normalize(url)
                if normalized in self.visited:
                    continue
                if depth > self.max_depth:
                    continue
                if not self.scope.is_in_scope(url):
                    continue
                self.visited.add(normalized)
                batch.append((url, depth))

            if not batch:
                break

            tasks = [self._fetch_page(url, depth) for url, depth in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Crawl error: {result}")
                    continue
                if result is None:
                    continue

                page, depth = result
                self.pages.append(page)

                if len(self.pages) >= self.max_pages:
                    break

                # Enqueue discovered links
                for link in page.links:
                    norm = self._normalize(link)
                    if norm not in self.visited and self.scope.is_in_scope(link):
                        queue.append((link, depth + 1))

        return self.pages

    async def _fetch_page(self, url: str, depth: int) -> tuple[CrawledPage, int] | None:
        async with self.semaphore:
            try:
                response = await self.http.get(url)
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    return None

                body = response.text
                links = self._extract_links(url, body)
                forms = self._extract_forms(url, body)

                page = CrawledPage(
                    url=url,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=body,
                    forms=forms,
                    links=links,
                )
                return page, depth
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                return None

    def _extract_links(self, base_url: str, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        links: list[str] = []

        def add(href: str) -> None:
            if not href or href.strip().startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                return
            absolute = urljoin(base_url, href.strip())
            if absolute not in seen and self.scope.is_in_scope(absolute):
                seen.add(absolute)
                links.append(absolute)

        for tag in soup.find_all(["a", "link"], href=True):
            add(tag["href"])
        for tag in soup.find_all(["script", "img", "iframe", "source", "video", "audio"], src=True):
            add(tag["src"])
        for tag in soup.find_all("area", href=True):
            add(tag["href"])
        for tag in soup.find_all(attrs={"data-href": True}):
            add(tag["data-href"])
        for tag in soup.find_all(attrs={"data-src": True}):
            add(tag["data-src"])
        for tag in soup.find_all(srcset=True):
            for part in tag["srcset"].split(","):
                part = part.strip().split()[0] if part.strip() else ""
                add(part)
        for tag in soup.find_all("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)}):
            content = tag.get("content", "")
            m = re.search(r"url\s*=\s*(.+)", content, re.I)
            if m:
                add(m.group(1).strip())
        for form in soup.find_all("form", action=True):
            add(form["action"])
        return links

    def _extract_forms(self, base_url: str, html: str) -> list[FormData]:
        soup = BeautifulSoup(html, "lxml")
        forms: list[FormData] = []
        for form in soup.find_all("form"):
            action = urljoin(base_url, form.get("action", ""))
            method = (form.get("method", "GET")).upper()
            inputs = []
            for inp in form.find_all(["input", "textarea", "select"]):
                inputs.append({
                    "name": inp.get("name", ""),
                    "type": inp.get("type", "text"),
                    "value": inp.get("value", ""),
                })
            forms.append(FormData(action=action, method=method, inputs=inputs))
        return forms

    @staticmethod
    def _normalize(url: str) -> str:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower()
        port = parsed.port

        # Remove default ports
        if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
            port = None

        netloc = host
        if port:
            netloc = f"{host}:{port}"

        # Sort query params
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        sorted_query = urlencode(sorted(query_params.items()), doseq=True)

        # Remove fragment, strip trailing slash
        path = parsed.path.rstrip("/") or "/"

        return urlunparse((scheme, netloc, path, "", sorted_query, ""))
