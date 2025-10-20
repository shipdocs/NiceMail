"""Main window for the NiceMail application."""
from __future__ import annotations

from PySide6.QtCore import QItemSelection, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..core.controller import InboxData, MailController
from .models import MessageListModel
from .widgets.detail_panel import MessageDetailPanel
from .widgets.folder_hint import FolderHint


class MainWindow(QMainWindow):
    def __init__(self, controller: MailController, use_sample_data: bool) -> None:
        super().__init__()
        self._controller = controller
        self.setWindowTitle("NiceMail")
        self.setMinimumSize(1024, 640)

        self._setup_widgets()
        if use_sample_data:
            self._controller.ensure_sample_client()
        self._load_inbox()

    # --------------------------- setup ------------------------------------
    def _setup_widgets(self) -> None:
        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        sidebar = self._build_sidebar()
        self._message_list = self._build_message_list()
        self._detail_panel = MessageDetailPanel(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self._message_list)
        splitter.addWidget(self._detail_panel)
        splitter.setSizes([200, 320, 400])
        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _build_sidebar(self) -> QWidget:
        widget = QWidget(self)
        widget.setObjectName("sidebar")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Inbox overview")
        title.setObjectName("sidebarTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        self._summary_label = QLabel("Loading messages…")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        self._folder_hint = FolderHint()
        layout.addWidget(self._folder_hint)

        layout.addStretch()

        refresh_button = QPushButton("Refresh inbox")
        refresh_button.clicked.connect(self._refresh_clicked)
        refresh_button.setObjectName("primaryButton")
        layout.addWidget(refresh_button)

        return widget

    def _build_message_list(self) -> QListView:
        view = QListView(self)
        view.setObjectName("messageList")
        view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        view.setUniformItemSizes(True)
        view.setWordWrap(True)
        view.setSpacing(8)
        view.setResizeMode(QListView.ResizeMode.Adjust)
        view.verticalScrollBar().setSingleStep(40)
        self._model = MessageListModel()
        view.setModel(self._model)
        view.selectionModel().selectionChanged.connect(self._on_list_selection_changed)
        return view

    # --------------------------- data loading ------------------------------
    def _load_inbox(self) -> None:
        inbox = self._controller.load_initial_inbox()
        self._apply_inbox(inbox)
        self._controller.refresh_inbox_async(self._on_inbox_refreshed)

    def _apply_inbox(self, inbox: InboxData) -> None:
        self._model.set_messages(inbox.messages)
        if inbox.unread_count:
            message = f"You have {inbox.unread_count} new message{'s' if inbox.unread_count != 1 else ''}."
        else:
            message = "You're all caught up. Enjoy your day!"
        self._summary_label.setText(message)
        self._folder_hint.set_folders(inbox.folders)
        if inbox.messages:
            self._select_first()

    def _select_first(self) -> None:
        index = self._model.index(0, 0)
        if index.isValid():
            self._message_list.setCurrentIndex(index)
            self._detail_panel.show_message(self._model.message_at(index.row()))

    # ---------------------------- events -----------------------------------
    def _on_inbox_refreshed(self, result: InboxData | Exception) -> None:
        if isinstance(result, Exception):
            QMessageBox.warning(self, "Sync problem", "Could not refresh emails right now.")
            return
        self._apply_inbox(result)

    def _on_list_selection_changed(self, selected: QItemSelection, _deselected: QItemSelection) -> None:
        indexes = selected.indexes()
        if not indexes:
            return
        index = indexes[0]
        row = index.row()
        message = self._model.message_at(row)
        self._controller.mark_as_read(message)
        self._model.notify_message_changed(row)
        self._detail_panel.show_message(message)

    def _refresh_clicked(self) -> None:
        self._summary_label.setText("Refreshing…")
        self._controller.refresh_inbox_async(self._on_inbox_refreshed)


__all__ = ["MainWindow"]
