"""Build search metadata from public HTML and the site's verified business facts.

No network access or third-party dependencies. Source HTML remains authoritative
for page titles, descriptions and FAQ copy; generated blocks live only in publish/.
"""
from copy import deepcopy
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET

ORIGIN = "https://puregym-busan.github.io"
HOME = ORIGIN + "/"
PUBLIC_PAGES = {
    "index.html": HOME,
    "spaces.html": ORIGIN + "/spaces.html",
    "guide.html": ORIGIN + "/guide.html",
}
ARCHIVE_PAGES = ("concept-a.html", "concept-b.html", "concept-c.html", "proposals.html")
SEARCH_FILES = ("robots.txt", "sitemap.xml", "llms.txt")
ROBOTS = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
SOCIAL_IMAGE = ORIGIN + "/facility-training-floor.jpg"
IMAGE_ALT = "퓨어짐 부산 트레이닝룸 전경"
BUSINESS = {
    "@type": "HealthClub",
    "@id": HOME + "#business",
    "name": "퓨어짐 부산",
    "alternateName": ["PURE Wellness Center", "퓨어짐 하이록스&바레&요가 그룹운동"],
    "description": "부산 남천동에서 하이록스·웨이트·요가·바레 그룹수업과 소셜 사우나·콜드 플런지를 운영하는 웰니스 공간입니다.",
    "url": HOME,
    "telephone": "0507-1347-2861",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "광안해변로15번길 77, 3층 301호",
        "addressLocality": "수영구",
        "addressRegion": "부산광역시",
        "addressCountry": "KR",
    },
    "image": [SOCIAL_IMAGE, ORIGIN + "/facility-studio.jpg", ORIGIN + "/facility-sauna.jpg"],
    "sameAs": [
        "https://www.instagram.com/puregym.busan/",
        "https://m.place.naver.com/place/2096351642/home",
    ],
    "hasMap": "https://map.naver.com/p/entry/place/2096351642",
}
SERVICES = {
    "hyrox": "하이록스 그룹수업",
    "weights": "웨이트 그룹수업",
    "yoga": "요가 그룹수업",
    "barre": "바레 그룹수업",
}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK = re.compile(r"\n?\s*<!-- search-metadata:start -->.*?<!-- search-metadata:end -->\n?", re.S)


def text_content(parts):
    return re.sub(r"\s+", " ", "".join(parts)).strip()


class Document(HTMLParser):
    """Read head metadata, anchors and the user-visible FAQ without a DOM library."""

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.titles = []
        self._title = None
        self.metadata = {}
        self.canonicals = []
        self.ids = set()
        self.jsonld = []
        self._script = None
        self.faqs = []
        self._faq = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = bool(self.stack and self.stack[-1][1]) or tag in {"style", "script"} or attrs.get("aria-hidden") == "true" or "sr-only" in attrs.get("class", "").split() or "hidden" in attrs
        if tag not in VOID_TAGS:
            self.stack.append((tag, hidden))
        if "id" in attrs:
            self.ids.add(attrs["id"])
        in_head = any(item[0] == "head" for item in self.stack)
        if in_head and tag == "title":
            self._title = []
        if in_head and tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.metadata.setdefault(key.lower(), []).append(attrs.get("content", ""))
        if in_head and tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href", ""))
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._script = []
        if tag == "details" and "data-faq" in attrs:
            if self._faq is not None or hidden:
                raise ValueError("FAQ markup must be visible, non-nested details elements")
            self._faq = {"depth": len(self.stack), "question": [], "answer": [], "summary": None, "answer_depth": None}
        if self._faq is not None:
            if tag == "summary":
                self._faq["summary"] = len(self.stack)
            if "faq-answer" in attrs.get("class", "").split():
                self._faq["answer_depth"] = len(self.stack)
            if tag in {"br", "p", "li"}:
                self._faq["answer"].append(" ")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "title" and self._title is not None:
            self.titles.append(text_content(self._title))
            self._title = None
        if tag == "script" and self._script is not None:
            self.jsonld.append(json.loads("".join(self._script)))
            self._script = None
        depth = next((i + 1 for i in range(len(self.stack) - 1, -1, -1) if self.stack[i][0] == tag), 0)
        if self._faq is not None:
            faq = self._faq
            if tag == "details" and faq["depth"] == depth:
                question, answer = text_content(faq["question"]), text_content(faq["answer"])
                if not question or not answer:
                    raise ValueError("Each FAQ needs a summary and a non-empty .faq-answer")
                self.faqs.append((question, answer))
                self._faq = None
            else:
                if faq["summary"] == depth:
                    faq["summary"] = None
                if faq["answer_depth"] == depth:
                    faq["answer_depth"] = None
                if tag in {"p", "li"}:
                    faq["answer"].append(" ")
        if depth:
            del self.stack[depth - 1:]

    def handle_data(self, data):
        if self._title is not None:
            self._title.append(data)
        if self._script is not None:
            self._script.append(data)
        if self._faq is not None and not (self.stack and self.stack[-1][1]):
            if self._faq["summary"] is not None:
                self._faq["question"].append(data)
            elif self._faq["answer_depth"] is not None:
                self._faq["answer"].append(data)

    def meta(self, key):
        values = self.metadata.get(key, [])
        if len(values) > 1:
            raise ValueError(f"Duplicate {key} metadata")
        return values[0] if values else None


