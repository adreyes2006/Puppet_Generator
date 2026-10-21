# Research: Preview Render Quality

## Render engine selection

- `BLENDER_EEVEE_NEXT` is the engine identifier on Blender ≥4.2 (local 5.2.2 and
  CI 4.2.3 both use it; `BLENDER_EEVEE` was removed in 4.2).
- Engine assignment is a dynamic enum: `scene.render.engine` accepts the string
  or raises `TypeError` listing valid identifiers. Current code already relies
  on this (`preview.py:161-164`) but with the preference inverted — it tries
  Workbench first.
- Feature 003 flips the order: try `BLENDER_EEVEE_NEXT`, fall back to
  `BLENDER_WORKBENCH` on `TypeError`, and log a warning so CI output shows
  which engine rendered each PNG.
- EEVEE in background mode still needs an OpenGL context; CI already provides
  one via `xvfb-run` + Mesa (`libgl1-mesa-dri`, `libegl1`). Software EEVEE is
  slow — SC-001's 60s bound accounts for Mesa rasterization.

## Inverted-hull outline

- Technique: duplicate-effect via a `SOLIDIFY` modifier on each `pup.*`/`acc.*`
  object:
  - `thickness` < 0 (negative offset extrudes *outward* along normals when
    combined with flipped normals) — use `modifier.offset = -1.0` with positive
    `thickness` for a uniform outward hull.
  - `use_flip_normals = True` so the hull faces inward → only the rim behind
    the surface renders → reads as a stroke.
  - `material_offset` pointing at an appended dark material slot so the hull
    shades differently from the fill.
  - `use_even_offset = True` for consistent thickness on capsules.
- The outline material is a flat near-black material (`mat.outline`) with high
  emission strength so it stays dark under EEVEE lighting — identical look in
  Workbench fallback since emission bypasses shading.
- Idempotence: modifier named `outline_toon`; `apply` is a no-op when the
  modifier already exists (same pattern as `set_fill_mode`'s WIREFRAME check).
- Removal: `--reset` / `reset_styling()` removes `outline_toon` modifiers and
  the extra material slot alongside WIREFRAME cleanup.
- Mutual exclusion with `--fill-mode outline`: wireframe mode wins; applying a
  toon hull to wireframe-replaced geometry would render a hollow shell.

## Light rig

- Fixed rig, created by `PreviewRenderer` during EEVEE renders and removed on
  restore (same snapshot discipline as the camera):
  - `world.color` / world node `Background` color → light gray (0.05 strength
    ambient so nothing is pitch black).
  - One `SUN` lamp at ~(30°, -20°) rotation, `energy` ~2.0,
    `angle` ~0.5 for soft edge.
  - `use_shadow = True` on sun + contact shadow flags where available.
- EEVEE AO: `scene.eevee.use_gtao` exists on 4.2; removed in 4.3+ (always-on).
  Wrap in `hasattr` check — never hard-fail on AO settings.
- Snapshot must additionally capture `scene.world` state and any `preview_*`
  light objects so restore is total.

## Schema v2

- `styling-preset-v1` → `styling-preset-v2`: adds optional `outline` object
  `{enabled: bool, thickness: float|null, color: "#rrggbb"|null}`.
- `styling-v1` → `styling-v2` manifest: same `outline` object recorded, plus
  `render` object `{engine, resolution_x, resolution_y}` stored on the saved
  blend.
- Compatibility: `StylingPreset.load` accepts both schema strings; v1 payloads
  deserialize to `outline=None`. New saves always emit v2.
- `StylingState` gains `outline: dict | None` and `render: dict | None`
  fields; `StylingManifestWriter` emits them under v2.

## Richer props

- `PropSpec` gains `sub_props: tuple[SubPropSpec, ...] = ()`; each sub-prop is
  `(dx, dz, scale_x, scale_z, color, shape)` relative to the parent prop's
  origin.
- Builder composes all primitives into one `from_pydata` mesh per prop —
  vertices/faces merged with index offsets, per-face material indices assign
  each primitive its own `mat.bg_*` slot. Object name stays
  `bg.prop.<name>`; clear/manifest semantics unchanged.
- Primitives keep their staggered `prop_y` depth; sub-props share the
  parent's y (all vertices still on the prop's depth plane — planar contract
  preserved).

## CLI additions

- `--outline` (store_true), `--outline-thickness FLOAT` (Blender units),
  `--outline-color` (catalog name or `#rrggbb`),
  `--preview-resolution WxH` (default 640x480),
  `--render-resolution WxH` (default 1920x1080, stored on saved blend).
- `WxH` parser: `r"^(\d+)x(\d+)$"`, 16 ≤ W,H ≤ 16384; failures → `StylingError`
  (exit 2), consistent with existing validation.
- Warning path: `--fill-mode outline` + outline enabled →
  `Warning: --fill-mode outline overrides toon outline; skipping outline` and
  no hull modifiers created.

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Freestyle line art | Render-pipeline-dependent, not inspectable as scene state in tests |
| Grease Pencil strokes | Second object type to track/reset; Solidify rides existing modifiers |
| Cycles | Minutes per frame under Mesa; overkill for flat cartoon look |
| Optional outline field in v1 schema | User chose clean v2 bump |
