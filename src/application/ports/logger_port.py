from __future__ import annotations

from typing import Protocol


class LoggerPort(Protocol):
    def info(self, message: str) -> None:
        ...

    def warning(self, message: str) -> None:
        ...

    def error(self, message: str) -> None:
        ...
