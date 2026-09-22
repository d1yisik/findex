from __future__ import annotations

from functools import lru_cache, wraps
import time


def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"\033[90m[@timed] {func.__name__} виконано за {elapsed:.3f} ms\033[0m")
        return result

    return wrapper


def cached_search(maxsize: int = 128):
    def decorator(func):
        cached_func = lru_cache(maxsize=maxsize)(func)

        @wraps(func)
        def wrapper(query_str: str, *args, **kwargs):
            hits_before = cached_func.cache_info().hits
            res = cached_func(query_str, *args, **kwargs)
            hits_after = cached_func.cache_info().hits
            if hits_after > hits_before:
                print(f"\033[32m[CACHE HIT] Запит '{query_str}' отримано з кешу!\033[0m")
            return res

        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        return wrapper

    return decorator