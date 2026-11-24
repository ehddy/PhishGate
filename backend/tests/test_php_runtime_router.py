import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "tools/runtime/router.php"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@unittest.skipUnless(shutil.which("php"), "PHP runtime is not installed")
class PhpRuntimeRouterTests(unittest.TestCase):
    def test_real_directory_gets_trailing_slash_and_keeps_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            docroot = Path(temporary)
            nested = docroot / "kit4" / "a1b2c3" / "hash"
            nested.mkdir(parents=True)
            (nested / "index.php").write_text("<?php echo 'ok';", encoding="utf-8")

            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]

            process = subprocess.Popen(
                ["php", "-S", f"127.0.0.1:{port}", "-t", str(docroot), str(ROUTER)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                url = f"http://127.0.0.1:{port}/kit4/a1b2c3/hash?source=test"
                opener = urllib.request.build_opener(NoRedirect)
                redirect_location = None
                for attempt in range(30):
                    try:
                        opener.open(url)
                    except urllib.error.HTTPError as response:
                        if response.code == 308:
                            redirect_location = response.headers["Location"]
                            break
                    except urllib.error.URLError:
                        if attempt == 29:
                            self.fail("PHP test server did not start")
                        time.sleep(0.05)
                else:
                    self.fail("directory request was not redirected")

                self.assertEqual(redirect_location, "/kit4/a1b2c3/hash/?source=test")
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/kit4/a1b2c3/hash/"
                ) as final_response:
                    self.assertEqual(final_response.status, 200)
                    self.assertEqual(final_response.read(), b"ok")
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
