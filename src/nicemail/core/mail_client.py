"""Mail client abstractions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import imaplib
import email
from email.header import decode_header
from email.message import Message

from .config import MailAccountConfig


@dataclass(slots=True)
class MailFolder:
    name: str
    display_name: str
    is_primary: bool = False
    sort_index: int = 0


@dataclass(slots=True)
class MailMessage:
    """Simplified representation of an email message."""

    id: str
    account_id: str
    subject: str
    sender: str
    preview: str
    date_received: datetime
    is_unread: bool = True
    is_flagged: bool = False
    folder: str = "INBOX"


class MailClient:
    """Minimal client capable of fetching messages."""

    def __init__(self, account: MailAccountConfig, use_sample_data: bool = False) -> None:
        self.account = account
        self._use_sample_data = use_sample_data
        self._sample_messages: list[MailMessage] | None = None

    # ----------------------------- folder helpers --------------------------
    def list_primary_folders(self) -> Sequence[MailFolder]:
        base = [
            MailFolder(name="INBOX", display_name="Inbox", is_primary=True, sort_index=0),
            MailFolder(name="STARRED", display_name="Favorites", sort_index=1),
        ]
        extra = [
            MailFolder(name="SENT", display_name="Sent", sort_index=2),
            MailFolder(name="ARCHIVE", display_name="Archive", sort_index=3),
            MailFolder(name="SPAM", display_name="Spam", sort_index=4),
        ]
        return base + extra

    # ------------------------------- fetching ------------------------------
    def fetch_inbox(self, limit: int = 50) -> Sequence[MailMessage]:
        if self._use_sample_data or self.account.protocol == "demo":
            return self._load_sample_messages()[:limit]
        if self.account.protocol.lower() == "imap":
            return self._fetch_imap(limit)
        # Placeholder for POP3, SMTP fetch etc.
        return []

    def owns_message(self, message: MailMessage) -> bool:
        return message.account_id == self.account.address

    def mark_as_read(self, message: MailMessage) -> None:
        message.is_unread = False
        if not self._use_sample_data:
            self._imap_flag(message, mark_read=True)

    def toggle_flag(self, message: MailMessage) -> None:
        message.is_flagged = not message.is_flagged
        if not self._use_sample_data:
            self._imap_flag(message, toggle_star=True)

    # ------------------------------- IMAP ----------------------------------
    def _fetch_imap(self, limit: int) -> Sequence[MailMessage]:
        messages: list[MailMessage] = []
        try:
            with imaplib.IMAP4_SSL(self.account.incoming_server, self.account.port) as client:
                client.login(self.account.username or self.account.address, self.account.password or "")
                client.select("INBOX")
                typ, data = client.search(None, "ALL")
                if typ != "OK":
                    return []
                ids = data[0].split()[-limit:]
                for msg_id in reversed(ids):
                    typ, msg_data = client.fetch(msg_id, "(RFC822 FLAGS)")
                    if typ != "OK":
                        continue
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    subject = self._decode_header(email_message.get("Subject", "(No subject)"))
                    sender = self._decode_header(email_message.get("From", "Unknown sender"))
                    preview = self._extract_preview(email_message)
                    date_tuple = email.utils.parsedate_to_datetime(email_message.get("Date"))
                    date_received = date_tuple.astimezone(timezone.utc) if date_tuple else datetime.now(timezone.utc)
                    flags = msg_data[1].decode() if len(msg_data) > 1 and isinstance(msg_data[1], bytes) else ""
                    message = MailMessage(
                        id=f"{self.account.address}:{msg_id.decode()}",
                        account_id=self.account.address,
                        subject=subject,
                        sender=sender,
                        preview=preview,
                        date_received=date_received,
                        is_unread="\\Seen" not in flags,
                        is_flagged="\\Flagged" in flags,
                    )
                    messages.append(message)
        except Exception:
            return []
        return messages

    def _imap_flag(self, message: MailMessage, mark_read: bool = False, toggle_star: bool = False) -> None:
        try:
            with imaplib.IMAP4_SSL(self.account.incoming_server, self.account.port) as client:
                client.login(self.account.username or self.account.address, self.account.password or "")
                client.select("INBOX")
                msg_id = message.id.split(":")[-1]
                if mark_read:
                    client.store(msg_id, "+FLAGS", "(\\Seen)")
                if toggle_star:
                    if message.is_flagged:
                        client.store(msg_id, "+FLAGS", "(\\Flagged)")
                    else:
                        client.store(msg_id, "-FLAGS", "(\\Flagged)")
        except Exception:
            pass

    # ----------------------------- sample data -----------------------------
    def _load_sample_messages(self) -> list[MailMessage]:
        if self._sample_messages is None:
            sample_path = Path(__file__).resolve().parents[1] / "resources" / "sample_messages.json"
            with sample_path.resolve().open("r", encoding="utf8") as handle:
                import json

                entries = json.load(handle)
            messages: list[MailMessage] = []
            for entry in entries:
                messages.append(
                    MailMessage(
                        id=f"sample:{entry['id']}",
                        account_id=self.account.address,
                        subject=entry["subject"],
                        sender=entry["sender"],
                        preview=entry["preview"],
                        date_received=datetime.fromisoformat(entry["date_received"]),
                        is_unread=entry.get("is_unread", True),
                        is_flagged=entry.get("is_flagged", False),
                        folder=entry.get("folder", "INBOX"),
                    )
                )
            self._sample_messages = messages
        return list(self._sample_messages)

    # --------------------------- helpers -----------------------------------
    @staticmethod
    def _decode_header(value: str) -> str:
        decoded = decode_header(value)
        parts = []
        for text, encoding in decoded:
            if isinstance(text, bytes):
                parts.append(text.decode(encoding or "utf8", errors="replace"))
            else:
                parts.append(text)
        return " ".join(parts)

    @staticmethod
    def _extract_preview(message: Message) -> str:
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    body = payload.decode(part.get_content_charset() or "utf8", errors="replace")
                    break
        else:
            payload = message.get_payload(decode=True)
            if payload:
                body = payload.decode(message.get_content_charset() or "utf8", errors="replace")
        body = body.strip().replace("\n", " ")
        return body[:200]


__all__ = ["MailClient", "MailFolder", "MailMessage"]
