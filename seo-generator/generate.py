import csv
import os
import re
import json
import argparse
import anthropic
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the repo root (one level up from seo-generator/)
load_dotenv(Path(__file__).parent.parent / ".env")
from templates import (page_template, location_page_template, blog_page_template,
                       service_page_template, breadcrumb_schema)


def parse_meta_desc(response_text):
    """Extract META_DESC: line from Claude response. Returns the description string or None."""
    match = re.search(r'^META_DESC:(.+)$', response_text, re.MULTILINE)
    if match:
        return match.group(1).strip()[:160]
    return None


def parse_faq_schema(response_text):
    """Extract FAQ_JSON block from Claude response. Returns (clean_content, faq_schema_html)."""
    # Strip META_DESC line first so it doesn't leak into page content
    response_text = re.sub(r'^META_DESC:.+$\n?', '', response_text, flags=re.MULTILINE)
    match = re.search(r'FAQ_JSON:(\[.*?\])', response_text, re.DOTALL)
    if not match:
        return response_text, ""
    content = response_text[:match.start()].strip()
    try:
        faqs = json.loads(match.group(1))
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": faq["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}}
                for faq in faqs
            ]
        }
        return content, f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    except (json.JSONDecodeError, KeyError):
        return content, ""


def build_blogposting_schema(title, meta_desc, slug):
    """Build BlogPosting JSON-LD schema block."""
    base_url = "https://www.leadingtuition.co.uk"
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": meta_desc,
        "url": f"{base_url}/blog/{slug}",
        "datePublished": date.today().isoformat(),
        "author": {"@type": "Organization", "name": "Leading Tuition Team"},
        "publisher": {"@type": "Organization", "name": "Leading Tuition", "url": base_url}
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Script directory (seo-generator/) and output directory
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"  # Cloudflare Pages serves from seo-generator/output/


def load_csv(filename):
    with open(SCRIPT_DIR / filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def ask_claude(prompt: str, max_tokens: int = 3200) -> str:
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                temperature=0.35,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            if "overloaded" in str(e).lower() or "529" in str(e):
                wait = 30 * (attempt + 1)
                print(f"  API overloaded, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("API still overloaded after maximum retries — try again later")


def specialist_prompt(title: str, keyword: str, slug: str) -> str:
    master_context = """
You are writing a specialist SEO page for Leading Tuition, a UK tutoring company.

Audience:
- The reader is usually a UK parent of a student aged roughly 10 to 18.
- They are anxious, short on time, and want trustworthy, specific guidance.

Global rules:
- Write for a UK parent, not an SEO algorithm.
- Use a warm, expert, reassuring tone.
- Acknowledge the parent's real situation in the opening paragraph.
- Write genuinely useful content, not generic filler.
- Include at least 3 specific, verifiable facts where appropriate.
- Never mention BMAT as a current admissions test.
- Never use markdown.
- Output plain HTML only.
- Use only these tags where helpful: <p>, <h2>, <ul>, <li>, <strong>.
- Do not include <html>, <head>, or <body>.
- Do not include CTA buttons or generic footer text because the template already handles CTAs.
- End naturally, without sounding salesy.
- Include one FAQ section with the heading <h2>Frequently Asked Questions</h2>.
- Under the FAQ section, include exactly 4 FAQ questions written as <p><strong>Question</strong></p> followed by a normal <p> answer.
"""

    if slug == "ucat-tutor":
        return f"""
{master_context}

Before writing, think through:
1. What does a UK parent know and not know about UCAT?
2. What misconceptions about UCAT preparation waste the most time?
3. What changed recently? BMAT was abolished in 2023, and Oxford, Cambridge, and Imperial now use UCAT.
4. What information would make this page genuinely better than generic tutoring pages?

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge the pressure families feel around medical applications
- Include these exact <h2> sections:
  1. What Is the UCAT?
  2. What UCAT Score Do You Need?
  3. The 5 UCAT Subtests
  4. Why UCAT Preparation Is Different
  5. How Leading Tuition Supports UCAT Students
  6. Your 10-Week UCAT Preparation Timeline
  7. Frequently Asked Questions
- Must explicitly include:
  - The 5 UCAT subtests: Verbal Reasoning, Decision Making, Quantitative Reasoning, Abstract Reasoning, Situational Judgement
  - 2024 average score around 615 per subtest (combined ~2,460)
  - Competitive scores around 670 to 700+ per subtest for top medical schools
  - Oxford, Cambridge, and Imperial now use UCAT
  - BMAT was abolished in 2023
  - Students get one attempt per application cycle
  - UCAT is different from A-Level revision because it tests cognitive speed and decision-making, not just learned content
  - The 10-week timeline section must be a structured <ul> list with specific weekly goals (not prose), with entries for Weeks 1-2, Weeks 3-4, Weeks 5-6, Weeks 7-8, and Weeks 9-10
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs about UCAT timing, score expectations, retakes, and tutoring support
- Include a natural contextual in-content link in the body of the page to the MMI coaching page at /services/specialist-admissions/mmi-interview-coaching — use anchor text such as 'medical school MMI interview coaching'

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    if slug == "mmi-interview-coaching":
        return f"""
{master_context}

Before writing, think through:
1. Most parents do not know what an MMI actually is.
2. What station types and preparation methods make the biggest difference?
3. What timing pressures matter most after UCAT results?

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge how intimidating medical interviews can feel
- Include these exact <h2> sections:
  1. What Is the MMI Format?
  2. What Medical Schools Look for at MMI
  3. UK Medical Schools That Use the MMI Format
  4. The Most Common MMI Station Types — with Example Prompts
  5. How Leading Tuition MMI Coaching Works
  6. Your 6-Week MMI Preparation Schedule
  7. Frequently Asked Questions
- Must explicitly include:
  - Typical MMI format: 5 to 10 stations
  - Typical station length: 5 to 8 minutes
  - Different assessors across stations
  - The difference between MMI and traditional panel interviews
  - Section 3 must be a <ul> list naming at least 8 UK medical schools that use MMI (including Birmingham, Bristol, King's College London, Leicester, Brighton and Sussex, Hull York, Exeter, Nottingham, Barts, St George's)
  - Section 4 must list each station type (ethical scenario, role play, data interpretation, written, presentation, empathy) with a one-sentence example prompt for each
  - Section 6 must be a structured <ul> week-by-week list (not prose) covering Weeks 1 through 6 with specific activities for each week
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs including one about which schools use MMI
- Include a natural contextual in-content link in the body of the page to the UCAT preparation page at /services/specialist-admissions/ucat-tutor — use anchor text such as 'UCAT preparation'

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    if slug == "oxbridge-admissions-preparation":
        return f"""
{master_context}

Before writing, think through:
1. How is Oxbridge admissions prep different from ordinary A-Level tutoring?
2. What misconceptions do families often have about Oxbridge interviews?
3. Which timeline facts matter most?

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge how high-pressure and time-sensitive Oxbridge applications feel
- Include these exact <h2> sections:
  1. What Makes Oxbridge Applications Different
  2. The Application Timeline
  3. Oxford and Cambridge Interviews
  4. Subject-Specific Admissions Tests
  5. The Oxbridge Personal Statement
  6. How Leading Tuition Supports Oxbridge Applicants
  7. Frequently Asked Questions
- Must explicitly include:
  - UCAS deadline for Oxbridge: 15 October
  - Interviews usually take place in December
  - Oxford and Cambridge interview styles differ
  - Subject-specific tests such as MAT, LNAT, TSA, HAT, ELAT
  - Oxbridge interviews focus on problem-solving and academic thinking, not memorised answers
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs
- Include a natural contextual in-content link in the body of the page to the University Admissions page at /services/specialist-admissions/university-personal-statement — use anchor text such as 'UCAS personal statement support'

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    if slug == "university-personal-statement":
        return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge that personal statements often feel vague and stressful
- Include these exact <h2> sections:
  1. What Universities Actually Want
  2. What Makes a Strong Personal Statement
  3. Common Mistakes Students Make
  4. How Leading Tuition Supports Personal Statement Writing
  5. When Students Should Start
  6. Frequently Asked Questions
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs
"""

    if slug == "medicine-prep-hub":
        return f"""
{master_context}

Now write a detailed specialist hub page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge how overwhelming medicine applications feel for families
- Include these exact <h2> sections:
  1. What Medicine Applicants Need to Prepare For
  2. UCAT Preparation
  3. MMI Interview Preparation
  4. A-Level Subject Support for Medicine
  5. Building a Strong Application Strategy
  6. Frequently Asked Questions
- Mention that medicine applicants often need support across UCAT, interviews, and A-Level sciences
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs
"""

    if slug == "oxbridge-subject-preparation":
        return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge how different Oxbridge subject prep feels from ordinary school revision
- Include these exact <h2> sections:
  1. Why Subject-Specific Oxbridge Preparation Matters
  2. Interviews and Subject Thinking
  3. Admissions Tests by Subject
  4. Common Mistakes Applicants Make
  5. How Leading Tuition Supports Applicants
  6. Frequently Asked Questions
- Mention that requirements vary by subject and college
- Mention examples such as MAT, LNAT, TSA, HAT, ELAT where relevant
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs
"""

    if slug == "medical-school-interviews":
        return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge the anxiety families feel when their child receives a medical school interview invitation
- Include these exact <h2> sections:
  1. The Two Main UK Medical School Interview Formats
  2. What Medical Schools Are Actually Assessing
  3. MMI vs Panel: Which Format Is Harder to Prepare For?
  4. The Most Common Interview Mistakes and How to Avoid Them
  5. How Leading Tuition Supports Interview Preparation
  6. Frequently Asked Questions
- Must explicitly include:
  - The difference between MMI (Multiple Mini Interview) and traditional panel interviews
  - Examples of which format different UK medical schools use (e.g. MMI at Leeds, Manchester, King's; panel at some others)
  - The key competencies assessed: communication, empathy, ethical reasoning, NHS awareness, motivation for medicine
  - Why mock interviews with structured feedback are more effective than self-study
  - A contextual link to /services/specialist-admissions/mmi-interview-coaching using anchor text 'MMI interview coaching'
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs about medical school interview preparation

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    if slug == "mmi-station-types":
        return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge that most applicants have never encountered an MMI before and find the format bewildering at first
- Include these exact <h2> sections:
  1. What Is an MMI Station?
  2. The Six Most Common MMI Station Types
  3. What Assessors Are Looking for at Each Station Type
  4. Example Prompts by Station Type
  5. How to Prepare for Each Station Type
  6. Frequently Asked Questions
- Must explicitly cover these six station types with a dedicated explanation for each:
  1. Role play / actor stations (communication with a simulated patient or colleague)
  2. Ethical scenario stations (no right answer — process and reasoning matter)
  3. Personal qualities and motivation stations (why medicine, work experience reflection)
  4. NHS and healthcare awareness stations (current issues, NHS structure)
  5. Data interpretation stations (reading a graph or table and explaining findings)
  6. Teamwork or group task stations (less common but used at some schools)
- Include example prompts for at least 3 station types
- Include a contextual link to /services/specialist-admissions/mmi-interview-coaching using anchor text 'MMI interview coaching'
- In the FAQ section, include 4 specific parent-facing FAQs

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    if slug == "mmi-practice-questions":
        return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge that reading about MMI is not the same as practising it, and that many applicants underestimate how much active practice matters
- Include these exact <h2> sections:
  1. How to Use MMI Practice Questions
  2. Ethics and Scenario Questions
  3. Role Play Station Questions
  4. NHS Awareness and Healthcare Questions
  5. Personal Qualities and Motivation Questions
  6. How Leading Tuition Structures MMI Practice
  7. Frequently Asked Questions
- Must explicitly include:
  - At least 3 example ethics/scenario questions with brief guidance on how to approach each
  - At least 2 example role play station prompts
  - At least 2 NHS awareness questions
  - At least 2 personal qualities questions
  - The importance of timing (each MMI station is 5-8 minutes) and structuring an answer within that window
  - A contextual link to /services/specialist-admissions/mmi-interview-coaching using anchor text 'MMI interview coaching'
- Present questions as <p><strong>Q: [question]</strong></p> followed by a brief approach note
- In the FAQ section, include 4 specific parent-facing FAQs

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    if slug == "which-medical-schools-use-mmi":
        return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge that interview format varies significantly between UK medical schools and that many families do not realise this until after submitting their UCAS application
- Include these exact <h2> sections:
  1. Why Interview Format Matters for Preparation
  2. UK Medical Schools That Use the MMI Format
  3. UK Medical Schools That Use Panel or Traditional Interviews
  4. Schools With Hybrid or Changing Formats
  5. How to Tailor Your Preparation to Your Interview Format
  6. Frequently Asked Questions
- Must explicitly name specific UK medical schools in each category — do not use vague language like "many schools". Include at least 6 named schools across the three categories. Use data that was accurate as of 2024/2025.
- Note that formats can change year to year and applicants should verify directly with each school
- Include a contextual link to /services/specialist-admissions/mmi-interview-coaching using anchor text 'MMI interview coaching'
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""

    return f"""
{master_context}

Now write a detailed specialist page in HTML about: {title}

Requirements:
- Length: 1,050 to 1,300 words
- Opening paragraph must acknowledge the parent's situation
- Include at least 5 useful <h2> sections, including Frequently Asked Questions
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs
- Keep the page highly specific and parent-facing
- Include concrete UK context wherever relevant

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""


def subject_prompt(subject: str) -> str:
    chemistry_extra = ""
    if subject.lower() == "chemistry":
        chemistry_extra = """
- You must explicitly mention Required Practicals and explain why students often lose marks on them.
- Include a section on AQA Chemistry Required Practical mark scheme guidance: explain the specific types of questions that appear and common errors.
"""

    maths_extra = ""
    if subject.lower() == "maths" or subject.lower() == "mathematics":
        maths_extra = """
- You must include a dedicated <h2> section titled 'AQA GCSE Maths: Paper Structure, Tiers, and Key Topics'.
- This section must cover:
  - AQA paper structure: Paper 1 (non-calculator), Papers 2 and 3 (calculator) — each 80 marks, 1 hour 30 minutes
  - Foundation tier (grades 1-5, max grade 5) vs Higher tier (grades 4-9) — list what differs
  - Key topics for the non-calculator paper: surds, exact values, algebraic manipulation, estimation, bounds
  - Key topics for calculator papers: trigonometry, Pythagoras in 3D, volume/surface area, quadratic formula, proportionality graphs, cumulative frequency
  - Importance of showing working for method marks
"""

    return f"""
You are writing a UK tutoring subject page for Leading Tuition.

Audience:
- The primary reader is a UK parent considering tutoring support for their child.

Rules:
- Write for a UK parent, not an SEO algorithm.
- Use a warm, clear, reassuring tone.
- Output plain HTML only.
- Do not use markdown.
- Use only these tags where helpful: <p>, <h2>, <ul>, <li>, <strong>.
- Do not include <html>, <head>, or <body>.
- Do not include CTA buttons because the template already handles them.
- Avoid generic fluff.
- The page must feel different from pages for other subjects.
- Include one FAQ section with the heading <h2>Frequently Asked Questions</h2>.
- Under the FAQ section, include exactly 4 FAQ questions written as <p><strong>Question</strong></p> followed by a normal <p> answer.

Now write a detailed subject page about: {subject} tutoring

Requirements:
- Length: 1,000 to 1,200 words
- Opening paragraph must acknowledge the parent's real concern
- Include at least 5 <h2> sections, one of which must be Frequently Asked Questions
- Mention UK context such as GCSE and A-Level where relevant
- Mention specific exam boards where relevant, such as AQA, Edexcel, OCR, or WJEC
- Explain common student weaknesses or misconceptions in this subject
- Explain how tutoring support helps with marks, confidence, and exam performance
- Include one short bullet list
{chemistry_extra}{maths_extra}
- In the FAQ section, include 4 specific parent-facing FAQs
- Within the first 300 words of body content, include a contextual in-content link to the GCSE Tutoring hub using the HTML: <a href="/gcse/">GCSE tutoring</a> — weave this naturally into a sentence about GCSE support.
- Within the first 300 words of body content, include a contextual in-content link to the A-Level hub using the HTML: <a href="/a-level/">A-Level tuition</a> — weave this naturally into a sentence about A-Level support.
- End naturally
"""




# ── Static page metadata ──────────────────────────────────────────────────────
STATIC_META = {
    "index.html": {
        "html_title": "Leading Tuition | Expert GCSE and A-Level Tutors Online | UK",
        "og_title":   "Expert GCSE and A-Level Tutors Online | UK",
        "meta_desc":  ("Expert one-to-one GCSE and A-Level tutoring from Oxford and "
                       "Cambridge-educated tutors. AQA, Edexcel and OCR. "
                       "Book a free consultation today."),
        "slug": "",
    },
    "about.html": {
        "html_title": "About Leading Tuition | Oxford-Educated Tutors",
        "og_title":   "About Leading Tuition | Oxford-Educated Tutors",
        "meta_desc":  ("Meet the Leading Tuition team — Oxford and Cambridge-educated tutors "
                       "delivering expert GCSE, A-Level and admissions support. "
                       "4.8/5 Trustpilot. Book a free consultation."),
        "slug": "about",
    },
    "contact.html": {
        "html_title": "Contact Us | Leading Tuition",
        "og_title":   "Contact Us | Leading Tuition",
        "meta_desc":  ("Get in touch with Leading Tuition. Book a free consultation with our "
                       "expert tutors. Call +44 207 167 8440 or email "
                       "hello@leadingtuition.co.uk."),
        "slug": "contact",
    },
}

_GA_BLOCK = """  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-D49V0X7BHL"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-D49V0X7BHL');
  </script>"""


def _static_head(html_title, og_title, meta_desc, slug):
    """Build a complete, correct <head>...</head> block for a static page."""
    base_url = "https://www.leadingtuition.co.uk"
    canonical = f"{base_url}/{slug}" if slug else f"{base_url}/"
    og_image  = f"{base_url}/images/og-default.jpg"
    return f"""<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="google-site-verification" content="google81c812594c7ae29d" />
  <title>{html_title}</title>
  <meta name="description" content="{meta_desc}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Leading Tuition" />
  <meta property="og:title" content="{og_title}" />
  <meta property="og:description" content="{meta_desc}" />
  <meta property="og:image" content="{og_image}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:locale" content="en_GB" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{og_title}" />
  <meta name="twitter:description" content="{meta_desc}" />
  <meta name="twitter:image" content="{og_image}" />
  <link rel="stylesheet" href="/style.css" />
  <link rel="icon" type="image/png" href="/images/favicon.png" />
{_GA_BLOCK}
</head>"""


def generate_static_pages():
    """Generate all 6 core pages (homepage, about, contact, plus 3 index pages).
    No Claude API call needed — run with: python generate.py --static
    """
    from templates import breadcrumb_schema

    # ── 1–3: Homepage, About, Contact ────────────────────────────────────────
    for filename, meta in STATIC_META.items():
        source = Path("..") / filename
        if not source.exists():
            print(f"WARNING: source file not found: {source} — skipping {filename}")
            continue

        html = source.read_text(encoding="utf-8")

        # Replace the entire <head>...</head> block
        new_head = _static_head(
            meta["html_title"], meta["og_title"], meta["meta_desc"], meta["slug"]
        )
        html = re.sub(r"<head>[\s\S]*?</head>", new_head, html, count=1)

        # Inject BreadcrumbList schema before </body> if not already present
        if 'BreadcrumbList' not in html:
            crumb = breadcrumb_schema("home", meta["slug"], meta["html_title"].split(" | ")[0])
            html = html.replace("</body>", f"{crumb}\n</body>", 1)

        out = OUTPUT_DIR / filename
        out.write_text(html, encoding="utf-8")
        print(f"Generated static page: {out}")

    # ── 4: Locations index ────────────────────────────────────────────────────
    cities = [row["city"] for row in load_csv("locations.csv")]
    loc_links = "\n".join(
        f'  <a href="/locations/{c.lower().replace(" ", "-")}" class="index-card"><strong>{c}</strong></a>'
        for c in cities
    )
    loc_content = f"""<p>Leading Tuition provides expert private tutors across the UK.
Choose your city below to find specialist GCSE, A-Level, 11+, and medicine prep tutors in your area.</p>
<div class="subject-grid">
{loc_links}
</div>"""
    loc_crumb = breadcrumb_schema("location", "locations", "Locations")
    loc_html = page_template(
        "Private Tutors by Location",
        loc_content,
        meta_desc=("Expert private tutors across the UK. Find GCSE, A-Level, 11+ and medicine "
                   "prep tutors in your city. DBS checked. 4.8/5 Trustpilot."),
        slug="locations",
        page_type="location",
        section="",
        schema_extra=loc_crumb,
    )
    (OUTPUT_DIR / "locations.html").write_text(loc_html, encoding="utf-8")
    print("Generated static page: output/locations.html")

    # ── 5: Subjects index ─────────────────────────────────────────────────────
    subjects = [row["subject"] for row in load_csv("subjects.csv")]
    sub_links = "\n".join(
        f'  <a href="/services/subjects/{s.lower().replace(" ", "-")}-tutor" class="index-card"><strong>{s}</strong></a>'
        for s in subjects
    )
    sub_content = f"""<p>Find a specialist tutor for your subject. Our tutors cover all GCSE and A-Level
subjects across AQA, Edexcel, OCR, and WJEC exam boards.</p>
<div class="subject-grid">
{sub_links}
</div>"""
    sub_crumb = breadcrumb_schema("subject", "subjects", "Subjects")
    sub_html = page_template(
        "GCSE and A-Level Tutors by Subject",
        sub_content,
        meta_desc=("Expert GCSE and A-Level tutors for every subject. AQA, Edexcel, OCR and WJEC. "
                   "DBS checked. 4.8/5 Trustpilot. Book a free consultation."),
        slug="subjects",
        page_type="subject",
        section="",
        schema_extra=sub_crumb,
    )
    (OUTPUT_DIR / "subjects.html").write_text(sub_html, encoding="utf-8")
    print("Generated static page: output/subjects.html")

    # ── 6: Blog index ─────────────────────────────────────────────────────────
    posts = load_csv("blog_topics.csv")
    blog_items = []
    for row in posts:
        title = row["title"]
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug).strip("-")
        blog_items.append(f'  <p><a href="{slug}"><strong>{title}</strong></a></p>')
    blog_content = (
        "<p>Practical, expert-backed guidance for UK parents and students on GCSEs, "
        "A-Levels, medical school applications, and more.</p>\n"
        + "\n".join(blog_items)
    )
    blog_crumb = breadcrumb_schema("blog", "blog", "Blog")
    blog_html = page_template(
        "Tutoring Advice and Guides",
        blog_content,
        meta_desc=("Expert tutoring advice for UK parents and students. Guides on GCSEs, A-Levels, "
                   "UCAT, MMI, Oxbridge, and 11+. From Leading Tuition."),
        slug="blog",
        page_type="blog",
        section="",
        schema_extra=blog_crumb,
    )
    (OUTPUT_DIR / "blog.html").write_text(blog_html, encoding="utf-8")
    print("Generated static page: output/blog.html")


# ── Specialist page meta descriptions ────────────────────────────────────────
SPECIALIST_META = {
    "ucat-tutor": (
        "Expert UCAT tutors with 90th-percentile scores. Proven strategies for all 5 sections. "
        "DBS-checked tutors. 4.8/5 Trustpilot. Book a free consultation."
    ),
    "mmi-interview-coaching": (
        "Expert MMI interview coaching for medical school entry. Role-play, ethical scenarios and "
        "structured feedback. 4.8/5 Trustpilot. Book a free consultation."
    ),
    "oxbridge-admissions-preparation": (
        "Expert Oxbridge admissions preparation: personal statements, interview practice and written "
        "test support. 4.8/5 Trustpilot. Book a free consultation."
    ),
    "university-personal-statement": (
        "Expert personal statement help for UCAS, Russell Group and Oxbridge. Tailored coaching from "
        "top graduates. 4.8/5 Trustpilot. Book a free consultation."
    ),
    "medicine-prep-hub": (
        "Complete medicine preparation: UCAT, MMI coaching, and personal statements. Expert support "
        "from medics. 4.8/5 Trustpilot. Book a free consultation."
    ),
    "oxbridge-subject-preparation": (
        "Oxbridge subject interview preparation by Oxford and Cambridge graduates. Tailored coaching "
        "for all subjects. 4.8/5 Trustpilot. Book a free consultation."
    ),
    "medical-school-interviews": (
        "Complete guide to UK medical school interviews — MMI and panel formats, what selectors assess, "
        "and how to prepare. Expert coaching from medics. Book a free consultation."
    ),
    "mmi-station-types": (
        "Full breakdown of MMI station types used at UK medical schools — role play, ethics, "
        "communication, and data stations explained with example prompts. Book a free consultation."
    ),
    "mmi-practice-questions": (
        "Real-style MMI practice questions for UK medical school applicants. Ethics, role play, "
        "communication and data stations. Expert coaching from Leading Tuition."
    ),
    "which-medical-schools-use-mmi": (
        "Which UK medical schools use MMI interviews in 2025? Full list of MMI, panel, and hybrid "
        "formats by institution. Expert preparation support from Leading Tuition."
    ),
}


# These slugs live under /medicine-prep/{slug}/ rather than /services/specialist-admissions/
MEDICINE_CLUSTER_SLUGS = {
    "medical-school-interviews",
    "mmi-station-types",
    "mmi-practice-questions",
    "which-medical-schools-use-mmi",
}


def generate_specialist_pages(limit=None):
    pages = load_csv("specialist_pages.csv")
    if limit is not None:
        pages = pages[:limit]

    for row in pages:
        slug = row["slug"]
        title = row["title"]
        keyword = row["keyword"]

        meta_desc = SPECIALIST_META.get(
            slug,
            f"Expert {title} support from Oxford and Cambridge-educated tutors. "
            "4.8/5 Trustpilot. Book a free consultation."
        )

        prompt = specialist_prompt(title=title, keyword=keyword, slug=slug)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)
        html = page_template(title, content, meta_desc=meta_desc, slug=slug, page_type="specialist", section="Services", schema_extra=faq_schema)

        # Medicine cluster pages go to output/medicine-prep/{slug}/index.html
        # All other specialist pages go to output/services/specialist-admissions/{slug}.html
        if slug in MEDICINE_CLUSTER_SLUGS:
            out_dir = OUTPUT_DIR / "medicine-prep" / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            file_path = out_dir / "index.html"
        else:
            out_dir = OUTPUT_DIR / "services" / "specialist-admissions"
            out_dir.mkdir(parents=True, exist_ok=True)
            file_path = out_dir / f"{slug}.html"

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated specialist page: {file_path}")


