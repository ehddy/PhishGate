import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SAFETY_INI = ROOT / "tools/runtime/phishgate-safety.ini"


def read_ini_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in SAFETY_INI.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


class PhpSafetyConfigTests(unittest.TestCase):
    def test_blocks_delivery_execution_sockets_and_uploads(self) -> None:
        disabled = set(read_ini_values()["disable_functions"].split(","))
        expected = {
            "curl_exec",
            "exec",
            "fsockopen",
            "move_uploaded_file",
            "proc_open",
            "socket_create",
            "stream_socket_client",
            "system",
        }
        self.assertTrue(expected.issubset(disabled))

    def test_keeps_local_file_helpers_for_legacy_screen_flows(self) -> None:
        disabled = set(read_ini_values()["disable_functions"].split(","))
        compatibility_helpers = {
            "copy",
            "fopen",
            "fwrite",
            "file_put_contents",
            "mkdir",
            "rename",
            "touch",
        }
        self.assertTrue(compatibility_helpers.isdisjoint(disabled))

    def test_mail_is_defined_but_uses_an_inert_sink(self) -> None:
        values = read_ini_values()
        disabled = set(values["disable_functions"].split(","))
        self.assertNotIn("mail", disabled)
        self.assertEqual(values["sendmail_path"], "/bin/true")

    def test_docker_and_conda_reference_the_shared_policy(self) -> None:
        compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
        self.assertGreaterEqual(compose.count("./tools/runtime/phishgate-safety.ini:"), 2)

        for name in ("start_dynapd_php.sh", "start_phishdecloaker_php.sh"):
            launcher = (ROOT / "tools/runtime" / name).read_text(encoding="utf-8")
            self.assertIn("phishgate-safety.ini", launcher)
            self.assertNotIn('DISABLED_FUNCTIONS="chmod', launcher)

    def test_docker_and_conda_use_the_shared_directory_router(self) -> None:
        compose = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
        self.assertEqual(compose.count("./tools/runtime/router.php:"), 2)

        for name in ("start_dynapd_php.sh", "start_phishdecloaker_php.sh"):
            launcher = (ROOT / "tools/runtime" / name).read_text(encoding="utf-8")
            self.assertIn("router.php", launcher)


if __name__ == "__main__":
    unittest.main()
