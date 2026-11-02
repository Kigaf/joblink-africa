"""Conservative HTML importers for official Kenyan public-sector vacancy pages.

These are vacancy-page monitors, not public APIs. They preserve the official detail/
advert/PDF URL and create draft records only. Every item still needs human review.
"""
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OFFICIAL_KE_SOURCES = [
    {"name": "Kenya Public Service Commission (PSC)", "url": "https://www.psckjobs.go.ke/ActiveJobsAdverts.aspx", "domain": "psckjobs.go.ke"},
    {"name": "Judicial Service Commission (JSC)", "url": "https://jsc.go.ke/jsc_job_updates/jsc-advertised-positions/", "domain": "jsc.go.ke"},
    {"name": "National Police Service Commission (KPS/NPSC)", "url": "https://www.npsc.go.ke/advertised-jobs/", "domain": "npsc.go.ke"},
    {"name": "Teachers Service Commission (TSC)", "url": "https://recruitment.tsc.go.ke/", "domain": "tsc.go.ke"},
    {"name": "Ministry of Defence (MOD)", "url": "https://www.mod.go.ke/category/jobs/", "domain": "mod.go.ke"},
    {"name": "Kenyan Ministries & Public Agencies (Government Advertising Agency)", "url": "https://www.gaa.go.ke/job-adverts", "domain": "gaa.go.ke"},
    {"name": "Safaricom PLC", "url": "https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs", "domain": "egjd.fa.us6.oraclecloud.com"},
    {"name": "KCB Group", "url": "https://kcbgroup.com/careers", "domain": "kcbgroup.com"},
    {"name": "Kenya Airways", "url": "https://careers.kenya-airways.com/", "domain": "careers.kenya-airways.com"},
    {"name": "Central Bank of Kenya", "url": "https://careers.centralbank.go.ke/", "domain": "careers.centralbank.go.ke"},
    {"name": "Airtel Kenya", "url": "https://www.airtelkenya.com/ke/about/Careers", "domain": "airtelkenya.com"},
    {"name": "AirKenya", "url": "https://airkenya.com/careers/", "domain": "airkenya.com"},
    {"name": "Equity Bank Kenya", "url": "https://equitybank.taleo.net/careersection/int_new/jobsearch.ftl?ftlcompclass=LoginComponent&lang=en", "domain": "equitybank.taleo.net", "allow_unrelated_job_titles": True},
    {"name": "Co-operative Bank of Kenya", "url": "https://www.co-opbank.co.ke/careers/", "domain": "www.co-opbank.co.ke", "allow_unrelated_job_titles": True},
    {"name": "Nation Media Group", "url": "https://www.nationmedia.com/careers/", "domain": "www.nationmedia.com", "allow_unrelated_job_titles": True},
    {"name": "Jubilee Insurance", "url": "https://jubileeinsurance.com/ke/career-opportunities/", "domain": "jubileeinsurance.com", "allow_unrelated_job_titles": True},
    {"name": "National Bank of Kenya", "url": "https://nationalbank.co.ke/about-us/careers", "domain": "nationalbank.co.ke", "allow_unrelated_job_titles": True},
]

JOB_WORDS = re.compile(r"\b(vacanc(?:y|ies)|job|career|recruit|position|advert|internship|employment|shortlist)\b", re.I)
IGNORE_WORDS = re.compile(r"\b(read more|learn more|contact us|privacy|terms|download|login|register)\b", re.I)
CLOSED_WORDS = re.compile(r"\b(advert closed|applications closed|deadline passed|no longer accepting|shortlisted candidates|results of advert)\b", re.I)
DATE_PATTERNS = [
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b"),
]

def _date_from_text(text):
    for pattern in DATE_PATTERNS:
        match = pattern.search(text or "")
        if not match:
            continue
        raw = match.group(1)
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    return None