def generate_subject_pages(limit=None):
    subjects = load_csv("subjects.csv")
    if limit is not None:
        subjects = subjects[:limit]

    subjects_dir = OUTPUT_DIR / "services" / "subjects"
    subjects_dir.mkdir(parents=True, exist_ok=True)

    for row in subjects:
        subject = row["subject"]
        slug = subject.lower().replace(" ", "-")
        title = f"{subject} Tutor"
        page_slug = f"services/subjects/{slug}-tutor"
        # Per-subject overrides — distinct descriptions for SEO differentiation
        _subject_meta = {
            "Biology":          "Expert Biology tutors for GCSE and A-Level. All specifications covered: AQA, OCR, Edexcel. Required practicals, essay skills, and A-Level scaling. 4.8/5.",
            "Business Studies": "Expert Business Studies tutors for GCSE and A-Level. Case study technique, financial ratios, and business analysis. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",
            "Chemistry":        "Expert Chemistry tutors for GCSE and A-Level. Organic mechanisms, stoichiometry, required practicals. AQA, Edexcel and OCR. DBS-checked. 4.8/5 Trustpilot.",
            "Computer Science": "Expert Computer Science tutors for GCSE and A-Level. Programming, algorithms, networks and theory. AQA and OCR specifications. DBS-checked. 4.8/5 Trustpilot.",
            "Economics":        "Expert Economics tutors for GCSE and A-Level. Micro and macroeconomics, evaluation skills, and essay technique. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",
            "English Language": "Expert English Language tutors for GCSE and A-Level. Analytical frameworks, language analysis, and creative writing. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",
            "English Literature":"Expert English Literature tutors for GCSE and A-Level. Text analysis, essay technique, and unseen poetry. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",
            "Further Maths":    "Expert Further Maths tutors for GCSE and A-Level. Decision maths, mechanics, statistics, and pure modules. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",
            "Geography":        "Expert Geography tutors for GCSE and A-Level. Physical and human geography, fieldwork, and evaluation skills. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",
            "History":          "Expert History tutors for GCSE and A-Level. Source analysis, essay structure, and argument development. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",
            "Maths":            "Expert Maths tutors for GCSE and A-Level. Pure, Statistics, and Mechanics modules covered. AQA, Edexcel, OCR. Higher and Foundation. 4.8/5 Trustpilot.",
            "Physics":          "Expert Physics tutors for GCSE and A-Level. Mechanics, electricity, waves and nuclear physics. AQA, Edexcel, OCR. DBS-checked. 4.8/5 Trustpilot.",
            "Politics":         "Expert Politics tutors for GCSE and A-Level. UK Government and Politics, political ideologies, and comparative politics. AQA, Edexcel. 4.8/5 Trustpilot.",
            "Psychology":       "Expert Psychology tutors for GCSE and A-Level. Research methods, biological, cognitive, and social psychology. AQA, OCR. DBS-checked. 4.8/5 Trustpilot.",
            "Statistics":       "Expert Statistics tutors for GCSE and A-Level. Probability, hypothesis testing, distributions, and data analysis. AQA, Edexcel, OCR. 4.8/5 Trustpilot.",
        }
        meta_desc = _subject_meta.get(
            subject,
            f"Expert {subject} tutors for GCSE and A-Level. AQA, Edexcel and OCR support. "
            f"DBS-checked tutors. 4.8/5 Trustpilot. Book a free consultation."
        )

        prompt = subject_prompt(subject)
        content = ask_claude(prompt)
        html = page_template(
            title, content,
            meta_desc=meta_desc,
            slug=page_slug,
            page_type="subject",
            section="Subjects",
            base_tag='<base href="../" />'
        )

        file_path = subjects_dir / f"{slug}-tutor.html"
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated subject page: {file_path}")


