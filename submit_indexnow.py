"""
submit_indexnow.py
==================
Submits all public pages of leadingtuition.co.uk to IndexNow.

IndexNow key: 8953b81f83ca47ef82f7680b35e64d91
Key file hosted at: https://www.leadingtuition.co.uk/8953b81f83ca47ef82f7680b35e64d91.txt

Run from the repo root:
  python submit_indexnow.py

IndexNow API accepts up to 10,000 URLs per request.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

SITE = "www.leadingtuition.co.uk"
BASE_URL = f"https://{SITE}"
KEY = "8953b81f83ca47ef82f7680b35e64d91"
KEY_LOCATION = f"{BASE_URL}/{KEY}.txt"
OUTPUT_DIR = Path(__file__).parent / "seo-generator" / "output"

# Pages to exclude from submission (noindex pages)
EXCLUDE_SUFFIXES = ["purchase-confirmed.html"]
EXCLUDE_DIRS = []

def collect_urls():
    urls = []
    for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
        # Skip excluded files
        if any(html_file.name == ex for ex in EXCLUDE_SUFFIXES):
            continue

        # Convert file path to URL
        rel = html_file.relative_to(OUTPUT_DIR)
        parts = rel.parts

        # index.html -> directory URL
        if parts[-1] == "index.html":
            path = "/" + "/".join(parts[:-1])
            if path != "/":
                path += "/"
        else:
            path = "/" + "/".join(parts)

        urls.append(BASE_URL + path)

    return urls


def submit_urls(urls):
    payload = {
        "host": SITE,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "LeadingTuition-IndexNow/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
            print(f"✅  IndexNow response: HTTP {status}")
            if body:
                print(f"    Body: {body[:200]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌  HTTP error {e.code}: {body[:300]}")
    except Exception as e:
        print(f"❌  Error: {e}")


def main():
    urls = collect_urls()
    print(f"📋  Collected {len(urls)} URLs to submit")
    for u in urls[:5]:
        print(f"    {u}")
    if len(urls) > 5:
        print(f"    ... and {len(urls) - 5} more")

    print(f"\n🚀  Submitting to IndexNow (api.indexnow.org) ...")
    submit_urls(urls)
    print("\n✅  Done. Check Bing Webmaster Tools > IndexNow to see submission status.")


if __name__ == "__main__":
    main()
