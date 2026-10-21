# Data Model: Preview Render Quality

## Entities

### OutlineSpec

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | bool | `False` | `True` when `--outline` or preset `outline.enabled` set |
| `thickness` | float \| None | `None` → `limb_thickness × 0.15` | Absolute Blender units, > 0 |
| `color` | str \| None | `None` → `"#0d0d0d"` | `#rrggbb` hex after normalization |

- Frozen dataclass in `styling/outline.py`. `None` fields mean "derive at apply
  time" so presets stay portable across puppet sizes.
- `parse_outline_color(value)` accepts catalog preset name or `#rrggbb`;
  returns hex string. Reuses `MATERIAL_CATALOG` colors for named lookup.

### RenderProfile

| Field | Type | Default |
|-------|------|---------|
| `engine` | str | `"BLENDER_EEVEE_NEXT"` (fallback `BLENDER_WORKBENCH`) |
| `preview_resolution` | tuple[int, int] | `(640, 480)` |
| `render_resolution` | tuple[int, int] | `(1920, 1080)` |
| `light_rig` | str | `"sun_ambient"` (fixed; only value for now) |

- Frozen dataclass in `styling/render.py`. `parse_resolution("WxH")` validates
  `r"^(\d+)x(\d+)$"`, bounds 16–16384.
- `apply_to_blend(scene)` sets engine + `render_resolution` on the saved blend;
  `apply_to_preview(scene)` sets engine + `preview_resolution` + light rig.

### SubPropSpec

| Field | Type | Notes |
|-------|------|-------|
| `dx`, `dz` | float | Offset from parent prop center |
| `scale_x`, `scale_z` | float | Half-extents (rect) / radius (circle) |
| `color` | RGBA tuple | Own `mat.bg_*` material slot |
| `shape` | str | `"rect"` \| `"circle"` |

- `PropSpec.sub_props: tuple[SubPropSpec, ...] = ()`. Builder merges sub-prop
  primitives into the parent mesh via `from_pydata` with index offsets and
  per-face `material_index`. Single `bg.prop.<name>` object retained.

### StylingPreset (v2)

- `schema` emitted as `"styling-preset-v2"`.
- `load` accepts `"styling-preset-v1"` and `"styling-preset-v2"`; v1 payloads
  map to `outline=None`.
- New field `outline: OutlineSpec | None`; serialized as
  `{enabled, thickness, color}` object (null fields omitted when None → still
  `{enabled: false}` serialized as `{"enabled": false}`).

### StylingState (v2 manifest)

- `outline: dict | None` — `{enabled, thickness, color}` (resolved values:
  concrete thickness float, hex color).
- `render: dict | None` — `{engine, resolution_x, resolution_y}` captured at
  save time from the styled blend.
- `schema` emitted as `"styling-v2"`; reader accepts v1 (missing keys → None).

## State transitions

```text
preset v1 load ──→ StylingPreset(outline=None)
preset v2 load ──→ StylingPreset(outline=OutlineSpec)
CLI --outline  ──→ OutlineSpec(enabled=True, ...)
                        │
OutlineApplier.apply(obj, spec) ──→ 'outline_toon' SOLIDIFY modifier
                                    + appended mat.outline slot
                        │
--reset / reset_styling() ──→ modifier removed, slot popped,
                              mat.outline datablock removed
                        │
StylingManifestWriter ──→ styling-v2 JSON {outline, render, ...}
```

## Validation rules

- `thickness` must be `> 0` and finite when provided (else `PresetError`).
- `color` must be catalog name or `#rrggbb` (else `PresetError`/`StylingError`).
- `fill_mode == "outline"` + `outline.enabled` → warning, outline skipped.
- `WxH` resolutions: each dimension 16–16384.
