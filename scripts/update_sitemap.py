
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

BASE_URL = "https://kigaf.github.io/joblink-africa"
SITEMAP_FILE = Path("sitemap.xml")

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

def fetch_published_jobs():
    query = urllib.parse.urlencode({
        "select": "id,status,deadline",
        "status": "eq.published",
        "order": "posted.desc"
    })

    request = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/jobs?{query}",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Accept": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            jobs = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        raise RuntimeError(
            "Could not read jobs from Supabase. "
            "Check the repository secrets and Supabase read policies."
        ) from error

    today = date.today()
    published = []

    for job in jobs:
        if job.get("status") != "published":
            continue

        deadline = job.get("deadline")

        # Keep jobs with no deadline or a deadline that has not passed.
        if deadline:
            try:
                if date.fromisoformat(deadline) < today:
                    continue
            except ValueError:
                continue

        published.append(job)

    return published

def build_sitemap(jobs):
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)

    urlset = ET.Element(f"{{{namespace}}}urlset")

    static_pages = [
        f"{BASE_URL}/",
        f"{BASE_URL}/privacy.html",
        f"{BASE_URL}/terms.html",
    ]

    for url in static_pages:
        element = ET.SubElement(urlset, f"{{{namespace}}}url")
        ET.SubElement(element, f"{{{namespace}}}loc").text = url

    for job in jobs:
        job_id = job.get("id")
        if not job_id:
            continue

        job_url = (
            f"{BASE_URL}/job.html?"
            f"{urllib.parse.urlencode({'id': job_id})}"
        )

        element = ET.SubElement(urlset, f"{{{namespace}}}url")
        ET.SubElement(element, f"{{{namespace}}}loc").text = job_url

    xml_bytes = ET.tostring(
        urlset,
        encoding="utf-8",
        xml_declaration=True
    )

    SITEMAP_FILE.write_bytes(xml_bytes)
    print(f"Sitemap updated: {len(jobs)} published jobs included.")

if __name__ == "__main__":
    jobs = fetch_published_jobs()
    build_sitemap(jobs)
