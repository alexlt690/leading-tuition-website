"""
Standalone navbar sync script — no anthropic module needed.
Extracts the canonical <nav> and <script> blocks from templates.py and
propagates both to all output HTML files.
Run from: seo-generator/ directory
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from templates import service_page_template

OUTPUT_DIR = Path(__file__).parent / "output"

# Extract canonical nav + script from a rendered sample page
sample = service_page_template("__dummy__", "<p>x</p>")

nav_match = re.search(r'<nav class="navbar">.*?</nav>', sample, re.DOTALL)
if not nav_match:
    raise ValueError("Could not extract <nav> block from service_page_template output")
canonical_nav = nav_match.group(0)
print(f"Canonical nav extracted ({len(canonical_nav)} chars)")

script_match = re.search(r'<script>\s*\(function\(\).*?\}\)\(\);\s*</script>', sample, re.DOTALL)
if not script_match:
    raise ValueError("Could not extract nav <script> block from service_page_template output")
canonical_script = script_match.group(0)
print(f"Canonical script extracted ({len(canonical_script)} chars)")

nav_pattern    = re.compile(r'<nav class="navbar">.*?</nav>', re.DOTALL)
script_pattern = re.compile(r'<script>\s*\(function\(\).*?\}\)\(\);\s*</script>', re.DOTALL)

updated = 0
skipped = 0
for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
    content = html_file.read_text(encoding="utf-8")
    if '<nav class="navbar">' not in content:
        skipped += 1
        continue
    new_content = nav_pattern.sub(canonical_nav, content)
    new_content = script_pattern.sub(canonical_script, new_content)
    if new_content != content:
        html_file.write_text(new_content, encoding="utf-8")
        updated += 1
        print(f"  Updated: {html_file.relative_to(OUTPUT_DIR)}")
    else:
        skipped += 1

print(f"\nDone: nav+script updated in {updated} files ({skipped} files unchanged or no navbar)")
