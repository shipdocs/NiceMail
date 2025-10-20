"""High level controller connecting UI to services."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .config import AppConfig, MailAccountConfig
from .mail_client import MailClient, MailFolder, MailMessage
from .services import BackgroundTaskRunner
from .spam_manager import SpamManager


@dataclass
class InboxData:
    """Aggregated data for the inbox view."""

    folders: Sequence[MailFolder]
    messages: Sequence[MailMessage]
    unread_count: int


class MailController:
    """Coordinate the UI with the mail + spam services."""

    def __init__(self, config: AppConfig, background_runner: BackgroundTaskRunner) -> None:
        self._config = config
        self._background = background_runner
        self._clients: List[MailClient] = [MailClient(account) for account in config.accounts]
        self._spam_manager = SpamManager(config.spam)

    @property
    def accounts(self) -> Sequence[MailAccountConfig]:
        return tuple(client.account for client in self._clients)

    def load_initial_inbox(self) -> InboxData:
        messages: list[MailMessage] = []
        folders: list[MailFolder] = []
        for client in self._clients:
            folders.extend(client.list_primary_folders())
            inbox_messages = client.fetch_inbox(limit=50)
            filtered = self._spam_manager.filter_messages(inbox_messages)
            messages.extend(filtered)
        unread_count = sum(message.is_unread for message in messages)
        messages.sort(key=lambda msg: msg.date_received, reverse=True)
        unique: dict[tuple[str, str], MailFolder] = {}
        for folder in folders:
            key = (folder.name, folder.display_name)
            if key not in unique or folder.is_primary:
                unique[key] = folder
        ordered_folders = sorted(unique.values(), key=lambda f: f.sort_index)
        return InboxData(folders=ordered_folders, messages=messages, unread_count=unread_count)

    def refresh_inbox_async(self, callback) -> None:
        """Refresh the inbox without blocking the UI."""

        def task() -> InboxData:
            return self.load_initial_inbox()

        self._background.run(task, callback)

    def mark_as_read(self, message: MailMessage) -> None:
        for client in self._clients:
            if client.owns_message(message):
                client.mark_as_read(message)
                break

    def toggle_flag(self, message: MailMessage) -> None:
        for client in self._clients:
            if client.owns_message(message):
                client.toggle_flag(message)
                break

    def ensure_sample_client(self) -> None:
        if not self._clients:
            sample_account = MailAccountConfig(
                name="Demo Mail",
                address="grandma@example.com",
                incoming_server="sample.local",
                protocol="demo",
            )
            self._clients.append(MailClient(sample_account, use_sample_data=True))


__all__ = ["InboxData", "MailController"]
