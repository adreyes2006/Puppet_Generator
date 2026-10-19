import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import bpy
from bpy import app

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from puppet_pipeline.common.manifest import ManifestWriter
from puppet_pipeline.common.params import ParameterError, PuppetParameters
from puppet_pipeline.common.scene import reset_puppet_scene
from puppet_pipeline.generation.geometry import GeometryBuilder
from puppet_pipeline.generation.parts import build_part_specs
from puppet_pipeline.rigging.armature import ArmatureBuilder
from puppet_pipeline.rigging.binding import BindingApplier
from puppet_pipeline.rigging.constraints import ConstraintBuilder

MINIMUM_BLENDER_VERSION = (4, 2, 0)


class OutputPathError(ValueError):
    pass


@dataclass(frozen=True)
class GenerationRequest:
    parameters: PuppetParameters
    output_path: Path
    manifest_path: Path


def blender_arguments(arguments: Sequence[str]) -> list[str]:
    try:
        separator = arguments.index("--")
    except ValueError:
        return []
    return list(arguments[separator + 1 :])


def create_parser() -> argparse.ArgumentParser:
    defaults = PuppetParameters()
    parser = argparse.ArgumentParser(
        description="Generate a rigged 2D stick-figure puppet in Blender.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    positive = "must be a finite number greater than zero"
    parser.add_argument("--upper-arm-length", type=float, default=defaults.upper_arm_len, help=positive)
    parser.add_argument("--forearm-length", type=float, default=defaults.forearm_len, help=positive)
    parser.add_argument("--thigh-length", type=float, default=defaults.thigh_len, help=positive)
    parser.add_argument("--shin-length", type=float, default=defaults.shin_len, help=positive)
    parser.add_argument("--limb-thickness", type=float, default=defaults.limb_radius, help=positive)
    parser.add_argument("--torso-length", type=float, default=defaults.torso_len, help=positive)
    parser.add_argument("--head-radius", type=float, default=defaults.head_radius, help=positive)
    parser.add_argument("--hip-width", type=float, default=defaults.hip_width, help=positive)
    parser.add_argument("--shoulder-width", type=float, default=defaults.shoulder_width, help=positive)
    parser.add_argument("--seed", type=int, default=defaults.seed, help="nonnegative integer")
    parser.add_argument("--output", type=Path, default=Path("puppet.blend"), help="output .blend path")
    parser.add_argument("--manifest", type=Path, help="JSON manifest path; derived from --output when omitted")
    return parser


def _validate_writable_parent(path: Path, label: str) -> None:
    parent = path.expanduser().resolve().parent
    if not parent.exists():
        raise OutputPathError(f"{label} parent directory does not exist: {parent}")
    if not parent.is_dir():
        raise OutputPathError(f"{label} parent is not a directory: {parent}")
    if not os.access(parent, os.W_OK):
        raise OutputPathError(f"{label} parent directory is not writable: {parent}")
    if path.exists() and path.is_dir():
        raise OutputPathError(f"{label} path is a directory: {path}")


def parse_request(arguments: Sequence[str]) -> GenerationRequest:
    parsed = create_parser().parse_args(arguments)
    parameters = PuppetParameters(
        upper_arm_len=parsed.upper_arm_length,
        forearm_len=parsed.forearm_length,
        thigh_len=parsed.thigh_length,
        shin_len=parsed.shin_length,
        limb_radius=parsed.limb_thickness,
        torso_len=parsed.torso_length,
        head_radius=parsed.head_radius,
        hip_width=parsed.hip_width,
        shoulder_width=parsed.shoulder_width,
        seed=parsed.seed,
    )
    parameters.validate()

    output_path = parsed.output.expanduser()
    manifest_path = (
        parsed.manifest.expanduser()
        if parsed.manifest is not None
        else output_path.with_suffix(".manifest.json")
    )
    _validate_writable_parent(output_path, "output")
    _validate_writable_parent(manifest_path, "manifest")

    return GenerationRequest(
        parameters=parameters,
        output_path=output_path,
        manifest_path=manifest_path,
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
    except (ParameterError, OutputPathError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    output_path = request.output_path.resolve()
    manifest_path = request.manifest_path.resolve()
    output_existed = output_path.exists()
    manifest_existed = manifest_path.exists()
    previous_manifest = manifest_path.read_bytes() if manifest_existed else None
    try:
        collections = reset_puppet_scene()
        parts = build_part_specs(request.parameters)
        objects = GeometryBuilder(collections.geometry).build(parts)
        bone_specs = ArmatureBuilder.plan(request.parameters, parts)
        armature = ArmatureBuilder(collections.rig).build(bone_specs)
        ConstraintBuilder(armature).apply()
        BindingApplier.bind(objects, armature)
        ManifestWriter.write(
            manifest_path,
            request.parameters,
            objects,
            armature,
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
        if previous_manifest is not None:
            manifest_path.write_bytes(previous_manifest)
        elif manifest_path.exists():
            manifest_path.unlink()
        print(f"Generation failed: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
