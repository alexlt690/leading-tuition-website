"""
Standalone navbar sync script — no anthropic module needed.
Extracts the canonical <nav> from templates.py and propagates it to all output HTML files.
Run from: seo-generator/ directory
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from templates import service_page_template

OUTPUT_DIR = Path(__file__).parent / "output"

# Extract canonical nav from a rendered sample page
sample = service_page_template("__dummy__", "<p>x</p>")
match = re.search(r'<nav class="navbar">.*?</nav>', sample, re.DOTALL)
if not match:
    raise ValueError("Could not extract <nav> block from service_page_template output")
canonical_nav = match.group(0)
print(f"Canonical nav extracted ({len(canonical_nav)} chars)")

nav_pattern = re.compile(r'<nav class="navbar">.*?</nav>', re.DOTALL)

updated = 0
skipped = 0
for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
    content = html_file.read_text(encoding="utf-8")
    if '<nav class="navbar">' not in content:
        skipped += 1
        continue
    new_content = nav_pattern.sub(canonical_nav, content)
    if new_content != content:
        html_file.write_text(new_content, encoding="utf-8")
        updated += 1
        print(f"  Updated: {html_file.relative_to(OUTPUT_DIR)}")
    else:
        skipped += 1

print(f"\nDone: navbar updated in {updated} files ({skipped} files unchanged or no navbar)")
