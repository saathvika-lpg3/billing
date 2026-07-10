from __future__ import annotations

import os
import re
from pathlib import Path

from PyQt6.QtGui import QPageLayout
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PrintPreviewDialog(QDialog):
    def __init__(self, parent: QWidget | None, pdf_path: Path, title: str = "Print Preview") -> None:
        super().__init__(parent)
        self.pdf_path = Path(pdf_path)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 260)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        head = QFrame()
        head.setObjectName("card")
        head_layout = QVBoxLayout(head)
        head_layout.setContentsMargins(14, 12, 14, 12)
        title = QLabel("PDF Ready For Preview")
        title.setObjectName("pageTitle")
        subtitle = QLabel(str(self.pdf_path))
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        head_layout.addWidget(title)
        head_layout.addWidget(subtitle)
        root.addWidget(head)

        controls = QFrame()
        controls.setObjectName("card")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(14, 12, 14, 12)
        self.paper = QComboBox()
        self.paper.addItems(["A2", "A3", "A4", "A5"])
        self.orientation = QComboBox()
        self.orientation.addItems(["Portrait", "Landscape"])
        paper, orientation = self._detect_pdf_layout()
        self.paper.setCurrentText(paper)
        self.orientation.setCurrentText(orientation)
        controls_layout.addWidget(QLabel("Paper"))
        controls_layout.addWidget(self.paper)
        controls_layout.addWidget(QLabel("Orientation"))
        controls_layout.addWidget(self.orientation)
        controls_layout.addStretch(1)
        root.addWidget(controls)

        info = QLabel(
            f"Detected PDF layout: {paper} {orientation}. Open Preview shows the generated PDF. Print opens the Windows printer dialog before sending the PDF to the default PDF handler."
        )
        info.setObjectName("caption")
        info.setWordWrap(True)
        root.addWidget(info)

        actions = QHBoxLayout()
        actions.addStretch(1)
        open_button = QPushButton("Open Preview")
        open_button.clicked.connect(self.open_preview)
        print_button = QPushButton("Print")
        print_button.clicked.connect(self.print_pdf)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        actions.addWidget(open_button)
        actions.addWidget(print_button)
        actions.addWidget(close_button)
        root.addLayout(actions)

    def open_preview(self) -> None:
        try:
            os.startfile(str(self.pdf_path))
        except OSError as exc:
            QMessageBox.warning(self, self.windowTitle(), f"Preview could not be opened:\n{exc}")

    def print_pdf(self) -> None:
        # Try to print without blocking UI. Preferably an integrated Qt PDF printing
        # would be used, but fallback to launching OS print in a background thread
        # so the UI remains responsive.
        from threading import Thread

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Landscape if self.orientation.currentText() == "Landscape" else QPageLayout.Orientation.Portrait)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        def _start_print():
            try:
                os.startfile(str(self.pdf_path), "print")
            except OSError:
                # nothing we can do in background thread; notify on main thread via message box later
                pass

        try:
            # Launch OS print request asynchronously so UI isn't blocked waiting
            t = Thread(target=_start_print, daemon=True)
            t.start()
        except Exception as exc:
            QMessageBox.warning(self, self.windowTitle(), f"Print could not be started:\n{exc}")
            return
        QMessageBox.information(self, self.windowTitle(), "Print request sent to Windows.")

    def _detect_pdf_layout(self) -> tuple[str, str]:
        pattern = re.compile(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]")
        try:
            with open(self.pdf_path, "rb") as fh:
                data = b""
                while True:
                    chunk = fh.read(65536)
                    if not chunk:
                        return "A4", "Portrait"
                    data = data[-128:] + chunk
                    match = pattern.search(data)
                    if match:
                        break
        except OSError:
            return "A4", "Portrait"
        width = float(match.group(1))
        height = float(match.group(2))
        long_edge = max(width, height)
        paper = "A4"
        if long_edge > 1500:
            paper = "A2"
        elif long_edge > 1000:
            paper = "A3"
        elif long_edge < 700:
            paper = "A5"
        orientation = "Landscape" if width > height else "Portrait"
        return paper, orientation


def show_print_preview(parent: QWidget | None, pdf_path: Path, title: str = "Print Preview") -> None:
    dialog = PrintPreviewDialog(parent, pdf_path, title)
    dialog.open_preview()
    dialog.exec()
