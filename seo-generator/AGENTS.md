# AGENTS.md — Leading Tuition Website

> **Read this file in full before making any changes.**
> Every rule here exists because a previous agent (or human) broke something by not knowing it.

---

## QUICK REFERENCE

| What you need | Answer |
|---|---|
| Cloudflare build output dir | `seo-generator/output/` |
| Cloudflare project name | `leading-tuition-seo` |
| Production branch | `main` → `www.leadingtuition.co.uk` |
| Staging branch | `dev` → new preview URL on every push |
| Run generate.py from | `cd seo-generator/` first, then `python generate.py ...` |
| Claude model used | `claude-sonnet-4-6`, temperature 0.35 |
| generate.py line count | ~3500 lines — verify with `wc -l seo-generator/generate.py` before committing |
| .gitignore encoding | UTF-16 (Windows BOM) — always open in binary mode |
| Canonical www version | `https://www.leadingtuition.co.uk` (www, HTTPS) |
| Who commits | **The human commits. Agents do not commit or push.** |

---

## HARD RULES — NEVER VIOLATE

These are the most common agent errors. Check this list before touching anything.

1. **Do NOT serve from repo root.** Cloudflare serves exclusively from `seo-generator/output/`. Files at the repo root are NOT public.
2. **Do NOT change `OUTPUT_DIR` in `generate.py`.** It must stay `SCRIPT_DIR / "output"` (i.e. `seo-generator/output/`). Verify: `grep "OUTPUT_DIR" seo-generator/generate.py` must show `SCRIPT_DIR / "output"`.
3. **Do NOT delete flat HTML files from `seo-generator/output/`** (`index.html`, `about.html`, `contact.html`, etc.). Deleting them takes down those live URLs immediately.
4. **Do NOT put `robots.txt` at the repo root.** It must live at `seo-generator/output/robots.txt`.
5. **Do NOT add `Disallow: /seo-generator/` to robots.txt.** That path does not exist in the public URL namespace.
6. **Do NOT copy generated pages to the repo root.** They will never be served from there.
7. **Do NOT use `git checkout main -- file.html` to restore standard pages.** `main` has an older navbar; this reintroduces inconsistency.
8. **Do NOT add `aggregateRating` to `@type: "Service"` JSON-LD schemas.** Only `EducationalOrganization`/`Organization` schemas at homepage level may have `aggregateRating`.
9. **Do NOT use inline `onclick` inside Python f-strings** (e.g. in resource pages). Python `\'` collapses to `'` in the HTML, breaking JS. Use `data-*` attributes and event delegation.
10. **Do NOT use Python's built-in `hash()` for variant assignment.** It is randomised per process (PYTHONHASHSEED). Use `hashlib.md5` instead.
11. **`.gitignore` is UTF-8 (converted March 2026).** Edit it normally. Do NOT re-encode as UTF-16 — git cannot reliably parse UTF-16 gitignore files, causing entries like `.env` to be silently ignored by git (i.e. not gitignored). Verify with `git check-ignore -v .env`.
12. **Do NOT close `<meta>` tags without `/>`.** A missing `/>` on a meta tag causes the HTML parser to swallow the next tag, breaking stylesheet loading. Every `<meta ... />` must end with ` />`.
13. **Do NOT use relative `href` in `blog.html` post links.** The page is at `/blog` (no trailing slash), so `href="slug"` resolves to `/slug`. Use absolute paths: `href="/blog/slug"`.
14. **Do NOT commit `generate.py` without verifying its size** (`wc -l seo-generator/generate.py` should be ~3500 lines).
15. **Do NOT regenerate pages when files already exist in the wrong location.** Copy them instead — saves API credits. `cp -r locations/*.html seo-generator/output/locations/`.
16. **Do NOT run `submit_indexnow.py` against the dev preview URL.** Only submit production URLs (`www.leadingtuition.co.uk`).
17. **Do NOT hardcode Google Drive folder URLs or Stripe keys in code.** All sensitive values live in Cloudflare environment variables.
18. **Do NOT add "Google Drive" wording to any user-facing copy** in `purchase-confirmed.html` or resource pages. Drive is an implementation detail.

---

## 1. Cloudflare Serving & File Paths

