from __future__ import annotations

from PyQt6.QtCore import QObject, Qt, QEvent, QTimer
from PyQt6.QtWidgets import QComboBox, QCompleter, QWidget


_HELP = "Type to filter | Up/Down navigate | Enter select | Esc close"


class _SmartComboGuard(QObject):
    def __init__(self, combo: QComboBox) -> None:
        super().__init__(combo)
        self.combo = combo
        self.last_valid_index = combo.currentIndex()

    def remember_index(self, index: int) -> None:
        if index >= 0:
            self.last_valid_index = index
            QTimer.singleShot(0, self.show_text_start)

    def show_text_start(self) -> None:
        line_edit = self.combo.lineEdit()
        if line_edit is not None and not line_edit.hasFocus():
            line_edit.deselect()
            line_edit.setCursorPosition(0)

    def normalize_text(self) -> None:
        combo = self.combo
        if combo.property("allowCustomText") is True:
            return
        text = combo.currentText().strip()
        exact = combo.findText(text, Qt.MatchFlag.MatchFixedString)
        if exact >= 0:
            combo.setCurrentIndex(exact)
            return
        for index in range(combo.count()):
            if text and text.casefold() in combo.itemText(index).casefold():
                combo.setCurrentIndex(index)
                return
        if 0 <= self.last_valid_index < combo.count():
            combo.setCurrentIndex(self.last_valid_index)
        elif combo.count():
            combo.setCurrentIndex(0)
        self.show_text_start()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            completer = self.combo.completer()
            if completer and completer.popup().isVisible():
                completer.popup().hide()
                return True
        return super().eventFilter(watched, event)


def configure_smart_combo(combo: QComboBox) -> QComboBox:
    """Give an existing combo consistent contains-filter keyboard behaviour."""

    if combo.property("smartDropdown") is True or combo.property("smartDropdownDisabled") is True:
        return combo
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    combo.setMaxVisibleItems(14)
    combo.setProperty("smartDropdown", True)
    combo.setProperty("enterSubmits", True)
    line_edit = combo.lineEdit()
    if line_edit is not None:
        line_edit.setPlaceholderText(line_edit.placeholderText() or "Type to filter")
    completer = QCompleter(combo.model(), combo)
    completer.setCompletionColumn(combo.modelColumn())
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    completer.setMaxVisibleItems(14)
    combo.setCompleter(completer)

    guard = _SmartComboGuard(combo)
    combo._smart_combo_guard = guard  # type: ignore[attr-defined]
    combo.currentIndexChanged.connect(guard.remember_index)
    if line_edit is not None:
        line_edit.editingFinished.connect(guard.normalize_text)
        line_edit.installEventFilter(guard)
        line_edit.textEdited.connect(lambda _text, current=completer: current.complete())
    QTimer.singleShot(0, guard.show_text_start)

    existing = combo.toolTip().strip()
    if _HELP not in existing:
        combo.setToolTip(f"{existing}\n{_HELP}".strip())
    combo.setAccessibleDescription(_HELP)
    return combo


def install_smart_combos(root: QWidget) -> int:
    configured = 0
    combos = [root] if isinstance(root, QComboBox) else []
    combos.extend(root.findChildren(QComboBox))
    for combo in combos:
        if combo.property("smartDropdown") is not True and combo.property("smartDropdownDisabled") is not True:
            configure_smart_combo(combo)
            configured += 1
    return configured