def validate_indexing(name, document):
    for key in ("robots", "googlebot", "bingbot"):
        value = (document.meta(key) or "").lower()
        directives = {token.strip() for token in value.split(",")}
        if directives.intersection({"noindex", "none", "nosnippet", "max-snippet:0"}):
            raise ValueError(f"{name} has a search-blocking {key} directive")


def validate_source(name, document):
    if len(document.titles) != 1 or not document.titles[0]:
        raise ValueError(f"{name} must have one non-empty title")
    if not document.meta("description"):
        raise ValueError(f"{name} needs a description")
    if document.canonicals != [PUBLIC_PAGES[name]]:
        raise ValueError(f"{name} canonical must be {PUBLIC_PAGES[name]}")
    validate_indexing(name, document)
    if document.jsonld:
        raise ValueError(f"{name} has unmanaged JSON-LD; maintain it in scripts/search.py")
    if name == "guide.html":
        if not document.faqs:
            raise ValueError("guide.html requires visible FAQs")
        if len({question for question, _ in document.faqs}) != len(document.faqs):
            raise ValueError("FAQ questions must be unique")
        for anchor in SERVICES:
            if anchor not in document.ids:
                raise ValueError(f"guide.html missing service anchor #{anchor}")


def structured_data(name, document, image):
    url = PUBLIC_PAGES[name]
    website = {"@type": "WebSite", "@id": HOME + "#website", "url": HOME, "name": BUSINESS["name"], "alternateName": "PURE Wellness Center", "inLanguage": "ko-KR", "publisher": {"@id": BUSINESS["@id"]}}
    page = {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": document.titles[0], "description": document.meta("description"), "inLanguage": "ko-KR", "isPartOf": {"@id": website["@id"]}, "about": {"@id": BUSINESS["@id"]}, "primaryImageOfPage": {"@type": "ImageObject", "url": image}}
    graph = [deepcopy(BUSINESS), website, page]
    if name == "index.html":
        page["mainEntity"] = {"@id": BUSINESS["@id"]}
    else:
        breadcrumb = {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "퓨어짐 부산", "item": HOME}, {"@type": "ListItem", "position": 2, "name": "시설 둘러보기" if name == "spaces.html" else "수업·첫 방문 안내", "item": url}]}
        graph.append(breadcrumb)
        page["breadcrumb"] = {"@id": breadcrumb["@id"]}
    if name == "guide.html":
        page["@type"] = ["WebPage", "FAQPage"]
        page["mainEntity"] = [{"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}} for question, answer in document.faqs]
        for anchor, service_name in SERVICES.items():
            graph.append({"@type": "Service", "@id": url + "#service-" + anchor, "url": url + "#" + anchor, "name": service_name, "serviceType": service_name, "provider": {"@id": BUSINESS["@id"]}, "areaServed": {"@type": "Place", "name": "부산광역시 수영구 남천동"}})
        page["mentions"] = [{"@id": url + "#service-" + anchor} for anchor in SERVICES]
    return {"@context": "https://schema.org", "@graph": graph}


def decorate_page(name, source, output):
    source = BLOCK.sub("\n", source)
    document = Document(source)
    validate_source(name, document)
    image = document.meta("og:image") or SOCIAL_IMAGE
    image_path = urlsplit(image)
    if image_path.scheme != "https" or image_path.netloc != urlsplit(ORIGIN).netloc or not (output / image_path.path.lstrip("/")).is_file():
        raise ValueError(f"{name} sharing image must be a packaged HTTPS image")
    if document.meta("og:url") not in (None, PUBLIC_PAGES[name]):
        raise ValueError(f"{name} og:url conflicts with its canonical")
    values = {
        "robots": ROBOTS,
        "og:type": "website",
        "og:locale": "ko_KR",
        "og:site_name": BUSINESS["name"],
        "og:title": document.titles[0],
        "og:description": document.meta("description"),
        "og:url": PUBLIC_PAGES[name],
        "og:image": image,
        "og:image:alt": IMAGE_ALT,
        "og:image:type": "image/jpeg",
        "twitter:card": "summary_large_image",
        "twitter:title": document.meta("og:title") or document.titles[0],
        "twitter:description": document.meta("og:description") or document.meta("description"),
        "twitter:image": image,
        "twitter:image:alt": document.meta("og:image:alt") or IMAGE_ALT,
    }
    if image == SOCIAL_IMAGE:
        values.update({"og:image:width": "1800", "og:image:height": "1350"})
    additions = []
    for key, value in values.items():
        existing = document.meta(key)
        if existing is None:
            attribute = "property" if key.startswith("og:") else "name"
            additions.append(f'  <meta {attribute}="{key}" content="{escape(value, quote=True)}">')
        elif not existing:
            raise ValueError(f"{name} has empty {key}")
    data = json.dumps(structured_data(name, document, image), ensure_ascii=False, indent=2).replace("<", "\\u003c")
    additions.append('  <script type="application/ld+json" id="site-structured-data">\n' + data + '\n  </script>')
    block = "  <!-- search-metadata:start -->\n" + "\n".join(additions) + "\n  <!-- search-metadata:end -->\n"
    if source.count("</head>") != 1:
        raise ValueError(f"{name} must contain exactly one closing head")
    head, _, rest = source.partition("</head>")
    return head.rstrip() + "\n" + block + "</head>" + rest


def llms_text():
    return f"""# 퓨어짐 부산 · PURE Wellness Center

> 부산광역시 수영구 남천동의 하이록스·웨이트·요가·바레 그룹운동 및 웰니스 공간.

## 방문 정보
- 주소: 부산 수영구 광안해변로15번길 77, 3층 301호
- 전화: {BUSINESS['telephone']}
- 프로그램: 하이록스, 웨이트, 요가, 바레 그룹수업
- 시설: 트레이닝룸, 요가·바레 스튜디오, 소셜 사우나, 콜드 플런지, 라커·샤워 공간
- 무료 상담과 프로그램별 1일 이용권은 별도 예약 상품입니다.
- 최신 수업 시간표, 요금, 운영·휴무 및 시설 이용 조건은 공식 채널에서 확인합니다.

## 홈페이지
- [퓨어짐 부산]({HOME}): 공간과 프로그램, 위치·주차 안내
- [수업·첫 방문 안내]({ORIGIN}/guide.html): 네 가지 그룹수업, 예약 안내와 자주 묻는 질문
- [시설 둘러보기]({ORIGIN}/spaces.html): 실제 시설 사진

## 공식 채널
- [네이버 플레이스]({BUSINESS['sameAs'][1]}): 업체 정보, 예약 및 운영 안내
- [Instagram]({BUSINESS['sameAs'][0]}): 공간과 수업 소식

이 문서는 공개 홈페이지의 안내를 요약한 보조 자료입니다. 요금·일정·이용 조건은 최신 공식 안내를 기준으로 합니다.
"""


def prepare_search(output):
    """Decorate production HTML and return the generated publication filenames."""
    output = Path(output)
    decorated = {}
    for name in PUBLIC_PAGES:
        decorated[name] = decorate_page(name, (output / name).read_text(encoding="utf-8"), output)
    for name in ARCHIVE_PAGES:
        document = Document((output / name).read_text(encoding="utf-8"))
        if "noindex" not in (document.meta("robots") or "").lower():
            raise ValueError(f"Archived {name} must stay noindex")
    # Validate every page before writing any generated results.
    for name, source in decorated.items():
        (output / name).write_text(source, encoding="utf-8")
    (output / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: " + ORIGIN + "/sitemap.xml\n", encoding="utf-8")
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    urlset = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
    for url in PUBLIC_PAGES.values():
        item = ET.SubElement(urlset, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        ET.SubElement(item, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = url
    ET.indent(urlset, space="  ")
    ET.ElementTree(urlset).write(output / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (output / "llms.txt").write_text(llms_text(), encoding="utf-8")
    validate_search(output)
    return SEARCH_FILES


def validate_search(output):
    """Fail publication when crawlable pages, identity or FAQ data drift."""
    output = Path(output)
    titles, descriptions = [], []
    for name, url in PUBLIC_PAGES.items():
        document = Document((output / name).read_text(encoding="utf-8"))
        validate_indexing(name, document)
        if document.canonicals != [url] or len(document.jsonld) != 1:
            raise ValueError(f"{name} has invalid canonical or JSON-LD count")
        for key in ("robots", "og:title", "og:description", "og:url", "og:image", "twitter:card"):
            if not document.meta(key):
                raise ValueError(f"{name} missing {key}")
        graph = document.jsonld[0]["@graph"]
        business = [item for item in graph if item.get("@id") == BUSINESS["@id"]]
        if business != [BUSINESS]:
            raise ValueError(f"{name} business identity drift")
        if name == "guide.html":
            page = next(item for item in graph if item.get("@id") == url + "#webpage")
            schema_faq = [(item["name"], item["acceptedAnswer"]["text"]) for item in page["mainEntity"]]
            if schema_faq != document.faqs:
                raise ValueError("FAQ structured data does not match visible copy")
        titles.extend(document.titles)
        descriptions.append(document.meta("description"))
    if len(set(titles)) != len(PUBLIC_PAGES) or len(set(descriptions)) != len(PUBLIC_PAGES):
        raise ValueError("Production page titles and descriptions must be distinct")
    locations = [item.text for item in ET.parse(output / "sitemap.xml").iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    if locations != list(PUBLIC_PAGES.values()):
        raise ValueError("Sitemap must contain only the canonical production pages")
    robots = RobotFileParser()
    robots.parse((output / "robots.txt").read_text(encoding="utf-8").splitlines())
    for agent in ("Googlebot", "bingbot", "Yeti", "OAI-SearchBot", "PerplexityBot", "Claude-SearchBot"):
        if not all(robots.can_fetch(agent, url) for url in PUBLIC_PAGES.values()):
            raise ValueError(f"Production crawling is blocked for {agent}")
    if robots.site_maps() != [ORIGIN + "/sitemap.xml"]:
        raise ValueError("robots.txt must reference the public sitemap")
