"""
Build search-index.json from every top-level HTML page and inject the
site-wide search UI into their navbars.

Run this any time page content changes:

    python tools/build_search_index.py

Safe to re-run — injection is idempotent (skips pages that already have the
search UI).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "search-index.json"

# Pages that are fragments or partials (no <html>/<nav>) — skip entirely
SKIP_FILES = {"nm_table_rows.html"}

SEARCH_MARKUP = (
    '<div class="navbar-search">'
    '<input type="text" class="navbar-search-input" '
    'placeholder="Search site… (press /)" autocomplete="off" '
    'aria-label="Search the site">'
    '<div class="search-results" role="listbox"></div>'
    '</div>'
)
SEARCH_CSS_LINK = '<link rel="stylesheet" href="css/search.css">'
SEARCH_SCRIPT_TAG = '<script src="js/site-search.js" defer></script>'

MAX_CONTENT_CHARS = 1200  # per-page excerpt cap to keep index small


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_entry(path: Path) -> dict | None:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # Must be a real page with a navbar
    if not soup.find("nav", class_="navbar"):
        return None

    title_tag = soup.find("title")
    title = collapse(title_tag.get_text()) if title_tag else path.stem

    # Strip " — Scythe FFXI" suffix if present for cleaner display
    title = re.sub(r"\s*[—\-]+\s*Scythe.*$", "", title, flags=re.IGNORECASE)

    subtitle_tag = soup.find(class_="page-subtitle")
    subtitle = collapse(subtitle_tag.get_text()) if subtitle_tag else ""

    # Prefer <h1 class="page-title"> as the primary title, fall back to <title>
    page_title_tag = soup.find(class_="page-title")
    if page_title_tag:
        page_title = collapse(page_title_tag.get_text())
        if page_title:
            title = page_title

    headings = []
    for h in soup.find_all(["h2", "h3"]):
        text = collapse(h.get_text())
        if text and len(text) < 120:
            headings.append(text)

    # Content: all paragraph and list-item text, minus navbar + footer
    for junk in soup.select("nav, footer, script, style"):
        junk.extract()

    content_parts = []
    for el in soup.find_all(["p", "li", "td", "th"]):
        text = collapse(el.get_text())
        if text:
            content_parts.append(text)
    content = collapse(" ".join(content_parts))[:MAX_CONTENT_CHARS]

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = collapse(meta_tag["content"])

    if not subtitle and meta_desc:
        subtitle = meta_desc

    return {
        "url": path.name,
        "title": title,
        "subtitle": subtitle,
        "headings": headings[:30],
        "content": content,
    }


def inject_search_ui(path: Path) -> bool:
    """Insert the search box, CSS link, and script tag. Returns True if changed."""
    html = path.read_text(encoding="utf-8", errors="ignore")
    original = html

    # Skip if already injected
    already_has_search = "navbar-search-input" in html

    if not already_has_search:
        # Insert before <button class="mobile-toggle" ...>
        m = re.search(r"(\s*)(<button[^>]*mobile-toggle[^>]*>)", html)
        if m:
            indent = m.group(1)
            insertion = indent + SEARCH_MARKUP + m.group(1) + m.group(2)
            html = html[: m.start()] + insertion + html[m.end():]
        else:
            # Fallback: inject after <div class="navbar-inner">
            html = re.sub(
                r"(<div class=\"navbar-inner\">)",
                r"\1\n        " + SEARCH_MARKUP,
                html,
                count=1,
            )

    # Add CSS link if missing (place next to css/style.css link)
    if "css/search.css" not in html:
        html = re.sub(
            r"(<link[^>]*href=\"css/style\.css[^\"]*\"[^>]*>)",
            r"\1\n    " + SEARCH_CSS_LINK,
            html,
            count=1,
        )

    # Add script tag if missing (before </body>)
    if "js/site-search.js" not in html:
        html = re.sub(
            r"(</body>)",
            "    " + SEARCH_SCRIPT_TAG + "\n\\1",
            html,
            count=1,
        )

    if html != original:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def main() -> None:
    entries = []
    injected = 0
    indexed = 0

    for path in sorted(ROOT.glob("*.html")):
        if path.name in SKIP_FILES:
            continue
        entry = extract_entry(path)
        if entry is None:
            print(f"skip  {path.name} (no navbar)")
            continue
        entries.append(entry)
        indexed += 1
        if inject_search_ui(path):
            injected += 1
            print(f"inject {path.name}")
        else:
            print(f"ok    {path.name}")

    OUTPUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    total_bytes = OUTPUT.stat().st_size
    print()
    print(f"indexed {indexed} pages  -> {OUTPUT.name}  ({total_bytes:,} bytes)")
    print(f"injected search UI into {injected} page(s)")


if __name__ == "__main__":
    main()
