import hashlib
import requests
import asyncio
from initialisation import *
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import time

DOWNLOAD_DIR = os.path.expanduser("~/.openclaw/VinUniversityPolicies")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_and_hash(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        content = response.content
        sha256 = hashlib.sha256(content).hexdigest()

        last_modified = response.headers.get("Last-Modified")

        return sha256, last_modified

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None

def generate_safe_filename(url: str, filetype: str) -> str:
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:12]

    base = generate_name_from_url(url)

    if filetype == "pdf" and not base.endswith(".pdf"):
        base += ".pdf"
    elif filetype == "link" and not base.endswith(".html"):
        base += ".html"

    return f"{url_hash}_{base}"

def download_and_store(entry: dict):
    url = entry["url"]
    filetype = entry["type"]

    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        filename = generate_safe_filename(url, filetype)
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        hash_obj = hashlib.sha256()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    hash_obj.update(chunk)

        sha256 = hash_obj.hexdigest()
        last_modified = response.headers.get("Last-Modified")

        return filepath, sha256, last_modified

    except Exception as e:
        print(f"Download error for {url}: {e}")
        return None, None, None


def check_files():
    manifest = load_manifest()
    manifest = normalize_manifest(manifest)

    updated = False

    for entry in manifest.get("files", []):
        url = entry.get("url")
        if not url:
            continue

        print(f"Checking: {url}")

        filepath, new_hash, last_modified = download_and_store(entry)

        if not new_hash:
            continue

        if entry["sha256"] != new_hash:
            print(f"Updated: {entry['name']}")

            entry["sha256"] = new_hash
            entry["local_path"] = filepath
            entry["last_modified"] = last_modified
            entry["last_checked"] = datetime.utcnow().isoformat()

            updated = True
        else:
            print(f"No change: {entry['name']}")
            entry["last_checked"] = datetime.utcnow().isoformat()

    if updated:
        save_manifest(manifest)

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Example: run every 10 minutes
    scheduler.add_job(check_files, "interval", minutes=60, next_run_time=datetime.now() + timedelta(seconds=1), start_date=datetime.now() + timedelta(seconds=1))

    # Or cron style:
    # scheduler.add_job(check_files, "cron", hour="*/1")  # every hour

    scheduler.start()
    print("Scheduler started.")

if __name__ == "__main__":
    start_scheduler()

    try:
        asyncio.run(asyncio.Event().wait())
    except KeyboardInterrupt:
        pass