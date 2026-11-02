#!/usr/bin/env python3
"""Import approved RSS/Atom, UN Talent JSON API and ReliefWeb jobs into Supabase as drafts."""
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
SERVICE_KEY = os.environ["SUPABASE_SECRET_KEY"]
FEEDS_JSON = os.environ.get("JOB_FEEDS_JSON", "[]")
HEADERS = {
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}
TODAY = date.today().isoformat()
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "JobLinkAfricaJobImporter/1.0 (vacancy aggregation; contact site administrator)"})

def clean(value):
    if isinstance(value, list):
        value = ", ".join(str(x) for x in value)
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", value).strip()

def nested(obj, *path):
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj

def parse_date(value):
    if not value:
        return TODAY
    try:
        if isinstance(value, dict):
            value = value.get("date") or value.get("datetime")
        if not value:
            return TODAY
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            dt = parsedate_to_datetime(str(value))
            return dt.date().isoformat()
    except Exception:
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

def make_record(title, url, summary, posted, feed, original_company=""):
    title, url, summary = clean(title), str(url or "").strip(), clean(summary)
    if not title or not url:
        return None
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None

    combined = f"{title} {summary}"
    source_name = clean(feed.get("name") or parsed.netloc)
    company = clean(original_company) or source_name
    country = infer_country(combined, feed.get("country"))
    remote = "remote" in combined.lower() or "work from home" in combined.lower()
    location = "Remote" if remote else (country if country != "International / Not specified" else "Not specified")
    job_type = "Internship" if "intern" in combined.lower() else ("Contract" if "contract" in combined.lower() else "Full-time")
    mode = "Remote" if remote else "On-site"
    description = (summary or "Open the original listing to review the full vacancy details.")[:5000]
    return {
        "title": title[:180], "company": company[:180],
        "country": country[:100], "location": location[:120],
        "category": infer_category(combined), "type": job_type, "mode": mode,
        "experience": "", "salary": "Not provided", "sponsor": False,
        "featured": False, "posted": parse_date(posted), "deadline": None,
        "source": f"{source_name} (automated feed)",
        "url": url,
        "description": f"{description}\\n\\nImported from {source_name}. Verify details and application instructions on the original listing before publishing.",
        "requirements": "Not supplied or not verified. Review the original listing and add verified requirements before publishing.",
        "status": "draft",
    }

def rss_records(feed):
    feed_url = str(feed.get("url", "")).strip()
    if not feed_url.startswith("https://"):
        print(f"Skipping non-HTTPS feed: {feed_url}")
        return []
    parsed = feedparser.parse(feed_url)
    if parsed.bozo and not parsed.entries:
        print(f"Feed unavailable: {feed.get('name', feed_url)}: {parsed.bozo_exception}")
        return []
    records = []
    for entry in parsed.entries[:100]:
        record = make_record(
            entry.get("title"), entry.get("link"),
            entry.get("summary") or entry.get("description"),
            entry.get("published") or entry.get("updated"),
            feed,
        )
        if record:
            records.append(record)
    return records

def reliefweb_records(feed):
    # ReliefWeb requires a pre-approved appname on every API request.
    appname = str(feed.get("appname") or os.environ.get("RELIEFWEB_APPNAME") or "").strip()
    if not appname:
        print("Skipping ReliefWeb: add your approved RELIEFWEB_APPNAME after ReliefWeb approves it.")
        return []
    endpoint = "https://api.reliefweb.int/v2/jobs"
    payload = {
        "limit": min(int(feed.get("limit", 100)), 100),
        "preset": "latest",
        "profile": "list",
        "fields": {"include": [
            "title", "url", "body", "how_to_apply", "date.created",
            "date.closing", "country.name", "city", "source.name",
            "type.name", "career_categories.name", "experience.name"
        ]},
        "sort": ["date.created:desc"],
    }
    response = SESSION.post(endpoint, params={"appname": appname}, json=payload, timeout=45)
    if not response.ok:
        print(f"ReliefWeb API error ({response.status_code}): {response.text[:500]}", file=sys.stderr)
        response.raise_for_status()
    records = []
    for item in response.json().get("data", []):
        fields = item.get("fields", {})
        title = fields.get("title")
        # Use the original source URL. Do not fabricate an employer application link.
        url = fields.get("url")
        if isinstance(url, list):
            url = url[0] if url else ""
        source = nested(fields, "source", "name") or feed.get("name", "ReliefWeb")
        country_names = nested(fields, "country", "name") or feed.get("country")
        city = fields.get("city")
        location = ", ".join(x for x in [clean(city), clean(country_names)] if x)
        body = fields.get("body") or ""
        how_to_apply = fields.get("how_to_apply") or ""
        summary = "\n\n".join(x for x in [clean(body), clean(how_to_apply)] if x)
        meta = " ".join([
            clean(nested(fields, "type", "name")),
            clean(nested(fields, "career_categories", "name")),
            clean(nested(fields, "experience", "name")),
            clean(location),
        ])
        merged_feed = {**feed, "name": f"ReliefWeb — {clean(source)}", "country": clean(country_names) or feed.get("country")}
        record = make_record(title, url, summary, nested(fields, "date", "created"), merged_feed, clean(source))
        if record:
            record["location"] = location[:120] or record["location"]
            record["category"] = infer_category(f"{title} {summary} {meta}")
            closing = nested(fields, "date", "closing")
            record["deadline"] = parse_date(closing) if closing else None
            record["source"] = f"ReliefWeb API — {clean(source)}"
            record["description"] = (
                f"{summary[:4500]}\\n\\nListed by {clean(source)} via ReliefWeb. "
                "Check the original listing for current details and application instructions."
            )
            records.append(record)
    return records

