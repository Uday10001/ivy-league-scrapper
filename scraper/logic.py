import hashlib
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from .models import Opportunity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


def _save_item(title, link, university_name, source_type="news_event", description=""):
    """Persist a single scraped item; returns True if newly created."""
    if not title or not link:
        return False
    # Normalise relative URLs
    if link.startswith("/"):
        base_map = {
            "Harvard":   "https://news.harvard.edu",
            "Yale":      "https://news.yale.edu",
            "Princeton": "https://www.princeton.edu",
            "MIT":       "https://news.mit.edu",
            "Columbia":  "https://news.columbia.edu",
            "UPenn":     "https://penntoday.upenn.edu",
            "Cornell":   "https://news.cornell.edu",
            "Dartmouth": "https://home.dartmouth.edu",
            "Brown":     "https://news.brown.edu",
        }
        base = base_map.get(university_name, "")
        link = base + link
    content_hash = hashlib.sha256(f"{title}{link}".encode()).hexdigest()
    _, created = Opportunity.objects.get_or_create(
        content_hash=content_hash,
        defaults={
            "title": title[:500],
            "url": link,
            "university": university_name,
            "source_type": source_type,
            "description": description[:1000],
        },
    )
    return created


# ---------------------------------------------------------------------------
# RSS / Atom parser — handles RSS 2.0, Atom, and namespaced feeds (dc:, media:)
# ---------------------------------------------------------------------------

