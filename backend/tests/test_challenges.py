import hashlib
import json
import unittest

from PIL import Image

from app.challenges import (
    ROTATION_SCENE_DIRECTORY,
    ROTATION_SCENE_PATHS,
    TEXT_CHALLENGE_ALPHABET,
    challenge_rng,
    create_area_select_challenge,
    create_digit_challenge,
    create_image_grid_challenge,
    create_math_challenge,
    create_rotation_challenge,
    create_text_challenge,
)


class ChallengeRngTests(unittest.TestCase):
    def test_same_material_reproduces_the_same_generator_state(self) -> None:
        first = challenge_rng("challenge-seed", "kit1", "config-hash", 0)
        second = challenge_rng("challenge-seed", "kit1", "config-hash", 0)
        self.assertEqual(first.getstate(), second.getstate())

    def test_different_kit_produces_a_different_generator_state(self) -> None:
        first = challenge_rng("challenge-seed", "kit1", "config-hash", 0)
        second = challenge_rng("challenge-seed", "kit2", "config-hash", 0)
        self.assertNotEqual(first.getstate(), second.getstate())

    def test_different_config_hash_produces_a_different_generator_state(self) -> None:
        first = challenge_rng("challenge-seed", "kit1", "config-a", 0)
        second = challenge_rng("challenge-seed", "kit1", "config-b", 0)
        self.assertNotEqual(first.getstate(), second.getstate())

    def test_different_stage_index_produces_a_different_generator_state(self) -> None:
        first = challenge_rng("challenge-seed", "kit1", "config-hash", 0)
        second = challenge_rng("challenge-seed", "kit1", "config-hash", 1)
        self.assertNotEqual(first.getstate(), second.getstate())

    def test_different_seed_produces_a_different_generator_state(self) -> None:
        first = challenge_rng("seed-a", "kit1", "config-hash", 0)
        second = challenge_rng("seed-b", "kit1", "config-hash", 0)
        self.assertNotEqual(first.getstate(), second.getstate())


