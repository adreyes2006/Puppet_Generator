import re

STYLING_NAMING_VERSION = "1.1"

STYLE_COLLECTION_NAME = "PUPPET.STYLE"
ACCESSORY_COLLECTION_NAME = "PUPPET.STYLE.ACCESSORIES"
BACKGROUND_COLLECTION_NAME = "PUPPET.STYLE.BACKGROUND"

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_ELEMENT = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*(?:\.[a-z][a-z0-9]*(?:_[a-z0-9]+)*)?$")
_NUMERIC_SUFFIX = re.compile(r"\.\d{3}$")


class StylingNamingError(ValueError):
    pass


def has_numeric_suffix(name: str) -> bool:
    return isinstance(name, str) and _NUMERIC_SUFFIX.search(name) is not None


def accessory_name(kind: str, style: str, side: str | None = None) -> str:
    if not isinstance(kind, str) or not _SNAKE_CASE.fullmatch(kind):
        raise StylingNamingError(f"Invalid accessory kind: {kind!r}")
    if not isinstance(style, str) or not _SNAKE_CASE.fullmatch(style):
        raise StylingNamingError(f"Invalid accessory style: {style!r}")
    name = f"acc.{kind}.{style}"
    if side is None:
        return name
    if side not in {"L", "R"}:
        raise StylingNamingError(f"Invalid side: {side!r}; expected 'L' or 'R'")
    return f"{name}.{side}"


def background_name(element: str) -> str:
    if not isinstance(element, str) or not _ELEMENT.fullmatch(element):
        raise StylingNamingError(f"Invalid background element: {element!r}")
    return f"bg.{element}"


def prop_name(element: str) -> str:
    return background_name(f"prop.{element}")


def material_name(preset: str) -> str:
    if not isinstance(preset, str) or not _SNAKE_CASE.fullmatch(preset):
        raise StylingNamingError(f"Invalid material preset name: {preset!r}")
    return f"mat.{preset}"