# ── Per-city context for location page generation ────────────────────────────
CITY_CONTEXT = {
    "London": {
        "schools": ["St Paul's School", "Westminster School", "City of London School", "North London Collegiate School", "Henrietta Barnett School"],
        "grammar_schools": ["Henrietta Barnett School", "Queen Elizabeth's School Barnet", "Tiffin Girls' School"],
        "areas": ["Kensington", "Islington", "Richmond", "Hampstead", "Wimbledon"],
        "exam_board": "various (AQA, Edexcel, OCR — depending on school)",
        "eleven_plus": True,
        "local_pressure": "extremely competitive independent school entry at 7+, 11+, and 13+, fierce sixth-form competition, and thousands of families navigating Oxbridge and Russell Group applications each year",
        "special": None,
    },
    "Manchester": {
        "schools": ["Manchester Grammar School", "Manchester High School for Girls", "Withington Girls' School", "Cheadle Hulme School"],
        "grammar_schools": ["Altrincham Grammar School for Boys", "Altrincham Grammar School for Girls", "Sale Grammar School"],
        "areas": ["Didsbury", "Chorlton", "Altrincham", "Sale", "Prestwich"],
        "exam_board": "AQA (dominant in the North West)",
        "eleven_plus": True,
        "local_pressure": "strong grammar school competition across Trafford, Altrincham, and Sale, alongside high demand for support into Manchester University and medical schools",
        "special": None,
    },
    "Birmingham": {
        "schools": ["King Edward's School Birmingham", "Edgbaston High School for Girls", "King Edward VI Aston School", "King Edward VI Camp Hill School for Boys"],
        "grammar_schools": ["King Edward VI Aston School", "King Edward VI Camp Hill School for Boys", "King Edward VI Five Ways School"],
        "areas": ["Edgbaston", "Moseley", "Sutton Coldfield", "Harborne", "Solihull"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "intense competition for the King Edward VI foundation grammar schools, which are among the most academically selective in the country",
        "special": None,
    },
    "Leeds": {
        "schools": ["Leeds Grammar School", "Roundhay School", "Lawnswood School", "Notre Dame Catholic Sixth Form College"],
        "grammar_schools": [],
        "areas": ["Roundhay", "Chapel Allerton", "Headingley", "Harrogate", "Ilkley"],
        "exam_board": "AQA (dominant in Yorkshire)",
        "eleven_plus": False,
        "local_pressure": "strong A-Level demand targeting the University of Leeds and Russell Group entry, with many families in the northern suburbs seeking structured GCSE support",
        "special": None,
    },
    "Bristol": {
        "schools": ["Bristol Grammar School", "Clifton College", "St Mary Redcliffe and Temple School", "Cotham School", "Redland High School"],
        "grammar_schools": [],
        "areas": ["Clifton", "Redland", "Westbury Park", "Bishopston", "Henleaze"],
        "exam_board": "OCR (common in the Bristol and South West area)",
        "eleven_plus": False,
        "local_pressure": "high demand for support into the University of Bristol and competitive independent school entry, alongside growing interest in medicine and Oxbridge preparation",
        "special": None,
    },
    "Sheffield": {
        "schools": ["Sheffield High School for Girls", "Silverdale School", "King Edward VII School", "Tapton School"],
        "grammar_schools": [],
        "areas": ["Broomhill", "Nether Edge", "Fulwood", "Crookes", "Totley"],
        "exam_board": "AQA (dominant in Yorkshire)",
        "eleven_plus": False,
        "local_pressure": "steady demand for GCSE and A-Level support targeting the University of Sheffield and Russell Group, with an increasing number of medicine applicants from the area",
        "special": None,
    },
    "Liverpool": {
        "schools": ["Liverpool College", "Merchant Taylors' School", "The Belvedere Academy", "Calderstones School", "Wirral Grammar School"],
        "grammar_schools": ["Wirral Grammar School for Boys", "Wirral Grammar School for Girls"],
        "areas": ["Allerton", "Woolton", "West Derby", "Childwall", "Wirral"],
        "exam_board": "AQA (dominant in the North West)",
        "eleven_plus": True,
        "local_pressure": "demand for 11+ preparation across the Wirral alongside strong interest in medicine — the University of Liverpool's medical school draws significant applicant volume from the area",
        "special": None,
    },
    "Oxford": {
        "schools": ["Oxford High School", "Magdalen College School", "St Edward's School", "Cherwell School", "Headington School"],
        "grammar_schools": [],
        "areas": ["Summertown", "Jericho", "Headington", "Cowley", "Botley"],
        "exam_board": "OCR (common in Oxfordshire)",
        "eleven_plus": False,
        "local_pressure": "Oxford families face unique pressure — many parents and students are deeply aware of university admissions, and aspirations for Oxford and other highly competitive universities shape tutoring demand across all ages",
        "special": "oxbridge_proximity",
    },
    "Cambridge": {
        "schools": ["The Perse School", "Hills Road Sixth Form College", "Long Road Sixth Form College", "St Mary's School Cambridge", "The Stephen Perse Foundation"],
        "grammar_schools": [],
        "areas": ["Newnham", "Trumpington", "Chesterton", "Cherry Hinton", "Ely"],
        "exam_board": "OCR (common in Cambridgeshire)",
        "eleven_plus": False,
        "local_pressure": "Cambridge families often have high academic expectations, and many students are aiming for Cambridge University itself or other top universities. The town's culture of scholarship creates strong demand across all year groups",
        "special": "oxbridge_proximity",
    },
    "Brighton": {
        "schools": ["Brighton College", "Brighton and Hove High School", "BHASVIC", "Varndean Sixth Form College", "Dorothy Stringer School"],
        "grammar_schools": [],
        "areas": ["Hove", "Kemptown", "Fiveways", "Preston Park", "Lewes"],
        "exam_board": "OCR and Edexcel (common in Sussex)",
        "eleven_plus": False,
        "local_pressure": "strong demand for A-Level support from students targeting London and Russell Group universities, alongside competitive independent school preparation",
        "special": None,
    },
    "Nottingham": {
        "schools": ["Nottingham High School", "Trent College", "Bilborough College", "West Bridgford School", "Bluecoat Beechdale Academy"],
        "grammar_schools": [],
        "areas": ["West Bridgford", "Mapperley", "Sherwood", "Beeston", "Arnold"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "demand for structured GCSE and A-Level support, with increasing interest in medicine and Russell Group admissions among families in West Bridgford and the surrounding suburbs",
        "special": None,
    },
    "Leicester": {
        "schools": ["Leicester Grammar School", "Loughborough Grammar School", "Stoneygate School", "Gartree School"],
        "grammar_schools": [],
        "areas": ["Oadby", "Stoneygate", "Knighton", "Evington", "Wigston"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "demand for support targeting the University of Leicester's medical school and Russell Group entry, with growing interest in 11+ preparation among families in the Oadby and Stoneygate areas",
        "special": None,
    },
    "Slough": {
        "schools": ["Slough Grammar School", "Herschel Grammar School", "Langley Grammar School", "Upton Court Grammar School", "St Bernard's Catholic Grammar School", "Eton College"],
        "grammar_schools": ["Slough Grammar School", "Herschel Grammar School", "Langley Grammar School", "Upton Court Grammar School", "St Bernard's Catholic Grammar School"],
        "areas": ["Langley", "Burnham", "Windsor", "Maidenhead", "Iver"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "exceptionally competitive 11+ preparation across the Slough grammar school consortium — five grammar schools sharing the same SET exam — with families from Slough, Langley, Windsor and Maidenhead all competing for the same places",
        "special": None,
    },
    "Reading": {
        "schools": ["Reading School", "Kendrick School", "The Abbey School Reading", "The Oratory School", "St Joseph's College Reading"],
        "grammar_schools": ["Reading School", "Kendrick School"],
        "areas": ["Caversham", "Earley", "Tilehurst", "Woodley", "Henley-on-Thames"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "highly competitive 11+ preparation for Reading School and Kendrick School, two of the most selective grammar schools in England, alongside strong A-Level demand from families across Berkshire",
        "special": None,
    },
    "Guildford": {
        "schools": ["Royal Grammar School Guildford", "Tormead School", "Guildford High School", "St Catherine's School", "George Abbot School"],
        "grammar_schools": ["Royal Grammar School Guildford"],
        "areas": ["Merrow", "Shalford", "Godalming", "Farnham", "Woking"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "very competitive 11+ preparation for Royal Grammar School Guildford alongside strong demand for A-Level support from families in Surrey aiming for London and Oxbridge universities",
        "special": None,
    },
    "Coventry": {
        "schools": ["King Henry VIII School", "Bablake School", "Blue Coat CE School", "Finham Park School"],
        "grammar_schools": [],
        "areas": ["Earlsdon", "Kenilworth", "Leamington Spa", "Tile Hill"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "proximity to the University of Warwick creates a highly aspirational academic culture, with strong demand for A-Level support among families targeting Russell Group universities and medicine",
        "special": None,
    },
    "Watford": {
        "schools": ["Watford Grammar School for Boys", "Watford Grammar School for Girls", "St Michael's Catholic Grammar School", "St Columba's College"],
        "grammar_schools": ["Watford Grammar School for Boys", "Watford Grammar School for Girls"],
        "areas": ["Bushey", "Chorleywood", "Rickmansworth", "Oxhey"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "competitive 11+ entry for Watford Grammar School for Boys and Watford Grammar School for Girls, two oversubscribed selective state schools drawing applicants from across Hertfordshire",
        "special": None,
    },
    "Kingston upon Thames": {
        "schools": ["Tiffin School", "Tiffin Girls' School", "Surbiton High School", "Kingston Grammar School", "Holy Cross School"],
        "grammar_schools": ["Tiffin School", "Tiffin Girls' School"],
        "areas": ["Surbiton", "Norbiton", "New Malden", "Ham", "Tolworth"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "Tiffin School and Tiffin Girls' School are among the most academically competitive grammar schools in England, drawing hundreds of applicants from across South West London and Surrey for a small number of places each year",
        "special": None,
    },
    "Croydon": {
        "schools": ["Whitgift School", "Trinity School Croydon", "Old Palace of John Whitgift School", "Riddlesdown Collegiate"],
        "grammar_schools": ["Nonsuch High School for Girls", "Wallington County Grammar School"],
        "areas": ["Purley", "Coulsdon", "South Croydon", "Addiscombe", "Selsdon"],
        "exam_board": "AQA and Edexcel",
        "eleven_plus": True,
        "local_pressure": "competitive independent school entry for Whitgift and Trinity alongside selective school competition in neighbouring Sutton and Surrey, creating strong demand for 11+ preparation and A-Level support",
        "special": None,
    },
    "Bromley": {
        "schools": ["Newstead Wood School", "St Olave's Grammar School", "Langley Park School for Boys", "Hayes School"],
        "grammar_schools": ["Newstead Wood School", "St Olave's Grammar School for Boys", "Ravens Wood School"],
        "areas": ["Chislehurst", "Orpington", "Beckenham", "Petts Wood", "Shortlands"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "Newstead Wood and St Olave's are two of the most oversubscribed selective schools in Greater London, with many hundreds of children competing each year for a small number of places",
        "special": None,
    },
    "Barnet": {
        "schools": ["Queen Elizabeth's School Barnet", "Henrietta Barnett School", "Mill Hill School", "Haberdashers' Boys' School"],
        "grammar_schools": ["Queen Elizabeth's School Barnet", "Henrietta Barnett School"],
        "areas": ["East Barnet", "Cockfosters", "Finchley", "Totteridge", "Whetstone"],
        "exam_board": "AQA",
        "eleven_plus": True,
        "local_pressure": "Queen Elizabeth's School Barnet and Henrietta Barnett School are consistently ranked among the top state schools in England, and competition for places drives intense 11+ preparation among families across North London and Hertfordshire",
        "special": None,
    },
    "Ealing": {
        "schools": ["St Benedict's School", "Notting Hill and Ealing High School", "Drayton Manor High School", "Greenford High School"],
        "grammar_schools": [],
        "areas": ["Acton", "Hanwell", "Northfields", "Greenford", "Southall"],
        "exam_board": "AQA and Edexcel",
        "eleven_plus": False,
        "local_pressure": "strong demand for GCSE and A-Level support in West London, with many families seeking structured tuition to support entry to London universities and competitive independent schools including St Benedict's and Notting Hill and Ealing High",
        "special": None,
    },
    "Harrow": {
        "schools": ["Harrow School", "John Lyon School", "Harrow High School", "Canons High School", "St Dominic's Sixth Form College"],
        "grammar_schools": [],
        "areas": ["Stanmore", "Pinner", "Hatch End", "North Harrow", "Rayners Lane"],
        "exam_board": "AQA and Edexcel",
        "eleven_plus": False,
        "local_pressure": "competitive independent school entry for Harrow School and John Lyon School, alongside strong demand from families in Stanmore and Pinner seeking structured GCSE and A-Level support targeting Russell Group universities",
        "special": None,
    },
    "Wimbledon": {
        "schools": ["King's College School Wimbledon", "Wimbledon High School", "Rutlish School", "Ricards Lodge High School"],
        "grammar_schools": [],
        "areas": ["Raynes Park", "Merton Park", "Colliers Wood", "South Wimbledon", "Mitcham"],
        "exam_board": "AQA and Edexcel",
        "eleven_plus": False,
        "local_pressure": "competitive independent school entry for King's College School and Wimbledon High School — two of South West London's most academically selective schools — alongside strong A-Level demand from families targeting Russell Group and Oxbridge",
        "special": None,
    },
    "Twickenham": {
        "schools": ["Radnor House School", "Orleans Park School", "Waldegrave School for Girls", "Hampton School", "Lady Eleanor Holles School"],
        "grammar_schools": ["Tiffin School", "Tiffin Girls' School"],
        "areas": ["Richmond", "St Margarets", "Hampton", "Whitton", "Teddington"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "proximity to Tiffin School and Tiffin Girls' School creates intense 11+ competition, while a strong independent school sector including Hampton School and Lady Eleanor Holles means families face competitive entry choices at every stage",
        "special": None,
    },
    "York": {
        "schools": ["Bootham School", "St Peter's School York", "The Mount School York", "Archbishop Holgate's School", "Fulford School"],
        "grammar_schools": [],
        "areas": ["Heslington", "Bishopthorpe", "Fulford", "Clifton", "Poppleton"],
        "exam_board": "AQA",
        "eleven_plus": False,
        "local_pressure": "the University of York and the city's strong academic heritage create high aspirations among families, with steady demand for A-Level support targeting Russell Group entry and growing interest in medicine preparation",
        "special": None,
    },
    "Exeter": {
        "schools": ["Exeter School", "The Maynard School", "Exeter College", "St Luke's Science and Sports College", "Clyst Vale Community College"],
        "grammar_schools": [],
        "areas": ["Heavitree", "Topsham", "Pinhoe", "Exwick", "Crediton"],
        "exam_board": "OCR",
        "eleven_plus": False,
        "local_pressure": "the University of Exeter is one of the most popular Russell Group destinations in the South West, creating strong A-Level aspirations among local families alongside competitive independent school entry at Exeter School and The Maynard",
        "special": None,
    },
    "Norwich": {
        "schools": ["Norwich School", "Notre Dame High School", "City of Norwich School", "Langley School", "The Hewett Academy"],
        "grammar_schools": [],
        "areas": ["Eaton", "Thorpe St Andrew", "Hellesdon", "Sprowston", "Costessey"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "Norwich School is one of the most academically selective independent schools in the East of England, and the University of East Anglia draws strong local aspiration, with growing demand for A-Level support and Russell Group preparation",
        "special": None,
    },
    "Bath": {
        "schools": ["King Edward's School Bath", "Prior Park College", "Kingswood School", "Beechen Cliff School", "Hayesfield Girls' School"],
        "grammar_schools": [],
        "areas": ["Bathampton", "Larkhall", "Oldfield Park", "Weston", "Bradford-on-Avon"],
        "exam_board": "OCR",
        "eleven_plus": False,
        "local_pressure": "a thriving independent school sector alongside the University of Bath and proximity to Bristol create strong academic aspirations; demand is high for A-Level support and independent school preparation at King Edward's, Prior Park, and Kingswood",
        "special": None,
    },
    "Cheltenham": {
        "schools": ["Cheltenham Ladies' College", "Cheltenham College", "Dean Close School", "Pate's Grammar School", "Cheltenham Bournside School"],
        "grammar_schools": ["Pate's Grammar School"],
        "areas": ["Leckhampton", "Charlton Kings", "Prestbury", "Bishops Cleeve", "Cirencester"],
        "exam_board": "OCR",
        "eleven_plus": True,
        "local_pressure": "Pate's Grammar School is one of the most academically selective state schools in England, attracting applicants from across Gloucestershire; alongside one of the most prestigious independent school sectors in the country — including Cheltenham Ladies' College and Cheltenham College",
        "special": None,
    },
    "Milton Keynes": {
        "schools": ["Walton High School", "Denbigh School", "Stantonbury International School", "Leon Academy", "The Radcliffe School"],
        "grammar_schools": ["Aylesbury Grammar School", "Sir Henry Floyd Grammar School"],
        "areas": ["Woburn Sands", "Newport Pagnell", "Bletchley", "Wolverton", "Stony Stratford"],
        "exam_board": "AQA and OCR",
        "eleven_plus": True,
        "local_pressure": "Milton Keynes sits within Buckinghamshire, a fully selective county where the 11+ determines secondary school placement; families across the area seek preparation for Aylesbury Grammar School and other highly competitive Buckinghamshire selective schools",
        "special": None,
    },
    "Luton": {
        "schools": ["Luton VI Form College", "Stopsley High School", "St Joseph's Catholic High School", "Icknield High School"],
        "grammar_schools": [],
        "areas": ["Dunstable", "Harpenden", "Leagrave", "Stopsley", "Caddington"],
        "exam_board": "AQA and Edexcel",
        "eleven_plus": False,
        "local_pressure": "strong demand for GCSE and A-Level support among families in Harpenden and the surrounding villages who are targeting Russell Group universities, alongside growing interest in medicine preparation and Oxbridge coaching",
        "special": None,
    },
    "Derby": {
        "schools": ["Derby Grammar School", "Ockbrook School", "Emmanuel School Derby", "Merrill Academy", "Allestree Woodlands School"],
        "grammar_schools": [],
        "areas": ["Mickleover", "Allestree", "Littleover", "Chellaston", "Borrowash"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "demand for structured GCSE and A-Level support, particularly in the Littleover and Mickleover suburbs, with growing interest in medicine preparation targeting Nottingham and Leicester medical schools",
        "special": None,
    },
    "Portsmouth": {
        "schools": ["Portsmouth Grammar School", "St John's College Portsmouth", "Mayfield School", "Priory School Portsmouth", "Purbrook Park School"],
        "grammar_schools": [],
        "areas": ["Southsea", "Gosport", "Havant", "Fareham", "Waterlooville"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "competitive independent school entry at Portsmouth Grammar School alongside strong A-Level demand from families targeting Southampton, Exeter, and other Russell Group universities; growing interest in medicine preparation and UCAT coaching",
        "special": None,
    },
    "Northampton": {
        "schools": ["Northampton School for Boys", "Northampton High School for Girls", "Sponne School Towcester", "Guilsborough School"],
        "grammar_schools": [],
        "areas": ["Abington", "Kingsthorpe", "Duston", "Weston Favell", "Wellingborough"],
        "exam_board": "AQA and OCR",
        "eleven_plus": False,
        "local_pressure": "steady demand for GCSE and A-Level support among families targeting Russell Group universities, with growing interest in medicine preparation and structured coaching for students aiming for Nottingham and Leicester medical schools",
        "special": None,
    },
}


def location_prompt(city: str) -> str:
    ctx = CITY_CONTEXT.get(city, {})
    schools = ctx.get("schools", [])
    grammar_schools = ctx.get("grammar_schools", [])
    areas = ctx.get("areas", [])
    exam_board = ctx.get("exam_board", "AQA or OCR")
    eleven_plus = ctx.get("eleven_plus", False)
    local_pressure = ctx.get("local_pressure", "competitive academic environment")
    special = ctx.get("special")

    schools_str = ", ".join(schools) if schools else "local schools"
    areas_str = ", ".join(areas) if areas else "local areas"
    grammar_str = (
        f"Grammar schools in the area include: {', '.join(grammar_schools)}."
        if grammar_schools
        else ""
    )

    curriculum_note = ""
    gcse_section_title = "GCSE and A-Level Support"
    gcse_section_note = f"The dominant exam board in {city} is {exam_board}. Mention specific exam boards and qualification levels."

    # Oxbridge-proximity cities: extra callout
    if special == "oxbridge_proximity":
        oxbridge_note = f"""
- This page is for {city}, which has an unusually high proportion of students aiming for Oxbridge.
- Acknowledge this explicitly and explain that Leading Tuition supports both subject-level preparation and admissions coaching.
- Mention admissions tests (MAT, LNAT, TSA, HAT, ELAT) and interview preparation as relevant.
"""
    else:
        oxbridge_note = ""

    # 11+ section note
    if eleven_plus:
        eleven_plus_note = f"""
- {city} has competitive 11+ entry. {grammar_str} Name these schools specifically.
- Explain the 11+ process and how Leading Tuition helps families prepare.
"""
    else:
        eleven_plus_note = f"""
- {city} does not have grammar schools requiring 11+. Do not write about 11+ preparation as a standalone topic — instead, briefly mention that Leading Tuition supports primary-age students and early secondary preparation.
"""

    # 4 structure variants assigned deterministically so reruns are consistent
    import hashlib
    variant = int(hashlib.md5(city.encode()).hexdigest(), 16) % 4

    if variant == 0:
        # Opens with local academic landscape; leads with GCSE/A-Level, builds up to admissions
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Private Tuition in {city} — Understanding the Local Landscape
  2. {gcse_section_title}
  3. 11+ and Selective School Entry in {city}
  4. University and Medicine Admissions Support
  5. How Our Tutors Work with {city} Families
  6. Frequently Asked Questions

Opening paragraph angle: Start by describing the specific academic pressures and milestones that define education in {city}. Ground it in local detail — name areas, schools, or the dominant exam board. The parent should feel you understand their city, not just their postcode.

FAQ focus: One question on GCSE exam boards used locally, one on 11+ or selective entry, one on online vs in-person sessions, one on how quickly students typically see progress."""

    elif variant == 1:
        # Opens with the parent's anxiety; leads with selective/grammar school pressure first
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Tutoring in {city} — What Local Families Ask Us Most
  2. 11+ and Grammar School Preparation in {city}
  3. GCSE and A-Level Tuition Across {city}
  4. Oxbridge, Medicine, and Competitive University Applications
  5. Why {city} Parents Choose Leading Tuition
  6. Frequently Asked Questions about Tutoring in {city}

Opening paragraph angle: Open with the specific decision or worry a {city} parent is sitting with right now — whether that's a grammar school deadline, an upcoming GCSE mock, or a university application. Acknowledge the pressure without amplifying it. Name 1–2 specific schools or areas in the first paragraph.

FAQ focus: One question on how early to start 11+ preparation, one on what subjects are most requested in {city}, one on DBS checks and tutor vetting, one on session frequency recommendations."""

    elif variant == 2:
        # Opens with tutors and credibility; leads with medicine/university, then works down to GCSE
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Expert Tutors in {city} — How We're Different
  2. Medicine, Oxbridge, and University Admissions Coaching
  3. A-Level and GCSE Tuition in {city}
  4. Primary, 11+, and Early Secondary Support
  5. What {city} Families Say About Working with Us
  6. Common Questions from {city} Parents

Opening paragraph angle: Lead with the quality and specialism of Leading Tuition's tutors, grounding it immediately in what that means for a family in {city}. Mention the specific academic stakes in {city} — what students here are competing for, and why having the right tutor matters. Name at least one school or area.

FAQ focus: One question on how tutors are matched to students, one on UCAT and medical school preparation, one on A-Level subject choices, one on whether tuition works for students who are already doing well."""

    else:
        # variant == 3: Opens with a specific local challenge; weaves all levels through a narrative structure
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Supporting {city} Students from 11+ to University
  2. Preparing for Selective Schools and the 11+ in {city}
  3. Raising Grades at GCSE — {city} Schools and Exam Boards
  4. A-Level Tuition and Sixth Form Support in {city}
  5. Medical School and Oxbridge Preparation for {city} Applicants
  6. Frequently Asked Questions

Opening paragraph angle: Frame the page around a student's academic journey in {city} — from primary through to university application. Acknowledge that the challenges change at each stage and that Leading Tuition supports families at all of them. Name 2–3 specific schools or neighbourhoods to establish local credibility immediately.

FAQ focus: One question on whether Leading Tuition covers the student's specific school or exam board, one on moving from GCSE to A-Level support, one on last-minute or intensive revision programmes, one on what happens if a student's grades don't improve."""

    return f"""
You are writing a location SEO page for Leading Tuition, a UK tutoring company.

Audience:
- The reader is a UK parent in or near {city} looking for private tuition for their child.
- They want to see that Leading Tuition understands their local area and its specific academic pressures.
- They are anxious, busy, and want to feel they are in safe hands.

Global rules:
- Write for a UK parent, not an SEO algorithm.
- Use a warm, expert, reassuring tone.
- Output plain HTML only — no markdown.
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>.
- Do not include <html>, <head>, or <body>.
- Do not include CTA buttons or footer text — the template handles those.
- End naturally, without sounding salesy.
- Include one FAQ section with exactly 4 questions.
- Never use generic filler phrases like "look no further" or "we've got you covered".
- Never mention BMAT as a current admissions test — it was abolished in 2023. Oxford, Cambridge, and Imperial now use UCAT.
{curriculum_note}

Before writing, think through:
1. What does a parent in {city} worry about most when it comes to their child's education?
2. What is specific to {city} that makes this page feel genuinely local, not templated?
3. What are 3 concrete facts about {city}'s educational landscape that a local parent would recognise?

Now write a location page in HTML about: Private Tuition in {city}

Content requirements:
- Target length: 950 to 1,100 words
- Opening paragraph must mention {city} by name and acknowledge {local_pressure}
- You MUST mention at least 3 of these real local schools by name: {schools_str}
- You MUST name at least 2 of these local neighbourhoods or areas: {areas_str}
- {gcse_section_note}
{eleven_plus_note}
{oxbridge_note}

Structure to use:
{structure}

Additional requirements:
- Include one short <ul> bullet list somewhere in the page (not in the FAQ section)
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- Do not pad — every sentence must be genuinely useful
"""


def blog_prompt(title: str, keyword: str, slug: str) -> str:
    master_context = """
You are writing an SEO blog post for Leading Tuition, a UK tutoring company.

Audience:
- The primary reader is a UK parent or student searching for practical, trustworthy guidance.
- They want a clear, honest answer — not a sales page.

Global rules:
- Write for a UK parent or student, not an SEO algorithm.
- Use a clear, warm, authoritative tone.
- Output plain HTML only — no markdown.
- Use only these tags: <p>, <h2>, <h3>, <ul>, <ol>, <li>, <strong>, <em>.
- Do not include <html>, <head>, or <body>.
- Do not include CTA buttons or footer text — the template handles those.
- Do not mention Leading Tuition more than twice in the body content.
- Include specific UK facts, figures, exam board references, and year group context.
- End with a brief, natural closing paragraph — not a sales pitch.
- Include one FAQ section with exactly 4 questions under <h2>Frequently Asked Questions</h2>.
- Under the FAQ section, write each question as <p><strong>Question?</strong></p> followed by a <p> answer.
- Never use generic filler phrases like "navigate the journey", "look no further", or "in today's world".
- Never mention BMAT as a current admissions test — it was abolished in 2023. Oxford, Cambridge, and Imperial now use UCAT.
- After all HTML content, on a new line, output a META_DESC line in this exact format (one line, 145–158 characters including spaces, must include the target keyword naturally, must answer what the page covers and give a reason to click — no generic filler like "Expert advice from Leading Tuition"):
META_DESC:Your compelling meta description here, 145-158 chars, keyword-rich, specific.
- Then on the next line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{"q":"Question one","a":"Answer one"},{"q":"Question two","a":"Answer two"},{"q":"Question three","a":"Answer three"},{"q":"Question four","a":"Answer four"}]
"""

    if slug == "ucat-score-requirements-for-uk-medical-schools-2025":
        return f"""
{master_context}

Before writing, think through:
1. What score thresholds do different tiers of UK medical schools actually use?
2. What do parents and students get wrong about UCAT scoring?
3. What happened to BMAT, and why does it matter for 2025 applicants?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must immediately address why UCAT scores matter and how competitive they are
- Include these exact <h2> sections in this order:
  1. What Is a Good UCAT Score?
  2. How Medical Schools Use UCAT Scores
  3. 2024 UCAT Cut-Off Scores: What Six Medical Schools Expected
  4. UCAT Score Benchmarks by School Tier
  5. What Happens If Your Score Is Below Average
  6. How to Prepare Effectively
  7. Frequently Asked Questions
- Must include:
  - 2024 average UCAT score approximately 615 per subtest (combined ~2,460)
  - Competitive scores approximately 670 to 700+ for top medical schools
  - The 5 UCAT subtests: Verbal Reasoning, Decision Making, Quantitative Reasoning, Abstract Reasoning, Situational Judgement
  - Situational Judgement is banded (Band 1 to 4), not scored numerically
  - Oxford, Cambridge, and Imperial now use UCAT (BMAT was abolished in 2023)
  - Students have one attempt per application cycle
  - Section 3 must contain an HTML <table> with columns: Medical School, 2024 Approximate Cut-Off (Total), Approx. Per Subtest, How UCAT Is Used. Include 6 schools: Oxford (~2,760+), Imperial (~2,720+), Edinburgh (~2,660+), Manchester (~2,620+), Sheffield (~2,580+), Nottingham (~2,540+). Add a note that SJT Band 1-2 is expected at all schools.
- Include one short bullet or numbered list
- FAQ questions must address timing, score expectations, retakes policy, and school-specific thresholds
"""

    if slug == "what-grade-do-you-need-for-oxbridge-chemistry":
        return f"""
{master_context}

Before writing, think through:
1. What grades do Oxford and Cambridge Chemistry actually require — and what is the realistic competitive floor?
2. What admissions tests and interviews are involved?
3. What do applicants get wrong about Oxbridge Chemistry entry?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must address the question directly and acknowledge that grades are necessary but not sufficient
- Include these exact <h2> sections in this order:
  1. The Grade Requirements for Oxbridge Chemistry
  2. A-Level Subject Choices That Matter
  3. The Chemistry Admissions Test (CAT / PAT)
  4. What the Interview Process Looks Like
  5. How to Strengthen an Oxbridge Chemistry Application
  6. Frequently Asked Questions
- Must include:
  - Oxford Chemistry typically requires A*A*A with A* in Chemistry and Mathematics
  - Cambridge Chemistry typically requires A*A*A with A* in Chemistry
  - Oxford uses the Chemistry Admissions Test (CAT); Cambridge uses the Natural Sciences Admissions Assessment (NSAA)
  - Interviews focus on problem-solving and reasoning, not memorised answers
  - Strong candidates typically have Further Maths or Physics alongside Chemistry
- Include one short bullet or numbered list
- FAQ questions must address grade requirements, admissions tests, subject combinations, and interview preparation
"""

    if slug == "how-to-prepare-for-a-medical-school-mmi-interview":
        return f"""
{master_context}

Before writing, think through:
1. What is an MMI, and what do most applicants not understand about it?
2. What station types trip candidates up most often?
3. How is MMI preparation different from preparing for a traditional panel interview?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must acknowledge how unfamiliar and nerve-wracking the MMI format can feel
- Include these exact <h2> sections in this order:
  1. What Is the MMI Format?
  2. The Most Common MMI Station Types
  3. What Assessors Are Looking For
  4. How to Prepare for MMI Stations
  5. Common Mistakes to Avoid
  6. Frequently Asked Questions
- Must include:
  - Typical format: 5 to 10 stations, each 5 to 8 minutes
  - Different assessors at each station
  - Common station types: ethical scenarios, role play, data interpretation, written task, empathy station
  - MMI tests communication, ethical reasoning, and self-awareness — not clinical knowledge
  - Preparation timeline of roughly 6 to 10 weeks is recommended
- Include one short bullet list
- FAQ questions must address timing, station types, what to say when stuck, and how to practise
"""

    if slug == "a-level-subject-choices-for-medicine-applications":
        return f"""
{master_context}

Before writing, think through:
1. Which A-Level subjects are genuinely required versus recommended for medicine?
2. What mistakes do applicants make with subject choices that hurt their chances?
3. How do subject choices interact with UCAT, personal statements, and interviews?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must address why A-Level choices matter more for medicine than for most other courses
- Include these exact <h2> sections in this order:
  1. The Essential A-Levels for Medicine
  2. Recommended and Useful Additional Subjects
  3. Subjects to Approach with Caution
  4. How Subject Choices Affect Your Application
  5. What Else Matters Alongside Your Subjects
  6. Frequently Asked Questions
- Must include:
  - Chemistry is required by virtually all UK medical schools
  - Biology is required or strongly preferred by most
  - A third science or Mathematics is broadly advantageous
  - Humanities and social sciences are acceptable as a third choice at most schools
  - Some schools (notably Oxford and Cambridge) have stricter requirements
  - Critical Thinking and General Studies are not counted by most medical schools
- Include one short bullet or numbered list
- FAQ questions must address Chemistry requirements, whether Biology is compulsory, AS-Level retakes, and what to do with mixed subject sets
"""

    if slug == "what-is-the-11-plus-exam":
        return f"""
{master_context}

Before writing, think through:
1. What do parents actually need to know about the 11+ that is not obvious from the name?
2. How does the format vary between regions and consortia?
3. What is the realistic preparation timeline and what does it involve?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must explain what the 11+ is and why it matters without being condescending
- Include these exact <h2> sections in this order:
  1. What Is the 11 Plus Exam?
  2. Which Schools Use the 11 Plus?
  3. What the 11 Plus Tests
  4. How the 11 Plus Varies by Region
  5. When and How to Prepare
  6. Frequently Asked Questions
- Must include:
  - The 11+ is a selective entrance exam taken in Year 6 (age 10 to 11)
  - Used by grammar schools and some independent schools
  - Tests typically include: verbal reasoning, non-verbal reasoning, mathematics, and English
  - GL Assessment and CEM are the two main test providers — format varies by area
  - Results usually determine entry to Year 7
  - Preparation typically starts in Year 4 or early Year 5
- Include one short bullet list
- FAQ questions must address when to start, test providers, pass marks, and how to find out which test a specific school uses
"""

    if slug == "how-long-does-gcse-revision-take":
        return f"""
{master_context}

Before writing, think through:
1. What do parents and Year 11 students actually want to know about revision hours and timing?
2. What makes revision effective vs. ineffective — and what habits waste the most time?
3. What realistic week-by-week structure would help a student starting 12 weeks before exams?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must answer the title question directly with a realistic, specific answer
- Include these exact <h2> sections in this order:
  1. The Short Answer: How Long Does GCSE Revision Actually Take?
  2. Why There's No Single "Right" Number of Hours
  3. A Realistic Revision Timeline for Year 11 Students
  4. 12-Week GCSE Revision Schedule: Week by Week
  5. How to Revise Efficiently — Quality Matters More Than Hours
  6. Subject-by-Subject Estimates: What to Expect
  7. When Students Should Consider Extra Support
  8. Frequently Asked Questions
- Must include:
  - Section 4 must be a structured <ul> list with all 12 weeks numbered (Week 1 through Week 12), each with specific daily/weekly activities — not a single paragraph
  - Mention active recall, spaced repetition, and past paper practice as key techniques
  - Reference AQA, Edexcel, and OCR past papers as free resources
  - Subject-specific hour estimates for Maths, English, Sciences, Humanities, and Languages
  - The Easter break as a key intensive revision window
- Include one short bullet or numbered list
- FAQ questions must address total hours needed, how to start, managing multiple subjects, and what to do if behind
"""

    if slug == "the-new-ucas-personal-statement-2026-a-guide-to-the-3-question-format":
        return f"""
{master_context}

Before writing, think through:
1. What exactly changed in the UCAS personal statement format for 2026 entry — and what stayed the same?
2. What are the three questions, and what does each one actually ask?
3. What mistakes will students make if they approach 2026 the same way as older guidance?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must immediately flag that this is a major format change and who it affects (Year 13 2025-26 cohort)
- Include these exact <h2> sections in this order:
  1. What Changed with the UCAS Personal Statement in 2026?
  2. The Three Questions Explained
  3. How to Answer Question 1: Why This Subject?
  4. How to Answer Question 2: Preparing for Higher Education
  5. How to Answer Question 3: Broader Skills and Experiences
  6. Common Mistakes to Avoid
  7. Frequently Asked Questions
- Must include:
  - The old format was a free-form 4,000-character essay; the new format is three structured questions
  - Question 1 focuses on subject passion and intellectual curiosity
  - Question 2 focuses on readiness and preparation for university-level study
  - Question 3 focuses on extracurricular activities, skills, and personal development
  - Each question has its own character limit
  - This applies to 2026 entry (Year 13 students in 2025-26)
  - Mention that super-curricular activities are now more clearly separated from academic motivation
- Include one short bullet or numbered list
- FAQ questions must address: whether the old advice still applies, word/character limits, how to structure each answer, and whether the change helps or hinders applicants
"""

    if slug == "ucat-cut-offs-for-every-uk-medical-school-5-year-trends-and-2026-predictions":
        return f"""
{master_context}

Before writing, think through:
1. What are the actual UCAT cut-off score trends over the past 5 years at different medical schools?
2. Which schools are most and least score-dependent, and how does SJT interact?
3. What can applicants in 2026 realistically predict from past trends?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph must explain why cut-offs vary so much and why tracking trends matters for 2026 applicants
- Include these exact <h2> sections in this order:
  1. How UCAT Cut-Offs Work (and Why They Change Each Year)
  2. UCAT Cut-Off Trends: High-Competition Schools
  3. UCAT Cut-Off Trends: Mid-Range Schools
  4. UCAT Cut-Off Trends: Lower-Threshold Schools
  5. The Role of SJT in Cut-Off Decisions
  6. 2026 Predictions: What Scores to Target
  7. Frequently Asked Questions
- Must include:
  - Section 2 must contain an HTML <table> showing approximate trends for 5 high-competition schools (Oxford, Imperial, Edinburgh, UCL, Barts): columns = School, ~2022, ~2023, ~2024, Trend
  - Section 3 must contain an HTML <table> for mid-range schools (Bristol, Leeds, Birmingham, Nottingham, Sheffield): same columns
  - Section 4 must contain an HTML <table> for lower-threshold schools (Lancaster, Keele, Sunderland, Lincoln, Anglia Ruskin): same columns
  - Explain SJT Bands 1-2 are expected at most competitive schools; Band 3 may be tolerated at others
  - Clarify that cut-offs are set post-hoc based on applicant pool — not pre-announced
  - 2026 prediction: rising cut-offs at Oxford/Imperial given UCAT now replaces BMAT there (since 2024)
- Include one short bullet list
- FAQ questions must address: what is a safe UCAT score, do all schools publish cut-offs, what to do with a low SJT band, and how many schools to apply to
"""

    if slug == "oxford-cambridge-and-ucl-medicine-mastering-the-ucat-for-elite-universities":
        return f"""
{master_context}

Before writing, think through:
1. How do Oxford, Cambridge, and UCL each use UCAT in their admissions process — and what makes each distinctive?
2. What score is genuinely required at each, and what does a realistic competitive application look like?
3. What are the biggest misconceptions about applying to these three schools?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must immediately establish why these three schools are distinct and why the UCAT stakes are higher
- Include these exact <h2> sections in this order:
  1. Why Oxford, Cambridge, and UCL Set the UCAT Bar So High
  2. Oxford Medicine: UCAT Requirements and What Else Matters
  3. Cambridge Medicine: UCAT, ESAT, and the Clinical Years
  4. UCL Medicine: A Competitive London Alternative
  5. How to Prepare Your UCAT for Top-Three Entry
  6. Frequently Asked Questions
- Must include:
  - Oxford has used UCAT since 2024 entry (previously BMAT)
  - Cambridge does NOT use UCAT — it uses ESAT for some routes and has separate interview process
  - UCL uses UCAT and is one of the most competitive London medical schools
  - Approximate UCAT score targets: Oxford 2,750+, UCL 2,700+
  - All three require exceptional interviews, not just high scores
  - Clarify the confusion around Cambridge not using UCAT
- Include one short bullet list
- FAQ questions must address: whether Cambridge uses UCAT, the minimum UCAT score for Oxford, how UCL compares, and interview format differences
"""

    if slug == "low-ucat-score-top-5-strategic-uk-medical-schools-to-apply-to-in-2026":
        return f"""
{master_context}

Before writing, think through:
1. Which medical schools genuinely weight UCAT less heavily, or have lower thresholds, in 2026?
2. What is a "low" score in context — and what other factors can compensate?
3. What mistakes do low-scorers make when choosing schools to apply to?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must be empathetic but pragmatic — a lower UCAT score is not the end, but strategy matters
- Include these exact <h2> sections in this order:
  1. What Counts as a Low UCAT Score?
  2. Schools That Weight UCAT Less Heavily
  3. The Top 5 Strategic Choices for 2026
  4. What to Emphasise When Your UCAT Is Below Average
  5. Can You Resit the UCAT?
  6. Frequently Asked Questions
- Must include:
  - "Low" in context means below approximately 2,500 combined (below the national mean)
  - Section 3 must contain an HTML <table> with columns: Medical School, Why Strategic, Approx. UCAT Threshold, Interview Style — covering 5 schools (e.g. Lancaster, Keele, Anglia Ruskin, Sunderland, Hull York)
  - Schools that holistically review: GCSEs, personal statement, and references can outweigh a middling UCAT
  - Resitting: one attempt per cycle; resit preparation strategy
  - SJT Band still matters even when cognitive score is lower
  - Encourage applicants to be realistic about school selection — avoid top-5 with sub-2,500 scores
- Include one short bullet list
- FAQ questions must address: can you get into medicine with a low UCAT, which schools weigh UCAT least, how to improve, and whether to resit or apply
"""

    if slug == "mmi-interviews-2026-50-real-scenarios-and-model-answer-frameworks":
        return f"""
{master_context}

Before writing, think through:
1. What are the most commonly encountered MMI station types in 2026 UK medical school interviews?
2. What makes a model answer framework actually useful — what structure do high-scoring candidates use?
3. What categories of scenario trip up even well-prepared applicants?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,400 to 1,800 words
- Opening paragraph must frame why MMI preparation requires scenario practice, not just knowledge
- Include these exact <h2> sections in this order:
  1. How MMI Interviews Work in 2026
  2. Ethical Scenario Stations: Examples and Frameworks
  3. Empathy and Communication Stations
  4. Role Play Stations
  5. Data Interpretation and Written Stations
  6. NHS Knowledge and Current Affairs Stations
  7. Common Mistakes and How to Avoid Them
  8. Frequently Asked Questions
- Must include:
  - Each section (2-6) must contain at least 5 labelled scenario examples in a <ul> list
  - For ethical scenarios: introduce the SBARR or four-principles framework (autonomy, beneficence, non-maleficence, justice)
  - For empathy stations: introduce a simple structure — acknowledge, explore, respond
  - Role play: explain candidates are marked on tone and listening, not on giving clinical advice
  - NHS current affairs examples relevant to 2026: junior doctor contracts, waiting lists, AI in diagnostics
  - Emphasise that assessors mark each station independently — bad stations can be recovered
- Include one short bullet list
- FAQ questions must address: how many stations are typical, whether you can ask for time to think, how to handle stations where you don't know the answer, and how to practise alone
"""

    if slug == "medical-schools-that-dont-care-about-gcses-a-strategic-selection-guide":
        return f"""
{master_context}

Before writing, think through:
1. Which UK medical schools genuinely give less weight to GCSEs — and which still care despite claiming otherwise?
2. What are the thresholds different schools apply, and how transparent are they about this?
3. What strategy should applicants with weaker GCSEs follow?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must acknowledge that GCSEs matter at most schools, but not equally — and explain why
- Include these exact <h2> sections in this order:
  1. Why GCSEs Matter (and When They Don't)
  2. Medical Schools With Lower GCSE Requirements
  3. Medical Schools That Don't Screen on GCSEs at All
  4. Graduate-Entry Courses: A Different Route
  5. Building a Strong Application Despite Weak GCSEs
  6. Frequently Asked Questions
- Must include:
  - Section 2 must contain an HTML <table>: School, GCSE Policy, What They Look For Instead — covering 5 schools (e.g. Lancaster, Keele, Sunderland, Lincoln, Hull York)
  - Graduate-entry schools (Warwick, Swansea) typically do not screen on GCSEs at all
  - GCSEs matter most for Oxford, Cambridge, UCL, Imperial, and Edinburgh
  - UCAT and interview performance can compensate for weak GCSEs at many schools
  - Mention the GAMSAT for graduate entry as an alternative to UCAT
- Include one short bullet list
- FAQ questions must address: what is a "low" GCSE grade for medicine, can you get in with C grades, whether schools ask for GCSE certificates, and the best advice for applicants with mixed results
"""

    if slug == "how-to-get-2800-in-the-ucat-a-week-by-week-revision-roadmap":
        return f"""
{master_context}

Before writing, think through:
1. What preparation habits and techniques actually distinguish 2800+ scorers from average candidates?
2. How should preparation be structured across 10-12 weeks — and what are the critical milestones?
3. What are the most commonly wasted revision hours and how should they be redirected?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph must frame 2800+ as genuinely achievable with structured preparation — not just for exceptional students
- Include these exact <h2> sections in this order:
  1. What Does a 2800+ Score Actually Require?
  2. The 12-Week UCAT Revision Roadmap
  3. Verbal Reasoning: Speed and Accuracy Strategies
  4. Decision Making and Quantitative Reasoning: The Logic Approach
  5. Abstract Reasoning: Pattern Spotting Under Pressure
  6. Situational Judgement: How to Score Band 1
  7. Mock Exams and Final Preparation
  8. Frequently Asked Questions
- Must include:
  - Section 2 must be a structured <ul> week-by-week plan (Weeks 1-12), each with specific focus areas
  - 2800+ corresponds to approximately 700 per subtest — in the top 10% of all sitters
  - Official UCAT practice materials (Medify, Kaplan, Question Bank) — mention at least 2
  - Time management is critical: each subtest is strictly timed
  - SJT Band 1 requires understanding of GMC Good Medical Practice principles
  - Diminishing returns on practice without review — reviewing wrong answers is as important as volume
- Include one short bullet list
- FAQ questions must address: how many practice questions to do per day, when to start, the difference between Medify and the official question bank, and whether the UCAT can be taken more than once per cycle
"""

    if slug == "2026-grammar-school-league-tables-top-schools-ranked-by-gcse-results":
        return f"""
{master_context}

Before writing, think through:
1. Which grammar schools consistently top GCSE league tables — and what does that data actually tell parents?
2. How should parents interpret league table data? What is misleading about raw rankings?
3. What do the top-performing grammar schools in 2026 have in common?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must address why parents rely on league tables — and what these tables can and cannot tell you
- Include these exact <h2> sections in this order:
  1. How Grammar School League Tables Work
  2. Top Grammar Schools by GCSE Results: 2025 Data
  3. Regional Breakdown: Where Grammar Schools Perform Best
  4. What to Look for Beyond Raw Rankings
  5. How to Use League Table Data Strategically
  6. Frequently Asked Questions
- Must include:
  - Section 2 must contain an HTML <table>: School Name, Location, Approx. % 9-7 Grades, Value-Added Score (approx.), Notable Features — covering at least 8 schools (include: King Edward VI Five Ways, Wallington County Grammar, Dartford Grammar, Kendrick, Reading School, Aylesbury Grammar, Tiffin, Wilson's)
  - Progress 8 and Attainment 8 explained briefly as the two main DfE metrics
  - Distinguish between selective (grammar) and super-selective grammars (e.g. King Edward's Birmingham, Tiffin)
  - Location matters: some grammar schools draw national applicants; others are strictly local
  - League table position does not always predict best fit — pastoral care and culture matter
- Include one short bullet list
- FAQ questions must address: which grammar school is best in England, how to compare two schools in the same area, whether to prioritise league table position or school culture, and where to find official DfE data
"""

    if slug == "11-plus-pass-marks-by-region-how-high-do-you-need-to-score":
        return f"""
{master_context}

Before writing, think through:
1. What are the actual 11+ pass marks in different regions of England — and why do they vary so much?
2. What is standardised scoring and how does it differ from raw marks?
3. What does a parent need to know to understand whether their child's score was sufficient?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must immediately explain that pass marks are not fixed numbers — they depend on the region, school, and year
- Include these exact <h2> sections in this order:
  1. Why 11 Plus Pass Marks Vary by Region
  2. How Standardised Scores Work
  3. 11 Plus Pass Marks by Region: 2025 Overview
  4. Super-Selective vs. Standard Grammar Schools
  5. What to Do If Your Child Is Near the Borderline
  6. Frequently Asked Questions
- Must include:
  - Section 3 must contain an HTML <table>: Region, Test Provider (GL/CEM/Local), Standardised Score Target, Raw Score Range (approx.), Number of Grammar Schools — covering at least 8 regions (Kent, Buckinghamshire, Lincolnshire, West Midlands, Essex, Berkshire, Greater Manchester, Surrey)
  - GL Assessment uses standardised scores (mean 100, SD 15); CEM uses percentiles
  - Super-selectives (e.g. King Edward's, Tiffin, Henrietta Barnett) may require 130+ standardised score
  - Standard grammars may offer places to children scoring 111-115+
  - Borderline policies: some schools have waiting lists or second round interviews
  - Mention that schools' own websites publish qualifying score ranges for recent years
- Include one short bullet list
- FAQ questions must address: what is a passing score in Kent, how CEM results are communicated, what to do if a score is borderline, and whether there is an appeal process
"""

    if slug == "gl-assessment-vs-cem-vs-local-school-exams-the-2026-format-guide":
        return f"""
{master_context}

Before writing, think through:
1. What are the concrete differences between GL Assessment, CEM, and locally-set 11+ exams in format, content, and scoring?
2. Which regions use which provider — and how does that determine preparation strategy?
3. What are the most common mistakes families make in preparing for the wrong exam type?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must explain that getting the wrong preparation materials is one of the biggest 11+ mistakes
- Include these exact <h2> sections in this order:
  1. The Three Types of 11 Plus Exam
  2. GL Assessment: Format and What to Expect
  3. CEM: Format and What to Expect
  4. Local School Exams: Who Sets Them and Why
  5. Region-by-Region Guide: Who Uses Which Provider
  6. Preparing for the Right Exam: What to Buy and What to Avoid
  7. Frequently Asked Questions
- Must include:
  - Section 5 must contain an HTML <table>: Region, Provider, Subjects Tested, Scoring Method — covering at least 10 regions (Kent, Bucks, Lincs, Essex, Birmingham, Surrey, Wirral, Gloucestershire, Berkshire, Devon)
  - GL Assessment: verbal reasoning, non-verbal reasoning, maths, English — often separate papers; multiple choice
  - CEM: integrated paper mixing comprehension, vocabulary, numerical, spatial; marks awarded for speed and accuracy
  - Local exams: e.g. Sutton schools consortium, CSSE (Essex), Hertfordshire — independently designed
  - Preparation resources: GL official practice papers vs. CEM-style Bond books — NOT interchangeable
  - GL questions tend to be more predictable; CEM is deliberately harder to tutor for
- Include one short bullet list
- FAQ questions must address: how to find out which test a school uses, whether GL or CEM is harder, whether past papers are available, and whether preparation for one helps with the other
"""

    if slug == "the-6-month-11-plus-countdown-a-monthly-study-milestone-plan":
        return f"""
{master_context}

Before writing, think through:
1. What does a realistic 6-month 11+ preparation plan look like for a Year 5 or early Year 6 child?
2. What should be covered in each month — and what should be left until closer to the exam?
3. What do parents consistently underestimate or over-prioritise in 11+ preparation?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must reassure parents that 6 months is a realistic timeline if well-structured
- Include these exact <h2> sections in this order:
  1. Is 6 Months Enough for the 11 Plus?
  2. Month 1: Diagnosis and Baseline Assessment
  3. Month 2: Core Skills Foundation
  4. Month 3: Verbal and Non-Verbal Reasoning Intensive
  5. Month 4: Timed Practice and Stamina Building
  6. Month 5: Mock Exams and Weak Area Focus
  7. Month 6: Final Preparation and Exam Technique
  8. Frequently Asked Questions
- Must include:
  - Each month section (2-7) must be a <ul> list of 4-6 specific milestones or activities
  - Distinguish between GL and CEM prep timelines (CEM requires more comprehension work from the start)
  - Month 1 should include a diagnostic test to identify weak areas
  - Month 5 should include at least 3 full timed mock exams
  - Final week: light revision only, prioritise sleep and confidence
  - Mention that tutoring can help but parental involvement is also key
- Include one short bullet list elsewhere in the post
- FAQ questions must address: when to start 11+ preparation for Year 5 vs Year 6, how many hours per week to study, whether to use a tutor, and how to handle a child who is anxious about the test
"""

    if slug == "creative-writing-for-the-11-plus-how-to-score-in-the-top-5":
        return f"""
{master_context}

Before writing, think through:
1. What actually distinguishes top-5% 11+ creative writing responses from merely competent ones?
2. What structures and techniques do high-scoring students consistently use?
3. What errors do most children make that immediately place them in the average band?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must challenge the misconception that creative writing is about imagination alone — structure and technique matter just as much
- Include these exact <h2> sections in this order:
  1. Why Creative Writing Matters in the 11 Plus
  2. What Markers Are Actually Looking For
  3. Structure: Opening, Development, and Ending
  4. Language Techniques That Impress Markers
  5. Common Types of 11 Plus Creative Writing Prompts
  6. How to Practise Effectively
  7. Frequently Asked Questions
- Must include:
  - Section 4 must include a <ul> of at least 8 specific techniques: e.g. varied sentence length, show don't tell, sensory detail, rule of three, simile/metaphor, direct speech, paragraph control, cyclical endings
  - Markers want a clear narrative arc — not a rambling stream of ideas
  - A strong opening line is disproportionately important — spend time on it
  - Vocabulary range matters: use precise verbs, avoid overused adjectives (nice, big, good)
  - Children should practise writing 300-400 words in 25-30 minutes under timed conditions
  - Reading quality fiction is the single best long-term preparation
- Include one short bullet list elsewhere in the post
- FAQ questions must address: how long the creative writing section is, whether there is a word minimum, how to improve vocabulary, and how many creative writing pieces to practise before the exam
"""

    if slug == "grammar-school-vs-private-school-which-is-best-for-your-child":
        return f"""
{master_context}

Before writing, think through:
1. What are the genuine differences between grammar schools and private schools — academically, socially, and financially?
2. What factors should actually determine the choice — and what factors are overrated?
3. In what situations is one clearly better than the other?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must acknowledge that this is a genuine dilemma for many families and that the answer is not universal
- Include these exact <h2> sections in this order:
  1. Grammar Schools vs. Private Schools: The Key Differences
  2. Academic Standards: A Fair Comparison
  3. Social Environment and Extracurricular Opportunities
  4. The Cost Question: Grammar vs. Fees
  5. Which Is Better for Oxbridge and Competitive University Entry?
  6. How to Decide What Is Right for Your Child
  7. Frequently Asked Questions
- Must include:
  - Section 1 must contain an HTML <table>: Factor, Grammar School, Private School — covering: cost, selectivity, academic focus, pastoral care, class sizes, sport and arts, diversity, 6th form options
  - Grammar schools are fully state-funded; top private schools charge £15,000-£45,000 per year
  - Academic outcomes at top grammars are comparable to selective independent schools
  - Private schools typically offer stronger extracurricular provision and smaller class sizes
  - Super-selective grammars (Tiffin, King Edward's, Henrietta Barnett) may out-perform mid-tier private schools
  - The choice often depends on geography: not all areas have grammar schools
- Include one short bullet list elsewhere in the post
- FAQ questions must address: which produces better university results, whether private school offers better pastoral support, how to decide between a grammar offer and a private school offer, and whether grammar school is really free
"""

    if slug == "is-the-11-plus-too-stressful-how-to-build-resilience-in-your-child":
        return f"""
{master_context}

Before writing, think through:
1. What does the research actually say about the psychological impact of 11+ preparation on children?
2. What parental behaviours make anxiety worse — and which genuinely help?
3. What practical strategies build resilience without simply dismissing the pressure?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must validate that the 11+ is genuinely stressful for some children — while also noting that the experience can build confidence when handled well
- Include these exact <h2> sections in this order:
  1. Is the 11 Plus Actually Too Stressful?
  2. Warning Signs That Preparation Has Become Counterproductive
  3. How Parents Accidentally Increase Anxiety
  4. Practical Strategies to Build Resilience
  5. Helping Children Cope with Exam Day Itself
  6. What to Do If Your Child Does Not Pass
  7. Frequently Asked Questions
- Must include:
  - Section 3 must be a <ul> of at least 6 specific parental behaviours that inadvertently add pressure (e.g. talking about results constantly, comparing to siblings, drilling for hours at weekends)
  - Section 4 must be a <ul> of at least 6 practical strategies: e.g. separating effort from outcome, normalising mistakes in practice, mindfulness or breathing techniques, celebrating small wins
  - Acknowledge that some children genuinely thrive on structured challenge; others need more support
  - Recommend speaking to teachers or a child psychologist if anxiety becomes clinical
  - The pass/fail framing is itself unhealthy — school fit matters more than the selective status
- Include one short bullet list elsewhere in the post
- FAQ questions must address: at what age preparation stress becomes harmful, whether to stop preparation if a child is very anxious, how to explain a failed result, and whether 11+ failure affects future outcomes
"""

    if slug == "the-new-esat-and-tmua-exams-a-preparation-guide-for-oxbridge-2026":
        return f"""
{master_context}

Before writing, think through:
1. What exactly are the ESAT and TMUA — and which courses and universities require each?
2. How do these exams differ from each other and from the tests they replaced (NSAA, ENGAA)?
3. What preparation strategies work best for each?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must immediately explain that 2026 applicants face a changed admissions test landscape and that getting confused between ESAT and TMUA is a costly mistake
- Include these exact <h2> sections in this order:
  1. What Are the ESAT and TMUA?
  2. Who Needs to Take Each Exam?
  3. ESAT: Format, Content, and Scoring
  4. TMUA: Format, Content, and Scoring
  5. How to Prepare for the ESAT
  6. How to Prepare for the TMUA
  7. Frequently Asked Questions
- Must include:
  - Section 2 must contain an HTML <table>: Subject/Course, University, Required Test — covering at least 8 subject-university combinations (e.g. Engineering at Cambridge → ESAT; Maths at Cambridge → TMUA optional but advantageous; Economics at Cambridge → TMUA; Physics at Cambridge → ESAT; Natural Sciences at Cambridge → ESAT; Maths at Oxford → MAT, not ESAT/TMUA; Engineering at Oxford → PAT)
  - ESAT replaced the ENGAA and NSAA in 2024; TMUA has been used since 2016 but expanded
  - ESAT has a core Mathematics 1 module plus subject-specific modules (Physics, Chemistry, Biology)
  - TMUA tests mathematical reasoning and application — not curriculum content directly
  - Both are scored on a 1-9 scale; typical competitive scores: TMUA 6.5+, ESAT equivalent
  - Free preparation materials available from Cambridge Assessment Admissions Testing
- Include one short bullet list
- FAQ questions must address: whether the ESAT replaces the NSAA, the difference between MAT and TMUA, how to access past papers, and whether a poor score prevents an offer
"""

    if slug == "oxbridge-interview-questions-100-real-examples-for-every-major-subject":
        return f"""
{master_context}

Before writing, think through:
1. What types of interview questions genuinely distinguish Oxbridge interviews from typical interviews?
2. What subject areas have the most distinctive or surprising question styles?
3. What do these questions reveal about what Oxbridge actually wants to see in candidates?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,400 to 1,800 words
- Opening paragraph must frame Oxbridge interviews as intellectual conversations, not knowledge tests — and explain what this means for how to answer
- Include these exact <h2> sections in this order:
  1. What Makes Oxbridge Interview Questions Different?
  2. Science and Engineering Questions
  3. Medicine and Biology Questions
  4. Mathematics Questions
  5. Humanities and Social Sciences Questions
  6. Law Questions
  7. Economics and PPE Questions
  8. How to Approach Any Oxbridge Question
  9. Frequently Asked Questions
- Must include:
  - Each subject section (2-7) must contain at least 6 specific example questions in a <ul> list — aiming for ~50 total across sections
  - For each section, include 1-2 sentences of commentary on what the interviewer is actually looking for
  - Emphasise: interviewers expect candidates to think out loud and be wrong — that is the point
  - Common trap: trying to reach a definitive answer quickly rather than exploring the question
  - Bring genuine curiosity — candidates who have done super-curricular reading often find these easier
  - Preparation: practise with past personal statement topics and subject-specific problem sets
- Include one short bullet list elsewhere in the post
- FAQ questions must address: whether there are "right" answers to Oxbridge interview questions, how long interviews last, whether you should memorise sample questions, and how to handle a question you genuinely cannot answer
"""

    if slug == "what-is-super-curricular-how-to-build-a-profile-for-oxford-and-cambridge":
        return f"""
{master_context}

Before writing, think through:
1. What is the difference between extracurricular and super-curricular — and why does this distinction matter so much for Oxbridge?
2. What actually counts as strong super-curricular engagement for different subjects?
3. What are common mistakes students make when trying to build a super-curricular profile?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must clearly define super-curricular and distinguish it from general extracurricular — this confusion is the most common mistake
- Include these exact <h2> sections in this order:
  1. What Is Super-Curricular Activity?
  2. Why Oxbridge Cares About Super-Curricular Engagement
  3. Super-Curricular Ideas by Subject
  4. How to Document and Reflect on Your Super-Curricular Activities
  5. How the New UCAS Format Changes Super-Curricular Evidence
  6. Common Mistakes to Avoid
  7. Frequently Asked Questions
- Must include:
  - Section 3 must be a <ul> list with at least 6 subject areas (Sciences, Maths, Medicine, Humanities, Social Sciences, Law) each with 3-4 specific examples of super-curricular activities
  - Distinction: extracurricular = sport, music, volunteering; super-curricular = reading beyond the syllabus, attending lectures, independent research, online courses related to your subject
  - The new UCAS 3-question format has a dedicated question for super-curricular engagement
  - Quality matters more than quantity: deep engagement with one topic beats a list of surface-level activities
  - Candidates should be prepared to discuss anything they mention in their UCAS answers during the interview
  - Reading recommendations: journals (Nature, The Economist, JSTOR), open courseware (MIT OpenCourseWare, Coursera)
- Include one short bullet list elsewhere in the post
- FAQ questions must address: what counts as super-curricular, whether work experience is super-curricular, how early to start, and whether free activities are as valid as paid ones
"""

    if slug == "oxford-vs-cambridge-which-university-is-easier-for-your-subject":
        return f"""
{master_context}

Before writing, think through:
1. Which subjects genuinely have different acceptance rates or requirements at Oxford vs. Cambridge?
2. What factors beyond acceptance rates should inform a subject-specific choice?
3. What are the biggest misconceptions students have when comparing the two universities?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph must acknowledge that neither is universally "easier" — but subject-specific data and structural differences genuinely matter
- Include these exact <h2> sections in this order:
  1. The Honest Answer: Neither Is Simply Easier
  2. Acceptance Rates by Subject: Oxford vs. Cambridge
  3. Structural Differences That Affect Your Application
  4. Admissions Tests: Where They Differ
  5. The Interview: How Each University Approaches It
  6. Which Should You Apply To for Your Subject?
  7. Frequently Asked Questions
- Must include:
  - Section 2 must contain an HTML <table>: Subject, Oxford Acceptance Rate (approx.), Cambridge Acceptance Rate (approx.), Key Difference — covering at least 8 subjects (Medicine, Maths, Law, Economics, English, History, Computer Science, Engineering)
  - Structural: Oxford uses more tutorial-based learning; Cambridge uses supervision system — similar in principle
  - Cambridge has Natural Sciences as a broad entry route; Oxford separates Physics, Chemistry, Biology
  - Cambridge does not use UCAT for Medicine; Oxford introduced UCAT from 2024
  - Application timing: both apply via UCAS, same deadline — but admissions test timing varies
  - Encourage candidates to choose based on course structure fit, not perceived ease
- Include one short bullet list
- FAQ questions must address: can you apply to both Oxford and Cambridge, which is more prestigious, which is harder for medicine, and whether college choice affects acceptance rate
"""

    if slug == "contextual-admissions-how-your-background-can-lower-your-offer-requirements":
        return f"""
{master_context}

Before writing, think through:
1. What is contextual admissions and how does it actually work in practice at UK universities?
2. Which factors count as contextual — and which universities are most transparent about how they use this information?
3. What do students with contextual flags need to do differently in their applications?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must explain contextual admissions clearly and directly — many students have never heard of it despite being eligible
- Include these exact <h2> sections in this order:
  1. What Is Contextual Admissions?
  2. Which Flags Are Used in Contextual Decisions?
  3. Which Universities Offer Contextual Reduced Offers?
  4. How Much Can Your Offer Be Reduced?
  5. Do You Need to Do Anything Differently?
  6. Frequently Asked Questions
- Must include:
  - Section 3 must contain an HTML <table>: University, Types of Contextual Flags Used, Typical Reduction — covering at least 6 universities (UCL, Bristol, Edinburgh, Manchester, Sheffield, Leeds)
  - Common contextual flags: care-leaver status, first generation to university, Polar4/TUNDRA quintile 1-2 postcodes, attending a low-performing school, Free School Meals
  - UCAS flags this automatically from postcode and school data — students do not always need to self-declare
  - Reductions can be 1-3 grade points below standard offer
  - Oxford, Cambridge, and Imperial also have contextual programmes (UNIQ, CUSU, Sutton Trust links)
  - Contextual data is not disclosed to applicants at every institution
- Include one short bullet list
- FAQ questions must address: how to find out if you qualify, whether contextual admission affects your degree experience, how to check your school's performance rating, and whether you should mention context in your personal statement
"""

    if slug == "is-private-tuition-worth-it-a-cost-benefit-analysis-of-1-to-1-learning":
        return f"""
{master_context}

Before writing, think through:
1. What does the research actually say about the effectiveness of private tuition on academic outcomes?
2. When is tuition most vs. least effective — and what makes the difference?
3. How should parents think about the cost relative to the likely benefit?

Now write a detailed blog post in HTML: {title}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must be balanced — acknowledge tuition is expensive and that it is not always necessary, while also presenting the evidence that it can significantly help
- Include these exact <h2> sections in this order:
  1. The Evidence for Private Tuition
  2. When Tuition Makes the Most Difference
  3. When Tuition Is Less Likely to Help
  4. The Real Cost of Tuition: A Breakdown
  5. How to Get the Best Return on Tuition Investment
  6. Frequently Asked Questions
- Must include:
  - Reference EEF (Education Endowment Foundation) evidence: 1-to-1 tuition shows on average +5 months learning progress
  - Tuition is most effective when: child has specific gaps not addressed at school, preparing for high-stakes exams, working with an expert in a specialist subject
  - Cost range: £40-£80/hr for GCSE; £60-£100/hr for A-Level; £100-£200/hr for Oxbridge/admissions prep in London
  - Section 4 must include a simple cost scenario: e.g. 1 hour per week for 10 weeks at £60/hr = £600
  - Quality varies enormously: an Oxbridge-educated specialist tutor is not the same as a general undergraduate
  - Alternative: group tuition at lower cost per session may suit some learners
- Include one short bullet list
- FAQ questions must address: how to find a good tutor, how many sessions are typically needed, whether online tuition is as effective as in-person, and whether tuition is tax-deductible for businesses
"""

    # ── 11+ resource cluster posts ────────────────────────────────────────────

    if slug == "iseb-common-pre-test-a-parents-guide-for-2026":
        return f"""
{master_context}

Before writing, think through:
1. What is the ISEB Common Pre-Test and why do parents confuse it with the 11+?
2. Which prestigious independent schools use ISEB, and what does that mean for preparation?
3. What makes the adaptive, online ISEB format fundamentally different to practise for?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph: establish immediately that the ISEB pre-test and the 11+ are different assessments with different purposes — many families encounter both, some only one
- Include these exact <h2> sections in this order:
  1. What Is the ISEB Common Pre-Test?
  2. Which Schools Use the ISEB Pre-Test?
  3. How the ISEB Pre-Test Differs from the 11+
  4. What the ISEB Pre-Test Actually Tests
  5. How to Prepare Without Official Past Papers
  6. Frequently Asked Questions
- Must include:
  - ISEB tests four areas: English, Maths, Verbal Reasoning, Non-Verbal Reasoning — online, adaptive, multiple-choice
  - Used by schools including Eton, Harrow, Winchester, Marlborough, Sevenoaks, Tonbridge, and many London independents
  - ISEB does not release past papers — only official familiarisation materials exist
  - Adaptive format means harder questions follow correct answers; standard timed paper practice does not replicate this
  - Families often sit both ISEB and school-specific 11+ papers — preparation overlaps significantly for Maths and VR/NVR
  - At a natural point where familiarisation materials or practice papers are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">ISEB familiarisation papers and other independent school 11+ past papers</a>
- FAQ questions must address: when the ISEB is typically sat (Year 6, autumn term), whether a child can resit, how long preparation should take, and whether a high ISEB score guarantees a school place
"""

    if slug == "the-north-london-girls-schools-11-what-parents-need-to-know":
        return f"""
{master_context}

Before writing, think through:
1. What is the North London independent school landscape — which schools share a consortium paper and which set their own?
2. What do parents in North London genuinely struggle to understand about these admissions processes?
3. How does selectivity vary across South Hampstead, NLCS, Channing, Highgate Girls, and The Latymer School?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph: acknowledge that North London has one of the most competitive independent school 11+ landscapes in the country, with several schools sharing consortium papers while others set their own
- Include these exact <h2> sections in this order:
  1. Which Schools Are in the North London Girls' Consortium?
  2. What the Consortium 11+ Paper Tests
  3. How Selective Are These Schools — Really?
  4. Schools Outside the Consortium: South Hampstead, NLCS and The Latymer School
  5. How to Pace Preparation Across Multiple Schools
  6. Frequently Asked Questions
- Must include:
  - The main consortium schools include Channing, Highgate Girls, Channing, City of London Girls and others — the consortium uses a shared paper
  - South Hampstead High School and North London Collegiate set their own papers and are among the most academically selective girls' schools in the country
  - The Latymer School is a state selective school with its own process — mention briefly as context
  - The consortium format typically includes English comprehension, creative writing, and Maths
  - Selective ratios: some consortium schools receive 8–10 applicants per place; NLCS and SHHS are even more competitive
  - At a natural point where practice papers or past exam materials are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">past papers from consortium schools and other North London independents</a>
- FAQ questions must address: whether consortium schools interview all applicants, whether creative writing is marked on style or content, what Year 6 looks like for a child preparing for multiple schools, and whether it is worth applying to both consortium and non-consortium schools
"""

    if slug == "manchester-grammar-school-11-format-past-papers-and-how-to-prepare":
        return f"""
{master_context}

Before writing, think through:
1. What makes Manchester Grammar School academically distinctive — it's non-selective on wealth, highly competitive on ability
2. How does the MGS 11+ exam format differ from GL Assessment, CEM, and other local options?
3. What do parents in Manchester underestimate when preparing a child for MGS?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph: establish that MGS is one of the most academically selective independent schools in the north of England — and that its 11+ exam is set in-house, not by GL or CEM, which changes how to prepare
- Include these exact <h2> sections in this order:
  1. About Manchester Grammar School
  2. The MGS 11+ Examination: Format and Structure
  3. What the MGS Exam Tests — and What It Doesn't
  4. How Competitive Is Entry to Manchester Grammar?
  5. Building an Effective Preparation Plan
  6. Frequently Asked Questions
- Must include:
  - MGS is academically non-selective on wealth but highly selective on ability — means-tested bursaries available
  - The exam is set by MGS itself, not by GL Assessment or CEM — this means generic 11+ practice is useful but not sufficient
  - The exam tests Maths, English, and reasoning — but the style of questions is more demanding and less formulaic than GL-style papers
  - Entry is typically from Year 6 with the exam sat in January of Year 6
  - Boys only — one of the best-performing independent schools in the north of England by A-Level outcomes and Oxbridge send rate
  - At a natural point where past papers are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">Manchester Grammar past papers from recent sittings</a>
- FAQ questions must address: whether tutoring is necessary for MGS entry, what score is needed to pass, how the MGS exam compares to the Trafford consortium grammar school exams, and whether there is a waiting list or appeal process
"""

    if slug == "fsce-11-exam-2026-what-it-is-and-how-to-prepare":
        return f"""
{master_context}

Before writing, think through:
1. What is FSCE (Future Stories Community Enterprise) and why are some areas replacing GL Assessment with it?
2. What makes the FSCE format genuinely harder to prepare for than GL or CEM?
3. What does the "Discovery Paper" creative writing element mean for preparation?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph: establish that FSCE is a new exam board replacing GL Assessment at several English grammar schools from 2025 onwards — and that parents searching for FSCE past papers will find almost nothing, which is by design
- Include these exact <h2> sections in this order:
  1. What Is the FSCE 11+?
  2. Which Schools Have Switched to FSCE?
  3. How FSCE Differs from GL Assessment and CEM
  4. What the FSCE Tests: KS2 Maths, English, and the Discovery Paper
  5. How to Prepare for the FSCE Without Past Papers
  6. Frequently Asked Questions
- Must include:
  - FSCE stands for Future Stories Community Enterprise — a newer provider designed to reduce the "drillability" of 11+ preparation
  - Schools that have adopted or are moving to FSCE include Reading School, Kendrick, Chelmsford County High, KEGS, and others
  - FSCE deliberately does not publish past papers — the format is designed to change year-on-year
  - No standalone Verbal Reasoning or Non-Verbal Reasoning section — replaced by integrated KS2-level Maths and English tasks
  - The Discovery Paper is an extended creative or reflective writing task — assessed for ideas and communication, not grammar drilling
  - Preparation should focus on: strong KS2 Maths and English, reading widely, practising timed writing to prompts
  - At a natural point where practice materials are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">KS2-style Maths and English practice papers that provide a useful starting point</a>
- FAQ questions must address: whether FSCE is harder than GL Assessment, what year to start preparation, whether a child who has been doing GL practice needs to change their approach, and what the FSCE pass mark is
"""

    if slug == "11-english-comprehension-question-types-mark-schemes-and-practice-advice":
        return f"""
{master_context}

Before writing, think through:
1. What are the distinct question types in 11+ English comprehension, and how are they marked differently?
2. What are the specific techniques for inference questions that children consistently get wrong?
3. How does comprehension style vary between independent schools — and why does this matter for practice?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph: establish that comprehension is the section where marks are most commonly dropped — not because children misunderstand the passage, but because they don't understand how different question types are marked
- Include these exact <h2> sections in this order:
  1. The Main Types of 11+ Comprehension Questions
  2. Retrieval Questions: Finding and Quoting Accurately
  3. Inference Questions: Reading Between the Lines
  4. Vocabulary Questions: Beyond Simple Definitions
  5. How Marks Are Awarded — and Where They Are Lost
  6. How to Practise Comprehension Effectively
  7. Frequently Asked Questions
- Must include:
  - The four core question types: retrieval (find it in the text), inference (implied meaning), vocabulary (in context), author's craft/language analysis
  - Retrieval: children must quote or paraphrase directly — generic statements about the passage lose marks
  - Inference: the most commonly dropped marks — children must explain why the author has implied something, not just state it
  - Vocabulary in context: definitions alone are rarely enough — the mark scheme wants the word's meaning in this specific context
  - Mark allocation: 1-mark vs 2-mark questions require very different answer lengths
  - Comprehension styles vary between schools — some independents favour inference-heavy passages; others weight vocabulary more heavily
  - At a natural point where practice is discussed, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">English past papers from schools including Dulwich, Bancroft's and The Perse, which show how comprehension style varies between institutions</a>
- FAQ questions must address: how long a comprehension answer should be, whether underlining helps, how to improve inference skills specifically, and whether the same comprehension skills apply to all 11+ providers (GL, CEM, independent schools)
"""

    if slug == "is-my-child-on-track-for-the-11-a-year-by-year-readiness-guide":
        return f"""
{master_context}

Before writing, think through:
1. What does "on track" genuinely mean at each year group — and why do parents misjudge it?
2. What are the reliable indicators vs the misleading ones (e.g. school performance is not always a good proxy)?
3. How should a parent use past papers as a calibration tool, not just as drilling?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph: acknowledge that this is one of the most common and least well-answered questions in 11+ preparation — most resources tell you what to do, not how to know if it's working
- Include these exact <h2> sections in this order:
  1. Why "On Track" Is Harder to Define Than It Sounds
  2. Year 3 and Year 4: What Strong Early Foundations Look Like
  3. Year 5: The Critical Calibration Year
  4. Using Past Papers to Benchmark Honestly
  5. Red Flags: When to Reassess the Plan
  6. Frequently Asked Questions
- Must include:
  - "On track" depends entirely on which school the child is targeting — a score that comfortably passes for one school may fall short at another
  - School performance (e.g. reading age, SATS projections) is a useful but imperfect proxy — 11+ tests skills that are not always covered in the classroom
  - Year 5 is when most reliable benchmarking begins — Year 4 is too early for timed paper data to be meaningful
  - A useful rule: if a child scores consistently above 75% on timed past papers from target-level schools in Year 5, preparation is on track; below 60% consistently suggests a structural gap, not a motivation problem
  - Red flags: consistent time pressure (finishing fewer than 80% of questions), strong on one section and very weak on another, visible anxiety during timed practice
  - At a natural point where past papers as benchmarking tools are discussed, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">past papers spanning a range of selectivity levels, from competitive independents to highly selective London consortium schools</a>
- FAQ questions must address: what to do if a child plateaus in Year 5, whether mock exams are more reliable than past papers, whether Year 4 preparation is too early, and what "strong" vs "borderline" looks like in practice
"""

    if slug == "11-answer-sheet-practice-how-to-fill-in-bubble-sheets-and-avoid-costly-mistakes":
        return f"""
{master_context}

Before writing, think through:
1. Why do children who know the correct answers still lose marks on answer sheets — what are the specific failure modes?
2. How do different 11+ providers and independent schools structure their answer sheets differently?
3. What does realistic answer-sheet practice look like, and how early should it start?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,000 to 1,300 words
- Opening paragraph: make clear this is a genuinely underrated preparation step — answer sheet errors can cost 3–8 marks on a paper a child otherwise answered correctly, which at competitive schools is the difference between a pass and a fail
- Include these exact <h2> sections in this order:
  1. Why Answer Sheets Cause Problems — Even for Well-Prepared Children
  2. Types of 11+ Answer Sheets: Bubble Grids, Multiple Choice, and Separate Booklets
  3. The Most Common Answer Sheet Mistakes
  4. How to Practise Answer Sheets Effectively
  5. Timing: Managing Pace Across Paper and Answer Sheet Together
  6. Frequently Asked Questions
- Must include:
  - The core failure modes: skipping a question but continuing on the answer sheet (misalignment), rushing at the end and circling without checking, using the wrong answer format (e.g. circling instead of shading)
  - Different formats: GL Assessment uses separate multiple-choice answer sheets with bubble grids; independent schools often use separate lined booklets; CEM varies
  - Children should practise under timed conditions with the actual answer sheet format for their target school — not just on paper with a pen next to each question
  - Good practice habit: mark every question before moving on — do not leave blanks to return to without also leaving a matching blank on the answer sheet
  - At a natural point where paper formats are discussed, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">past papers from a range of independent and selective schools, many of which include separate answer booklets</a>
- FAQ questions must address: whether multiple-choice answers can be changed once marked, at what age to introduce answer-sheet practice, whether GL and CEM answer sheets differ significantly, and how much time to allow for transferring answers
"""

    # ── Oxbridge Interview Questions blog posts ───────────────────────────────
    if slug == "oxford-maths-interview-questions-2026-with-step-by-step-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. What question types genuinely appear in Oxford Maths interviews — pure problems, graph sketching, proof, applied/mechanics — and how does the difficulty gradient work?
2. What does "thinking aloud" look like for a Maths problem, and why do tutors reward process over correct answers?
3. How does Oxford Maths style differ from Cambridge Maths interview style?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph (40–60 words): direct answer — what Oxford Maths interviews test, who does them, and how this post helps. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Are the Most Common Oxford Maths Interview Question Types in 2026?
  2. Pure Maths Problems: 4 Real-Style Questions with Step-by-Step Model Answers
  3. Graph Sketching and Curve Analysis: What Tutors Are Looking For
  4. Applied and Mechanics Questions: 3 Worked Examples
  5. Oxford vs Cambridge Maths Interviews: Key Style Differences
  6. How to Think Aloud When You Get Stuck
  7. Frequently Asked Questions
- Must include:
  - A table: Question Type | Example question | What tutors reward | Common mistake
  - 6–8 embedded practice questions with model answer frameworks (not just the answer — the reasoning steps)
  - Concrete advice on graph sketching: check intercepts, behaviour as x→∞, stationary points
  - The thinking-aloud principle: saying "I don't know this yet, but I know that..." is better than silence
  - Oxford style emphasises novel problems from first principles; Cambridge slightly more structured scaffolding
  - At a natural point where preparation materials are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">past Oxford Maths interview questions with worked solutions</a>
- FAQ must address: whether calculators are allowed, how long Oxford Maths interviews last, whether STEP preparation helps, and what to do when completely stuck
"""

    if slug == "cambridge-medicine-interview-questions-2026-science-questions-and-how-to-answer-them":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Medicine interviews are more science-heavy than MMI-style ethical interviews — what specific science problem types appear (mechanisms, data interpretation, "why doesn't X happen?" questions)?
2. How does the Cambridge Medicine interview differ from Oxford Medicine and from standard MMI interviews at other schools?
3. What does a strong science answer look like — how do tutors want students to think through unfamiliar biological or chemical mechanisms?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph (40–60 words): direct answer — Cambridge Medicine interviews are science-first, not ethics-first. What to expect and how this post prepares you. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Makes Cambridge Medicine Interviews Different from Other Medical Interviews?
  2. The Most Common Cambridge Medicine Question Types in 2026
  3. Classic Science Questions: 5 Real-Style Examples with Model Answers
  4. Data and Graph Interpretation: How to Structure Your Response
  5. Ethics and Personal Statement Questions at Cambridge
  6. How Cambridge Medicine Interviews Differ by College
  7. Frequently Asked Questions
- Must include:
  - A table: Question type | Example | Model answer key points | What Cambridge tutors reward
  - Classic Cambridge Medicine question patterns: "Why don't fish freeze?", mechanism questions, "How many X are in Y?" estimation questions
  - Contrast with Oxford Medicine (more philosophy/ethics mix) and MMI-format schools
  - Science answer framework: state what you know → identify the gap → reason from first principles → check your logic aloud
  - College variation: some Cambridge colleges use one interviewer, others two; science weighting varies
  - At a natural point where preparation materials are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Medicine interview questions from recent cycles</a>
- FAQ must address: whether Cambridge Medicine interviews include ethical scenarios, how many interviews candidates typically have, what the interviewers are looking for in science answers, and whether A-level content is sufficient
"""

    if slug == "oxford-ppe-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford PPE interviews test three disciplines — what question types appear for each (Philosophy: logic and thought experiments; Politics: current affairs + political theory; Economics: micro/macro concepts and data)?
2. How does Oxford PPE differ from similar multi-discipline interviews — what is the Oxford tutorial style and how does it show up in interview?
3. What does a strong PPE answer look like — how should candidates link 2026 current affairs to philosophical and economic frameworks?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph (40–60 words): direct answer — what Oxford PPE interviews test across all three disciplines, the tutorial format, and why model answers help. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Do Oxford PPE Interviews Actually Test in 2026?
  2. Philosophy Questions: Logic Problems and Thought Experiments with Model Answers
  3. Politics Questions: Current Affairs and Political Theory — 4 Real-Style Examples
  4. Economics Questions: Microeconomics, Data and Opportunity Cost Problems
  5. Linking Current Affairs to PPE Frameworks: A 2026 Cheat Sheet
  6. How Oxford PPE Interviews Are Structured and What to Expect
  7. Frequently Asked Questions
- Must include:
  - A table: Discipline | Example question | Framework to use | What tutors reward
  - Philosophy examples: thought experiments (trolley problem variations, personal identity), syllogisms, logic puzzles
  - Politics examples: 2026-relevant topics (AI regulation, fiscal policy) linked to social contract, legitimacy, democratic theory
  - Economics examples: supply/demand shifts, opportunity cost problems, interpreting a simple graph or statistic
  - The cheat sheet: 3–4 current 2026 news items mapped to core PPE concepts
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford PPE and philosophy interview questions with model answers</a>
- FAQ must address: whether candidates need prior economics A-level, how many Oxford PPE interviews candidates have, whether interviewers share questions across colleges, and how much current affairs knowledge is required
"""

    if slug == "oxford-vs-cambridge-interview-key-differences-by-subject-2026":
        return f"""
{master_context}

Before writing, think through:
1. What are the genuine structural differences between Oxford and Cambridge interviews (format, number, length, use of material, college variation)?
2. For each major subject — Maths, Medicine, PPE/HSS, Law, Natural Sciences/Physics — how does the question style and emphasis differ between the two universities?
3. What should a candidate do differently in preparation depending on whether they applied to Oxford or Cambridge?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph (40–60 words): direct answer — Oxford and Cambridge both use subject-based interviews, but the style, format, and emphasis differ in ways that matter for preparation. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. Oxford vs Cambridge Interview Format: Structure, Length, and Number of Interviews
  2. Maths: Oxford First Principles vs Cambridge Scaffolded Problems
  3. Medicine: Oxford's Ethics Mix vs Cambridge's Science Focus
  4. Law: Oxford Unseen Passages vs Cambridge Legal Logic
  5. Sciences and Engineering: How Practical and Theoretical Questions Differ
  6. PPE, History, and Humanities: Tutorial-Style vs Supervision-Style Questions
  7. Frequently Asked Questions
- Must include:
  - A master comparison table: Subject | Oxford style | Cambridge style | Key preparation difference
  - Concrete examples of a question type for each university per subject
  - The college variation point: both universities show significant college-to-college variation — candidates should research their specific college
  - Practical takeaways: "If you applied to Oxford Maths, prioritise X; if Cambridge Maths, prioritise Y"
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">subject-specific Oxford and Cambridge interview questions and model answers</a>
- FAQ must address: whether candidates can apply to both Oxford and Cambridge (they cannot), how to find college-specific interview styles, whether subject choice affects the number of interviews, and whether interview performance outweighs predicted grades
"""

    if slug == "cambridge-law-interview-questions-2026-real-examples-and-how-to-structure-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Law interviews emphasise legal reasoning from first principles — what question types appear (unseen statutes, logic puzzles, hypothetical scenarios, reading comprehension under time pressure)?
2. How does Cambridge Law differ from Oxford Law interviews — and from law interviews at other universities like UCL or LSE?
3. What does a strong Cambridge Law answer look like — how should candidates apply legal logic to a scenario they have never seen before?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph (40–60 words): direct answer — Cambridge Law interviews test legal reasoning, not legal knowledge. What to expect and how to prepare. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Cambridge Law Interviews Actually Test in 2026
  2. Unseen Statute Questions: A Step-by-Step Model Answer Walkthrough
  3. Legal Logic and Hypothetical Scenarios: 4 Real-Style Questions with Answers
  4. Reading Comprehension Under Time Pressure: How to Handle Pre-Interview Material
  5. Cambridge Law vs Oxford Law: Interview Style Differences
  6. How to Structure Any Cambridge Law Answer in 4 Steps
  7. Frequently Asked Questions
- Must include:
  - A worked example of an unseen statute question: present a short fictional law, then walk through how to apply it to 2–3 scenarios step by step
  - A table: Question type | Example | Answer structure | Common mistake
  - The 4-step framework: Identify the legal issue → Find the relevant rule → Apply the rule to the facts → Identify any ambiguity or edge case
  - Cambridge Law interviews often use pre-read material (a short passage given 10–20 minutes before) — explain how to use this time
  - Cambridge slightly more focused on textual analysis; Oxford slightly more on philosophical foundations of law
  - At a natural point where preparation materials are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Law interview questions with structured model answers</a>
- FAQ must address: whether a Law A-level is required or useful, how many Cambridge Law interviews candidates typically have, whether interviewers share reading materials in advance universally, and how legal ethics questions are handled
"""

    if slug == "oxford-physics-interview-questions-2026-estimation-problems-and-worked-solutions":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Physics interviews test both conceptual understanding and problem-solving — what question types appear (Fermi estimation, mechanics, electromagnetism, dimensional analysis, data interpretation)?
2. What does a strong Fermi estimation look like — what values should physics candidates have memorised, and how do you sanity-check an order-of-magnitude answer?
3. How does Oxford Physics interview style relate to PAT preparation, and what goes beyond PAT-level difficulty?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph (40–60 words): direct answer — Oxford Physics interviews combine conceptual questions with novel problem-solving. No calculators, no formula sheets — just reasoning aloud. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Physics Interviews Test in 2026
  2. Fermi Estimation Questions: 4 Real-Style Examples with Worked Solutions
  3. Mechanics and Classical Physics: Step-by-Step Model Answers
  4. Conceptual Questions: How Tutors Test Deep Understanding
  5. The Sanity Check List: Values Every Oxford Physics Applicant Should Know
  6. How Oxford Physics Interviews Differ from PAT Preparation
  7. Frequently Asked Questions
- Must include:
  - The sanity check list: radius of Earth (~6,400 km), mass of a proton (~1.67×10⁻²⁷ kg), Avogadro's number, speed of light, atmospheric pressure — presented as a concise reference table
  - 3–4 Fermi estimation examples with full reasoning: "How many piano tuners in London?", "What is the mass of air in this room?", "How many heartbeats in a lifetime?"
  - Conceptual example: a counterintuitive result the candidate must reason through (e.g. a ball on a rotating turntable, tension in a rope over a pulley)
  - Oxford Physics interviews often go beyond PAT — expect unfamiliar scenarios where process matters more than the answer
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Physics interview questions including estimation and mechanics problems</a>
- FAQ must address: whether the PAT is used during Oxford Physics interviews, how long Oxford Physics interviews last, whether candidates are expected to know university-level content, and how to handle being given a question outside A-level syllabus
"""

    if slug == "the-hardest-oxford-and-cambridge-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. What makes a question genuinely "hard" in an Oxbridge interview — is it mathematical difficulty, philosophical ambiguity, the need to synthesise across fields, or the expectation of no right answer?
2. What does a high-scoring response to an impossible or open-ended question look like — how do tutors reward structured uncertainty?
3. Which subjects produce the most notorious interview questions, and what patterns appear across the hardest ones?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph (40–60 words): direct answer — the hardest Oxford and Cambridge questions are hard not because the answers are obscure, but because they require structured thinking under pressure. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. Why Oxford and Cambridge Ask Questions You Can't Fully Answer
  2. The Hardest Maths and Science Questions — with Model Answer Frameworks
  3. The Hardest Humanities and Social Science Questions — with Reasoning Guides
  4. Medicine and Interdisciplinary Curveballs — Classic Stumpers Explained
  5. How to Stay Composed When You Don't Know the Answer
  6. What Separates a Top Answer from an Average One
  7. Frequently Asked Questions
- Must include:
  - At least 8 genuinely hard questions spread across subjects, each with a model answer framework (not just the answer — the approach)
  - A table: Question | Subject | Why it's hard | What a top answer includes
  - The "structured uncertainty" framework: say what you know → identify the gap → reason from adjacent knowledge → state your conclusion with appropriate confidence
  - Subject-specific examples: Maths (non-standard proof), Philosophy (free will paradox), Medicine (ethical dilemma with scientific uncertainty), PPE (policy tradeoff with no clear winner)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">the full bank of Oxford and Cambridge interview questions with model answers</a>
- FAQ must address: whether interviewers deliberately ask unanswerable questions, how to tell when to move on from a question you're stuck on, whether getting a question wrong disqualifies a candidate, and whether the hardest questions are the most important ones
"""

    if slug == "how-to-answer-oxford-interview-questions-when-you-dont-know-the-answer":
        return f"""
{master_context}

Before writing, think through:
1. What does thinking-aloud look like in an Oxford interview — what is the actual verbal process that tutors reward, and how does it differ from just attempting to produce the right answer?
2. What are the common failure modes when a candidate doesn't know an answer (silence, giving up, guessing randomly) versus the productive responses?
3. How does this skill vary by subject — what does thinking aloud look like for a Maths problem vs a Philosophy question vs a Medicine ethics scenario?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,000 to 1,300 words
- Opening paragraph (40–60 words): direct answer — getting a question wrong does not disqualify you. Oxford interviewers deliberately give questions candidates can't fully answer to see how they think. Include "Updated March 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. Why Oxford Interviewers Ask Questions You Can't Answer (On Purpose)
  2. The Thinking-Aloud Framework: What to Say When You Don't Know
  3. Maths and Sciences: How to Reason Through an Unfamiliar Problem
  4. Humanities and PPE: How to Structure an Argument You're Building in Real Time
  5. What Not to Do: The Most Common Mistakes Under Pressure
  6. Practising Thinking Aloud: A 5-Step Method
  7. Frequently Asked Questions
- Must include:
  - The explicit thinking-aloud script: "I haven't seen this before, but I know that [adjacent fact] — so if I apply [principle], then..."
  - A worked example of a candidate reasoning through a Maths problem they don't immediately know how to solve
  - A worked example of a candidate building a Philosophy argument in real time
  - The "wrong answer, right thinking" principle — a real-style scenario where a candidate gets the answer wrong but demonstrates strong reasoning
  - Common mistakes: giving up and saying "I don't know", confidently guessing, asking the interviewer for the answer, staying silent for more than a few seconds
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford and Cambridge interview questions that test how you think under pressure</a>
- FAQ must address: how long candidates are expected to spend on a problem before asking for a hint, whether silence is ever appropriate, how to practise thinking aloud at home, and whether this technique works the same way at Cambridge
"""

    # Generic blog prompt for remaining posts
    return f"""
{master_context}

Before writing, think through:
1. What does a UK parent or student searching for "{keyword}" actually want to know?
2. What are the 3 most important practical points they need — and what are common misconceptions?
3. What UK-specific context (exam boards, year groups, school types, qualification levels) makes this genuinely useful?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,100 to 1,400 words
- Opening paragraph must directly and concisely answer the core question the title poses
- Include at least 5 <h2> sections, the last being Frequently Asked Questions
- Include one short bullet or numbered list
- Include specific UK context throughout: exam boards, year groups, grade systems, school types
- FAQ questions must be questions a parent or student would realistically search for
- Do not pad — every sentence must be genuinely useful
- End with a brief natural closing paragraph

After all HTML content, on a new line, output exactly 5 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}},{{"q":"Question five","a":"Answer five"}}]
"""


BLOG_RELATED_RESOURCES = {
    "ucat-score-requirements-for-uk-medical-schools-2025": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation with Leading Tuition', "
        "and link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub'."
    ),
    "how-to-prepare-for-a-medical-school-mmi-interview": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the MMI coaching page at /services/specialist-admissions/mmi-interview-coaching using anchor text 'MMI interview coaching', "
        "and link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation'."
    ),
    "what-is-the-11-plus-exam": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the Maths tutor page at /services/subjects/maths-tutor using anchor text 'specialist Maths tutoring'."
    ),
    "how-long-does-gcse-revision-take": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the GCSE tuition page at /services/levels/gcse-tuition using anchor text 'GCSE tuition with Leading Tuition', "
        "and link to the Maths tutor page at /services/subjects/maths-tutor using anchor text 'specialist GCSE Maths tutoring'."
    ),
    "triple-vs-double-science-gcse": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the GCSE tuition page at /services/levels/gcse-tuition using anchor text 'GCSE tuition', "
        "and link to the Chemistry tutor page at /services/subjects/chemistry-tutor using anchor text 'Chemistry tutoring'."
    ),
    "online-tutoring-vs-in-person-tutoring-for-gcse": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the GCSE tuition page at /services/levels/gcse-tuition using anchor text 'GCSE tuition with Leading Tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation'."
    ),
    "a-level-subject-choices-for-medicine-applications": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub', "
        "link to the A-Level tuition page at /services/levels/a-level-tuition using anchor text 'A-Level tuition with Leading Tuition', "
        "and link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation'."
    ),
    "ucas-personal-statement-guide": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the University Personal Statement page at /services/specialist-admissions/university-personal-statement using anchor text 'personal statement support with Leading Tuition', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation'."
    ),
    "what-grade-do-you-need-for-oxbridge-chemistry": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation', "
        "and link to the Chemistry tutor page at /services/subjects/chemistry-tutor using anchor text 'specialist Chemistry tutoring'."
    ),
    "how-to-find-a-good-private-tutor": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the GCSE tuition page at /services/levels/gcse-tuition using anchor text 'GCSE tuition', "
        "link to the A-Level tuition page at /services/levels/a-level-tuition using anchor text 'A-Level tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation'."
    ),
    # ── New blog posts (Phase C) ──────────────────────────────────────────────
    "the-new-ucas-personal-statement-2026-a-guide-to-the-3-question-format": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the University Personal Statement page at /services/specialist-admissions/university-personal-statement using anchor text 'personal statement support with Leading Tuition', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation'."
    ),
    "ucat-cut-offs-for-every-uk-medical-school-5-year-trends-and-2026-predictions": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation with Leading Tuition', "
        "link to the Medical School Guides hub at /medical-schools/ using anchor text 'medical school entry guides', "
        "and link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub'."
    ),
    "oxford-cambridge-and-ucl-medicine-mastering-the-ucat-for-elite-universities": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation with Leading Tuition', "
        "link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxbridge interview preparation', "
        "and link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub'."
    ),
    "low-ucat-score-top-5-strategic-uk-medical-schools-to-apply-to-in-2026": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation with Leading Tuition', "
        "link to the Medical School Guides hub at /medical-schools/ using anchor text 'medical school entry guides', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation to discuss your UCAT score'."
    ),
    "mmi-interviews-2026-50-real-scenarios-and-model-answer-frameworks": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the MMI coaching page at /services/specialist-admissions/mmi-interview-coaching using anchor text 'MMI interview coaching with Leading Tuition', "
        "link to the Medical School Interviews page at /services/specialist-admissions/medical-school-interviews/ using anchor text 'medical school interview preparation', "
        "and link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub'."
    ),
    "medical-schools-that-dont-care-about-gcses-a-strategic-selection-guide": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Medical School Guides hub at /medical-schools/ using anchor text 'complete medical school entry guides', "
        "link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'UCAT preparation with Leading Tuition', "
        "and link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub'."
    ),
    "how-to-get-2800-in-the-ucat-a-week-by-week-revision-roadmap": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the UCAT preparation page at /services/specialist-admissions/ucat-tutor using anchor text 'specialist UCAT tuition with Leading Tuition', "
        "and link to the Medicine Preparation hub at /services/specialist-admissions/medicine-prep-hub using anchor text 'Medicine Preparation hub'."
    ),
    "2026-grammar-school-league-tables-top-schools-ranked-by-gcse-results": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the GCSE tuition page at /services/levels/gcse-tuition using anchor text 'GCSE tuition'."
    ),
    "11-plus-pass-marks-by-region-how-high-do-you-need-to-score": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free 11+ consultation'."
    ),
    "gl-assessment-vs-cem-vs-local-school-exams-the-2026-format-guide": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the Maths tutor page at /services/subjects/maths-tutor using anchor text 'specialist Maths tutoring'."
    ),
    "the-6-month-11-plus-countdown-a-monthly-study-milestone-plan": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation to discuss your 11+ preparation'."
    ),
    "creative-writing-for-the-11-plus-how-to-score-in-the-top-5": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the English tutor page at /services/subjects/english-tutor using anchor text 'specialist English tutoring'."
    ),
    "grammar-school-vs-private-school-which-is-best-for-your-child": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation to discuss school options'."
    ),
    "is-the-11-plus-too-stressful-how-to-build-resilience-in-your-child": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation'."
    ),
    "the-new-esat-and-tmua-exams-a-preparation-guide-for-oxbridge-2026": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the ESAT preparation page at /admissions-tests/esat-preparation/ using anchor text 'ESAT preparation with Leading Tuition', "
        "link to the TMUA preparation page at /admissions-tests/tmua-preparation/ using anchor text 'TMUA preparation with Leading Tuition', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation'."
    ),
    "oxbridge-interview-questions-100-real-examples-for-every-major-subject": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'subject-specific Oxbridge interview preparation', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation with Leading Tuition'."
    ),
    "what-is-super-curricular-how-to-build-a-profile-for-oxford-and-cambridge": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation', "
        "link to the University Personal Statement page at /services/specialist-admissions/university-personal-statement using anchor text 'personal statement support', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxbridge interview preparation'."
    ),
    "oxford-vs-cambridge-which-university-is-easier-for-your-subject": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxbridge interview preparation by subject', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation with Leading Tuition'."
    ),
    "contextual-admissions-how-your-background-can-lower-your-offer-requirements": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the University Personal Statement page at /services/specialist-admissions/university-personal-statement using anchor text 'personal statement support with Leading Tuition', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation'."
    ),
    "is-private-tuition-worth-it-a-cost-benefit-analysis-of-1-to-1-learning": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the GCSE tuition page at /services/levels/gcse-tuition using anchor text 'GCSE tuition with Leading Tuition', "
        "link to the A-Level tuition page at /services/levels/a-level-tuition using anchor text 'A-Level tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free consultation'."
    ),
    # ── New 11+ resource-driving blog posts ──────────────────────────────────
    "iseb-common-pre-test-a-parents-guide-for-2026": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the 11+ School Guides hub at /11-plus/ using anchor text '11+ school preparation guides'."
    ),
    "the-north-london-girls-schools-11-what-parents-need-to-know": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the 11+ resources page at /resources/11-plus using anchor text 'past papers from North London consortium schools and other independents'."
    ),
    "manchester-grammar-school-11-format-past-papers-and-how-to-prepare": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the 11+ resources page at /resources/11-plus using anchor text 'Manchester Grammar past papers and other selective school practice materials'."
    ),
    "fsce-11-exam-2026-what-it-is-and-how-to-prepare": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the 11+ School Guides hub at /11-plus/ using anchor text '11+ school preparation guides'."
    ),
    "11-english-comprehension-question-types-mark-schemes-and-practice-advice": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "link to the English tutor page at /services/subjects/english-tutor using anchor text 'specialist English tutoring', "
        "and link to the 11+ resources page at /resources/11-plus using anchor text 'English past papers from Dulwich, Bancroft\\'s, The Perse and other independent schools'."
    ),
    "is-my-child-on-track-for-the-11-a-year-by-year-readiness-guide": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the consultation page at /consultation using anchor text 'book a free 11+ consultation'."
    ),
    "11-answer-sheet-practice-how-to-fill-in-bubble-sheets-and-avoid-costly-mistakes": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition', "
        "and link to the 11+ resources page at /resources/11-plus using anchor text 'past papers from independent and selective schools, many including separate answer booklets'."
    ),
    # ── Oxbridge Interview Questions blog posts ───────────────────────────────
    "oxford-maths-interview-questions-2026-with-step-by-step-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Maths interview questions and worked solutions', "
        "and link to the Oxford Maths interview preparation page at /oxbridge-interviews/maths-interview/ using anchor text 'Oxford Maths interview preparation with Leading Tuition'."
    ),
    "cambridge-medicine-interview-questions-2026-science-questions-and-how-to-answer-them": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Medicine interview questions from recent cycles', "
        "and link to the Medicine interview preparation page at /oxbridge-interviews/medicine-interview/ using anchor text 'Oxbridge Medicine interview preparation with Leading Tuition'."
    ),
    "oxford-ppe-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford PPE and philosophy interview questions with model answers', "
        "and link to the PPE interview preparation page at /oxbridge-interviews/ppe-interview/ using anchor text 'Oxford PPE interview preparation with Leading Tuition'."
    ),
    "oxford-vs-cambridge-interview-key-differences-by-subject-2026": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'subject-specific Oxford and Cambridge interview questions', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation with Leading Tuition'."
    ),
    "cambridge-law-interview-questions-2026-real-examples-and-how-to-structure-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Law interview questions with model answers', "
        "and link to the Law interview preparation page at /oxbridge-interviews/law-interview/ using anchor text 'Oxbridge Law interview preparation with Leading Tuition'."
    ),
    "oxford-physics-interview-questions-2026-estimation-problems-and-worked-solutions": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Physics interview questions including estimation and mechanics problems', "
        "and link to the Physics interview preparation page at /oxbridge-interviews/physics-interview/ using anchor text 'Oxford Physics interview preparation with Leading Tuition'."
    ),
    "the-hardest-oxford-and-cambridge-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'the full bank of Oxford and Cambridge interview questions with model answers', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation with Leading Tuition'."
    ),
    "how-to-answer-oxford-interview-questions-when-you-dont-know-the-answer": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford and Cambridge interview questions that test how you think under pressure', "
        "and link to the Oxbridge Admissions Preparation page at /services/specialist-admissions/oxbridge-admissions-preparation using anchor text 'Oxbridge admissions preparation with Leading Tuition'."
    ),
}


