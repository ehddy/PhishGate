import json
import re
import tempfile
import unittest
from pathlib import Path

from app.research_log import ResearchLogger


class ResearchLoggerTests(unittest.TestCase):
    def test_creates_unique_timestamped_jsonl_and_writes_only_completion_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = ResearchLogger(temporary_directory, "phishwalk click r1")
            self.assertRegex(
                logger.path.name,
                r"^\d{8}T\d{6}\.\d{6}Z-phishwalk-click-r1-[0-9a-f]{10}\.jsonl$",
            )
            logger.gate_completed(
                session_id="research-session",
                target_path="/opaque/",
                profile_id="click",
                stage_index=0,
                stage_count=1,
                gate_type="click",
                template_id="alert",
                context_mode="brand-label",
                elapsed_ms=125,
            )
            records = [json.loads(line) for line in logger.path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["success_state"], "gate_completed")
        self.assertEqual(records[0]["elapsed_ms"], 125)
        self.assertEqual(records[0]["context_mode"], "brand-label")
        self.assertEqual(
            set(records[0]),
            {
                "timestamp_utc",
                "session_id",
                "target_path",
                "profile_id",
                "stage_index",
                "stage_count",
                "gate_type",
                "template_id",
                "context_mode",
                "elapsed_ms",
                "success_state",
            },
        )


if __name__ == "__main__":
    unittest.main()
