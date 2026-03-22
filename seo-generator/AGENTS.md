# AGENTS.md — Leading Tuition Website: Architecture & Rules for AI Agents

Read this entire file before making any changes. It exists because previous agents (and humans) made costly mistakes by misunderstanding the architecture. Every section is a hard-won learning.

---

## 1. CRITICAL: How Cloudflare Serves This Site

**Cloudflare Pages build output directory: `/seo-generator/output`**

This is the single most important fact. Cloudflare does NOT serve from the repo root. It serves exclusively from `seo-generator/output/`. Every public URL maps directly into that directory:

| Public URL | File on disk |
|---|---|
| `leadingtuition.co.uk/` | `seo-generator/output/index.html` |
| `leadingtuition.co.uk/blog/post-slug` | `seo-generator/output/blog/post-slug.html` |
| `leadingtuition.co.uk/admissions-tests/bmat/` | `seo-generator/output/admissions-tests/bmat/index.html` |
| `leadingtuition.co.uk/robots.txt` | `seo-generator/output/robots.txt` |
| `leadingtuition.co.uk/sitemap.xml` | `seo-generator/output/sitemap.xml` |

**The repo root (files like `/blog/`, `/locations/`, `/index.html`) is NOT served publicly.** Those files exist in the repo but Cloudflare ignores them. Do not add pages there expecting them to go live.

**Consequence:** If you delete any file from `seo-generator/output/`, that page goes down on the live site.

---

## 2. generate.py — How It Works

- **Location:** `seo-generator/generate.py`
- **OUTPUT_DIR:** `Path("output")` — relative path, always outputs to `seo-generator/output/`
- **Run from:** Always `cd seo-generator/` first, then `python generate.py ...`
- **CSV files** (blog_topics.csv, locations.csv, etc.) are read from `seo-generator/` directory
- **API:** Uses `claude-sonnet-4-6` via Anthropic API, temperature 0.35
- **`--new-only` flag:** Skips files that already exist in output. Use this to avoid regenerating pages.

### Key CLI flags
```
python generate.py --blog --new-only          # generate new blog posts only
python generate.py --oxbridge-interviews --new-only  # generate Oxbridge interview pages
python generate.py --navbar                   # propagate navbar to all output HTML files
python generate.py --sitemap                  # regenerate sitemap.xml from output/ directory
python generate.py --all                      # generate everything
```

### What generate.py generates (in seo-generator/output/)
- `blog/slug.html` — blog posts (from blog_topics.csv)
- `locations/city.html` — location pages (from locations.csv)
- `admissions-tests/slug/index.html` — admissions test pages (from admissions_tests.csv)
- `medical-schools/slug/index.html` — medical school pages (from medical_schools.csv)
- `oxbridge-interviews/subject-interview/index.html` — Oxbridge pages (from oxbridge_interviews.csv)
- `services/specialist-admissions/slug.html` or `slug/index.html` — service pages
- `index.html`, `blog.html`, `locations.html` etc. — static hub pages

---

## 3. File Structure That Must Always Exist in seo-generator/output/

These flat HTML files at the root of `seo-generator/output/` are real pages. **Never delete them.** Their absence takes down those URLs:

```
seo-generator/output/
  index.html          → leadingtuition.co.uk/
  about.html          → leadingtuition.co.uk/about
  contact.html        → leadingtuition.co.uk/contact
  consultation.html   → leadingtuition.co.uk/consultation
  faqs.html           → leadingtuition.co.uk/faqs
  services.html       → leadingtuition.co.uk/services
  tutors.html         → leadingtuition.co.uk/tutors
  blog.html           → leadingtuition.co.uk/blog
  locations.html      → leadingtuition.co.uk/locations
  subjects.html       → leadingtuition.co.uk/subjects
  sitemap.xml         → leadingtuition.co.uk/sitemap.xml
  robots.txt          → leadingtuition.co.uk/robots.txt
  style.css           → leadingtuition.co.uk/style.css
```

---

## 4. Git Branch Structure

- **`main`** — production branch, deploys to `www.leadingtuition.co.uk`
- **`dev`** — staging branch, deploys to a preview URL like `{hash}.leading-tuition-website.pages.dev`
- **Cloudflare project name:** `leading-tuition-seo`
- Each push to `dev` creates a NEW preview URL. The old URL is invalidated. Always get the latest URL from the Cloudflare dashboard.

---

## 5. SEO / Google Search Console Issues & Root Causes

### What was found in GSC
- "Duplicate without user-selected canonical" — caused by stale pages with identical canonical tags
- "Not found 404" — caused by stale pages with canonicals pointing to URLs that don't exist
- "Crawled - currently not indexed" — caused by thin/stale pages with wrong canonical targets
- "Discovered - currently not indexed" — new pages not yet crawled; normal, resolves over time

