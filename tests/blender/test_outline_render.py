import tempfile
import unittest
from pathlib import Path

import bpy

from puppet_pipeline.styling.materials import MaterialApplier
from puppet_pipeline.styling.outline import OutlineApplier, OutlineSpec
from puppet_pipeline.styling.presets import reset_styling
from puppet_pipeline.styling.preview import PreviewRenderer
from tests.blender.fixtures import build_rig_fixture


def _pixels(path: Path):
    image = bpy.data.images.load(str(path))
    try:
        width, height = image.size
        return width, height, list(image.pixels)
    finally:
        bpy.data.images.remove(image)


def _is_dark(px) -> bool:
    return px[0] < 0.15 and px[1] < 0.15 and px[2] < 0.15


class OutlinePixelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_rig_fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.preview_dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        reset_styling()
        self.tmp.cleanup()

    def _render(self, outline: bool) -> Path:
        for name, obj in self.fixture.objects.items():
            MaterialApplier.apply(obj, "blue")
        if outline:
            OutlineApplier.apply_all(
                OutlineSpec(enabled=True, thickness=0.2), 0.10
            )
        return PreviewRenderer.render("material", "red", self.preview_dir)

    def test_dark_outline_pixels_adjacent_to_fill(self) -> None:
        path = self._render(outline=True)
        width, height, pixels = _pixels(path)
        dark_with_fill_neighbor = 0
        for y in range(height):
            for x in range(width):
                i = (y * width + x) * 4
                if not _is_dark(pixels[i : i + 4]):
                    continue
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        j = (ny * width + nx) * 4
                        neighbor = pixels[j : j + 4]
                        if not _is_dark(neighbor) and neighbor[3] > 0.5:
                            dark_with_fill_neighbor += 1
                            break
        self.assertGreater(
            dark_with_fill_neighbor,
            40,
            "expected dark outline pixels adjacent to fill pixels",
        )

    def test_outline_changes_render_output(self) -> None:
        with_outline = self._render(outline=True).read_bytes()
        reset_styling()
        self.fixture = build_rig_fixture()
        without_outline = self._render(outline=False).read_bytes()
        self.assertNotEqual(with_outline, without_outline)


if __name__ == "__main__":
    unittest.main()