def generate_blog_pages(limit=None, new_only=False):
    posts = load_csv("blog_topics.csv")
    if limit is not None:
        posts = posts[:limit]

    for row in posts:
        title = row["title"]
        keyword = row["keyword"]
        # Generate slug from title: lowercase, spaces to hyphens, strip punctuation
        import re as _re
        slug = title.lower()
        slug = _re.sub(r"[^\w\s-]", "", slug)
        slug = _re.sub(r"\s+", "-", slug).strip("-")

        blog_dir = OUTPUT_DIR / "blog"
        blog_dir.mkdir(parents=True, exist_ok=True)
        file_path = blog_dir / f"{slug}.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): blog/{slug}.html")
            continue

        # meta_desc priority: 1) manual override in CSV, 2) Claude-generated META_DESC: line,
        # 3) fallback formula. Never use generic title-only filler — it kills CTR.
        csv_meta_desc = row.get("meta_desc", "").strip()

        related_instruction = BLOG_RELATED_RESOURCES.get(slug, "")
        base_prompt = blog_prompt(title=title, keyword=keyword, slug=slug)
        prompt = base_prompt + (f"\n{related_instruction}" if related_instruction else "")
        raw = ask_claude(prompt, max_tokens=4000)
        content, faq_schema = parse_faq_schema(raw)

        # Resolve meta description
        if csv_meta_desc:
            meta_desc = csv_meta_desc
        else:
            ai_meta = parse_meta_desc(raw)
            meta_desc = ai_meta or (
                f"{title} — practical guidance for UK students and parents. "
                "Expert tutors from Oxford and Cambridge. 4.8/5 Trustpilot."
            )

        blogposting_schema = build_blogposting_schema(title, meta_desc, slug)
        schema_extra = faq_schema + "\n" + blogposting_schema
        html = blog_page_template(title=title, content=content, meta_desc=meta_desc, slug=slug, og_type="article", schema_extra=schema_extra)

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated blog post: {file_path}")