**Build output directory:** `seo-generator/output/` — Cloudflare serves nothing else.

### Public URL → file mapping

| Public URL | File on disk |
|---|---|
| `leadingtuition.co.uk/` | `seo-generator/output/index.html` |
| `leadingtuition.co.uk/blog/post-slug` | `seo-generator/output/blog/post-slug.html` |
| `leadingtuition.co.uk/admissions-tests/slug/` | `seo-generator/output/admissions-tests/slug/index.html` |
| `leadingtuition.co.uk/medical-schools/slug/` | `seo-generator/output/medical-schools/slug/index.html` |
| `leadingtuition.co.uk/oxbridge-interviews/slug/` | `seo-generator/output/oxbridge-interviews/slug/index.html` |
| `leadingtuition.co.uk/robots.txt` | `seo-generator/output/robots.txt` |
| `leadingtuition.co.uk/sitemap.xml` | `seo-generator/output/sitemap.xml` |

### Protected flat files — never delete

```
seo-generator/output/
  index.html          about.html          contact.html
  consultation.html   faqs.html           services.html
  tutors.html         blog.html           locations.html
  subjects.html       sitemap.xml         robots.txt
  style.css
  resources/index.html
  resources/pre-11-plus.html
  resources/11-plus.html
  resources/13-plus.html
  resources/oxbridge-interview-questions.html
  resources/gcse-resources-for-parents.html
```

### GSC ghost URLs — do nothing

GSC may show errors for `/seo-generator/output/locations/london` (with the full internal path). These are stale from when Cloudflare briefly served the repo root. They 404 naturally and expire on their own. Do not create redirects or files for them.

---

## 2. generate.py — Usage

**Always run from:** `cd seo-generator/` then `python generate.py ...`

### CLI flags

```bash
python generate.py --blog --new-only            # new blog posts only (skips existing)
python generate.py --oxbridge-interviews --new-only
python generate.py --medical-schools --new-only
python generate.py --admissions-tests --new-only
python generate.py --locations --new-only
python generate.py --navbar                     # sync navbar to all output HTML files
python generate.py --sitemap                    # regenerate sitemap.xml
python generate.py --all                        # generate everything
```

`--new-only` skips files already present in `seo-generator/output/`. Omit it only when regenerating existing pages intentionally.

### What it generates

| Output path | Source CSV |
|---|---|
| `output/blog/slug.html` | `blog_topics.csv` |
| `output/locations/city.html` | `locations.csv` |
| `output/admissions-tests/slug/index.html` | `admissions_tests.csv` |
| `output/medical-schools/slug/index.html` | `medical_schools.csv` |
| `output/oxbridge-interviews/subject-interview/index.html` | `oxbridge_interviews.csv` |

### API retry behaviour

`ask_claude()` retries up to 5 times on 529 (overload) with delays of 30/60/90/120/150s. If it still fails, wait a few minutes and re-run with `--new-only`.

---

## 3. URL & Canonical Tag Patterns

Canonical tags must exactly match the live public URL.

| Page type | Canonical format | Trailing slash? |
|---|---|---|
| Homepage | `https://www.leadingtuition.co.uk/` | Yes |
| Blog post | `https://www.leadingtuition.co.uk/blog/slug` | No |
| Location | `https://www.leadingtuition.co.uk/locations/city` | No |
| Admissions test | `https://www.leadingtuition.co.uk/admissions-tests/slug/` | Yes |
| Medical school | `https://www.leadingtuition.co.uk/medical-schools/slug/` | Yes |
| Oxbridge interview | `https://www.leadingtuition.co.uk/oxbridge-interviews/subject-interview/` | Yes |

**Rule:** `index.html` pages (directory-style) → trailing slash. Flat `.html` files → no trailing slash.

---

## 4. Meta Descriptions

### Quality standard

Every meta description must:
- Be **145–158 characters** (including spaces)
- Include the **target keyword naturally** (once)
- **Answer what the page covers** specifically
- **Give a reason to click** — a specific fact, angle, or promise
- **Never use generic filler**: "Expert advice from Leading Tuition", "Book a free consultation", "Find out more"

### Three-tier priority in `generate_blog_pages()`

