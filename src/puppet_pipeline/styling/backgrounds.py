from __future__ import annotations

from dataclasses import dataclass

from puppet_pipeline.styling import naming as styling_naming


def _rgba(r: int, g: int, b: int, a: float = 1.0) -> tuple[float, float, float, float]:
    return (r / 255.0, g / 255.0, b / 255.0, a)


@dataclass(frozen=True)
class SubPropSpec:
    dx: float
    dz: float
    scale_x: float
    scale_z: float
    color: tuple[float, float, float, float]
    shape: str = "rect"


@dataclass(frozen=True)
class PropSpec:
    name: str
    x: float
    z: float
    scale_x: float
    scale_z: float
    color: tuple[float, float, float, float]
    shape: str = "rect"
    sub_props: tuple[SubPropSpec, ...] = ()

    @property
    def scale(self) -> tuple[float, float]:
        return (self.scale_x, self.scale_z)


@dataclass(frozen=True)
class BackgroundSpec:
    name: str
    sky_color: tuple[float, float, float, float]
    ground_color: tuple[float, float, float, float]
    horizon_z: float
    depth_y: float
    props: tuple[PropSpec, ...]


def _prop(name, x, z, sx, sz, rgba, shape="rect", sub_props=()):
    return PropSpec(name, x, z, sx, sz, rgba, shape, sub_props)


def _sub(dx, dz, sx, sz, rgba, shape="rect"):
    return SubPropSpec(dx, dz, sx, sz, rgba, shape)


