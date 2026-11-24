import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.profiles import ProfileConfigError, load_active_profile


class ProfileLoaderTests(unittest.TestCase):
    def load(self, yaml_text: str):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "profiles.yaml"
            config_path.write_text(yaml_text, encoding="utf-8")
            with patch.dict(
                os.environ,
                {"PHISHGATE_CONFIG": str(config_path), "PHISHGATE_PROFILE": "test"},
            ):
                return load_active_profile()

    def test_fixed_template_is_normalized_to_one_option(self) -> None:
        profile = self.load(
            """
profiles:
  test:
    gates:
      - type: click
        template: alert
        parameters:
          context_mode: neutral
"""
        )
        self.assertEqual(profile.gates[0].templates[0].template_id, "alert")
        self.assertEqual(profile.gates[0].templates[0].parameters["context_mode"], "neutral")

    def test_pool_merges_common_and_template_parameters(self) -> None:
        profile = self.load(
            """
profiles:
  test:
    gates:
      - type: interaction
        templates:
          - movement-verify
          - id: press-and-hold
            parameters:
              hold_duration_ms: 3000
          - id: slide-to-verify
            parameters:
              completion_percent: 94
        parameters:
          context_mode: neutral
"""
        )
        movement, press_and_hold, slider = profile.gates[0].templates
        self.assertEqual(movement.parameters, {"context_mode": "neutral"})
        self.assertEqual(
            press_and_hold.parameters,
            {"context_mode": "neutral", "hold_duration_ms": 3000},
        )
        self.assertEqual(
            slider.parameters,
            {"context_mode": "neutral", "completion_percent": 94},
        )

    def test_stage_cannot_mix_fixed_template_and_pool(self) -> None:
        with self.assertRaises(ProfileConfigError):
            self.load(
                """
profiles:
  test:
    gates:
      - type: click
        template: alert
        templates: [alert]
"""
            )

    def test_invalid_context_mode_fails_during_profile_load(self) -> None:
        with self.assertRaisesRegex(ProfileConfigError, "context_mode"):
            self.load(
                """
profiles:
  test:
    gates:
      - type: click
        template: alert
        parameters:
          context_mode: netural
"""
            )

    def test_legacy_pointer_and_viewport_gate_types_are_rejected(self) -> None:
        for gate_type in ("pointer", "viewport"):
            with self.assertRaisesRegex(ProfileConfigError, "unsupported type"):
                self.load(
                    f"""
profiles:
  test:
    gates:
      - type: {gate_type}
        template: legacy-template
"""
                )

    def test_invalid_variant_pool_fails_during_profile_load(self) -> None:
        with self.assertRaisesRegex(ProfileConfigError, "layout_variants"):
            self.load(
                """
profiles:
  test:
    gates:
      - type: click
        template: alert
        parameters:
          layout_variants: [centered, external-layout]
"""
            )

    def test_main_challenge_profile_loads_full_template_pool(self) -> None:
        config_path = Path(__file__).parents[2] / "config" / "profiles.yaml"
        with patch.dict(
            os.environ,
            {"PHISHGATE_CONFIG": str(config_path), "PHISHGATE_PROFILE": "challenge"},
        ):
            profile = load_active_profile()

        stage = profile.gates[0]
        self.assertEqual(stage.gate_type, "challenge")
        self.assertEqual(
            tuple(template.template_id for template in stage.templates),
            ("custom-digit", "math-challenge", "image-grid", "text-captcha", "area-select", "rotate-upright"),
        )
        self.assertEqual(stage.templates[0].parameters["digit_count"], 5)
        self.assertEqual(stage.templates[1].parameters["max_operand"], 12)
        self.assertEqual(stage.templates[2].parameters["grid_size"], 3)
        self.assertEqual(stage.templates[3].parameters["text_length"], 6)
        self.assertEqual(stage.templates[4].parameters["columns"], 3)
        self.assertEqual(stage.templates[5].parameters["step_count"], 8)

    def test_main_interaction_profile_loads_full_template_pool(self) -> None:
        config_path = Path(__file__).parents[2] / "config" / "profiles.yaml"
        with patch.dict(
            os.environ,
            {"PHISHGATE_CONFIG": str(config_path), "PHISHGATE_PROFILE": "interaction"},
        ):
            profile = load_active_profile()

        stage = profile.gates[0]
        self.assertEqual(stage.gate_type, "interaction")
        self.assertEqual(
            tuple(template.template_id for template in stage.templates),
            (
                "movement-verify",
                "press-and-hold",
                "slide-to-verify",
                "terms-scroll",
                "below-fold-reveal",
            ),
        )
        self.assertEqual(stage.templates[1].parameters["hold_duration_ms"], 3000)
        self.assertEqual(stage.templates[2].parameters["completion_percent"], 94)
        self.assertEqual(stage.templates[3].parameters["threshold_percent"], 90)
        self.assertEqual(stage.templates[4].parameters["threshold_percent"], 82)

    def test_single_template_interaction_profiles_use_interaction_gate_type(self) -> None:
        config_path = Path(__file__).parents[2] / "config" / "profiles.yaml"
        expected_profiles = {
            "interaction-movement-verify": ("movement-verify", None, None),
            "interaction-press-and-hold": ("press-and-hold", "hold_duration_ms", 3000),
            "interaction-slide-to-verify": ("slide-to-verify", "completion_percent", 94),
            "interaction-terms-scroll": ("terms-scroll", "threshold_percent", 90),
            "interaction-below-fold-reveal": ("below-fold-reveal", "threshold_percent", 82),
        }

        for profile_name, (template_id, parameter_name, parameter_value) in expected_profiles.items():
            with self.subTest(profile=profile_name), patch.dict(
                os.environ,
                {"PHISHGATE_CONFIG": str(config_path), "PHISHGATE_PROFILE": profile_name},
            ):
                profile = load_active_profile()
                stage = profile.gates[0]
                template = stage.templates[0]
                self.assertEqual(stage.gate_type, "interaction")
                self.assertEqual(template.template_id, template_id)
                if parameter_name is not None:
                    self.assertEqual(template.parameters[parameter_name], parameter_value)

    def test_legacy_pointer_viewport_profiles_are_removed(self) -> None:
        config_path = Path(__file__).parents[2] / "config" / "profiles.yaml"
        for removed in (
            "pointer",
            "viewport",
            "pointer-movement-verify",
            "pointer-press-and-hold",
            "pointer-slide-to-verify",
            "viewport-terms-scroll",
            "viewport-below-fold-reveal",
        ):
            with patch.dict(
                os.environ,
                {"PHISHGATE_CONFIG": str(config_path), "PHISHGATE_PROFILE": removed},
            ):
                with self.assertRaises(ProfileConfigError):
                    load_active_profile()


if __name__ == "__main__":
    unittest.main()