| Priority | Source | How |
|---|---|---|
| 1 (highest) | `meta_desc` column in `blog_topics.csv` | Add column; value used verbatim (truncated to 160 chars) |
| 2 | `META_DESC:` line in Claude's response | Extracted by `parse_meta_desc(raw)` |
| 3 (fallback) | Formula | `f"{title} — practical guidance for UK students and parents. Expert tutors from Oxford and Cambridge. 4.8/5 Trustpilot."` |

### META_DESC: protocol

`blog_prompt()` instructs Claude to output exactly:
```
META_DESC:Your compelling meta description here, 145-158 chars, keyword-rich, specific.
```
`parse_meta_desc(raw)` in `generate.py` extracts this line. `parse_faq_schema()` strips it before it can leak into page content.

### Specialist and location pages

Set via `OXBRIDGE_INTERVIEW_META`, `MEDICAL_SCHOOL_META`, `ELEVEN_PLUS_META` dicts in `generate.py`, or passed as the `meta_desc` argument to `page_template()`. Edit those dicts directly — no CSV needed.

### Where descriptions are written in HTML

`base_html()` in `templates.py` writes the same string to all three tags. When editing manually, update all three:
```html
<meta name="description" content="..." />
<meta property="og:description" content="..." />
<meta name="twitter:description" content="..." />
```

### Meta tag syntax — must use self-closing `/>`

```html
<!-- BROKEN — causes stylesheet to not load -->
<meta name="description" content="Some text">

<!-- CORRECT -->
<meta name="description" content="Some text" />
```

A missing `/>` causes the HTML5 parser to swallow the next tag as an attribute. Symptom: page renders unstyled with giant logo image. Diagnosis:
```js
document.querySelectorAll('link[rel="stylesheet"]').length  // returns 0 if broken
```

Bulk check: `grep -rn '<meta name="description" content="[^"]*">' seo-generator/output/` — any match (without `/>`) is broken.

### Bulk audit for generic descriptions

```bash
grep -r 'name="description"' seo-generator/output/ | grep 'Expert advice from Leading Tuition'
```
Any match should be updated manually or via CSV override.

---

## 5. Navbar Sync

### Two separate navbar variants

| Variant | Lives in | Covers |
|---|---|---|
| Canonical | `templates.py` | All generated pages (`blog/`, `oxbridge-interviews/`, `locations/`, etc.) |
| Flat page copies | Each `seo-generator/output/*.html` manually | `index.html`, `about.html`, `contact.html`, `consultation.html`, `faqs.html`, `tutors.html`, `locations.html`, `subjects.html`, `services.html`, `blog.html` |

### Current canonical navbar (March 2026)

- 4-column Services mega-menu: Subjects, Levels, Specialist & Admissions, Admissions Tests
- Blog dropdown: 8 featured posts + "View all posts →" link
- Includes `/oxbridge-interviews/` under Specialist & Admissions

### Sync procedure

After any navbar change in `templates.py`:

**Step 1** — propagate to generated pages:
```bash
cd seo-generator && python generate.py --navbar
```
Or use `sync_navbar.py` which also syncs the mobile toggle `<script>` block:
```bash
python seo-generator/sync_navbar.py
```
Use `sync_navbar.py` whenever the mobile JS block changes — `--navbar` only syncs the `<nav>` element.

**Step 2** — sync flat standard pages (run this Python snippet from repo root):
```python
import re, os

with open('seo-generator/output/blog/oxbridge-interview-questions-100-real-examples-for-every-major-subject.html') as f:
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

**Step 3** — verify (must use Python regex, not `md5sum` or `sed -n` — those stop at the first `</nav>`):
```python
import re
with open('seo-generator/output/blog/oxbridge-interview-questions-100-real-examples-for-every-major-subject.html') as f:
    ref = re.search(r'<nav class="navbar">.*?</nav>', f.read(), re.DOTALL).group(0)
with open('seo-generator/output/index.html') as f:
    idx = re.search(r'<nav class="navbar">.*?</nav>', f.read(), re.DOTALL).group(0)
print("Match:", ref == idx)  # Must be True
```

### Mobile flyout toggle (March 2026 pattern)

Each `.nav-flyout` div uses a separate `<button>` for expand/collapse, distinct from the `<a>` link:
```html
<div class="nav-flyout">
  <a href="/gcse/">GCSE</a>
  <button class="nav-flyout-toggle" aria-label="Show sub-pages" aria-expanded="false">▾</button>
  <div class="nav-flyout-menu">...</div>
