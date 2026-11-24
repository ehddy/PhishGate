import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError

from app.upstream_policy import (
    KIT_CONTENT_SECURITY_POLICY,
    LocalUpstreamClient,
    preserved_content_type,
    rewrite_public_redirect_root,
    validate_upstream_base,
)


class RedirectTestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/relative":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
            return
        if self.path == "/external":
            self.send_response(302)
            self.send_header("Location", "https://example.com/")
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        self.server.received_post = (  # type: ignore[attr-defined]
            self.path,
            self.headers.get("Content-Type"),
            self.rfile.read(content_length),
        )
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"submitted")

    def log_message(self, format: str, *args: object) -> None:
        return


class UpstreamPolicyTests(unittest.TestCase):
    def test_preserves_content_type_parameters_and_uses_safe_fallback(self) -> None:
        self.assertEqual(
            preserved_content_type({"Content-Type": "text/html; charset=UTF-8"}),
            "text/html; charset=UTF-8",
        )
        self.assertEqual(preserved_content_type({"Content-Type": "image/png"}), "image/png")
        self.assertEqual(preserved_content_type({}), "application/octet-stream")
        self.assertEqual(
            preserved_content_type({"Content-Type": "text/html\r\nX-Test: injected"}),
            "application/octet-stream",
        )

    def test_browser_policy_allows_external_scripts_but_not_active_egress(self) -> None:
        policy = KIT_CONTENT_SECURITY_POLICY
        self.assertIn("default-src 'self'", policy)
        self.assertIn("script-src 'self' 'unsafe-inline' 'unsafe-eval' http: https:;", policy)
        self.assertIn("style-src 'self' 'unsafe-inline' http: https:", policy)
        self.assertIn("img-src 'self' data: blob: http: https:", policy)
        self.assertIn("font-src 'self' data: http: https:", policy)
        self.assertIn("connect-src 'self'", policy)
        self.assertIn("form-action 'self'", policy)
        self.assertIn("frame-src 'self'", policy)
        self.assertIn("object-src 'none'", policy)

    def test_accepts_only_known_local_origin_urls(self) -> None:
        self.assertEqual(validate_upstream_base("http://127.0.0.1:8081/"), "http://127.0.0.1:8081")
        self.assertEqual(validate_upstream_base("http://phishdecloaker-kits:80"), "http://phishdecloaker-kits")

        for invalid in (
            "https://127.0.0.1",
            "http://example.com",
            "http://user:pass@127.0.0.1",
            "http://127.0.0.1/base",
            "http://127.0.0.1?target=other",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_upstream_base(invalid)

    def test_returns_same_origin_redirect_and_blocks_external_redirect(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectTestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_port}"
            client = LocalUpstreamClient(base_url)
            with client.open(f"{base_url}/relative") as response:
                self.assertEqual(response.status, 302)
                self.assertEqual(response.headers["Location"], "/ok")
                self.assertEqual(
                    client.browser_redirect_location(f"{base_url}/relative", response.headers["Location"]),
                    "/ok",
                )
            with self.assertRaises(HTTPError) as raised:
                client.open(f"{base_url}/external")
            self.assertEqual(raised.exception.code, 302)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_removes_internal_hostname_from_absolute_redirect(self) -> None:
        client = LocalUpstreamClient("http://127.0.0.1:8081")
        self.assertEqual(
            client.browser_redirect_location(
                "http://127.0.0.1:8081/kit2/settings/login.php",
                "http://127.0.0.1:8081/kit2/otp1.php?step=2#code",
            ),
            "/kit2/otp1.php?step=2#code",
        )

    def test_rewrites_canonical_redirect_to_public_alias(self) -> None:
        self.assertEqual(
            rewrite_public_redirect_root(
                "/kit2/otp1.php?step=2#code",
                "kit2",
                "opaque-kit-alias",
            ),
            "/opaque-kit-alias/otp1.php?step=2#code",
        )
        self.assertEqual(
            rewrite_public_redirect_root("../otp1.php", "kit2", "opaque-kit-alias"),
            "../otp1.php",
        )

    def test_client_rejects_a_target_on_another_local_origin(self) -> None:
        client = LocalUpstreamClient("http://127.0.0.1:8081")
        with self.assertRaises(ValueError):
            client.open("http://127.0.0.1:8082/kit1/")

    def test_forwards_post_body_content_type_and_query_without_parsing(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectTestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_port}"
            client = LocalUpstreamClient(base_url)
            body = b"username=synthetic%40example.test&password=not-real"
            with client.open(
                f"{base_url}/submit?flow=login",
                method="POST",
                body=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                self.assertEqual(response.read(), b"submitted")
            self.assertEqual(
                server.received_post,  # type: ignore[attr-defined]
                ("/submit?flow=login", "application/x-www-form-urlencoded", body),
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_rejects_methods_outside_the_reviewed_proxy_scope(self) -> None:
        client = LocalUpstreamClient("http://127.0.0.1:8081")
        with self.assertRaises(ValueError):
            client.open("http://127.0.0.1:8081/kit1/", method="PUT")


if __name__ == "__main__":
    unittest.main()