def untalent_records(feed):
    """Read UN Talent JSON API; the open project describes fair use as free with attribution."""
    endpoint = str(feed.get("url") or "https://untalent.org/api/v1/jobs").strip()
    if not endpoint.startswith("https://"):
        print("Skipping UN Talent API: endpoint must use HTTPS.")
        return []
    params = {}
    for key in ("locationSlugs", "areaSlugs", "levelSlugs"):
        if feed.get(key):
            params[key] = str(feed[key])
    token = str(feed.get("token") or os.environ.get("UNTALENT_API_TOKEN") or "").strip()
    if token:
        params["token"] = token
    records = []
    max_pages = max(1, min(int(feed.get("pages", 1)), 5))
    page_size = int(feed.get("page_size", 100))
    for page in range(1, max_pages + 1):
        response = SESSION.get(endpoint, params={**params, "page": page}, timeout=45)
        if not response.ok:
            print(f"UN Talent API error ({response.status_code}): {response.text[:400]}", file=sys.stderr)
            response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("data") or payload.get("jobs") or payload.get("results") or payload.get("items") or []
            if isinstance(items, dict):
                items = items.get("data") or items.get("jobs") or []
        else:
            items = []
        if not isinstance(items, list) or not items:
            break
        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name")
            url = item.get("url") or item.get("link")
            company = item.get("company") or item.get("organization") or item.get("employer") or ""
            summary = item.get("description") or item.get("summary") or item.get("excerpt") or ""
            posted = item.get("published_at") or item.get("published") or item.get("created_at") or item.get("date")
            country = item.get("location") or item.get("country") or feed.get("country")
            merged = {**feed, "name": feed.get("name", "UN Talent"), "country": country or "International"}
            record = make_record(title, url, summary, posted, merged, clean(company))
            if record:
                record["source"] = "UN Talent"
                record["description"] += "\\n\\nSource: UN Talent. Follow the original listing link to review the vacancy and apply."
                records.append(record)
        if len(items) < page_size:
            break
    return records

def existing_urls(urls):
    found = set()
    # Avoid PostgREST in.(...) quoting problems by querying each URL exactly.
    for url in urls:
        params = {"select": "url", "url": f"eq.{url}", "limit": "1"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/jobs", headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        found.update(item["url"] for item in response.json())
    return found

def main():
    try:
        feeds = json.loads(FEEDS_JSON)
        if not isinstance(feeds, list):
            raise ValueError("JOB_FEEDS_JSON must be a JSON array.")
    except Exception as exc:
        raise SystemExit(f"Invalid JOB_FEEDS_JSON: {exc}")
    if not feeds:
        print("No feeds configured. Add approved RSS/Atom or API sources to JOB_FEEDS_JSON.")
        return

    candidates = []
    for feed in feeds:
        if not isinstance(feed, dict):
            continue
        kind = str(feed.get("type", "rss")).lower()
        try:
            if kind == "rss":
                candidates.extend(rss_records(feed))
            elif kind == "reliefweb":
                candidates.extend(reliefweb_records(feed))
            elif kind in ("untalent", "untalent_api"):
                candidates.extend(untalent_records(feed))
            else:
                print(f"Unsupported feed type '{kind}' for {feed.get('name', 'unnamed source')}; skipped.")
        except Exception as exc:
            print(f"Source failed ({feed.get('name', kind)}): {exc}", file=sys.stderr)

    unique = {}
    for item in candidates:
        unique[item["url"]] = item
    candidates = list(unique.values())
    if not candidates:
        print("No usable job entries found.")
        return

    seen = existing_urls([x["url"] for x in candidates])
    new_items = [x for x in candidates if x["url"] not in seen]
    if not new_items:
        print(f"No new jobs. Checked {len(candidates)} feed entries.")
        return

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/jobs",
        headers={**HEADERS, "Prefer": "return=minimal"},
        json=new_items,
        timeout=60,
    )
    if not response.ok:
        print(response.text[:1000], file=sys.stderr)
        response.raise_for_status()
    print(f"Imported {len(new_items)} new jobs as DRAFT. Existing URLs skipped: {len(seen)}.")

if __name__ == "__main__":
    main()