</div>
```
Button is `display:none` on desktop; visible in `@media (max-width: 900px)`. JS toggles `.open` on the parent `.nav-flyout` div.

---

## 6. Breadcrumb Schema (BreadcrumbList JSON-LD)

### The double-prefix bug (fixed March 2026)

**Root cause:** `page_template()` was called with `slug` already set to the full prefixed path (e.g. `"oxbridge-interviews/biology-interview/"`). Internally it also called `breadcrumb_schema(page_type, slug, ...)`, which ran `page_url_path()` and prepended the prefix again — producing doubled paths like `/oxbridge-interviews/oxbridge-interviews/biology-interview/`.

Additionally, `generate_oxbridge_interview_pages()` and `generate_medical_school_pages()` each passed a correct breadcrumb in `schema_extra`, so every page ended up with TWO `BreadcrumbList` schemas.

**Fix applied in `page_template()`:** Skip generating an internal breadcrumb when `schema_extra` already contains `"BreadcrumbList"`. If generating internally, strip the page-type prefix from `slug` before passing to `breadcrumb_schema()`.

### Rule going forward

- If calling `page_template()` with a `schema_extra` that already contains a `BreadcrumbList`, do not pass a prefixed slug to `breadcrumb_schema()` separately — the template skips it automatically.
- If `schema_extra` has no `BreadcrumbList`, pass the bare slug (without page-type prefix) to `breadcrumb_schema()`. The function applies the prefix itself via `page_url_path()`.

### Verify no doubled paths exist

```bash
grep -r 'oxbridge-interviews/oxbridge-interviews' seo-generator/output/
grep -r 'medical-schools/medical-schools' seo-generator/output/
```
Both must return zero matches.

---

## 7. JSON-LD Schema — aggregateRating Rules

**Rule:** `aggregateRating` may only appear on `EducationalOrganization` or `Organization` schemas (homepage-level only). Never on `@type: "Service"` schemas.

GSC flags this as "Invalid object type for field '<parent_node>'" under Enhancements → Review snippets.

**Bulk fix pattern:**
```python
import re, json
from pathlib import Path

def fix_service_schema(html):
    modified = False
    def replace_jsonld(m):
        nonlocal modified
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return m.group(0)
        if isinstance(data, dict) and data.get('@type') == 'Service' and 'aggregateRating' in data:
            del data['aggregateRating']
            modified = True
            return f'<script type="application/ld+json">\n{json.dumps(data, indent=2)}\n</script>'
        return m.group(0)
    pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL | re.IGNORECASE)
    return pattern.sub(replace_jsonld, html), modified
