# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import pytest
import httpx

from findex.fetcher import fetch_page
from findex.robots import RobotsCache
from findex.url_utils import normalize_url


def test_url_normalization() -> None:
    raw = "HTTP://Example.COM:80/Foo/Bar/#fragment?b=2&a=1"
    normalized = normalize_url(raw)
    assert "http://example.com/Foo/Bar/" in normalized or "http://example.com/Foo/Bar" in normalized
    assert "#fragment" not in normalized


@pytest.mark.asyncio
async def test_robots_cache() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private/")
        return httpx.Response(200, text="Allowed content")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        cache = RobotsCache()
        allowed = await cache.is_allowed(client, "http://testserver/public/")
        disallowed = await cache.is_allowed(client, "http://testserver/private/")
        assert allowed is True
        assert disallowed is False


@pytest.mark.asyncio
async def test_fetch_retry_on_500() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return httpx.Response(500, text="Error")
        return httpx.Response(200, text="Success")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        res = await fetch_page(client, "http://testserver/page", max_retries=2, base_backoff=0.01)
        assert res.status_code == 200
        assert res.text == "Success"
        assert attempts == 2