"""Generic gate-injection mode: operator-configured upstream, no datasets.

These cover the additive `PHISHGATE_GENERIC_UPSTREAM` mode without disturbing
the research-dataset runtime. The open-proxy guard (per-request origin pin) is
asserted to stay intact.
"""

import importlib
import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class UpstreamAllowlistTests(unittest.TestCase):
    def reload_policy(self, allowed_hosts: str):
        import app.upstream_policy as policy

        with patch.dict(os.environ, {"PHISHGATE_UPSTREAM_ALLOWED_HOSTS": allowed_hosts}):
            return importlib.reload(policy)

    def tearDown(self) -> None:
        import app.upstream_policy as policy

        # Restore the module to its unconfigured allowlist for other tests.
        with patch.dict(os.environ, {"PHISHGATE_UPSTREAM_ALLOWED_HOSTS": ""}):
            importlib.reload(policy)

    def test_operator_host_extends_the_allowlist(self) -> None:
        policy = self.reload_policy("demo-upstream, my-app")
        self.assertIn("demo-upstream", policy.ALLOWED_UPSTREAM_HOSTS)
        self.assertIn("my-app", policy.ALLOWED_UPSTREAM_HOSTS)
        # Built-ins remain.
        self.assertIn("127.0.0.1", policy.ALLOWED_UPSTREAM_HOSTS)

    def test_builtin_only_without_operator_hosts(self) -> None:
        policy = self.reload_policy("")
        self.assertNotIn("demo-upstream", policy.ALLOWED_UPSTREAM_HOSTS)
        self.assertIn("localhost", policy.ALLOWED_UPSTREAM_HOSTS)

    def test_open_still_pins_to_one_origin_no_open_proxy(self) -> None:
        policy = self.reload_policy("demo-upstream")
        client = policy.LocalUpstreamClient("http://demo-upstream")
        # A different but still-allowlisted host is rejected because it is not
        # the single configured upstream origin -- the open-proxy guard.
        with self.assertRaisesRegex(ValueError, "does not match its configured"):
            client.open("http://localhost/somewhere")


def _load_main_in_generic_mode(profile: str = "click"):
    """Import app.main fresh with generic mode on and no dataset annotation."""
    scratch = ROOT / "backend" / "tests"
    env = {
        "PHISHGATE_GENERIC_UPSTREAM": "on",
        "PHISHGATE_SEED": "test-generic-seed",
        # Use a built-in allowlisted host so this test does not depend on the
        # PHISHGATE_UPSTREAM_ALLOWED_HOSTS module state (exercised separately).
        "PHISHGATE_UPSTREAM": "http://localhost",
        "PHISHGATE_UPSTREAM_ALLOWED_HOSTS": "",
        "PHISHGATE_BRAND_ANNOTATION": str(scratch / "does-not-exist.csv"),
        "PHISHGATE_DYNAPD_SELECTION": "",
        "PHISHGATE_CONFIG": str(ROOT / "config" / "profiles.yaml"),
        "PHISHGATE_PROFILE": profile,
        "PHISHGATE_LOG_DIR": str(ROOT / "logs"),
    }
    with patch.dict(os.environ, env, clear=False):
        spec = importlib.util.spec_from_file_location(
            "phishgate_main_generic", ROOT / "backend" / "app" / "main.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _fake_request(method: str = "GET"):
    from starlette.requests import Request

    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/anything/here",
            "raw_path": b"/anything/here",
            "query_string": b"",
            "headers": [],
        }
    )


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") is not None, "fastapi not installed in this env"
)
class GenericModeAppTests(unittest.TestCase):
    def test_interaction_profile_uses_one_gate_type_and_completion_endpoint(self) -> None:
        main = _load_main_in_generic_mode(profile="interaction")
        self.assertEqual(main.ACTIVE_STAGE.gate_type, "interaction")
        self.assertEqual(
            {template.template_id for template in main.ACTIVE_STAGE.templates},
            main.SUPPORTED_TEMPLATES["interaction"],
        )

        route_paths = {route.path for route in main.app.routes}
        self.assertIn(
            f"{main.ROUTE_PREFIX}/api/gates/interaction/complete", route_paths
        )
        self.assertNotIn(f"{main.ROUTE_PREFIX}/api/gates/pointer/complete", route_paths)
        self.assertNotIn(f"{main.ROUTE_PREFIX}/api/gates/viewport/complete", route_paths)

    def test_starts_without_dataset_and_gates_any_path(self) -> None:
        main = _load_main_in_generic_mode()  # no RuntimeError despite missing CSV
        self.assertTrue(main.GENERIC_UPSTREAM_ENABLED)
        self.assertIsNotNone(main.ACTIVE_STAGE)

        generic = main.ResolvedTarget("generic", "generic")
        response = main._gate_or_serve(
            generic, _fake_request(), redirect_target="/anything/here", log_target_path="/anything/here"
        )
        # An unresolved path is gated: a redirect into the gate SPA prefix.
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 307)
        self.assertIn(f"{main.ROUTE_PREFIX}/?t=", response.headers["location"])

    def test_baseline_passes_through_without_a_gate(self) -> None:
        main = _load_main_in_generic_mode(profile="baseline")
        self.assertIsNone(main.ACTIVE_STAGE)

        generic = main.ResolvedTarget("generic", "generic")
        response = main._gate_or_serve(
            generic, _fake_request(), redirect_target="/anything/here", log_target_path="/anything/here"
        )
        # Baseline has no gate -> None means "proxy straight through".
        self.assertIsNone(response)


class DemoComposeParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")

    def test_demo_backend_is_dataset_free_and_generic(self) -> None:
        # The demo backend must not carry the dataset-coupled anchor/deps.
        self.assertIn("backend-demo:", self.compose)
        block = self.compose.split("backend-demo:", 1)[1].split("frontend-demo:", 1)[0]
        self.assertIn('PHISHGATE_GENERIC_UPSTREAM: "on"', block)
        self.assertIn("PHISHGATE_UPSTREAM: http://demo-upstream:80", block)
        self.assertNotIn("phishdecloaker-kits", block)
        self.assertNotIn("kit_brand_annotation.csv", block)
        self.assertNotIn("manual_annotation.csv", block)

    def test_demo_upstream_is_a_plain_static_server(self) -> None:
        self.assertIn("demo-upstream:", self.compose)
        self.assertIn("./demo/upstream:/usr/share/nginx/html:ro", self.compose)


if __name__ == "__main__":
    unittest.main()
