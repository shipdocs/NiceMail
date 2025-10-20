"""Message detail panel."""
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from ...core.mail_client import MailMessage


class MessageDetailPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("detailPanel")
        self._subject = QLabel("Select a message")
        self._subject.setWordWrap(True)
        subject_font = QFont()
        subject_font.setPointSize(18)
        subject_font.setBold(True)
        self._subject.setFont(subject_font)

        self._meta = QLabel("")
        self._meta.setWordWrap(True)
        meta_font = QFont()
        meta_font.setPointSize(12)
        self._meta.setFont(meta_font)

        self._body = QTextEdit()
        self._body.setReadOnly(True)
        self._body.setObjectName("messageBody")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        layout.addWidget(self._subject)
        layout.addWidget(self._meta)
        layout.addWidget(self._body, 1)

    def show_message(self, message: MailMessage) -> None:
        self._subject.setText(message.subject)
        meta = f"From {message.sender}\nReceived {message.date_received.strftime('%A %d %B %Y %H:%M')}"
        self._meta.setText(meta)
        self._body.setPlainText(message.preview)


__all__ = ["MessageDetailPanel"]
