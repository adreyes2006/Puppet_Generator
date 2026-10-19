# Research: 2D Stick-Figure Puppet Generation

All Technical Context items are resolved; no technical questions remain.

## Decision: Blender 4.2+ compatibility, validated on Blender 5.2.2 LTS with Python 3.13

- **Rationale**: The runtime keeps 4.2 as its minimum while real integration and MCP validation use
  Blender 5.2.2 LTS. The bundled interpreter removes dependency management. Version is guarded at
  runtime via `bpy.app.version`.
- **Alternatives**: Blender 3.6 LTS (older, still common in studios — rejected: 4.x API is what
  new work should target); system Python + `bpy` wheel (rejected: `pip install bpy` wheel lags
  releases and complicates CI vs. `blender --background`).

## Decision: Character lives in the XZ plane, depth along +Y

- **Rationale**: Matches Blender's front view (camera looking along +Y). Bones with y=0 and a
  roll aligning local Z to world +Y make every joint a single-axis hinge — the precondition for
  planar IK.
- **Alternatives**: XY plane with Z-depth (works, but "front view" muscle memory and default
  rigs favor XZ); Grease Pencil armature workflow (rejected: adds a second object model,
  violates YAGNI for a stick figure).

## Decision: Built-in legacy IK solver with per-axis limits + pole targets

- **Rationale**: Modern Blender ships the built-in IK solver (iTaSC was removed after 2.79).
  Slight symmetric rest-pose pre-bends avoid straight-chain singularities; in-plane pole targets
  select bend direction, and movement tests enforce negligible Y displacement. `chain_count=2`
  gives classic two-bone limbs.
- **Alternatives**: FK-only rig (simpler but user asked for IK and it materially improves
  posing); custom 2D analytic IK via drivers (rejected: drivers are the animation stage per
  constitution, and drivers computing transforms would leak animation logic into rigging).

## Decision: Rigid vertex-group binding (one bone per vertex, weight 1.0)

- **Rationale**: Stick-figure parts are rigid capsules; `ARMATURE` modifier + vertex groups is
  the simplest correct binding and makes the rig verifier's assertions unambiguous.
- **Alternatives**: `bpy.ops.object.parent_set(type='ARMATURE_AUTO')` auto-weights (rejected:
  non-deterministic weights, harder to verify); bone parenting per part (viable for rigid
  parts, but vertex groups keep a uniform binding mechanism when smooth skinning is added later
  — recorded as compatible future path, not built now).

## Decision: Mesh creation via `mesh.from_pydata` + `bmesh`-free primitives

- **Rationale**: Direct vertex/face construction is deterministic and headless-safe;
  `bpy.ops` context dependence is minimized to what's unavoidable (edit-mode toggle).
- **Alternatives**: `bpy.ops.mesh.primitive_*` for every part (context-sensitive, slower,
  leaves operator state); `bmesh` (fine, but `from_pydata` is simpler for capsule cross-sections).

## Decision: Testing split — pytest for pure logic, in-Blender harness for scene tests

- **Rationale**: `bpy` only exists inside Blender; params/naming/manifest modules are pure
  Python and testable in CI directly. Scene tests run via
  `blender --background --python tests/blender/run_in_blender.py` which imports test modules,
  runs assertions, exits non-zero on failure.
- **Alternatives**: pytest-blender plugin (nice but adds a dependency; revisit if test count
  grows); Blender MCP for tests (rejected: MCP is for interactive sessions, not CI — and a
  test shouldn't depend on a running MCP server).

## Decision: Manifest is JSON Schema v1, single sidecar file

- **Rationale**: Satisfies FR-008/009 and constitution stage contracts; JSON is the agreed
  interchange format in the constitution's Technology Constraints.
- **Alternatives**: `.blend` custom properties only (rejected: downstream stages shouldn't need
  Blender to read the contract); YAML (extra dependency for zero gain).
