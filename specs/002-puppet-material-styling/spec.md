# Feature Specification: Puppet Material and Accessory Styling

**Feature Branch**: `feature/puppet-material-styling`

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Build a material and accessory styling system for the puppet feature. Users should be able to browse and apply different visual materials (like colors and thickness) and choose whether the puppet is color-filled or not. Additionally, users must be able to customize specific accessories like shoes and hats, and change the background, backgrounds could be scenarios, like a kitchen, a playground, an office, toom, bathroom or others. The goal is to allow deeper user customization and unique character looks. The system must provide clear visual previews of all materials, accessories, and backgrounds before application, and allow users to save or reset their styling choices."

## Clarifications

### Session 2026-10-17

- Q: How will users interact with the styling system? → A: CLI arguments + JSON styling preset file; previews written as PNG images to `build/previews/`
- Q: Where do accessory meshes come from? → A: Procedurally generate accessories from primitives (box/cylinder/sphere) with parameters — fully deterministic, no external files
- Q: What does outline/wireframe fill mode mean technically? → A: Geometry-based — a Wireframe modifier or edge-only rebuild renders the puppet as edges instead of solid fills
- Q: How should styling output relate to the existing schema-v1 manifest? → A: Separate `<name>.styling.json` file written alongside the generation manifest — preserves schema-v1, keeps styling lifecycle independent
- Q: How should background scenarios be represented? → A: Procedural 2D silhouette scenes (flat colored shapes forming scenario elements like horizon, slide, swing) built from primitives — deterministic, reads as a scene

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply Body Materials (Priority: P1)

As a user, I want to apply colors and visual styles to the generated puppet's body parts so that it matches my creative vision instead of appearing as unstyled geometry.

**Why this priority**: Material application is the core value of the styling system; without it, the puppet cannot be visually customized.

**Independent Test**: Can be fully tested by loading a generated puppet, assigning a color material to at least one body part, and verifying the viewport/rendered output changes. This delivers immediate visual customization without accessories or backgrounds.

**Acceptance Scenarios**:

1. **Given** a generated puppet with default grey materials, **When** I select a red material for the torso and apply it, **Then** the torso displays the red material while other parts remain unchanged.
2. **Given** a styled puppet, **When** I change the fill mode from filled to outline-only, **Then** the puppet renders as wireframe/outlined shapes instead of solid colored meshes.

---

### User Story 2 - Add Accessories (Priority: P2)

As a user, I want to add shoes and hats to my puppet so that it gains personality and distinctive visual details.

**Why this priority**: Accessories differentiate the puppet's appearance beyond flat body colors, supporting the goal of "unique character looks."

**Independent Test**: Can be fully tested by loading a generated puppet, selecting a shoe accessory for one foot, and verifying a shoe mesh appears attached to that foot and moves with it.

**Acceptance Scenarios**:

1. **Given** a generated puppet, **When** I select the "sneakers" accessory for the feet, **Then** left and right foot geometry gains shoe meshes that follow foot movement.
2. **Given** a puppet with a hat accessory, **When** I remove the hat, **Then** the head returns to its original unadorned state without affecting body materials.

---

### User Story 3 - Change Background Scene (Priority: P3)

As a user, I want to place my puppet against different background scenarios like a kitchen or playground so that the final render tells a story.

**Why this priority**: Backgrounds provide environmental context for the character but are not required for the character itself to be customized.

**Independent Test**: Can be fully tested by loading a styled puppet, selecting a "kitchen" background, and verifying the world background or backdrop plane changes while the puppet remains unchanged.

**Acceptance Scenarios**:

1. **Given** a styled puppet in a blank scene, **When** I select the "playground" background, **Then** a playground backdrop appears behind the puppet in the viewport and rendered output.
2. **Given** a puppet with a background active, **When** I clear the background, **Then** the scene returns to the default empty background.

---

### User Story 4 - Preview Before Applying (Priority: P4)

As a user, I want to see what materials, accessories, and backgrounds will look like before I apply them so that I can make informed styling decisions without trial-and-error.

**Why this priority**: Previews reduce frustration and rework, but the system can technically apply styles directly without previews.

**Independent Test**: Can be fully tested by requesting a preview of a material choice and verifying a PNG preview image is written to `build/previews/` without modifying the scene's permanent state.

**Acceptance Scenarios**:

1. **Given** a generated puppet and the CLI, **When** I request a preview of "blue metallic" on the torso, **Then** a PNG preview image showing the blue metallic torso is written to `build/previews/` and no permanent material change is applied.
2. **Given** the background browser, **When** I preview the "office" background, **Then** a PNG preview image of the office backdrop is written to `build/previews/` and the active scene background remains unchanged.

---

### User Story 5 - Save and Reset Styling (Priority: P5)

As a user, I want to save my styling choices as a preset and reset to defaults so that I can experiment freely without losing my preferred look.

