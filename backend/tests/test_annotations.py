import csv
import os
import tempfile
import unittest
from pathlib import Path

from app.annotations import _metadata_index, _slug_index, derive_access_slug


class AccessSlugTests(unittest.TestCase):
    def test_slug_formula_is_legacy_compatible(self) -> None:
        self.assertEqual(derive_access_slug("test-seed", "kit1"), "a41499658149")
        self.assertEqual(derive_access_slug("test-seed", "kit26"), "7d0d78828777")

    def test_slug_index_uses_only_stable_directory_column(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            annotation_path = Path(temporary_directory) / "annotation.csv"
            with annotation_path.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=("directory", "brand"))
                writer.writeheader()
                writer.writerow({"directory": "kit26", "brand": "Example University"})

            index = _slug_index(str(annotation_path), "test-seed")

        self.assertEqual(index, {"7d0d78828777": "kit26"})

    def test_empty_seed_does_not_create_routes(self) -> None:
        self.assertEqual(_slug_index("unused.csv", ""), {})

    def test_brand_is_loaded_without_presentation_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            annotation_path = Path(temporary_directory) / "annotation.csv"
            with annotation_path.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=("directory", "brand"),
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "directory": "kit2",
                        "brand": "Example Bank",
                    }
                )

            metadata = _metadata_index(str(annotation_path))["kit2"]

        self.assertEqual(metadata.brand, "Example Bank")

    def test_shipped_annotation_is_brand_only(self) -> None:
        default_path = Path(__file__).resolve().parents[2] / "data" / "kit_brand_annotation.csv"
        annotation_path = Path(os.environ.get("PHISHGATE_BRAND_ANNOTATION", default_path))
        with annotation_path.open(encoding="utf-8", newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        self.assertEqual(len(rows), 100)
        self.assertEqual(
            {row["directory"] for row in rows},
            {f"kit{index}" for index in range(1, 101)},
        )
        self.assertTrue(all(row["brand"].strip() for row in rows))
        self.assertNotIn("site_family", rows[0])
        self.assertNotIn("locale", rows[0])

        by_directory = {row["directory"]: row for row in rows}
        self.assertEqual(by_directory["kit65"]["brand"], "dpdgroup")


if __name__ == "__main__":
    unittest.main()
