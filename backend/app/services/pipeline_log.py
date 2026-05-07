import time
from contextlib import contextmanager
from typing import Any, Generator


def section(title: str, **kwargs: Any) -> None:
    suffix = "  ".join(f"{key}={value}" for key, value in kwargs.items())
    header = f"[{title}]"
    if suffix:
        header += f"  {suffix}"
    print(f"\n──── {header} " + "─" * max(0, 60 - len(header)), flush=True)


def line(text: str, indent: int = 1) -> None:
    print(("  " * indent) + text, flush=True)


def kv(**kwargs: Any) -> None:
    for key, value in kwargs.items():
        line(f"{key}: {value}")


class _Timer:
    def __init__(self) -> None:
        self.elapsed = 0.0

    def fmt(self) -> str:
        if self.elapsed < 0.001:
            return f"{self.elapsed * 1_000_000:.0f}us"
        if self.elapsed < 1.0:
            return f"{self.elapsed * 1000:.0f}ms"
        return f"{self.elapsed:.2f}s"


@contextmanager
def timed() -> Generator[_Timer, None, None]:
    timer = _Timer()
    start = time.perf_counter()
    try:
        yield timer
    finally:
        timer.elapsed = time.perf_counter() - start