**Why this priority**: Persistence and experimentation are quality-of-life features that support iterative design but are not essential for a single styling session.

**Independent Test**: Can be fully tested by styling a puppet, saving the configuration to a file, resetting to defaults, reloading the file, and verifying all choices are restored.

**Acceptance Scenarios**:

1. **Given** a fully styled puppet with materials, accessories, and background, **When** I save the styling as "my_look.json" and then reset, **Then** the puppet returns to defaults and all styling can be restored by loading "my_look.json."
2. **Given** a saved styling preset, **When** I apply it to a different puppet of the same spec, **Then** the same materials, accessories, and background are applied successfully.

---

### Edge Cases

- What happens when the user tries to apply styling to a scene that contains no generated puppet? (System MUST fail gracefully and prompt to generate first.)
- What happens when an accessory doesn't fit the current limb thickness? (System MUST warn or auto-scale.)
- What happens when a background image file is missing or corrupt? (System MUST fallback to blank background and report the error.)
- What happens when the user saves a preset with an invalid or unsupported name? (System MUST validate filename before writing.)
- What happens when styling is applied to a puppet with modified geometry? (System MUST either adapt or clearly warn that styling may be broken.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to assign a color material to each of the 14 body parts independently.
- **FR-002**: System MUST support two fill modes: solid color fill (default) and outline mode implemented via a Wireframe modifier or edge-only geometry, not a shader-only transparency trick.
- **FR-003**: System MUST provide a catalog of predefined material presets (e.g., matte colors, skin tones, metallic, glowing).
- **FR-004**: System MUST allow users to add and remove shoes and hats to the puppet as separate accessory objects.
- **FR-005**: System MUST procedurally generate all accessory geometry from parameterized primitives (box, cylinder, sphere); no external mesh assets may be imported.
- **FR-006**: System MUST parent accessories to the appropriate bones (feet for shoes, head for hats) so they follow limb movement.
- **FR-007**: System MUST provide a catalog of predefined background scenarios (e.g., kitchen, playground, office, room, bathroom), each rendered as a procedural 2D silhouette scene composed of flat-colored primitive shapes; no external images may be used.
- **FR-008**: System MUST render visual previews of materials, accessories, and backgrounds as PNG image files under `build/previews/` before confirming application; preview is non-interactive.
- **FR-009**: System MUST allow users to save a complete styling configuration (materials + accessories + background) to a JSON file.
- **FR-010**: System MUST allow users to reset the puppet to its default unstyled state without affecting the underlying rig or geometry.
- **FR-011**: System MUST validate that a generated puppet exists in the scene before allowing styling operations.
- **FR-012**: System MUST keep styling changes separate from the base geometry so that regenerating the puppet does not destroy styling data unnecessarily.
- **FR-013**: System MUST emit a separate `<name>.styling.json` manifest alongside the generation `.blend`/manifest recording active materials, accessories, and background; the schema-v1 generation manifest MUST NOT be modified.

### Key Entities *(include if feature involves data)*

- **MaterialPreset**: A named set of shader parameters (base color, roughness, metallic, emission) plus fill mode; does not include geometry.
- **Accessory**: A procedurally generated mesh (shoe, hat) with attachment metadata defining which bone it parents to and any offset/transform data.
- **BackgroundPreset**: A procedural 2D silhouette scene definition (flat-colored primitive shapes forming scenario elements) that can be swapped in/out; no external images.
- **StylingPreset**: A JSON file capturing the complete visual state: material assignments per body part, active accessories, selected background.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can apply a color material to any body part in under 10 seconds via CLI or script interface.
- **SC-002**: The system supports at least 10 material presets, 3 shoe styles, 3 hat styles, and 5 background scenarios at launch.
- **SC-003**: Each preview render completes in under 60 seconds headless on a standard workstation, without modifying the scene's saved state.
- **SC-004**: Saved styling presets can be loaded and applied to a fresh puppet with 100% fidelity (same materials, accessories, background).
- **SC-005**: Reset operation restores the puppet to a completely unstyled state with no residual materials, accessories, or background artifacts.
- **SC-006**: All styling operations pass automated tests verifying material assignment, accessory parenting, background switching, preview generation, and preset round-trip.

## Assumptions

- Users have already generated a puppet using `generate_puppet.py`; styling operates on that output.
- The feature is accessed via Python CLI/script interface, not a custom GUI (consistent with project constitution).
- "Toom" in the description is interpreted as "room" (a typo).
- Backgrounds are procedural 2D silhouette scenes built from flat-colored primitives; no external images or complex 3D environments.
- Accessories are generated procedurally from primitives; no external mesh assets are bundled or downloaded.
- The system does not create animation data; accessories follow bones via parenting only.
- Styling presets are stored as JSON files in the project workspace.
