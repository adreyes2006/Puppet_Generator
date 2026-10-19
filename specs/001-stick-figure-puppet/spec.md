# Feature Specification: 2D Stick-Figure Puppet Generation

**Feature Branch**: `001-stick-figure-puppet`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Draft the specification for a Python script that automates the generation of a 2D stick-figure puppet in Blender. The script must accept parameters for limb length and thickness, automatically generate a 2D skeletal rig, and bind the geometry to the armature. Include acceptance criteria for testing the rig's movement."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Parameterized Stick-Figure Puppet (Priority: P1)

As a pipeline user, I run the generation script with parameters for limb lengths and limb
thickness and receive a Blender file containing a complete 2D stick-figure puppet: geometry for
the head, torso, upper/lower arms, hands, upper/lower legs, and feet, plus a skeletal rig with
all geometry bound to it — ready to be posed.

**Why this priority**: This is the entire core value of the feature. A single run that produces
a usable rigged puppet from parameters is the minimum viable product.

**Independent Test**: Run the script headlessly with a set of parameters, open the resulting
`.blend` file, and confirm the puppet geometry exists, an armature is present, and rotating a
limb bone moves the corresponding limb geometry.

**Acceptance Scenarios**:

1. **Given** Blender is available, **When** the script is run with default parameters, **Then** a
   `.blend` file is produced containing a symmetric, upright stick-figure puppet with all expected
   body parts, an armature, and geometry bound to the armature.
2. **Given** custom parameters (e.g., longer arms, thicker legs), **When** the script is run,
   **Then** the produced puppet's limb geometry measurably reflects those parameters.
3. **Given** the generated file, **When** a limb bone is rotated in pose mode, **Then** the
   corresponding limb geometry deforms/moves with the bone while the rest of the puppet is
   unaffected.

---

### User Story 2 - Automated Rig Movement Verification (Priority: P2)

As a pipeline user, I can run an automated check that poses the generated rig through a defined
set of bone rotations and verifies that the bound geometry follows each bone within a tolerance,
so regressions in generation or binding are caught without manual inspection.

**Why this priority**: The user explicitly asked for acceptance criteria for testing rig
movement. Automated verification makes the pipeline trustworthy and is a prerequisite for the
constitution's test-first quality gate.

**Independent Test**: Run the verification against a known-good generated puppet (passes) and
against a deliberately broken artifact, e.g., unbound geometry (fails).

**Acceptance Scenarios**:

1. **Given** a generated puppet, **When** each named limb bone is rotated through its test range,
   **Then** the vertices bound to that bone displace in the expected direction, and vertices
   bound to other bones do not move.
2. **Given** a generated puppet, **When** the root/hip bone is translated, **Then** the entire
   puppet moves with it.
3. **Given** a generated puppet, **When** a bone is rotated beyond a sane limit (e.g., elbow
   past straight), **Then** the verification reports it, or the rig's constraints prevent the
   pose — the behavior is explicit, not silent.

---

### User Story 3 - Manifest & Naming Contract for Downstream Stages (Priority: P3)

As a downstream pipeline stage (animation controllers), I receive a JSON manifest alongside the
`.blend` file listing every body part, bone name, and hierarchy, so controllers can target bones
by stable names without inspecting the file.

**Why this priority**: Required by the constitution's stage-separation and reproducibility
principles, but the puppet is usable without it.

**Independent Test**: Generate a puppet and diff the manifest's bone/part list against the
actual contents of the `.blend` file — they must match exactly.

**Acceptance Scenarios**:

1. **Given** a generation run, **Then** a manifest file lists every mesh object, every bone, and
   the bone parent/child hierarchy.
2. **Given** two runs with identical parameters and seed, **Then** the manifests and bone names
   are identical.

---

### Edge Cases

- Invalid or missing parameters (negative length, zero thickness, non-numeric input) must fail
  fast with a clear error message, not produce a broken puppet.
- Extreme but valid proportions (e.g., arm length ≫ torso length) must still produce a
  connected, fully bound rig — no detached or unweighted parts.
- Re-running the script in a non-empty scene must not leave duplicate or orphaned
  objects/bones from a prior run.
- Missing write permission or invalid output path must produce a clear error, not a partial file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The script MUST accept parameters controlling, at minimum: upper-arm length,
  forearm length, thigh length, shin length, and limb thickness (radius), with sensible defaults
  for each.
- **FR-002**: The script MUST reject invalid parameter values (non-positive lengths/thickness,
  non-numeric input) with a clear, non-zero-exit error before creating any scene objects.
- **FR-003**: The script MUST generate 2D stick-figure geometry comprising at minimum: head,
  torso, two upper arms, two forearms, two hands, two thighs, two shins, and two feet.
- **FR-004**: The script MUST generate a skeletal rig (armature) containing named bones for every
  movable part, in a hierarchy rooted at a hip/root bone, with left/right naming conventions
  (e.g., `upper_arm.L`).
- **FR-005**: All generated geometry MUST be bound to the armature so that each body part follows
  its corresponding bone; every generated mesh vertex MUST be assigned to exactly one bone
  (rigid binding is acceptable for a stick figure).
- **FR-006**: The script MUST run end-to-end in Blender background mode
  (`blender --background --python`) with no UI interaction.
- **FR-007**: The script MUST save the result to a configurable output `.blend` path.
- **FR-008**: The script MUST emit a JSON manifest listing all mesh objects, all bones, and the
  bone hierarchy.
- **FR-009**: Bone names, object names, and the manifest schema MUST follow a stable, documented
  naming convention consumable by downstream stages.
- **FR-010**: A rig-movement verification MUST exist that exercises every limb bone plus the root
  bone and asserts bound geometry follows, per the acceptance scenarios in User Story 2.
- **FR-011**: Re-running generation in the same Blender session MUST clean up prior generated
  objects and produce an identical result for identical parameters.
- **FR-012**: The script MUST NOT create keyframes, actions, drivers, or animation constraints —
  animation control is a separate pipeline stage per the constitution.

### Key Entities

- **Puppet**: The generated 2D character; a set of named mesh objects bound to an armature.
- **Armature/Rig**: The bone hierarchy (hip → spine/head, hip → thighs → shins → feet,
  chest → upper arms → forearms → hands); the pose interface.
- **Generation Parameters**: User-supplied limb lengths and thickness plus defaults; recorded in
  the manifest for reproducibility.
- **Manifest**: JSON sidecar describing objects, bones, hierarchy, parameters, and naming
  convention version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can produce a complete, rigged, poseable puppet from a single command in
  under 60 seconds on a standard workstation.
- **SC-002**: 100% of generated meshes are bound to the armature; zero unbound vertices.
- **SC-003**: The automated rig verification exercises 100% of bones and passes on a correctly
  generated puppet; it fails when binding is deliberately broken.
- **SC-004**: Varying limb parameters by ≥20% produces visibly and measurably different limb
  geometry (parameter effect is verifiable in output).
- **SC-005**: Re-running with identical inputs produces byte-identical manifests and identical
  bone/object naming.

## Assumptions

- A compatible Blender version is installed and invocable on the command line; the exact minimum
  version is declared by the script (per constitution, pinned in planning).
- "2D stick figure" means simple flat/cylindrical parts intended for a 2D look (front-facing,
  planar), not full 3D anatomy; rigid per-part bone binding is sufficient — no smooth skinning.
- Symmetric puppet: left and right limbs share the same length/thickness parameters.
- Output is a `.blend` file plus a JSON manifest next to it.
- Animation, posing presets, and control-bone abstractions are out of scope (separate stage).
