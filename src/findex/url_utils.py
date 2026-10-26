# pyright: reportUnknownVariableType=none
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownArgumentType=none
# pyright: reportAttributeAccessIssue=none
# pyright: reportMissingImports=none
# pyright: reportUnusedImport=none
# pyright: reportConstantRedefinition=none

from html.parser import HTMLParser as BaseHTMLParser
from typing import Any, List, Tuple
from urllib.parse import urljoin, urlparse
from yarl import URL

try:
    import selectolax.parser  # type: ignore
    HAS_SELECTOLAX = True
except Exception:
    HAS_SELECTOLAX = False


class SimpleLinkAndTextExtractor(BaseHTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []
        self.text_parts: List[str] = []
        self._ignore: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._ignore = True
        if tag == "a":
            for attr, val in attrs:
                if attr == "href" and val:
                    self.links.append(val)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._ignore = False

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)


def normalize_url(raw_url: str) -> str:
    """Канонізує URL: нижній регістр схеми/хоста, видаляє фрагмент #, сортує query, нормує слеші."""
    try:
        parsed = URL(raw_url)
        parsed = parsed.with_fragment(None)

        scheme = str(parsed.scheme).lower()
        host = str(parsed.host).lower() if parsed.host else ""

        if not scheme or not host:
            return raw_url

        query_pairs = sorted(parsed.query.items())

        normalized = URL.build(
            scheme=scheme,
            host=host,
            port=parsed.port,
            path=parsed.path or "/",
            query=query_pairs,
        )
        return str(normalized)
    except Exception:
        return raw_url


def extract_links_and_text(html_content: str, base_url: str) -> Tuple[List[str], str]:
    """Витягує канонізовані посилання та чистий текст з HTML."""
    links: List[str] = []
    text_content: str = ""

    if HAS_SELECTOLAX:
        try:
            tree: Any = selectolax.parser.HTMLParser(html_content)  # type: ignore
            for node in tree.css("script, style"):  # type: ignore
                node.decompose()  # type: ignore
            text_content = str(tree.text(deep=True, separator=" "))  # type: ignore

            for node in tree.css("a[href]"):  # type: ignore
                href = node.attributes.get("href")  # type: ignore
                if href:
                    full_url = urljoin(base_url, str(href))
                    links.append(normalize_url(full_url))
        except Exception:
            p = SimpleLinkAndTextExtractor()
            p.feed(html_content)
            for href in p.links:
                full_url = urljoin(base_url, href)
                links.append(normalize_url(full_url))
            text_content = " ".join(p.text_parts)
    else:
        p = SimpleLinkAndTextExtractor()
        p.feed(html_content)
        for href in p.links:
            full_url = urljoin(base_url, href)
            links.append(normalize_url(full_url))
        text_content = " ".join(p.text_parts)

    valid_links = [link for link in links if urlparse(link).scheme in ("http", "https")]
    return valid_links, " ".join(text_content.split())