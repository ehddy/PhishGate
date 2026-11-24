import unittest

from bs4 import BeautifulSoup

from app.manual_render import _inline_css_urls, _mhtml_to_html


def mhtml_document(html: str) -> bytes:
    return (
        "MIME-Version: 1.0\r\n"
        "Content-Type: multipart/related; boundary=test\r\n"
        "Snapshot-Content-Location: https://example.test/login\r\n"
        "\r\n"
        "--test\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Content-Location: https://example.test/login\r\n"
        "\r\n"
        f"{html}\r\n"
        "--test--\r\n"
    ).encode("utf-8")


class ManualRenderTests(unittest.TestCase):
    def test_empty_and_fragment_css_urls_do_not_inline_the_stylesheet_itself(self) -> None:
        stylesheet_url = "https://example.test/main.css"
        css = '.empty{background:url()} .mask{filter:url("#mask")}'
        by_loc = {
            stylesheet_url: {
                "ctype": "text/css",
                "data": b"large stylesheet payload",
            }
        }

        rendered = _inline_css_urls(css, stylesheet_url, by_loc)

        self.assertIn('url("")', rendered)
        self.assertIn('url("#mask")', rendered)
        self.assertNotIn("large stylesheet payload", rendered)

    def test_all_links_are_same_tab_and_inert(self) -> None:
        rendered = _mhtml_to_html(
            mhtml_document(
                '<html><body><a href="https://outside.test/path" target="_blank" '
                'ping="https://tracker.test" download>Open</a><a href="mailto:a@b.test">Mail</a></body></html>'
            )
        )
        soup = BeautifulSoup(rendered, "html.parser")
        anchors = soup.find_all("a")

        self.assertEqual([anchor.get("href") for anchor in anchors], ["#", "#"])
        self.assertEqual(anchors[0].get("data-original-href"), "https://outside.test/path")
        self.assertEqual(anchors[1].get("data-original-href"), "mailto:a@b.test")
        for anchor in anchors:
            self.assertNotIn("target", anchor.attrs)
            self.assertNotIn("ping", anchor.attrs)
            self.assertNotIn("download", anchor.attrs)

        runtime = soup.find("script", attrs={"data-phishgate-runtime": True})
        self.assertIn('event.target.closest("a")', runtime.get_text())

    def test_unbundled_resources_cannot_reach_the_network(self) -> None:
        rendered = _mhtml_to_html(
            mhtml_document(
                '<html><head><link rel="icon" href="https://outside.test/icon.png">'
                '<style>@import "https://outside.test/theme.css";'
                '.hero{background:url(https://outside.test/hero.png)}</style></head>'
                '<body><img src="https://outside.test/image.png" '
                'srcset="https://outside.test/image-2x.png 2x">'
                '<video poster="https://outside.test/poster.png"></video>'
                '<object data="https://outside.test/file.pdf"></object></body></html>'
            )
        )
        soup = BeautifulSoup(rendered, "html.parser")

        self.assertIsNone(soup.find("link").get("href"))
        self.assertIsNone(soup.find("img").get("src"))
        self.assertIsNone(soup.find("img").get("srcset"))
        self.assertIsNone(soup.find("video").get("poster"))
        self.assertIsNone(soup.find("object").get("data"))
        self.assertNotIn("outside.test", soup.find("style").get_text())


if __name__ == "__main__":
    unittest.main()
