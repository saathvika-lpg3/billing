from typing import Mapping, Any

from services.ui_profile_adapter import control_attribute_map_from_profile


def apply_profile_to_widgets(profile_code: str, widget_map: Mapping[str, Any]):
    """Apply UI profile attributes to a mapping of widget keys -> widget instances.

    widget_map: dict where keys are the control keys expected by profile and
    values are the actual widget objects.
    """
    mapping = control_attribute_map_from_profile(profile_code, list(widget_map.keys()))
    for key, attrs in mapping.items():
        widget = widget_map.get(key)
        if widget is None:
            continue
        # visibility
        try:
            visible = attrs.get("visible", True)
            if hasattr(widget, "setVisible"):
                widget.setVisible(visible)
        except Exception:
            pass
        # enabled
        try:
            enabled = attrs.get("enabled", True)
            if hasattr(widget, "setEnabled"):
                widget.setEnabled(enabled)
        except Exception:
            pass
        # required
        try:
            if attrs.get("required"):
                from widgets.form_layout_helpers import mark_widget_required

                mark_widget_required(widget)
        except Exception:
            pass

    return mapping
