#!/usr/bin/env python3
"""Import public RSS/Atom job feeds into Supabase as drafts for human review.

Only add feeds whose publisher permits automated access/reuse. The importer stores
the original item URL as the application/source URL and never publishes automatically.
"""
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
FEEDS_JSON = os.environ.get("JOB_FEEDS_JSON", "[]")
HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}
TODAY = date.today().isoformat()

def clean(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", value).strip()

def parse_date(entry):
    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.date().isoformat()
            except Exception:
                pass
    return TODAY

def infer_category(text):
    t = text.lower()
    mapping = [
        (("ict", "software", "developer", "data", "cyber", "it support", "technology"), "Technology & ICT"),
        (("nurse", "doctor", "medical", "clinical", "health"), "Healthcare & Medical"),
        (("teacher", "lecturer", "education", "school"), "Education & Teaching"),
        (("finance", "account", "bank", "audit", "procurement", "administration"), "Business, Finance & Administration"),
        (("engineer", "construction", "architect"), "Engineering & Construction"),
        (("ngo", "humanitarian", "development", "programme", "program"), "NGO & Development"),
        (("government", "county", "public service", "civil service"), "Government & Public Service"),
        (("marketing", "sales", "communications", "media", "design"), "Sales & Marketing"),
        (("customer service", "call centre", "call center", "support agent"), "Customer Service & Call Centre"),
    ]
    for words, category in mapping:
        if any(w in t for w in words):
            return category
    return "Other"

def infer_country(text, feed_country):
    if feed_country:
        return feed_country
    t = text.lower()
    for country in ("Kenya", "Uganda", "Tanzania", "Rwanda", "South Sudan", "Ethiopia", "Somalia", "Nigeria", "Ghana", "South Africa", "United Kingdom", "Australia", "Canada", "United States"):
        if country.lower() in t:
            return country
    if "remote" in t or "work from home" in t:
        return "Remote / Worldwide"
    return "International / Not specified"

def make_record(entry, feed):
    title = clean(entry.get("title"))
    url = entry.get("link", "").strip()
    summary = clean(entry.get("summary") or entry.get("description"))
    if not title or not url:
        return None
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None

    combined = f"{title} {summary}"
    source_name = clean(feed.get("name") or parsed.netloc)
    country = infer_country(combined, feed.get("country"))
    remote = "remote" in combined.lower() or "work from home" in combined.lower()
    location = "Remote" if remote else (country if country != "International / Not specified" else "Not specified")
    job_type = "Internship" if "intern" in combined.lower() else ("Contract" if "contract" in combined.lower() else "Full-time")
    mode = "Remote" if remote else "On-site"

    # Keep descriptions short and source-attributed; editors should verify and enrich.
    description = summary or "Open the original employer/source listing to review the full vacancy details."
    description = description[:5000]
    digest = hashlib.sha256(url.lower().encode("utf-8")).hexdigest()
    return {
        "title": title[:180],
        "company": source_name[:180],
        "country": country[:100],
        "location": location[:120],
        "category": infer_category(combined),
        "type": job_type,
        "mode": mode,
        "experience": "",
        "salary": "Not provided",
        "sponsor": False,
        "featured": False,
        "posted": parse_date(entry),
        "deadline": None,
        "source": f"{source_name} (RSS feed)",
        "url": url,
        "description": f"{description}\n\nImported from {source_name}. Verify all details on the original listing before publishing.",
        "requirements": "Not supplied by the feed. Review the original listing and add verified requirements before publishing.",
        "status": "draft",
        "import_hash": digest,
    }

def existing_urls(urls):
    found = set()
    for start in range(0, len(urls), 50):
        batch = urls[start:start + 50]
        params = {"select": "url", "url": "in.(" + ",".join(batch) + ")"}
        r = requests.get(f"{SUPABASE_URL}/rest/v1/jobs", headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        found.update(x["url"] for x in r.json())
    return found

def main():
    try:
        feeds = json.loads(FEEDS_JSON)
        if not isinstance(feeds, list):
            raise ValueError("JOB_FEEDS_JSON must be a JSON array.")
    except Exception as exc:
        raise SystemExit(f"Invalid JOB_FEEDS_JSON: {exc}")
    if not feeds:
        print("No feeds configured. Add approved RSS/Atom feed URLs to the JOB_FEEDS_JSON repository variable.")
        return

    candidates = []
    for feed in feeds:
        feed_url = str(feed.get("url", "")).strip()
        if not feed_url.startswith("https://"):
            print(f"Skipping non-HTTPS feed: {feed_url}")
            continue
        parsed = feedparser.parse(feed_url)
        if parsed.bozo and not parsed.entries:
            print(f"Feed unavailable: {feed.get('name', feed_url)}: {parsed.bozo_exception}")
            continue
        for entry in parsed.entries[:100]:
            record = make_record(entry, feed)
            if record:
                candidates.append(record)

    # De-duplicate within this run and against existing job URLs.
    unique = {}
    for item in candidates:
        unique[item["url"]] = item
    candidates = list(unique.values())
    if not candidates:
        print("No usable job entries found.")
        return

    seen = existing_urls([x["url"] for x in candidates])
    new_items = [{k: v for k, v in x.items() if k != "import_hash"} for x in candidates if x["url"] not in seen]
    if not new_items:
        print(f"No new jobs. Checked {len(candidates)} feed entries.")
        return

    # Service-role key is used only in this GitHub Actions runner, never in site JavaScript.
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/jobs",
        headers={**HEADERS, "Prefer": "return=minimal"},
        json=new_items,
        timeout=60,
    )
    if not response.ok:
        print(response.text, file=sys.stderr)
        response.raise_for_status()
    print(f"Imported {len(new_items)} new jobs as DRAFT. Existing URLs skipped: {len(seen)}.")

if __name__ == "__main__":
    main()
