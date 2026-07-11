from __future__ import annotations

from PyQt6.QtWidgets import QApplication, QComboBox, QWidget

from widgets.smart_combo import configure_smart_combo, install_smart_combos


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_smart_combo_filters_by_contains_and_preserves_valid_selection() -> None:
    application = _app()
    assert application is not None
    combo = QComboBox()
    combo.addItems(["Apple", "Samsung", "Xiaomi"])
    configure_smart_combo(combo)
    combo.lineEdit().setText("sung")
    combo.completer().setCompletionPrefix("sung")
    assert combo.completer().completionModel().rowCount() == 1
    combo.lineEdit().setText("not-a-real-value")
    combo._smart_combo_guard.normalize_text()
    assert combo.currentText() in {"Apple", "Samsung", "Xiaomi"}
    assert combo.property("smartDropdown") is True
    assert "Enter select" in combo.toolTip()


def test_install_smart_combos_configures_entire_widget_tree_once() -> None:
    application = _app()
    assert application is not None
    root = QWidget()
    first = QComboBox(root)
    second = QComboBox(root)
    assert install_smart_combos(root) == 2
    assert install_smart_combos(root) == 0
    assert first.isEditable() and second.isEditable()
