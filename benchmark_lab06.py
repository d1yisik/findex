# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import asyncio
import time
import psutil

from findex.crawler import AsyncCrawler


async def run_benchmark_for_concurrency(start_url: str, concurrency: int, max_pages: int = 50):
    process = psutil.Process()
    start_time = time.monotonic()

    crawler = AsyncCrawler(start_urls=[start_url], max_pages=max_pages, max_concurrency=concurrency)
    
    pages = 0
    async for _ in crawler.crawl_stream():
        pages += 1

    wall_time = time.monotonic() - start_time
    pages_per_sec = pages / max(wall_time, 0.001)
    peak_rss_mb = process.memory_info().rss / (1024 * 1024)

    return {
        "concurrency": concurrency,
        "wall_time": wall_time,
        "pages_per_sec": pages_per_sec,
        "errors": crawler.error_count,
        "peak_rss_mb": peak_rss_mb,
    }


async def main():
    target_url = "https://docs.python.org/3/"
    max_pages = 50  # Можна збільшити до 200 відповідно до завдання
    
    print(f"--- Running Lab 06 Benchmark for {target_url} (max_pages={max_pages}) ---")
    results = []
    
    for c in [1, 5, 20]:
        print(f"Testing concurrency = {c}...")
        res = await run_benchmark_for_concurrency(target_url, concurrency=c, max_pages=max_pages)
        results.append(res)
        await asyncio.sleep(1)

    print("\n| Concurrency | Wall Time (s) | Pages / sec | Errors | Peak RSS (MB) |")
    print("|------------|---------------|-------------|--------|---------------|")
    for r in results:
        print(f"| {r['concurrency']:<10} | {r['wall_time']:<13.2f} | {r['pages_per_sec']:<11.2f} | {r['errors']:<6} | {r['peak_rss_mb']:<13.2f} |")


if __name__ == "__main__":
    asyncio.run(main())