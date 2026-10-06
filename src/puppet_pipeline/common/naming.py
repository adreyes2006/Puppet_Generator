import re

NAMING_VERSION = 1

ROOT_COLLECTION_NAME = "PUPPET"
GEOMETRY_COLLECTION_NAME = "PUPPET.GEOMETRY"
RIG_COLLECTION_NAME = "PUPPET.RIG"
ARMATURE_OBJECT_NAME = "rig"
ARMATURE_DATA_NAME = "rig.data"
ANIMATION_COLLECTION_NAME = "PUPPET.ANIMATION"
RESERVED_BONE_PREFIX = "anim_"

GEOMETRY_BINDINGS = {
    "pup.head": "head",
    "pup.torso": "spine",
    "pup.upper_arm.L": "upper_arm.L",
    "pup.upper_arm.R": "upper_arm.R",
    "pup.forearm.L": "forearm.L",
    "pup.forearm.R": "forearm.R",
    "pup.hand.L": "hand.L",
    "pup.hand.R": "hand.R",
    "pup.thigh.L": "thigh.L",
    "pup.thigh.R": "thigh.R",
    "pup.shin.L": "shin.L",
    "pup.shin.R": "shin.R",
    "pup.foot.L": "foot.L",
    "pup.foot.R": "foot.R",
}

DEFORMING_BONE_NAMES = (
    "hips",
    "spine",
    "chest",
    "neck",
    "head",
    "shoulder.L",
    "shoulder.R",
    "upper_arm.L",
    "upper_arm.R",
    "forearm.L",
    "forearm.R",
    "hand.L",
    "hand.R",
    "thigh.L",
    "thigh.R",
    "shin.L",
    "shin.R",
    "foot.L",
    "foot.R",
)

CONTROL_BONE_NAMES = (
    "hand_ctrl.L",
    "hand_ctrl.R",
    "foot_ctrl.L",
    "foot_ctrl.R",
    "elbow_pole.L",
    "elbow_pole.R",
    "knee_pole.L",
    "knee_pole.R",
)

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_BLENDER_NUMERIC_SUFFIX = re.compile(r"\.\d{3}$")
_BONE_NAME = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*(?:\.(?:L|R))?$")
_OBJECT_NAME = re.compile(r"^pup\.[a-z][a-z0-9]*(?:_[a-z0-9]+)*(?:\.(?:L|R))?$")
_COLLECTION_NAME = re.compile(r"^PUPPET(?:\.(?:GEOMETRY|RIG))?$")


class NamingError(ValueError):
    pass


def bilateral_name(base: str, side: str) -> str:
    if not isinstance(base, str) or not _SNAKE_CASE.fullmatch(base):
        raise NamingError(f"Invalid bilateral base name: {base!r}")
    if side not in {"L", "R"}:
        raise NamingError(f"Invalid side: {side!r}; expected 'L' or 'R'")
    return f"{base}.{side}"


def has_blender_numeric_suffix(name: str) -> bool:
    return isinstance(name, str) and _BLENDER_NUMERIC_SUFFIX.search(name) is not None


def is_reserved_name(name: str) -> bool:
    return isinstance(name, str) and (
        name.startswith(RESERVED_BONE_PREFIX) or name == ANIMATION_COLLECTION_NAME
    )


def validate_generated_name(name: str) -> None:
    if not isinstance(name, str):
        raise NamingError(f"Generated name must be a string: {name!r}")
    if has_blender_numeric_suffix(name):
        raise NamingError(f"Blender numeric suffix is forbidden: {name!r}")
    if is_reserved_name(name):
        raise NamingError(f"Animation name is reserved: {name!r}")
    if name in {ARMATURE_OBJECT_NAME, ARMATURE_DATA_NAME}:
        return
    if not any(
        pattern.fullmatch(name)
        for pattern in (_BONE_NAME, _OBJECT_NAME, _COLLECTION_NAME)
    ):
        raise NamingError(f"Name does not conform to naming contract v1: {name!r}")
