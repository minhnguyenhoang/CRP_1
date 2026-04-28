import json
import os
from urllib.parse import urlparse

MANIFEST_FILE = "manifest.json"


DEFAULT_FIELDS = {
    "name": None,
    "url": None,
    "type": "link",
    "sha256": None,
    "last_checked": None,
    "last_modified": None
}


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except:
        return False


def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        return {"files": []}
    
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(data):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def generate_name_from_url(url: str) -> str:
    path = urlparse(url).path
    name = os.path.basename(path)
    return name if name else "unnamed_file"


def detect_type(url: str) -> str:
    if url.lower().endswith(".pdf"):
        return "pdf"
    return "link"


def normalize_manifest(manifest: dict) -> dict:
    """
    Ensure every file entry contains all expected fields.
    Also enforce type based on URL (.pdf => pdf, else link).
    """
    for entry in manifest.get("files", []):
        # Add missing fields
        for key, default_value in DEFAULT_FIELDS.items():
            if key not in entry:
                entry[key] = default_value

        # Enforce correct type based on URL
        url = entry.get("url", "")
        if isinstance(url, str) and url.lower().endswith(".pdf"):
            entry["type"] = "pdf"
        else:
            entry["type"] = "link"

    return manifest


def main():
    manifest = load_manifest()

    # Normalize existing entries before doing anything else
    manifest = normalize_manifest(manifest)

    print("Enter file URLs (input a non-link to stop):")

    while True:
        url = input("> ").strip()

        if not is_valid_url(url):
            print("Stopping input.")
            break

        entry = {
            "name": generate_name_from_url(url),
            "url": url,
            "type": detect_type(url),
            "sha256": None,
            "last_checked": None,
            "last_modified": None
        }

        manifest["files"].append(entry)
        print(f"Added: {entry['name']} ({entry['type']})")

    save_manifest(manifest)
    print(f"Saved to {MANIFEST_FILE}")


if __name__ == "__main__":
    main()