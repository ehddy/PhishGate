import csv
import tempfile
import unittest
from pathlib import Path

from scripts.dataset_bundle import DEFAULT_BUNDLE_DIRECTORY, ROOT, pack, unpack, verify


class DatasetBundleTests(unittest.TestCase):
    def test_default_bundle_directory_is_inside_ignored_project_tmp(self) -> None:
        self.assertEqual(DEFAULT_BUNDLE_DIRECTORY, ROOT / "tmp" / "dataset-bundles")

    def make_source(self, root: Path) -> None:
        dynapd = root / "data/private/dynapd"
        selected = dynapd / "raw_selected"
        selected.mkdir(parents=True)
        with (dynapd / "selection.csv").open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=("copied_directory",))
            writer.writeheader()
            for index in range(100):
                directory = f"dynapd-{index:012x}"
                writer.writerow({"copied_directory": directory})
                kit = selected / directory
                kit.mkdir()
                (kit / "index.php").write_text(f"kit {index}\n", encoding="utf-8")

        samples = root / "data/manual/samples"
        for label in ("phishing", "benign"):
            sample = samples / label / f"{label}-sample"
            sample.mkdir(parents=True)
            (sample / "page.mhtml").write_text(label, encoding="utf-8")
        (root / "data/manual_annotation.csv").write_text(
            "dataset,label,directory\nmanual,phishing,phishing-sample\n", encoding="utf-8"
        )
        (root / "data/manual_benign_annotation.csv").write_text(
            "dataset,label,directory\nmanual,benign,benign-sample\n", encoding="utf-8"
        )

    def test_pack_verify_restore_and_refuse_different_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            destination = base / "destination"
            bundles = base / "bundles"
            self.make_source(source)

            groups = ["dynapd", "manual-phishing", "manual-benign"]
            pack(source, bundles, groups)
            verify(bundles)
            unpack(destination, bundles, None)
            unpack(destination, bundles, None)

            restored = destination / "data/private/dynapd/raw_selected/dynapd-000000000000/index.php"
            self.assertEqual(restored.read_text(encoding="utf-8"), "kit 0\n")
            restored.write_text("different\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "Refusing to overwrite different"):
                unpack(destination, bundles, ["dynapd"])


if __name__ == "__main__":
    unittest.main()