```

After fixing: push to dev → GSC → Enhancements → Review snippets → "Validate Fix".

---

## 8. Git & Deployment

| Branch | Deploys to | Use for |
|---|---|---|
| `main` | `www.leadingtuition.co.uk` | Production only — merge from dev after verification |
| `dev` | New preview URL per push | All development and testing |

**Preview URL:** Each push to `dev` creates a NEW preview URL. Old URLs stop working. Always get the current URL from the Cloudflare dashboard (project: `leading-tuition-seo`).

**The human commits and pushes. Agents prepare files only.**

---

## 9. Adding New Pages — Workflow

1. Add slug/title/metadata to the relevant CSV in `seo-generator/`
2. Add a custom prompt branch in `blog_prompt()` or equivalent in `generate.py`
3. Add the slug to `BLOG_RELATED_RESOURCES` dict for interlinking
4. `cd seo-generator && python generate.py --[flag] --new-only`
5. `python generate.py --navbar` (or `python sync_navbar.py` if JS changed)
6. `python generate.py --sitemap`
7. Verify file exists in `seo-generator/output/` at the expected path
8. Verify canonical tag, meta description, and breadcrumb JSON-LD in the generated file
9. Human commits and pushes to `dev`; verify on preview URL; human merges to `main`

---

## 10. Sitemap

- **File:** `seo-generator/output/sitemap.xml` → served at `/sitemap.xml`
- **Generate:** `python generate.py --sitemap` (scans all HTML in `seo-generator/output/`)
- **Submit to GSC:** Production URL only (`www.leadingtuition.co.uk/sitemap.xml`), never the dev preview URL

**Priority scheme:**

| Priority | Pages |
|---|---|
| 1.0 | Homepage |
| 0.9 | Hub pages (`/a-level/`, `/gcse/`, `/admissions-tests/`, etc.) |
| 0.8 | Individual sub-pages |
| 0.7 | Locations, services, levels |
| 0.6 | Blog posts, static pages |

Hub pages must exist as real HTML files for `--sitemap` to include them. If a hub page appears in the nav but is missing from the sitemap, add it manually or create the file.

---

## 11. SEO Issues & Root Causes

### Resolved issues (March 2026)

| GSC issue | Root cause | Fix |
|---|---|---|
| Duplicate without user-selected canonical | Stale pages with identical or wrong canonical tags | Deleted stale files (`gcse-maths-tutor.html`, `medicine-prep/` etc.) from `dev` |
| Not found 404 | Canonicals pointing to non-existent URLs | Same — deleted source files |
| Breadcrumb errors | Doubled path prefix in JSON-LD (`/oxbridge-interviews/oxbridge-interviews/`) | Fixed `page_template()` + bulk-replaced in 56 HTML files |
| Generic meta descriptions | `generate_blog_pages()` used hardcoded filler formula | Added `META_DESC:` protocol + `parse_meta_desc()` |
| aggregateRating on Service schemas | JSON-LD included `aggregateRating` on `@type: "Service"` | Removed from affected pages |

### SEO structural duplication

All four generated page families (locations, medical schools, admissions tests, Oxbridge interviews) use a fixed H2 structure per family, which Google treats as near-duplicates.

**Fix pattern:** Replace fixed H2 list in each prompt function with a `VARIANTS` list of 3–5 genuinely different structures. Assign variants deterministically:
```python
import hashlib
variant = int(hashlib.md5(slug.encode()).hexdigest(), 16) % num_variants
```
Each variant must differ in H2 order, section emphasis, opening angle, and FAQ topics — not just wording.

After modifying a prompt: delete all existing pages in that family and regenerate without `--new-only`.

**Fix priority order:**
1. Location pages (34 pages, highest risk)
2. Medical school pages (38 pages)
3. Admissions test pages (13 pages)
4. Oxbridge interview pages (18 pages, lowest risk — subject questions vary)

### GSC "Crawled - currently not indexed" / "Discovered - currently not indexed"

"Discovered" is normal for new pages — resolves over time. "Crawled but not indexed" on existing pages usually signals thin or near-duplicate content. Improve content or add internal links.

### robots.txt

Currently `Allow: /` with sitemap pointer. Do not add `Disallow: /seo-generator/` — that path doesn't exist publicly.

---

## 12. Location Pages — Related Callouts

All location pages must have a `<!-- RELATED-CALLOUT -->` section immediately before `</footer>`. Check for this comment before adding a callout to avoid duplicates.

**Geographic targeting:**

| Location type | Link targets |
|---|---|
| London-adjacent (Ealing, Twickenham, Watford) | Tiffin, QE Barnet, St Olave's |
| Bucks-adjacent (Milton Keynes, Northampton, Oxford) | Bucks grammar schools |
| Kent-adjacent (Brighton, Guildford, Portsmouth) | Tonbridge Grammar, Weald of Kent |
| Cambridge | Oxbridge/medicine pages |
| Oxford | Bucks grammars + Oxbridge |
| Generic (Birmingham, Bristol, Leeds, etc.) | Nearby admissions test or interview prep pages |

Use existing location pages in `seo-generator/output/locations/` as reference.

---

## 13. Resource Pages — Papers UI (11+, 13+, Pre-11+)

### Pages and files

| Public URL | File |
|---|---|
| `/resources/pre-11-plus` | `seo-generator/output/resources/pre-11-plus.html` |
| `/resources/11-plus` | `seo-generator/output/resources/11-plus.html` |
| `/resources/13-plus` | `seo-generator/output/resources/13-plus.html` |

These are **manually maintained**. Do NOT regenerate with `generate.py`. Edit directly or re-run `build_resource_pages.py` (repo root) with an updated CSV.

### PDF file structure

```
seo-generator/output/public/papers/
  11-plus/{institution-slug}/{clean-filename}.pdf
  pre-11-plus/{institution-slug}/...
  13-plus/{institution-slug}/...