def _scrape_rss(feed_url, university_name, source_type="news_event"):
    """
    Fetch and parse an RSS or Atom feed.  Handles:
      - RSS 2.0  (<item> with <link> as text node OR as CDATA)
      - Atom     (<entry> with <link href="..."/>)
      - dc: namespace (Dublin Core) used by Drupal/Princeton
      - <guid> as fallback link
    """
    import xml.etree.ElementTree as ET

    session = requests.Session()
    session.headers.update(COMMON_HEADERS)
    # Some servers need an explicit Accept header for RSS/XML
    session.headers["Accept"] = "application/rss+xml, application/xml, text/xml, */*"

    resp = session.get(feed_url, timeout=25, allow_redirects=True)
    resp.raise_for_status()

    # ElementTree chokes on encoding declarations sometimes; decode manually
    content = resp.content

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.error("XML parse error for %s: %s", feed_url, e)
        return 0

    # Namespace map — cover common cases
    ns = {
        "atom":  "http://www.w3.org/2005/Atom",
        "dc":    "http://purl.org/dc/elements/1.1/",
        "media": "http://search.yahoo.com/mrss/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    count = 0

    # ── RSS 2.0: <channel><item> ──────────────────────────────
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        # <link> in RSS 2.0 is a text node *between* sibling tags — ET returns it via .text
        link_el = item.find("link")
        if link_el is not None:
            # When <link> has no text (e.g. Atom-style inside RSS), fall back to tail
            link = (link_el.text or link_el.tail or "").strip()
        else:
            link = ""

        # Fallback: <guid isPermaLink="true"> or just <guid>
        if not link:
            guid_el = item.find("guid")
            if guid_el is not None:
                is_permalink = guid_el.attrib.get("isPermaLink", "true").lower()
                if is_permalink != "false":
                    link = (guid_el.text or "").strip()

        # Description: prefer content:encoded, then description
        desc = ""
        content_enc = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        if content_enc is not None and content_enc.text:
            # Strip HTML from content:encoded
            desc = BeautifulSoup(content_enc.text, "html.parser").get_text(" ", strip=True)[:500]
        if not desc:
            raw_desc = item.findtext("description") or ""
            desc = BeautifulSoup(raw_desc, "html.parser").get_text(" ", strip=True)[:500]

        if _save_item(title, link, university_name, source_type, desc):
            count += 1

    # ── Atom: <feed><entry> ───────────────────────────────────
    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title_el = entry.find("{http://www.w3.org/2005/Atom}title")
        title = (title_el.text or "").strip() if title_el is not None else ""

        # Prefer link with rel="alternate" or no rel attribute
        link = ""
        for link_el in entry.findall("{http://www.w3.org/2005/Atom}link"):
            rel = link_el.attrib.get("rel", "alternate")
            if rel in ("alternate", ""):
                link = link_el.attrib.get("href", "")
                break
        if not link:
            # Any link
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.attrib.get("href", "")

        summary_el = entry.find("{http://www.w3.org/2005/Atom}summary")
        desc = (summary_el.text or "").strip() if summary_el is not None else ""

        if _save_item(title, link, university_name, source_type, desc):
            count += 1

    return count


# ---------------------------------------------------------------------------
# Strategy 2 – requests + BS4 (HTML scrape, no JS)
# ---------------------------------------------------------------------------

def _scrape_with_requests(url, list_selector, title_selector, university_name, source_type="news_event"):
    from urllib.parse import urljoin
    session = requests.Session()
    session.headers.update(COMMON_HEADERS)
    resp = session.get(url, timeout=20, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select(list_selector)
    count = 0
    for item in items:
        el = item.select_one(title_selector)
        if not el:
            if item.name == "a":
                el = item
            else:
                continue
        title = el.get_text(strip=True)
        if not title:
            continue
        link = el.get("href", "")
        if not link:
            a = item.find("a", href=True)
            link = a["href"] if a else ""
        # Resolve relative paths like /news/article → https://brown.edu/news/article
        if link and not link.startswith("http"):
            link = urljoin(url, link)
        if _save_item(title, link, university_name, source_type):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Strategy 3 – Playwright stealth (last resort for JS-heavy pages)
# ---------------------------------------------------------------------------

def _scrape_with_playwright(url, list_selector, title_selector, university_name, source_type="news_event"):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=COMMON_HEADERS["User-Agent"],
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9", "DNT": "1"},
        )
        context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = context.new_page()
        count = 0
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            time.sleep(random.uniform(1.5, 3.0))
            try:
                page.wait_for_selector(list_selector, timeout=15_000)
            except Exception:
                logger.warning("Selector '%s' not found; scraping available DOM", list_selector)
            soup = BeautifulSoup(page.content(), "html.parser")
            for item in soup.select(list_selector):
                el = item.select_one(title_selector)
                if not el:
                    continue
                title = el.get_text(strip=True)
                link = el.get("href", "")
                if _save_item(title, link, university_name, source_type):
                    count += 1
        finally:
            browser.close()
    return count


# ---------------------------------------------------------------------------
# Verified source configs  (URLs confirmed from official RSS listing pages)
# ---------------------------------------------------------------------------
#
# Harvard: https://news.harvard.edu/gazette/rss-feeds/
#   → All stories: https://news.harvard.edu/gazette/feed
#
# MIT: https://news.mit.edu/rss/feed   (confirmed working)
#
# Yale: https://news.yale.edu/rss-feeds
#   → All topics: https://news.yale.edu/news-rss
#
# Princeton: https://www.princeton.edu/feed  (RSS 2.0, uses dc: namespace)
# ---------------------------------------------------------------------------

SOURCES = {
    "Harvard": [
        {
            "url": "https://news.harvard.edu/gazette/feed",
            "type": "rss",
            "source_type": "news_event",
            "label": "Harvard Gazette (all stories)",
        },
        {
            "url": "https://news.harvard.edu/gazette/section/science-technology/feed/",
            "type": "rss",
            "source_type": "research",
            "label": "Harvard Gazette (Science & Tech)",
        },
    ],
    "MIT": [
        {
            "url": "https://news.mit.edu/rss/feed",
            "type": "rss",
            "source_type": "news_event",
            "label": "MIT News (all)",
        },
        {
            "url": "https://news.mit.edu/topic/mitresearch-rss.xml",
            "type": "rss",
            "source_type": "research",
            "label": "MIT News (research)",
        },
    ],
    "Yale": [
        {
            "url": "https://news.yale.edu/news-rss",
            "type": "rss",
            "source_type": "news_event",
            "label": "Yale News (all topics)",
        },
        {
            "url": "https://news.yale.edu/topics/science-technology/rss",
            "type": "rss",
            "source_type": "research",
            "label": "Yale News (Science & Tech)",
        },
    ],
    "Princeton": [
        {
            "url": "https://www.princeton.edu/feed",
            "type": "rss",
            "source_type": "news_event",
            "label": "Princeton University News",
        },
    ],
    "Columbia": [
        {
            "url": "https://www.columbiaspectator.com/news/feed/",
            "type": "rss",
            "source_type": "news_event",
            "label": "Columbia Spectator News",
        },
    ],
"Cornell": [
        {
            "url": "https://news.cornell.edu/taxonomy/term/81/feed",
            "type": "rss",
            "source_type": "news_event",
            "label": "Cornell Chronicle (News & Events)",
        },
        {
            "url": "https://news.cornell.edu/taxonomy/term/24043/feed",
            "type": "rss",
            "source_type": "research",
            "label": "Cornell Chronicle (AI & Tech)",
        },
    ],
"Brown": [
        {
            # Brown has no public RSS — scrape the listing page directly
            "url": "https://www.brown.edu/news/all",
            "type": "html",
            "list_selector": "h3.news-teaser__title, .views-row h3, article h3, h3",
            "title_selector": "a",
            "source_type": "news_event",
            "label": "Brown University News (HTML)",
        },
    ],
"Dartmouth": [
        {
            # Dartmouth has no public RSS — scrape the news listing directly
            "url": "https://home.dartmouth.edu/news",
            "type": "html",
            "list_selector": "article, h3.node__title, h2.node__title",
            "title_selector": "a",
            "source_type": "news_event",
            "label": "Dartmouth News (HTML)",
        },
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class IvyScraper:
    """
    Multi-strategy scraper. For each source it tries in order:
      1. _scrape_rss  (RSS/Atom — no bot detection, fast)
      2. _scrape_with_requests  (HTML + BS4)
      3. _scrape_with_playwright  (full browser, JS support)
    """

    def scrape_university(self, url, list_selector, title_selector,
                          university_name, source_type="news_event"):
        """Generic HTML scrape entry point with Playwright fallback."""
        logger.info("Scraping %s via requests…", url)
        try:
            return _scrape_with_requests(url, list_selector, title_selector, university_name, source_type)
        except Exception as exc:
            logger.warning("requests failed (%s) — trying Playwright", exc)
        try:
            return _scrape_with_playwright(url, list_selector, title_selector, university_name, source_type)
        except Exception as exc:
            logger.error("Playwright also failed: %s", exc)
            return 0

    def scrape_one(self, university):
        """Scrape all configured sources for one university."""
        sources = SOURCES.get(university, [])
        if not sources:
            logger.warning("No sources configured for '%s'", university)
            return 0

        total = 0
        for src in sources:
            label = src.get("label", src["url"])
            try:
                if src["type"] == "rss":
                    n = _scrape_rss(src["url"], university, src.get("source_type", "news_event"))
                else:
                    n = self.scrape_university(
                        src["url"],
                        src["list_selector"],
                        src["title_selector"],
                        university,
                        src.get("source_type", "news_event"),
                    )
                logger.info("%s → %d new items", label, n)
                total += n
            except requests.HTTPError as e:
                logger.error("%s: HTTP %s — skipping", label, e.response.status_code)
            except requests.Timeout:
                logger.error("%s: request timed out — skipping", label)
            except Exception as exc:
                logger.error("%s: unexpected error — %s", label, exc)

        return total

    def scrape_all(self):
        """Scrape every configured university."""
        return {uni: self.scrape_one(uni) for uni in SOURCES}

    @property
    def universities(self):
        return list(SOURCES.keys())
