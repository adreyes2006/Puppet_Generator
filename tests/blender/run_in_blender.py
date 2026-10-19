import argparse
import os
import sys
import unittest
from collections.abc import Sequence
from pathlib import Path

import bpy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src"
TEST_ROOT = Path(__file__).resolve().parent


def blender_arguments(arguments: Sequence[str]) -> list[str]:
    try:
        separator = arguments.index("--")
    except ValueError:
        return []
    return list(arguments[separator + 1 :])


def configure_import_paths() -> None:
    for path in (str(PROJECT_ROOT), str(SOURCE_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run puppet tests inside Blender.")
    parser.add_argument("--blend", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--verbose", action="store_true")
    return parser


def _load_inputs(blend_path: Path | None, manifest_path: Path | None) -> None:
    if blend_path is not None:
        resolved_blend = blend_path.expanduser().resolve()
        if not resolved_blend.is_file():
            raise FileNotFoundError(f"Blend fixture not found: {resolved_blend}")
        result = bpy.ops.wm.open_mainfile(filepath=str(resolved_blend))
        if "FINISHED" not in result:
            raise RuntimeError(f"Could not load blend fixture: {resolved_blend}")
        os.environ["PUPPET_BLEND_PATH"] = str(resolved_blend)
    if manifest_path is not None:
        resolved_manifest = manifest_path.expanduser().resolve()
        if not resolved_manifest.is_file():
            raise FileNotFoundError(f"Manifest fixture not found: {resolved_manifest}")
        os.environ["PUPPET_MANIFEST_PATH"] = str(resolved_manifest)


def main(arguments: Sequence[str] | None = None) -> int:
    configure_import_paths()
    parsed = create_parser().parse_args(
        blender_arguments(sys.argv if arguments is None else arguments)
    )
    try:
        _load_inputs(parsed.blend, parsed.manifest)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"Fixture error: {error}", file=sys.stderr)
        return 2

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(TEST_ROOT),
        pattern=parsed.pattern,
        top_level_dir=str(PROJECT_ROOT),
    )
    if suite.countTestCases() == 0:
        print(f"No Blender tests matched {parsed.pattern!r}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(
        verbosity=2 if parsed.verbose else 1,
    ).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
