"""
Copies Oxbridge Interview Question files into a folder ready to upload to Cloudflare R2.

USAGE:
  python prepare_r2_oxbridge.py

OUTPUT:
  Creates  r2_upload_oxbridge/  next to this script with two subfolders:
    oxbridge-samples/   <- free samples (served openly via /api/oxbridge-sample)
    oxbridge-packs/     <- paid packs   (served via /api/download after purchase)

Upload to R2:
  1. Cloudflare → R2 → lt-answers → Upload → Upload folder
  2. Select  r2_upload_oxbridge/
  Done!
"""

import re
import shutil
import sys
from pathlib import Path

BASE = Path(r"C:\Users\arunu\OneDrive\Documents\leading tuition\OxbridgeInterviewQuestions")
SAMPLES_SRC   = BASE / "Sample"
PACKS_SRC     = BASE / "Uncovered packs"
OUT_DIR       = Path(__file__).parent / "r2_upload_oxbridge"


def slugify(name):
    """'Vet Med 1' -> 'vet-med-1', 'Evolution & behaviour' -> 'evolution-behaviour'"""
    s = name.lower().strip()
    s = re.sub(r"[&]", "", s)           # strip ampersands
    s = re.sub(r"[^a-z0-9\s-]", "", s) # strip other special chars
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def copy_folder(src_dir, dest_prefix, label):
    pdfs = list(src_dir.glob("*.pdf"))
    if not pdfs:
        print(f"WARNING: no PDFs found in {src_dir}")
        return [], []

    ok, missing = [], []
    for src in sorted(pdfs):
        stem = src.stem  # filename without .pdf
        slug = slugify(stem)
        r2_key = f"{dest_prefix}/{slug}.pdf"
        dest = OUT_DIR / r2_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  ✓  {r2_key}  ({stem})")
        ok.append((r2_key, stem))
    return ok, missing


def main():
    if not BASE.exists():
        print(f"ERROR: source folder not found:\n  {BASE}")
        print("Run this script on your Windows machine.")
        sys.exit(1)

    # Wipe and recreate output
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    print("\n── Free samples ──────────────────────────────────")
    samples, _ = copy_folder(SAMPLES_SRC, "oxbridge-samples", "Sample")

    print("\n── Paid packs ────────────────────────────────────")
    packs, _ = copy_folder(PACKS_SRC, "oxbridge-packs", "Pack")

    print(f"\n── Done ──")
    print(f"  Samples: {len(samples)}  →  r2_upload_oxbridge/oxbridge-samples/")
    print(f"  Packs:   {len(packs)}   →  r2_upload_oxbridge/oxbridge-packs/")
    print(f"\nNext: Cloudflare → R2 → lt-answers → Upload → Upload folder → select r2_upload_oxbridge/")

    # Print the slug mapping for reference (used in the HTML page)
    print("\n── Pack slug mapping (for reference) ─────────────")
    for r2_key, label in packs:
        print(f"  '{label}' -> '{r2_key}'")


if __name__ == "__main__":
    main()
