# pyright: reportUnknownVariableType=none
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownArgumentType=none
# pyright: reportAttributeAccessIssue=none

import asyncio
from typing import Dict
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsCache:
    """Кеш для завантаження та перевірки правил robots.txt для різних хостів."""

    def __init__(self, user_agent: str = "FindexBot/1.0 (+https://github.com/d1yisik/findex)") -> None:
        self.user_agent: str = user_agent
        self._cache: Dict[str, RobotFileParser] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def is_allowed(self, client: httpx.AsyncClient, url: str) -> bool:
        parsed = urlparse(url)
        host_key = f"{parsed.scheme}://{parsed.netloc}"

        async with self._lock:
            if host_key not in self._cache:
                robots_url = f"{host_key}/robots.txt"
                parser = RobotFileParser()
                parser.set_url(robots_url)
                try:
                    resp = await client.get(robots_url, timeout=5.0, follow_redirects=True)
                    if resp.status_code == 200:
                        parser.parse(resp.text.splitlines())
                    else:
                        parser.parse([])
                except Exception:
                    parser.parse([])
                self._cache[host_key] = parser

            return self._cache[host_key].can_fetch(self.user_agent, url)