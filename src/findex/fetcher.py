# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import asyncio
from dataclasses import dataclass
import random
import time
from typing import Optional

import httpx


@dataclass
class FetchResult:
    url: str
    status_code: int
    content: bytes
    text: str
    elapsed_time: float
    error: Optional[str] = None


async def fetch_page(
    client: httpx.AsyncClient,
    url: str,
    max_retries: int = 3,
    base_backoff: float = 0.5,
    timeout_sec: float = 10.0,
) -> FetchResult:
    """Завантажує сторінку з підтримкою таймаутів, Retry-After та exponential backoff + jitter."""
    start_time = time.monotonic()

    for attempt in range(max_retries + 1):
        try:
            async with asyncio.timeout(timeout_sec):
                response = await client.get(url, follow_redirects=True)
                elapsed = time.monotonic() - start_time

                # 429 та 5xx — повторюємо спробу
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < max_retries:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            delay = float(retry_after)
                        else:
                            delay = base_backoff * (2**attempt) + random.uniform(0, 0.1)
                        await asyncio.sleep(delay)
                        continue

                return FetchResult(
                    url=url,
                    status_code=response.status_code,
                    content=response.content,
                    text=response.text,
                    elapsed_time=elapsed,
                    error=None if response.status_code < 400 else f"HTTP {response.status_code}",
                )

        except (httpx.RequestError, TimeoutError, asyncio.TimeoutError) as exc:
            if attempt < max_retries:
                delay = base_backoff * (2**attempt) + random.uniform(0, 0.1)
                await asyncio.sleep(delay)
            else:
                elapsed = time.monotonic() - start_time
                return FetchResult(
                    url=url,
                    status_code=0,
                    content=b"",
                    text="",
                    elapsed_time=elapsed,
                    error=f"Fetch failed after {max_retries} retries: {exc}",
                )

    elapsed = time.monotonic() - start_time
    return FetchResult(
        url=url,
        status_code=0,
        content=b"",
        text="",
        elapsed_time=elapsed,
        error="Max retries reached",
    )