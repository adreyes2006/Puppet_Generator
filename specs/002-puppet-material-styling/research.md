# Research: Puppet Material and Accessory Styling

**Date**: 2026-10-17 | **Feature**: `specs/002-puppet-material-styling`

## Decision 1: Material application via Principled BSDF node inputs

**Decision**: Create `mat.*` material datablocks with `use_nodes=True` and set `base_color`,
`roughness`, `metallic`, and emission on the Principled BSDF shader **inputs** — never on
`material.diffuse_color` and never looked up by localized node name.

**Rationale**: With `use_nodes` enabled (default in Blender ≥2.8), `diffuse_color` only affects
viewport display and is ignored by renders. Node names are localized on non-English installs, so
`nodes["Principled BSDF"]` can return `None`; lookup by `node.type == "BSDF_PRINCIPLED"` is stable.
This is the same MCP safe-usage rule already encoded in the constitution (Principle III).

**Alternatives considered**: `diffuse_color` viewport-only styling — rejected (renders show default
grey); localized-name lookup — rejected (breaks on non-English UI).

## Decision 2: Outline mode via Wireframe modifier

**Decision**: Outline fill mode adds a `WIREFRAME` modifier to each of the 14 `pup.*` mesh objects
(`thickness` proportional to `limb_thickness`, `use_replace=True`). Solid mode removes the modifier.
Accessory and background meshes never receive the modifier.

**Rationale**: Clarification answer B. A modifier is geometry-level, deterministic, togglable,
and easily testable (`len(obj.modifiers) == 1 and obj.modifiers[0].type == 'WIREFRAME'`). It
coexists safely with the existing Armature modifier (order: Armature first, then Wireframe).
`use_replace=False` produces a cage+skin look which is a third unrequested mode — rejected.

**Alternatives considered**: Shader transparency + emission edges — complex node graphs, render-
engine differences; Freestyle — EEVEE/Workbench unsupported, Cycles-only line sets; edge-only mesh
rebuild — destroys the base mesh topology the binding contract depends on.

## Decision 3: Procedural accessories from composed primitives

**Decision**: Shoes and hats are built by creating primitive meshes (`bpy.ops.mesh.primitive_*` or
`from_pydata`), scaling/locating them, and joining into a single `acc.*` object. Shoes use box +
scaled cylinder (toe cap); hats use scaled sphere/cylinder + flat brim disc. No `bmesh` dependency —
object-level compose + `bpy.ops.object.join` is simpler and sufficient for 3-piece silhouettes.

**Rationale**: Spec clarification A — deterministic, parameter-driven, zero external assets.
Joined single objects keep the scene graph small and give one parent target per accessory.

**Alternatives considered**: Bundled `.obj`/`.blend` accessory assets — rejected (external files,
licensing, nondeterminism); `bmesh` boolean union — more code for no visible gain at silhouette
resolution.

## Decision 4: Bone-space parenting for accessories

**Decision**: Accessories parent to the **armature object** with `parent_type='BONE'` and
`parent_bone` set to `foot.L`/`foot.R`/`head`. The object's `matrix_parent_inverse` is composed so
the accessory sits at the anatomically correct offset at rest pose.

**Rationale**: Bone parenting makes the accessory follow limb movement automatically with zero
constraints or drivers (no animation data, per constitution). `parent_type='BONE'` is the
documented `bpy` mechanism for bone-space attachment; alternatives (Child Of constraint on the
armature's bone) also work but add a constraint the rig doesn't otherwise need.

**Alternatives considered**: Vertex-group binding to the same deform bone — rejected (accessories
are rigid props, not skin); Child Of constraint — works but unnecessary complexity vs. built-in
bone parenting.

## Decision 5: Backgrounds as flat silhouette meshes at +Y depth

**Decision**: Each `BackgroundSpec` emits flat `bg.*` meshes (ground plane, horizon band, prop
silhouettes from scaled boxes/cylinders/UV-sphere halves) placed at a fixed `y = +depth` behind the
puppet's XZ plane, all in `PUPPET.STYLE.BACKGROUND`. Colors come from simple emission-free
materials so Workbench previews render correctly.

**Rationale**: Spec clarification B — the scene must *read* as a scenario, which a world color
cannot do; procedural shapes keep determinism and no-asset rules. Flat meshes parallel to the
viewing plane suit a 2D puppet and remain cheap to render.

**Alternatives considered**: World color/gradient — rejected (fails "reads as a scene");
image-plane textures — rejected (external assets); full 3D mini-environments — rejected (scope,
per spec assumption).

## Decision 6: Previews via offscreen Workbench render

**Decision**: `PreviewRenderer` sets the scene's render engine to `BLENDER_WORKBENCH` (fallback
`BLENDER_EEVEE_NEXT` if unavailable — read accepted engines via `try/except TypeError` per MCP
rules), frames the puppet bounds with the existing `PUPPET` camera or a temporary camera, renders a
still PNG to `build/previews/`, then restores every mutated render/scene setting.

**Rationale**: Workbench renders solid-color studio shading in milliseconds and honors
`mat.*` material colors for viewport-style previews — fastest deterministic option that works in
`--background` without GPU requirements beyond what EEVEE already needs. Non-destructive restore
satisfies the "preview does not change permanent state" requirement.

**Alternatives considered**: EEVEE preview — heavier, GPU/driver sensitive in headless CI;
viewport screenshot via MCP — requires live session, can't run in `--background` CI.

## Decision 7: Styling manifest as sibling JSON (schema `styling-v1`)

**Decision**: Write `<name>.styling.json` next to the generation manifest. Fields: `schema`
(`"styling-v1"`), `source_manifest` (path/fingerprint of the puppet manifest), `blender_version`,
`materials` (part→preset), `fill_mode`, `accessories`, `background`, `preview_files`.

**Rationale**: Spec clarification B — keeps schema-v1 immutable (constitution breaking-change
rule: contract changes must bump versions; we avoid touching it entirely) and lets styling be
applied/cleared without regenerating the base manifest.

**Alternatives considered**: Extend schema-v1 — rejected (breaking change cascades to all
consumers); custom properties inside `.blend` — rejected (not diffable, hard to validate in CI).
