"""Configuration management for NiceMail."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tomllib


def _default_cache_dir() -> Path:
    return Path.home() / ".config" / "nicemail"


@dataclass(slots=True)
class MailAccountConfig:
    """Describe how to connect to a mailbox."""

    name: str
    address: str
    incoming_server: str
    protocol: str = "imap"
    port: int = 993
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = True


@dataclass(slots=True)
class SpamConfig:
    """Configuration related to spam filtering."""

    provider: str = "chatgpt"
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    threshold: float = 0.6
    enabled: bool = True


@dataclass(slots=True)
class AppConfig:
    """Root configuration object for the application."""

    accounts: List[MailAccountConfig] = field(default_factory=list)
    spam: SpamConfig = field(default_factory=SpamConfig)
    cache_dir: Path = field(default_factory=_default_cache_dir)

    def has_accounts(self) -> bool:
        return bool(self.accounts)


class ConfigLoader:
    """Load application configuration from disk."""

    DEFAULT_LOCATIONS: tuple[Path, ...] = (
        Path.home() / ".config" / "nicemail.toml",
        Path.home() / ".config" / "nicemail" / "config.toml",
    )

    def load(self, override: Path | None = None) -> AppConfig:
        if override:
            return self._load_file(override)

        for path in self.DEFAULT_LOCATIONS:
            if path.exists():
                return self._load_file(path)

        return AppConfig()

    def _load_file(self, path: Path) -> AppConfig:
        data = tomllib.loads(path.read_text(encoding="utf8"))
        accounts = [MailAccountConfig(**entry) for entry in data.get("accounts", [])]
        spam_data = data.get("spam", {})
        spam = SpamConfig(**spam_data)
        cache_dir = Path(data.get("cache_dir")) if data.get("cache_dir") else _default_cache_dir()
        return AppConfig(accounts=accounts, spam=spam, cache_dir=cache_dir)


__all__ = [
    "AppConfig",
    "ConfigLoader",
    "MailAccountConfig",
    "SpamConfig",
]