BACKGROUND_CATALOG: dict[str, BackgroundSpec] = {
    "kitchen": BackgroundSpec(
        name="kitchen",
        sky_color=_rgba(255, 236, 200),
        ground_color=_rgba(120, 72, 40),
        horizon_z=0.0,
        depth_y=1.5,
        props=(
            _prop(
                "fridge", -1.4, 1.0, 0.5, 1.0, _rgba(220, 220, 230),
                sub_props=(
                    _sub(0.12, 0.25, 0.30, 0.55, _rgba(200, 205, 215)),
                    _sub(-0.18, 0.25, 0.03, 0.35, _rgba(120, 125, 135)),
                ),
            ),
            _prop(
                "counter", 0.9, 0.45, 1.1, 0.45, _rgba(150, 90, 50),
                sub_props=(
                    _sub(0.0, 0.42, 1.15, 0.06, _rgba(200, 160, 110)),
                    _sub(-0.4, -0.05, 0.18, 0.30, _rgba(110, 60, 30)),
                ),
            ),
            _prop(
                "window", 0.0, 1.6, 0.5, 0.4, _rgba(150, 200, 240),
                sub_props=(
                    _sub(0.0, 0.0, 0.03, 0.4, _rgba(240, 240, 245)),
                    _sub(0.0, 0.0, 0.5, 0.03, _rgba(240, 240, 245)),
                ),
            ),
        ),
    ),
    "playground": BackgroundSpec(
        name="playground",
        sky_color=_rgba(135, 206, 250),
        ground_color=_rgba(90, 160, 70),
        horizon_z=0.0,
        depth_y=1.5,
        props=(
            _prop(
                "slide", -1.2, 0.8, 0.35, 0.8, _rgba(220, 80, 60),
                sub_props=(
                    _sub(0.45, -0.25, 0.35, 0.12, _rgba(240, 170, 60)),
                    _sub(-0.15, -0.7, 0.5, 0.08, _rgba(120, 60, 40)),
                ),
            ),
            _prop(
                "swing", 1.1, 0.9, 0.7, 0.08, _rgba(240, 200, 60),
                sub_props=(
                    _sub(-0.3, -0.45, 0.02, 0.42, _rgba(160, 120, 60)),
                    _sub(0.3, -0.45, 0.02, 0.42, _rgba(160, 120, 60)),
                    _sub(0.0, -0.85, 0.22, 0.05, _rgba(200, 90, 60)),
                ),
            ),
            _prop(
                "sun", 1.6, 2.2, 0.35, 0.35, _rgba(255, 220, 60), shape="circle",
                sub_props=(
                    _sub(0.0, 0.0, 0.22, 0.22, _rgba(255, 240, 140), shape="circle"),
                ),
            ),
        ),
    ),
    "office": BackgroundSpec(
        name="office",
        sky_color=_rgba(235, 235, 240),
        ground_color=_rgba(110, 110, 120),
        horizon_z=0.0,
        depth_y=1.5,
        props=(
            _prop(
                "desk", 0.9, 0.5, 1.0, 0.5, _rgba(160, 110, 70),
                sub_props=(
                    _sub(0.0, 0.48, 1.05, 0.05, _rgba(190, 140, 95)),
                    _sub(-0.4, -0.1, 0.08, 0.35, _rgba(110, 75, 45)),
                ),
            ),
            _prop(
                "monitor", 0.9, 1.15, 0.5, 0.3, _rgba(40, 40, 45),
                sub_props=(
                    _sub(0.0, 0.0, 0.42, 0.22, _rgba(90, 160, 220)),
                    _sub(0.0, -0.35, 0.08, 0.06, _rgba(60, 60, 65)),
                ),
            ),
            _prop(
                "cabinet", -1.3, 0.8, 0.5, 0.8, _rgba(180, 180, 190),
                sub_props=(
                    _sub(0.0, 0.2, 0.42, 0.22, _rgba(150, 150, 160)),
                    _sub(0.0, -0.25, 0.42, 0.22, _rgba(150, 150, 160)),
                ),
            ),
        ),
    ),
    "room": BackgroundSpec(
        name="room",
        sky_color=_rgba(240, 220, 190),
        ground_color=_rgba(140, 95, 60),
        horizon_z=0.0,
        depth_y=1.5,
        props=(
            _prop(
                "bed", -1.1, 0.5, 0.9, 0.5, _rgba(150, 170, 210),
                sub_props=(
                    _sub(-0.5, 0.15, 0.25, 0.18, _rgba(245, 245, 250)),
                    _sub(0.0, -0.2, 0.85, 0.15, _rgba(100, 130, 190)),
                ),
            ),
            _prop(
                "shelf", 1.2, 1.4, 0.5, 0.7, _rgba(120, 80, 50),
                sub_props=(
                    _sub(0.0, 0.2, 0.42, 0.05, _rgba(160, 120, 80)),
                    _sub(0.0, -0.2, 0.42, 0.05, _rgba(160, 120, 80)),
                ),
            ),
            _prop(
                "lamp", 1.6, 0.9, 0.15, 0.9, _rgba(250, 230, 140),
                sub_props=(
                    _sub(0.0, 0.55, 0.3, 0.25, _rgba(255, 200, 90)),
                    _sub(0.0, -0.85, 0.2, 0.06, _rgba(110, 90, 60)),
                ),
            ),
        ),
    ),
    "bathroom": BackgroundSpec(
        name="bathroom",
        sky_color=_rgba(200, 230, 240),
        ground_color=_rgba(160, 190, 200),
        horizon_z=0.0,
        depth_y=1.5,
        props=(
            _prop(
                "toilet", -1.2, 0.4, 0.4, 0.4, _rgba(240, 240, 245),
                sub_props=(
                    _sub(0.0, 0.35, 0.32, 0.25, _rgba(225, 228, 235)),
                    _sub(0.0, -0.15, 0.2, 0.2, _rgba(200, 205, 215)),
                ),
            ),
            _prop(
                "sink", 0.9, 0.9, 0.5, 0.45, _rgba(240, 240, 245),
                sub_props=(
                    _sub(0.0, 0.3, 0.08, 0.12, _rgba(170, 175, 185)),
                    _sub(0.0, -0.35, 0.35, 0.1, _rgba(200, 205, 215)),
                ),
            ),
            _prop(
                "mirror", 0.9, 1.7, 0.4, 0.35, _rgba(190, 220, 235),
                sub_props=(
                    _sub(0.0, 0.0, 0.44, 0.39, _rgba(150, 155, 165)),
                    _sub(0.0, 0.0, 0.36, 0.31, _rgba(200, 230, 245)),
                ),
            ),
        ),
    ),
}

_SPAN_X = 8.0
_SPAN_Z_TOP = 4.5
_SPAN_Z_BOTTOM = -1.0
_PROP_DEPTH_STEP = 0.01


def _flat_material(key: str, rgba) -> object:
    import bpy

    name = f"mat.bg_{key}"
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = next(
        node
        for node in material.node_tree.nodes
        if node.type == "BSDF_PRINCIPLED"
    )
    principled.inputs["Base Color"].default_value = rgba
    principled.inputs["Roughness"].default_value = 1.0
    emission = principled.inputs.get("Emission Color") or principled.inputs.get(
        "Emission"
    )
    if emission is not None:
        emission.default_value = rgba
    strength = principled.inputs.get("Emission Strength")
    if strength is not None:
        strength.default_value = 0.5
    material.diffuse_color = rgba
    return material


