from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from puppet_pipeline.styling.presets import PART_NAMES

STYLING_SCHEMA = "styling-v1"


class StylingManifestError(ValueError):
    pass


@dataclass(frozen=True)
class StylingState:
    fill_mode: str = "solid"
    materials: dict[str, str] = field(default_factory=dict)
    accessories: list[dict[str, str]] = field(default_factory=list)
    background: str | None = None
    preview_files: list[str] = field(default_factory=list)


class StylingManifestWriter:
    @staticmethod
    def build(
        state: StylingState,
        source_manifest: str,
        blender_version: str,
    ) -> dict[str, Any]:
        if state.fill_mode not in ("solid", "outline"):
            raise StylingManifestError(f"invalid fill_mode: {state.fill_mode!r}")
        materials = {}
        for part, preset_name in sorted(state.materials.items()):
            object_name = part if part.startswith("pup.") else f"pup.{part}"
            short = object_name.removeprefix("pup.")
            if short not in PART_NAMES:
                raise StylingManifestError(f"invalid part in materials: {part!r}")
            materials[object_name] = preset_name
        accessories = []
        for entry in state.accessories:
            name = entry.get("name", "")
            if not name.startswith("acc."):
                raise StylingManifestError(f"invalid accessory name: {name!r}")
            if entry.get("attach_bone") not in ("foot.L", "foot.R", "head"):
                raise StylingManifestError(
                    f"invalid attach_bone: {entry.get('attach_bone')!r}"
                )
            accessories.append(
                {
                    "name": name,
                    "style": entry["style"],
                    "attach_bone": entry["attach_bone"],
                }
            )
        return {
            "schema": STYLING_SCHEMA,
            "source_manifest": str(source_manifest),
            "blender_version": blender_version,
            "fill_mode": state.fill_mode,
            "materials": materials,
            "accessories": accessories,
            "background": state.background,
            "preview_files": list(state.preview_files),
        }

    @staticmethod
    def serialize(manifest: dict[str, Any]) -> bytes:
        return (
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
                separators=(",", ": "),
            )
            + "\n"
        ).encode("utf-8")

    @classmethod
    def write(
        cls,
        path: Path,
        state: StylingState,
        source_manifest: str,
        blender_version: str,
    ) -> Path:
        resolved_path = path.expanduser().resolve()
        content = cls.serialize(cls.build(state, source_manifest, blender_version))
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{resolved_path.name}.",
                suffix=".tmp",
                dir=resolved_path.parent,
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, resolved_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        return resolved_path
