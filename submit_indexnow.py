"""
submit_indexnow.py
==================
Submits pages of leadingtuition.co.uk to IndexNow.

IndexNow key: 8953b81f83ca47ef82f7680b35e64d91
Key file hosted at: https://www.leadingtuition.co.uk/8953b81f83ca47ef82f7680b35e64d91.txt

Usage:
  python submit_indexnow.py              # submit pages modified in the last 1 day
  python submit_indexnow.py --days 3    # submit pages modified in the last 3 days
  python submit_indexnow.py --all       # submit every page (full reindex)

IndexNow API accepts up to 10,000 URLs per request.
"""

import json
import urllib.request
import urllib.error
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone

SITE = "www.leadingtuition.co.uk"
BASE_URL = f"https://{SITE}"
KEY = "8953b81f83ca47ef82f7680b35e64d91"
KEY_LOCATION = f"{BASE_URL}/{KEY}.txt"
OUTPUT_DIR = Path(__file__).parent / "seo-generator" / "output"

# Pages to exclude from submission (noindex pages)
EXCLUDE_SUFFIXES = ["purchase-confirmed.html"]


def collect_urls(max_age_days=None):
    """
    Collect URLs from the output directory.

    If max_age_days is set, only include files whose modification time is
    within the last max_age_days days. This lets you submit only newly
    generated pages rather than reindexing the entire site every time.
    """
    now = time.time()
    cutoff = now - (max_age_days * 86400) if max_age_days is not None else None

    urls = []
    skipped = 0

    for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
        # Skip excluded files
        if any(html_file.name == ex for ex in EXCLUDE_SUFFIXES):
            continue

        # Skip files older than the cutoff
        if cutoff is not None:
            mtime = html_file.stat().st_mtime
            if mtime < cutoff:
                skipped += 1
                continue

        # Convert file path to URL
        rel = html_file.relative_to(OUTPUT_DIR)
        parts = rel.parts

        # index.html -> directory URL with trailing slash
        if parts[-1] == "index.html":
            path = "/" + "/".join(parts[:-1])
            if path != "/":
                path += "/"
        else:
            path = "/" + "/".join(parts)

        urls.append(BASE_URL + path)

    if cutoff is not None:
        mtime_str = datetime.fromtimestamp(cutoff, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"📅  Filtering to files modified after {mtime_str}")
        print(f"    {skipped} older files skipped, {len(urls)} new/modified files included")

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
    parser = argparse.ArgumentParser(description="Submit pages to IndexNow")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--days", type=int, default=1,
        help="Only submit pages modified within the last N days (default: 1)",
    )
    group.add_argument(
        "--all", action="store_true",
        help="Submit all pages regardless of modification date",
    )
    args = parser.parse_args()

    max_age = None if args.all else args.days

    if max_age is not None:
        print(f"🔍  Collecting pages modified in the last {max_age} day(s)...")
    else:
        print("🔍  Collecting ALL pages for full reindex...")

    urls = collect_urls(max_age_days=max_age)

    if not urls:
        print("ℹ️   No pages found matching the filter. Try --days 3 or --all.")
        return

    print(f"\n📋  {len(urls)} URL(s) to submit:")
    for u in urls[:10]:
        print(f"    {u}")
    if len(urls) > 10:
        print(f"    ... and {len(urls) - 10} more")

    print(f"\n🚀  Submitting to IndexNow (api.indexnow.org) ...")
    submit_urls(urls)
    print("\n✅  Done. Check Bing Webmaster Tools > IndexNow to see submission status.")


if __name__ == "__main__":
    main()
