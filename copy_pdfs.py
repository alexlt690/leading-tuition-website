#!/usr/bin/env python3
"""
copy_pdfs.py — Run this script on your Windows machine.
Copies all resource PDFs from their source location into the repo
under seo-generator/output/public/papers/{slug}/{institution-slug}/
"""

import csv
import re
import shutil
from pathlib import Path

# ─── CONFIGURE THESE ────────────────────────────────────────────────────────
CSV_PATH = Path(r"C:\Users\arunu\PycharmProjects\pythonProject\anjali\paper_dedupe_run_v2\resources_page_mapping_with_local_paths_filtered.csv")
REPO_ROOT = Path(r"C:\Users\arunu\PycharmProjects\leading-tuition-website")
OUTPUT_BASE = REPO_ROOT / "seo-generator" / "output" / "public" / "papers"
# ────────────────────────────────────────────────────────────────────────────


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def clean_repo_filename(src_path_str, is_answer=False):
    """Derive a clean filename from the original source filename."""
    src = Path(src_path_str)
    fname = src.name.lower()
    # Strip leading numeric index e.g. "0225__"
    fname = re.sub(r"^\d+__", "", fname)
    # Strip known source prefixes so they don't appear in URLs
    for prefix in ["elevenaid_", "11plusguide_", "piacademy_"]:
        if fname.startswith(prefix):
            fname = fname[len(prefix):]
            break
    # Strip piacademy-style numeric index immediately before institution name (e.g. "13alleyns")
    fname = re.sub(r"^\d+(?=[a-z])", "", fname)
    fname = fname.lstrip("-_")
    fname = re.sub(r"[^a-z0-9._-]", "-", fname)
    fname = re.sub(r"-+", "-", fname).strip("-")
    if is_answer and not any(x in fname for x in ["mark-scheme", "answers", "answer"]):
        fname = fname.replace(".pdf", "-mark-scheme.pdf")
    return fname


copied = 0
skipped = 0
errors = []

with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Processing {len(rows)} rows...\n")

for row in rows:
    slug = row["page_slug"]
    institution = row["institution"]
    inst_slug = slugify(institution)

    # Question file
    q_src = row["question_absolute_path"].strip()
    if q_src and row["question_file_exists"] == "True":
        q_fname = clean_repo_filename(q_src, is_answer=False)
        dest_dir = OUTPUT_BASE / slug / inst_slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / q_fname
        if dest.exists():
            skipped += 1
        else:
            try:
                shutil.copy2(q_src, dest)
                print(f"  COPIED: {dest.relative_to(REPO_ROOT)}")
                copied += 1
            except Exception as e:
                errors.append((q_src, str(e)))
                print(f"  ERROR:  {q_src} — {e}")

    # Answer file (if present)
    a_src = row["answer_absolute_path"].strip()
    if a_src and row["answer_file_exists"] == "True":
        a_fname = clean_repo_filename(a_src, is_answer=True)
        dest_dir = OUTPUT_BASE / slug / inst_slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / a_fname
        if dest.exists():
            skipped += 1
        else:
            try:
                shutil.copy2(a_src, dest)
                print(f"  COPIED: {dest.relative_to(REPO_ROOT)}")
                copied += 1
            except Exception as e:
                errors.append((a_src, str(e)))
                print(f"  ERROR:  {a_src} — {e}")

print(f"\nDone.")
print(f"  Copied:  {copied}")
print(f"  Skipped: {skipped} (already existed)")
if errors:
    print(f"  Errors:  {len(errors)}")
    for src, err in errors:
        print(f"    {src}: {err}")
else:
    print(f"  Errors:  0")
print(f"\nPDFs are now in: {OUTPUT_BASE}")
print("Next step: git add seo-generator/output/public/ && git commit")
