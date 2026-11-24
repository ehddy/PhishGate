import unittest

from app.presentation import build_display_context, public_interaction_parameters


class BuildDisplayContextTests(unittest.TestCase):
    def build(self, **parameters: object) -> dict[str, str | None]:
        return build_display_context(
            brand="Example Bank",
            kit_root="kit2",
            profile_id="click-cookie",
            template_id="cookie-consent",
            presentation_seed="example-experiment",
            parameters=parameters,
        )

    def test_same_experiment_inputs_return_the_same_context(self) -> None:
        self.assertEqual(self.build(), self.build())

    def test_neutral_context_hides_brand(self) -> None:
        context = self.build(context_mode="neutral")
        self.assertIsNone(context["brand"])

    def test_brand_label_exposes_only_the_brand(self) -> None:
        context = self.build(context_mode="brand-label")
        self.assertEqual(context["brand"], "Example Bank")

    def test_themed_shell_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.build(context_mode="themed-shell")

    def test_invalid_experiment_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.build(context_mode="raw-html")
        with self.assertRaises(ValueError):
            self.build(layout_variants=["external-layout"])
        with self.assertRaises(ValueError):
            self.build(copy_variants=[])
        with self.assertRaises(ValueError):
            self.build(theme_variants="mint")

    def test_brand_is_trimmed(self) -> None:
        context = build_display_context(
            brand="  Example  ",
            kit_root="kit1",
            profile_id="click-alert",
            template_id="alert",
            presentation_seed="example-experiment",
            parameters={"context_mode": "brand-label"},
        )
        self.assertEqual(context["brand"], "Example")

    def test_configured_variant_lists_are_respected(self) -> None:
        context = self.build(
            layout_variants=["compact"],
            copy_variants=["concise"],
            theme_variants=["violet"],
        )
        self.assertEqual(context["variant_id"], "compact.concise.violet")

    def test_empty_seed_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_display_context(
                brand=None,
                kit_root="kit1",
                profile_id="baseline",
                template_id="baseline",
                presentation_seed="",
                parameters={},
            )

    def test_public_parameters_exclude_raw_presentation_inputs(self) -> None:
        public_parameters = public_interaction_parameters(
            {
                "context_mode": "<script>unsafe</script>",
                "layout_variants": ["external-layout"],
                "threshold_percent": 82,
            }
        )
        self.assertEqual(public_parameters, {"threshold_percent": 82})


if __name__ == "__main__":
    unittest.main()
