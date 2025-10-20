"""Qt models used by the UI."""
from __future__ import annotations

from datetime import datetime
from typing import List, Sequence

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from ..core.mail_client import MailMessage


class MessageListModel(QAbstractListModel):
    """Represent mailbox messages in a list view."""

    HEADERS = ["From", "Subject", "Preview", "Date", "Flags"]

    def __init__(self) -> None:
        super().__init__()
        self._messages: List[MailMessage] = []

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        return 0 if parent and parent.isValid() else len(self._messages)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        message = self._messages[index.row()]
        if role == Qt.DisplayRole:
            return self._format_message(message)
        if role == Qt.DecorationRole:
            return "⭐" if message.is_flagged else ""
        if role == Qt.UserRole:
            return message
        if role == Qt.FontRole:
            from PySide6.QtGui import QFont

            font = QFont()
            font.setPointSize(12)
            font.setBold(message.is_unread)
            return font
        return None

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        roles = super().roleNames()
        roles[Qt.UserRole] = b"message"
        return roles

    def set_messages(self, messages: Sequence[MailMessage]) -> None:
        self.beginResetModel()
        self._messages = list(messages)
        self.endResetModel()

    def notify_message_changed(self, row: int) -> None:
        index = self.index(row, 0)
        if index.isValid():
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.FontRole, Qt.DecorationRole])
    def message_at(self, row: int) -> MailMessage:
        return self._messages[row]

    def _format_message(self, message: MailMessage) -> str:
        date_str = message.date_received.strftime("%b %d, %H:%M")
        return f"{message.sender}\n{message.subject}\n{message.preview}\n{date_str}"


__all__ = ["MessageListModel"]
