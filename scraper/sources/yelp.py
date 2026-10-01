"""Yelp Places (Fusion) API - business search.

Docs: https://docs.developer.yelp.com/reference/v3_business_search
Needs YELP_API_KEY in your .env file.
Note: Yelp returns the business's Yelp page, not its own website.
"""
import os
import time

import requests

from scraper import make_lead

URL = "https://api.yelp.com/v3/businesses/search"
PAGE_SIZE = 50
MAX_RESULTS = 240  # Yelp caps offset + limit at 240 per search


def search(query, location, max_pages=5):
    """Search Yelp, e.g. query='plumbers', location='Atlanta, GA'."""
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        raise SystemExit("Missing YELP_API_KEY. Add it to your .env file.")

    headers = {"Authorization": f"Bearer {api_key}"}
    leads = []

    for page in range(max_pages):
        offset = page * PAGE_SIZE
        limit = min(PAGE_SIZE, MAX_RESULTS - offset)
        if limit <= 0:
            break

        params = {"term": query, "location": location, "limit": limit, "offset": offset}
        resp = requests.get(URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        businesses = data.get("businesses", [])

        for biz in businesses:
            leads.append(make_lead(
                name=biz.get("name"),
                phone=biz.get("display_phone") or biz.get("phone"),
                website="",
                address=", ".join(biz.get("location", {}).get("display_address", [])),
                category=", ".join(c.get("title", "") for c in biz.get("categories", [])),
                source="yelp",
                source_url=biz.get("url"),
            ))
        print(f"  Yelp page {page + 1}: {len(leads)} leads so far")

        if len(businesses) < limit or offset + limit >= data.get("total", 0):
            break
        time.sleep(1)

    return leads
