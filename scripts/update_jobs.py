import json, os, time, requests
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(__file__))
CFG = os.path.join(ROOT, "scripts", "sources.json")
OUT = os.path.join(ROOT, "data", "jobs.json")

KEYWORDS = [
    "gis", "geospatial", "wildfire", "fire", "evacuation",
    "traffic", "transportation", "hazard", "disaster",
    "remote sensing", "modeling", "simulation"
]
EXCLUDE_PHRASES = [
    "u.s. citizen only",
    "us citizen only",
    "must be a u.s. citizen",
    "security clearance",
    "secret clearance",
    "top secret",
    "dod",
    "department of defense",
    "clearance required"
]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def relevant(text):
    t = text.lower()

    # Exclude restricted jobs
    if any(p in t for p in EXCLUDE_PHRASES):
        return False

    # Keep only relevant keywords
    return any(k in t for k in KEYWORDS)


def fetch_remotive(q):
    url = "https://remotive.com/api/remote-jobs"
    r = requests.get(url, params={"search": q}, timeout=30)
    r.raise_for_status()
    jobs = []

    for j in r.json().get("jobs", []):
        text = f"{j.get('title','')} {j.get('description','')}"
        if not relevant(text):
            continue

        jobs.append({
            "source": "Remotive",
            "title": j["title"],
            "company": j["company_name"],
            "location": j["candidate_required_location"],
            "url": j["url"],
            "summary": j["description"][:250].replace("\n", " ")
        })
    return jobs

def fetch_usajobs(q):
    email = os.environ.get("USAJOBS_EMAIL")
    key = os.environ.get("USAJOBS_KEY")
    if not email or not key:
        return []

    headers = {"User-Agent": email, "Authorization-Key": key}
    url = "https://data.usajobs.gov/api/search"
    r = requests.get(url, headers=headers, params={"Keyword": q}, timeout=30)
    r.raise_for_status()

    jobs = []
    for it in r.json()["SearchResult"]["SearchResultItems"]:
        m = it["MatchedObjectDescriptor"]
        text = f"{m.get('PositionTitle','')} {m.get('UserArea',{})}"
        if not relevant(text):
            continue

        jobs.append({
            "source": "USAJOBS",
            "title": m["PositionTitle"],
            "company": m["OrganizationName"],
            "location": m.get("PositionLocationDisplay", ""),
            "url": m["PositionURI"],
            "summary": m.get("UserArea", {}).get("Details", {}).get("JobSummary", "")[:250]
        })
    return jobs

def main():
    cfg = json.load(open(CFG))
    all_jobs = []

    for q in cfg["queries"]:
        if cfg["remotive"]:
            all_jobs += fetch_remotive(q)
        if cfg["usajobs"]:
            all_jobs += fetch_usajobs(q)
        time.sleep(0.5)

    # Deduplicate
    seen = set()
    jobs = []
    for j in all_jobs:
        if j["url"] not in seen:
            seen.add(j["url"])
            jobs.append(j)

    json.dump(
        {"updated_at": now(), "jobs": jobs},
        open(OUT, "w"),
        indent=2
    )

if __name__ == "__main__":
    main()