def _quad_primitive(x: float, z: float, sx: float, sz: float, y: float):
    verts = [
        (x - sx, y, z - sz),
        (x + sx, y, z - sz),
        (x + sx, y, z + sz),
        (x - sx, y, z + sz),
    ]
    return verts, [(0, 1, 2, 3)]


def _circle_primitive(x: float, z: float, r: float, y: float, segments: int = 24):
    import math

    verts = [(x, y, z)] + [
        (x + r * math.cos(a), y, z + r * math.sin(a))
        for a in [2 * math.pi * i / segments for i in range(segments)]
    ]
    faces = [(0, i + 1, (i + 1) % segments + 1) for i in range(segments)]
    return verts, faces


def _quad_mesh(name: str, x: float, z: float, sx: float, sz: float, y: float):
    import bpy

    verts, faces = _quad_primitive(x, z, sx, sz, y)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def _primitive(shape: str, x, z, sx, sz, y):
    if shape == "circle":
        return _circle_primitive(x, z, sx, y)
    return _quad_primitive(x, z, sx, sz, y)


def _prop_mesh(name: str, prop: PropSpec, y: float):
    """Compose a prop and its sub_props into one mesh with per-face materials."""
    import bpy

    primitives = [(prop.x, prop.z, prop.scale_x, prop.scale_z, prop.shape)]
    primitives += [
        (prop.x + sub.dx, prop.z + sub.dz, sub.scale_x, sub.scale_z, sub.shape)
        for sub in prop.sub_props
    ]
    verts: list = []
    faces: list = []
    face_materials: list[int] = []
    for material_index, (px, pz, sx, sz, shape) in enumerate(primitives):
        pverts, pfaces = _primitive(shape, px, pz, sx, sz, y)
        offset = len(verts)
        verts.extend(pverts)
        for face in pfaces:
            faces.append(tuple(offset + i for i in face))
            face_materials.append(material_index)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for polygon, material_index in zip(mesh.polygons, face_materials):
        polygon.material_index = material_index
    return mesh


def _spawn(name: str, mesh, rgba, collection) -> None:
    import bpy

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    colors = rgba if isinstance(rgba, (list, tuple)) and rgba and isinstance(rgba[0], (list, tuple)) else [rgba]
    for index, color in enumerate(colors):
        obj.data.materials.append(
            _flat_material(f"{name.replace('.', '_')}_{index}", color)
        )


class BackgroundBuilder:
    """Builds planar silhouette backgrounds in PUPPET.STYLE.BACKGROUND."""

    @staticmethod
    def build(scenario: str | None):
        """Replace any bg.* objects with the named scenario; None clears only."""
        import bpy

        from puppet_pipeline.styling.scene import setup_style_collections

        BackgroundBuilder.clear()
        if scenario is None:
            return None
        spec = BACKGROUND_CATALOG.get(scenario)
        if spec is None:
            raise ValueError(f"Unknown background scenario: {scenario!r}")

        setup_style_collections()
        collection = bpy.data.collections[styling_naming.BACKGROUND_COLLECTION_NAME]
        y = spec.depth_y

        _spawn(
            styling_naming.background_name("sky"),
            _quad_mesh(
                "bg.sky",
                0.0,
                (spec.horizon_z + _SPAN_Z_TOP) / 2,
                _SPAN_X,
                (_SPAN_Z_TOP - spec.horizon_z) / 2,
                y,
            ),
            spec.sky_color,
            collection,
        )
        _spawn(
            styling_naming.background_name("ground"),
            _quad_mesh(
                "bg.ground",
                0.0,
                (spec.horizon_z + _SPAN_Z_BOTTOM) / 2,
                _SPAN_X,
                (spec.horizon_z - _SPAN_Z_BOTTOM) / 2,
                y,
            ),
            spec.ground_color,
            collection,
        )
        for index, prop in enumerate(spec.props):
            prop_y = y - _PROP_DEPTH_STEP * (index + 1)
            name = styling_naming.prop_name(prop.name)
            mesh = _prop_mesh(name, prop, prop_y)
            colors = [prop.color] + [sub.color for sub in prop.sub_props]
            _spawn(name, mesh, colors, collection)
        return scenario

    @staticmethod
    def clear() -> None:
        """Remove every bg.* object and its orphaned mesh data."""
        import bpy

        for obj in [
            o for o in bpy.data.objects if o.name.startswith("bg.")
        ]:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
