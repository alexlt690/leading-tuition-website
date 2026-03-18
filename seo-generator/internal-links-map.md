# Internal Links Map — Leading Tuition SEO

## Purpose
This document records the 10 minimum required internal links that create topic clusters across the site. All links use the current hierarchical URL structure (`/services/subjects/`, `/services/levels/`, `/services/specialist-admissions/`, `/blog/`, `/locations/`).

---

## The 10 Priority Internal Links

### 1. UCAT page → MMI page and Medicine Prep Hub
- **From:** `/services/specialist-admissions/ucat-tutor`
- **To:** `/services/specialist-admissions/mmi-interview-coaching` — anchor: "medical school MMI interview coaching"
- **To:** `/services/specialist-admissions/medicine-prep-hub` — anchor: "Medicine Preparation hub"
- **Status:** ✅ Both links present in output file (body text)

### 2. MMI page → UCAT page and Medicine Prep Hub
- **From:** `/services/specialist-admissions/mmi-interview-coaching`
- **To:** `/services/specialist-admissions/ucat-tutor` — anchor: "UCAT preparation"
- **To:** `/services/specialist-admissions/medicine-prep-hub` — (add if not present)
- **Status:** ✅ UCAT link present. Medicine Prep Hub link — check/add on next regeneration.

### 3. Oxbridge page → Medicine Prep Hub and University Admissions page
- **From:** `/services/specialist-admissions/oxbridge-admissions-preparation`
- **To:** `/services/specialist-admissions/university-personal-statement` — anchor: "UCAS personal statement support"
- **To:** `/services/specialist-admissions/medicine-prep-hub` — (add on next regeneration)
- **Status:** ✅ Personal statement link present. Medicine Prep Hub — add on next regeneration.

### 4. Medicine Prep Hub → UCAT, MMI, Oxbridge, University pages
- **From:** `/services/specialist-admissions/medicine-prep-hub`
- **To:** `/services/specialist-admissions/ucat-tutor`
- **To:** `/services/specialist-admissions/mmi-interview-coaching`
- **To:** `/services/specialist-admissions/oxbridge-admissions-preparation`
- **To:** `/services/specialist-admissions/university-personal-statement`
- **Status:** ⬜ Verify all 4 outbound links present in output file.

### 5. Each location page → GCSE subject page and A-Level page
- **From:** `/locations/{city}` (all 14 cities)
- **To:** `/services/levels/gcse-tuition` — anchor: "GCSE tuition"
- **To:** `/services/levels/a-level-tuition` — anchor: "A-Level tuition"
- **Status:** ⬜ Check on next location page audit. Add to location_prompt in generate.py if missing.

### 6. GCSE level page → all 15 subject pages (Browse by Subject)
- **From:** `/services/levels/gcse-tuition`
- **To:** All 15 `/services/subjects/{subject}-tutor` pages
- **Status:** ✅ Browse by Subject grid present in output file and generate.py prompt.

### 7. A-Level level page → all 15 subject pages (Browse by Subject)
- **From:** `/services/levels/a-level-tuition`
- **To:** All 15 `/services/subjects/{subject}-tutor` pages
- **Status:** ✅ Browse by Subject grid present in output file and generate.py prompt.

### 8. Each blog post → 2 relevant service pages (Related Resources section)
- **From:** All 10 blog posts
- **To:** Relevant specialist or level pages (see BLOG_RELATED_RESOURCES in generate.py)
- **Status:** ✅ All 10 blogs now have Related Resources sections in output files. All 10 entries present in BLOG_RELATED_RESOURCES dict.

### 9. Subject pages → relevant level pages (contextual)
- **From:** `/services/subjects/{subject}-tutor`
- **To:** `/services/levels/gcse-tuition` — anchor referencing GCSE [Subject]
- **To:** `/services/levels/a-level-tuition` — anchor referencing A-Level [Subject]
- **Status:** ⬜ Add to subject_prompt in generate.py. Currently subject pages do not consistently link back to level pages.

### 10. Homepage → top 4 specialist pages (hub links)
- **From:** `/` (homepage)
- **To:** `/services/specialist-admissions/ucat-tutor`
- **To:** `/services/specialist-admissions/mmi-interview-coaching`
- **To:** `/services/specialist-admissions/oxbridge-admissions-preparation`
- **To:** `/services/specialist-admissions/medicine-prep-hub`
- **Status:** ⬜ Verify in homepage output. If missing, add to generate_static_pages() or homepage source file.

---

## Status Key
- ✅ Done and verified in output files
- ⬜ Not yet implemented — add on next regeneration pass
- ❌ Implemented but incorrect (path error or wrong anchor)

---

## Path Reference (correct hierarchical URLs)

| Page type | URL pattern |
|---|---|
| Subject pages | `/services/subjects/{slug}-tutor` |
| Level pages | `/services/levels/{slug}-tuition` |
| Specialist pages | `/services/specialist-admissions/{slug}` |
| Blog posts | `/blog/{slug}` |
| Location pages | `/locations/{city}` |
| Static pages | `/`, `/about`, `/contact`, `/consultation`, `/faqs` |

---

## generate.py Reference
- `BLOG_RELATED_RESOURCES` dict — controls Related Resources links for all 10 blog posts
- `specialist_prompt()` — lines 100–290, contains contextual link instructions for UCAT, MMI, Oxbridge
- `subject_prompt()` — add outbound links to level pages here (item 9 above)
- `location_prompt()` — add outbound links to level pages here (item 5 above)
