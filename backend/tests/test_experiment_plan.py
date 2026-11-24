import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.prepare_experiment import (
    TargetRecord,
    _write_record_set,
    _write_condition_order,
    build_aux_reference_plan,
    build_benchmark_variants,
    build_context_mode_plan,
    build_domain_style_plan,
    build_main_plan,
    build_preliminary_plan,
)


def make_records() -> dict[str, list[TargetRecord]]:
    sizes = {"G1": 20, "G2": 10, "G3": 20}
    groups: dict[str, list[TargetRecord]] = {}
    for group_id, size in sizes.items():
        records: list[TargetRecord] = []
        for index in range(size):
            if group_id == "G1":
                dataset = "phishdecloaker" if index % 2 == 0 else "dynapd"
            elif group_id == "G2":
                dataset = "manual_phishing"
            else:
                dataset = "manual_benign"
            records.append(
                TargetRecord(
                    group_id=group_id,
                    dataset=dataset,
                    canonical_id=f"{group_id.lower()}-{index:03d}",
                    brand="Example",
                    target_url=f"http://example.test/{group_id.lower()}-{index:03d}/",
                    slug_url=f"http://127.0.0.1/{group_id.lower()}-{index:03d}/",
                )
            )
        groups[group_id] = records
    return groups


class BenchmarkVariantTests(unittest.TestCase):
    def test_subset_manifest_uses_runtime_dataset_names(self) -> None:
        groups = make_records()
        combined = [record for records in groups.values() for record in records]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_record_set(
                root,
                groups,
                combined,
                dataset_splits=("phishdecloaker", "dynapd"),
            )
            rows = list(csv.DictReader((root / "manifest.csv").read_text().splitlines()))
            detailed = list(csv.DictReader((root / "records.csv").read_text().splitlines()))
            phishdecloaker_urls = (root / "phishdecloaker.txt").read_text().splitlines()
            dynapd_urls = (root / "dynapd.txt").read_text().splitlines()

        self.assertEqual(len(rows), 50)
        self.assertEqual(len(detailed), 50)
        self.assertEqual(
            {row["dataset"] for row in rows},
            {"phishdecloaker", "dynapd", "manual"},
        )
        self.assertEqual(len(phishdecloaker_urls), 10)
        self.assertEqual(len(dynapd_urls), 10)

    def test_builds_original_and_three_gated_families(self) -> None:
        variants = build_benchmark_variants(make_records(), "seed-a")

        # Original + one gated variant per family (click, interaction, challenge).
        self.assertEqual(len(variants), 200)
        self.assertEqual(
            Counter(row["condition"] for row in variants),
            {"gated": 150, "original": 50},
        )
        self.assertEqual(
            Counter(row["evaluation_family"] for row in variants),
            {"original": 50, "click": 50, "interaction": 50, "challenge": 50},
        )
        self.assertEqual(len({row["variant_id"] for row in variants}), len(variants))

        # Each gated family's pooled templates are balanced within each group.
        for group_id in ("G1", "G2", "G3"):
            for family in ("click", "interaction", "challenge"):
                counts = Counter(
                    row["template_id"]
                    for row in variants
                    if row["group_id"] == group_id
                    and row["evaluation_family"] == family
                )
                self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

        # Interaction is one backend gate type and one pooled runtime profile.
        interaction = [r for r in variants if r["evaluation_family"] == "interaction"]
        self.assertEqual({row["gate_type"] for row in interaction}, {"interaction"})
        self.assertEqual({row["profile_id"] for row in interaction}, {"interaction"})
        self.assertEqual(
            {row["template_id"] for row in interaction},
            {
                "movement-verify",
                "press-and-hold",
                "slide-to-verify",
                "terms-scroll",
                "below-fold-reveal",
            },
        )

    def test_condition_order_is_reproducible_and_position_balanced(self) -> None:
        groups = make_records()
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.csv"
            second = Path(temporary) / "second.csv"
            _write_condition_order(first, groups, "seed-a", purpose="main")
            _write_condition_order(second, groups, "seed-a", purpose="main")
            self.assertEqual(first.read_bytes(), second.read_bytes())

            rows = list(csv.DictReader(first.read_text(encoding="utf-8").splitlines()))
            for group_id in ("G1", "G2", "G3"):
                group_rows = [row for row in rows if row["group_id"] == group_id]
                for position in range(2):
                    counts = Counter(
                        row["condition_order"].split(">")[position] for row in group_rows
                    )
                    self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_domain_style_plan_pairs_original_and_click(self) -> None:
        groups = make_records()
        records = groups["G1"]
        variants = build_benchmark_variants(groups, "seed-a")
        rows = build_domain_style_plan(records, variants, "seed-a", "8080")

        self.assertEqual(len(rows), len(records) * 2)
        self.assertEqual(Counter(row["domain_style"] for row in rows), {
            "hash": len(records) * 2,
        })
        self.assertEqual(Counter(row["profile_id"] for row in rows), {
            "baseline": len(records),
            "click": len(records),
        })
        self.assertEqual(
            {row["PHISHGATE_EXPERIMENT_MANIFEST"] for row in rows},
            {"/app/targets/SUBSETS/AUX_G1/manifest.csv"},
        )
        self.assertEqual(
            sorted(int(row["run_order"]) for row in rows),
            list(range(1, len(rows) + 1)),
        )

        for style in ("hash",):
            click_counts = Counter(
                row["template_id"]
                for row in rows
                if row["domain_style"] == style and row["profile_id"] == "click"
            )
            self.assertLessEqual(max(click_counts.values()) - min(click_counts.values()), 1)
            for record in records:
                paired = [
                    row for row in rows
                    if row["domain_style"] == style
                    and row["canonical_id"] == record.canonical_id
                ]
                self.assertEqual(len(paired), 2)
                self.assertEqual(len({row["target_url"] for row in paired}), 1)

        first = records[0]
        hosts = {
            row["target_url"].split("/")[2]
            for row in rows
            if row["canonical_id"] == first.canonical_id
        }
        self.assertEqual(len(hosts), 1)

    def test_auxiliary_run_plans_match_their_execution_budgets(self) -> None:
        groups = make_records()
        variants = build_benchmark_variants(groups, "seed-a")
        main = build_main_plan(variants, "seed-a")
        preliminary = build_preliminary_plan({"G1": groups["G1"]}, "seed-a")
        aux_reference = build_aux_reference_plan(groups["G1"], variants, "seed-a")
        context = build_context_mode_plan(groups["G1"], variants, "seed-a")
        domain = build_domain_style_plan(groups["G1"], variants, "seed-a", "8080")

        self.assertEqual(len(preliminary), 20 * 3 * 6)
        self.assertEqual(len(main), 50 * 16)
        self.assertEqual(len(aux_reference), 20 * 4)
        self.assertEqual(len(context), 20 * 2 * 3)
        for rows in (main, preliminary, aux_reference, context, domain):
            self.assertEqual(
                [row["run_order"] for row in rows],
                list(range(1, len(rows) + 1)),
            )
            self.assertEqual(len({row["run_id"] for row in rows}), len(rows))

        self.assertEqual(
            Counter(row["detector"] for row in main),
            {
                "memophishagent": 100,
                "phishllm": 100,
                "one_shot": 200,
                "generic": 200,
                "phishwalk": 200,
            },
        )
        main_family_counts = Counter(
            (row["detector"], row["evaluation_family"]) for row in main
        )
        for detector in ("memophishagent", "phishllm"):
            self.assertEqual(
                {
                    family: main_family_counts[(detector, family)]
                    for family in ("original", "click", "interaction", "challenge")
                },
                {"original": 50, "click": 50, "interaction": 0, "challenge": 0},
            )
        for detector in ("one_shot", "generic", "phishwalk"):
            self.assertEqual(
                {
                    family: main_family_counts[(detector, family)]
                    for family in ("original", "click", "interaction", "challenge")
                },
                {"original": 50, "click": 50, "interaction": 50, "challenge": 50},
            )
        self.assertEqual(
            {row["model_id"] for row in preliminary},
            {
                "gpt-5.6-luna",
                "claude-haiku-4-5",
                "gemini-3.5-flash-lite",
                "oss1",
                "oss2",
                "oss3",
            },
        )
        self.assertEqual(
            {row["model_pool"] for row in preliminary}, {"selection", "oss"}
        )
        self.assertTrue(
            all(
                row["PHISHGATE_EXPERIMENT_MANIFEST"].endswith("/EVAL/manifest.csv")
                for row in main
            )
        )
        self.assertTrue(
            all(
                row["PHISHGATE_EXPERIMENT_MANIFEST"].endswith("/PRELIM/manifest.csv")
                for row in preliminary
            )
        )
        self.assertEqual(
            {row["PHISHGATE_EXPERIMENT_MANIFEST"] for row in context},
            {"/app/targets/SUBSETS/AUX_G1/manifest.csv"},
        )
        self.assertEqual(
            {row["PHISHGATE_EXPERIMENT_MANIFEST"] for row in aux_reference},
            {"/app/targets/SUBSETS/AUX_G1/manifest.csv"},
        )
        self.assertEqual(
            Counter(row["detector"] for row in aux_reference),
            {
                "phishwalk": 40,
                "one_shot": 20,
                "generic": 20,
            },
        )
        self.assertEqual(
            {row["evaluation_family"] for row in aux_reference},
            {"original", "click"},
        )
        self.assertEqual({row["context_mode"] for row in aux_reference}, {"neutral"})
        self.assertEqual(
            {row["domain_style"] for row in aux_reference}, {"pronounceable"}
        )
        # The context subset reuses the click assignment, so balanced assignment
        # spreads the 20 G1 records across the click pool with per-template record
        # counts differing by at most 1 -- i.e. row counts (x2 contexts x3
        # detectors = x6) differ by at most 6, whatever the click pool size.
        context_template_counts = Counter(row["template_id"] for row in context)
        self.assertLessEqual(
            max(context_template_counts.values()) - min(context_template_counts.values()), 6
        )
        self.assertEqual(
            {row["context_mode"] for row in context},
            {"neutral", "brand-label"},
        )

        main_templates = {
            (row["dataset"], row["canonical_id"], row["evaluation_family"]): row[
                "template_id"
            ]
            for row in variants
        }
        for row in context:
            key = (row["dataset"], row["canonical_id"], row["evaluation_family"])
            self.assertEqual(row["template_id"], main_templates[key])

        reference_templates = {
            (
                row["dataset"],
                row["canonical_id"],
                row["evaluation_family"],
            ): row["template_id"]
            for row in aux_reference
        }
        for row in (*context, *domain):
            key = (row["dataset"], row["canonical_id"], row["evaluation_family"])
            self.assertEqual(row["template_id"], reference_templates[key])

        self.assertEqual(
            preliminary,
            build_preliminary_plan({"G1": groups["G1"]}, "seed-a"),
        )


if __name__ == "__main__":
    unittest.main()
