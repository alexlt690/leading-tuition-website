"""
Copies answer PDFs into a folder ready to upload to Cloudflare R2.

USAGE:
  python prepare_r2_upload.py

OUTPUT:
  Creates  r2_upload/  next to this script.
  The folder structure mirrors the R2 bucket exactly.

  Upload to R2:
    1. Go to Cloudflare dashboard → R2 → lt-answers
    2. Click Upload → Upload folder
    3. Select the  r2_upload/  folder
    Done!
"""

import csv
import re
import shutil
import sys
from pathlib import Path

CSV_PATH = Path(__file__).parent / "resources_page_mapping_with_local_paths_filtered-4558bcd2.csv"
OUT_DIR  = Path(__file__).parent / "r2_upload"


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def clean_repo_filename(src_path_str, is_answer=False):
    src = Path(src_path_str.replace("\\", "/"))
    fname = src.name.lower()
    fname = re.sub(r"^\d+__", "", fname)
    for prefix in ["elevenaid_", "11plusguide_", "piacademy_"]:
        if fname.startswith(prefix):
            fname = fname[len(prefix):]
            break
    fname = re.sub(r"^\d+(?=[a-z])", "", fname)
    fname = fname.lstrip("-_")
    fname = re.sub(r"[^a-z0-9._-]", "-", fname)
    fname = re.sub(r"-+", "-", fname).strip("-")
    if is_answer and not any(x in fname for x in ["mark-scheme", "answers", "answer"]):
        fname = fname.replace(".pdf", "-mark-scheme.pdf")
    return fname


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found — expected at:\n  {CSV_PATH}")
        sys.exit(1)

    # Collect uploads
    uploads = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            a_src = (row.get("answer_absolute_path") or "").strip()
            if not a_src or row.get("answer_file_exists", "").strip().lower() != "true":
                continue
            slug      = row["page_slug"]
            inst_slug = slugify(row["institution"])
            a_fname   = clean_repo_filename(a_src, True)
            r2_key    = f"{slug}/{inst_slug}/{a_fname}"
            uploads.append((r2_key, Path(a_src)))

    print(f"Found {len(uploads)} answer PDFs.\n")

    # Wipe and recreate output dir
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    ok = 0
    missing = []

    for r2_key, src in uploads:
        if not src.exists():
            missing.append(src)
            print(f"  MISSING  {src}")
            continue
        dest = OUT_DIR / r2_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  ✓  {r2_key}")
        ok += 1

    print(f"\n── Done ──")
    print(f"  Copied:  {ok} files  →  r2_upload/")
    if missing:
        print(f"  Missing: {len(missing)} files (skipped)")
    print(f"\nNext: Cloudflare → R2 → lt-answers → Upload → Upload folder → select r2_upload/")


if __name__ == "__main__":
    main()
