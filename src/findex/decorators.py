from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def cached(func: F) -> F:
    cache_store: dict[tuple[Any, ...], Any] = {}

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        hashable_args: list[Any] = []
        for arg in args:
            try:
                hash(arg)
                hashable_args.append(arg)
            except TypeError:
                hashable_args.append(id(arg))

        key = tuple(hashable_args) + tuple(sorted(kwargs.items()))
        if key not in cache_store:
            cache_store[key] = func(*args, **kwargs)
        return cache_store[key]

    return wrapper  # type: ignore[return-value]


def timed(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        _ = time.perf_counter() - start
        return result

    return wrapper  # type: ignore[return-value]