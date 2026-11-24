import importlib.util
import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SHARED_SOURCE = "data/private/phishdecloaker/extracted/src"


def load_conda_runner():
    spec = importlib.util.spec_from_file_location("conda_run", ROOT / "tools/conda/run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeDatasetParityTests(unittest.TestCase):
    def test_container_dependencies_are_locked(self) -> None:
        backend_dockerfile = (ROOT / "backend/Dockerfile").read_text(
            encoding="utf-8"
        )
        frontend_dockerfile = (ROOT / "frontend/Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("FROM python:3.11.0-slim@sha256:", backend_dockerfile)
        self.assertIn("requirements.lock.txt", backend_dockerfile)
        self.assertIn("--require-hashes", backend_dockerfile)
        self.assertIn("FROM node:22-alpine@sha256:", frontend_dockerfile)
        self.assertIn("frontend/package-lock.json", frontend_dockerfile)
        self.assertIn("RUN npm ci", frontend_dockerfile)
        self.assertNotIn("RUN npm install", frontend_dockerfile)
        self.assertIn("FROM nginx:1.27-alpine@sha256:", frontend_dockerfile)

    def test_docker_mounts_the_conda_phishdecloaker_source(self) -> None:
        compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
        conda_launcher = (ROOT / "tools/conda/run.py").read_text(encoding="utf-8")

        self.assertIn(f"source: ./{SHARED_SOURCE}", compose)
        self.assertIn("target: /var/www/html", compose)
        self.assertIn("read_only: true", compose)
        self.assertIn(
            'ROOT / "data" / "private" / "phishdecloaker" / "extracted" / "src"',
            conda_launcher,
        )
        self.assertIn("./targets:/app/targets:ro", compose)

    def test_both_kit_services_share_one_php_runtime_image(self) -> None:
        compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
        self.assertNotIn("gyataro", compose)
        self.assertNotIn("cloaken", compose)
        # Both kit datasets run on the same pinned PHP image.
        self.assertEqual(compose.count("image: php:7.4.27-cli@sha256:"), 2)

    def test_conda_setup_prunes_obsolete_runtime_packages(self) -> None:
        setup = (ROOT / "setup_environment.sh").read_text(encoding="utf-8")
        self.assertIn('conda env update --prune -n "${name}" -f "${file}"', setup)

    def test_conda_builds_and_loads_required_php_extensions(self) -> None:
        environment = (ROOT / "environment.yml").read_text(encoding="utf-8")
        setup = (ROOT / "setup_environment.sh").read_text(encoding="utf-8")
        builder = (ROOT / "tools/conda/build_php_extensions.py").read_text(
            encoding="utf-8"
        )
        runner = (ROOT / "tools/conda/run.py").read_text(encoding="utf-8")

        self.assertIn("php=7.4.27", environment)
        self.assertIn("python=3.11.0", environment)
        self.assertIn("backend/requirements.lock.txt", environment)
        self.assertIn("libcurl=7.86.*", environment)
        self.assertIn("zlib=1.3.*", environment)
        self.assertIn("tools/conda/build_php_extensions.py", setup)
        self.assertIn("PHP_SOURCE_SHA256", builder)
        self.assertIn('"curl": {', builder)
        self.assertIn('"zlib": {', builder)
        self.assertIn("function_exists('curl_version')", runner)
        self.assertIn("function_exists('gzinflate')", runner)

        for name in ("start_dynapd_php.sh", "start_phishdecloaker_php.sh"):
            launcher = (ROOT / "tools/runtime" / name).read_text(encoding="utf-8")
            self.assertIn("PHISHGATE_PHP_CURL_EXTENSION", launcher)
            self.assertIn('extension=${PHISHGATE_PHP_CURL_EXTENSION}', launcher)
            self.assertIn("PHISHGATE_PHP_ZLIB_EXTENSION", launcher)
            self.assertIn('extension=${PHISHGATE_PHP_ZLIB_EXTENSION}', launcher)

    def test_conda_setup_can_skip_node_for_a_prebuilt_frontend(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_bin = Path(temporary)
            conda_log = fake_bin / "conda.log"
            frontend_dist = fake_bin / "dist"
            frontend_dist.mkdir()
            (frontend_dist / "index.html").write_text("<!doctype html>", encoding="utf-8")
            (frontend_dist / "assets").mkdir()
            (frontend_dist / "assets" / "app.js").write_text("", encoding="utf-8")
            fake_conda = fake_bin / "conda"
            fake_conda.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_CONDA_LOG"\n',
                encoding="utf-8",
            )
            fake_conda.chmod(0o755)
            env = {
                **os.environ,
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "FAKE_CONDA_LOG": str(conda_log),
                "PHISHGATE_FRONTEND_DIST": str(frontend_dist),
            }

            subprocess.run(
                ["bash", str(ROOT / "setup_environment.sh")],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

            calls = conda_log.read_text(encoding="utf-8")
            self.assertIn("PhishGate", calls)
            self.assertNotIn("PhishGate-node", calls)
            self.assertNotIn("npm", calls)

    def test_conda_requires_a_complete_prebuilt_frontend(self) -> None:
        runner = load_conda_runner()
        with tempfile.TemporaryDirectory() as temporary:
            frontend_dist = Path(temporary) / "dist"
            with patch.object(runner, "FRONTEND_DIST", frontend_dist):
                self.assertFalse(runner.frontend_build_ready())
                frontend_dist.mkdir()
                (frontend_dist / "index.html").write_text("<!doctype html>", encoding="utf-8")
                self.assertFalse(runner.frontend_build_ready())
                (frontend_dist / "assets").mkdir()
                self.assertFalse(runner.frontend_build_ready())
                (frontend_dist / "assets" / "app.js").write_text("", encoding="utf-8")
                self.assertTrue(runner.frontend_build_ready())

    def test_docker_fails_closed_when_the_shared_dataset_is_incomplete(self) -> None:
        compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
        self.assertIn("create_host_path: false", compose)
        self.assertIn("test -f /var/www/html/kit1/index.php", compose)
        self.assertIn("test -f /var/www/html/kit100/index.php", compose)
        self.assertIn("condition: service_healthy", compose)

    def test_docker_overlays_kit4_copy_target_with_exact_mode(self) -> None:
        compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
        self.assertIn("- /var/www/html/kit4/a1b2c3:size=64m,mode=0777", compose)

    def test_conda_serves_a_disposable_copy_and_never_writes_the_dataset(self) -> None:
        runner = load_conda_runner()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "data" / "src"
            (source / "kit4" / "a1b2c3").mkdir(parents=True)
            (source / "kit4" / "a1b2c3").chmod(0o777)
            (source / "kit4" / "index.php").write_text("<?php", encoding="utf-8")
            runtime = root / "tmp" / "conda-runtime" / "phishdecloaker"

            with patch.multiple(
                runner,
                ROOT=root,
                PHISHDECLOAKER_ROOT=source,
                RUNTIME_ROOT=runtime.parent,
                PHISHDECLOAKER_RUNTIME_ROOT=runtime,
            ):
                (runtime / "stale").mkdir(parents=True)
                docroot = runner.prepare_phishdecloaker_runtime_copy()
                self.assertEqual(docroot, runtime)
                self.assertFalse((runtime / "stale").exists())
                self.assertEqual((runtime / "kit4" / "a1b2c3").stat().st_mode & 0o777, 0o777)

                (runtime / "kit4" / "a1b2c3" / "visit").mkdir()
                (runtime / "kit4" / "visit.txt").write_text("log", encoding="utf-8")
                runner.remove_phishdecloaker_runtime_copy()

                self.assertFalse(runtime.exists())
                self.assertEqual(
                    sorted(p.relative_to(source).as_posix() for p in source.rglob("*")),
                    ["kit4", "kit4/a1b2c3", "kit4/index.php"],
                )

    def test_conda_refuses_to_delete_outside_tmp_or_the_dataset(self) -> None:
        runner = load_conda_runner()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "data" / "src"
            source.mkdir(parents=True)
            with patch.multiple(
                runner, ROOT=root, PHISHDECLOAKER_ROOT=source, PHISHDECLOAKER_RUNTIME_ROOT=source
            ):
                with self.assertRaisesRegex(SystemExit, "Refusing to remove"):
                    runner.remove_phishdecloaker_runtime_copy()
            self.assertTrue(source.is_dir())

    def test_conda_keeps_nohup_but_cleans_up_on_plain_hangup(self) -> None:
        runner = load_conda_runner()
        original = {s: signal.getsignal(s) for s in (signal.SIGHUP, signal.SIGTERM)}
        try:
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            runner.install_shutdown_signals()
            self.assertIs(signal.getsignal(signal.SIGHUP), signal.SIG_IGN)
            self.assertIs(signal.getsignal(signal.SIGTERM), runner.raise_keyboard_interrupt)

            signal.signal(signal.SIGHUP, signal.SIG_DFL)
            runner.install_shutdown_signals()
            self.assertIs(signal.getsignal(signal.SIGHUP), runner.raise_keyboard_interrupt)
        finally:
            for signum, handler in original.items():
                signal.signal(signum, handler)

    def test_conda_checks_public_port_against_unprivileged_start(self) -> None:
        runner = load_conda_runner()
        with patch.object(runner.os, "geteuid", return_value=1000):
            with patch.object(runner, "unprivileged_port_start", return_value=1024):
                with self.assertRaisesRegex(SystemExit, "ip_unprivileged_port_start=80"):
                    runner.require_bindable_public_port("80")
                runner.require_bindable_public_port("8080")
            with patch.object(runner, "unprivileged_port_start", return_value=80):
                runner.require_bindable_public_port("80")
        with patch.object(runner.os, "geteuid", return_value=0):
            runner.require_bindable_public_port("80")

    def test_generic_mode_flag_reads_env(self) -> None:
        runner = load_conda_runner()
        self.assertTrue(runner.generic_mode({"PHISHGATE_GENERIC_UPSTREAM": "on"}))
        self.assertFalse(runner.generic_mode({"PHISHGATE_GENERIC_UPSTREAM": ""}))
        self.assertFalse(runner.generic_mode({}))

    def test_generic_runtime_env_keeps_operator_upstream_and_skips_datasets(self) -> None:
        runner = load_conda_runner()
        file_env = {
            "PHISHGATE_GENERIC_UPSTREAM": "on",
            "PHISHGATE_SEED": "test-seed",
            "PHISHGATE_PROFILE": "click",
            "PHISHGATE_UPSTREAM": "http://my-app:3000",
        }
        clear = {k: "" for k in (
            "PHISHDECLOAKER_DOCROOT", "PHISHGATE_DYNAPD_SELECTION",
            "PHISHGATE_PHP_CURL_EXTENSION", "PHISHGATE_PHP_ZLIB_EXTENSION",
        )}
        with patch.dict(os.environ, clear, clear=False):
            for key in clear:
                os.environ.pop(key, None)
            env = runner.runtime_env(file_env)
        # The operator's upstream is preserved (not overridden to a local PHP port).
        self.assertEqual(env["PHISHGATE_UPSTREAM"], "http://my-app:3000")
        # No dataset / local-PHP / compiled-extension wiring in generic mode.
        self.assertNotIn("PHISHDECLOAKER_DOCROOT", env)
        self.assertNotIn("PHISHGATE_DYNAPD_SELECTION", env)
        self.assertNotIn("PHISHGATE_PHP_CURL_EXTENSION", env)

    def test_conda_cli_can_select_generated_evaluation_manifest(self) -> None:
        runner = load_conda_runner()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            file_env = {
                "PHISHGATE_GENERIC_UPSTREAM": "on",
                "PHISHGATE_SEED": "test-seed",
                "PHISHGATE_PROFILE": "click",
                "PHISHGATE_EXPERIMENT_MANIFEST": "/app/config/cohort.csv",
            }
            with patch.multiple(
                runner,
                ROOT=root,
                FRONTEND_DIST=root / "frontend" / "dist",
            ), patch.dict(
                os.environ,
                {"PHISHGATE_EXPERIMENT_MANIFEST": "/app/targets/EVAL/manifest.csv"},
                clear=False,
            ):
                env = runner.runtime_env(file_env)

            self.assertEqual(
                env["PHISHGATE_EXPERIMENT_MANIFEST"],
                str(root / "targets" / "EVAL" / "manifest.csv"),
            )


if __name__ == "__main__":
    unittest.main()
