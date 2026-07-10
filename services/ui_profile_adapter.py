from __future__ import annotations

from typing import Dict, Iterable

from services.business_rules import profile_metadata


def control_attribute_map_from_profile(profile_code: str, control_keys: Iterable[str]) -> Dict[str, dict]:
    """Return a mapping of control_key -> attributes based on the business profile.

    Attributes per control:
      - visible: bool
      - required: bool
      - enabled: bool

    This function is UI-framework-agnostic and suitable for unit testing. A separate
    thin wrapper can apply these attributes to real widgets (e.g., PyQt) in views.
    """
    meta = profile_metadata(profile_code)
    required = set(meta.get("required_fields") or ())
    optional = set(meta.get("optional_fields") or ())
    hidden = set(meta.get("hidden_fields") or ())
    gst_required = bool(meta.get("gst_required"))

    result: Dict[str, dict] = {}
    for key in control_keys:
        k = str(key)
        is_visible = k not in hidden
        is_required = k in required
        # Special-case: GST field visibility/requirement
        if k in ("gst", "gst_rate"):
            is_required = gst_required and is_required
            is_visible = gst_required or is_visible
        result[k] = {"visible": is_visible, "required": is_required, "enabled": True}
    return result


def keys_needed_for_profile(profile_code: str) -> list[str]:
    """Return a deduplicated list of relevant control keys for a profile.

    Useful for views to know which controls to create or bind.
    """
    meta = profile_metadata(profile_code)
    keys = []
    for seq in (meta.get("required_fields") or (), meta.get("optional_fields") or (), meta.get("hidden_fields") or (), meta.get("columns") or ()):  # type: ignore[arg-type]
        for k in seq:
            if k not in keys:
                keys.append(k)
    # Ensure GST field present for profiles that require GST
    if meta.get("gst_required") and "gst" not in keys:
        keys.append("gst")
    return keys
