import httpx

from app.scanner.rate_limiter import CircuitBreaker, PerDomainThrottle

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class HttpClient:
    """httpx wrapper with rate limiting, circuit breaker, and retries."""

    def __init__(
        self,
        throttle: PerDomainThrottle | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        timeout: float = 15.0,
        max_retries: int = 2,
        custom_headers: dict | None = None,
    ):
        self.throttle = throttle or PerDomainThrottle()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.max_retries = max_retries

        headers = {**DEFAULT_HEADERS}
        if custom_headers:
            headers.update(custom_headers)

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            max_redirects=5,
            verify=False,  # Scan targets may have self-signed certs
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
                    await asyncio.sleep(1.0 * (attempt + 1))

        raise last_exc  # type: ignore[misc]

    async def close(self) -> None:
        await self.client.aclose()
