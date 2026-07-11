from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QFrame, QMessageBox, QPushButton, QSizePolicy, QWidget

from widgets.erp_components import install_button_feedback
from widgets.flow_layout import FlowLayout


ActionRole = Literal["primary", "secondary", "destructive", "positive"]
ActionState = Literal["normal", "busy", "success", "error"]
ActionCallback = Callable[[], object]


@dataclass(frozen=True)
class ActionSpec:
    label: str
    callback: ActionCallback | None
    tooltip: str = ""
    shortcut: str = ""
    role: ActionRole | None = None
    enabled: bool = True
    visible: bool = True
    checkable: bool = False


class CompactActionToolbar(QFrame):
    """A compact left-to-right action row that wraps only when required.

    ``(label, callback)`` tuples remain supported so existing handlers and
    shortcuts can migrate without an adapter. ``ActionSpec`` adds explicit
    roles, tooltips and state for permission-aware screens.
    """

    def __init__(
        self,
        actions: Sequence[ActionSpec | tuple[str, ActionCallback | None]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("actionToolbar")
        self.setProperty("role", "toolbar")
        self.setProperty("actionLayout", "horizontal-wrap")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.flow_layout = FlowLayout(self, margin=4, spacing=5)
        self.buttons: dict[str, QPushButton] = {}
        self._state_tokens: dict[str, int] = {}

        for value in actions:
            action = value if isinstance(value, ActionSpec) else ActionSpec(value[0], value[1])
            self._add_action(action)

    def _add_action(self, action: ActionSpec) -> None:
        if action.label in self.buttons:
            raise ValueError(f"Duplicate toolbar action label: {action.label}")
        role = action.role or self._role_for_label(action.label)
        button = QPushButton(action.label, self)
        button.setObjectName(
            "primaryButton" if role == "primary" else "dangerButton" if role == "destructive" else "quickButton"
        )
        button.setProperty("toolbarAction", True)
        button.setProperty("actionRole", role)
        button.setProperty("actionState", "normal")
        button.setProperty("success", False)
        button.setProperty("error", False)
        button.setMinimumHeight(26)
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setCheckable(action.checkable)
        button.setEnabled(action.enabled)
        button.setVisible(action.visible)
        if action.tooltip:
            button.setToolTip(action.tooltip)
        if action.shortcut:
            button.setShortcut(QKeySequence(action.shortcut))
            shortcut_hint = f"Shortcut: {action.shortcut}"
            button.setToolTip(f"{button.toolTip()}\n{shortcut_hint}".strip())
        install_button_feedback(button)
        if action.callback is None:
            button.clicked.connect(
                lambda checked=False, label=action.label: QMessageBox.information(
                    self,
                    label,
                    f"{label} is not available for this screen.",
                )
            )
        else:
            button.clicked.connect(lambda checked=False, callback=action.callback: callback())
        self.buttons[action.label] = button
        self.flow_layout.addWidget(button)

    def button(self, label: str) -> QPushButton:
        return self.buttons[label]

    def set_action_enabled(self, label: str, enabled: bool) -> None:
        button = self.button(label)
        button.setProperty("allowed", enabled)
        button.setEnabled(enabled)
        self._refresh_style(button)

    def set_action_state(
        self,
        label: str,
        state: ActionState,
        *,
        reset_after_ms: int = 0,
    ) -> None:
        if state not in {"normal", "busy", "success", "error"}:
            raise ValueError(f"Unsupported action state: {state}")
        button = self.button(label)
        was_busy = button.property("actionState") == "busy"
        if state == "busy" and not was_busy:
            button.setProperty("_enabledBeforeBusy", button.isEnabled())
            button.setEnabled(False)
        elif state != "busy" and was_busy:
            button.setEnabled(button.property("_enabledBeforeBusy") is not False)
        button.setProperty("actionState", state)
        button.setProperty("busy", state == "busy")
        button.setProperty("success", state == "success")
        button.setProperty("error", state == "error")
        self._refresh_style(button)

        token = self._state_tokens.get(label, 0) + 1
        self._state_tokens[label] = token
        if reset_after_ms > 0 and state in {"success", "error"}:
            QTimer.singleShot(reset_after_ms, lambda: self._reset_if_current(label, token))

    def set_busy(self, label: str, busy: bool = True) -> None:
        self.set_action_state(label, "busy" if busy else "normal")

    def mark_success(self, label: str, reset_after_ms: int = 1400) -> None:
        self.set_action_state(label, "success", reset_after_ms=reset_after_ms)

    def mark_error(self, label: str, reset_after_ms: int = 2200) -> None:
        self.set_action_state(label, "error", reset_after_ms=reset_after_ms)

    def _reset_if_current(self, label: str, token: int) -> None:
        if self._state_tokens.get(label) == token:
            self.set_action_state(label, "normal")

    def _refresh_style(self, button: QPushButton) -> None:
        style = button.style()
        style.unpolish(button)
        style.polish(button)
        button.update()

    def _role_for_label(self, label: str) -> ActionRole:
        normalized = " ".join(label.lower().replace("&", "").split())
        if any(word in normalized for word in ("delete", "cancel", "remove", "close", "lock", "restore", "free space")):
            return "destructive"
        if normalized.startswith(("save", "run", "search", "show")) or normalized in {"post", "apply"}:
            return "primary"
        if normalized.startswith(("add", "new")):
            return "positive"
        return "secondary"
