# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import asyncio
from dataclasses import dataclass, field
import logging
from typing import AsyncGenerator, Dict, Set, Tuple
from urllib.parse import urlparse

import httpx

from findex.fetcher import fetch_page
from findex.robots import RobotsCache
from findex.url_utils import extract_links_and_text, normalize_url


@dataclass
class CrawledPage:
    url: str
    status_code: int
    text: str
    links: list[str] = field(default_factory=list)
    elapsed_time: float = 0.0
    depth: int = 0
    error: str | None = None


class AsyncCrawler:
    def __init__(
        self,
        start_urls: list[str],
        max_pages: int = 200,
        max_concurrency: int = 5,
        host_concurrency: int = 2,
        host_delay: float = 0.1,
        user_agent: str = "FindexBot/1.0 (+https://github.com/d1yisik/findex)",
    ) -> None:
        self.start_urls: list[str] = [normalize_url(u) for u in start_urls]
        self.max_pages: int = max_pages
        self.max_concurrency: int = max_concurrency
        self.host_concurrency: int = host_concurrency
        self.host_delay: float = host_delay
        self.user_agent: str = user_agent

        self.global_sem: asyncio.Semaphore = asyncio.Semaphore(max_concurrency)
        self.host_sems: Dict[str, asyncio.Semaphore] = {}
        self.robots_cache: RobotsCache = RobotsCache(user_agent=user_agent)

        self.seen_urls: Set[str] = set()
        self.queue: asyncio.Queue[Tuple[str, int]] = asyncio.Queue()
        self.pages_crawled: int = 0
        self.active_requests: int = 0
        self.error_count: int = 0
        self.stop_event: asyncio.Event = asyncio.Event()

    def _get_host_sem(self, url: str) -> asyncio.Semaphore:
        host = urlparse(url).netloc
        if host not in self.host_sems:
            self.host_sems[host] = asyncio.Semaphore(self.host_concurrency)
        return self.host_sems[host]

    async def crawl_stream(self) -> AsyncGenerator[CrawledPage, None]:
        for url in self.start_urls:
            self.seen_urls.add(url)
            await self.queue.put((url, 0))

        results_queue: asyncio.Queue[CrawledPage] = asyncio.Queue()

        headers = {"User-Agent": self.user_agent}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:

            async def worker():
                while not self.stop_event.is_set():
                    try:
                        async with asyncio.timeout(0.5):
                            url, depth = await self.queue.get()
                    except TimeoutError:
                        if self.pages_crawled >= self.max_pages or (self.active_requests == 0 and self.queue.empty()):
                            break
                        continue

                    if self.pages_crawled >= self.max_pages:
                        self.queue.task_done()
                        break

                    # Перевіряємо robots.txt
                    allowed = await self.robots_cache.is_allowed(client, url)
                    if not allowed:
                        self.queue.task_done()
                        continue

                    host_sem = self._get_host_sem(url)
                    self.active_requests += 1

                    try:
                        async with self.global_sem, host_sem:
                            res = await fetch_page(client, url)
                            if self.host_delay > 0:
                                await asyncio.sleep(self.host_delay)
                    finally:
                        self.active_requests -= 1

                    if res.error or res.status_code >= 400:
                        self.error_count += 1
                        c_page = CrawledPage(
                            url=url,
                            status_code=res.status_code,
                            text="",
                            links=[],
                            elapsed_time=res.elapsed_time,
                            depth=depth,
                            error=res.error,
                        )
                    else:
                        links, clean_text = extract_links_and_text(res.text, url)
                        c_page = CrawledPage(
                            url=url,
                            status_code=res.status_code,
                            text=clean_text,
                            links=links,
                            elapsed_time=res.elapsed_time,
                            depth=depth,
                        )

                        # Додаємо нові посилання в чергу
                        for link in links:
                            if link not in self.seen_urls and len(self.seen_urls) < self.max_pages * 5:
                                self.seen_urls.add(link)
                                await self.queue.put((link, depth + 1))

                    self.pages_crawled += 1
                    await results_queue.put(c_page)
                    self.queue.task_done()

                    if self.pages_crawled >= self.max_pages:
                        self.stop_event.set()

            # Запуск воркерів через TaskGroup (Python 3.11+)
            try:
                async with asyncio.TaskGroup() as tg:
                    num_workers = min(self.max_concurrency * 2, 20)
                    workers = [tg.create_task(worker()) for _ in range(num_workers)]

                    while self.pages_crawled < self.max_pages and not (self.queue.empty() and self.active_requests == 0 and results_queue.empty()):
                        try:
                            async with asyncio.timeout(0.2):
                                page = await results_queue.get()
                                yield page
                                results_queue.task_done()
                        except TimeoutError:
                            if self.stop_event.is_set() and results_queue.empty():
                                break

                    self.stop_event.set()
                    for w in workers:
                        w.cancel()
            except* Exception as e:
                logging.debug("Crawler TaskGroup finished with exception: %s", e)

            # Віддаємо залишки з черги результатів
            while not results_queue.empty():
                yield await results_queue.get()