# ── Level page metadata ───────────────────────────────────────────────────────
LEVEL_METADATA = {
    "Primary": {
        "slug": "primary-tuition",
        "title": "Primary Tuition",
        "keyword": "primary school tutor",
        "meta_desc": "Primary school tutoring with Oxford and Cambridge-educated tutors. Maths, English and SATs preparation. 4.8/5 Trustpilot. Book a free consultation.",
    },
    "11+": {
        "slug": "11plus-tuition",
        "title": "11+ Tuition",
        "keyword": "11 plus tutor",
        "meta_desc": "11+ tutoring with Oxford and Cambridge-educated tutors. All subjects covered. AQA, Edexcel and OCR. 4.8/5 Trustpilot. Book a free consultation.",
    },
    "13+": {
        "slug": "13plus-tuition",
        "title": "13+ Tuition",
        "keyword": "13 plus tutor",
        "meta_desc": "13+ and Common Entrance tutoring with Oxford and Cambridge-educated tutors. All subjects covered. 4.8/5 Trustpilot. Book a free consultation.",
    },
    "GCSE": {
        "slug": "gcse-tuition",
        "title": "GCSE Tuition",
        "keyword": "gcse tutor",
        "meta_desc": "GCSE tutoring with Oxford and Cambridge-educated tutors. All subjects covered. AQA, Edexcel and OCR. 4.8/5 Trustpilot. Book a free consultation.",
    },
    "A-Level": {
        "slug": "a-level-tuition",
        "title": "A-Level Tuition",
        "keyword": "a level tutor",
        "meta_desc": "A-Level tutoring with Oxford and Cambridge-educated tutors. All subjects covered. AQA, Edexcel and OCR. 4.8/5 Trustpilot. Book a free consultation.",
    },
    "SATs": {
        "slug": "sats-tuition",
        "title": "SATs Tuition",
        "keyword": "sats tutor",
        "meta_desc": "SATs tutoring with Oxford and Cambridge-educated tutors. KS1 and KS2 maths, reading and grammar. 4.8/5 Trustpilot. Book a free consultation.",
    },
    "University": {
        "slug": "university-tuition",
        "title": "University Tuition",
        "keyword": "university tutor",
        "meta_desc": "University tutoring with Oxford and Cambridge-educated tutors. Essays, dissertations and exam prep. 4.8/5 Trustpilot. Book a free consultation.",
    },
}


