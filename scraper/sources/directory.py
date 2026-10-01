"""HTML directory scraper (state business registries, chamber of commerce lists, etc.).

Uses requests + BeautifulSoup. Each website is described by a small JSON config of
CSS selectors, so you can point it at a new directory without changing the code.
See configs/demo.json for an example.
"""
import json
import time
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from scraper import make_lead

HEADERS = {"User-Agent": "lead-gen-scraper/1.0 (portfolio project)"}


def is_local(url):
    return not url.startswith(("http://", "https://"))


def fetch(url):
    """Get a page's HTML. Local file paths are supported for the offline demo."""
    if is_local(url):
        return Path(url).read_text(encoding="utf-8")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def allowed_by_robots(url):
    """Respect the site's robots.txt rules."""
    if is_local(url):
        return True
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    parser = robotparser.RobotFileParser()
    try:
        parser.parse(fetch(robots_url).splitlines())
    except requests.RequestException:
        return True  # no robots.txt means no stated restrictions
    return parser.can_fetch(HEADERS["User-Agent"], url)


def get_text(item, selector):
    """Text from the first element matching the selector, or '' if not found."""
    if not selector:
        return ""
    el = item.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def get_link(item, selector, base_url):
    if not selector:
        return ""
    el = item.select_one(selector)
    return urljoin(base_url, el["href"]) if el and el.get("href") else ""


def scrape(config_path, max_pages=50):
    """Scrape every page of a directory, following its 'next page' link."""
    config = json.loads(Path(config_path).read_text())
    fields = config["fields"]
    url = config["start_url"]
    delay = config.get("delay_seconds", 2)
    leads, seen_pages = [], set()

    for page in range(1, max_pages + 1):
        if url in seen_pages:
            break  # stop if pagination loops back on itself
        seen_pages.add(url)

        if not allowed_by_robots(url):
            print(f"  robots.txt blocks {url}, stopping.")
            break

        soup = BeautifulSoup(fetch(url), "html.parser")
        items = soup.select(config["item_selector"])

        for item in items:
            leads.append(make_lead(
                name=get_text(item, fields.get("name")),
                phone=get_text(item, fields.get("phone")),
                website=get_link(item, fields.get("website"), url),
                address=get_text(item, fields.get("address")),
                category=get_text(item, fields.get("category")),
                source=config.get("source_name", "directory"),
                source_url=url,
            ))
        print(f"  Page {page}: {len(items)} listings ({len(leads)} total)")

        next_selector = config.get("next_page_selector")
        next_link = soup.select_one(next_selector) if next_selector else None
        if not next_link or not next_link.get("href"):
            break
        url = urljoin(url, next_link["href"])
        if not is_local(url):
            time.sleep(delay)  # be polite to the website

    return leads
