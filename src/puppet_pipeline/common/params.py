import math
from dataclasses import dataclass, fields
from numbers import Real


class ParameterError(ValueError):
    pass


@dataclass(frozen=True)
class PuppetParameters:
    upper_arm_len: float = 1.0
    forearm_len: float = 0.9
    thigh_len: float = 1.2
    shin_len: float = 1.1
    limb_radius: float = 0.06
    torso_len: float = 1.4
    head_radius: float = 0.22
    hip_width: float = 0.35
    shoulder_width: float = 0.55
    seed: int = 0

    def validate(self) -> None:
        for field in fields(self):
            if field.name == "seed":
                continue
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ParameterError(f"{field.name} must be numeric")
            if not math.isfinite(value) or value <= 0:
                raise ParameterError(
                    f"{field.name} must be finite and greater than zero"
                )

        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ParameterError("seed must be an integer")
        if self.seed < 0:
            raise ParameterError("seed must be nonnegative")
