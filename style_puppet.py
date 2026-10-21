import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import bpy
from bpy import app

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

MINIMUM_BLENDER_VERSION = (4, 2, 0)


class StylingError(ValueError):
    pass


@dataclass(frozen=True)
class StylingRequest:
    input_path: Path
    output_path: Path
    styling_manifest_path: Path
    materials: tuple[tuple[str, str], ...] = ()
    fill_mode: str = "solid"
    accessories: tuple[tuple[str, str | None], ...] = ()
    background: str | None = None
    no_background: bool = False
    preset_path: Path | None = None
    save_preset_path: Path | None = None
    reset: bool = False
    previews: tuple[tuple[str, str], ...] = ()
    preview_dir: Path = field(default_factory=lambda: Path("build/previews"))


def blender_arguments(arguments: Sequence[str]) -> list[str]:
    try:
        separator = arguments.index("--")
    except ValueError:
        return []
    return list(arguments[separator + 1 :])


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply materials, accessories, and backgrounds to a generated puppet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", type=Path, required=True, help="input .blend path from generate_puppet.py")
    parser.add_argument("--output", type=Path, help="output .blend path; defaults to overwriting --input")
    parser.add_argument("--styling-manifest", type=Path, help="styling JSON manifest path; derived from --output when omitted")
    parser.add_argument(
        "--material",
        action="append",
        default=[],
        metavar="PART=PRESET",
        help="assign a material preset to a body part; repeatable",
    )
    parser.add_argument(
        "--fill-mode",
        choices=("solid", "outline"),
        default="solid",
        help="solid color fill or outline (wireframe) mode",
    )
    parser.add_argument(
        "--accessory",
        action="append",
        default=[],
        metavar="STYLE[:BONE]",
        help="add an accessory (e.g., sneakers, cap); repeatable",
    )
    parser.add_argument("--background", help="background scenario name (e.g., playground)")
    parser.add_argument("--no-background", action="store_true", help="remove any active background")
    parser.add_argument("--preset", type=Path, help="apply a styling preset JSON file")
    parser.add_argument("--save-preset", type=Path, help="save the resulting styling state to a preset JSON file")
    parser.add_argument("--reset", action="store_true", help="remove all styling and restore defaults")
    parser.add_argument(
        "--preview",
        action="append",
        default=[],
        metavar="KIND=NAME",
        help="render a non-destructive PNG preview (kinds: material, accessory, background); repeatable",
    )
    parser.add_argument(
        "--preview-dir",
        type=Path,
        default=Path("build/previews"),
        help="directory for preview PNG output",
    )
    return parser


def _validate_writable_parent(path: Path, label: str) -> None:
    parent = path.expanduser().resolve().parent
    if not parent.exists():
        raise StylingError(f"{label} parent directory does not exist: {parent}")
    if not parent.is_dir():
        raise StylingError(f"{label} parent is not a directory: {parent}")
    if not os.access(parent, os.W_OK):
        raise StylingError(f"{label} parent directory is not writable: {parent}")
    if path.exists() and path.is_dir():
        raise StylingError(f"{label} path is a directory: {path}")


def _parse_key_value(argument: str, label: str, require_value: bool = True) -> tuple[str, str | None]:
    if "=" in argument:
        key, _, value = argument.partition("=")
    elif ":" in argument:
        key, _, value = argument.partition(":")
    else:
        if require_value:
            raise StylingError(f"{label} must be in KEY=VALUE form: {argument!r}")
        return argument, None
    key = key.strip()
    value = value.strip()
    if not key:
        raise StylingError(f"{label} has an empty key: {argument!r}")
    if require_value and not value:
        raise StylingError(f"{label} has an empty value: {argument!r}")
    return key, value or None


def parse_request(arguments: Sequence[str]) -> StylingRequest:
    parsed = create_parser().parse_args(arguments)

    input_path = parsed.input.expanduser()
    if not input_path.exists() or input_path.is_dir():
        raise StylingError(f"input .blend does not exist: {input_path}")

    output_path = parsed.output.expanduser() if parsed.output else input_path
    styling_manifest_path = (
        parsed.styling_manifest.expanduser()
        if parsed.styling_manifest is not None
        else output_path.with_suffix(".styling.json")
    )
    _validate_writable_parent(output_path, "output")
    _validate_writable_parent(styling_manifest_path, "styling manifest")
    preview_dir = parsed.preview_dir
    if not preview_dir.is_absolute():
        preview_dir = PROJECT_ROOT / preview_dir
    if parsed.preview and not preview_dir.exists():
        preview_dir.mkdir(parents=True, exist_ok=True)
    if parsed.preset is not None and not parsed.preset.expanduser().is_file():
        raise StylingError(f"preset file does not exist: {parsed.preset}")
    if parsed.save_preset is not None:
        _validate_writable_parent(parsed.save_preset, "save preset")

    materials = tuple(
        (part, preset) for part, preset in (_parse_key_value(m, "material") for m in parsed.material)
    )
    accessories = tuple(
        _parse_key_value(item, "accessory", require_value=False) for item in parsed.accessory
    )
    previews = tuple(
        (kind, name) for kind, name in (_parse_key_value(p, "preview") for p in parsed.preview)
    )

    return StylingRequest(
        input_path=input_path,
        output_path=output_path,
        styling_manifest_path=styling_manifest_path,
        materials=materials,
        fill_mode=parsed.fill_mode,
        accessories=accessories,
        background=parsed.background,
        no_background=parsed.no_background,
        preset_path=parsed.preset.expanduser() if parsed.preset else None,
        save_preset_path=parsed.save_preset.expanduser() if parsed.save_preset else None,
        reset=parsed.reset,
        previews=previews,
        preview_dir=preview_dir,
    )


