# Data Model: Puppet Material and Accessory Styling

**Feature**: `specs/002-puppet-material-styling` | **Date**: 2026-10-17

## Entities

### MaterialPreset

A named, immutable material definition applied to body parts.

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | str | Unique in catalog; matches `mat.*` naming |
| `base_color` | (r,g,b,a) float ×4 | Each channel 0.0–1.0 |
| `roughness` | float | 0.0–1.0 |
| `metallic` | float | 0.0–1.0 |
| `emission_color` | (r,g,b,a) | For `glowing` presets; zero otherwise |
| `emission_strength` | float | ≥ 0; 0 disables emission |
| `fill_mode` | `solid \| outline` | Per-preset default; user may override globally |

**Validation**: name non-empty; all numeric channels finite and in range; `outline` presets still
carry a `base_color` used to tint the wireframe.

### AccessorySpec / Accessory

A procedurally generated rigid prop attached to one rig bone.

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | str | `acc.<style>[.L\|.R]` per naming v1 extension |
| `style` | `shoe \| hat` catalog id | Must exist in accessory catalog |
| `attach_bone` | str | `foot.L`, `foot.R` (shoes), `head` (hats) — must be a deforming bone |
| `offset` | (x,y,z) float ×3 | Bone-space translation from joint origin |
| `scale` | (x,y,z) float ×3 | Proportional to `limb_thickness` |
| `primitives` | list[PrimitiveSpec] | 1–4 composed primitives |

**Validation**: `attach_bone` must exist in `rig.data.bones` with `use_deform=True`; scale > 0;
offset finite. Accessories never receive vertex groups or Armature modifiers (rigid bone parenting
only). Accessories are excluded from the Wireframe modifier pass.

### BackgroundSpec / BackgroundPreset

A procedural 2D silhouette scene placed behind the puppet.

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | str | Catalog id: `kitchen`, `playground`, `office`, `room`, `bathroom`, … |
| `sky_color` / `ground_color` | (r,g,b,a) | Flat material colors for background bands |
| `horizon_z` | float | Z height where sky meets ground |
| `depth_y` | float | Fixed Y distance behind puppet plane (default 1.5) |
| `props` | list[PropSpec] | 0–n flat silhouette shapes |

`PropSpec` fields: `kind` (`box|cylinder|sphere_half|capsule`), `position` (x,z), `scale` (x,z),
`color` (r,g,b,a). All props share `depth_y` so the scene stays planar.

**Validation**: all colors in range; `depth_y > 0`; prop scales > 0; name must exist in catalog.

### StylingPreset (file)

The complete savable styling state — `preset.schema.json`.

```json
{
  "schema": "styling-preset-v1",
  "fill_mode": "solid",
  "materials": { "head": "skin_light", "torso": "blue", "…": "…" },
  "accessories": [
    { "style": "sneakers", "attach_bone": "foot.L" },
    { "style": "cap", "attach_bone": "head" }
  ],
  "background": "playground"
}
```

**Validation**: `schema` exact match; material preset names and accessory styles must exist in
their catalogs; `attach_bone` must match the accessory style's allowed bones; `fill_mode ∈
{solid, outline}`; unknown keys rejected (strict parse). Filename validated as portable
(`[A-Za-z0-9._-]+`) before write.

### StylingManifest (file)

Emitted artifact — `styling.schema.json`.

| Field | Type | Notes |
|-------|------|-------|
| `schema` | `"styling-v1"` | Fixed |
| `source_manifest` | str | Path of the generation manifest this styling targets |
| `blender_version` | str | e.g. `5.2.2` |
| `fill_mode` | `solid\|outline` | Active mode |
| `materials` | object | part name → applied preset name (only non-default parts listed) |
| `accessories` | list | Active accessories: style + attach_bone |
| `background` | str \| null | Active scenario or null |
| `preview_files` | list[str] | PNGs produced for this styling state |

## Relationships

```text
StylingPreset (input file)
      │  applies
      ▼
┌─ MaterialPreset ──→ assigned to each pup.* object (0..1 material slots each)
├─ Accessory ───────→ BONE-parented to rig.data.bones[foot.L|foot.R|head]
└─ BackgroundSpec ──→ bg.* objects in PUPPET.STYLE.BACKGROUND
      │
      ▼
StylingManifest (output file) ──references──→ source generation manifest
```

## State transitions

```text
unstyled ──apply──▶ styled ──apply other──▶ styled (re-styled)
   ▲                  │
   └──── reset() ◄────┘        styled ──save──▶ preset file ──load──▶ styled
```

`reset()` is total: removes `mat.*` beyond defaults, all `acc.*` and `bg.*` objects, all Wireframe
modifiers, and the `PUPPET.STYLE` collection tree; base geometry, rig, and weights are untouched.
