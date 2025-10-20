"""Widget that gently hints at extra folders."""
from __future__ import annotations

from typing import Sequence

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ...core.mail_client import MailFolder


class FolderHint(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("folderHint")
        self._expanded = False
        self._folders: Sequence[MailFolder] = []

        self._label = QLabel("Your main Inbox keeps things simple. Other folders are tucked away but always nearby.")
        self._label.setWordWrap(True)

        self._toggle = QPushButton("Show other folders")
        self._toggle.setObjectName("subtleButton")
        self._toggle.clicked.connect(self._toggle_folders)

        self._extra = QLabel("")
        self._extra.setWordWrap(True)
        self._extra.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(self._label)
        layout.addWidget(self._toggle)
        layout.addWidget(self._extra)

    def set_folders(self, folders: Sequence[MailFolder]) -> None:
        self._folders = folders
        self._update_text()

    def _toggle_folders(self) -> None:
        self._expanded = not self._expanded
        self._extra.setVisible(self._expanded)
        self._toggle.setText("Hide folders" if self._expanded else "Show other folders")
        self._update_text()

    def _update_text(self) -> None:
        if not self._folders:
            self._extra.setText("")
            return
        base = ("Your main Inbox keeps things simple. Other folders are tucked away but always nearby.")
        if self._expanded:
            names = ", ".join(folder.display_name for folder in self._folders if not folder.is_primary)
            self._label.setText(base)
            self._extra.setText(f"Also available: {names}.")
        else:
            primary = next((folder.display_name for folder in self._folders if folder.is_primary), "Inbox")
            self._label.setText(
                f"You're viewing your {primary}. Tap below to peek at other folders whenever you're ready."
            )
            self._extra.setText("")


__all__ = ["FolderHint"]
