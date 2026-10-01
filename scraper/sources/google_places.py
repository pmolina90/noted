"""Google Places API (New) - Text Search.

Docs: https://developers.google.com/maps/documentation/places/web-service/text-search
Needs GOOGLE_PLACES_API_KEY in your .env file.
"""
import os
import time

import requests

from scraper import make_lead

URL = "https://places.googleapis.com/v1/places:searchText"

# Only ask for the fields we use - Google bills by the fields you request.
FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.primaryTypeDisplayName",
    "places.googleMapsUri",
    "nextPageToken",
])


def search(query, location, max_pages=3):
    """Search Google Places, e.g. query='plumbers', location='Atlanta, GA'.

    Google returns 20 results per page and up to 3 pages (60 results) per search.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise SystemExit("Missing GOOGLE_PLACES_API_KEY. Add it to your .env file.")

    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELD_MASK}
    body = {"textQuery": f"{query} in {location}", "pageSize": 20}
    leads = []

    for page in range(1, max_pages + 1):
        resp = requests.post(URL, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for place in data.get("places", []):
            leads.append(make_lead(
                name=place.get("displayName", {}).get("text"),
                phone=place.get("nationalPhoneNumber"),
                website=place.get("websiteUri"),
                address=place.get("formattedAddress"),
                category=place.get("primaryTypeDisplayName", {}).get("text"),
                source="google_places",
                source_url=place.get("googleMapsUri"),
            ))
        print(f"  Google page {page}: {len(leads)} leads so far")

        token = data.get("nextPageToken")
        if not token:
            break
        body["pageToken"] = token
        time.sleep(2)  # the next-page token takes a moment to become valid

    return leads
