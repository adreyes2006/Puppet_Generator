from __future__ import annotations

from dataclasses import dataclass

DEFAULT_OUTLINE_COLOR = "#0d0d0d"
THICKNESS_FACTOR = 0.15


@dataclass(frozen=True)
class OutlineSpec:
    enabled: bool = False
    thickness: float | None = None
    color: str | None = None

    def resolve(self, limb_thickness: float) -> dict:
        raise NotImplementedError


def parse_outline_color(value: str) -> str:
    raise NotImplementedError


class OutlineApplier:
    """Applies/removes inverted-hull toon outlines on pup.* and acc.* objects."""

    @staticmethod
    def apply(obj, spec: OutlineSpec) -> None:
        raise NotImplementedError

    @staticmethod
    def apply_all(spec: OutlineSpec, limb_thickness: float) -> None:
        raise NotImplementedError

    @staticmethod
    def remove_all() -> None:
        raise NotImplementedError
