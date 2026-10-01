"""Lead generation scraper package."""

# Every source returns leads with these fields so cleaning and export work the same way.
LEAD_FIELDS = ["name", "phone", "website", "address", "category", "source", "source_url"]


def make_lead(**kwargs):
    """Build a lead dict with every standard field present (missing ones become empty strings)."""
    return {field: (kwargs.get(field) or "").strip() for field in LEAD_FIELDS}
