import pytest

from app.scanner.crawler import AsyncCrawler
from app.scanner.scope import ScopeValidator


class TestScopeValidator:
    def test_in_scope_same_domain(self):
        scope = ScopeValidator("https://example.com")
        assert scope.is_in_scope("https://example.com/page")
        assert scope.is_in_scope("https://example.com/page?q=1")

    def test_out_of_scope_different_domain(self):
        scope = ScopeValidator("https://example.com")
        assert not scope.is_in_scope("https://evil.com/page")

    def test_subdomain_excluded_by_default(self):
        scope = ScopeValidator("https://example.com")
        assert not scope.is_in_scope("https://sub.example.com/page")

    def test_subdomain_included(self):
        scope = ScopeValidator("https://example.com", include_subdomains=True)
        assert scope.is_in_scope("https://sub.example.com/page")

    def test_static_resources_excluded(self):
        scope = ScopeValidator("https://example.com")
        assert not scope.is_in_scope("https://example.com/style.css")
        assert not scope.is_in_scope("https://example.com/image.png")
        assert not scope.is_in_scope("https://example.com/app.js")

    def test_exclude_patterns(self):
        scope = ScopeValidator("https://example.com", exclude_patterns=[r"/logout", r"/admin.*"])
        assert not scope.is_in_scope("https://example.com/logout")
        assert not scope.is_in_scope("https://example.com/admin/users")
        assert scope.is_in_scope("https://example.com/dashboard")

    def test_non_http_rejected(self):
        scope = ScopeValidator("https://example.com")
        assert not scope.is_in_scope("ftp://example.com/file")
        assert not scope.is_in_scope("javascript:alert(1)")


class TestURLNormalization:
    def test_normalize_strips_fragment(self):
        result = AsyncCrawler._normalize("https://example.com/page#section")
        assert "#" not in result

    def test_normalize_strips_trailing_slash(self):
        result = AsyncCrawler._normalize("https://example.com/page/")
        assert result == "https://example.com/page"

    def test_normalize_sorts_query_params(self):
        result = AsyncCrawler._normalize("https://example.com/page?b=2&a=1")
        assert "a=1" in result
        assert result.index("a=1") < result.index("b=2")

    def test_normalize_lowercases_host(self):
        result = AsyncCrawler._normalize("https://EXAMPLE.COM/Page")
        assert "example.com" in result

    def test_normalize_removes_default_port(self):
        result = AsyncCrawler._normalize("https://example.com:443/page")
        assert ":443" not in result

    def test_normalize_keeps_nondefault_port(self):
        result = AsyncCrawler._normalize("https://example.com:8080/page")
        assert ":8080" in result
