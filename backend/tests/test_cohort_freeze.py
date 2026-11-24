import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import prepare_experiment


class CohortFreezeTests(unittest.TestCase):
    def write_csv(self, path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_freeze_is_sorted_stable_and_refuses_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config"
            kits = root / "kits.csv"
            dynapd = root / "dynapd.csv"
            phishing = root / "phishing.csv"
            benign = root / "benign.csv"
            self.write_csv(kits, ("directory",), [{"directory": "kit2"}, {"directory": "kit1"}])
            self.write_csv(dynapd, ("canonical_id",), [{"canonical_id": "dynapd-b"}])
            self.write_csv(phishing, ("directory",), [{"directory": "phish-z"}])
            self.write_csv(benign, ("directory",), [{"directory": "benign-a"}])

            replacements = {
                "ROOT": root,
                "CONFIG_ROOT": config,
                "KIT_ANNOTATION": kits,
                "DYNAPD_SELECTION": dynapd,
                "MANUAL_PHISHING": phishing,
                "MANUAL_BENIGN": benign,
            }
            with patch.multiple(prepare_experiment, **replacements):
                output = config / "cohort.csv"
                prepare_experiment.freeze_cohort(str(output))
                first = output.read_bytes()
                prepare_experiment.freeze_cohort(str(output))
                self.assertEqual(output.read_bytes(), first)

                rows = list(csv.DictReader(first.decode("utf-8").splitlines()))
                self.assertEqual(
                    [(row["group_id"], row["dataset"], row["canonical_id"]) for row in rows],
                    [
                        ("G1", "dynapd", "dynapd-b"),
                        ("G1", "phishdecloaker", "kit1"),
                        ("G1", "phishdecloaker", "kit2"),
                        ("G2", "manual", "phish-z"),
                        ("G3", "manual", "benign-a"),
                    ],
                )

                self.write_csv(phishing, ("directory",), [{"directory": "phish-new"}])
                with self.assertRaisesRegex(SystemExit, "Refusing to replace"):
                    prepare_experiment.freeze_cohort(str(output))

    def test_preparation_and_runtime_manifests_are_separate(self) -> None:
        env = {
            "PHISHGATE_COHORT_MANIFEST": "/app/config/cohort.csv",
            "PHISHGATE_EXPERIMENT_MANIFEST": "/app/targets/EVAL/manifest.csv",
        }

        self.assertEqual(
            prepare_experiment._cohort_manifest_path(env),
            prepare_experiment.ROOT / "config" / "cohort.csv",
        )
        self.assertEqual(
            prepare_experiment._manifest_path(env),
            prepare_experiment.TARGET_ROOT / "EVAL" / "manifest.csv",
        )

        legacy = {"PHISHGATE_EXPERIMENT_MANIFEST": "/app/config/cohort.csv"}
        self.assertEqual(
            prepare_experiment._cohort_manifest_path(legacy),
            prepare_experiment.ROOT / "config" / "cohort.csv",
        )

    def test_missing_frozen_cohort_stops_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.csv"
            env = {"PHISHGATE_COHORT_MANIFEST": str(missing)}
            with self.assertRaisesRegex(SystemExit, "Unable to read"):
                prepare_experiment._selected_keys(
                    env,
                    {("phishdecloaker", "kit1"): "Example"},
                )


if __name__ == "__main__":
    unittest.main()
