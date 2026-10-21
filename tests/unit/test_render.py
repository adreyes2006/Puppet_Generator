import pytest

from puppet_pipeline.styling.render import (
    DEFAULT_ENGINE,
    DEFAULT_PREVIEW_RESOLUTION,
    DEFAULT_RENDER_RESOLUTION,
    FALLBACK_ENGINE,
    RenderProfile,
    parse_resolution,
)


class TestParseResolution:
    def test_valid(self):
        assert parse_resolution("1280x720") == (1280, 720)
        assert parse_resolution("640x480") == (640, 480)

    def test_rejects_bad_format(self):
        for bad in ("720p", "axb", "1280", "1280x", "x720", "1280*720", ""):
            with pytest.raises(ValueError):
                parse_resolution(bad)

    def test_rejects_out_of_bounds(self):
        with pytest.raises(ValueError):
            parse_resolution("15x480")
        with pytest.raises(ValueError):
            parse_resolution("640x16385")


class TestRenderProfile:
    def test_defaults(self):
        profile = RenderProfile()
        assert profile.engine == DEFAULT_ENGINE == "BLENDER_EEVEE_NEXT"
        assert FALLBACK_ENGINE == "BLENDER_WORKBENCH"
        assert profile.preview_resolution == DEFAULT_PREVIEW_RESOLUTION == (640, 480)
        assert profile.render_resolution == DEFAULT_RENDER_RESOLUTION == (1920, 1080)
        assert profile.light_rig == "sun_ambient"
