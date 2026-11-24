import unittest

from app.seeding import derive_seed


class SeedDerivationTests(unittest.TestCase):
    def test_same_master_and_purpose_are_reproducible(self) -> None:
        self.assertEqual(derive_seed("experiment", "route"), derive_seed("experiment", "route"))

    def test_purposes_are_domain_separated(self) -> None:
        self.assertNotEqual(derive_seed("experiment", "route"), derive_seed("experiment", "assignment"))

    def test_master_seed_changes_every_derived_stream(self) -> None:
        self.assertNotEqual(derive_seed("experiment-a", "challenge"), derive_seed("experiment-b", "challenge"))


if __name__ == "__main__":
    unittest.main()
