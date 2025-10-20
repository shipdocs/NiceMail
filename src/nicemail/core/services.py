"""Shared services used across the application."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

Callback = Callable[[Any], None]


class BackgroundTaskRunner:
    """Simple wrapper over a thread pool for background work."""

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="nicemail")

    def run(self, func: Callable[[], Any], callback: Callback | None = None) -> Future:
        future = self._executor.submit(func)
        if callback:
            def _done(fut: Future) -> None:
                try:
                    result = fut.result()
                except Exception as exc:  # pragma: no cover - logged elsewhere
                    result = exc
                app = QApplication.instance()
                if app is None:
                    callback(result)
                else:
                    QTimer.singleShot(0, lambda: callback(result))

            future.add_done_callback(_done)
        return future

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


__all__ = ["BackgroundTaskRunner"]
