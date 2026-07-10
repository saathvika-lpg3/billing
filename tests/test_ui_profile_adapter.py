from services.ui_profile_adapter import control_attribute_map_from_profile, keys_needed_for_profile


def test_control_map_for_retail():
    keys = ["item", "qty", "rate", "gst", "table_no"]
    attrs = control_attribute_map_from_profile("retail_supermarket", keys)
    assert attrs["item"]["required"] is True
    assert attrs["qty"]["required"] is True
    assert attrs["table_no"]["visible"] is False or isinstance(attrs["table_no"]["visible"], bool)


def test_keys_needed_contains_gst_for_gst_profiles():
    keys = keys_needed_for_profile("distributor_wholesale")
    assert "gst" in keys
