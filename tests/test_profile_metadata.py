from services.business_rules import profile_metadata


def test_profile_metadata_contains_expected_keys():
    meta = profile_metadata("retail_supermarket")
    assert meta["code"] == "retail"
    assert "required_fields" in meta
    assert "visible_columns" in meta
    assert isinstance(meta["visible_columns"], tuple)


def test_profile_metadata_defaults_to_distributor():
    meta = profile_metadata("unknown-type")
    assert meta["code"] == "distributor_wholesale"