def level_prompt(level: str) -> str:
    master_context = """
You are writing a service page for Leading Tuition, a UK tutoring company.

Audience:
- The primary reader is a UK parent considering tutoring for their child, or in some cases an older student.
- They are anxious, time-poor, and want to feel confident they are making the right decision.

Global rules:
- Write for a UK parent, not an SEO algorithm.
- Use a warm, expert, reassuring tone.
- Output plain HTML only — no markdown.
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>.
- Do not include <html>, <head>, or <body>.
- Do not include CTA buttons or footer text — the template handles those.
- Open with genuine empathy for the parent's specific situation — not a company boast.
- Include at least 3 specific, verifiable facts.
- Include one "I didn't know that" moment — one fact genuinely new to most parents.
- End naturally, without sounding salesy.
- Include one FAQ section with exactly 4 questions under <h2>Frequently Asked Questions</h2>.
- Write each FAQ question as <p><strong>Question?</strong></p> followed by a <p> answer.
- Never use filler phrases like "look no further", "unlock your potential", or "we are passionate about".
- Never mention BMAT as a current admissions test — it was abolished in 2023.
"""

    if level == "GCSE":
        return f"""
{master_context}

Before writing, think through:
1. What are parents of Year 10 and 11 students most anxious about at GCSE?
2. What do most parents not fully understand about how GCSE grading works?
3. What is the difference between tutoring that produces real improvement and tutoring that just provides reassurance?

Now write a detailed service page in HTML about: GCSE Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge the pressure parents feel as GCSE exams approach
- CRITICAL: All grades must use the 9–1 scale — NEVER use A*, A, B, C, D, E, F, or G
- Include these exact <h2> sections in this order:
  1. Why GCSE Results Matter
  2. The Most Commonly Tutored GCSE Subjects
  3. How GCSE Grading Works — and What Each Grade Really Means
  4. How to Get the Most from GCSE Tutoring
  5. Frequently Asked Questions about GCSE Tuition
- Must include:
  - GCSE grades run from 9 (highest) to 1 (lowest) in England — grade 4 is considered a standard pass, grade 5 a strong pass
  - Most students sit GCSEs in Year 10 and Year 11, with exams at the end of Year 11
  - The main exam boards are AQA, Edexcel, and OCR — different schools follow different boards
  - A grade 9 is awarded to roughly the top 3–4% of students nationally in each subject
  - Mock exams in Year 10 and Year 11 are important indicators but do not count toward final grades
- Include one short bullet list
- FAQ questions must address grade targets, which subjects benefit most from tutoring, exam board differences, and when to start
- After the FAQ section, include this exact HTML block verbatim — do not modify the links or text:
<h2>Find a GCSE Tutor by Subject</h2>
<div class="subject-grid">
  <a href="subjects/maths-tutor">Maths</a>
  <a href="subjects/chemistry-tutor">Chemistry</a>
  <a href="subjects/biology-tutor">Biology</a>
  <a href="subjects/physics-tutor">Physics</a>
  <a href="subjects/english-literature-tutor">English Literature</a>
  <a href="subjects/english-language-tutor">English Language</a>
  <a href="subjects/further-maths-tutor">Further Maths</a>
  <a href="subjects/computer-science-tutor">Computer Science</a>
  <a href="subjects/economics-tutor">Economics</a>
  <a href="subjects/history-tutor">History</a>
  <a href="subjects/geography-tutor">Geography</a>
  <a href="subjects/psychology-tutor">Psychology</a>
  <a href="subjects/politics-tutor">Politics</a>
  <a href="subjects/business-studies-tutor">Business Studies</a>
  <a href="subjects/statistics-tutor">Statistics</a>
</div>
"""

    if level == "A-Level":
        return f"""
{master_context}

Before writing, think through:
1. Why does A-Level feel so different from GCSE — and what catches students off guard?
2. What do parents not understand about how A-Level is assessed?
3. What does effective A-Level tutoring look like compared to just "going through the content"?

Now write a detailed service page in HTML about: A-Level Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge how significant the jump from GCSE to A-Level feels for both students and parents
- CRITICAL: Do NOT mention January modules — they were abolished. All A-Levels are now linear with all papers sat at the end of Year 13
- CRITICAL: Do NOT state that AS-Level grades count toward A-Level grades — they have been separate qualifications since 2017
- Include these exact <h2> sections in this order:
  1. Why A-Level Is Different from GCSE
  2. The Subjects Where Tutoring Makes the Biggest Difference
  3. How A-Level Assessment Actually Works
  4. What Good A-Level Tutoring Looks Like
  5. Frequently Asked Questions about A-Level Tuition
- Must include:
  - A-Levels are linear — all assessment takes place through exams at the end of Year 13, not through coursework or module tests throughout the two years (with some subject exceptions for coursework components)
  - AS-Levels have been decoupled from A-Levels since 2017 — AS results do not contribute to the final A-Level grade
  - The grade boundaries for A-Level subjects vary by exam board and by year — AQA, Edexcel, OCR, and WJEC each set their own mark schemes
  - University conditional offers are almost always based on A-Level grades, typically A*AA to ABB for competitive courses
  - The jump in demand between GCSE and A-Level is significant — students are expected to read independently, form arguments, and apply knowledge in unfamiliar contexts
- Include one short bullet list
- FAQ questions must address: when to start tutoring, what makes A-Level harder than GCSE, how tutoring supports university applications, and subject-specific advice
- After the FAQ section, include this exact HTML block verbatim — do not modify the links or text:
<h2>Find an A-Level Tutor by Subject</h2>
<div class="subject-grid">
  <a href="/services/subjects/maths-tutor">Maths</a>
  <a href="/services/subjects/further-maths-tutor">Further Maths</a>
  <a href="/services/subjects/chemistry-tutor">Chemistry</a>
  <a href="/services/subjects/biology-tutor">Biology</a>
  <a href="/services/subjects/physics-tutor">Physics</a>
  <a href="/services/subjects/english-literature-tutor">English Literature</a>
  <a href="/services/subjects/english-language-tutor">English Language</a>
  <a href="/services/subjects/history-tutor">History</a>
  <a href="/services/subjects/geography-tutor">Geography</a>
  <a href="/services/subjects/economics-tutor">Economics</a>
  <a href="/services/subjects/politics-tutor">Politics</a>
  <a href="/services/subjects/psychology-tutor">Psychology</a>
  <a href="/services/subjects/computer-science-tutor">Computer Science</a>
  <a href="/services/subjects/business-studies-tutor">Business Studies</a>
  <a href="/services/subjects/statistics-tutor">Statistics</a>
</div>
"""

    if level == "11+":
        return f"""
{master_context}

Before writing, think through:
1. What do most parents misunderstand about how the 11+ actually works?
2. How does the experience of sitting the 11+ differ from a normal school test?
3. What preparation mistakes waste the most time — and what actually works?

Now write a detailed service page in HTML about: 11+ Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge the anxiety parents feel when they first start researching the 11+
- CRITICAL: Never describe the 11+ as a "national standardised test" — it is not. It varies entirely by region and school
- CRITICAL: Always acknowledge that the format, content, and difficulty vary by area, consortium, and school
- Include these exact <h2> sections in this order:
  1. What the 11 Plus Actually Tests
  2. How the 11 Plus Varies by Region and School
  3. When to Start Preparing — and What That Preparation Involves
  4. What Effective 11 Plus Tutoring Looks Like
  5. Frequently Asked Questions about 11 Plus Tuition
- Must include:
  - The 11+ is a selective entry exam taken in Year 6, typically in September or October, with results determining Year 7 grammar or independent school entry
  - There are two main test providers: GL Assessment and CEM (Centre for Evaluation and Monitoring) — different areas and schools use different providers, and the format differs significantly between them
  - GL Assessment papers tend to be more predictable in format; CEM papers are designed to be harder to prepare for with standard practice papers
  - The four areas typically tested are: verbal reasoning, non-verbal reasoning, mathematics, and English comprehension — but not every test includes all four
  - Preparation typically starts in Year 4 or Year 5 — starting in Year 6 is generally too late for the most competitive schools
  - Parents should check their target school's admissions page to confirm which test provider is used
- Include one short bullet list
- FAQ questions must address: when to start, CEM vs GL Assessment differences, what happens if a child misses the threshold, and how to prepare a child who finds timed tests difficult
"""

    if level == "13+":
        return f"""
{master_context}

Before writing, think through:
1. What is Common Entrance, and how does it differ from school-specific 13+ papers?
2. What do families underestimate about preparing for 13+ entry?
3. How does the process vary between schools — and why does that matter for preparation?

Now write a detailed service page in HTML about: 13+ Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge that 13+ entry to independent schools is among the most academically demanding assessments students face at that age
- CRITICAL: Acknowledge that 13+ assessment is not standardised nationally — requirements vary significantly by school
- Include these exact <h2> sections in this order:
  1. What 13 Plus Entry Actually Involves
  2. Common Entrance vs School-Specific Papers
  3. The Subjects and Standards Required
  4. How to Approach 13 Plus Preparation
  5. Frequently Asked Questions about 13 Plus Tuition
- Must include:
  - 13+ entry is used by many leading independent schools for Year 9 entry
  - Common Entrance (CE) at 13+ is set by ISEB (the Independent Schools Examinations Board) and covers English, Mathematics, Sciences, History, Geography, Religious Studies, Languages, and others
  - Many highly selective schools — including Eton, Winchester, and Westminster — set their own papers in addition to or instead of Common Entrance
  - Scholarship examinations typically take place in Year 8 (January to March) and are harder than CE papers
  - CE pass marks are set by the receiving school, not by ISEB — a mark that earns entry to one school may not be sufficient at another
  - Pre-testing often happens at 11 or 12 for 13+ entry, meaning conditional offers are given early
- Include one short bullet list
- FAQ questions must address: what Common Entrance covers, how scholarship exams differ, when preparation should start, and what to do if a school sets its own papers
"""

    if level == "Primary":
        return f"""
{master_context}

Before writing, think through:
1. When does primary tutoring genuinely help — and when is it unnecessary or counterproductive?
2. What do parents worry about at primary age that tutoring can realistically address?
3. What are the key assessments in primary school that parents often do not know about?

Now write a detailed service page in HTML about: Primary Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge that parents of primary-age children often feel uncertain about whether tutoring is appropriate — and address that uncertainty honestly
- Include these exact <h2> sections in this order:
  1. When Primary Tutoring Makes Sense
  2. What Primary Tutoring Covers
  3. Key Assessments at Primary School
  4. How We Work with Primary-Age Children
  5. Frequently Asked Questions about Primary Tuition
- Must include:
  - KS1 covers Years 1 and 2 (ages 5–7); KS2 covers Years 3 to 6 (ages 7–11)
  - The Year 1 Phonics Screening Check assesses decoding ability — children who do not meet the expected standard resit in Year 2
  - The Year 4 Multiplication Tables Check tests fluency with times tables up to 12×12 on a computer-based assessment
  - KS2 SATs take place in Year 6 and cover Reading, Grammar, Punctuation and Spelling, and Maths — Writing is assessed by teachers
  - Children applying for 11+ selective entry typically begin preparation in Year 4 or Year 5
  - Primary tutoring often focuses on building genuine confidence and foundational skills rather than drilling test content
- Include one short bullet list
- FAQ questions must address: whether primary tutoring is beneficial or adds pressure, when 11+ prep should start, how to support a child who is struggling with reading, and what the Phonics Screening Check involves
"""

    if level == "SATs":
        return f"""
{master_context}

Before writing, think through:
1. What are KS1 and KS2 SATs, and how do parents often misunderstand their purpose?
2. What does the content of SATs actually test — and where do children most commonly lose marks?
3. How should preparation balance confidence with genuine skill-building?

Now write a detailed service page in HTML about: SATs Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge the stress that SATs create for both children and parents — and offer an honest perspective on what they are for
- Include these exact <h2> sections in this order:
  1. What Are SATs and What Do They Test?
  2. KS1 SATs and KS2 SATs — What Is the Difference?
  3. Where Children Commonly Struggle in SATs
  4. How Targeted SATs Preparation Helps
  5. Frequently Asked Questions about SATs Tuition
- Must include:
  - KS1 SATs (Year 2) assess Reading and Maths; teacher assessment also contributes to the overall picture at this stage
  - KS2 SATs (Year 6) include papers in Reading, Grammar Punctuation and Spelling (GPS), and Maths — Writing is assessed by teachers, not through a separate exam paper
  - KS2 SATs results are used to set secondary school teaching groups — they are not pass/fail, but they do follow children into Year 7
  - The scaled score system runs from 80 to 120, with 100 representing the expected standard
  - KS2 SATs take place in May of Year 6, typically over three days
  - Schools use SATs data for self-evaluation and Ofsted inspections, which is why some schools put significant emphasis on them
- Include one short bullet list
- FAQ questions must address: whether SATs affect secondary school placement, how to help an anxious child, what the scaled score means, and when to start preparing
"""

    if level == "University":
        return f"""
{master_context}

Before writing, think through:
1. Who actually benefits from university-level tutoring — and what do they need?
2. What is different about tutoring at degree level compared to GCSE or A-Level?
3. What subjects and tasks are most commonly supported at university level?

Now write a detailed service page in HTML about: University Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge that university students often feel they should be able to manage independently — and address why seeking support is a sensible, not a weak, decision
- Include these exact <h2> sections in this order:
  1. Who University Tutoring Is For
  2. The Subjects and Tasks We Support
  3. Dissertation and Extended Essay Support
  4. How University Tutoring Works in Practice
  5. Frequently Asked Questions about University Tuition
- Must include:
  - University degree classifications in the UK: First Class (70%+), Upper Second (2:1, 60–69%), Lower Second (2:2, 50–59%), Third (40–49%)
  - A 2:1 is the minimum grade required for most graduate employer schemes and many postgraduate programmes
  - Dissertation modules typically account for 30 to 40 credits — often the largest single component of a final year
  - Many students find the transition from structured A-Level learning to independent university study genuinely difficult — this is a well-documented adjustment challenge
  - University tutoring often focuses on academic writing, critical analysis, and structuring arguments rather than content delivery
  - Postgraduate students (Masters and PhD) also benefit from tutoring support, particularly for thesis writing and research methodology
- Include one short bullet list
- FAQ questions must address: whether tutoring is appropriate for university students, what dissertation support involves, how sessions work remotely, and whether tutors work across all degree subjects
"""

    # Fallback (should not be reached with current CSV)
    return f"""
{master_context}

Now write a detailed service page in HTML about: {level} Tuition

Requirements:
- Length: 1,100 to 1,350 words
- Opening paragraph must acknowledge the parent's or student's real concern
- Include at least 5 <h2> sections, the last being Frequently Asked Questions
- Include specific UK context: exam boards, year groups, grade systems
- Include one short bullet list
- Include exactly 4 FAQ questions
"""


