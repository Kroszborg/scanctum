import httpx
from typing import Optional

from app.config import settings
from app.scanner.rate_limiter import CircuitBreaker, PerDomainThrottle

DEFAULT_HEADERS = {
    "User-Agent": settings.SCANNER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class HttpClient:
    """httpx wrapper with rate limiting, circuit breaker, and retries.

    Optimizations:
    - Connection pooling via httpx limits
    - Configurable timeouts
    - Exponential backoff retries
    - Gzip/deflate compression support
    """

    def __init__(
        self,
        throttle: PerDomainThrottle | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        custom_headers: dict | None = None,
    ):
        self.throttle = throttle or PerDomainThrottle()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.max_retries = max_retries if max_retries is not None else settings.SCANNER_MAX_RETRIES
        self.timeout = timeout if timeout is not None else settings.SCANNER_TIMEOUT

        headers = {**DEFAULT_HEADERS}
        if custom_headers:
            headers.update(custom_headers)

        # Optimized httpx client with connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=10,  # Keep 10 idle connections per domain
            max_connections=50,  # Max 50 total connections
            keepalive_expiry=30.0,  # Keep connections alive for 30s
        )

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(self.timeout, connect=10.0),  # Separate connect timeout
            follow_redirects=True,
            max_redirects=10,
            verify=False,  # Scan targets may have self-signed certs
            limits=limits,
        )

    async def get(self, url: str) -> httpx.Response:
        return await self._request("GET", url)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        from urllib.parse import urlparse
        domain = urlparse(url).hostname or ""

        if self.circuit_breaker.is_open(domain):
            raise ConnectionError(f"Circuit breaker open for {domain}")

        await self.throttle.wait(url)

        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(method, url, **kwargs)
                self.circuit_breaker.record_success(domain)
                return response
            except (httpx.TransportError, httpx.TimeoutException) as e:
                last_exc = e
                self.circuit_breaker.record_failure(domain)
                if attempt < self.max_retries:
                    import asyncio
                    # Exponential backoff: 1s, 2s, 4s...
                    await asyncio.sleep((2 ** attempt) * 0.5)

        raise last_exc  # type: ignore[misc]

    async def close(self) -> None:
        await self.client.aclose()
