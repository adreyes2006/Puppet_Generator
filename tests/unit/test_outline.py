import pytest

from puppet_pipeline.styling.outline import (
    DEFAULT_OUTLINE_COLOR,
    THICKNESS_FACTOR,
    OutlineSpec,
    parse_outline_color,
)


class TestOutlineSpec:
    def test_defaults_disabled(self):
        spec = OutlineSpec()
        assert spec.enabled is False
        assert spec.thickness is None
        assert spec.color is None

    def test_resolve_derives_thickness(self):
        spec = OutlineSpec(enabled=True)
        resolved = spec.resolve(0.10)
        assert resolved["thickness"] == pytest.approx(0.10 * THICKNESS_FACTOR)
        assert resolved["color"] == DEFAULT_OUTLINE_COLOR

    def test_resolve_keeps_explicit_values(self):
        spec = OutlineSpec(enabled=True, thickness=0.05, color="#ff0000")
        resolved = spec.resolve(0.10)
        assert resolved["thickness"] == 0.05
        assert resolved["color"] == "#ff0000"


class TestParseOutlineColor:
    def test_hex_passthrough(self):
        assert parse_outline_color("#1a2b3c") == "#1a2b3c"

    def test_hex_uppercase_normalized(self):
        assert parse_outline_color("#AABBCC") == "#aabbcc"

    def test_catalog_name_to_hex(self):
        assert parse_outline_color("red") == "#d32f2f"
        assert parse_outline_color("black") == "#202020"

    def test_invalid_hex_rejected(self):
        with pytest.raises(ValueError):
            parse_outline_color("#12345")
        with pytest.raises(ValueError):
            parse_outline_color("#gggggg")

    def test_unknown_name_rejected(self):
        with pytest.raises(ValueError):
            parse_outline_color("chartreuse")
