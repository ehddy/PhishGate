"""Minimal run-scoped JSONL logging for accepted Gate completions."""

from __future__ import annotations

import json
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_LOG_DIR = "/app/logs"


class ResearchLogger:
    """Create one unique file per backend process and append complete records."""

    def __init__(self, directory: str | Path, run_label: str = "") -> None:
        log_dir = Path(directory)
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        safe_label = re.sub(r"[^a-zA-Z0-9_-]+", "-", run_label).strip("-")[:48]
        unique_slug = secrets.token_hex(5)
        label_part = f"-{safe_label}" if safe_label else ""
        self.path = log_dir / f"{timestamp}{label_part}-{unique_slug}.jsonl"
        self.path.touch(exist_ok=False)
        self._lock = threading.Lock()

    def gate_completed(
        self,
        *,
        session_id: str,
        target_path: str,
        profile_id: str,
        stage_index: int,
        stage_count: int,
        gate_type: str,
        template_id: str,
        context_mode: str,
        elapsed_ms: int,
    ) -> None:
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "session_id": session_id,
            "target_path": target_path,
            "profile_id": profile_id,
            "stage_index": stage_index,
            "stage_count": stage_count,
            "gate_type": gate_type,
            "template_id": template_id,
            "context_mode": context_mode,
            "elapsed_ms": max(0, elapsed_ms),
            "success_state": "gate_completed",
        }
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock, self.path.open("a", encoding="utf-8") as log_file:
            log_file.write(line)
            log_file.flush()
