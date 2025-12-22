import json, os, time, requests
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(__file__))
SOURCES_FILE = os.path.join(ROOT, "scripts", "sources.json")
OUT_FILE = os.path.join(ROOT, "data", "jobs.json")

def now_iso():
  return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def fetch_remotive(query):
  url = "https://remotive.com/api/remote-jobs"
  r = requests.get(url, params={"search": query}, timeout=30)
  r.raise_for_status()
  data = r.json()
  jobs = []
  for j in data.get("jobs", []):
    jobs.append({
      "source": "Remotive",
      "title": j.get("title"),
      "company": j.get("company_name"),
      "location": j.get("candidate_required_location"),
      "url": j.get("url"),
      "summary": (j.get("description") or "")[:220].replace("\n"," ").strip()
    })
  return jobs

def fetch_usajobs(query):
  # Get these from GitHub Secrets: USAJOBS_EMAIL, USAJOBS_KEY
  email = os.environ.get("USAJOBS_EMAIL")
  key = os.environ.get("USAJOBS_KEY")
  if not email or not key:
    return []

  headers = {"User-Agent": email, "Authorization-Key": key}
  url = "https://data.usajobs.gov/api/search"
  r = requests.get(url, headers=headers, params={"Keyword": query}, timeout=30)
  r.raise_for_status()
  data = r.json()

  items = data.get("SearchResult", {}).get("SearchResultItems", [])
  jobs = []
  for it in items:
    m = it.get("MatchedObjectDescriptor", {})
    locs = m.get("PositionLocationDisplay") or ""
    jobs.append({
      "source": "USAJOBS",
      "title": m.get("PositionTitle"),
      "company": (m.get("OrganizationName") or "U.S. Government"),
      "location": locs,
      "url": m.get("PositionURI"),
      "summary": (m.get("UserArea", {}).get("Details", {}).get("JobSummary") or "")[:220].replace("\n"," ").strip()
    })
  return jobs

def main():
  os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
  cfg = json.load(open(SOURCES_FILE, "r", encoding="utf-8"))

  all_jobs = []
  for q in cfg.get("queries", []):
    if cfg.get("remotive"):
      all_jobs.extend(fetch_remotive(q))
    if cfg.get("usajobs"):
      all_jobs.extend(fetch_usajobs(q))
    time.sleep(0.5)

  # De-dup by url
  seen = set()
  dedup = []
  for j in all_jobs:
    u = j.get("url")
    if not u or u in seen:
      continue
    seen.add(u)
    dedup.append(j)

  out = {"updated_at": now_iso(), "jobs": dedup}
  json.dump(out, open(OUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
  print(f"Wrote {len(dedup)} jobs -> {OUT_FILE}")

if __name__ == "__main__":
  main()
