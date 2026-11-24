import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.dynapd_annotations import (
    derive_access_slug,
    derive_redirect_root_alias,
    has_slug_mappings,
    list_dynapd_ids,
    lookup_dynapd_by_slug,
    lookup_dynapd_metadata,
    rewrite_public_redirect_root,
    upstream_location,
)
from app.seeding import derive_seed


class DynaPDAnnotationTests(unittest.TestCase):
    def write_selection(self, directory: str, rows: list[dict[str, str]]) -> Path:
        path = Path(directory) / "selection.csv"
        with path.open("w", encoding="utf-8", newline="") as selection_file:
            writer = csv.DictWriter(
                selection_file,
                fieldnames=(
                    "canonical_id",
                    "brand",
                    "entrypoint",
                    "copied_directory",
                ),
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_loads_metadata_and_seeded_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            selection = self.write_selection(
                temporary_directory,
                [
                    {
                        "canonical_id": "dynapd-0123456789ab",
                        "brand": "Example Brand",
                        "entrypoint": "login/index.php?step=1",
                        "copied_directory": "dynapd-0123456789ab",
                    }
                ],
            )
            environment = {
                "PHISHGATE_DYNAPD_SELECTION": str(selection),
                "PHISHGATE_SEED": "1234",
            }
            with patch.dict(os.environ, environment):
                canonical_ids = list_dynapd_ids()
                metadata = lookup_dynapd_metadata("dynapd-0123456789ab")
                slug = derive_access_slug(
                    derive_seed("1234", "route"),
                    "dynapd-0123456789ab",
                )
                resolved = lookup_dynapd_by_slug(slug)
                mappings_exist = has_slug_mappings()

        self.assertEqual(canonical_ids, ("dynapd-0123456789ab",))
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.brand, "Example Brand")
        self.assertEqual(metadata.entrypoint, "login/index.php?step=1")
        self.assertEqual(resolved, "dynapd-0123456789ab")
        self.assertTrue(mappings_exist)

    def test_rejects_duplicate_canonical_ids(self) -> None:
        duplicate = {
            "canonical_id": "dynapd-0123456789ab",
            "brand": "Example Brand",
            "entrypoint": "index.php",
            "copied_directory": "dynapd-0123456789ab",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            selection = self.write_selection(
                temporary_directory,
                [duplicate, duplicate],
            )
            with patch.dict(
                os.environ,
                {"PHISHGATE_DYNAPD_SELECTION": str(selection)},
            ):
                with self.assertRaises(RuntimeError):
                    list_dynapd_ids()

    def test_maps_entrypoint_and_relative_assets_without_exposing_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            selection = self.write_selection(
                temporary_directory,
                [
                    {
                        "canonical_id": "dynapd-0123456789ab",
                        "brand": "Example Brand",
                        "entrypoint": "nested/login/index.php?step=1",
                        "copied_directory": "dynapd-0123456789ab",
                    }
                ],
            )
            with patch.dict(
                os.environ,
                {"PHISHGATE_DYNAPD_SELECTION": str(selection)},
            ):
                entrypoint = upstream_location("dynapd-0123456789ab", "/")
                asset = upstream_location("dynapd-0123456789ab", "/assets/app.css")

        self.assertEqual(
            entrypoint,
            ("dynapd-0123456789ab/nested/login/index.php", "step=1"),
        )
        self.assertEqual(
            asset,
            ("dynapd-0123456789ab/nested/login/assets/app.css", ""),
        )

    def test_rejects_parent_directory_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            selection = self.write_selection(
                temporary_directory,
                [
                    {
                        "canonical_id": "dynapd-0123456789ab",
                        "brand": "Example Brand",
                        "entrypoint": "../outside.php",
                        "copied_directory": "dynapd-0123456789ab",
                    }
                ],
            )
            with patch.dict(
                os.environ,
                {"PHISHGATE_DYNAPD_SELECTION": str(selection)},
            ):
                with self.assertRaises(RuntimeError):
                    list_dynapd_ids()

    def test_rewrites_internal_redirect_to_public_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            selection = self.write_selection(
                temporary_directory,
                [
                    {
                        "canonical_id": "dynapd-0123456789ab",
                        "brand": "Example Brand",
                        "entrypoint": "nested/login/index.php?step=1",
                        "copied_directory": "dynapd-0123456789ab",
                    }
                ],
            )
            with patch.dict(
                os.environ,
                {"PHISHGATE_DYNAPD_SELECTION": str(selection)},
            ):
                rewritten = rewrite_public_redirect_root(
                    "/dynapd-0123456789ab/nested/login/otp.php?step=2#code",
                    "dynapd-0123456789ab",
                    "opaque-kit-alias",
                    "dynapd-0123456789ab/nested/login/index.php",
                )
                relative = rewrite_public_redirect_root(
                    "../otp.php?step=3",
                    "dynapd-0123456789ab",
                    "opaque-kit-alias",
                    "dynapd-0123456789ab/nested/login/step/index.php",
                )
                outside_entrypoint = rewrite_public_redirect_root(
                    "/dynapd-0123456789ab/other/page.php",
                    "dynapd-0123456789ab",
                    "opaque-kit-alias",
                    "dynapd-0123456789ab/nested/login/index.php",
                )
                unrelated = rewrite_public_redirect_root(
                    "/another-local-path/page.php",
                    "dynapd-0123456789ab",
                    "opaque-kit-alias",
                    "dynapd-0123456789ab/nested/login/index.php",
                )
                root_alias = derive_redirect_root_alias("dynapd-0123456789ab")
                round_trip = upstream_location(
                    "dynapd-0123456789ab",
                    f"/{root_alias}/other/page.php",
                )

        public_root = f"/opaque-kit-alias/{root_alias}"
        self.assertEqual(
            rewritten,
            f"{public_root}/nested/login/otp.php?step=2#code",
        )
        self.assertEqual(relative, f"{public_root}/nested/login/otp.php?step=3")
        self.assertEqual(outside_entrypoint, f"{public_root}/other/page.php")
        self.assertEqual(unrelated, "/another-local-path/page.php")
        self.assertEqual(round_trip, ("dynapd-0123456789ab/other/page.php", ""))


if __name__ == "__main__":
    unittest.main()
