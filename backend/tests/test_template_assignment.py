import unittest
from collections import Counter

from app.profiles import GateTemplate
from app.research_groups import TargetKey
from app.template_assignment import build_balanced_assignment


class BalancedAssignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.targets = tuple(TargetKey("manual", f"sample-{index}") for index in range(103))
        self.templates = tuple(GateTemplate(name, {}) for name in ("a", "b", "c", "d", "e"))

    def assign(self, seed: str):
        return build_balanced_assignment(
            seed=seed,
            gate_type="click",
            group_id="G2",
            targets=self.targets,
            templates=self.templates,
        )

    def test_same_seed_reproduces_the_same_mapping(self) -> None:
        self.assertEqual(self.assign("seed-a"), self.assign("seed-a"))

    def test_different_seed_changes_the_mapping(self) -> None:
        first = self.assign("seed-a")
        second = self.assign("seed-b")
        self.assertTrue(any(first[target] != second[target] for target in self.targets))

    def test_counts_differ_by_at_most_one(self) -> None:
        counts = Counter(template.template_id for template in self.assign("seed-a").values())
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)


if __name__ == "__main__":
    unittest.main()