class ReproducibleChallengeContentTests(unittest.TestCase):
    """Every create_*_challenge should regenerate identical content (not just
    an identical generator) for the same challenge_rng() material -- this is
    the property the runtime actually depends on for a fresh token under the
    same experiment condition."""

    def test_digit_challenge_is_reproducible_for_the_same_material(self) -> None:
        first = create_digit_challenge(rng=challenge_rng("s", "kit1", "c", 0))
        second = create_digit_challenge(rng=challenge_rng("s", "kit1", "c", 0))
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.variant, second.variant)
        self.assertEqual(first.image_data_url, second.image_data_url)

    def test_digit_challenge_differs_for_a_different_stage(self) -> None:
        first = create_digit_challenge(rng=challenge_rng("s", "kit1", "c", 0))
        second = create_digit_challenge(rng=challenge_rng("s", "kit1", "c", 1))
        self.assertNotEqual((first.answer, first.variant), (second.answer, second.variant))

    def test_digit_challenge_without_rng_still_produces_a_valid_answer(self) -> None:
        challenge = create_digit_challenge(digit_count=5)
        self.assertEqual(len(challenge.answer), 5)
        self.assertTrue(challenge.answer.isdigit())

    def test_math_challenge_is_reproducible_for_the_same_material(self) -> None:
        first = create_math_challenge(rng=challenge_rng("s", "kit24", "c", 0))
        second = create_math_challenge(rng=challenge_rng("s", "kit24", "c", 0))
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.prompt, second.prompt)
        self.assertEqual(first.operator, second.operator)
        self.assertEqual(first.variant, second.variant)

    def test_math_challenge_differs_for_a_different_kit(self) -> None:
        first = create_math_challenge(rng=challenge_rng("s", "kit24", "c", 0))
        second = create_math_challenge(rng=challenge_rng("s", "kit99", "c", 0))
        self.assertNotEqual((first.prompt, first.answer), (second.prompt, second.answer))

    def test_text_challenge_is_reproducible_for_the_same_material(self) -> None:
        first = create_text_challenge(rng=challenge_rng("s", "kit7", "c", 0))
        second = create_text_challenge(rng=challenge_rng("s", "kit7", "c", 0))
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.variant, second.variant)
        self.assertEqual(first.image_data_url, second.image_data_url)

    def test_text_challenge_differs_for_a_different_stage(self) -> None:
        first = create_text_challenge(rng=challenge_rng("s", "kit7", "c", 0))
        second = create_text_challenge(rng=challenge_rng("s", "kit7", "c", 1))
        self.assertNotEqual(first.answer, second.answer)

    def test_text_challenge_answer_uses_the_unambiguous_alphabet(self) -> None:
        challenge = create_text_challenge(length=6)
        self.assertEqual(len(challenge.answer), 6)
        self.assertTrue(all(character in TEXT_CHALLENGE_ALPHABET for character in challenge.answer))
        # The ambiguous glyphs must never appear in an answer.
        self.assertFalse(set(challenge.answer) & set("IO01"))

    def test_image_grid_challenge_is_reproducible_for_the_same_material(self) -> None:
        first = create_image_grid_challenge(rng=challenge_rng("s", "kit5", "c", 0))
        second = create_image_grid_challenge(rng=challenge_rng("s", "kit5", "c", 0))
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.category_label, second.category_label)
        self.assertEqual(first.variant, second.variant)
        self.assertEqual(first.cell_image_data_urls, second.cell_image_data_urls)


    def test_area_select_challenge_is_reproducible_for_the_same_material(self) -> None:
        first = create_area_select_challenge(rng=challenge_rng("s", "kit3", "c", 0))
        second = create_area_select_challenge(rng=challenge_rng("s", "kit3", "c", 0))
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.category_label, second.category_label)
        self.assertEqual(first.image_data_url, second.image_data_url)

    def test_area_select_answer_is_a_valid_region_index(self) -> None:
        challenge = create_area_select_challenge(columns=3, rows=2)
        self.assertTrue(challenge.answer.isdigit())
        self.assertIn(int(challenge.answer), range(challenge.columns * challenge.rows))

    def test_rotation_challenge_is_reproducible_for_the_same_material(self) -> None:
        first = create_rotation_challenge(rng=challenge_rng("s", "kit9", "c", 0))
        second = create_rotation_challenge(rng=challenge_rng("s", "kit9", "c", 0))
        self.assertEqual(first.answer, second.answer)
        self.assertEqual(first.variant, second.variant)
        self.assertEqual(first.image_data_url, second.image_data_url)

    def test_rotation_answer_is_a_nonzero_step_within_range(self) -> None:
        challenge = create_rotation_challenge(step_count=8)
        self.assertTrue(challenge.answer.isdigit())
        # The scene is always tilted, so the correction is never zero.
        self.assertIn(int(challenge.answer), range(1, challenge.step_count))

    def test_rotation_scene_pool_contains_eight_local_photographs(self) -> None:
        self.assertEqual(len(ROTATION_SCENE_PATHS), 8)
        source_document = json.loads(
            (ROTATION_SCENE_DIRECTORY / "sources.json").read_text(encoding="utf-8")
        )
        sources = {asset["file"]: asset for asset in source_document["assets"]}
        self.assertEqual(set(sources), {path.name for path in ROTATION_SCENE_PATHS})
        for scene_path in ROTATION_SCENE_PATHS:
            with self.subTest(scene=scene_path.name):
                self.assertTrue(scene_path.is_file())
                with Image.open(scene_path) as image:
                    self.assertEqual(image.format, "JPEG")
                digest = hashlib.sha256(scene_path.read_bytes()).hexdigest()
                self.assertEqual(digest, sources[scene_path.name]["sha256"])


if __name__ == "__main__":
    unittest.main()