def main(arguments: Sequence[str] | None = None) -> int:
    if app.version < MINIMUM_BLENDER_VERSION:
        required = ".".join(map(str, MINIMUM_BLENDER_VERSION))
        installed = ".".join(map(str, app.version))
        print(
            f"Blender {required} or newer is required; found {installed}.",
            file=sys.stderr,
        )
        return 1

    try:
        request = parse_request(
            blender_arguments(sys.argv if arguments is None else arguments)
        )
    except StylingError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    output_path = request.output_path.resolve()
    output_existed = output_path.exists()
    try:
        bpy.ops.wm.open_mainfile(filepath=str(request.input_path.resolve()))

        from puppet_pipeline.styling.materials import MaterialApplier
        from puppet_pipeline.styling.presets import StylingPreset
        from puppet_pipeline.styling.manifest import (
            StylingManifestWriter,
            StylingState,
        )
        from puppet_pipeline.styling.scene import (
            setup_style_collections,
            validate_puppet_scene,
        )

        warnings = validate_puppet_scene()
        for warning in warnings:
            print(f"Warning: {warning}")
        setup_style_collections()

        limb_thickness = _source_limb_thickness(request.input_path)

        if request.reset:
            from puppet_pipeline.styling.presets import reset_styling

            reset_styling()

        preset = (
            StylingPreset.load(request.preset_path)
            if request.preset_path is not None
            else None
        )
        materials_map = dict(preset.materials) if preset else {}
        materials_map.update(
            {part if not part.startswith("pup.") else part: preset_name
             for part, preset_name in request.materials}
        )
        for part, preset_name in materials_map.items():
            object_name = part if part.startswith("pup.") else f"pup.{part}"
            obj = bpy.data.objects.get(object_name)
            if obj is None:
                raise StylingError(f"unknown body part: {part!r}")
            MaterialApplier.apply(obj, preset_name)

        fill_mode = preset.fill_mode if preset else request.fill_mode
        MaterialApplier.set_fill_mode(fill_mode, limb_thickness)

        accessories_state: list[dict[str, str]] = []
        background_state: str | None = None

        preset_accessories = preset.accessories if preset else []
        for entry in preset_accessories:
            from puppet_pipeline.styling.accessories import AccessoryBuilder

            accessories_state.extend(
                AccessoryBuilder.build(
                    entry["style"], entry["attach_bone"], limb_thickness
                )
            )
        for style, bone in request.accessories:
            from puppet_pipeline.styling.accessories import AccessoryBuilder

            accessories_state.extend(
                AccessoryBuilder.build(style, bone, limb_thickness)
            )

        requested_background = (
            preset.background if preset and preset.background else request.background
        )
        if requested_background or request.no_background:
            from puppet_pipeline.styling.backgrounds import BackgroundBuilder

            background_state = BackgroundBuilder.build(requested_background)

        preview_files: list[str] = []
        if request.previews:
            from puppet_pipeline.styling.preview import PreviewRenderer

            for kind, name in request.previews:
                preview_files.append(
                    str(
                        PreviewRenderer.render(
                            kind, name, request.preview_dir, limb_thickness
                        )
                    )
                )

        if request.save_preset_path is not None:
            StylingPreset(
                fill_mode=fill_mode,
                materials={
                    part.removeprefix("pup."): preset_name
                    for part, preset_name in materials_map.items()
                },
                accessories=accessories_state,
                background=background_state,
            ).save(request.save_preset_path)

        if not request.previews or _has_apply_operations(request):
            from puppet_pipeline.styling.render import RenderProfile

            render_record = RenderProfile().apply_to_blend(bpy.context.scene)
            if render_record["warning"]:
                print(f"Warning: {render_record['warning']}")
            source_manifest = request.input_path.with_suffix(".manifest.json")
            StylingManifestWriter.write(
                request.styling_manifest_path,
                StylingState(
                    fill_mode=fill_mode,
                    materials=materials_map,
                    accessories=accessories_state,
                    background=background_state,
                    render={
                        "engine": render_record["engine"],
                        "resolution_x": render_record["resolution_x"],
                        "resolution_y": render_record["resolution_y"],
                    },
                    preview_files=preview_files,
                ),
                source_manifest=str(source_manifest),
                blender_version=".".join(map(str, app.version)),
            )
            result = bpy.ops.wm.save_as_mainfile(
                filepath=str(output_path),
                check_existing=False,
            )
            if "FINISHED" not in result:
                raise RuntimeError(f"Blender save failed with result: {sorted(result)}")
    except Exception as error:
        if not output_existed and output_path.exists():
            output_path.unlink()
        print(f"Styling failed: {error}", file=sys.stderr)
        return 1

    return 0


def _has_apply_operations(request: StylingRequest) -> bool:
    return bool(
        request.materials
        or request.accessories
        or request.background
        or request.no_background
        or request.preset_path
        or request.reset
        or request.fill_mode == "outline"
    )


def _source_limb_thickness(input_path: Path) -> float:
    import json

    manifest_path = input_path.with_suffix(".manifest.json")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        thickness = float(payload["parameters"]["limb_radius"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        from puppet_pipeline.styling.materials import DEFAULT_LIMB_THICKNESS

        return DEFAULT_LIMB_THICKNESS
    return thickness if thickness > 0 else DEFAULT_LIMB_THICKNESS


if __name__ == "__main__":
    raise SystemExit(main())