def generate_level_pages(limit=None):
    levels = load_csv("levels.csv")
    if limit is not None:
        levels = levels[:limit]

    for row in levels:
        level = row["level"]
        meta = LEVEL_METADATA.get(level)
        if not meta:
            print(f"Skipping unknown level: {level}")
            continue

        slug = meta["slug"]
        title = meta["title"]
        meta_desc = meta["meta_desc"]

        prompt = level_prompt(level)
        content = ask_claude(prompt, max_tokens=3600)
        html = service_page_template(title=title, content=content, meta_desc=meta_desc, slug=slug, page_type="level")

        levels_dir = OUTPUT_DIR / "services" / "levels"
        levels_dir.mkdir(parents=True, exist_ok=True)
        file_path = levels_dir / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated level page: {file_path}")


def generate_location_pages(limit=None, new_only=False, city_filter=None):
    cities = load_csv("locations.csv")
    if limit is not None:
        cities = cities[:limit]

    for row in cities:
        city = row["city"]
        slug = city.lower().replace(" ", "-")

        # Filter to a single city if requested
        if city_filter and city.lower() != city_filter.lower():
            continue

        locations_dir = OUTPUT_DIR / "locations"
        locations_dir.mkdir(parents=True, exist_ok=True)
        file_path = locations_dir / f"{slug}.html"

        # Check new_only BEFORE calling the API
        if new_only and file_path.exists():
            print(f"  SKIP (exists): {file_path}")
            continue

        title = f"Private Tuition in {city}"
        # Per-city overrides — distinct descriptions for each location for SEO uniqueness
        _location_meta = {
            "Barnet":              "Private tutors in Barnet for GCSE, A-Level and 11+ prep. Specialist coaching for QE Barnet and Henrietta Barnett. DBS-checked. 4.8/5 Trustpilot.",
            "Bath":                "Private tutors in Bath covering GCSE, A-Level, 11+ and university preparation. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Birmingham":          "Private tutors in Birmingham for GCSE, A-Level, 11+ and medicine prep. Specialist King Edward's and grammar school coaching. DBS-checked. 4.8/5 Trustpilot.",
            "Brighton":            "Private tutors in Brighton for GCSE, A-Level, medicine prep and university applications. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Bristol":             "Private tutors in Bristol for GCSE, A-Level, 11+ prep, and Bristol University medicine applications. Oxford-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Bromley":             "Private tutors in Bromley for GCSE, A-Level and 11+ Kent Test preparation. Grammar school coaching alongside medicine and Oxbridge prep. 4.8/5 Trustpilot.",
            "Cambridge":           "Private tutors in Cambridge for GCSE, A-Level, and Oxbridge preparation. Specialist coaching from Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Cheltenham":          "Private tutors in Cheltenham for GCSE, A-Level and 11+ prep including Pate's Grammar coaching. Oxford-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Coventry":            "Private tutors in Coventry for GCSE, A-Level and medicine prep. Specialist support for Warwick University applications. DBS-checked. 4.8/5 Trustpilot.",
            "Croydon":             "Private tutors in Croydon for GCSE, A-Level and 11+ Sutton grammar preparation. Specialist Sutton SET coaching alongside medicine prep. 4.8/5 Trustpilot.",
            "Derby":               "Private tutors in Derby for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors, all DBS-checked. 4.8/5 Trustpilot.",
            "Ealing":              "Private tutors in Ealing for GCSE, A-Level and 11+ preparation. Specialist coaching for West London selective schools. DBS-checked. 4.8/5 Trustpilot.",
            "Exeter":              "Private tutors in Exeter for GCSE, A-Level and medicine prep. Specialist support for Exeter University admissions. DBS-checked. 4.8/5 Trustpilot.",
            "Guildford":           "Private tutors in Guildford for GCSE, A-Level and 11+ preparation. Specialist coaching for Royal Grammar School Guildford. DBS-checked. 4.8/5 Trustpilot.",
            "Harrow":              "Private tutors in Harrow for GCSE, A-Level and 11+ preparation. Specialist coaching for North London selective schools. DBS-checked. 4.8/5 Trustpilot.",
            "Kingston upon Thames":"Private tutors in Kingston upon Thames for GCSE, A-Level, and specialist 11+ coaching for Tiffin School and Tiffin Girls'. DBS-checked. 4.8/5 Trustpilot.",
            "Leeds":               "Private tutors in Leeds for GCSE, A-Level and medicine prep. Specialist support for Leeds University medicine and Oxbridge applications. 4.8/5 Trustpilot.",
            "Leicester":           "Private tutors in Leicester for GCSE, A-Level and medicine prep. Support for Leicester medical school applications. DBS-checked. 4.8/5 Trustpilot.",
            "Liverpool":           "Private tutors in Liverpool for GCSE, A-Level and medicine prep. Specialist coaching for Liverpool medical school applicants. DBS-checked. 4.8/5 Trustpilot.",
            "London":              "Private tutors across London for GCSE, A-Level, 11+, medicine prep and Oxbridge admissions. Oxbridge-educated, DBS-checked. 4.8/5 Trustpilot.",
            "Luton":               "Private tutors in Luton for GCSE, A-Level and 11+ prep. Specialist grammar school coaching for Hertfordshire and Bedfordshire. DBS-checked. 4.8/5.",
            "Manchester":          "Private tutors in Manchester for GCSE, A-Level and 11+ Trafford consortium prep. Specialist Altrincham and Sale Grammar coaching. DBS-checked. 4.8/5.",
            "Milton Keynes":       "Private tutors in Milton Keynes for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Northampton":         "Private tutors in Northampton for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors. DBS-checked. 4.8/5 Trustpilot.",
            "Norwich":             "Private tutors in Norwich for GCSE, A-Level and university prep. Specialist coaching for UEA admissions and selective schools. DBS-checked. 4.8/5 Trustpilot.",
            "Nottingham":          "Private tutors in Nottingham for GCSE, A-Level and medicine prep. Specialist Nottingham medical school application coaching. DBS-checked. 4.8/5 Trustpilot.",
            "Oxford":              "Private tutors in Oxford for GCSE, A-Level and Oxbridge preparation. Expert coaching in one of the UK's most academic cities. DBS-checked. 4.8/5 Trustpilot.",
            "Portsmouth":          "Private tutors in Portsmouth for GCSE, A-Level, 11+ and medicine preparation. Oxford and Cambridge-educated tutors, DBS-checked. 4.8/5 Trustpilot.",
            "Reading":             "Private tutors in Reading for GCSE, A-Level and 11+ prep. Specialist grammar school coaching including Reading School and Kendrick. 4.8/5 Trustpilot.",
            "Sheffield":           "Private tutors in Sheffield for GCSE, A-Level and medicine prep. Specialist Sheffield University medical school coaching. DBS-checked. 4.8/5 Trustpilot.",
            "Slough":              "Private tutors in Slough for GCSE, A-Level and 11+ prep. Specialist coaching for Slough grammar schools including Upton Court. DBS-checked. 4.8/5.",
            "Twickenham":          "Private tutors in Twickenham for GCSE, A-Level and 11+ preparation. Close to Tiffin School and Richmond Park area. DBS-checked. 4.8/5 Trustpilot.",
            "Watford":             "Private tutors in Watford for GCSE, A-Level and 11+ preparation. Specialist grammar school coaching across Hertfordshire. DBS-checked. 4.8/5 Trustpilot.",
            "Wimbledon":           "Private tutors in Wimbledon for GCSE, A-Level and 11+ preparation. Expert coaching for Raynes Park and South London selective schools. 4.8/5 Trustpilot.",
            "York":                "Private tutors in York for GCSE, A-Level and 11+ prep. Specialist university admissions coaching for University of York. DBS-checked. 4.8/5 Trustpilot.",
        }
        meta_desc = _location_meta.get(
            city,
            f"Expert private tutors in {city}. DBS checked. GCSE, A-Level, 11+ and medicine prep. "
            f"4.8/5 Trustpilot. Book a free consultation today."
        )

        prompt = location_prompt(city)
        content = ask_claude(prompt, max_tokens=3600)
        html = location_page_template(city=city, title=title, content=content, meta_desc=meta_desc, slug=slug)

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated location page: {file_path}")


# ── Admissions Test page prompts ─────────────────────────────────────────────

ADMISSIONS_TEST_META = {
    "lnat-preparation":
        "Expert LNAT preparation from Oxbridge-educated tutors. Critical reasoning strategies for Section A and essay technique for Section B. 4.8/5 Trustpilot.",
    "mat-preparation":
        "Expert MAT preparation for Oxford and Imperial Mathematics. Problem-solving technique, past paper coaching, and mock tests from Oxford-educated tutors. 4.8/5.",
    "pat-preparation":
        "Expert PAT preparation for Oxford Physics applicants. Mechanics, electricity, and optics coaching from Oxford-educated physicists. 4.8/5 Trustpilot.",
    "tsa-preparation":
        "Expert TSA preparation for Oxford Economics, PPE, and Psychology applicants. Critical thinking and problem solving coaching from Oxford-educated tutors. 4.8/5.",
    "hat-preparation":
        "Expert HAT preparation for Oxford History applicants. Source analysis, time management, and timed practice from Oxford-educated tutors. 4.8/5 Trustpilot.",
    "elat-preparation":
        "Expert ELAT preparation for Oxford English applicants. Close reading technique, comparative essay writing, and timed practice from Oxford-educated tutors. 4.8/5.",
    "mlat-preparation":
        "Expert MLAT preparation for Oxford Modern Languages applicants. Language reasoning, vocabulary analysis, and timed practice from Oxford-educated tutors. 4.8/5.",
    "step-preparation":
        "Expert STEP Maths preparation for Cambridge and Warwick applicants. Pure and applied problem-solving coaching from Cambridge-educated mathematicians. 4.8/5.",
    "tmua-preparation":
        "Expert TMUA preparation for Cambridge, Bath, and Durham applicants. Mathematical reasoning strategies and timed practice from Cambridge-educated tutors. 4.8/5.",
    "esat-preparation":
        "Expert ESAT preparation for Cambridge Engineering and Natural Science applicants. Section-by-section strategy from Cambridge-educated tutors. 4.8/5 Trustpilot.",
    "phil-preparation":
        "Expert Oxford PHIL test preparation. Argument analysis, philosophical reasoning, and written response coaching from Oxford-educated Philosophy tutors. 4.8/5.",
    "bmat-history":
        "BMAT was scrapped in 2023. See which UK medical schools now use UCAT instead, what changed, and what this means for your 2025–26 medicine application.",
}


def admissions_test_prompt(slug: str, title: str, full_name: str, keyword: str, institution: str) -> str:
    is_bmat = slug == "bmat-history"

    if is_bmat:
        return f"""
You are writing an SEO service page for Leading Tuition, a UK tutoring company.

Topic: BMAT — What Replaced It and What to Do Now
The BMAT (BioMedical Admissions Test) was abolished after the 2022–23 application cycle.
Oxford, Cambridge, and Imperial — the three universities that previously used BMAT — now use UCAT for Medicine.
This page exists to capture "BMAT tutor" and "BMAT preparation" search traffic and redirect it usefully.

Audience:
- A student or parent who searched "BMAT" and does not yet know it was abolished
- They need clear, honest information and a path forward

Global rules:
- Write for a UK applicant, not an SEO algorithm
- Use a clear, warm, authoritative tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions

Requirements:
- Length: 800 to 1,000 words
- Opening paragraph must immediately clarify that BMAT has been abolished, without being harsh
- Include these exact <h2> sections in this order:
  1. What Was the BMAT?
  2. When Was BMAT Abolished and Why?
  3. What Replaced BMAT? UCAT at Oxford, Cambridge, and Imperial
  4. What This Means for Your Medicine Application
  5. Frequently Asked Questions
- Must include:
  - BMAT was used by Oxford, Cambridge, Imperial, and a small number of international schools
  - BMAT was discontinued after the 2022–23 cycle by Cambridge Assessment Admissions Testing
  - From 2024 entry, Oxford, Cambridge, and Imperial all require UCAT
  - UCAT covers Verbal Reasoning, Decision Making, Quantitative Reasoning, Abstract Reasoning, and Situational Judgement
  - Students who were preparing for BMAT should now focus their energy on UCAT
- FAQ questions must address: when BMAT ended, which tests replaced it at each university, whether old BMAT prep books are still useful, and how to prepare for UCAT
"""

    import hashlib
    variant = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 3

    if variant == 0:
        # Leads with what the test is and tests; then preparation strategy
        structure = f"""
Use exactly these <h2> sections in this order:
  1. What Is the {full_name}?
  2. What Does the {full_name} Test?
  3. How the {full_name} Is Scored
  4. How to Prepare Effectively
  5. How Leading Tuition Supports {full_name} Preparation
  6. Frequently Asked Questions

Opening paragraph angle: Open by acknowledging the challenge the test poses and why specialist preparation matters. Establish clearly which universities and courses require it and what is at stake for the applicant.

FAQ focus: Registration deadlines, what score to aim for, whether past papers are available, and how tutoring helps."""

    elif variant == 1:
        # Leads with common mistakes and preparation pitfalls; test mechanics explained in context
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Why Most Students Find the {full_name} Harder Than Expected
  2. What the {full_name} Actually Tests — Format and Structure
  3. How Scoring Works and What Universities Do With It
  4. A Realistic {full_name} Preparation Timeline
  5. How Leading Tuition Approaches {full_name} Coaching
  6. Frequently Asked Questions

Opening paragraph angle: Open with the most common misconception students have about this test — what they think it tests versus what it actually tests. Immediately establish why self-study alone often underperforms and what a structured approach looks like.

FAQ focus: How far in advance to start preparing, whether the test can be retaken, what a competitive score looks like at {institution}, and what resources beyond past papers are useful."""

    else:
        # variant == 2: Leads with the university context and what's at stake; test details woven in
        structure = f"""
Use exactly these <h2> sections in this order:
  1. The {full_name} and What It Means for Your Application
  2. Test Format — Sections, Timing, and Question Types
  3. Scoring and How {institution} Uses Your Result
  4. Common Weaknesses and How to Address Them
  5. Preparing With Leading Tuition
  6. Frequently Asked Questions

Opening paragraph angle: Open from the university application angle — frame the {full_name} as a selection tool that {institution} uses to differentiate between candidates who all have strong predicted grades. Explain what this means practically for how a student should approach preparation.

FAQ focus: Whether the test score or grades matter more, how to manage preparation alongside A-Levels, what to do if the first attempt goes badly, and whether Leading Tuition offers mock tests."""

    return f"""
You are writing a specialist admissions test preparation page for Leading Tuition, a UK tutoring company.

Test: {full_name} ({title})
Used by: {institution}
Target keyword: {keyword}

Audience:
- A UK student (typically Year 12 or Year 13) preparing to apply to competitive universities
- Their parent may also be reading — they want reassurance that the support is expert and structured
- They are intelligent but anxious about a high-stakes test they may not fully understand yet

Global rules:
- Write for a UK applicant, not an SEO algorithm
- Use a clear, warm, authoritative tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions
- Never mention BMAT as a current admissions test — it was abolished in 2023
- Never use generic filler phrases like "look no further" or "unlock your potential"

Before writing, think through:
1. What does the student actually need to know about this test — format, timing, scoring, and what it tests?
2. What do most applicants get wrong in their preparation, and what approach actually works?
3. What specific support can Leading Tuition provide that makes a difference?

Now write a detailed service page in HTML about: {title}

Content requirements:
- Length: 950 to 1,150 words
- Which universities and courses require this test
- Test format (number of sections, timing, question types)
- Scoring method and how universities use the score
- Realistic timeline for preparation (how many weeks/months before the test)
- Common mistakes and how to avoid them
- Include one short bullet list

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- After all HTML content, on a new line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]
- Do not pad — every sentence must earn its place
"""


def generate_admissions_test_pages(limit=None, new_only=False):
    tests = load_csv("admissions_tests.csv")
    if limit is not None:
        tests = tests[:limit]

    for row in tests:
        slug = row["slug"]
        title = row["title"]
        full_name = row["full_name"]
        keyword = row["keyword"]
        institution = row["institution"]

        meta_desc = ADMISSIONS_TEST_META.get(
            slug,
            f"Expert {full_name} preparation from Leading Tuition. "
            "Specialist coaching from Oxbridge-educated tutors. 4.8/5 Trustpilot. Book a free consultation."
        )

        out_dir = OUTPUT_DIR / "admissions-tests" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): admissions-tests/{slug}/")
            continue

        prompt = admissions_test_prompt(slug=slug, title=title, full_name=full_name,
                                        keyword=keyword, institution=institution)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        # Build Service + AggregateRating schema
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": title,
            "url": f"https://www.leadingtuition.co.uk/admissions-tests/{slug}/",
            "description": meta_desc,
            "provider": {
                "@type": "Organization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
            "areaServed": {"@type": "Country", "name": "United Kingdom"},
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.8", "bestRating": "5",
                "worstRating": "1", "ratingCount": "54", "reviewCount": "54"
            }
        }
        import json as _json
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        breadcrumb = breadcrumb_schema("admissions-test", slug, title)
        schema_extra = faq_schema + "\n" + service_schema + "\n" + breadcrumb

        html = page_template(
            title, content,
            meta_desc=meta_desc,
            slug=f"admissions-tests/{slug}/",
            page_type="admissions-test",
            section="Admissions Tests",
            schema_extra=schema_extra
        )

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated admissions test page: admissions-tests/{slug}/")


# ── Medical School guide prompts ─────────────────────────────────────────────

def medical_school_prompt(slug: str, name: str, city: str, interview_type: str, ucat_notes: str) -> str:
    import hashlib
    variant = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 3

    if variant == 0:
        # Leads with school character; entry requirements follow the why
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Why Choose {name} for Medicine?
  2. Entry Requirements and A-Level Grades
  3. UCAT Requirements at {name}
  4. The Interview Process at {name}
  5. What Makes a Strong {name} Application
  6. Frequently Asked Questions about Applying to {name}

Opening paragraph angle: Open with what genuinely distinguishes {name} as a place to study medicine — curriculum style, clinical access, location, reputation in a specific speciality, or student culture. Make the reader feel they are learning something specific, not reading a template.

FAQ focus: UCAT score threshold, whether work experience is required, how to prepare for the {interview_type} format, whether {name} accepts graduate or international applicants."""

    elif variant == 1:
        # Leads with competitive landscape and application strategy; practical and strategic tone
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Getting Into {name} Medical School — What You're Up Against
  2. A-Level and Academic Requirements
  3. UCAT Strategy for {name}
  4. The {name} Interview — Format, Style, and How to Prepare
  5. Building a {name}-Worthy Application
  6. Frequently Asked Questions

Opening paragraph angle: Open with the competitive reality of applying to {name} — how many applicants per place, what kind of student typically succeeds here, and what makes the difference between an offer and a rejection. Ground it in specifics: interview format, UCAT weighting, or a distinctive feature of how {name} selects.

FAQ focus: When to sit UCAT, minimum vs competitive UCAT scores, what {name} looks for in personal statements, and whether predicted grades affect shortlisting."""

    else:
        # variant == 2: Leads with student experience and clinical training; admissions woven in
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Studying Medicine at {name} — The Student Experience
  2. Course Structure and Clinical Training in {city}
  3. Entry Requirements, UCAT, and Academic Thresholds
  4. Interviews at {name} — What to Expect
  5. How to Make Your Application Stand Out
  6. Frequently Asked Questions for {name} Applicants

Opening paragraph angle: Open with what it is actually like to study medicine at {name} — the curriculum model (PBL, traditional, integrated), when students first see patients, what {city} offers in terms of clinical placement variety, and the culture of the medical school. Draw the reader in before covering admissions.

FAQ focus: How early clinical exposure is at {name}, what UCAT score to aim for, how the {interview_type} differs from other formats, and how to balance A-Level revision with UCAT preparation."""

    return f"""
You are writing a medical school guide for Leading Tuition, a UK tutoring company.

Medical School: {name}
City: {city}
Interview format: {interview_type}
UCAT/entry notes: {ucat_notes}

Audience:
- A Year 12 or Year 13 student researching this specific medical school
- Their parent may also be reading
- They want detailed, accurate, and genuinely useful information — not a generic template

Global rules:
- Write for a UK applicant, not an SEO algorithm
- Use a clear, warm, authoritative tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions
- Never mention BMAT as a current admissions test — it was abolished in 2023
- Never use filler phrases like "look no further" or "we've got you covered"

Before writing, think through:
1. What is genuinely distinctive about {name} as a medical school — curriculum, location, culture, clinical access?
2. What are the actual entry requirements — A-Level grades, UCAT thresholds, and interview format?
3. What do successful applicants to {name} tend to have in common beyond grades?

Now write a detailed medical school guide in HTML about: {name} Medicine Entry Requirements

Content requirements:
- Length: 1,050 to 1,250 words
- Typical A-Level offer (A*AA or AAA with specific subjects)
- UCAT requirement: {ucat_notes}
- Interview format: {interview_type} — explain what this involves at {name} specifically
- Any personal statement or work experience considerations
- Approximate number of places per year (approximate is fine)
- Location: {city} — what this means for clinical placements and student life
- Include one short bullet list

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- Do not pad — every sentence must earn its place
"""


def generate_medical_school_pages(limit=None, new_only=False):
    schools = load_csv("medical_schools.csv")
    if limit is not None:
        schools = schools[:limit]

    for row in schools:
        slug = row["slug"]
        name = row["name"]
        city = row["city"]
        interview_type = row["interview_type"]
        ucat_notes = row["ucat_notes"]

        title = f"{name} Medicine Entry Requirements"
        meta_desc = (
            f"Complete guide to {name} Medicine entry requirements: A-Level grades, UCAT thresholds, "
            f"interview format, and how to build a strong application. Expert support from Leading Tuition."
        )

        out_dir = OUTPUT_DIR / "medical-schools" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): medical-schools/{slug}/")
            continue

        prompt = medical_school_prompt(slug=slug, name=name, city=city,
                                       interview_type=interview_type, ucat_notes=ucat_notes)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        import json as _json
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "url": f"https://www.leadingtuition.co.uk/medical-schools/{slug}/",
            "description": meta_desc,
            "publisher": {
                "@type": "Organization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk"
            }
        }
        article_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        breadcrumb = breadcrumb_schema("medical-school", slug, name)
        schema_extra = faq_schema + "\n" + article_schema + "\n" + breadcrumb

        html = page_template(
            title, content,
            meta_desc=meta_desc,
            slug=f"medical-schools/{slug}/",
            page_type="medical-school",
            section="Medical School Guides",
            schema_extra=schema_extra
        )

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated medical school page: medical-schools/{slug}/")


# ── Oxbridge Interview page metadata ─────────────────────────────────────────

OXBRIDGE_INTERVIEW_META = {
    "medicine-interview":
        "Oxbridge Medicine interview preparation: MMI and panel coaching, ethical scenarios, and scientific reasoning. Expert support from Oxford and Cambridge medics.",
    "law-interview":
        "Oxford and Cambridge Law interview preparation: LNAT coaching, legal reasoning, and mock interviews. Expert support from Oxbridge-educated law tutors.",
    "maths-interview":
        "Oxford and Cambridge Mathematics interview prep: MAT and STEP coaching, problem-solving technique from Cambridge-educated mathematicians. 4.8/5 Trustpilot.",
    "physics-interview":
        "Oxford and Cambridge Physics interview preparation: PAT and ESAT coaching, applied problem-solving, and mock interviews from Oxbridge-educated physicists.",
    "chemistry-interview":
        "Oxford and Cambridge Chemistry interview prep: ESAT coaching, problem-solving technique, and mock interviews. Expert support from Oxbridge-educated tutors.",
    "biology-interview":
        "Oxford and Cambridge Biology interview preparation: ESAT coaching, problem-solving technique, and mock interviews. Expert support from Oxbridge-educated tutors.",
    "engineering-interview":
        "Oxford and Cambridge Engineering interview preparation: applied problem-solving, PAT and ESAT coaching. Expert support from Oxbridge-educated engineers.",
    "economics-interview":
        "Oxford and Cambridge Economics interview prep: graph analysis, TSA coaching, and mock interviews to build economic reasoning. Oxbridge-educated tutors.",
    "history-interview":
        "Oxford and Cambridge History interview prep: HAT coaching, source analysis, and historical argument technique. Expert support from Oxbridge-educated tutors.",
    "english-interview":
        "Oxford and Cambridge English interview preparation: close reading, ELAT coaching, and literary argument technique. Expert support from Oxbridge-educated tutors.",
    "ppe-interview":
        "Oxford PPE interview preparation: TSA coaching, cross-disciplinary reasoning across Politics, Philosophy and Economics. Expert Oxford-educated tutors.",
    "computer-science-interview":
        "Oxford and Cambridge Computer Science interview prep: algorithmic thinking, MAT and TMUA coaching, and mock interviews from Oxbridge-educated tutors.",
    "classics-interview":
        "Oxford and Cambridge Classics interview preparation: unseen texts, written work coaching, and mock interviews from Oxbridge-educated Classics tutors.",
    "modern-languages-interview":
        "Oxford and Cambridge Modern Languages interview prep: language discussion, MLAT coaching, and literature analysis from Oxbridge-educated tutors.",
    "geography-interview":
        "Oxford and Cambridge Geography interview preparation: essay and map questions, fieldwork discussion, and mock interviews from Oxbridge-educated tutors.",
    "psychology-interview":
        "Oxford and Cambridge Psychology interview preparation: research critique, scientific reasoning, and mock interviews from Oxbridge-educated Psychology tutors.",
    "natural-sciences-interview":
        "Cambridge Natural Sciences interview preparation: ESAT coaching, problem-solving technique, and mock interviews from Cambridge-educated Natural Sciences tutors.",
    "philosophy-interview":
        "Oxford and Cambridge Philosophy interview preparation: argument analysis, PHIL test coaching, and philosophical reasoning with Oxbridge-educated tutors.",
}


