"""
fix_location_h2s.py
====================
Brute-force replaces <h2> headings in location pages to match the 4-variant
structure defined in generate.py, WITHOUT calling the Claude API.

The content under each <h2> was written for the old headings, so this is an
imperfect fix — but it eliminates the identical-H2-skeleton problem that causes
Google to treat all location pages as near-duplicates.

Run from repo root:
    python seo-generator/fix_location_h2s.py

After running:
    python seo-generator/generate.py --sitemap
    commit and push to dev, verify, then merge to main.
"""

import re
import hashlib
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output" / "locations"

# ── Variant H2 definitions (must match generate.py exactly) ─────────────────
# gcse_section_title is always "GCSE and A-Level Support" in generate.py

def get_h2s(city, variant):
    return {
        0: [
            f"Private Tuition in {city} — Understanding the Local Landscape",
            "GCSE and A-Level Support",
            f"11+ and Selective School Entry in {city}",
            "University and Medicine Admissions Support",
            f"How Our Tutors Work with {city} Families",
            "Frequently Asked Questions",
        ],
        1: [
            f"Tutoring in {city} — What Local Families Ask Us Most",
            f"11+ and Grammar School Preparation in {city}",
            f"GCSE and A-Level Tuition Across {city}",
            "Oxbridge, Medicine, and Competitive University Applications",
            f"Why {city} Parents Choose Leading Tuition",
            f"Frequently Asked Questions about Tutoring in {city}",
        ],
        2: [
            f"Expert Tutors in {city} — How We're Different",
            "Medicine, Oxbridge, and University Admissions Coaching",
            f"A-Level and GCSE Tuition in {city}",
            f"Primary, 11+, and Early Secondary Support",
            f"What {city} Families Say About Working with Us",
            f"Common Questions from {city} Parents",
        ],
        3: [
            f"Supporting {city} Students from 11+ to University",
            f"Preparing for Selective Schools and the 11+ in {city}",
            f"Raising Grades at GCSE — {city} Schools and Exam Boards",
            f"A-Level Tuition and Sixth Form Support in {city}",
            f"Medical School and Oxbridge Preparation for {city} Applicants",
            "Frequently Asked Questions",
        ],
    }[variant]


def city_to_slug(city):
    return city.lower().replace(" ", "-")


def assign_variant(city):
    return int(hashlib.md5(city.encode()).hexdigest(), 16) % 4


def replace_h2s(html, new_h2s):
    """Replace first N <h2> tags (the content H2s) with new_h2s list.
    The final H2 is always a template-injected FAQ heading — left untouched."""
    existing = re.findall(r'<h2>.*?</h2>', html, re.DOTALL)
    # Pages have one extra trailing FAQ H2 from the template — ignore it
    content_h2s = existing[:-1] if existing and 'Frequently Asked Questions' in existing[-1] else existing

    if len(content_h2s) != len(new_h2s):
        return html, False, (
            f"H2 count mismatch: found {len(content_h2s)} content H2s "
            f"(+1 template FAQ), expected {len(new_h2s)}"
        )

    result = html
    for old, new_text in zip(content_h2s, new_h2s):
        new_tag = f"<h2>{new_text}</h2>"
        result = result.replace(old, new_tag, 1)

    changed = result != html
    return result, changed, None


def main():
    import csv

    csv_path = Path(__file__).parent / "locations.csv"
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        cities = [row["city"] for row in reader]

    print(f"Processing {len(cities)} location pages...\n")

    updated = []
    skipped = []
    errors = []

    for city in cities:
        slug = city_to_slug(city)
        html_path = OUTPUT_DIR / f"{slug}.html"

        if not html_path.exists():
            errors.append(f"  MISSING: {slug}.html")
            continue

        variant = assign_variant(city)
        new_h2s = get_h2s(city, variant)

        html = html_path.read_text(encoding="utf-8")
        new_html, changed, err = replace_h2s(html, new_h2s)

        if err:
            errors.append(f"  ERROR {city}: {err}")
            continue

        if changed:
            html_path.write_text(new_html, encoding="utf-8")
            updated.append(f"  {city} (variant {variant})")
        else:
            skipped.append(f"  {city} — already correct (variant {variant})")

    print("✅ Updated:")
    print("\n".join(updated) if updated else "  (none)")
    print("\n⏭  Skipped (already correct):")
    print("\n".join(skipped) if skipped else "  (none)")
    if errors:
        print("\n❌ Errors:")
        print("\n".join(errors))

    print(f"\nDone. {len(updated)} updated, {len(skipped)} skipped, {len(errors)} errors.")


if __name__ == "__main__":
    main()
