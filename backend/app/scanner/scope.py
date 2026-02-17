import re
from urllib.parse import urlparse


STATIC_EXTENSIONS = frozenset({
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".avi",
    ".zip", ".gz", ".tar", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
})


class ScopeValidator:
    """Validates that URLs stay within the defined scan scope."""

    def __init__(
        self,
        target_url: str,
        include_subdomains: bool = False,
        exclude_patterns: list[str] | None = None,
    ):
        parsed = urlparse(target_url)
        self.target_domain = parsed.hostname or ""
        self.target_scheme = parsed.scheme
        self.include_subdomains = include_subdomains
        self.exclude_regexes = [
            re.compile(p) for p in (exclude_patterns or [])
        ]

    def is_in_scope(self, url: str) -> bool:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # Must be http or https
        if parsed.scheme not in ("http", "https"):
            return False

        # Domain check
        if self.include_subdomains:
            if not (hostname == self.target_domain or hostname.endswith(f".{self.target_domain}")):
                return False
        else:
            if hostname != self.target_domain:
                return False

        # Static resource filter
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in STATIC_EXTENSIONS):
            return False

        # Exclusion patterns
        for regex in self.exclude_regexes:
            if regex.search(url):
                return False

        return True
