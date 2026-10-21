from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ENGINE = "BLENDER_EEVEE_NEXT"
FALLBACK_ENGINE = "BLENDER_WORKBENCH"
DEFAULT_PREVIEW_RESOLUTION = (640, 480)
DEFAULT_RENDER_RESOLUTION = (1920, 1080)


def parse_resolution(value: str) -> tuple[int, int]:
    raise NotImplementedError


@dataclass(frozen=True)
class RenderProfile:
    engine: str = DEFAULT_ENGINE
    preview_resolution: tuple[int, int] = DEFAULT_PREVIEW_RESOLUTION
    render_resolution: tuple[int, int] = DEFAULT_RENDER_RESOLUTION
    light_rig: str = "sun_ambient"

    @staticmethod
    def apply_engine(scene) -> str | None:
        raise NotImplementedError

    @staticmethod
    def setup_light_rig(scene) -> list:
        raise NotImplementedError

    @staticmethod
    def teardown_light_rig(scene, created: list) -> None:
        raise NotImplementedError

    def apply_to_blend(self, scene) -> dict:
        raise NotImplementedError