### What caused the duplicate/404 issues
- Old `gcse-maths-tutor.html`, `gcse-maths-help.html` etc. in `seo-generator/output/` had canonical tags pointing to `/gcse-maths-tutor` (a URL that doesn't exist). These have been deleted from `dev`.
- Old `medicine-prep/` directory had wrong URL structure. Deleted from `dev`.

### robots.txt
- Must live at `seo-generator/output/robots.txt` (NOT repo root) to be served at `/robots.txt`
- Currently: `Allow: /` with sitemap pointer — all pages are crawlable
- Do NOT add `Disallow: /seo-generator/` — that path does not exist publicly (Cloudflare serves from `seo-generator/output/`, so there is no `/seo-generator/` in the public URL namespace)

---

## 6. templates.py — Key Facts

- **Location:** `seo-generator/templates.py`
- Four template functions: `service_page_template`, `blog_page_template`, `location_page_template`, `page_template`
- All four share the same navbar HTML — use `--navbar` flag or `generate_navbar()` to sync changes
- **Navbar blog dropdown:** Shows 8 featured posts + "View all posts →" link (not all posts)
- **`page_url_path()`** has mapping `"oxbridge-interview": "oxbridge-interviews"` — needed for correct canonical URLs
- **`breadcrumb_schema()`** handles oxbridge-interview case explicitly

---

## 7. URL / Canonical Tag Patterns

Canonical tags must always match the actual public URL exactly:

| Page type | Canonical format | File location |
|---|---|---|
| Homepage | `https://www.leadingtuition.co.uk/` | `output/index.html` |
| Blog post | `https://www.leadingtuition.co.uk/blog/slug` | `output/blog/slug.html` |
| Location | `https://www.leadingtuition.co.uk/locations/city` | `output/locations/city.html` |
| Admissions test | `https://www.leadingtuition.co.uk/admissions-tests/slug/` | `output/admissions-tests/slug/index.html` |
| Medical school | `https://www.leadingtuition.co.uk/medical-schools/slug/` | `output/medical-schools/slug/index.html` |
| Oxbridge interview | `https://www.leadingtuition.co.uk/oxbridge-interviews/subject-interview/` | `output/oxbridge-interviews/subject-interview/index.html` |

**Note:** Directory-style pages (`index.html` inside a folder) use a trailing slash in the canonical. Flat `.html` files do not.

---

## 8. Common Mistakes Made By Previous Agents (Do Not Repeat)

1. **Assumed Cloudflare serves from repo root** — it serves from `seo-generator/output/`. Verify with Cloudflare Pages settings before assuming anything.

2. **Changed OUTPUT_DIR in generate.py to point to repo root** — this breaks the entire workflow. OUTPUT_DIR must stay as `Path("output")`.

3. **Deleted flat HTML files from seo-generator/output/** (index.html, about.html etc.) thinking they were duplicates — they are the actual live pages. Deleting them takes down the site.

4. **Put robots.txt at repo root** — it must be in `seo-generator/output/` to be publicly accessible.

5. **Added Disallow: /seo-generator/ to robots.txt** — that path doesn't exist publicly. Harmless but misleading.

6. **Copied generated pages to repo root** — those copies are never served. Only `seo-generator/output/` content is served.

7. **Confused preview URLs** — each `git push origin dev` creates a new preview URL. Previous preview URLs stop working. Always check Cloudflare dashboard for the current URL. The project is named `leading-tuition-seo`.

8. **Staged and committed generate.py while it had unsaved/empty state** — always verify file size before committing: `wc -l seo-generator/generate.py` should be ~3500 lines.

9. **Synced navbar to standard pages from templates.py without verifying stylesheet loaded first** — when standard pages (services, consultation, faqs, tutors) had broken meta tags causing no CSS to load, the unstyled result was mistakenly attributed to the navbar change. Always verify CSS is loading before diagnosing layout issues (see Section 11).

10. **Blog post links in blog.html used relative hrefs** — the page is served at `/blog` (not `/blog/`), so `href="slug"` resolves to `/slug` not `/blog/slug`. All post links in `blog.html` must use absolute paths: `href="/blog/slug"`.

11. **Navbar inconsistency between standard pages and generated pages** — the standard flat pages (`seo-generator/output/*.html`) and generated pages (`blog/`, `oxbridge-interviews/`) are templated separately. After any navbar update in `templates.py`, both sets must be synced. See Section 12 for the correct sync procedure.

---

## 11. Critical: Meta Description Tag Syntax — Must Close with `/>`

Any `<meta>` tag that is not properly closed causes the HTML5 parser to treat the next tag as an attribute rather than a new element. This means a missing `/>` on a `<meta name="description">` tag will cause the following `<link rel="stylesheet">` to be silently swallowed, resulting in **zero stylesheets loading**.

**Symptom:** Page renders with a giant logo image and unstyled content. The navbar logo (`<img src="/images/logo.png">`) renders at its full natural size because no CSS is applied.

**Diagnosis:** In browser DevTools console run:
```js
document.querySelectorAll('link[rel="stylesheet"]').length  // returns 0 if broken
document.head.innerHTML.substring(0, 500)  // reveals the malformed tag
```

**Broken (causes no CSS to load):**
```html
<meta name="description" content="Some description text">
<link rel="stylesheet" href="/style.css" />
```

**Correct:**
```html
<meta name="description" content="Some description text" />
<link rel="stylesheet" href="/style.css" />
```

**Fix:** Always close meta tags with ` />`. To check all files at once:
```bash
grep -rn '<meta name="description" content="[^"]*">' seo-generator/output/
```
Any match (without `/>`) is broken. Fix with:
```bash
sed -i 's|<meta name="description" content="\(.*\)"$|<meta name="description" content="\1" />|' path/to/file.html
```

**Affected files historically:** `services.html`, `consultation.html`, `faqs.html`, `tutors.html` — these were restored from `main` branch without the closing `/>` and had to be manually corrected.

---

## 12. Navbar Sync — Canonical Source and Procedure

There are **two navbar variants** in the repo:

| Navbar version | Where it lives | Used by |
|---|---|---|
| **Canonical (newer)** | `templates.py` → propagated via `generate.py --navbar` | `blog/*.html`, `oxbridge-interviews/**/*.html`, `locations/**/*.html`, all generated pages |
| **Flat page copies** | Manually maintained in each `seo-generator/output/*.html` | `index.html`, `about.html`, `contact.html`, `consultation.html`, `faqs.html`, `services.html`, `tutors.html`, `locations.html`, `subjects.html`, `blog.html` |

**The canonical navbar** (as of March 2026) has:
- 4 columns in the Services mega-menu: Subjects, Levels, Specialist & Admissions, **Admissions Tests**
- Blog dropdown: 8 featured posts + "View all posts →" link
- Includes `/oxbridge-interviews/` link under Specialist & Admissions

**When to sync:** After any navbar change in `templates.py`, run:
```bash
cd seo-generator && python generate.py --navbar
```
This updates all generated pages. Then manually sync the flat standard pages using this Python snippet:
```python
import re, os

with open('blog/oxbridge-interview-questions-100-real-examples-for-every-major-subject.html') as f:
    canonical_navbar = re.search(r'(<nav class="navbar">.*?</nav>)', f.read(), re.DOTALL).group(1)

flat_pages = [
    'seo-generator/output/index.html',
    'seo-generator/output/about.html',
    'seo-generator/output/contact.html',
    'seo-generator/output/consultation.html',
    'seo-generator/output/faqs.html',
    'seo-generator/output/tutors.html',
    'seo-generator/output/locations.html',
    'seo-generator/output/subjects.html',
    'seo-generator/output/services.html',
    'seo-generator/output/blog.html',
]

for path in flat_pages:
    with open(path) as f:
        content = f.read()
    new_content = re.sub(r'<nav class="navbar">.*?</nav>', canonical_navbar, content, flags=re.DOTALL)
    if new_content != content:
        with open(path, 'w') as f:
            f.write(new_content)
        print(f"Updated: {path}")
```

**Verify sync with Python** (not `sed -n` / `md5sum` — those stop at first `</nav>` and give false mismatches):
```python
import re
with open('blog/oxbridge-interview-questions-100-real-examples-for-every-major-subject.html') as f:
    ref = re.search(r'<nav class="navbar">.*?</nav>', f.read(), re.DOTALL).group(0)
with open('seo-generator/output/index.html') as f:
    idx = re.search(r'<nav class="navbar">.*?</nav>', f.read(), re.DOTALL).group(0)
print("Match:", ref == idx)  # Must be True
```

**Do NOT use `git checkout main -- file.html`** to restore standard pages — the `main` branch has an older navbar. This reintroduces inconsistency and requires another sync pass.

---

## 9. Workflow for Adding New Pages

1. Add the new page's slug/title/metadata to the relevant CSV in `seo-generator/`
2. Add a custom prompt branch in `blog_prompt()` or equivalent function in `generate.py`
3. Add the slug to `BLOG_RELATED_RESOURCES` dict for interlinking
4. Run: `python generate.py --[flag] --new-only` from `seo-generator/` directory
5. Run: `python generate.py --navbar` to propagate navbar to new files
6. Run: `python generate.py --sitemap` to update sitemap
7. Verify the file exists in `seo-generator/output/` at the expected path
8. Commit `seo-generator/output/` changes and push to `dev`
9. Verify preview URL works before merging to `main`

---

## 10. Sitemap

- **Served at:** `leadingtuition.co.uk/sitemap.xml` → `seo-generator/output/sitemap.xml`
- **Generated by:** `python generate.py --sitemap` (scans all HTML files in `seo-generator/output/`)
- **Priority rules:** 1.0 homepage, 0.9 hub pages (/a-level/, /gcse/, /admissions-tests/ etc.), 0.8 individual sub-pages, 0.7 locations/services/levels, 0.6 blog/static pages
- **Submitted to GSC:** Only submit the main sitemap URL, not the dev preview URL
