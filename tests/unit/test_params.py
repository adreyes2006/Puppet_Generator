import unittest
from dataclasses import FrozenInstanceError

from puppet_pipeline.common.params import ParameterError, PuppetParameters


DIMENSION_DEFAULTS = {
    "upper_arm_len": 1.0,
    "forearm_len": 0.9,
    "thigh_len": 1.2,
    "shin_len": 1.1,
    "limb_radius": 0.06,
    "torso_len": 1.4,
    "head_radius": 0.22,
    "hip_width": 0.35,
    "shoulder_width": 0.55,
}


class PuppetParameterDefaultsTests(unittest.TestCase):
    def test_defaults_match_data_model(self) -> None:
        parameters = PuppetParameters()

        for field_name, expected in DIMENSION_DEFAULTS.items():
            with self.subTest(field_name=field_name):
                self.assertEqual(getattr(parameters, field_name), expected)
        self.assertEqual(parameters.seed, 0)

    def test_parameters_are_immutable(self) -> None:
        parameters = PuppetParameters()

        with self.assertRaises(FrozenInstanceError):
            parameters.upper_arm_len = 2.0

    def test_positive_custom_dimensions_and_nonnegative_seed_are_valid(self) -> None:
        parameters = PuppetParameters(
            upper_arm_len=1.5,
            forearm_len=1.3,
            thigh_len=1.6,
            shin_len=1.4,
            limb_radius=0.1,
            torso_len=1.8,
            head_radius=0.3,
            hip_width=0.4,
            shoulder_width=0.7,
            seed=42,
        )

        self.assertIsNone(parameters.validate())


class PuppetParameterValidationTests(unittest.TestCase):
    def test_all_dimensions_must_be_greater_than_zero(self) -> None:
        for field_name in DIMENSION_DEFAULTS:
            for invalid_value in (0, 0.0, -0.01, -1):
                with self.subTest(field_name=field_name, invalid_value=invalid_value):
                    values = {field_name: invalid_value}
                    with self.assertRaisesRegex(
                        ParameterError,
                        rf"\b{field_name}\b.*greater than zero",
                    ):
                        PuppetParameters(**values).validate()

    def test_all_dimensions_reject_non_numeric_input(self) -> None:
        for field_name in DIMENSION_DEFAULTS:
            for invalid_value in (None, "1.0", object(), True):
                with self.subTest(field_name=field_name, invalid_value=invalid_value):
                    values = {field_name: invalid_value}
                    with self.assertRaisesRegex(
                        ParameterError,
                        rf"\b{field_name}\b.*numeric",
                    ):
                        PuppetParameters(**values).validate()

    def test_seed_must_be_nonnegative(self) -> None:
        for invalid_seed in (-1, -42):
            with self.subTest(invalid_seed=invalid_seed):
                with self.assertRaisesRegex(
                    ParameterError,
                    r"\bseed\b.*nonnegative",
                ):
                    PuppetParameters(seed=invalid_seed).validate()

    def test_seed_must_be_an_integer(self) -> None:
        for invalid_seed in (1.5, "1", None, True):
            with self.subTest(invalid_seed=invalid_seed):
                with self.assertRaisesRegex(
                    ParameterError,
                    r"\bseed\b.*integer",
                ):
                    PuppetParameters(seed=invalid_seed).validate()


if __name__ == "__main__":
    unittest.main()
