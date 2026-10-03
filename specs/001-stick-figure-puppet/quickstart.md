# Quickstart: Validate the 2D Stick-Figure Puppet

This guide describes the commands and observable outcomes that will validate the completed feature.
The implementation files do not exist yet; create them through `/speckit.tasks` and
`/speckit.implement` before running these scenarios.

## Prerequisites

- Blender 4.2 or newer is installed (validated on Blender 5.2.2 LTS).
- `blender` is available on `PATH`, or replace it below with the absolute executable path.
- Run commands from the repository root.
- Python dependencies for pure unit tests are installed in the development environment.

## 1. Run Pure-Python Unit Tests

```bash
python -m pytest tests/unit
```

Expected outcome:

- Parameter validation accepts defaults and positive custom values.
- Zero, negative, and non-numeric dimensions are rejected before scene generation.
- Naming tests match [contracts/naming.md](contracts/naming.md).
- Manifest fixtures validate against
  [contracts/manifest.schema.json](contracts/manifest.schema.json).
- Process exits with code `0`.

## 2. Generate the Default Puppet Headlessly

```bash
blender --background --factory-startup --python generate_puppet.py -- \
  --output build/default-puppet.blend \
  --manifest build/default-puppet.manifest.json
```

Expected outcome:

- Command exits with code `0` in under 60 seconds.
- `build/default-puppet.blend` and `build/default-puppet.manifest.json` exist.
- The manifest reports `schema_version: 1`, `naming_version: 1`, and the default dimensions.
- The `.blend` contains `PUPPET.GEOMETRY` and `PUPPET.RIG`, one `rig` armature, all required
  geometry objects, and all required deform/control bones.
- No actions, keyframes, drivers, or `PUPPET.ANIMATION` collection exist.

## 3. Generate a Custom-Proportion Puppet

```bash
blender --background --factory-startup --python generate_puppet.py -- \
  --upper-arm-length 1.5 \
  --forearm-length 1.3 \
  --thigh-length 1.6 \
  --shin-length 1.4 \
  --limb-thickness 0.10 \
  --seed 42 \
  --output build/custom-puppet.blend \
  --manifest build/custom-puppet.manifest.json
```

Expected outcome:

- Command exits with code `0`.
- The manifest records exactly the supplied values and seed.
- Arms and legs measure at least 20% longer/thicker than the relevant defaults.
- All parts remain connected and bound despite changed proportions.

## 4. Run Blender Contract and Movement Tests

```bash
blender --background --factory-startup --python tests/blender/run_in_blender.py -- \
  --blend build/default-puppet.blend \
  --manifest build/default-puppet.manifest.json
```

Expected outcome:

- Every manifest object and bone is present and follows naming contract v1.
- Every mesh vertex belongs to exactly one matching bone vertex group at weight `1.0`.
- Every mesh has one armature modifier targeting `rig`.
- Moving `hips` translates every evaluated mesh vertex by the same vector.
- Rotating each FK bone ±15° around its permitted planar axis moves its bound geometry while
  unrelated rigid parts remain stationary within the documented epsilon.
- Moving `hand_ctrl.L/R` and `foot_ctrl.L/R` solves each two-bone IK chain in the XZ plane.
- IK evaluation produces no meaningful Y displacement and uses the intended elbow/knee bend side.
- Test process exits with code `0`.

## 5. Verify Determinism and Safe Re-run

Run the default generation command twice, writing manifests to two paths:

```bash
blender --background --factory-startup --python generate_puppet.py -- \
  --output build/repeat-a.blend --manifest build/repeat-a.json --seed 0
blender --background --factory-startup --python generate_puppet.py -- \
  --output build/repeat-b.blend --manifest build/repeat-b.json --seed 0
```

Compare manifests:

```bash
python -c "from pathlib import Path; assert Path('build/repeat-a.json').read_bytes() == Path('build/repeat-b.json').read_bytes()"
```

Expected outcome:

- The manifests are byte-identical.
- Contract tests find no Blender-generated numeric suffixes such as `.001`.
- Running generation twice in one Blender process leaves exactly one puppet hierarchy.

## 6. Verify Failure Behavior

```bash
blender --background --factory-startup --python generate_puppet.py -- \
  --upper-arm-length -1 --output build/invalid.blend
```

Expected outcome:

- Command exits non-zero with a message identifying `upper_arm_length` as invalid.
- `build/invalid.blend` is not created.
- No partial manifest is created.

## Optional Interactive MCP Inspection

For an agent-driven inspection, first call Blender MCP `get_addon_status()` and
`get_scene_info()`, load `build/default-puppet.blend`, then use `get_viewport_screenshot()` and
`get_scene_info()` after posing the controls. This visual check supplements but does not replace
the headless tests above.
