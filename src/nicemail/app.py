"""Application entry point for NiceMail."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .core.config import AppConfig, ConfigLoader
from .core.controller import MailController
from .core.services import BackgroundTaskRunner
from .ui.main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NiceMail - a gentle email client")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to a configuration file.",
    )
    parser.add_argument(
        "--no-sample-data",
        action="store_true",
        help="Do not fall back to bundled sample messages when no accounts are configured.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    app = QApplication(argv)
    app.setApplicationDisplayName("NiceMail")
    app.setApplicationName("NiceMail")

    config_loader = ConfigLoader()
    config: AppConfig = config_loader.load(args.config)

    background_tasks = BackgroundTaskRunner()
    controller = MailController(config=config, background_runner=background_tasks)
    window = MainWindow(controller=controller, use_sample_data=not args.no_sample_data)

    stylesheet_path = Path(__file__).parent / "resources" / "style.qss"
    if stylesheet_path.exists():
        with stylesheet_path.open("r", encoding="utf8") as handle:
            app.setStyleSheet(handle.read())

    window.show()
    exit_code = app.exec()
    background_tasks.shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