def official_vacancy_records():
    records = []
    headers = {"User-Agent": "JobLinkAfricaJobImporter/1.0 (+official vacancy page monitoring)"}
    for source in OFFICIAL_KE_SOURCES:
        try:
            response = requests.get(source["url"], headers=headers, timeout=35)
            response.raise_for_status()
            if urlparse(response.url).scheme != "https":
                print(f"Official source redirected away from HTTPS; skipped: {source['name']}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            # A page-level closure notice (e.g. TSC recruitment portal) prevents stale imports.
            page_text = soup.get_text(" ", strip=True)
            page_is_closed = bool(CLOSED_WORDS.search(page_text)) and "advert closed" in page_text.lower()
            seen = set()
            for anchor in soup.find_all("a", href=True):
                title = " ".join(anchor.get_text(" ", strip=True).split())
                # PSC rows label every detail link identically; use the position cell instead.
                row = anchor.find_parent("tr")
                if row:
                    cells = row.find_all(["td", "th"], recursive=False)
                    if len(cells) >= 3:
                        row_title = " ".join(cells[1].get_text(" ", strip=True).split())
                        if row_title:
                            title = row_title
                # For card-based pages, prefer a nearby heading over generic action text.
                if title.lower() in {"advert details", "download pdf", "apply here", "view details", "read more"}:
                    for parent in [anchor.parent, anchor.parent.parent if anchor.parent else None]:
                        if parent:
                            heading = parent.find(["h2", "h3", "h4", "h5"])
                            if heading and heading.get_text(" ", strip=True):
                                title = " ".join(heading.get_text(" ", strip=True).split())
                                break
                if not title or len(title) < 8 or len(title) > 220:
                    continue
                if not JOB_WORDS.search(title) and not re.search(r"\b(PSC|TSC|NPSC|JSC)\b", title, re.I):
                    # Career pages often show job titles without the words "job" or "vacancy".
                    card = anchor.find_parent(["article", "li", "tr"])
                    if not (source.get("allow_unrelated_job_titles") and card and
                            (card.find(["h2", "h3", "h4", "h5"]) or card.name == "tr")):
                        continue
                if IGNORE_WORDS.fullmatch(title):
                    continue
                href = urljoin(response.url, anchor["href"].strip())
                parsed = urlparse(href)
                if parsed.scheme != "https" or not parsed.netloc:
                    continue
                host = parsed.netloc.lower().split(":")[0]
                if not (host == source["domain"] or host.endswith("." + source["domain"])):
                    # Official recruitment portals sometimes link to a dedicated apply portal.
                    # Keep only same-source links here; external application URLs need review.
                    continue
                if href in seen:
                    continue
                seen.add(href)
                parent = anchor
                context = title
                for _ in range(4):
                    if parent.parent:
                        parent = parent.parent
                    snippet = " ".join(parent.get_text(" ", strip=True).split())
                    if len(snippet) > len(context):
                        context = snippet[:1800]
                    if parent.name in ("tr", "article", "li"):
                        break
                if page_is_closed or CLOSED_WORDS.search(context):
                    continue
                posted = _date_from_text(context)
                deadline = None
                # Avoid importing clearly stale notices; missing dates remain drafts for review.
                if posted and posted < date.today() - timedelta(days=120):
                    continue
                if posted and posted > date.today() + timedelta(days=2):
                    posted = None
                if not posted:
                    posted = date.today()
                summary = context[:1200]
                record = {
                    "title": title[:180],
                    "company": source["name"][:180],
                    "country": "Kenya",
                    "location": "Kenya",
                    "category": "Government & Public Service",
                    "type": "Internship" if "intern" in title.lower() else "Full-time",
                    "mode": "On-site",
                    "experience": "",
                    "salary": "Not provided",
                    "sponsor": False,
                    "featured": False,
                    "posted": posted.isoformat(),
                    "deadline": deadline.isoformat() if deadline else None,
                    "source": source["name"] + " (official vacancy page)",
                    "url": href,
                    "description": (
                        summary + "\n\nImported from the official vacancy page. "
                        "This is a draft summary only; verify the full advert, eligibility, "
                        "deadline and application method on the original page before publishing."
                    )[:5000],
                    "requirements": "Not extracted or verified. Review the original official advert before publishing.",
                    "status": "draft",
                }
                records.append(record)
        except Exception as exc:
            print(f"Official Kenyan source failed ({source['name']}): {exc}")
    print(f"Official Kenyan vacancy pages produced {len(records)} draft candidates.")
    return records
