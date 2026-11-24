import unittest

from app.runtime_config import derive_local_domain, derive_route_prefix


class RuntimeConfigTests(unittest.TestCase):
    def test_route_prefix_is_stable_and_opaque(self) -> None:
        self.assertEqual(derive_route_prefix("731339658"), "dc3239d1e4ff")
        self.assertNotEqual(derive_route_prefix("731339658"), derive_route_prefix("731339659"))

    def test_hash_domain_is_derived_from_seed(self) -> None:
        self.assertEqual(derive_local_domain("731339658", "hash"), "8ce513310a10.com")

    def test_pronounceable_domain_is_derived_from_seed(self) -> None:
        self.assertEqual(derive_local_domain("731339658", "pronounceable"), "gojacedah.com")

    def test_off_disables_local_domain(self) -> None:
        self.assertIsNone(derive_local_domain("731339658", "off"))

    def test_removed_keyword_domain_style_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            derive_local_domain("731339658", "keyword")

    def test_unknown_domain_style_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            derive_local_domain("731339658", "unknown")


if __name__ == "__main__":
    unittest.main()
