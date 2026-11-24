import unittest
from collections import Counter

from scripts.prepare_experiment import (
    AUXILIARY_G1_DATASETS,
    PRELIMINARY_GROUP_QUOTAS,
    TargetRecord,
    build_evaluation_split,
    select_main_g1_subset,
    select_preliminary_records,
)


def make_groups(size: int = 120) -> dict[str, list[TargetRecord]]:
    groups: dict[str, list[TargetRecord]] = {}
    for group_id in ("G1", "G2", "G3"):
        records: list[TargetRecord] = []
        for index in range(size):
            if group_id == "G1":
                dataset = "phishdecloaker" if index % 2 == 0 else "dynapd"
                page_type = popularity = ""
            elif group_id == "G2":
                dataset = "manual_phishing"
                page_type = popularity = ""
            else:
                dataset = "manual_benign"
                page_type, popularity = (
                    ("form", "popular"),
                    ("form", "long_tail"),
                    ("general", "popular"),
                    ("general", "long_tail"),
                )[index % 4]
            records.append(
                TargetRecord(
                    group_id=group_id,
                    dataset=dataset,
                    canonical_id=f"{group_id.lower()}-{index:03d}",
                    brand="Example",
                    target_url=f"http://example.test/{group_id.lower()}-{index:03d}/",
                    slug_url=f"http://127.0.0.1/{group_id.lower()}-{index:03d}/",
                    page_type=page_type,
                    popularity=popularity,
                )
            )
        groups[group_id] = records
    return groups


class PreliminarySelectionTests(unittest.TestCase):
    def test_selects_exact_balanced_quota_without_duplicates(self) -> None:
        selected, combined = select_preliminary_records(make_groups(), "seed-a")

        self.assertEqual(
            {group_id: len(records) for group_id, records in selected.items()},
            PRELIMINARY_GROUP_QUOTAS,
        )
        self.assertEqual(len(combined), 50)
        self.assertEqual(len({(record.dataset, record.canonical_id) for record in combined}), 50)
        self.assertEqual(
            Counter(record.dataset for record in selected["G1"]),
            {"phishdecloaker": 25, "dynapd": 25},
        )

    def test_evaluation_is_the_disjoint_complement(self) -> None:
        groups = make_groups()
        _, development = select_preliminary_records(groups, "seed-a")
        evaluation_by_group, evaluation = build_evaluation_split(
            groups,
            development,
            "seed-a",
        )
        development_keys = {
            (record.dataset, record.canonical_id) for record in development
        }
        evaluation_keys = {
            (record.dataset, record.canonical_id) for record in evaluation
        }
        full_keys = {
            (record.dataset, record.canonical_id)
            for records in groups.values()
            for record in records
        }

        self.assertFalse(development_keys & evaluation_keys)
        self.assertEqual(development_keys | evaluation_keys, full_keys)
        self.assertEqual(len(evaluation_by_group["G1"]), 70)
        self.assertEqual(
            Counter(record.dataset for record in evaluation_by_group["G1"]),
            {"phishdecloaker": 35, "dynapd": 35},
        )

    def test_same_seed_reproduces_selection_and_order(self) -> None:
        first = select_preliminary_records(make_groups(), "seed-a")
        second = select_preliminary_records(make_groups(), "seed-a")
        self.assertEqual(first, second)

    def test_annotation_row_order_does_not_change_the_cohort(self) -> None:
        groups = make_groups()
        reversed_groups = {
            group_id: list(reversed(records))
            for group_id, records in groups.items()
        }
        self.assertEqual(
            select_preliminary_records(groups, "seed-a"),
            select_preliminary_records(reversed_groups, "seed-a"),
        )

    def test_different_seed_changes_selection(self) -> None:
        _, first = select_preliminary_records(make_groups(), "seed-a")
        _, second = select_preliminary_records(make_groups(), "seed-b")
        self.assertNotEqual(first, second)

    def test_auxiliary_subset_uses_balanced_main_g1_only(self) -> None:
        groups = make_groups()
        _, development = select_preliminary_records(groups, "seed-a")
        evaluation_by_group, evaluation = build_evaluation_split(
            groups,
            development,
            "seed-a",
        )

        selected, combined = select_main_g1_subset(
            evaluation_by_group,
            "seed-a",
        )

        development_keys = {
            (record.dataset, record.canonical_id) for record in development
        }
        evaluation_keys = {
            (record.dataset, record.canonical_id) for record in evaluation
        }
        combined_keys = {
            (record.dataset, record.canonical_id) for record in combined
        }
        self.assertEqual(set(selected), {"G1"})
        self.assertEqual(len(combined), 50)
        self.assertEqual(
            Counter(record.dataset for record in combined),
            AUXILIARY_G1_DATASETS,
        )
        self.assertFalse(combined_keys & development_keys)
        self.assertTrue(combined_keys <= evaluation_keys)

    def test_fails_when_a_g1_source_is_too_small(self) -> None:
        groups = make_groups()
        groups["G1"] = [
            record for record in groups["G1"] if record.dataset == "phishdecloaker"
        ][:24] + [record for record in groups["G1"] if record.dataset == "dynapd"]
        with self.assertRaises(SystemExit):
            select_preliminary_records(groups, "seed-a")


if __name__ == "__main__":
    unittest.main()
