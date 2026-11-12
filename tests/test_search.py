"""Search publication guards; run with python3 -m unittest discover -s tests."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import search


class SearchPublicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="puregym-search-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        # Image content is outside this unit's scope; package.py copies verified assets.
        (self.root / "facility-training-floor.jpg").write_bytes(b"image fixture")
        for name, canonical in search.PUBLIC_PAGES.items():
            body = "<h1>퓨어짐 부산</h1>"
            if name == "guide.html":
                body += "".join(f'<section id="{anchor}"><h2>{title}</h2></section>' for anchor, title in search.SERVICES.items())
                body += """<details data-faq><summary>어떤 <span>수업</span>이 있나요?<span aria-hidden="true">+</span></summary>
<div class="faq-answer"><p>하이록스와 요가 수업이 있습니다.</p><p><a href="https://example.com/">예약 안내</a><span class="sr-only"> (새 창)</span>를 확인하세요.</p></div></details>"""
            (self.root / name).write_text(f'<!doctype html><html lang="ko"><head><title>{name} | 퓨어짐 부산</title><meta name="description" content="{name} 설명"><link rel="canonical" href="{canonical}"></head><body>{body}</body></html>', encoding="utf-8")
        for name in search.ARCHIVE_PAGES:
            (self.root / name).write_text('<html><head><meta name="robots" content="noindex,follow"></head><body>과거 시안</body></html>', encoding="utf-8")

    def replace(self, filename, old, new):
        path = self.root / filename
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_generation_is_repeatable_and_uses_visible_faq(self):
        self.assertEqual(search.prepare_search(self.root), search.SEARCH_FILES)
        first = {path.name: path.read_bytes() for path in self.root.iterdir()}
        search.prepare_search(self.root)
        self.assertEqual(first, {path.name: path.read_bytes() for path in self.root.iterdir()})
        document = search.Document((self.root / "guide.html").read_text())
        self.assertEqual(document.faqs, [("어떤 수업이 있나요?", "하이록스와 요가 수업이 있습니다. 예약 안내를 확인하세요.")])
        page = next(item for item in document.jsonld[0]["@graph"] if item["@id"].endswith("#webpage"))
        self.assertEqual(page["mainEntity"][0]["acceptedAnswer"]["text"], document.faqs[0][1])
        self.assertEqual(len(document.jsonld), 1)
        self.assertEqual(len(document.metadata["og:title"]), 1)
        self.assertNotIn("concept-", (self.root / "sitemap.xml").read_text())
        self.assertNotIn("lastmod", (self.root / "sitemap.xml").read_text())

    def test_preserves_editorial_social_title_without_duplicate_tags(self):
        self.replace("index.html", "</head>", '<meta property="og:title" content="공간의 이야기"><meta name="google-site-verification" content="verification-fixture"><meta name="naver-site-verification" content="naver-fixture"></head>')
        search.prepare_search(self.root)
        document = search.Document((self.root / "index.html").read_text())
        self.assertEqual(document.metadata["og:title"], ["공간의 이야기"])
        self.assertEqual(document.meta("twitter:title"), "공간의 이야기")
        self.assertEqual(document.meta("google-site-verification"), "verification-fixture")
        self.assertEqual(document.meta("naver-site-verification"), "naver-fixture")

    def test_rejects_wrong_or_duplicate_canonical(self):
        for inserted in ['<link rel="canonical" href="https://example.com/">', f'<link rel="canonical" href="{search.HOME}">']:
            with self.subTest(inserted=inserted):
                original = (self.root / "index.html").read_text()
                self.replace("index.html", "</head>", inserted + "</head>")
                with self.assertRaisesRegex(ValueError, "canonical"):
                    search.prepare_search(self.root)
                (self.root / "index.html").write_text(original)

    def test_rejects_source_noindex_and_archives_accidentally_indexable(self):
        self.replace("index.html", "</head>", '<meta name="robots" content="follow, noindex"></head>')
        with self.assertRaisesRegex(ValueError, "search-blocking"):
            search.prepare_search(self.root)
        self.replace("index.html", '<meta name="robots" content="follow, noindex">', "")
        self.replace("concept-b.html", "noindex,follow", "index,follow")
        with self.assertRaisesRegex(ValueError, "must stay noindex"):
            search.prepare_search(self.root)

    def test_rejects_missing_photo_and_missing_service_anchor(self):
        (self.root / "facility-training-floor.jpg").unlink()
        with self.assertRaisesRegex(ValueError, "packaged HTTPS image"):
            search.prepare_search(self.root)
        (self.root / "facility-training-floor.jpg").write_bytes(b"image fixture")
        self.replace("guide.html", 'id="barre"', 'id="renamed-barre"')
        with self.assertRaisesRegex(ValueError, "missing service anchor #barre"):
            search.prepare_search(self.root)

    def test_rejects_hidden_or_empty_faq_answer(self):
        self.replace("guide.html", "<details data-faq>", "<details data-faq hidden>")
        with self.assertRaisesRegex(ValueError, "visible"):
            search.prepare_search(self.root)
        self.replace("guide.html", "<details data-faq hidden>", "<details data-faq>")
        self.replace("guide.html", 'class="faq-answer"', 'class="other-answer"')
        with self.assertRaisesRegex(ValueError, "non-empty"):
            search.prepare_search(self.root)

    def test_validation_detects_visible_answer_drift(self):
        search.prepare_search(self.root)
        self.replace("guide.html", "<p>하이록스와 요가 수업이 있습니다.</p>", "<p>본문이 변경되었습니다.</p>")
        with self.assertRaisesRegex(ValueError, "does not match visible"):
            search.validate_search(self.root)

    def test_validation_rejects_blocked_crawlers_and_output_noindex(self):
        search.prepare_search(self.root)
        self.replace("robots.txt", "Allow: /", "Disallow: /")
        with self.assertRaisesRegex(ValueError, "blocked for"):
            search.validate_search(self.root)
        self.replace("robots.txt", "Disallow: /", "Allow: /")
        self.replace("index.html", 'content="index,follow,', 'content="noindex,follow,')
        with self.assertRaisesRegex(ValueError, "search-blocking"):
            search.validate_search(self.root)

    def test_rejects_duplicate_meta_and_identity_drift(self):
        self.replace("index.html", "</head>", '<meta name="description" content="중복 설명"></head>')
        with self.assertRaisesRegex(ValueError, "Duplicate description"):
            search.prepare_search(self.root)
        self.replace("index.html", '<meta name="description" content="중복 설명">', "")
        search.prepare_search(self.root)
        self.replace("spaces.html", '"telephone": "0507-1347-2861"', '"telephone": "000-000-0000"')
        with self.assertRaisesRegex(ValueError, "identity drift"):
            search.validate_search(self.root)


if __name__ == "__main__":
    unittest.main()
