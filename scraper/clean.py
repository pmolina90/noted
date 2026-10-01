"""Turn raw scraped rows into a clean lead list with pandas."""
import re

import pandas as pd

from scraper import LEAD_FIELDS


def format_phone(raw):
    """Standardize US phone numbers to (404) 555-1234. Leaves anything else as-is."""
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return raw.strip()


def format_website(raw):
    """Add https:// if missing, lowercase the domain, drop the trailing slash."""
    if not raw:
        return ""
    url = raw.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    scheme, rest = url.split("://", 1)
    domain, _, path = rest.partition("/")
    url = f"{scheme}://{domain.lower()}" + (f"/{path}" if path else "")
    return url.rstrip("/")


def tidy_text(value):
    """Collapse extra spaces and line breaks."""
    return re.sub(r"\s+", " ", value or "").strip()


def match_key(text):
    """Lowercase letters/numbers only, so 'Joe's Plumbing, LLC' matches 'joes plumbing llc'."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def clean_leads(raw_leads):
    df = pd.DataFrame(raw_leads, columns=LEAD_FIELDS).fillna("")

    for col in ["name", "address", "category"]:
        df[col] = df[col].map(tidy_text)
    df["phone"] = df["phone"].map(format_phone)
    df["website"] = df["website"].map(format_website)

    # Rows with no business name aren't usable leads.
    df = df[df["name"] != ""]

    # Remove duplicates: same phone number, or same name + address.
    before = len(df)
    df["_name_addr"] = df["name"].map(match_key) + "|" + df["address"].map(match_key)
    has_phone = df["phone"] != ""
    df = pd.concat([
        df[has_phone].drop_duplicates(subset="phone"),
        df[~has_phone],
    ])
    df = df.drop_duplicates(subset="_name_addr").drop(columns="_name_addr")
    duplicates_removed = before - len(df)

    # Flag what each lead is missing so the client knows who's reachable.
    df["has_phone"] = df["phone"] != ""
    df["has_website"] = df["website"] != ""
    df["missing_contact"] = ~df["has_phone"] & ~df["has_website"]

    df = df.sort_values(["missing_contact", "name"]).reset_index(drop=True)
    return df, duplicates_removed