def oxbridge_interview_prompt(slug: str, title: str, subjects: str,
                              oxford_test: str, cambridge_test: str, keyword: str) -> str:
    import hashlib
    variant = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 2

    if variant == 0:
        # Leads with what to expect; admissions tests then preparation then example questions
        structure = f"""
Use exactly these <h2> sections in this order:
  1. What to Expect in a {subjects} Oxbridge Interview
  2. The Admissions Tests: {oxford_test} (Oxford) and {cambridge_test} (Cambridge)
  3. How to Prepare for Your {subjects} Interview
  4. Example Interview Questions for {subjects}
  5. Common Mistakes and How to Avoid Them
  6. Frequently Asked Questions about {subjects} Oxbridge Interviews

Opening paragraph angle: Immediately explain what makes {subjects} Oxbridge interviews different from school or sixth-form expectations — the style of questioning, what tutors are actually assessing, and why standard revision alone won't prepare you.

FAQ focus: How long interviews last, whether prior knowledge is tested, how to practise effectively, and what to do if you don't know the answer to a question."""

    else:
        # variant == 1: Leads with example questions and subject-specific challenge first; process explained after
        structure = f"""
Use exactly these <h2> sections in this order:
  1. What {subjects} Oxbridge Interviewers Are Really Looking For
  2. Example Interview Questions for {subjects} — and How to Approach Them
  3. The Admissions Tests: {oxford_test} (Oxford) and {cambridge_test} (Cambridge)
  4. Building Your Preparation — A Practical Plan
  5. The Mistakes That Cost Candidates Offers
  6. Frequently Asked Questions

Opening paragraph angle: Open with a specific example of the kind of thinking {subjects} interviews demand — something that surprises candidates who expected a more traditional format. Make the reader immediately understand this is different from anything they have done before.

FAQ focus: Whether Oxford and Cambridge {subjects} interviews differ meaningfully, how many interviews candidates typically have, what super-curricular preparation matters most, and whether mock interviews are worth doing."""

    return f"""
You are writing an Oxbridge interview preparation service page for Leading Tuition, a UK tutoring company.

Subject(s): {subjects}
Oxford admissions test: {oxford_test}
Cambridge admissions test: {cambridge_test}

Audience:
- A Year 12 or Year 13 student (or their parent) preparing for Oxford or Cambridge interviews in {subjects}
- They want specific, actionable guidance — not generic interview tips
- They are anxious but ambitious, and want to know exactly what to expect and how to prepare

Global rules:
- Write for a UK student, not an SEO algorithm
- Use a clear, warm, authoritative tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions
- Never mention BMAT as a current admissions test — it was abolished in 2023
- Never use filler phrases like "look no further" or "we've got you covered"
- After all HTML content, on a new line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]

Before writing, think through:
1. What makes the {subjects} Oxbridge interview genuinely distinctive — what does it assess that other interviews don't?
2. What are the most common mistakes candidates make in {subjects} interviews, and why?
3. What does a top-1% interview performance in {subjects} actually look like?

Now write a detailed Oxbridge interview preparation service page in HTML: {title}

Content requirements:
- Length: 1,050 to 1,250 words
- At least 5 genuine, intellectually challenging example interview questions for {subjects} in a <ul>
- Specific advice on thinking aloud and engaging with questions even when uncertain
- Distinction between what Oxford and Cambridge look for if there is a meaningful difference
- Admissions test context: how {oxford_test} at Oxford and {cambridge_test} at Cambridge relate to interview preparation
- A brief note on super-curricular preparation relevant to {subjects}
- Include one short bullet list

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- Do not pad — every sentence must earn its place
"""


def generate_oxbridge_interview_pages(limit=None, new_only=False):
    rows = load_csv("oxbridge_interviews.csv")
    if limit is not None:
        rows = rows[:limit]

    for row in rows:
        slug = row["slug"]
        title = row["title"]
        subjects = row["subjects"]
        oxford_test = row["oxford_test"]
        cambridge_test = row["cambridge_test"]
        keyword = row["keyword"]

        meta_desc = OXBRIDGE_INTERVIEW_META.get(
            slug,
            f"Expert {title} preparation with Leading Tuition. "
            "Specialist coaching from Oxbridge-educated tutors. 4.8/5 Trustpilot. Book a free consultation."
        )

        out_dir = OUTPUT_DIR / "oxbridge-interviews" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): oxbridge-interviews/{slug}/")
            continue

        prompt = oxbridge_interview_prompt(slug=slug, title=title, subjects=subjects,
                                          oxford_test=oxford_test, cambridge_test=cambridge_test,
                                          keyword=keyword)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        import json as _json
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": title,
            "url": f"https://www.leadingtuition.co.uk/oxbridge-interviews/{slug}/",
            "description": meta_desc,
            "provider": {
                "@type": "Organization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
            "areaServed": {"@type": "Country", "name": "United Kingdom"},
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.8", "bestRating": "5",
                "worstRating": "1", "ratingCount": "54", "reviewCount": "54"
            }
        }
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        breadcrumb = breadcrumb_schema("oxbridge-interview", slug, title)
        schema_extra = faq_schema + "\n" + service_schema + "\n" + breadcrumb

        html = page_template(
            title, content,
            meta_desc=meta_desc,
            slug=f"oxbridge-interviews/{slug}/",
            page_type="oxbridge-interview",
            section="Oxbridge Interview Preparation",
            schema_extra=schema_extra
        )

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated Oxbridge interview page: oxbridge-interviews/{slug}/")


# ── 11+ School Preparation pages ─────────────────────────────────────────────

ELEVEN_PLUS_META = {
    "tiffin-school":           "Expert Tiffin School 11+ preparation with Leading Tuition. Specialist coaching for the Kingston Grammar Test. 4.8/5 Trustpilot. Book a free consultation.",
    "tiffin-girls-school":     "Expert Tiffin Girls' School 11+ preparation with Leading Tuition. Specialist coaching for the Kingston Grammar Test. 4.8/5 Trustpilot. Book a free consultation.",
    "queens-elizabeth-barnet": "Expert QE Barnet 11+ preparation with Leading Tuition. Specialist coaching for one of England's most selective grammar schools. 4.8/5 Trustpilot.",
    "henrietta-barnett-school":"Expert Henrietta Barnett School 11+ preparation with Leading Tuition. Specialist coaching for the UK's most selective state school. 4.8/5 Trustpilot.",
    "sutton-grammar-schools":  "Expert Sutton grammar school 11+ preparation. Specialist Sutton SET coaching for Wilson's, Sutton Grammar, Wallington, Nonsuch and Greenshaw. 4.8/5 Trustpilot.",
    "st-olaves-grammar-school":"Expert St Olave's Grammar School 11+ preparation. One of the UK's most selective schools — specialist coaching for the TBGS Orpington selective entry.",
    "slough-grammar-schools":  "Expert Slough grammar school 11+ preparation. Specialist SET coaching for all 5 Slough schools: Upton Court, Herschel, Langley, Slough Grammar and Khalsa.",
    "bucks-grammar-schools":   "Expert Buckinghamshire grammar school 11+ preparation with Leading Tuition. Specialist SET coaching for Bucks grammar schools. 4.8/5 Trustpilot.",
    "dr-challoners-grammar":   "Expert Dr Challoner's 11+ preparation with Leading Tuition. Specialist Bucks SET coaching for Dr Challoner's Grammar and High School. 4.8/5 Trustpilot.",
    "kegs-chelmsford":         "Expert KEGS Chelmsford 11+ preparation with Leading Tuition. Specialist CSSE coaching for King Edward VI Grammar School. 4.8/5 Trustpilot.",
    "chelmsford-county-high":  "Expert Chelmsford County High School 11+ preparation with Leading Tuition. Specialist CSSE coaching. 4.8/5 Trustpilot. Book a free consultation.",
    "altrincham-grammar-schools":"Expert 11+ prep for Altrincham Grammar School and Sale Grammar. Specialist Trafford consortium coaching: GL-style reasoning and maths. 4.8/5 Trustpilot.",
    "sale-grammar-school":     "Expert Sale Grammar School 11+ preparation. Specialist Trafford consortium coaching with past papers, timed tests, and targeted weak-area support. 4.8/5.",
    "tonbridge-grammar-school":"Expert Tonbridge Grammar School 11+ preparation with Leading Tuition. Specialist Kent Test coaching. 4.8/5 Trustpilot. Book a free consultation.",
    "weald-of-kent-grammar":   "Expert Weald of Kent Grammar School 11+ preparation with Leading Tuition. Specialist Kent Test coaching. 4.8/5 Trustpilot. Book a free consultation.",
}


def eleven_plus_school_prompt(slug: str, school_name: str, location: str, region: str,
                               exam_board: str, consortium: str, is_consortium: str,
                               schools_covered: str, selectivity: str, keyword: str) -> str:
    import hashlib
    variant = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 3

    is_consortium_bool = is_consortium.lower() == "true"
    consortium_note = (
        f"This page covers the {consortium} — a shared exam used by multiple schools: {schools_covered}. "
        f"Write about all of them together, explaining what the shared exam means for preparation."
        if is_consortium_bool
        else f"This page is for {school_name} specifically — a single school with its own admissions process."
    )

    if variant == 0:
        # Leads with the school's profile and what makes it worth targeting; exam details follow
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Why Families Target {school_name}
  2. The {exam_board} — Format, Sections, and What It Tests
  3. How Competitive Is Entry to {school_name}?
  4. How to Prepare — A Realistic Timeline and Strategy
  5. How Leading Tuition Supports {school_name} Preparation
  6. Frequently Asked Questions about {school_name} 11+ Entry

Opening paragraph angle: Open with what makes {school_name} worth the preparation investment — academic outcomes, Oxbridge send rate, reputation in the area, or what it means for a child's secondary school journey. Ground it in the local context of {location}. Make the parent understand immediately why this school is worth targeting.

FAQ focus: How early to start preparing, what score or pass mark is needed, whether the exam can be sat more than once, and what happens if a child narrowly misses the mark."""

    elif variant == 1:
        # Leads with the exam itself — format and what it tests; school profile and strategy follow
        structure = f"""
Use exactly these <h2> sections in this order:
  1. The {exam_board} — What the Exam Looks Like
  2. About {school_name} — Selectivity, Places, and What to Expect
  3. Common Weaknesses and How to Address Them Before the Test
  4. A Month-by-Month Preparation Plan
  5. Working With Leading Tuition on {school_name} Preparation
  6. Frequently Asked Questions

Opening paragraph angle: Open by explaining what the {exam_board} actually involves — not just the subject areas but the style and difficulty of questions and why children who only do school work are typically underprepared. Establish the gap between classroom learning and what the exam demands.

FAQ focus: What the {exam_board} tests that schools don't cover, whether tutoring genuinely makes a difference, typical preparation duration, and what a borderline result means for appeal prospects."""

    else:
        # variant == 2: Leads with preparation strategy and timeline; school and exam details woven in
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Preparing for {school_name} — Where to Start
  2. Understanding the {exam_board} — Sections, Timing, and Scoring
  3. What Makes {school_name} So Competitive
  4. How Leading Tuition Prepares Students for the {exam_board}
  5. Supporting the Whole Family Through the 11+ Process
  6. Frequently Asked Questions about the {school_name} 11+

Opening paragraph angle: Open from the parent's perspective — acknowledge that starting 11+ preparation can feel overwhelming, especially when you're not sure how early to begin, what the exam actually involves, or how to judge whether your child is on track. Frame this page as the guide that answers all of those questions for {school_name} specifically.

FAQ focus: When tutoring should start, how to keep a child motivated during a long preparation period, whether practice papers alone are enough, and how to manage multiple grammar school applications at once."""

    return f"""
You are writing an 11+ grammar school preparation page for Leading Tuition, a UK tutoring company.

School / Consortium: {school_name}
Location: {location}
Region: {region}
Exam used: {exam_board}
Selectivity: {selectivity}
{consortium_note}

Audience:
- A UK parent in or near {location} considering grammar school entry for their child
- They want specific, accurate guidance about {school_name} — not a generic 11+ article
- They are anxious, time-pressured, and want to know exactly what is required and how to prepare

Global rules:
- Write for a UK parent, not an SEO algorithm
- Use a warm, expert, reassuring tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions
- Never use generic filler phrases like "look no further" or "we've got you covered"
- Never refer to 11+ as "easy" or imply any child can pass without serious preparation

Before writing, think through:
1. What is genuinely distinctive about {school_name} — its academic record, culture, or outcomes?
2. What does the {exam_board} actually test, and what do most children get wrong in preparation?
3. What does a realistic, well-paced preparation timeline look like for this specific exam?

Now write a detailed 11+ preparation guide in HTML about: {school_name} 11+ Preparation

Content requirements:
- Length: 1,000 to 1,200 words
- Name {school_name} and {location} specifically in the opening paragraph
- Explain the {exam_board} format: subjects tested, timing, question style
- Include selectivity context: {selectivity}
- Include at least one concrete preparation tip that is specific to the {exam_board} — not generic advice
- Include one short <ul> bullet list (not in the FAQ section)
- Mention that Leading Tuition provides 1-to-1 specialist tutoring for this exam

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- After all HTML content, on a new line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]
- Do not pad — every sentence must earn its place
"""


def generate_eleven_plus_pages(limit=None, new_only=False):
    schools = load_csv("eleven_plus_schools.csv")
    if limit is not None:
        schools = schools[:limit]

    for row in schools:
        slug          = row["slug"]
        school_name   = row["school_name"]
        location      = row["location"]
        region        = row["region"]
        exam_board    = row["exam_board"]
        consortium    = row["consortium"]
        is_consortium = row["is_consortium"]
        schools_covered = row["schools_covered"]
        selectivity   = row["selectivity"]
        keyword       = row["keyword"]

        meta_desc = ELEVEN_PLUS_META.get(
            slug,
            f"Expert {school_name} 11+ preparation with Leading Tuition. "
            "Specialist coaching from experienced tutors. 4.8/5 Trustpilot. Book a free consultation."
        )

        out_dir = OUTPUT_DIR / "11-plus" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): 11-plus/{slug}/")
            continue

        prompt = eleven_plus_school_prompt(
            slug=slug, school_name=school_name, location=location, region=region,
            exam_board=exam_board, consortium=consortium, is_consortium=is_consortium,
            schools_covered=schools_covered, selectivity=selectivity, keyword=keyword
        )
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        import json as _json
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f"{school_name} 11+ Preparation",
            "url": f"https://www.leadingtuition.co.uk/11-plus/{slug}/",
            "description": meta_desc,
            "provider": {
                "@type": "Organization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
            "areaServed": {"@type": "Country", "name": "United Kingdom"},
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.8", "bestRating": "5",
                "worstRating": "1", "ratingCount": "54", "reviewCount": "54"
            }
        }
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        breadcrumb = breadcrumb_schema("eleven-plus", slug, f"{school_name} 11+ Preparation")
        schema_extra = faq_schema + "\n" + service_schema + "\n" + breadcrumb

        html = page_template(
            f"{school_name} 11+ Preparation | Leading Tuition",
            content,
            meta_desc=meta_desc,
            slug=f"11-plus/{slug}/",
            page_type="eleven-plus",
            section="11+ School Preparation",
            schema_extra=schema_extra
        )

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated 11+ page: 11-plus/{slug}/")

    # Generate hub page
    schools_all = load_csv("eleven_plus_schools.csv")
    school_links = "\n".join(
        f'  <a href="/11-plus/{r["slug"]}/" class="index-card"><strong>{r["school_name"]}</strong>'
        f'<span>{r["location"]} — {r["exam_board"]}</span></a>'
        for r in schools_all
    )
    hub_content = f"""<p>Leading Tuition provides specialist 11+ preparation for the most competitive grammar schools across England.
Whether your child is sitting the Kingston Grammar Test for Tiffin, the Sutton SET, the Slough consortium exam, the Kent Test, or the Bucks SET,
our tutors know these specific exams in depth — not just the 11+ in general.</p>
<p>Select your target school or consortium below to find detailed preparation guidance, exam format information, and how we can help.</p>
<div class="subject-grid">
{school_links}
</div>"""

    hub_crumb = breadcrumb_schema("eleven-plus-hub", "11-plus", "11+ Grammar School Preparation")
    hub_html = page_template(
        "11+ Grammar School Preparation | Leading Tuition",
        hub_content,
        meta_desc="Specialist 11+ preparation for the UK's most competitive grammar schools. Tiffin, QE Barnet, Sutton SET, Slough SET, Kent Test, Bucks SET and more. 4.8/5 Trustpilot.",
        slug="11-plus/",
        page_type="eleven-plus-hub",
        section="",
        schema_extra=hub_crumb,
    )
    hub_path = OUTPUT_DIR / "11-plus" / "index.html"
    hub_path.write_text(hub_html, encoding="utf-8")
    print("Generated hub page: 11-plus/index.html")


def generate_navbar():
    """
    Propagate the canonical <nav> block from templates.py to every HTML file
    in output/ that contains a navbar. No API calls required.

    The canonical nav is extracted by rendering a dummy page through
    service_page_template() — the same template used by all generated pages —
    so this function always reflects whatever the current nav says in templates.py.
    """
    import re
    from templates import service_page_template

    # Extract canonical nav from a rendered sample page
    sample = service_page_template("__dummy__", "<p>x</p>")
    match = re.search(r'<nav class="navbar">.*?</nav>', sample, re.DOTALL)
    if not match:
        raise ValueError("Could not extract <nav> block from service_page_template output")
    canonical_nav = match.group(0)

    nav_pattern = re.compile(r'<nav class="navbar">.*?</nav>', re.DOTALL)

    # Top-level directories to skip (seo-generator/ is a source/tool dir, not live content)
    NAV_SKIP_DIRS = {"seo-generator", ".git", "node_modules"}

    updated = 0
    skipped = 0
    for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
        rel = html_file.relative_to(OUTPUT_DIR)
        if rel.parts and rel.parts[0] in NAV_SKIP_DIRS:
            continue
        content = html_file.read_text(encoding="utf-8")
        if '<nav class="navbar">' not in content:
            skipped += 1
            continue
        new_content = nav_pattern.sub(canonical_nav, content)
        if new_content != content:
            html_file.write_text(new_content, encoding="utf-8")
            updated += 1
        else:
            skipped += 1

    print(f"Navbar updated in {updated} files ({skipped} files unchanged or no navbar)")


def generate_sitemap():
    """
    Crawl output/ and write sitemap.xml.
    URL priority rules:
      1.0  homepage
      0.9  A-Level hub, GCSE hub
      0.8  specialist/admissions, medicine-prep cluster, subject sub-pages (/subjects/)
      0.7  location pages, original subject pages, level pages
      0.6  blog posts, core static pages
    """
    import datetime

    BASE_URL = "https://www.leadingtuition.co.uk"

    # Static pages that live at fixed root paths — map filename → url_path
    STATIC_ROOTS = {
        "index.html":        "/",
        "about.html":        "/about",
        "contact.html":      "/contact",
        "faqs.html":         "/faqs",
        "services.html":     "/services",
        "tutors.html":       "/tutors",
        "consultation.html": "/consultation",
        "locations.html":    "/locations",
        "blog.html":         "/blog",
    }

    # Paths to skip entirely
    SKIP_NAMES = {"sitemap.xml", "sitemap.html"}

    def get_priority(url_path: str) -> str:
        if url_path in ("/", ""):
            return "1.0"
        if url_path in ("/a-level/", "/gcse/"):
            return "0.9"
        if (url_path.startswith("/subjects/") or
                url_path.startswith("/medicine-prep/") or
                url_path.startswith("/services/specialist-admissions/")):
            return "0.8"
        if (url_path.startswith("/locations/") or
                url_path.startswith("/services/subjects/") or
                url_path.startswith("/services/levels/")):
            return "0.7"
        if url_path.startswith("/blog/"):
            return "0.6"
        if url_path == "/admissions-tests/":
            return "0.9"
        if url_path.startswith("/admissions-tests/"):
            return "0.8"
        if url_path == "/medical-schools/":
            return "0.9"
        if url_path.startswith("/medical-schools/"):
            return "0.8"
        if url_path == "/oxbridge-interviews/":
            return "0.9"
        if url_path.startswith("/oxbridge-interviews/"):
            return "0.8"
        if url_path == "/11-plus/":
            return "0.9"
        if url_path.startswith("/11-plus/"):
            return "0.8"
        return "0.6"

    entries = []  # list of (url, lastmod, priority)

    # Top-level directories to skip when crawling the repo root
    SKIP_DIRS = {"seo-generator", ".git", "node_modules"}

    for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
        if html_file.name in SKIP_NAMES:
            continue

        rel = html_file.relative_to(OUTPUT_DIR)
        # Skip anything inside excluded top-level directories
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            continue
        parts = rel.parts  # e.g. ('locations', 'coventry.html') or ('a-level', 'index.html')

        # Root-level static pages
        if len(parts) == 1:
            name = parts[0]
            if name in STATIC_ROOTS:
                url_path = STATIC_ROOTS[name]
            else:
                # Unknown root file — skip (gcse-maths-tutor.html etc are standalone keyword pages)
                url_path = "/" + name.replace(".html", "")
        elif rel.name == "index.html":
            # Directory-style page → trailing slash URL
            url_path = "/" + "/".join(parts[:-1]) + "/"
        else:
            # Flat file in a subdirectory
            url_path = "/" + "/".join(parts).replace(".html", "")

        lastmod = datetime.date.fromtimestamp(html_file.stat().st_mtime).isoformat()
        priority = get_priority(url_path)
        entries.append((BASE_URL + url_path, lastmod, priority))

    # Sort: homepage first, then by URL
    entries.sort(key=lambda x: (x[0] != BASE_URL + "/", x[0]))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, lastmod, priority in entries:
        lines += [
            "  <url>",
            f"    <loc>{url}</loc>",
            f"    <lastmod>{lastmod}</lastmod>",
            "    <changefreq>monthly</changefreq>",
            f"    <priority>{priority}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")

    sitemap_path = OUTPUT_DIR / "sitemap.xml"
    sitemap_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated sitemap.xml — {len(entries)} URLs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--static",           action="store_true", help="Generate homepage, about, contact, and index pages (no API)")
    parser.add_argument("--specialist",        action="store_true", help="Generate specialist pages")
    parser.add_argument("--subjects",          action="store_true", help="Generate subject pages")
    parser.add_argument("--locations",         action="store_true", help="Generate location pages")
    parser.add_argument("--blog",              action="store_true", help="Generate blog posts")
    parser.add_argument("--levels",            action="store_true", help="Generate level pages")
    parser.add_argument("--admissions-tests",   action="store_true", help="Generate admissions test pages (LNAT, MAT, PAT, TSA, etc.)")
    parser.add_argument("--medical-schools",    action="store_true", help="Generate medical school entry guide pages (~38 schools)")
    parser.add_argument("--oxbridge-interviews", action="store_true", help="Generate Oxbridge interview prep pages by subject (~18 pages)")
    parser.add_argument("--eleven-plus",         action="store_true", help="Generate 11+ grammar school preparation pages (~15 pages)")
    parser.add_argument("--sitemap",           action="store_true", help="Generate sitemap.xml from output/ directory (no API)")
    parser.add_argument("--navbar",            action="store_true", help="Push canonical nav from templates.py to all HTML files in output/ (no API)")
    parser.add_argument("--all",               action="store_true", help="Generate everything (30-45 min)")
    parser.add_argument("--limit",    type=int, default=None,       help="Limit number of pages generated per category")
    parser.add_argument("--city",     type=str, default=None,       help="Generate a single location page by city name (e.g. --city Slough)")
    parser.add_argument("--new-only", action="store_true",          help="Skip pages whose output file already exists (useful for resuming or adding new pages)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "services" / "subjects").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "services" / "levels").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "services" / "specialist-admissions").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "blog").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "locations").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "admissions-tests").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "medical-schools").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "oxbridge-interviews").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "11-plus").mkdir(parents=True, exist_ok=True)

    run_all = args.all
    new_only = args.new_only

    if args.static or run_all:
        generate_static_pages()

    if args.specialist or run_all:
        generate_specialist_pages(limit=args.limit)

    if args.subjects or run_all:
        generate_subject_pages(limit=args.limit)

    if args.locations or args.city or run_all:
        generate_location_pages(limit=args.limit, new_only=new_only, city_filter=args.city)

    if args.blog or run_all:
        generate_blog_pages(limit=args.limit, new_only=new_only)

    if args.levels or run_all:
        generate_level_pages(limit=args.limit)

    # New Phase 3 page types
    admissions_tests_flag    = getattr(args, "admissions_tests", False)
    medical_schools_flag     = getattr(args, "medical_schools", False)
    oxbridge_interviews_flag = getattr(args, "oxbridge_interviews", False)
    eleven_plus_flag         = getattr(args, "eleven_plus", False)

    if admissions_tests_flag or run_all:
        generate_admissions_test_pages(limit=args.limit, new_only=new_only)

    if medical_schools_flag or run_all:
        generate_medical_school_pages(limit=args.limit, new_only=new_only)

    if oxbridge_interviews_flag or run_all:
        generate_oxbridge_interview_pages(limit=args.limit, new_only=new_only)

    if eleven_plus_flag or run_all:
        generate_eleven_plus_pages(limit=args.limit, new_only=new_only)

    # --navbar runs after all generators so manually-written pages get the same nav.
    # It can also be run standalone at any time (no API calls required).
    if args.navbar or run_all:
        generate_navbar()

    # --sitemap runs last so the final sitemap reflects everything just generated.
    # It can also be run standalone at any time (no API calls required).
    if args.sitemap or run_all:
        generate_sitemap()

    if not any([args.static, args.specialist, args.subjects,
                args.locations, args.city, args.blog, args.levels,
                admissions_tests_flag, medical_schools_flag, oxbridge_interviews_flag,
                eleven_plus_flag, args.navbar, args.sitemap, run_all]):
        parser.print_help()


if __name__ == "__main__":
    main()