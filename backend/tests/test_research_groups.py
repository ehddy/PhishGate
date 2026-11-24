import os
import tempfile
import unittest
import csv
from pathlib import Path
from unittest.mock import patch

from app.research_groups import G1_SYNTHETIC, TargetKey, group_catalog, group_for_target


class ResearchGroupTests(unittest.TestCase):
    def test_dynapd_is_reserved_for_g1(self) -> None:
        self.assertEqual(group_for_target("dynapd", "sample-1"), G1_SYNTHETIC)

    def test_manifest_freezes_explicit_group_membership(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest = Path(temporary_directory) / "targets.csv"
            manifest.write_text(
                "group_id,dataset,canonical_id\nG1,phishdecloaker,kit1\nG1,dynapd,dynapd-1\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"PHISHGATE_EXPERIMENT_MANIFEST": str(manifest)}):
                catalog = group_catalog()

        self.assertEqual(
            catalog["G1"],
            (
                TargetKey("phishdecloaker", "kit1"),
                TargetKey("dynapd", "dynapd-1"),
            ),
        )
        self.assertEqual(catalog["G2"], ())
        self.assertEqual(catalog["G3"], ())

    def test_manifest_rejects_wrong_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest = Path(temporary_directory) / "targets.csv"
            manifest.write_text(
                "group_id,dataset,canonical_id\nG2,phishdecloaker,kit1\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"PHISHGATE_EXPERIMENT_MANIFEST": str(manifest)}):
                with self.assertRaises(RuntimeError):
                    group_catalog()

    def test_registered_dynapd_selection_joins_g1(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            selection = Path(temporary_directory) / "selection.csv"
            with selection.open("w", encoding="utf-8", newline="") as selection_file:
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
                writer.writerow(
                    {
                        "canonical_id": "dynapd-0123456789ab",
                        "brand": "Example Brand",
                        "entrypoint": "index.php",
                        "copied_directory": "dynapd-0123456789ab",
                    }
                )
            environment = {
                "PHISHGATE_DYNAPD_SELECTION": str(selection),
                "PHISHGATE_EXPERIMENT_MANIFEST": "",
            }
            with patch.dict(os.environ, environment):
                catalog = group_catalog()

        self.assertIn(TargetKey("dynapd", "dynapd-0123456789ab"), catalog["G1"])


if __name__ == "__main__":
    unittest.main()