```

- Institution slug: lowercase, hyphens, no special chars (e.g. `dulwich-college`)
- Filename: strip leading numeric prefix from original (e.g. `0082__name.pdf` → `name.pdf`)
- Mark-scheme files get `-mark-scheme` appended if not already in the name

### Adding new papers

1. Add rows to `resources_page_mapping_with_local_paths_filtered.csv`
2. Run `copy_pdfs.py` (repo root, Windows) to copy PDFs into `seo-generator/output/public/papers/`
3. Re-run `build_resource_pages.py`
4. Commit `seo-generator/output/resources/*.html` + `seo-generator/output/public/papers/`

### JS data structure per paper

```js
{ i: "Institution Name", s: "Subject", y: "2024", t: "Display Title", q: "/public/papers/...", a: "/public/papers/..." }
```
`a` = `""` if no answer file exists.

### UI rules

- No "has answers" filter — all papers show regardless
- No answers → show "Coming soon" (not "—" or blank)
- Accordion uses `data-acc-id` + event delegation (NOT inline `onclick` — Python f-strings collapse `\'` to `'`, breaking JS)
- Year dropdown scopes to selected institution only; institution change event must call both `populateFilters()` and `render()`
- Tabs filter by subject; institution + year dropdowns update accordingly

---

## 14. Bundle Payments — 11+/13+/Pre-11+ (Google Drive Delivery)

### Pricing

| Page | `bundle_key` | Price | Stripe `unitAmount` |
|---|---|---|---|
| 11+ | `bundle/11-plus` | £70 | `7000` |
| 13+ | `bundle/13-plus` | £50 | `5000` |
| Pre-11+ | `bundle/pre-11-plus` | £50 | `5000` |

### Payment flow

1. 🔒 Answers button → modal opens
2. "Buy Full Access" POSTs to `/api/create-checkout` with `{bundle_key, unitAmount}`
3. Stripe Checkout → `/purchase-confirmed?session_id=...`
4. Page calls `/api/get-downloads?session_id=...`
5. `get-downloads.js` → `{isBundle: true, downloadUrl: <Drive URL>}`
6. Teal "Access All Papers & Answers →" button opens Drive folder in new tab

### Environment variables (Cloudflare Pages dashboard — never hardcoded)

| Env var | Value |
|---|---|
| `DRIVE_11_PLUS` | `https://drive.google.com/drive/folders/1e7HyovSXzAQ_qJ0EMSxQGEISZiiVJvGx?usp=sharing` |
| `DRIVE_13_PLUS` | `https://drive.google.com/drive/folders/1TytGdhaJ_NYg4r3pYE9IC7AbhbDs7tB2?usp=sharing` |
| `DRIVE_PRE_11_PLUS` | `https://drive.google.com/drive/folders/1h8n9p-NBgKmcO0Vs1s418p8dy1Iuo2n9?usp=sharing` |

### Key files

| File | Role |
|---|---|
| `functions/api/create-checkout.js` | `ALLOWED_AMOUNTS = [300, 5000, 7000, 15000]` — must include all bundle prices |
| `functions/api/get-downloads.js` | `BUNDLE_ENV_KEYS` map: `bundle_key → env var name → Drive URL` |
| `seo-generator/output/purchase-confirmed.html` | Dual-mode: bundle → teal button (new tab, no `download` attr); individual → PDF download |
| `seo-generator/output/resources/11-plus.html` | Full access banner + 🔒 buttons + buy modal |

### purchase-confirmed.html — dual-mode rendering

| `isBundle` | UI shown | Button |
|---|---|---|
| `false` | "Your download is ready" | "Download PDF" with `download` attr |
| `true` | "Your access link is ready" | Teal "Access All Papers & Answers →", opens new tab, no `download` attr |

Both modes show "Save your access link" notice.

### Modal JS — all three functions required

```js
function showBuyModal() { ... }
function closeBuyModal() { ... }
function buyAccess() { ... }
```
Button wiring must use `btns.forEach`:
```js
var btns = [document.getElementById('buyAccessBtn'), document.getElementById('modalBuyBtn')];
btns.forEach(function(btn) { if (btn) btn.addEventListener('click', buyAccess); });
```
If `showBuyModal` is missing, 🔒 buttons silently do nothing. Verify: `typeof showBuyModal` in browser console must return `'function'`.

---

## 15. Cloudflare Functions — API Endpoints

All API logic lives in `functions/api/`. These run as Cloudflare Workers.

| File | Endpoint | Purpose |
|---|---|---|
| `create-checkout.js` | `POST /api/create-checkout` | Creates Stripe Checkout session |
| `stripe-webhook.js` | `POST /api/stripe-webhook` | Handles Stripe events, writes to KV |
| `get-downloads.js` | `GET /api/get-downloads?session_id=` | Returns download links post-purchase |
| `download.js` | `GET /api/download?s=&k=` | Signed R2 download proxy |
| `oxbridge-sample.js` | `GET /api/oxbridge-sample?file=` | Serves static Oxbridge sample PDFs |

### All required Cloudflare environment variables

```
STRIPE_SECRET_KEY          Stripe live secret key
STRIPE_WEBHOOK_SECRET      Stripe webhook signing secret
R2_ACCESS_KEY_ID           R2 API token (not root key)
R2_SECRET_ACCESS_KEY       R2 API token secret
R2_BUCKET_NAME             e.g. "leading-tuition-answers"
R2_ENDPOINT                e.g. "https://<account_id>.r2.cloudflarestorage.com"
KV_STORE                   KV namespace binding (set in Pages bindings)
DRIVE_11_PLUS              Google Drive folder URL for 11+ bundle
DRIVE_13_PLUS              Google Drive folder URL for 13+ bundle
DRIVE_PRE_11_PLUS          Google Drive folder URL for pre-11+ bundle
```

### KV store — purchase TTL

`stripe-webhook.js` writes purchase record to KV with **48-hour TTL** using `session_id` as key. After 48h the key expires and the download link stops working. This is intentional.

### R2 bucket — key structure

```
{category-slug}/{institution-slug}/{question-base}-answers.pdf
```
Example: `11-plus/dulwich-college/dulwich_maths_2023_paper_a-answers.pdf`

Bundle keys: `bundle/11-plus`, `bundle/13-plus`, `bundle/pre-11-plus` (distinct from per-paper keys).

### Uploading to R2 (bypassing 100-file dashboard limit)

```python
import boto3, os
s3 = boto3.client(
    's3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
)
s3.upload_file(local_path, bucket_name, r2_key)
```
Credentials from `.env` via `python-dotenv`. Never hardcode.

---

## 16. Oxbridge Interview Questions — Per-Paper R2 Download

`/resources/oxbridge-interview-questions` uses individual R2 downloads (not bundles). Each paper has its own signed URL from `/api/download`.

**Static sample PDFs:** `seo-generator/output/public/oxbridge-samples/{subject}-sample.pdf` → served at `/public/oxbridge-samples/...`. Must be inside `seo-generator/output/` — repo root `public/` is not served.

**R2 key structure:**
```
{subject-slug}/{institution-slug}/{paper-base}-answers.pdf
```
Each paper has its own key; institution slug groups papers from one institution.

---

## 17. Bing IndexNow

**Verification file:** `seo-generator/output/8953b81f83ca47ef82f7680b35e64d91.txt`

**Submission script:** `submit_indexnow.py` (repo root) — batches all 208+ public HTML pages and POSTs to `api.indexnow.org`.

```bash
python submit_indexnow.py
```

Run after any significant content deployment to `main`. Never run against the dev preview URL.

If you get HTTP 403 `SiteVerificationNotCompleted`: the site was imported from GSC and Bing's backend may take up to 24h to sync. Wait and retry.

---

## 18. www Redirect — GoDaddy Domain Forwarding

### Problem

Both `leadingtuition.co.uk` (non-www) and `www.leadingtuition.co.uk` appear in Google's index, splitting link equity. Canonical version is `www.leadingtuition.co.uk`.

### Why Cloudflare redirect rules cannot be used

The domain is managed by **GoDaddy DNS** — nameservers are NOT pointed to Cloudflare. Cloudflare only handles hosting via a CNAME on `www`. Cloudflare redirect rules cannot intercept bare-domain traffic.

### Solution: GoDaddy domain forwarding (301)

1. Log in to GoDaddy → **My Products** → **Domains**
2. Click **DNS** next to `leadingtuition.co.uk`
3. Scroll to **Forwarding** → click **Add** next to "Domain"
4. Set:
   - **Forward to:** `https://www.leadingtuition.co.uk`
   - **Redirect type:** Permanent (301)
   - **Settings:** Forward only *(not "Forward with masking" — masking breaks the URL)*
5. Save. Propagates within minutes to a few hours.

### Coverage and limitations

| Scenario | Outcome |
|---|---|
| `http://leadingtuition.co.uk` | ✅ 301 → `https://www.leadingtuition.co.uk` |
| `https://leadingtuition.co.uk` | ✅ 301 → `https://www.leadingtuition.co.uk` |
| `leadingtuition.co.uk/blog/some-post` | ⚠️ Redirects to root only (`/blog/some-post` not preserved — GoDaddy limitation) |
| Subdomains | ❌ Not affected |

Path-preserving redirects would require moving nameservers to Cloudflare.

### After setup

- Wait ~24h for Google to process 301s
- GSC "Change of address" tool is not needed here (both versions already in GSC — 301s are sufficient)
- Monitor GSC → Coverage over following weeks; non-www URLs should shift from "Indexed" to "Redirected"

---

## 19. .gitignore — UTF-8 (converted March 2026)

The `.gitignore` was originally UTF-16 with BOM (created on Windows) but has been **converted to UTF-8** because git cannot reliably read UTF-16 encoded gitignore files — null bytes between characters meant entries like `.env` were never matched, leaving sensitive files exposed.

**Current state:** `.gitignore` is plain UTF-8. Edit it normally:

```bash
echo 'new-entry/' >> .gitignore
```

Do NOT re-encode it as UTF-16. If a future collaborator opens it on Windows and saves as UTF-16, convert it back:

```python
raw = open('.gitignore', 'rb').read()
text = raw.decode('utf-16').replace('\r\n', '\n')
open('.gitignore', 'w', encoding='utf-8').write(text)
```

**Verify an entry is actually gitignored:**
```bash
git check-ignore -v .env   # must print a match line; exit 0
```
If it exits 1, the entry is not being matched — check encoding.

---

## 20. Anthropic API Key — .env Setup

`generate.py` loads the API key from a `.env` file at the **repo root** (one level above `seo-generator/`). The file is gitignored (`.gitignore` line 3).

**File location:** `{repo_root}/.env`

**Format:**
```
ANTHROPIC_API_KEY=sk-ant-...
```

**How it's loaded** (top of `generate.py`):
```python
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
```

**Rules:**
- Never hardcode the API key in any Python file
- Never commit `.env` — verify with `git check-ignore -v .env` (must match)
- If `generate.py` raises `AuthenticationError`, the key is missing or invalid — paste it into `.env`
- `python-dotenv` must be installed: `pip install python-dotenv --break-system-packages`

---

## 21. blog_topics.csv — Quoting Rules

`blog_topics.csv` has three columns: `title`, `keyword`, `meta_desc`. **All three can contain commas.** Always write it using Python's `csv.writer` with `QUOTE_MINIMAL` (or `QUOTE_ALL`) so that fields with commas are properly quoted. Never write it as a raw string with manual comma-separation.

**Correct pattern:**
```python
import csv
rows = [("Title with, comma", "keyword", "Description with, commas here.")]
with open('seo-generator/blog_topics.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['title', 'keyword', 'meta_desc'])
    for title, kw, desc in rows:
        writer.writerow([title, kw, desc])
```

**Verify after editing:**
```python
import csv
with open('seo-generator/blog_topics.csv', newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
# Check that meta_desc values are full-length (>100 chars for typical descriptions)
for r in rows[-5:]:
    print(len(r['meta_desc']), r['title'][:50])
```

If any `meta_desc` is suspiciously short (under 80 chars), the row has unquoted commas and will produce truncated descriptions at generation time.

**Meta description length standard:** 145–158 chars. Values over 158 are truncated to 160 at generation time, cutting off mid-sentence. Always check lengths before committing. 