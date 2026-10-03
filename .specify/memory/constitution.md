<!--
Sync Impact Report
- Version change: (none — initial ratification) → 1.0.0
- Modified principles: none (all principles newly authored)
- Added sections: Core Principles (I–VI), Technology Constraints, Development Workflow & Quality Gates, Governance
- Removed sections: none
- Follow-up TODOs: none
-->
# MyFirstAIDLCProject Constitution

## Core Principles

### I. Python-First Blender Automation (NON-NEGOTIABLE)

All interaction with Blender MUST be performed through Python scripting (`bpy` and supporting
libraries). No manual UI-driven steps may be part of the pipeline; every operation that produces or
modifies project artifacts (meshes, sprites, armatures, constraints, actions) MUST exist as a
reviewable, version-controlled Python script. Scripts MUST be executable headlessly via
`blender --background --python <script>` so results are reproducible without human interaction.

*Rationale: Manual Blender operations are unrepeatable and unreviewable. Scripting everything makes
the pipeline deterministic, testable, and suitable for AI-assisted development.*

### II. Strict Pipeline Stage Separation (NON-NEGOTIABLE)

The pipeline MUST be divided into three strictly separated stages, each implemented as an
independent module/package with a defined input/output contract:

1. **Character Generation** — produces 2D character geometry, sprites/textures, and part
   hierarchies (e.g., layered body parts). It MUST NOT create armatures, constraints, or
   animation data.
2. **Skeletal Rigging** — consumes a generated character and produces an armature, bone
   hierarchy, weights/parenting, and control bones. It MUST NOT modify character artwork or
   geometry, and MUST NOT create keyframes or animation logic.
3. **Animation Controllers** — consume a rigged character and produce drivers, constraints,
   actions, and animation state/control logic. They MUST NOT modify meshes or the base
   armature structure.

Cross-stage communication MUST occur only through documented artifact contracts (e.g., a saved
`.blend` file, exported JSON manifest, or named collections/objects with stable naming
conventions). No stage may reach into another stage's internals.

*Rationale: Separation keeps each stage independently testable and replaceable, prevents coupling
between art, rig, and motion concerns, and lets agents work on one stage without breaking others.*

### III. Blender MCP Integration

All live/agent-driven Blender interaction MUST go through the Blender MCP server. Agent code MUST
follow MCP safe-usage rules: call `get_addon_status()` and `get_scene_info()` before writing
scene-affecting code; look up shader nodes by `type`, never by localized display name; never
hardcode enum identifiers — read valid values from RNA or `try/except`; set colors on shader node
inputs when `use_nodes` is enabled; and verify results with `get_viewport_screenshot()` and
`get_scene_info()` after changes. MCP calls MUST be treated as the equivalent of running the
same Python in Blender directly — scripts executed through MCP must obey Principle I
(scriptable, reproducible) by being persisted as pipeline scripts, not one-off snippets.

*Rationale: Blender versions localize names and change enums; defensive MCP usage prevents brittle
automation, and persisting executed code keeps the pipeline reproducible.*

### IV. Deterministic & Reproducible Artifacts

Every generated artifact (character `.blend`, rig, animation set, exported sprite sheets or
manifests) MUST be reproducible from scripts plus checked-in inputs. Randomness MUST be seeded and
the seed recorded in the artifact's manifest. Naming conventions for objects, bones, and
collections MUST be stable, documented, and versioned so downstream stages can rely on them.

*Rationale: The stage contracts in Principle II only hold if artifacts and their naming are
predictable.*

### V. Test-First Validation

Each stage MUST ship with automated validation runnable in headless Blender: contract tests on
stage inputs/outputs (e.g., expected bone names exist, mesh vertex counts, driver counts), and
smoke tests that run a stage end-to-end on fixture inputs. A stage change MUST NOT be merged
unless its own tests and the contract tests of consuming stages pass.

*Rationale: With three decoupled stages, contract tests are the mechanism that detects contract
violations early.*

### VI. Simplicity & YAGNI

Build the simplest pipeline that satisfies the current specification. No speculative abstraction
layers, plugin systems, or multi-engine support unless the spec explicitly requires them. New
dependencies or stages MUST be justified against these principles.

## Technology Constraints

- **DCC**: Blender (version pinned per project; scripts must declare the minimum supported
  version). All automation via Python/`bpy`.
- **Agent interface**: Blender MCP server for live sessions; `blender --background` for CI.
- **Languages**: Python for all pipeline code. Data interchange between stages via `.blend`
  files and JSON manifests.
- **Forbidden**: UI-recorded macros, manual operator steps in the deliverable pipeline,
  hardcoded localized node names or enum identifiers, cross-stage writes into another stage's
  data structures.
- **Character format**: 2D layered parts; part names and layer ordering defined in the
  generation stage's output manifest.

## Development Workflow & Quality Gates

- Every feature follows the Spec Kit flow (`/speckit.specify` → `/speckit.plan` →
  `/speckit.tasks` → `/speckit.implement`); specs MUST state which pipeline stage(s) they touch.
- Code review MUST verify stage separation: generation diffs contain no rigging/animation
  changes, rigging diffs contain no mesh/animation changes, controller diffs contain no
  mesh/armature-structure changes.
- Quality gate: `blender --background` contract + smoke tests pass before merge.
- Any change to a stage's output contract (naming, manifest schema, bone hierarchy) is a
  breaking change: it MUST bump the contract version and update all consuming stages in the
  same change.

## Governance

This constitution supersedes ad-hoc practices in this repository. Amendments require a written
rationale, an update to this file with a semantic version bump (MAJOR for principle
removal/redefinition, MINOR for new or materially expanded sections, PATCH for clarifications),
and review approval before merge. All specs, plans, and reviews MUST verify compliance with the
principles above; violations discovered in review block merge. Complexity beyond these rules MUST
be justified in the relevant spec.

**Version**: 1.0.0 | **Ratified**: 2026-10-12 | **Last Amended**: 2026-10-12
