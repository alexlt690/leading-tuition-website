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

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

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

    # Build slug from title (same logic as generate_blog_pages)
    def _slugify(title):
        s = title.lower()
        s = re.sub(r"[^\w\s-]", "", s)
        return re.sub(r"\s+", "-", s).strip("-")

    # ── Success stories (pinned at top) ───────────────────────────────────────
    success_items = []
    for story in SUCCESS_STORIES:
        success_items.append(
            f'  <p><a href="{story["slug"]}"><strong>{story["title"]}</strong></a>'
            f' <em style="color:#666;font-size:0.9em;">— {story["success_rate"]}% success rate</em></p>'
        )

    # ── Categorised blog posts ─────────────────────────────────────────────────
    BLOG_CATEGORIES = {
        "11+ &amp; School Entrance": [
            "what-is-the-11-plus-exam",
            "the-6-month-11-plus-countdown-a-monthly-study-milestone-plan",
            "11-plus-pass-marks-by-region-how-high-do-you-need-to-score",
            "gl-assessment-vs-cem-vs-local-school-exams-the-2026-format-guide",
            "iseb-common-pre-test-a-parents-guide-for-2026",
            "the-north-london-girls-schools-11-what-parents-need-to-know",
            "the-11-plus-london-consortium-schools-which-schools-share-the-paper-and-how-offers-are-decided",
            "11-plus-exam-dates-2025-2026-independent-and-grammar-school-timetable",
            "common-entrance-13-plus-a-subject-by-subject-guide-to-marks-and-what-schools-require",
            "2026-grammar-school-league-tables-top-schools-ranked-by-gcse-results",
            "grammar-school-vs-private-school-which-is-best-for-your-child",
            "fsce-11-exam-2026-what-it-is-and-how-to-prepare",
            "manchester-grammar-school-11-format-past-papers-and-how-to-prepare",
            "creative-writing-for-the-11-plus-how-to-score-in-the-top-5",
            "11-english-comprehension-question-types-mark-schemes-and-practice-advice",
            "11-answer-sheet-practice-how-to-fill-in-bubble-sheets-and-avoid-costly-mistakes",
            "is-my-child-on-track-for-the-11-a-year-by-year-readiness-guide",
            "is-the-11-plus-too-stressful-how-to-build-resilience-in-your-child",
        ],
        "Medical School &amp; Oxbridge": [
            "ucat-score-requirements-for-uk-medical-schools-2025",
            "how-to-prepare-for-a-medical-school-mmi-interview",
            "a-level-subject-choices-for-medicine-applications",
            "ucat-cut-offs-for-every-uk-medical-school-5-year-trends-and-2026-predictions",
            "oxford-cambridge-and-ucl-medicine-mastering-the-ucat-for-elite-universities",
            "low-ucat-score-top-5-strategic-uk-medical-schools-to-apply-to-in-2026",
            "mmi-interviews-2026-50-real-scenarios-and-model-answer-frameworks",
            "medical-schools-that-dont-care-about-gcses-a-strategic-selection-guide",
            "how-to-get-2800-in-the-ucat-a-week-by-week-revision-roadmap",
            "oxbridge-interview-questions-100-real-examples-for-every-major-subject",
            "what-is-super-curricular-how-to-build-a-profile-for-oxford-and-cambridge",
            "oxford-vs-cambridge-which-university-is-easier-for-your-subject",
            "oxford-vs-cambridge-interview-key-differences-by-subject-2026",
            "contextual-admissions-how-your-background-can-lower-your-offer-requirements",
            "the-new-esat-and-tmua-exams-a-preparation-guide-for-oxbridge-2026",
            "oxford-maths-interview-questions-2026-with-step-by-step-model-answers",
            "cambridge-medicine-interview-questions-2026-science-questions-and-how-to-answer-them",
            "oxford-ppe-interview-questions-2026-with-model-answers",
            "cambridge-law-interview-questions-2026-real-examples-and-how-to-structure-answers",
            "oxford-physics-interview-questions-2026-estimation-problems-and-worked-solutions",
            "the-hardest-oxford-and-cambridge-interview-questions-2026-with-model-answers",
            "how-to-answer-oxford-interview-questions-when-you-dont-know-the-answer",
            "what-grade-do-you-need-for-oxbridge-chemistry",
        ],
        "GCSE, A-Level &amp; Tuition": [
            "how-long-does-gcse-revision-take",
            "triple-vs-double-science-gcse",
            "online-tutoring-vs-in-person-tutoring-for-gcse",
            "how-to-find-a-good-private-tutor",
            "is-private-tuition-worth-it-a-cost-benefit-analysis-of-1-to-1-learning",
            "ucas-personal-statement-guide",
            "the-new-ucas-personal-statement-2026-a-guide-to-the-3-question-format",
        ],
    }

    # Build a lookup: slug → title from CSV
    slug_to_title = {_slugify(row["title"]): row["title"] for row in posts}

    categorised_slugs = {s for slugs in BLOG_CATEGORIES.values() for s in slugs}

    category_html = ""
    for cat_name, slugs in BLOG_CATEGORIES.items():
        category_html += f"<h2>{cat_name}</h2>\n"
        for slug in slugs:
            title = slug_to_title.get(slug, slug.replace("-", " ").title())
            category_html += f'  <p><a href="{slug}"><strong>{title}</strong></a></p>\n'

    # Any posts in the CSV that weren't manually categorised go into a catch-all
    uncategorised = [
        row for row in posts
        if _slugify(row["title"]) not in categorised_slugs
        and _slugify(row["title"]) not in {s["slug"] for s in SUCCESS_STORIES}
    ]
    if uncategorised:
        category_html += "<h2>More Articles</h2>\n"
        for row in uncategorised:
            slug = _slugify(row["title"])
            category_html += f'  <p><a href="{slug}"><strong>{row["title"]}</strong></a></p>\n'

    blog_content = (
        "<p>Practical, expert-backed guidance for UK parents and students on selective school "
        "entry, GCSEs, A-Levels, medical school applications, Oxbridge, and more.</p>\n"
        "<h2>&#11088; Student Success Stories</h2>\n"
        + "\n".join(success_items)
        + "\n" + category_html
    )

    blog_crumb = breadcrumb_schema("blog", "blog", "Blog")
    blog_html = page_template(
        "Tutoring Advice and Guides",
        blog_content,
        meta_desc=("Expert tutoring advice for UK parents and students. School entrance results, "
                   "11+ guides, Oxbridge interview prep, UCAT, GCSE and A-Level advice from Leading Tuition."),
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
1. Oxford PPE interviews test three disciplines — what question types appear for each (Philosophy: logic, thought experiments, conceptual analysis; Politics: current affairs + political theory; Economics: micro/macro concepts, graphs, data)?
2. Philosophy is the discipline most candidates underprepare for — what does a strong philosophical argument look like under interview pressure? How do tutors push back and what should candidates do when challenged?
3. What does a strong PPE answer look like — how should candidates link 2026 current affairs to philosophical and economic frameworks in a single coherent answer?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,400 to 1,700 words
- Opening paragraph (40–60 words): direct answer — what Oxford PPE interviews test across all three disciplines, the tutorial format, and why model answers help. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Do Oxford PPE Interviews Actually Test in 2026?
  2. Philosophy Questions: Thought Experiments and Logic — 4 Full Model Answers
  3. Philosophy Under Pressure: How to Handle Tutor Push-Back and Maintain Your Argument
  4. Politics Questions: Current Affairs and Political Theory — 4 Real-Style Examples
  5. Economics Questions: Graphs, Opportunity Cost, and Microeconomics Problems with Worked Solutions
  6. Linking All Three Disciplines: A 2026 Cheat Sheet for PPE
  7. How Oxford PPE Interviews Are Structured and What to Expect
  8. Frequently Asked Questions
- Must include:
  - A table: Discipline | Example question | Framework to use | What tutors reward
  - Philosophy section must be the most detailed: 4 worked examples covering (a) a trolley-problem variation with a full model answer and defence, (b) a personal identity puzzle, (c) a logic/syllogism problem, (d) a "what is justice?" style open question — each with a 3–4 sentence model answer AND a note on how to respond if the tutor challenges your position
  - Philosophy push-back section: a sample tutor challenge ("But doesn't that imply X?") and 3 techniques for maintaining a position while genuinely engaging with the objection
  - Politics examples: 2026-relevant topics (AI governance, fiscal austerity, democratic backsliding) linked to social contract theory, Rawls, democratic legitimacy
  - Economics examples: supply/demand shift with a graph description, a simple opportunity cost problem with full workings, one data interpretation question
  - The cheat sheet: 4 current 2026 news items each mapped to a Philosophy concept, a Politics theory, and an Economics principle
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford PPE and philosophy interview questions with model answers</a>
- FAQ must address: whether candidates need prior economics A-level, how many Oxford PPE interviews candidates have, whether interviewers share questions across colleges, and how much current affairs knowledge is required
"""

    if slug == "oxford-vs-cambridge-interview-key-differences-by-subject-2026":
        return f"""
{master_context}

Before writing, think through:
1. What are the genuine structural differences between Oxford and Cambridge interviews (format, number, length, use of material, college variation)?
2. For each major subject — Maths, Medicine, Sciences, Engineering, Economics, History, English, Philosophy/PPE, Geography — how does the question style and emphasis differ?
3. What concrete example question would an Oxford interviewer vs Cambridge interviewer ask for the same subject — and why does that difference matter for preparation?

Now write a detailed blog post in HTML: {title}

Use this as the page H1: Oxford vs Cambridge Interview 2026: Key Differences by Subject with Model Questions

Target keyword: {keyword}

Requirements:
- Length: 1,500 to 1,800 words
- Opening paragraph (40–60 words): direct answer — Oxford and Cambridge both use subject-based tutorial/supervision-style interviews, but the question style, format, and depth of follow-up differ in ways that fundamentally change how candidates should prepare. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. Oxford vs Cambridge Interview Format: Structure, Length, and Number of Interviews
  2. Maths: Oxford First Principles vs Cambridge Applied Problems — with Real Example Questions
  3. Medicine: Oxford's Ethics and Science Mix vs Cambridge's Pure Science Focus
  4. Sciences and Engineering: How Practical and Theoretical Emphasis Differs
  5. Economics, PPE, and Social Sciences: Conceptual Frameworks vs Current Affairs
  6. English, History, and Humanities: Tutorial-Style Close Reading vs Supervision-Style Debate
  7. Frequently Asked Questions
- Must include:
  - A master comparison table with columns: Subject | Oxford question style | Cambridge question style | Key prep difference
  - For each subject section: one concrete example Oxford question AND one concrete Cambridge question for the same subject, showing the stylistic difference
  - Model answer sketch (2–3 sentences) showing the approach for each example question
  - The college variation point: both universities show significant college-to-college variation — candidates must research their specific college
  - Practical "If you applied to Oxford [Subject], prioritise X; if Cambridge [Subject], prioritise Y" takeaways throughout
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">subject-specific Oxford and Cambridge interview questions and model answers</a>
- FAQ must address: whether candidates can apply to both Oxford and Cambridge (they cannot in the same year), how to find college-specific interview styles, whether subject choice affects the number of interviews, and whether interview performance outweighs predicted grades
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

    if slug == "the-11-plus-london-consortium-schools-which-schools-share-the-paper-and-how-offers-are-decided":
        return f"""
{master_context}

Before writing, think through:
1. Which independent schools in London use a shared or co-ordinated 11+ exam — including the North London girls' schools consortium (NLCS, South Hampstead High, Channing, Highgate for girls) and the South London independent schools that share a paper (Alleyn's, JAGS, Dulwich College, CLSG, KCS Wimbledon)?
2. What is the exact timeline parents face — registration deadlines in May/June of Year 5, ISEB Common Pre-Test (used by some schools for pre-registration), main exam sittings in October/November of Year 6, interviews in December/January, offers in January/February?
3. How do consortium schools rank-order candidates across the shared paper, and how do parents navigate applying to multiple schools in the same sitting?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph (40–60 words): explain that "consortium" is used informally to describe groups of schools sharing exam infrastructure — make clear there are two main groups in London (North London girls' schools, South London independents) and that parents often apply to two or three schools in the same sitting
- Include these exact <h2> sections in this order:
  1. What Is the 11+ London Consortium?
  2. The North London Girls' Schools: Shared Paper and Key Facts
  3. The South London Independents: Alleyn's, JAGS, Dulwich College and Others
  4. The ISEB Common Pre-Test: How It Fits Into the Consortium Process
  5. The Timeline From Registration to Offer
  6. How Schools Rank-Order Candidates Across a Shared Paper
  7. Frequently Asked Questions
- Must include:
  - North London consortium: NLCS (~1,000 applicants for 120 places), South Hampstead High (~800 for 90 places), Channing (~600 for 72 places), Highgate (co-ed from 11, ~700 for 100 places)
  - South London group: Alleyn's, Dulwich College (boys), JAGS, KCS Wimbledon, Streatham and Clapham High — these schools often share exam sittings in late October/early November
  - ISEB Common Pre-Test: used by some schools (Haberdashers', HBS, Eton at 11+) as a pre-registration filter; scores 60–140, threshold approximately 115; schools receive results directly
  - Timeline table or list: May/June Year 5 (registration opens), September Year 6 (ISEB pre-test if applicable), October/November Year 6 (main exam sitting), December/January (interviews at shortlisted schools), January/February (offers)
  - How rank-ordering works: each school scores its own paper, shares the sitting date but not the marking — candidates are not ranked across schools, only within each school's own applicant pool
  - At a natural point where preparation materials are discussed, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/11-plus">past papers from consortium schools and North London independents</a>
- FAQ must address: whether applying to two consortium schools is allowed, how the ISEB pre-test affects consortium admissions, whether interview performance overrides exam scores, and what happens if a child receives two offers
"""

    if slug == "11-plus-exam-dates-2025-2026-independent-and-grammar-school-timetable":
        return f"""
{master_context}

Before writing, think through:
1. What are the actual exam dates and registration deadlines for major selective schools in England for the 2025-2026 admissions cycle (Year 6 children sitting exams in autumn 2025 for September 2026 entry)?
2. How do grammar school exam dates (typically September or early October, run by local authorities) differ from independent school exam dates (typically October/November, run by the schools themselves)?
3. What do parents most commonly get wrong about the timetable — missing registration deadlines, not realising some schools require separate registration for each child, confusing offer dates with decision deadlines?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,200 to 1,500 words
- Opening paragraph (40–60 words): explain that 11+ exam dates vary significantly by school type and region, and that missing a registration deadline is typically fatal to an application — the most common and most avoidable mistake
- Include these exact <h2> sections in this order:
  1. How 11+ Exam Dates Work: Grammar Schools vs Independent Schools
  2. Grammar School Exam Dates 2025: Key Regions and Timetables
  3. Independent School Exam Dates 2025: London and South-East
  4. Registration Deadlines: When You Must Apply
  5. Interview and Offer Dates: What Happens After the Exam
  6. How to Build a Personal Exam Calendar
  7. Frequently Asked Questions
- Must include an HTML <table> in section 2 with columns: School/Consortium, Exam Date (Approx), Registration Deadline, Exam Format. Include: Sutton Grammar Schools (GL Assessment, September 2025, deadline June 2025), Barnet grammars — QE Boys and Henrietta Barnett (school own exam, October 2025, deadline September 2025), Slough consortium (GL, September 2025, deadline May 2025), Kent grammar schools (GL, September 2025, deadline June 2025), Bucks grammar schools (GL, September 2025, deadline June 2025)
- Must include a second HTML <table> in section 3 with columns: School, Exam Date (Approx), Registration Opens, Format. Include: Haberdashers' Boys and Girls (ISEB pre-test June 2025, main exam October 2025), NLCS and South Hampstead High (own paper, October/November 2025, registration May/June 2025), Latymer Upper (own paper, October 2025), St Paul's Girls' School (own paper, September 2025 first round), Dulwich College, Alleyn's and JAGS (own papers, November 2025)
- At a natural point where school research is discussed, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/11-plus/">school-specific 11+ preparation guides</a>
- FAQ must address: what happens if two exams clash on the same day, whether registration deadlines are ever extended, how early preparation should start relative to exam dates, and what to do if you miss the registration window
"""

    if slug == "common-entrance-13-plus-a-subject-by-subject-guide-to-marks-and-what-schools-require":
        return f"""
{master_context}

Before writing, think through:
1. What does Common Entrance at 13+ actually test in each core subject — English (composition and comprehension separately), Maths (syllabus includes algebra, geometry, statistics), Science (single paper covering biology, chemistry and physics unless sat separately), French (listening, reading, writing, speaking), History, Geography, Religious Studies?
2. What mark thresholds do schools use — 60% is typically the minimum pass, 65% is solid, 70%+ is distinction — but how does this vary by school (Eton expects 70%+ across core subjects, many boarding schools are happy with 65% overall)?
3. What is the relationship between the ISEB Common Pre-Test (taken in Year 6) and Common Entrance (taken at end of Year 8) — and what happens at schools that set their own papers instead of using CE?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): establish what Common Entrance is (the shared examination at 13+ set by ISEB, used by most independent senior schools in England and Wales), when it is sat (May/June of Year 8), and why marks matter differently at different schools
- Include these exact <h2> sections in this order:
  1. What Is Common Entrance at 13+?
  2. English: What Is Tested and How It Is Marked
  3. Mathematics: Syllabus, Paper Structure and Common Mistakes
  4. Science: Single Paper or Three Separate Sciences?
  5. French, History, Geography and Other Subjects
  6. What Mark Do You Need? School-by-School Thresholds
  7. Schools That Don't Use Common Entrance
  8. Frequently Asked Questions
- Must include an HTML <table> in section 6 with columns: School, Minimum CE Mark, Notes. Include at least 6 schools: Eton College (70%+ across core subjects, pre-test conditional place confirmed on CE performance), Harrow School (65%+, interviews also weighted), Winchester College (does not use standard CE — own papers), Marlborough College (60–65%, CE plus interview), Rugby School (60%, CE plus report from current school), Sherborne School (60%+)
- Must include in section 7: Winchester College (own papers, Winchester College entrance examination, entirely separate from CE syllabus), Charterhouse (own papers for scholarship candidates), and a brief note that Eton King's Scholars sit a separate scholarship examination
- At a natural point where 13+ preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/13-plus">Common Entrance past papers and 13+ preparation resources</a>
- FAQ must address: whether CE marks are standardised across all schools, how the ISEB pre-test at Year 6 relates to the CE at Year 8, what happens if a pupil fails CE after receiving a conditional offer, and how CE differs from school scholarship examinations
"""

    # ── New Oxbridge interview subject pages ──────────────────────────────────

    if slug == "oxford-chemistry-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Chemistry interviews test both A-level mastery and genuine curiosity — what question types appear (organic mechanism arrow-pushing, periodic trends, electrochemistry, spectroscopy, reaction kinetics, novel synthesis problems)?
2. What does a strong Oxford Chemistry answer look like — how do candidates show chemical intuition rather than just reciting facts?
3. Which topics most frequently trip up candidates and why?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Chemistry interviews go beyond A-level recall, testing how candidates apply chemical principles to unfamiliar problems. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Chemistry Interviews Test in 2026
  2. Organic Chemistry Questions: Mechanism Arrow-Pushing with Full Model Answers
  3. Inorganic and Physical Chemistry: Trends, Bonding, and Energetics Problems
  4. Novel and Unfamiliar Problems: Applying Principles You Know to Situations You Haven't Seen
  5. The Most Common Mistakes Oxford Chemistry Candidates Make
  6. How to Prepare: What to Read and Practise Before Interview Day
  7. Frequently Asked Questions
- Must include:
  - 5 fully worked Q&A examples across the subject sections, each with the question, a model answer, and a note on what the interviewer is actually assessing
  - At least one organic mechanism problem shown step by step (with arrow notation described in text)
  - A "common mistakes" table: Mistake | Why it happens | What to do instead
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Chemistry interview questions with full model answers</a>
- FAQ must address: whether the Oxford Chemistry Aptitude Test (CAT) is used in the interview, how many interviews Oxford Chemistry applicants have, whether university-level chemistry is expected, and how to handle being given a mechanism you have never seen before
"""

    if slug == "cambridge-natural-sciences-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Natural Sciences is unique — applicants are interviewed by two departments and must show breadth across sciences. What question types appear across Biology, Chemistry, Physics, and Earth Sciences tracks?
2. What does it mean to show "cross-disciplinary thinking" and how do interviewers test for it?
3. How does the NatSci interview differ from applying to a single science subject — what should candidates emphasise that a pure Chemistry or Biology applicant would not?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge NatSci interviews test breadth as well as depth, with candidates typically interviewed in two subjects. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge Natural Sciences Interviews Work in 2026
  2. Biology Track Questions: Experimental Design and Data Interpretation with Model Answers
  3. Chemistry Track Questions: Mechanisms, Trends, and Applied Problems with Model Answers
  4. Physics Track Questions: Conceptual Problems and Estimation with Model Answers
  5. Showing Cross-Disciplinary Thinking: What Cambridge NatSci Tutors Actually Look For
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As across the subject tracks, each with model answer and tutor note
  - A table: NatSci track | Typical interview format | Example question type | Key preparation focus
  - A specific section on cross-disciplinary questions (e.g. applying physics principles to a biology problem) with one worked example
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Natural Sciences interview questions and worked solutions</a>
- FAQ must address: how many NatSci interviews Cambridge candidates typically have, whether candidates can be interviewed in subjects outside their A-level choices, how the pre-interview assessment relates to the interview, and what happens if a candidate underperforms in one of the two subject interviews
"""

    if slug == "cambridge-maths-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Maths interviews emphasise applied problem-solving and the ability to work through unfamiliar problems under guidance — how does this differ from Oxford Maths (which leans to pure/proof-based)?
2. What problem types appear (graph sketching, integration, series, proof by induction, combinatorics, geometry, real analysis introduction)?
3. What does a strong Cambridge Maths interview answer look like — how should candidates vocalise their reasoning and handle being guided toward a solution?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Maths interviews test how you think through problems, not just whether you know the answer. No formula sheets; reasoning aloud is essential. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Cambridge Maths Interviews Test in 2026
  2. Graph Sketching and Calculus: 3 Worked Problems with Full Solutions
  3. Proof and Pure Mathematics: How Cambridge Tests Mathematical Rigour
  4. Problem-Solving Under Guidance: What to Do When You Get Stuck
  5. Cambridge Maths vs Oxford Maths Interviews: Key Differences
  6. Frequently Asked Questions
- Must include:
  - 5 fully worked problems across the sections, each with full step-by-step solution and a note on what reasoning the interviewer expects to see verbalised
  - A graph sketching example with key features described (asymptotes, turning points, behaviour at infinity)
  - A practical "what to say when you don't know where to start" script for candidates
  - Connection to STEP preparation: Cambridge expects STEP preparation and problem-sets — explain how to use STEP for interview prep
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Maths interview questions with step-by-step worked solutions</a>
- FAQ must address: whether Cambridge Maths interviews use the STEP paper directly, how many interviews Cambridge Maths candidates typically have, whether A-level Further Maths is essential, and how to prepare if you find STEP questions too hard
"""

    if slug == "oxford-computer-science-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford CS interviews test algorithmic thinking, logic, and mathematical reasoning — what problem types appear (algorithm tracing, big-O complexity, data structures, graph problems, logic puzzles, mathematical induction)?
2. What does a strong Oxford CS answer look like — how do candidates show structured thinking rather than just producing code?
3. How much programming experience is assumed and what mathematical background matters most?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford CS interviews test how you think algorithmically and mathematically, not your coding fluency. No specific programming language is required. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Computer Science Interviews Test in 2026
  2. Algorithm and Data Structure Questions: 4 Worked Examples
  3. Logic and Discrete Mathematics Problems with Model Answers
  4. Complexity and Problem Analysis: What Big-O Questions Actually Test
  5. How to Think Aloud in an Oxford CS Interview
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As including: one algorithm trace (walk through a sorting algorithm step by step), one data structure choice question with justification, one logic puzzle, one big-O analysis
  - Pseudo-code style used (not tied to any specific language) for any algorithm examples
  - A "thinking aloud" model script: what a candidate says when working through an algorithm they haven't seen before
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Computer Science interview questions with worked solutions</a>
- FAQ must address: whether candidates need to know a specific programming language, whether A-level Further Maths is required, how many interviews Oxford CS applicants typically have, and whether the MAT is used during the interview
"""

    if slug == "cambridge-economics-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Economics interviews test economic reasoning from first principles — what question types appear (supply/demand shifts, game theory, market failure, current economic policy, data interpretation, elasticity problems)?
2. What does a strong Cambridge Economics answer look like — how do candidates apply microeconomic and macroeconomic frameworks to unfamiliar scenarios?
3. What 2026 economic events and policy debates are most relevant for candidates to know?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Economics interviews test your ability to apply economic logic, not recall of textbook content. Graph drawing and thinking through trade-offs are central. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Cambridge Economics Interviews Test in 2026
  2. Microeconomics Questions: Markets, Elasticity, and Game Theory with Model Answers
  3. Macroeconomics Questions: Policy, Inflation, and Growth with Worked Answers
  4. Data and Graph Interpretation: How to Analyse an Unfamiliar Chart Under Pressure
  5. Current Affairs for Cambridge Economics: 2026 Topics You Should Know
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full model answers and tutor commentary
  - One graph description (supply-demand shift or AD-AS) with the analysis narrated step by step
  - A current affairs section linking 2026 economic issues (e.g. UK fiscal policy, interest rates, AI and labour markets) to core economic frameworks
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Economics interview questions with model answers</a>
- FAQ must address: whether A-level Economics is required for Cambridge Economics, how many interviews candidates typically have, whether Mathematics A-level is needed, and how much current affairs knowledge is expected
"""

    if slug == "oxford-medicine-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Medicine uses a traditional panel interview format (NOT MMI) — what question types appear (scientific reasoning, ethical dilemmas, motivation, data interpretation, news in medicine)?
2. Oxford Medicine interviews are known for pushing candidates on scientific reasoning — what does "thinking like a scientist" look like in practice in the interview room?
3. What ethical frameworks are most relevant and how should candidates apply them without sounding like they memorised a textbook?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Medicine uses a traditional panel interview (not MMI), testing scientific reasoning, ethics, and genuine motivation for medicine. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Oxford Medicine Interviews Work in 2026 (Panel Format, Not MMI)
  2. Scientific Reasoning Questions: Data, Biology, and Medical Science with Model Answers
  3. Ethical Scenarios: How to Apply a Framework Without Sounding Robotic
  4. Motivation and Personal Statement Questions: What Oxford Medicine Tutors Look For
  5. Current Issues in Medicine: 2026 Topics Every Applicant Should Know
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As across the sections, each with model answer and specific note on what makes it strong
  - An ethics framework presented naturally (not as a numbered list to memorise but as a way of thinking): considering consequences, duties, patient autonomy, and systemic fairness
  - One scientific data interpretation question (e.g. interpret a graph or explain a medical phenomenon) with full model answer
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Medicine interview questions with model answers</a>
- FAQ must address: how many interviews Oxford Medicine applicants typically have, whether the BMAT is still used (it was discontinued — clarify), what the difference is between Oxford and Cambridge Medicine interviews, and whether work experience is discussed in depth
"""

    if slug == "oxford-engineering-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Engineering interviews combine physics application, mathematics, and materials/structural reasoning — what question types appear (mechanics, stress and strain, fluid dynamics, electrical circuits, dimensional analysis, design problems)?
2. What does a strong Oxford Engineering answer look like — how do candidates show engineering intuition rather than just A-level recall?
3. What makes Oxford Engineering interviews distinctive from Cambridge Engineering?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Engineering interviews test applied physics and mathematical reasoning, not engineering knowledge specifically. Thinking through novel problems under guidance is the key skill. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Engineering Interviews Test in 2026
  2. Mechanics and Applied Physics: 3 Worked Problems with Full Solutions
  3. Materials, Structures, and Design Questions with Model Answers
  4. Mathematical Reasoning in Engineering Contexts
  5. Oxford Engineering vs Cambridge Engineering: Interview Style Differences
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full step-by-step solutions and tutor notes on reasoning
  - One estimation/Fermi problem relevant to engineering (e.g. estimate the force on a bridge support)
  - One design-a-solution problem with a worked reasoning approach (not a fixed answer, but a structured way to think through it)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Engineering interview questions with worked solutions</a>
- FAQ must address: whether A-level Physics is essential, how many interviews Oxford Engineering applicants have, whether the PAT is used during the interview, and whether candidates are expected to have engineering work experience
"""

    if slug == "cambridge-engineering-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Engineering interviews lean more mathematical than Oxford's — what question types appear (differential equations, mathematical modelling, mechanics, electrical theory, dimensional analysis)?
2. What does a strong Cambridge Engineering answer look like — how do candidates demonstrate mathematical engineering rather than just applied physics?
3. How does the Cambridge Engineering interview connect to the ENGAA (Engineering Admissions Assessment)?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Engineering interviews are more mathematically rigorous than Oxford's, testing differential equations, mathematical modelling, and physical reasoning. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge Engineering Interviews Work in 2026
  2. Mathematical Engineering Problems: Differential Equations and Modelling with Worked Solutions
  3. Applied Physics and Mechanics Questions with Model Answers
  4. The ENGAA Connection: What Carries Over from the Admissions Assessment
  5. Cambridge Engineering vs Oxford Engineering: Key Interview Differences
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As, with at least one involving a differential equation set up from a physical scenario
  - A comparison of Oxford vs Cambridge Engineering interview style (Oxford: more intuitive/estimation; Cambridge: more formal mathematics)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Engineering interview questions with worked solutions</a>
- FAQ must address: whether Further Maths A-level is expected, how many interviews Cambridge Engineering candidates have, what the ENGAA tests and how it relates to the interview, and whether candidates need prior engineering knowledge
"""

    if slug == "oxford-biology-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Biology interviews test experimental thinking and the ability to reason from data — what question types appear (experimental design, data interpretation, genetics, evolution, physiology, ecology, biochemistry at A-level)?
2. What does a strong Oxford Biology answer look like — how do candidates demonstrate scientific rigour while remaining genuinely curious?
3. What are the most commonly tested A-level Biology extension topics in Oxford interviews?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Biology interviews test your ability to think like a scientist: designing experiments, interpreting data, and extending familiar concepts into unfamiliar territory. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Biology Interviews Test in 2026
  2. Experimental Design Questions: How to Plan and Critique an Experiment
  3. Data Interpretation: Graphs, Tables, and Statistical Questions with Model Answers
  4. Genetics, Evolution, and Physiology: 3 Worked Q&As
  5. Extending Beyond A-Level: Questions That Go Further
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full model answers and tutor notes
  - One experimental design question with a worked answer showing controls, variables, and how to critique a flawed experimental setup
  - One data interpretation question (describe the graph, then explain the biological mechanism)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Biology interview questions with worked solutions</a>
- FAQ must address: whether A-level Chemistry is needed for Oxford Biology, how many interviews candidates have, whether candidates are expected to have read beyond A-level, and how the Oxford Biology admissions test relates to the interview
"""

    if slug == "cambridge-computer-science-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge CS interviews are heavily mathematical — what problem types appear (combinatorics, graph theory, logic, algorithm design, formal proof, probability)?
2. How does Cambridge CS interview style differ from Oxford CS — Cambridge is more mathematically formal while Oxford emphasises algorithmic intuition?
3. What does a strong Cambridge CS answer look like under interview pressure?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Computer Science interviews are among the most mathematically rigorous at any UK university, combining algorithm design, discrete mathematics, and formal logic. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Cambridge Computer Science Interviews Test in 2026
  2. Algorithm Design and Complexity: 3 Worked Problems with Full Solutions
  3. Mathematical Logic and Discrete Mathematics Questions
  4. Cambridge CS vs Oxford CS: Interview Style Differences
  5. How to Prepare for the Most Mathematical CS Interview in the UK
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full solutions and reasoning notes
  - One formal proof or induction example
  - A comparison table: Cambridge CS vs Oxford CS — question type, mathematical rigour, expected background
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Computer Science interview questions with worked solutions</a>
- FAQ must address: whether candidates need A-level Further Mathematics, whether coding knowledge is tested, how many interviews Cambridge CS applicants have, and whether the Cambridge CS admissions test feeds into the interview
"""

    if slug == "oxford-economics-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Economics interviews test mathematical reasoning and economic intuition — what question types appear (supply/demand, game theory, welfare economics, current policy, mathematical problem-solving, graph interpretation)?
2. Oxford Economics is mathematically demanding — how do interviews test the mathematical side alongside economic reasoning?
3. What 2026 UK and global economic events should candidates know about?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Economics interviews combine mathematical problem-solving with economic reasoning. Candidates who can apply economic logic to novel scenarios and interpret data confidently perform best. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Economics Interviews Test in 2026
  2. Microeconomics and Market Analysis: 3 Worked Q&As with Model Answers
  3. Mathematical Economics Problems: Graphs, Functions, and Optimisation
  4. Current Affairs for Oxford Economics: 2026 Events and Frameworks
  5. Oxford Economics vs Cambridge Economics: Interview Style Comparison
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full model answers and tutor notes
  - One mathematical economics problem (e.g. find the profit-maximising output given a demand function)
  - Current affairs section linking 2026 economic events to core frameworks
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Economics interview questions with model answers</a>
- FAQ must address: whether A-level Economics is required, how much mathematics is expected, how many interviews Oxford Economics applicants have, and whether candidates need to have a specific economic viewpoint
"""

    if slug == "oxford-english-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford English interviews are famous for unseen passage analysis — candidates are given a passage they have never read and must construct an argument about it in real time. What does a high-scoring response look like?
2. What literary and analytical frameworks does a candidate need — and how do they apply them without sounding mechanical?
3. How does Oxford English differ from Cambridge English in interview style?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford English interviews centre on unseen passage analysis. Tutors want to see candidates read carefully, form an argument quickly, and defend it intelligently. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Oxford English Interviews Work in 2026
  2. Unseen Passage Analysis: A Step-by-Step Method with Worked Example
  3. Building and Defending a Literary Argument Under Pressure
  4. Personal Statement and Reading Questions: What to Expect
  5. Oxford English vs Cambridge English: Interview Style Differences
  6. Frequently Asked Questions
- Must include:
  - A worked unseen passage example: present a short passage (approximately 8–10 lines of verse or prose), then model a strong candidate response showing close reading, argument formation, and a specific analytical claim
  - A "mock dialogue" transcript showing tutor follow-up questions and strong candidate responses
  - The key distinction between a strong and average response (strong: makes a specific, arguable claim; average: describes what happens in the text)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford English interview questions with model answers</a>
- FAQ must address: whether candidates need to have read the whole text their passage is taken from, how many Oxford English interviews candidates have, whether creative writing appears in English interviews, and whether studying English A-level is necessary
"""

    if slug == "cambridge-english-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge English interviews emphasise historical and contextual reading alongside close textual analysis — how does this differ from Oxford English's primarily text-first approach?
2. Candidates are often given a passage and asked to situate it historically or generically — what does a strong contextualising response look like?
3. What personal statement questions commonly arise in Cambridge English interviews and what do tutors look for?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge English interviews test close reading alongside historical and contextual understanding. Tutors want to see how you situate a text, not just what you notice about it. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge English Interviews Work in 2026
  2. Close Reading with Historical Context: A Worked Passage Example
  3. Period and Genre Questions: Situating Texts in Literary History
  4. Personal Statement Deep-Dives: What Cambridge English Tutors Probe
  5. Cambridge English vs Oxford English: Key Interview Differences
  6. Frequently Asked Questions
- Must include:
  - A worked passage example with model response showing both close reading and contextual placement
  - A "mock dialogue" showing tutor push-back on a contextual claim and a strong candidate response
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge English interview questions with model answers</a>
- FAQ must address: how many Cambridge English interviews candidates have, whether Medieval English is tested, whether candidates are expected to know Old English, and how much weight personal statement reading carries
"""

    if slug == "oxford-history-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford History interviews typically involve source analysis and historical argument construction — what types of sources appear and what are candidates expected to do with them?
2. What makes a strong historical argument in an interview — how do tutors distinguish between descriptive and genuinely analytical responses?
3. What is the "defend a counter-intuitive position" approach that appears in Oxford History interviews and how should candidates handle it?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford History interviews test source analysis, argument construction, and willingness to engage with difficult historical questions. Tutors want analytical sharpness, not factual recall. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Oxford History Interviews Work in 2026
  2. Source Analysis: A Step-by-Step Method with Worked Example
  3. Constructing a Historical Argument Under Pressure
  4. Counter-Intuitive Positions: Defending an Uncomfortable Claim
  5. Personal Statement and Reading Questions in Oxford History Interviews
  6. Frequently Asked Questions
- Must include:
  - A worked source analysis example: provide a short primary source extract, model the analytical approach (provenance, purpose, context, significance) and show a candidate's worked response
  - A "counter-intuitive position" worked example: e.g. "Argue that the Black Death had positive long-term consequences" — model how to construct and sustain this argument
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford History interview questions with model answers</a>
- FAQ must address: which historical periods Oxford History interviews favour, how many interviews candidates have, whether prior History A-level is required, and whether world history or only British/European history appears
"""

    if slug == "cambridge-history-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge History interviews push deeper into historiography than Oxford — what does a historiographical debate question look like and how do candidates engage with competing historians' interpretations?
2. Cambridge History often asks candidates to defend a specific interpretive position against tutor challenge — what techniques help candidates hold their argument?
3. How does Cambridge History interview style differ from Oxford in terms of source use vs historiographical debate?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge History interviews go beyond source analysis into historiographical debate — you need to engage with how historians have disagreed and defend your own interpretation. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge History Interviews Work in 2026
  2. Historiographical Debate Questions: Engaging with Competing Interpretations
  3. Source Analysis at Cambridge: Similarities and Differences from Oxford
  4. Defending Your Interpretation: What Cambridge History Tutors Look For
  5. Cambridge History vs Oxford History: Interview Style Comparison
  6. Frequently Asked Questions
- Must include:
  - A worked historiographical debate example: present two conflicting historical interpretations of an event, then model how a candidate engages with both and defends their own position
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge History interview questions with model answers</a>
- FAQ must address: how many Cambridge History interviews candidates have, whether specific historical periods are favoured, whether candidates need to cite historians by name, and how much personal statement reading features in Cambridge History interviews
"""

    if slug == "oxford-philosophy-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Philosophy interviews (including Philosophy within PPE) test logical argument construction, conceptual analysis, and the ability to defend a position under sustained challenge — what question types appear (thought experiments, logical inference, conceptual distinctions, ethical dilemmas)?
2. What does a genuinely philosophical answer look like — how do candidates show precision and rigour without being mechanical?
3. How should candidates respond when a tutor challenges their position — what techniques preserve intellectual integrity while engaging with the objection?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Philosophy interviews test how you construct and defend an argument, not what philosophical positions you hold. Precision, intellectual honesty, and the ability to engage with push-back are what tutors reward. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Oxford Philosophy Interviews Test in 2026
  2. Thought Experiments: 4 Real-Style Questions with Full Model Answers
  3. Handling Tutor Push-Back: Defending Your Position Without Being Stubborn
  4. Conceptual Analysis Questions: Defining Terms Under Pressure
  5. Logic and Formal Reasoning in Philosophy Interviews
  6. Frequently Asked Questions
- Must include:
  - 5 worked philosophical Q&As: at least one thought experiment (trolley problem variation), one personal identity puzzle, one knowledge/epistemology question, one ethics dilemma, one conceptual analysis ("What do we mean by 'freedom'?")
  - Each worked answer must show: initial claim, the reasoning, a strong objection, and the candidate's response to that objection
  - A "push-back techniques" guide: 3 ways to respond when a tutor challenges your position (distinguish the objection, concede partially and reformulate, ask for clarification of the counterargument)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Philosophy interview questions with model answers</a>
- FAQ must address: whether candidates need prior Philosophy A-level or study, how many Oxford Philosophy interviews candidates have, whether formal logic is tested, and whether candidates are expected to know named philosophers
"""

    if slug == "cambridge-philosophy-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Philosophy interviews test rigorous argument construction and conceptual precision — what question types appear and how do they differ from Oxford Philosophy?
2. Cambridge Philosophy often connects to formal logic and analytic philosophy — how does this shape the question types that appear?
3. What does defending a philosophical claim look like in a Cambridge supervision-style interview?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Philosophy interviews test argument rigour and conceptual precision, often with a more analytic and formal emphasis than Oxford. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge Philosophy Interviews Work in 2026
  2. Analytic Philosophy Questions: Logic and Conceptual Analysis with Model Answers
  3. Thought Experiments and Ethical Reasoning at Cambridge
  4. Cambridge Philosophy vs Oxford Philosophy: Key Differences
  5. How to Prepare: What to Read and Practise
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with model answers and notes on what the interviewer is assessing
  - At least one formal logic question (simple valid/invalid argument assessment)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Philosophy interview questions with model answers</a>
- FAQ must address: whether candidates need A-level Philosophy, how many Cambridge Philosophy interviews candidates have, whether Cambridge Philosophy is part of a combined course, and what reading tutors most commonly ask about
"""

    if slug == "oxford-geography-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Geography interviews span both physical and human geography — what question types appear across these tracks (climate systems, geomorphology, urban policy, globalisation, migration, sustainability)?
2. What does data or map interpretation look like in an Oxford Geography interview and how should candidates approach it?
3. What current events in 2026 are most relevant for Oxford Geography candidates to know?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Geography interviews span physical and human geography, including data interpretation, policy analysis, and current global issues. Breadth of genuine interest matters. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Oxford Geography Interviews Work in 2026
  2. Physical Geography Questions: Climate, Geomorphology, and Systems Thinking
  3. Human Geography Questions: Policy, Globalisation, and Inequality
  4. Data and Map Interpretation: Worked Examples
  5. Current Issues for Oxford Geography Candidates: 2026 Topics
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full model answers and tutor notes
  - One data/map interpretation question with a worked analysis (describe what the data shows, explain the geographical process, consider limitations)
  - A 2026 current issues section linking recent events (climate policy, urban migration, resource conflicts) to geographical frameworks
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Geography interview questions with model answers</a>
- FAQ must address: whether candidates need both physical and human Geography A-level, how many Oxford Geography interviews candidates have, whether fieldwork experience features in the interview, and what the Oxford Geography admissions test covers
"""

    if slug == "cambridge-geography-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Geography interviews have a strong theoretical and conceptual emphasis — how does this show up in questions compared to Oxford Geography?
2. Cambridge Geography candidates are often asked to engage with a geographical debate or contested concept — what does a strong response to this look like?
3. What 2026 geographical issues are most relevant for Cambridge Geography applicants?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Geography interviews are theoretically rigorous, pushing candidates to engage with contested geographical concepts and current global debates. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge Geography Interviews Work in 2026
  2. Theoretical and Conceptual Geography Questions with Model Answers
  3. Physical Geography: Process, Systems, and Change
  4. Human Geography: Policy, Power, and Global Debates
  5. Cambridge Geography vs Oxford Geography: Interview Style Comparison
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full model answers
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Geography interview questions with model answers</a>
- FAQ must address: whether candidates need A-level Geography, how many Cambridge Geography interviews candidates have, whether the Cambridge Geography pre-interview assessment features in the interview, and how the Cambridge and Oxford interview styles compare
"""

    if slug == "oxford-modern-languages-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Modern Languages (MML) interviews are conducted partly in the target language — what does this involve and how should candidates prepare to discuss literature, film, and culture in their language?
2. What types of questions appear in the English-language component (translation discussion, cultural analysis, literary interpretation)?
3. How does the Oxford MML interview differ from a language A-level oral exam — what does genuine academic engagement with a language look like?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Modern Languages interviews are partly conducted in your target language and test literary analysis, cultural knowledge, and genuine academic interest. Language fluency alone is not enough. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Oxford Modern Languages Interviews Work in 2026
  2. In-Language Discussion: What to Expect and How to Prepare
  3. Literary Analysis Questions: Approaching an Unseen Text in Your Language
  4. Cultural Knowledge and Current Affairs in MML Interviews
  5. Translation Discussion and Linguistic Questions
  6. Frequently Asked Questions
- Must include:
  - Worked examples for both French and German/Spanish tracks where relevant
  - A worked in-language literary passage discussion (e.g. a short French poem or German prose extract) with model candidate responses
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Modern Languages interview questions with model answers</a>
- FAQ must address: whether candidates must achieve native-level fluency, how many Oxford MML interviews candidates have, whether candidates who took only one language can apply, and whether the Oxford MML interview includes linguistics questions
"""

    if slug == "cambridge-modern-languages-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Modern and Medieval Languages (MML) interviews cover similar ground to Oxford MML but with more emphasis on close textual analysis and linguistic study — how does this show up in questions?
2. Cambridge MML includes Medieval languages as a track — what does this involve in interview?
3. How should candidates prepare for in-language discussion and literary analysis at Cambridge?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Modern and Medieval Languages interviews test in-language literary analysis, linguistic curiosity, and cultural knowledge. Tutors want to see genuine intellectual engagement with language beyond A-level. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge MML Interviews Work in 2026
  2. In-Language Literary Analysis: Worked Examples for French, German, and Spanish
  3. Linguistic and Translation Questions at Cambridge
  4. Cambridge MML vs Oxford MML: Interview Style Differences
  5. How to Prepare for the Cambridge MML Interview
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As including at least one in-language example
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Modern Languages interview questions with model answers</a>
- FAQ must address: whether candidates need prior linguistics study, how many Cambridge MML interviews candidates have, whether the Medieval languages track involves Old or Middle English, and how in-language discussion is assessed
"""

    if slug == "cambridge-hsps-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge HSPS (Human, Social and Political Sciences) is an interdisciplinary degree — what does the interview test across its component disciplines (Sociology, Politics, Social Anthropology, Criminology)?
2. What does interdisciplinary thinking look like in an HSPS interview — how do candidates show they can move between social science frameworks?
3. What 2026 social and political events are most relevant for HSPS candidates to discuss?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge HSPS interviews test interdisciplinary social science reasoning across Politics, Sociology, and Social Anthropology. Tutors want candidates who can move between frameworks and engage with complex social questions. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. What Cambridge HSPS Interviews Test in 2026
  2. Politics and Political Theory Questions with Model Answers
  3. Sociology and Social Anthropology Questions with Model Answers
  4. Interdisciplinary Questions: Using Multiple Frameworks to Analyse One Problem
  5. Current Affairs for HSPS: 2026 Events and How to Frame Them
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As across the disciplines, each showing a candidate drawing on a relevant social science framework
  - One interdisciplinary example where a candidate is asked to analyse a social issue using both political and sociological lenses
  - A 2026 current affairs section linking recent events (political polarisation, immigration policy, social inequality) to HSPS frameworks
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge HSPS interview questions with model answers</a>
- FAQ must address: whether candidates need A-level Politics or Sociology, how many Cambridge HSPS interviews candidates have, how HSPS differs from PPE at Oxford, and whether criminology features in HSPS interviews
"""

    if slug == "oxford-veterinary-medicine-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Oxford Veterinary Medicine interviews combine scientific reasoning, animal biology, and ethical scenarios specific to veterinary practice — what question types appear?
2. What does a strong Vet Med answer look like — how do candidates show genuine passion for animal welfare alongside scientific rigour?
3. How does the Oxford Vet Med interview differ from the Cambridge Vet Med interview?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Oxford Veterinary Medicine interviews combine animal biology, ethical reasoning, and scientific problem-solving. Genuine experience with animals and scientific curiosity both matter. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Oxford Veterinary Medicine Interviews Work in 2026
  2. Animal Biology and Science Questions with Model Answers
  3. Ethical Scenarios in Vet Med: Animal Welfare, Owner Decisions, and Systemic Issues
  4. Motivation and Work Experience Questions: What Oxford Vet Med Tutors Look For
  5. Oxford Vet Med vs Cambridge Vet Med: Interview Differences
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As across the sections with full model answers and tutor notes
  - One ethical scenario worked in full (e.g. an owner refuses treatment their animal needs — how do you approach this?)
  - One scientific reasoning question (e.g. explain why cats cannot taste sweetness — what does this tell us about evolution?)
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Oxford Veterinary Medicine interview questions with model answers</a>
- FAQ must address: how much animal work experience is expected, how many interviews Oxford Vet Med applicants have, whether A-level Biology and Chemistry are both required, and whether the BMAT (discontinued) or other tests now apply
"""

    if slug == "cambridge-veterinary-medicine-interview-questions-2026-with-model-answers":
        return f"""
{master_context}

Before writing, think through:
1. Cambridge Veterinary Medicine interviews emphasise scientific reasoning alongside genuine commitment to animal welfare — what question types appear and how do they differ from Oxford Vet Med?
2. Cambridge Vet Med applicants are expected to have substantial animal experience — how does this come up in interview and what makes a strong answer about experience?
3. What scientific topics (physiology, anatomy, evolutionary biology, biochemistry) are most commonly tested?

Now write a detailed blog post in HTML: {title}

Target keyword: {keyword}

Requirements:
- Length: 1,300 to 1,600 words
- Opening paragraph (40–60 words): direct answer — Cambridge Veterinary Medicine interviews combine scientific problem-solving with animal welfare ethics and genuine passion for the profession. Substantial animal experience is expected and will be probed. Include "Updated April 2026 for 2026/27 entry."
- Include these exact <h2> sections in this order:
  1. How Cambridge Veterinary Medicine Interviews Work in 2026
  2. Scientific Reasoning Questions: Biology, Physiology, and Biochemistry with Model Answers
  3. Animal Welfare Ethics at Cambridge: Worked Scenarios
  4. Discussing Your Animal Experience: What Cambridge Vet Med Tutors Look For
  5. Cambridge Vet Med vs Oxford Vet Med: Key Interview Differences
  6. Frequently Asked Questions
- Must include:
  - 5 worked Q&As with full model answers
  - One detailed worked ethical scenario specific to veterinary medicine
  - At a natural point where preparation resources are mentioned, include this link woven into the prose — do NOT present it as a CTA or separate section: <a href="/resources/oxbridge-interview-questions">Cambridge Veterinary Medicine interview questions with model answers</a>
- FAQ must address: how much animal experience is expected, how many Cambridge Vet Med interviews applicants have, whether A-level Chemistry is required alongside Biology, and how the Cambridge Vet Med interview differs from a medical school interview
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
    # ── School entrance resource blog posts ───────────────────────────────────
    "the-11-plus-london-consortium-schools-which-schools-share-the-paper-and-how-offers-are-decided": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ school preparation guides hub at /11-plus/ using anchor text '11+ school-specific preparation guides', "
        "and link to the 11+ resources page at /resources/11-plus using anchor text 'past papers from consortium schools and North London independents'."
    ),
    "11-plus-exam-dates-2025-2026-independent-and-grammar-school-timetable": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 11+ school preparation guides hub at /11-plus/ using anchor text '11+ school-specific preparation guides', "
        "and link to the 11+ tuition page at /services/levels/11plus-tuition using anchor text '11+ tuition with Leading Tuition'."
    ),
    "common-entrance-13-plus-a-subject-by-subject-guide-to-marks-and-what-schools-require": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the 13+ resources page at /resources/13-plus using anchor text 'Common Entrance past papers and 13+ preparation resources', "
        "and link to the 13+ tuition page at /services/levels/13plus-tuition using anchor text '13+ and Common Entrance tuition'."
    ),
    # ── New Oxbridge interview subject pages ──────────────────────────────────
    "oxford-chemistry-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Chemistry interview questions with organic, inorganic and physical chemistry model answers', "
        "and link to the Chemistry interview preparation page at /oxbridge-interviews/chemistry-interview/ using anchor text 'Oxford Chemistry interview preparation with Leading Tuition'."
    ),
    "cambridge-natural-sciences-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Natural Sciences interview questions across biology, chemistry and physics', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Natural Sciences interview preparation with Leading Tuition'."
    ),
    "cambridge-maths-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Maths interview questions with step-by-step worked solutions', "
        "and link to the Maths interview preparation page at /oxbridge-interviews/maths-interview/ using anchor text 'Cambridge Maths interview preparation with Leading Tuition'."
    ),
    "oxford-computer-science-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Computer Science interview questions with algorithm and logic worked solutions', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Computer Science interview preparation with Leading Tuition'."
    ),
    "cambridge-economics-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Economics interview questions with microeconomics and macroeconomics model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Economics interview preparation with Leading Tuition'."
    ),
    "oxford-medicine-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Medicine interview questions including science reasoning and ethics scenarios', "
        "and link to the Medicine interview preparation page at /oxbridge-interviews/medicine-interview/ using anchor text 'Oxford Medicine interview preparation with Leading Tuition'."
    ),
    "oxford-engineering-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Engineering interview questions with mechanics and applied physics solutions', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Engineering interview preparation with Leading Tuition'."
    ),
    "cambridge-engineering-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Engineering interview questions with mathematical engineering worked solutions', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Engineering interview preparation with Leading Tuition'."
    ),
    "oxford-biology-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Biology interview questions with experimental design and data interpretation model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Biology interview preparation with Leading Tuition'."
    ),
    "cambridge-computer-science-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Computer Science interview questions with algorithm and discrete mathematics solutions', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Computer Science interview preparation with Leading Tuition'."
    ),
    "oxford-economics-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Economics interview questions with microeconomics and graph interpretation model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Economics interview preparation with Leading Tuition'."
    ),
    "oxford-english-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford English interview questions with unseen passage analysis model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford English interview preparation with Leading Tuition'."
    ),
    "cambridge-english-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge English interview questions with close reading and contextual analysis model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge English interview preparation with Leading Tuition'."
    ),
    "oxford-history-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford History interview questions with source analysis and argument construction model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford History interview preparation with Leading Tuition'."
    ),
    "cambridge-history-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge History interview questions with historiographical debate model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge History interview preparation with Leading Tuition'."
    ),
    "oxford-philosophy-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Philosophy interview questions with thought experiment and argument model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Philosophy interview preparation with Leading Tuition'."
    ),
    "cambridge-philosophy-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Philosophy interview questions with analytic philosophy and logic model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Philosophy interview preparation with Leading Tuition'."
    ),
    "oxford-geography-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Geography interview questions with physical and human geography model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Geography interview preparation with Leading Tuition'."
    ),
    "cambridge-geography-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Geography interview questions with physical and human geography model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Geography interview preparation with Leading Tuition'."
    ),
    "oxford-modern-languages-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Modern Languages interview questions with in-language literary analysis model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Modern Languages interview preparation with Leading Tuition'."
    ),
    "cambridge-modern-languages-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Modern Languages interview questions with literary analysis and in-language discussion model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Modern Languages interview preparation with Leading Tuition'."
    ),
    "cambridge-hsps-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge HSPS interview questions with politics, sociology, and social science model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge HSPS interview preparation with Leading Tuition'."
    ),
    "oxford-veterinary-medicine-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Oxford Veterinary Medicine interview questions with science reasoning and animal welfare ethics model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Oxford Veterinary Medicine interview preparation with Leading Tuition'."
    ),
    "cambridge-veterinary-medicine-interview-questions-2026-with-model-answers": (
        "At the end of this blog post, add a section titled 'Related Resources' containing these contextual links: "
        "link to the Oxbridge Interview Questions resources page at /resources/oxbridge-interview-questions using anchor text 'Cambridge Veterinary Medicine interview questions with biology, ethics, and animal welfare model answers', "
        "and link to the Oxbridge Interviews hub at /oxbridge-interviews/ using anchor text 'Cambridge Veterinary Medicine interview preparation with Leading Tuition'."
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
            "areaServed": {"@type": "Country", "name": "United Kingdom"}
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

    # ── University-specific metadata ─────────────────────────────────────────
    # Maps slug → (university, admissions_test, blog_url, blog_anchor,
    #              cross_link_url, cross_link_title, resources_anchor)
    OXFORD_SPECIFIC = {
        "oxford-maths-interview": (
            "Oxford", "MAT (Mathematics Admissions Test)",
            "/blog/oxford-maths-interview-questions-2026-with-step-by-step-model-answers",
            "Oxford Maths interview questions with step-by-step worked solutions",
            "/oxbridge-interviews/cambridge-maths-interview/",
            "Cambridge Mathematics Interview preparation",
            "Oxford Maths interview questions and model answers",
        ),
        "oxford-physics-interview": (
            "Oxford", "PAT (Physics Aptitude Test)",
            "/blog/oxford-physics-interview-questions-2026-estimation-problems-and-worked-solutions",
            "Oxford Physics interview questions including estimation and mechanics problems",
            "/oxbridge-interviews/cambridge-natural-sciences-interview/",
            "Cambridge Natural Sciences Interview preparation",
            "Oxford Physics interview questions with worked solutions",
        ),
        "oxford-chemistry-interview": (
            "Oxford", "CAT (Chemistry Aptitude Test)",
            "/blog/oxford-chemistry-interview-questions-2026-with-model-answers",
            "Oxford Chemistry interview questions with organic, inorganic and physical chemistry model answers",
            "/oxbridge-interviews/cambridge-natural-sciences-interview/",
            "Cambridge Natural Sciences Interview preparation",
            "Oxford Chemistry interview questions with model answers",
        ),
        "oxford-computer-science-interview": (
            "Oxford", "MAT (Mathematics Admissions Test)",
            "/blog/oxford-computer-science-interview-questions-2026-with-model-answers",
            "Oxford Computer Science interview questions with algorithm and problem-solving worked examples",
            "/oxbridge-interviews/cambridge-computer-science-interview/",
            "Cambridge Computer Science Interview preparation",
            "Oxford Computer Science interview questions and model answers",
        ),
        "oxford-engineering-interview": (
            "Oxford", "PAT (Physics Aptitude Test)",
            "/blog/oxford-engineering-interview-questions-2026-with-model-answers",
            "Oxford Engineering interview questions with mechanics and applied physics worked solutions",
            "/oxbridge-interviews/cambridge-engineering-interview/",
            "Cambridge Engineering Interview preparation",
            "Oxford Engineering interview questions with model answers",
        ),
        "oxford-biology-interview": (
            "Oxford", "No written test required",
            "/blog/oxford-biology-interview-questions-2026-with-model-answers",
            "Oxford Biology interview questions with experimental design and genetics worked examples",
            "/oxbridge-interviews/cambridge-natural-sciences-interview/",
            "Cambridge Natural Sciences Interview preparation",
            "Oxford Biology interview questions and model answers",
        ),
        "oxford-medicine-interview": (
            "Oxford", "No written test (UCAT required for shortlisting)",
            "/blog/oxford-medicine-interview-questions-2026-with-model-answers",
            "Oxford Medicine interview questions with ethics and scientific reasoning model answers",
            "/oxbridge-interviews/cambridge-medicine-interview/",
            "Cambridge Medicine Interview preparation",
            "Oxford Medicine interview questions with model answers",
        ),
        "oxford-economics-management-interview": (
            "Oxford", "TSA (Thinking Skills Assessment)",
            "/blog/oxford-economics-interview-questions-2026-with-model-answers",
            "Oxford Economics and Management interview questions with supply and demand and game theory worked examples",
            "/oxbridge-interviews/cambridge-economics-interview/",
            "Cambridge Economics Interview preparation",
            "Oxford Economics and Management interview questions and model answers",
        ),
        "oxford-english-interview": (
            "Oxford", "ELAT (English Literature Admissions Test, now discontinued — check current requirements)",
            "/blog/oxford-english-interview-questions-2026-with-model-answers",
            "Oxford English interview questions with unseen passage and literary argument model answers",
            "/oxbridge-interviews/cambridge-english-interview/",
            "Cambridge English Interview preparation",
            "Oxford English interview questions with model answers",
        ),
        "oxford-history-interview": (
            "Oxford", "HAT (History Aptitude Test)",
            "/blog/oxford-history-interview-questions-2026-with-model-answers",
            "Oxford History interview questions with source analysis and historical argument model answers",
            "/oxbridge-interviews/cambridge-history-interview/",
            "Cambridge History Interview preparation",
            "Oxford History interview questions with model answers",
        ),
        "oxford-philosophy-interview": (
            "Oxford", "TSA or PHIL test depending on course (PPE uses TSA; Philosophy & Theology uses PHIL)",
            "/blog/oxford-philosophy-interview-questions-2026-with-model-answers",
            "Oxford Philosophy interview questions with thought experiment and logical argument model answers",
            "/oxbridge-interviews/cambridge-philosophy-interview/",
            "Cambridge Philosophy Interview preparation",
            "Oxford Philosophy interview questions with model answers",
        ),
        "oxford-geography-interview": (
            "Oxford", "No written test required",
            "/blog/oxford-geography-interview-questions-2026-with-model-answers",
            "Oxford Geography interview questions with physical and human geography model answers",
            "/oxbridge-interviews/cambridge-geography-interview/",
            "Cambridge Geography Interview preparation",
            "Oxford Geography interview questions with model answers",
        ),
        "oxford-modern-languages-interview": (
            "Oxford", "MLAT (Modern Languages Admissions Test)",
            "/blog/oxford-modern-languages-interview-questions-2026-with-model-answers",
            "Oxford Modern Languages interview questions with literary discussion and language analysis model answers",
            "/oxbridge-interviews/cambridge-modern-languages-interview/",
            "Cambridge Modern Languages (MML) Interview preparation",
            "Oxford Modern Languages interview questions with model answers",
        ),
        "oxford-veterinary-medicine-interview": (
            "Oxford", "No written test required",
            "/blog/oxford-veterinary-medicine-interview-questions-2026-with-model-answers",
            "Oxford Veterinary Medicine interview questions with scientific reasoning and ethics model answers",
            "/oxbridge-interviews/cambridge-veterinary-medicine-interview/",
            "Cambridge Veterinary Medicine Interview preparation",
            "Oxford Veterinary Medicine interview questions with model answers",
        ),
    }

    CAMBRIDGE_SPECIFIC = {
        "cambridge-maths-interview": (
            "Cambridge", "STEP and/or TMUA",
            "/blog/cambridge-maths-interview-questions-2026-with-model-answers",
            "Cambridge Maths interview questions with step-by-step worked solutions",
            "/oxbridge-interviews/oxford-maths-interview/",
            "Oxford Mathematics Interview preparation",
            "Cambridge Maths interview questions and model answers",
        ),
        "cambridge-natural-sciences-interview": (
            "Cambridge", "ESAT (Engineering and Science Admissions Test)",
            "/blog/cambridge-natural-sciences-interview-questions-2026-with-model-answers",
            "Cambridge Natural Sciences interview questions with biology, chemistry and physics model answers",
            "/oxbridge-interviews/oxford-physics-interview/",
            "Oxford Physics Interview preparation",
            "Cambridge Natural Sciences interview questions with model answers",
        ),
        "cambridge-computer-science-interview": (
            "Cambridge", "TMUA (Test of Mathematics for University Admission)",
            "/blog/cambridge-computer-science-interview-questions-2026-with-model-answers",
            "Cambridge Computer Science interview questions with algorithm and mathematical reasoning model answers",
            "/oxbridge-interviews/oxford-computer-science-interview/",
            "Oxford Computer Science Interview preparation",
            "Cambridge Computer Science interview questions and model answers",
        ),
        "cambridge-engineering-interview": (
            "Cambridge", "ESAT (Engineering and Science Admissions Test)",
            "/blog/cambridge-engineering-interview-questions-2026-with-model-answers",
            "Cambridge Engineering interview questions with applied mathematics and physics model answers",
            "/oxbridge-interviews/oxford-engineering-interview/",
            "Oxford Engineering Interview preparation",
            "Cambridge Engineering interview questions and model answers",
        ),
        "cambridge-economics-interview": (
            "Cambridge", "TMUA (Test of Mathematics for University Admission)",
            "/blog/cambridge-economics-interview-questions-2026-with-model-answers",
            "Cambridge Economics interview questions with micro, macro and data interpretation model answers",
            "/oxbridge-interviews/oxford-economics-management-interview/",
            "Oxford Economics and Management Interview preparation",
            "Cambridge Economics interview questions with model answers",
        ),
        "cambridge-english-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-english-interview-questions-2026-with-model-answers",
            "Cambridge English interview questions with contextual reading and literary argument model answers",
            "/oxbridge-interviews/oxford-english-interview/",
            "Oxford English Interview preparation",
            "Cambridge English interview questions with model answers",
        ),
        "cambridge-history-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-history-interview-questions-2026-with-model-answers",
            "Cambridge History interview questions with historiographical debate and source analysis model answers",
            "/oxbridge-interviews/oxford-history-interview/",
            "Oxford History Interview preparation",
            "Cambridge History interview questions with model answers",
        ),
        "cambridge-philosophy-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-philosophy-interview-questions-2026-with-model-answers",
            "Cambridge Philosophy interview questions with conceptual analysis and argument evaluation model answers",
            "/oxbridge-interviews/oxford-philosophy-interview/",
            "Oxford Philosophy Interview preparation",
            "Cambridge Philosophy interview questions with model answers",
        ),
        "cambridge-geography-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-geography-interview-questions-2026-with-model-answers",
            "Cambridge Geography interview questions with physical and human geography model answers",
            "/oxbridge-interviews/oxford-geography-interview/",
            "Oxford Geography Interview preparation",
            "Cambridge Geography interview questions with model answers",
        ),
        "cambridge-modern-languages-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-modern-languages-interview-questions-2026-with-model-answers",
            "Cambridge Modern Languages interview questions with translation, literature and language in context model answers",
            "/oxbridge-interviews/oxford-modern-languages-interview/",
            "Oxford Modern Languages Interview preparation",
            "Cambridge Modern Languages (MML) interview questions with model answers",
        ),
        "cambridge-hsps-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-hsps-interview-questions-2026-with-model-answers",
            "Cambridge HSPS interview questions with social science reasoning and policy analysis model answers",
            "/oxbridge-interviews/ppe-interview/",
            "Oxford PPE Interview preparation",
            "Cambridge HSPS interview questions with model answers",
        ),
        "cambridge-veterinary-medicine-interview": (
            "Cambridge", "No written test required",
            "/blog/cambridge-veterinary-medicine-interview-questions-2026-with-model-answers",
            "Cambridge Veterinary Medicine interview questions with scientific reasoning and animal welfare ethics model answers",
            "/oxbridge-interviews/oxford-veterinary-medicine-interview/",
            "Oxford Veterinary Medicine Interview preparation",
            "Cambridge Veterinary Medicine interview questions with model answers",
        ),
        "cambridge-medicine-interview": (
            "Cambridge", "No written test (UCAT required for shortlisting)",
            "/blog/cambridge-medicine-interview-questions-2026-science-questions-and-how-to-answer-them",
            "Cambridge Medicine interview questions with science problem-solving and reasoning model answers",
            "/oxbridge-interviews/oxford-medicine-interview/",
            "Oxford Medicine Interview preparation",
            "Cambridge Medicine interview questions with model answers",
        ),
    }

    # Detect university-specific slugs
    uni_data = OXFORD_SPECIFIC.get(slug) or CAMBRIDGE_SPECIFIC.get(slug)
    if uni_data:
        university, admissions_test, blog_url, blog_anchor, cross_url, cross_title, resources_anchor = uni_data

        if variant == 0:
            structure = f"""
Use exactly these <h2> sections in this order:
  1. What to Expect in a {subjects} {university} Interview
  2. The Admissions Test: {admissions_test}
  3. How to Prepare for Your {university} {subjects} Interview
  4. Example {university} {subjects} Interview Questions
  5. Common Mistakes and How to Avoid Them
  6. Frequently Asked Questions about {university} {subjects} Interviews

Opening paragraph angle: Immediately explain what makes {subjects} {university} interviews distinctive — the college-based format, what tutors are actually assessing, and why standard revision alone will not prepare you.

FAQ focus: How long {university} {subjects} interviews last, whether prior knowledge is tested, how to practise effectively for {university}'s specific format, and what to do if you do not know the answer to a question."""
        else:
            structure = f"""
Use exactly these <h2> sections in this order:
  1. What {university} {subjects} Interviewers Are Really Looking For
  2. Example {university} {subjects} Interview Questions — and How to Approach Them
  3. The Admissions Test: {admissions_test}
  4. Building Your {university} {subjects} Preparation — A Practical Plan
  5. The Mistakes That Cost Candidates {university} Offers
  6. Frequently Asked Questions

Opening paragraph angle: Open with a specific example of the kind of thinking {university} {subjects} interviews demand — something that surprises candidates who expected a more traditional format.

FAQ focus: How many interviews {university} {subjects} candidates typically have, what super-curricular preparation matters most for {university}, whether mock interviews are worth doing, and how {university} {subjects} interviews compare to other universities."""

        return f"""
You are writing a university-specific interview preparation service page for Leading Tuition, a UK tutoring company.

University: {university}
Subject(s): {subjects}
Admissions test: {admissions_test}

Audience:
- A Year 12 or Year 13 student (or their parent) preparing specifically for {university} interviews in {subjects}
- They want {university}-specific, actionable guidance — not generic Oxbridge tips
- They are anxious but ambitious, and want to know exactly what {university} expects

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
1. What makes the {university} {subjects} interview specifically distinctive — including college variation, format, and what tutors reward?
2. What are the most common mistakes candidates make in {university} {subjects} interviews?
3. What does a top-1% {university} {subjects} interview performance actually look like?

Now write a detailed {university} {subjects} interview preparation service page in HTML: {title}

Content requirements:
- Length: 1,100 to 1,350 words
- At least 5 genuine, intellectually challenging example {university} {subjects} interview questions in a <ul>
- Specific advice on thinking aloud and engaging with questions even when uncertain
- {university}-specific detail: college interviews, format, typical number of interviews
- Admissions test context: how {admissions_test} relates to interview preparation
- A brief note on super-curricular preparation relevant to {university} {subjects}
- Include one short bullet list
- Internal links (must appear as natural anchor text within a sentence):
    * Link to the blog post at {blog_url} using anchor text '{blog_anchor}'
    * Link to the resources page at /resources/oxbridge-interview-questions using anchor text '{resources_anchor}'
    * Link to {cross_url} using anchor text '{cross_title}' as a brief note that candidates sometimes also consider the other university

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- Do not pad — every sentence must earn its place
- Focus entirely on {university} — do not write a generic Oxbridge page
"""

    # ── Generic Oxbridge prompt (existing subjects) ───────────────────────────
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
            "areaServed": {"@type": "Country", "name": "United Kingdom"}
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
    # ── New independent school pages ─────────────────────────────────────────
    "latymer-upper":           "Expert Latymer Upper School 11+ preparation with Leading Tuition. Specialist coaching for the Latymer entrance exam. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "st-pauls-girls":          "Expert St Paul's Girls' School 11+ preparation with Leading Tuition. Specialist coaching for the two-stage SPGS entrance exam. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "highgate-school":         "Expert Highgate School 11+ preparation with Leading Tuition. Specialist coaching for the Highgate entrance exam. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "city-of-london-school-girls": "Expert City of London School for Girls 11+ preparation with Leading Tuition. Specialist CLSG entrance exam coaching. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "james-allens":            "Expert James Allen's Girls' School 11+ preparation with Leading Tuition. Specialist JAGS entrance exam coaching. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "alleyn":                  "Expert Alleyn's School 11+ preparation with Leading Tuition. Specialist entrance exam coaching for one of South London's top independents. 4.8/5 Trustpilot.",
    "dulwich-college":         "Expert Dulwich College 11+ preparation with Leading Tuition. Specialist entrance exam coaching for Maths and English papers. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "kings-wimbledon":         "Expert King's College School Wimbledon 11+ preparation with Leading Tuition. Specialist KCS entrance exam coaching. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "habs-girls":              "Expert Haberdashers' Girls' School 11+ preparation with Leading Tuition. Specialist ISEB pre-test and Habs entrance exam coaching. 4.8/5 Trustpilot.",
    "streatham-clapham":       "Expert Streatham and Clapham High School 11+ preparation with Leading Tuition. Specialist SCHS entrance exam coaching. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    "dame-alice-owens":        "Expert Dame Alice Owen's School 11+ preparation with Leading Tuition. Specialist ISEB Common Pre-Test coaching for one of Hertfordshire's top selective schools. 4.8/5 Trustpilot.",
    "manchester-grammar-school": "Expert Manchester Grammar School 11+ preparation with Leading Tuition. Specialist MGS entrance exam coaching for Maths and English. 4.8/5 Trustpilot.",
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



# ── 11+ Borough Guide pages ───────────────────────────────────────────────────

BOROUGH_GUIDES = [
    {
        "slug": "barnet",
        "name": "Barnet",
        "schools": "Queen Elizabeth's Boys' School (QE Barnet) and Henrietta Barnett School",
        "exam": "Queen Elizabeth's uses its own highly competitive entrance exam; Henrietta Barnett uses the GSHSA consortium test",
        "selectivity": "QE Boys is ranked #1 grammar school in England by A-level results; Henrietta Barnett is the UK's most selective state school for girls",
        "keyword": "11+ tuition Barnet",
        "meta_desc": "Specialist 11+ tuition in Barnet for QE Boys and Henrietta Barnett School. Expert entrance exam coaching from Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "harrow",
        "name": "Harrow",
        "schools": "John Lyon School and other selective independents using ISEB pre-tests",
        "exam": "ISEB Common Pre-Test and school-specific papers",
        "selectivity": "John Lyon and local selective independents draw from a strong applicant pool across north-west London",
        "keyword": "11+ tuition Harrow",
        "meta_desc": "Specialist 11+ and entrance exam tuition in Harrow. Expert coaching for John Lyon, ISEB pre-tests and selective school entry. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "bromley",
        "name": "Bromley",
        "schools": "St Olave's Grammar School, Newstead Wood School, and Beths Grammar School",
        "exam": "GL Assessment reasoning (Bromley consortium) plus St Olave's own second-stage paper",
        "selectivity": "St Olave's is one of the most oversubscribed grammars in England; Newstead Wood and Beths are also highly competitive",
        "keyword": "11+ tuition Bromley",
        "meta_desc": "Specialist 11+ grammar school tuition in Bromley. Expert entrance exam coaching for St Olave's, Newstead Wood and Beths Grammar. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "croydon",
        "name": "Croydon",
        "schools": "Whitgift School, Trinity School, Old Palace of John Whitgift School, and the Sutton SET grammar schools",
        "exam": "ISEB pre-test and school-specific papers for Whitgift/Trinity/Old Palace; GL Assessment Sutton SET for consortium grammars",
        "selectivity": "Whitgift, Trinity and Old Palace are among the top independent schools in London; Sutton SET grammars are highly oversubscribed",
        "keyword": "11+ tuition Croydon",
        "meta_desc": "Specialist 11+ and entrance exam tuition in Croydon. Expert coaching for Whitgift, Trinity, Old Palace and Sutton SET grammar schools. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "ealing",
        "name": "Ealing",
        "schools": "Notting Hill and Ealing High School, St Benedict's School, and selective schools using ISEB pre-tests",
        "exam": "ISEB Common Pre-Test and school-specific entrance exams",
        "selectivity": "Selective independents in Ealing are competitive; many families also target grammar schools in neighbouring boroughs",
        "keyword": "11+ tuition Ealing",
        "meta_desc": "Specialist 11+ and entrance exam tuition in Ealing. Expert coaching for selective schools and ISEB pre-tests. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "slough",
        "name": "Slough",
        "schools": "Upton Court Grammar, Herschel Grammar, Langley Grammar, Slough Grammar, and Khalsa Grammar — the 5-school Slough SET consortium",
        "exam": "Slough SET (Selective Eligibility Test) — a GL Assessment-style exam sat by all 5 consortium schools",
        "selectivity": "All 5 Slough consortium schools are oversubscribed; the SET is sat by thousands of candidates each year",
        "keyword": "11+ tuition Slough",
        "meta_desc": "Specialist 11+ grammar school tuition in Slough for the Slough SET. Expert entrance exam coaching for all 5 consortium schools. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "kingston",
        "name": "Kingston",
        "schools": "Tiffin School (boys) and Tiffin Girls' School",
        "exam": "Kingston Grammar Test (KGT) — a bespoke exam sitting thousands of candidates for fewer than 200 places across both schools",
        "selectivity": "Tiffin School and Tiffin Girls' are among the most competitive state grammar schools in England — typically 2,000+ applicants for ~180 places each",
        "keyword": "11+ tuition Kingston",
        "meta_desc": "Specialist 11+ entrance exam tuition in Kingston for Tiffin School and Tiffin Girls'. Expert Kingston Grammar Test coaching from Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "sutton",
        "name": "Sutton",
        "schools": "Wilson's School, Sutton Grammar School, Wallington County Grammar, Nonsuch High School, and Greenshaw High School — the Sutton SET consortium",
        "exam": "Sutton Selective Eligibility Test (SET) — a GL Assessment exam used by all consortium schools",
        "selectivity": "Wilson's, Nonsuch, and Wallington are among the most oversubscribed grammar schools in England; all 5 schools see very high applicant numbers",
        "keyword": "11+ tuition Sutton",
        "meta_desc": "Specialist 11+ grammar school tuition in Sutton for the Sutton SET. Expert entrance exam coaching for Wilson's, Nonsuch, Wallington and all consortium schools. 4.8/5 Trustpilot.",
    },
    # ── New borough/area guides ───────────────────────────────────────────────
    {
        "slug": "enfield",
        "name": "Enfield",
        "schools": "Latymer School Edmonton, Enfield Grammar School, and Edmonton County School",
        "exam": "Latymer School uses its own highly competitive entrance exam; Enfield Grammar and Edmonton County use the GL Assessment North London consortium test",
        "selectivity": "Latymer School Edmonton is among the most competitive state schools in England with over 2,000 applicants for around 180 places; Enfield Grammar and Edmonton County are selective and heavily oversubscribed",
        "keyword": "11+ tuition Enfield",
        "meta_desc": "Specialist 11+ grammar school tuition in Enfield. Expert coaching for Latymer School Edmonton, Enfield Grammar and Edmonton County School. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "hertfordshire",
        "name": "Hertfordshire",
        "schools": "Dame Alice Owen's School, Watford Grammar School for Boys, Watford Grammar School for Girls, and St Albans School",
        "exam": "Dame Alice Owen's uses the ISEB Common Pre-Test for pre-registration; Watford Grammar schools use the Hertfordshire Consortium test (GL Assessment style); St Albans is an independent using its own exam",
        "selectivity": "Dame Alice Owen's is one of the most oversubscribed selective schools in Hertfordshire; Watford Grammar schools are highly competitive; the county attracts applicants from North London as well as local families",
        "keyword": "11+ tuition Hertfordshire",
        "meta_desc": "Specialist 11+ tuition in Hertfordshire. Expert coaching for Dame Alice Owen's, Watford Grammar and selective school entrance exams. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "kent",
        "name": "Kent",
        "schools": "Skinners' School, Judd School, Maidstone Grammar School, Tonbridge Grammar School, Weald of Kent Grammar School, and Simon Langton Grammar Schools",
        "exam": "The Kent Test — a GL Assessment paper in Maths, English and reasoning, sat in September of Year 6; out-of-county applicants face particularly strong competition",
        "selectivity": "Kent grammar schools are highly competitive; out-of-county applications have grown significantly with London families increasingly targeting Kent grammars; Judd and Skinners' are among the most oversubscribed boys' grammars in England",
        "keyword": "11+ tuition Kent",
        "meta_desc": "Specialist 11+ Kent Test tuition. Expert coaching for Judd School, Skinners', Tonbridge Grammar, Weald of Kent and all Kent grammar schools. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "north-london",
        "name": "North London",
        "schools": "Latymer Upper School, Highgate School, City of London School for Girls, North London Collegiate School, South Hampstead High School, and Channing School",
        "exam": "Each school uses its own entrance exam; NLCS, South Hampstead High and Channing share a sitting date in October/November; Latymer Upper and Highgate have their own papers; ISEB Common Pre-Test is used by Haberdashers' and some other North London independents for pre-registration",
        "selectivity": "North London independent schools are among the most competitive in the country; NLCS receives approximately 1,000 applicants for 120 places; South Hampstead High approximately 800 for 90 places; most require preparation from Year 4 or 5 to be competitive",
        "keyword": "11+ tuition North London",
        "meta_desc": "Specialist 11+ tuition in North London. Expert coaching for Latymer Upper, Highgate, NLCS, South Hampstead High, CLSG and North London independent school entrance exams. 4.8/5 Trustpilot.",
    },
]


def borough_guide_prompt(slug: str, name: str, schools: str, exam: str,
                          selectivity: str, keyword: str) -> str:
    import hashlib
    variant = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 2

    if variant == 0:
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Grammar Schools and Selective Entry in {name}
  2. The Entrance Exams — What Your Child Will Face
  3. How Competitive Is Entry? Places, Applicants, and Pass Marks
  4. How to Prepare — Timeline and Strategy for {name} Families
  5. How Leading Tuition Supports {name} 11+ Preparation
  6. Frequently Asked Questions about 11+ in {name}

Opening paragraph angle: Start from the parent's perspective — what it actually means to pursue selective school entry in {name}, which schools are worth targeting, and why specialist preparation matters here specifically."""
    else:
        structure = f"""
Use exactly these <h2> sections in this order:
  1. Preparing for the 11+ in {name} — Where to Start
  2. Which Schools and Which Exams?
  3. What the Exams Test — and Where Children Come Unstuck
  4. A Realistic Preparation Timeline for {name} Families
  5. Working With Leading Tuition in {name}
  6. Frequently Asked Questions

Opening paragraph angle: Open by explaining why {name} is a distinct 11+ market — the schools available, the exam format(s) used, and what sets preparation for these schools apart from generic 11+ coaching."""

    return f"""
You are writing an 11+ borough guide page for Leading Tuition, a UK tutoring company.

Borough: {name}
Grammar and selective schools: {schools}
Entrance exam(s): {exam}
Selectivity context: {selectivity}

Audience:
- A UK parent in or near {name} who is beginning to research grammar school entry
- They want borough-specific, accurate information — not a generic 11+ article
- They are anxious, researching early, and want to know exactly which schools are worth targeting, what exams are used, and how to prepare

Global rules:
- Write for a UK parent, not an SEO algorithm
- Use a warm, expert, reassuring tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions
- Never use generic filler phrases like "look no further" or "we've got you covered"
- Never refer to the 11+ as "easy" or imply any child can pass without serious preparation
- Be specific to {name} — name the schools, name the exams, give real numbers where available

Before writing, think through:
1. What makes the 11+ landscape in {name} distinctive — which schools, which exams, and why families should care?
2. What does the exam (or exams) actually test, and what do most children get wrong in preparation?
3. What does a realistic preparation timeline look like for families in this borough?

Now write a detailed 11+ borough guide in HTML for: 11+ Tuition in {name}

Content requirements:
- Length: 1,000 to 1,200 words
- Name {name} and the specific schools in the opening paragraph
- Explain the exam format(s): subjects tested, timing, question style
- Include selectivity context: {selectivity}
- Include at least one concrete preparation tip specific to the exam(s) used here
- Include one short <ul> bullet list (not in the FAQ section)
- Mention that Leading Tuition provides 1-to-1 specialist tutoring for these exams

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- After all HTML content, on a new line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]
- Do not pad — every sentence must earn its place
"""


def generate_borough_guide_pages(new_only=False):
    import json as _json

    # ── Hub page (no API) ─────────────────────────────────────────────────────
    borough_links = "\n".join(
        f'  <a href="/11-plus/{b["slug"]}/" class="index-card">'
        f'<strong>11+ in {b["name"]}</strong>'
        f'<span>{b["schools"].split(",")[0].strip()}'
        f'{" and more" if "," in b["schools"] else ""}</span></a>'
        for b in BOROUGH_GUIDES
    )
    hub_content = f"""<p>Leading Tuition provides specialist 11+ preparation across London and the South East.
Each borough has its own grammar schools, its own entrance exam formats, and its own level of competition.
Select your borough below for a detailed guide to the schools, the exams, and how to prepare.</p>
<p>Our tutors are specialists in specific exams — whether that is the Kingston Grammar Test for Tiffin, the Sutton SET,
the Slough consortium, or the GL Assessment reasoning papers used in Bromley and beyond.</p>
<div class="subject-grid">
{borough_links}
</div>"""

    hub_crumb = breadcrumb_schema("eleven-plus-boroughs-hub", "11-plus/boroughs", "11+ Borough Guides")
    hub_html = page_template(
        "11+ Borough Guides — Grammar School Tuition by Area | Leading Tuition",
        hub_content,
        meta_desc="Specialist 11+ tuition across London and the South East. Borough-by-borough guides to grammar schools, entrance exams and preparation. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
        slug="11-plus/boroughs/",
        page_type="eleven-plus-boroughs-hub",
        section="11+ Borough Guides",
        schema_extra=hub_crumb,
    )
    hub_dir = OUTPUT_DIR / "11-plus" / "boroughs"
    hub_dir.mkdir(parents=True, exist_ok=True)
    (hub_dir / "index.html").write_text(hub_html, encoding="utf-8")
    print("Generated hub page: 11-plus/boroughs/index.html")

    # ── Individual borough pages (API) ────────────────────────────────────────
    for b in BOROUGH_GUIDES:
        slug = b["slug"]
        name = b["name"]
        out_dir = OUTPUT_DIR / "11-plus" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): 11-plus/{slug}/")
            continue

        prompt = borough_guide_prompt(
            slug=slug, name=name,
            schools=b["schools"], exam=b["exam"],
            selectivity=b["selectivity"], keyword=b["keyword"]
        )
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f"11+ Tuition in {name}",
            "url": f"https://www.leadingtuition.co.uk/11-plus/{slug}/",
            "description": b["meta_desc"],
            "provider": {
                "@type": "EducationalOrganization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
            "areaServed": {"@type": "City", "name": name},
        }
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        breadcrumb = breadcrumb_schema("eleven-plus-borough", slug, f"11+ Tuition in {name}")
        schema_extra = faq_schema + "\n" + service_schema + "\n" + breadcrumb

        html = page_template(
            f"11+ Tuition in {name} | Leading Tuition",
            content,
            meta_desc=b["meta_desc"],
            slug=f"11-plus/{slug}/",
            page_type="eleven-plus-borough",
            section="11+ Borough Guides",
            schema_extra=schema_extra
        )

        file_path.write_text(html, encoding="utf-8")
        print(f"Generated borough guide: 11-plus/{slug}/")


IB_SUBJECT_PAGES = [
    {
        "slug": "maths",
        "name": "IB Maths",
        "courses": "Analysis & Approaches (AA) and Applications & Interpretation (AI) at both Higher Level and Standard Level",
        "hl_sl": "The gap between SL and HL in IB Maths is substantial — HL includes complex numbers, further calculus, vectors, and proof by induction that SL does not cover. AA HL is widely regarded as the most demanding pre-university maths qualification available in the UK, harder in many respects than A-Level Further Maths.",
        "struggles": "Paper 3 in AA HL (extended problem-solving under time pressure), the internal assessment (a 12-page mathematical exploration marked externally), managing time across three exam papers, and adapting to the IB's emphasis on conceptual understanding over procedural recall.",
        "meta_desc": "Specialist IB Maths tuition for Analysis & Approaches and Applications & Interpretation at HL and SL. Expert IB mathematics tutors from Oxford & Cambridge. 4.8/5 Trustpilot.",
    },
    {
        "slug": "chemistry",
        "name": "IB Chemistry",
        "courses": "IB Chemistry at Higher Level and Standard Level under the 2023 curriculum with restructured themes and Nature of Science emphasis",
        "hl_sl": "HL Chemistry adds significant depth in organic chemistry, energetics, and the HL-only extension material. The internal assessment — a scientific investigation accounting for 20% of the final grade — requires students to design, execute, and analyse an original experiment to a standard that rewards genuine scientific thinking.",
        "struggles": "The breadth of the HL syllabus alongside the quantitative demands of Papers 1 and 2, producing an IA that demonstrates real investigative rigour, and adapting to the 2023 curriculum's reorganisation away from traditional topic headings.",
        "meta_desc": "Specialist IB Chemistry tuition at Higher Level and Standard Level. Expert IB chemistry tutors from Oxford & Cambridge. Full 2023 curriculum and internal assessment support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "physics",
        "name": "IB Physics",
        "courses": "IB Physics at Higher Level and Standard Level, including the experimental investigation component and the 2023 curriculum restructure",
        "hl_sl": "HL Physics extends into wave phenomena, fields, and electromagnetic induction at a level demanding strong mathematical fluency alongside physical intuition. Paper 3 at HL requires confident application to unfamiliar experimental contexts — a skill that requires sustained practice to develop.",
        "struggles": "Applying physical principles to novel experimental scenarios, the mathematical rigour of HL particularly in fields and circular motion, and designing an IA investigation with a testable, well-controlled methodology.",
        "meta_desc": "Specialist IB Physics tuition at Higher Level and Standard Level. Expert IB physics tutors from Oxford & Cambridge. Full syllabus and internal assessment support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "biology",
        "name": "IB Biology",
        "courses": "IB Biology at Higher Level and Standard Level under the 2023 curriculum, which reorganises content around interconnected themes rather than traditional topic divisions",
        "hl_sl": "HL Biology requires deeper treatment of cell biology, genetics, ecology, and human physiology. The 2023 restructure places greater emphasis on conceptual understanding and application to novel contexts — it rewards students who understand mechanisms rather than memorise facts, and penalises rote learning under unfamiliar question framing.",
        "struggles": "The volume of HL content, navigating the new 2023 theme-based structure, and producing an IA that meets scientific rigour criteria (clear research question, controlled variables, sufficient data, honest evaluation) within the word count.",
        "meta_desc": "Specialist IB Biology tuition at Higher Level and Standard Level. Expert IB biology tutors from Oxford & Cambridge. 2023 curriculum and internal assessment support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "english",
        "name": "IB English",
        "courses": "IB English A: Language & Literature and English A: Literature at Higher Level and Standard Level",
        "hl_sl": "HL English A requires study of additional works and includes the HL essay — an independently written 1,200-1,500 word analytical essay on a literary text of the student's choosing, assessed externally. This demands a high degree of analytical independence and is one of the most challenging components in the IB for students who have not been trained in close literary analysis.",
        "struggles": "The Individual Oral (IO) which requires students to compare a literary text with a non-literary body of work under timed conditions without notes, the Paper 1 unseen text analysis, and for HL students the additional preparation required for the HL essay.",
        "meta_desc": "Specialist IB English tuition for Language & Literature and Literature A at HL and SL. Expert IB English tutors from Oxford & Cambridge. IO, essay, and Paper 1 support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "economics",
        "name": "IB Economics",
        "courses": "IB Economics at Higher Level and Standard Level covering microeconomics, macroeconomics, international economics, and development economics",
        "hl_sl": "HL Economics adds quantitative analysis requirements and a more rigorous treatment of macroeconomic models. Paper 3 at HL is a data-based paper requiring students to apply economic theory and quantitative skills to unfamiliar scenarios — including calculations involving multipliers, price elasticity, and balance of payments — a skill that rewards methodical practice over time.",
        "struggles": "Drawing and applying diagrams accurately and precisely under exam conditions, the commentary internal assessment (three commentaries on real economic events with strict word limits), and the HL Paper 3 quantitative demands.",
        "meta_desc": "Specialist IB Economics tuition at Higher Level and Standard Level. Expert IB economics tutors from Oxford & Cambridge. Paper 3, commentaries, and full syllabus support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "history",
        "name": "IB History",
        "courses": "IB History at Higher Level and Standard Level, covering prescribed subjects, world history topics, and the HL regional option",
        "hl_sl": "HL History requires study of an additional historical period through the HL extension — a depth study covering a 50-year period in substantial detail. Paper 3 at HL tests this through extended essays under timed conditions, demanding both breadth of knowledge and the ability to construct a sustained analytical argument.",
        "struggles": "Writing essays that argue rather than describe — the most common reason students underperform in IB History — balancing coverage across multiple topics, and producing an internal assessment (historical investigation using primary sources) that demonstrates genuine source evaluation rather than paraphrase.",
        "meta_desc": "Specialist IB History tuition at Higher Level and Standard Level. Expert IB history tutors from Oxford & Cambridge. Essay technique, Paper 3, and historical investigation support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "psychology",
        "name": "IB Psychology",
        "courses": "IB Psychology at Higher Level and Standard Level covering biological, cognitive, and sociocultural approaches plus two option topics",
        "hl_sl": "HL Psychology adds Paper 3, which focuses on qualitative research methodology — an area few students have encountered formally and one that requires a different mode of critical thinking from the quantitative approach tested in Papers 1 and 2.",
        "struggles": "Applying research studies accurately and selectively in exam answers (relevant detail, not exhaustive recall), the precise use of command terms (describe, explain, evaluate, discuss), and producing an internal assessment experimental study that meets research ethics and methodology standards.",
        "meta_desc": "Specialist IB Psychology tuition at Higher Level and Standard Level. Expert IB psychology tutors from Oxford & Cambridge. Full syllabus, Paper 3, and IA support. 4.8/5 Trustpilot.",
    },
]

IB_COMPONENT_PAGES = [
    {
        "slug": "extended-essay",
        "name": "Extended Essay",
        "display": "IB Extended Essay Tutor",
        "description": "The Extended Essay is a 4,000-word independent research essay on a topic of the student's choosing within a chosen IB subject. It is assessed externally by IB examiners and contributes to the Diploma alongside Theory of Knowledge through the combined bonus points matrix. Students are allocated a supervisor from their school but the research and writing are independent.",
        "challenges": "Developing a focused, genuinely researchable question (the most common failure point — questions that are too broad produce descriptive essays that score poorly); structuring an argument that goes beyond narration; engaging critically with sources; meeting formal requirements (abstract, bibliography, citations); and managing the extended research and writing process over several months while maintaining progress in other IB subjects.",
        "tutor_role": "A tutor helps a student develop and refine their research question, plan the argument structure, identify and evaluate relevant sources, and improve the analytical quality and expression of their writing throughout drafts. The work produced must be entirely the student's own — tutors support understanding, process, and skills development.",
        "meta_desc": "Specialist IB Extended Essay tutoring. Expert support for research questions, argument structure, and essay quality from Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "tok",
        "name": "Theory of Knowledge",
        "display": "IB TOK Tutor",
        "description": "Theory of Knowledge is a compulsory component of the IB Diploma that asks students to reflect on the nature, scope, and limits of knowledge across different disciplines. Assessment is through a 1,600-word essay responding to one of six prescribed titles released annually by the IB, and a TOK exhibition in which the student connects three objects or artefacts to a core theme.",
        "challenges": "Understanding what TOK actually requires — it is not a general opinion essay or a summary of knowledge claims, but a disciplined philosophical inquiry with specific criteria; choosing a line of argument that genuinely engages with the prescribed title rather than restating it; using real-life situations appropriately (not superficially); and structuring a coherent essay that earns marks on all five assessment criteria.",
        "tutor_role": "A tutor helps a student understand the TOK framework and assessment criteria, interpret the prescribed title accurately, develop a coherent thesis, plan an essay structure that addresses the criteria, and refine the writing through drafts. Many students find TOK conceptually unfamiliar — an experienced tutor makes the abstract requirements concrete and actionable.",
        "meta_desc": "Specialist IB Theory of Knowledge (TOK) tutoring. Expert support for TOK essays and exhibitions from Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "internal-assessment",
        "name": "Internal Assessment",
        "display": "IB Internal Assessment Tutor",
        "description": "The Internal Assessment is a school-assessed component that accounts for 20-30% of a student's final IB grade depending on the subject. Each subject has a different IA format: scientific investigation (sciences), mathematical exploration (maths), historical investigation (history), written commentary (economics), Individual Oral (English), or experimental study (psychology). All IAs are moderated externally by IB examiners.",
        "challenges": "Understanding the subject-specific assessment criteria — which differ substantially between subjects — and producing work that targets those criteria rather than general essay or report standards; choosing a topic that is genuinely investigable within the constraints of the format; meeting the word or page count limits; and maintaining academic integrity while producing work that reflects genuine individual understanding.",
        "tutor_role": "A tutor helps a student understand the assessment criteria for their specific subject, plan an appropriate topic and methodology, structure the work correctly, and improve the quality of their analysis and presentation through the drafting process. The IA must be the student's own work — tuition develops understanding and process, not content on the student's behalf.",
        "meta_desc": "Specialist IB Internal Assessment tutoring across all subjects. Expert IA planning, criteria support, and analysis coaching from Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
]


def ib_subject_prompt(page: dict) -> str:
    import hashlib
    variant = int(hashlib.md5(page["slug"].encode()).hexdigest(), 16) % 3

    if variant == 0:
        structure = f"""Use exactly these <h2> sections in this order:
  1. What Makes IB {page["name"]} Different
  2. Higher Level vs Standard Level — What the Gap Actually Means
  3. The Internal Assessment
  4. Where Students Most Often Lose Marks
  5. What to Expect From Tuition
  6. Frequently Asked Questions

Opening angle: Start by explaining what specifically distinguishes IB {page["name"]} from the equivalent A-Level or GCSE — in terms of content, assessment style, and the demands placed on students."""

    elif variant == 1:
        structure = f"""Use exactly these <h2> sections in this order:
  1. The IB {page["name"]} Exam — Structure and What It Tests
  2. HL and SL: A Meaningful Difference, Not Just More Content
  3. Where Marks Are Lost — and Why Good Students Still Underperform
  4. The Internal Assessment in {page["name"]}
  5. How a Specialist Tutor Supports {page["name"]} Preparation
  6. Frequently Asked Questions

Opening angle: Start from the exam structure — what papers exist, what each tests, and why the IB approach to {page["name"]} catches students off guard even when they have strong prior knowledge."""

    else:
        structure = f"""Use exactly these <h2> sections in this order:
  1. Why IB {page["name"]} Is Harder Than Students Expect
  2. The Internal Assessment — What Examiners Are Looking For
  3. HL vs SL — Choosing the Right Level and Preparing for It
  4. Exam Technique: Where the Marks Actually Come From
  5. Working With a Specialist IB {page["name"]} Tutor
  6. Frequently Asked Questions

Opening angle: Start from a student perspective — what IB {page["name"]} looks like in Year 12 when students first encounter it, what surprises them, and why preparation that worked at GCSE often does not transfer."""

    return f"""You are writing an IB tuition landing page for Leading Tuition, a UK tutoring company staffed by Oxford and Cambridge graduates.

Subject: {page["name"]}
Courses covered: {page["courses"]}
HL vs SL distinction: {page["hl_sl"]}
Where students most commonly struggle: {page["struggles"]}

Audience:
- A UK parent or IB student researching tuition for this specific IB subject
- They are looking for evidence of genuine subject expertise — not generic tutoring marketing
- They want to understand what makes IB {page["name"]} specifically demanding, and how tuition addresses those specific demands

{structure}

Global rules:
- Write for a UK parent or IB student, not an SEO algorithm
- Use a precise, expert tone — demonstrate subject knowledge, not marketing fluency
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer — the template handles those
- Never use generic filler phrases like "look no further", "we've got you covered", or "unlock your potential"
- Be specific — name real IB exam components, real assessment criteria, real syllabus content
- Do not pad — every sentence must earn its place

Content requirements:
- Length: 900 to 1,100 words
- Include one concrete, subject-specific piece of preparation advice that demonstrates genuine expertise
- Include at least one <ul> bullet list (not in the FAQ)
- The FAQ section should have exactly 4 questions written as <p><strong>Question?</strong></p> followed by <p>answer</p>

After all HTML content, on a new line, output exactly 4 FAQ pairs in this format:
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]
"""


def ib_component_prompt(page: dict) -> str:
    import hashlib
    variant = int(hashlib.md5(page["slug"].encode()).hexdigest(), 16) % 2

    if variant == 0:
        structure = f"""Use exactly these <h2> sections in this order:
  1. What the {page["name"]} Requires
  2. Where Students Most Often Go Wrong
  3. How the Assessment Is Marked
  4. How Tuition Helps — and What It Cannot Do
  5. Frequently Asked Questions

Opening angle: Start by explaining precisely what the {page["name"]} is — its word count or length, how it is assessed, and what weight it carries in the final IB grade — before addressing what makes it difficult."""

    else:
        structure = f"""Use exactly these <h2> sections in this order:
  1. Understanding the {page["name"]} — What the IB Actually Expects
  2. The Assessment Criteria Explained
  3. The Most Common Mistakes — and Why They Happen
  4. The Role of a Tutor: Support Without Crossing Lines
  5. Frequently Asked Questions

Opening angle: Start from the student's experience — what the {page["name"]} looks like when first encountered, why its requirements are frequently misunderstood, and what distinguishes work that scores well from work that does not."""

    return f"""You are writing an IB tuition landing page for Leading Tuition, a UK tutoring company staffed by Oxford and Cambridge graduates.

Component: {page["display"]}
What it is: {page["description"]}
Key challenges for students: {page["challenges"]}
What a tutor does: {page["tutor_role"]}

Audience:
- A UK parent or IB student looking for specialist support with this specific IB component
- They are anxious and under time pressure — the component deadline is real
- They want to understand what excellent work looks like, and how tuition helps them get there

{structure}

Global rules:
- Write for a UK parent or IB student, not an SEO algorithm
- Use a precise, expert tone — demonstrate knowledge of the IB assessment system
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer — the template handles those
- Never use generic filler phrases like "look no further" or "unlock your potential"
- Be specific about IB assessment criteria, word counts, mark allocations, and process
- Be honest about academic integrity — tutors support process and understanding, not write work for students
- Do not pad — every sentence must earn its place

Content requirements:
- Length: 800 to 1,000 words
- Include at least one <ul> bullet list
- The FAQ section should have exactly 4 questions written as <p><strong>Question?</strong></p> followed by <p>answer</p>

After all HTML content, on a new line, output exactly 4 FAQ pairs in this format:
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]
"""


# ── 13+ Preparation pages ─────────────────────────────────────────────────────

THIRTEEN_PLUS_PAGES = [
    {
        "slug": "common-entrance-exam",
        "display_title": "Common Entrance 13+",
        "school_name": "Common Entrance",
        "type": "exam_guide",
        "key_facts": "Set by ISEB and sat in May/June of Year 8; subjects include English, Maths, Science, French, History, Geography and Religious Studies; 60% is typically a pass, 65% is solid, 70%+ is distinction; most boarding schools issue conditional places based on CE performance after a pre-test in Year 6",
        "schools_list": "Used by most independent boarding and senior schools including Eton, Harrow, Marlborough, Rugby, Sherborne, Radley, Oundle and many others",
        "keyword": "Common Entrance 13 plus preparation",
        "meta_desc": "Expert Common Entrance 13+ preparation with Leading Tuition. Subject-by-subject CE coaching in Maths, English, Science, French and more. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "iseb-pre-test",
        "display_title": "ISEB Common Pre-Test (13+)",
        "school_name": "ISEB Common Pre-Test",
        "type": "exam_guide",
        "key_facts": "Taken in Year 6 (age 10-11) by children registering for boarding school entry at 13+; adaptive online test in Maths, English, Verbal Reasoning and Non-Verbal Reasoning; scores reported on a scale of 60-140 with a median of 100; schools receive results directly and use them to shortlist for interviews and conditional offers",
        "schools_list": "Used by Eton College, Harrow School, Winchester College, Radley College, Marlborough College, Rugby School, Charterhouse, Oundle School and many others",
        "keyword": "ISEB pre-test 13 plus preparation",
        "meta_desc": "Expert ISEB Common Pre-Test preparation for 13+ boarding school entry. Specialist coaching for this adaptive online test in Maths, English, VR and NVR. 4.8/5 Trustpilot.",
    },
    {
        "slug": "eton-college",
        "display_title": "Eton College 13+",
        "school_name": "Eton College",
        "type": "school",
        "key_facts": "Boys only; ISEB Common Pre-Test taken in Year 6 for all candidates; King's Scholarship examination (separate) for the most academic 70 scholars; conditional Common Entrance places confirmed by CE results in Year 8; approximately 250 places per year from a very large applicant pool",
        "schools_list": "Eton College, Windsor",
        "keyword": "Eton College 13 plus preparation",
        "meta_desc": "Expert Eton College 13+ preparation with Leading Tuition. Specialist ISEB pre-test coaching and Common Entrance support. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "harrow-school",
        "display_title": "Harrow School 13+",
        "school_name": "Harrow School",
        "type": "school",
        "key_facts": "Boys only; ISEB Common Pre-Test in Year 6 for initial registration; interviews at Harrow for shortlisted candidates; conditional Common Entrance offers; approximately 170 places per year; reputation for arts, leadership and co-curricular breadth alongside strong academics",
        "schools_list": "Harrow School, Harrow on the Hill",
        "keyword": "Harrow School 13 plus preparation",
        "meta_desc": "Expert Harrow School 13+ preparation with Leading Tuition. Specialist ISEB pre-test coaching, interview preparation and Common Entrance support. 4.8/5 Trustpilot.",
    },
    {
        "slug": "winchester-college",
        "display_title": "Winchester College 13+",
        "school_name": "Winchester College",
        "type": "school",
        "key_facts": "Boys only; does NOT use Common Entrance — Winchester sets its own entirely separate entrance examination (Win Coll papers) in a range of subjects; candidates also sit the ISEB pre-test for registration; approximately 130 places; the scholarship (Election) is one of the most prestigious academic awards in independent education",
        "schools_list": "Winchester College, Winchester",
        "keyword": "Winchester College 13 plus preparation",
        "meta_desc": "Expert Winchester College 13+ preparation with Leading Tuition. Specialist coaching for the Winchester College entrance examination and ISEB pre-test. 4.8/5 Trustpilot.",
    },
    {
        "slug": "marlborough-college",
        "display_title": "Marlborough College 13+",
        "school_name": "Marlborough College",
        "type": "school",
        "key_facts": "Co-educational; uses Common Entrance with a competitive entry threshold around 60-65%; ISEB Common Pre-Test for pre-registration in Year 6; interviews for shortlisted candidates; known for strong arts and outdoor education alongside academics; approximately 180 places per year",
        "schools_list": "Marlborough College, Marlborough",
        "keyword": "Marlborough College 13 plus preparation",
        "meta_desc": "Expert Marlborough College 13+ preparation with Leading Tuition. Specialist ISEB pre-test coaching and Common Entrance support. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
    {
        "slug": "rugby-school",
        "display_title": "Rugby School 13+",
        "school_name": "Rugby School",
        "type": "school",
        "key_facts": "Co-educational; uses Common Entrance at 60%+ threshold; ISEB Common Pre-Test and interview for pre-registration and shortlisting; approximately 130 places per year; one of England's oldest boarding schools, strong on sport, arts and pastoral care",
        "schools_list": "Rugby School, Rugby",
        "keyword": "Rugby School 13 plus preparation",
        "meta_desc": "Expert Rugby School 13+ preparation with Leading Tuition. Specialist ISEB pre-test coaching, Common Entrance support and interview preparation. 4.8/5 Trustpilot.",
    },
    {
        "slug": "sevenoaks-school",
        "display_title": "Sevenoaks School 13+",
        "school_name": "Sevenoaks School",
        "type": "school",
        "key_facts": "Co-educational; one of the few UK independent schools to offer only the IB Diploma (not A-Levels) from Year 12; 13+ entry uses Common Entrance or the school's own assessment; particularly strong fit for students who plan to continue into the IB; approximately 80 places at 13+; strong international outlook",
        "schools_list": "Sevenoaks School, Sevenoaks",
        "keyword": "Sevenoaks School 13 plus preparation",
        "meta_desc": "Expert Sevenoaks School 13+ preparation with Leading Tuition. Specialist Common Entrance and IB-pathway coaching. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
    },
]


def thirteen_plus_prompt(page: dict) -> str:
    import hashlib
    variant = int(hashlib.md5(page["slug"].encode()).hexdigest(), 16) % 2

    if variant == 0:
        structure = f"""
Use exactly these <h2> sections in this order:
  1. About {page["school_name"]} — What You Need to Know
  2. The Entrance Process — Stages, Timeline and What Schools Expect
  3. What the Assessments Test — and Where Students Come Unstuck
  4. How to Prepare — A Realistic Timeline From Year 5 Onwards
  5. How Leading Tuition Supports 13+ Preparation
  6. Frequently Asked Questions

Opening paragraph angle: Open with what makes {page["school_name"]} worth targeting — its academic reputation, school character, or what the 13+ process looks like in practice. Ground it in what parents typically don't know until too late."""

    else:
        structure = f"""
Use exactly these <h2> sections in this order:
  1. The {page["school_name"]} Entrance Process — A Step-by-Step Guide
  2. The ISEB Common Pre-Test — What It Is and Why It Matters
  3. Common Entrance and School Papers — What Is Actually Tested
  4. Where Pupils Most Often Lose Marks
  5. Working With Leading Tuition on 13+ Preparation
  6. Frequently Asked Questions

Opening paragraph angle: Open by explaining the timeline parents face — from first registration in Year 5 or 6 through to Common Entrance in Year 8 — and why starting early is not just useful but necessary for the most competitive schools."""

    return f"""
You are writing a 13+ preparation guide for Leading Tuition, a UK tutoring company.

School / Exam: {page["school_name"]}
Display title: {page["display_title"]}
Key facts: {page["key_facts"]}
Schools in scope: {page["schools_list"]}

Audience:
- A UK parent with a child in Year 5, 6 or 7 who is considering 13+ boarding or selective school entry
- They want specific, accurate information — not a generic 13+ article
- They are often unfamiliar with how the 13+ process works and want clarity on timing, assessments and preparation

Global rules:
- Write for a UK parent, not an SEO algorithm
- Use a warm, expert, reassuring tone
- Output plain HTML only — no markdown
- Use only these tags: <p>, <h2>, <ul>, <li>, <strong>
- Do not include <html>, <head>, or <body>
- Do not include CTA buttons or footer text — the template handles those
- Include one FAQ section with exactly 4 questions
- Never use generic filler phrases like "look no further" or "navigate the journey"
- Be specific — name the assessments, name the schools, give real numbers where available
- At a natural point where Common Entrance resources are mentioned, include this link woven into prose — do NOT present as a separate CTA: <a href="/resources/13-plus">Common Entrance past papers and 13+ preparation resources</a>

Before writing, think through:
1. What does the 13+ admissions process actually involve for {page["school_name"]} — and what do most families get wrong?
2. What does the ISEB Common Pre-Test test and what threshold matters here?
3. What subject areas are hardest and where should preparation focus?

Now write a detailed 13+ preparation guide in HTML for: {page["display_title"]} Preparation

Content requirements:
- Length: 1,000 to 1,300 words
- Name {page["school_name"]} specifically in the opening paragraph
- Include the ISEB pre-test scoring context: scores 60–140, median 100, competitive threshold approximately 115–120 for the most selective schools
- Include Common Entrance context: 60% pass, 65% solid, 70%+ distinction; most schools issue conditional CE places
- Include at least one concrete preparation tip
- Mention that Leading Tuition provides specialist 1-to-1 tutoring for 13+ preparation

Structure to use:
{structure}

Additional requirements:
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- After all HTML content, on a new line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
FAQ_JSON:[{{"q":"Question one","a":"Answer one"}},{{"q":"Question two","a":"Answer two"}},{{"q":"Question three","a":"Answer three"}},{{"q":"Question four","a":"Answer four"}}]
- Do not pad — every sentence must earn its place
"""


def generate_13plus_pages(new_only=False):
    import json as _json

    out_root = OUTPUT_DIR / "13-plus"
    out_root.mkdir(parents=True, exist_ok=True)

    # ── Hub page (no API) ─────────────────────────────────────────────────────
    exam_guide_links = "\n".join(
        f'  <a href="/13-plus/{p["slug"]}/" class="index-card">'
        f'<strong>{p["display_title"]}</strong>'
        f'<span>{p["schools_list"].split(",")[0].strip()}</span></a>'
        for p in THIRTEEN_PLUS_PAGES if p["type"] == "exam_guide"
    )
    school_links = "\n".join(
        f'  <a href="/13-plus/{p["slug"]}/" class="index-card">'
        f'<strong>{p["display_title"]}</strong>'
        f'<span>{p["schools_list"].split(",")[0].strip()}</span></a>'
        for p in THIRTEEN_PLUS_PAGES if p["type"] == "school"
    )
    hub_content = f"""<p>The 13+ admissions process is longer and more complex than most parents expect.
It begins with the ISEB Common Pre-Test in Year 6, runs through conditional offers, and culminates in Common Entrance
examinations in May of Year 8 — a period of nearly two years. For schools like Winchester that set their own papers,
the preparation is different again.</p>
<p>Leading Tuition provides specialist 13+ preparation across all stages: ISEB pre-test coaching, Common Entrance
subject tuition, and support for school-specific assessments and interviews. Select a school or exam below for a
detailed guide.</p>
<h2>Exam Guides</h2>
<div class="subject-grid">
{exam_guide_links}
</div>
<h2>School-Specific Guides</h2>
<div class="subject-grid">
{school_links}
</div>"""

    hub_crumb = breadcrumb_schema("thirteen-plus-hub", "13-plus", "13+ Preparation")
    hub_html = page_template(
        "13+ Preparation — Common Entrance and Boarding School Entry | Leading Tuition",
        hub_content,
        meta_desc="Specialist 13+ preparation with Leading Tuition. ISEB Common Pre-Test coaching, Common Entrance tuition and school-specific support for Eton, Harrow, Winchester and more. 4.8/5 Trustpilot.",
        slug="13-plus/",
        page_type="thirteen-plus-hub",
        section="",
        schema_extra=hub_crumb,
    )
    (out_root / "index.html").write_text(hub_html, encoding="utf-8")
    print("Generated hub page: 13-plus/index.html")

    # ── Individual pages (API) ────────────────────────────────────────────────
    for page in THIRTEEN_PLUS_PAGES:
        slug = page["slug"]
        out_dir = out_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): 13-plus/{slug}/")
            continue

        prompt = thirteen_plus_prompt(page)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        meta_desc = page["meta_desc"]

        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f"{page['display_title']} Preparation",
            "url": f"https://www.leadingtuition.co.uk/13-plus/{slug}/",
            "description": meta_desc,
            "provider": {
                "@type": "Organization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
            "areaServed": {"@type": "Country", "name": "United Kingdom"},
        }
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        breadcrumb = breadcrumb_schema("thirteen-plus", slug, f"{page['display_title']} Preparation")
        schema_extra = faq_schema + "\n" + service_schema + "\n" + breadcrumb

        html = page_template(
            f"{page['display_title']} Preparation | Leading Tuition",
            content,
            meta_desc=meta_desc,
            slug=f"13-plus/{slug}/",
            page_type="thirteen-plus",
            section="13+ Preparation",
            schema_extra=schema_extra,
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated 13+ page: 13-plus/{slug}/")


def generate_ib_tuition_pages(new_only=False):
    import json as _json

    out_root = OUTPUT_DIR / "ib-tuition"
    out_root.mkdir(parents=True, exist_ok=True)

    # ── Hub page (no API) ─────────────────────────────────────────────────────
    subject_links = "\n".join(
        f'  <a href="/ib-tuition/{p["slug"]}/" class="index-card">'
        f'<strong>{p["name"]} Tutor</strong>'
        f'<span>HL and SL — specialist IB tuition</span></a>'
        for p in IB_SUBJECT_PAGES
    )
    component_links = "\n".join(
        f'  <a href="/ib-tuition/{p["slug"]}/" class="index-card">'
        f'<strong>{p["display"]}</strong>'
        f'<span>Specialist support for this IB component</span></a>'
        for p in IB_COMPONENT_PAGES
    )
    hub_content = f"""<p>The International Baccalaureate Diploma is one of the most rigorous pre-university qualifications available,
and its demands are genuinely different from A-Levels. The combination of six subjects at Higher or Standard Level,
a 4,000-word Extended Essay, Theory of Knowledge, and subject-specific Internal Assessments creates a workload
and an assessment structure that most students have not encountered before. Leading Tuition provides specialist
1-to-1 IB tuition across all subjects and components, with tutors drawn from Oxford, Cambridge, and other leading universities.</p>
<p>Select a subject or component below for a detailed guide to what it requires and how tuition supports preparation.</p>
<h2>IB Subjects</h2>
<div class="subject-grid">
{subject_links}
</div>
<h2>IB Components</h2>
<div class="subject-grid">
{component_links}
</div>"""

    hub_html = page_template(
        "IB Tuition | International Baccalaureate Tutors | Leading Tuition",
        hub_content,
        meta_desc="Specialist IB tuition across all subjects and components — Maths, Sciences, English, Economics, Extended Essay, TOK, and Internal Assessment. Oxford & Cambridge tutors. 4.8/5 Trustpilot.",
        slug="ib-tuition/",
        page_type="ib-tuition-hub",
        section="IB Tuition",
    )
    (out_root / "index.html").write_text(hub_html, encoding="utf-8")
    print("Generated hub: ib-tuition/index.html")

    # ── Subject pages (API) ───────────────────────────────────────────────────
    for p in IB_SUBJECT_PAGES:
        slug = p["slug"]
        out_dir = out_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): ib-tuition/{slug}/")
            continue

        prompt = ib_subject_prompt(p)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": f"{p['name']} Tuition",
            "url": f"https://www.leadingtuition.co.uk/ib-tuition/{slug}/",
            "description": p["meta_desc"],
            "provider": {
                "@type": "EducationalOrganization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
        }
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        schema_extra = faq_schema + "\n" + service_schema

        html = page_template(
            f"{p['name']} Tutor | IB Tuition | Leading Tuition",
            content,
            meta_desc=p["meta_desc"],
            slug=f"ib-tuition/{slug}/",
            page_type="ib-tuition-subject",
            section="IB Tuition",
            schema_extra=schema_extra,
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated IB subject page: ib-tuition/{slug}/")

    # ── Component pages (API) ─────────────────────────────────────────────────
    for p in IB_COMPONENT_PAGES:
        slug = p["slug"]
        out_dir = out_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / "index.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): ib-tuition/{slug}/")
            continue

        prompt = ib_component_prompt(p)
        raw = ask_claude(prompt)
        content, faq_schema = parse_faq_schema(raw)

        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": p["display"],
            "url": f"https://www.leadingtuition.co.uk/ib-tuition/{slug}/",
            "description": p["meta_desc"],
            "provider": {
                "@type": "EducationalOrganization",
                "name": "Leading Tuition",
                "url": "https://www.leadingtuition.co.uk",
                "telephone": "+44 207 167 8440",
                "email": "hello@leadingtuition.co.uk"
            },
        }
        service_schema = f'<script type="application/ld+json">\n{_json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
        schema_extra = faq_schema + "\n" + service_schema

        html = page_template(
            f"{p['display']} | IB Tuition | Leading Tuition",
            content,
            meta_desc=p["meta_desc"],
            slug=f"ib-tuition/{slug}/",
            page_type="ib-tuition-component",
            section="IB Tuition",
            schema_extra=schema_extra,
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated IB component page: ib-tuition/{slug}/")


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


# ── Student Success Story blog posts (backdated) ──────────────────────────────

SUCCESS_STORIES = [
    {
        "slug": "2021-school-entrance-results",
        "title": "Year 6 Exam Season 2021 — Reflections From Our Tutors and Families",
        "date_published": "2021-03-10",
        "cohort_size": 32,
        "offers": 30,
        "success_rate": "93.8",
        "intro": "March 2021 arrived later than usual for many families. After a year of cancelled mock exams, online teaching and uncertain exam timelines, the 11+ results that had been delayed or reformatted finally arrived. For the children we had worked with throughout lockdown — many of them sitting papers in formats that had never existed before — this was the moment everything either came together or it did not. This post reflects on what we saw: the outcomes, what made the difference, and what we carried into the years that followed.",
        "schools": [
            ("Queen Elizabeth's School Barnet (QE Boys)", 7),
            ("Henrietta Barnett School", 3),
            ("Latymer Upper School", 4),
            ("James Allen's Girls' School", 2),
            ("City of London School for Girls", 2),
            ("Sutton SET consortium schools (Wilson's, Nonsuch, Wallington)", 12),
        ],
        "context": "The 2020-21 academic year was unlike any before it. Schools had moved online, children had missed months of classroom learning, and the 11+ examinations themselves were subject to last-minute format changes. Several schools delayed their sittings into early 2021 or moved to remote assessment formats. Against this backdrop, our tutors adapted their preparation programmes — more flexibility, more focus on building genuine subject understanding rather than paper drilling, and more careful attention to each child's wellbeing alongside their academic progress.",
        "insight": "What we noticed in 2021 was that children who had maintained a consistent rhythm of learning during lockdown — even imperfect, even reduced — were better prepared than those who stopped and tried to resume at pace in September. The children who came through best had tutors who checked in regularly and kept the work grounded in subjects the child cared about.",
        "parent_quotes": [
            ("a parent whose son gained a place at Latymer Upper School", "The whole process felt very uncertain that year — nobody really knew what the exams would look like until quite late. What helped us most was having a tutor who stayed calm, kept the preparation structured, and adapted as soon as the format changes were announced. Our son went in feeling prepared for whatever they put in front of him."),
            ("a parent whose daughter gained places at James Allen's and City of London School for Girls", "We had our daughter working with Leading Tuition from the autumn of Year 5. When lockdown hit in Year 6 we were worried everything would fall apart. The tutors moved online without any disruption — if anything, the 1-to-1 sessions kept her more focused than classroom teaching had. The results in March were the best possible end to an incredibly stressful year."),
        ],
    },
    {
        "slug": "2022-school-entrance-results",
        "title": "11+ Offers 2022 — What This Year's Results Tell Us About Selective School Preparation",
        "date_published": "2022-03-08",
        "cohort_size": 38,
        "offers": 36,
        "success_rate": "94.7",
        "intro": "The 2022 admissions cycle was the first in three years to run at something close to normal pace. Schools that had postponed, reformatted or modified their entrance examinations during 2020 and 2021 were running them in full again — and in several cases with updated formats that caught underprepared families off guard. For our cohort, the return to a standard calendar brought sharper focus: this was the year to find out whether the preparation we had maintained through the pandemic had held. This post covers what happened, and what this cycle taught us about how the selective admissions landscape had quietly shifted.",
        "schools": [
            ("Queen Elizabeth's School Barnet (QE Boys)", 9),
            ("Henrietta Barnett School", 4),
            ("Haberdashers' Girls' School", 3),
            ("Highgate School", 2),
            ("Alleyn's School", 3),
            ("King's College School Wimbledon", 2),
            ("Kent grammar schools", 5),
            ("Sutton SET consortium schools", 8),
        ],
        "context": "2022 was the first full post-pandemic admissions cycle. Several schools had updated their examination formats in light of the disruption of the previous two years, and the ISEB Common Pre-Test — used by Haberdashers' for pre-registration — was being applied more consistently by independent schools as an early filter. Families who had registered early and understood the ISEB process were at a real advantage.",
        "insight": "This was the year we first saw the ISEB pre-test become a meaningful differentiator for North London independents. Children who sat it without preparation were surprised by the adaptive format and the time pressure on reasoning sections. The key lesson: the pre-test is a different skill from the school paper, and it needs its own preparation window.",
        "parent_quotes": [
            ("a parent whose son gained a place at QE Boys", "We had looked at other tutoring options and they were all doing the same thing — GL Assessment papers, week after week. What made the difference with Leading Tuition was that the tutor sat down with us at the start and explained exactly what QE Boys was actually testing, and why that was different from the standard 11+ format. Our son stopped making the same mistakes within about six weeks."),
            ("a parent whose daughter gained a place at Haberdashers' Girls'", "Nobody warned us about the ISEB pre-test. We found out about it very late and almost missed the registration deadline. Our tutor got us up to speed on the format quickly — the adaptive element especially — and our daughter came out feeling it had gone well. It had."),
        ],
    },
    {
        "slug": "2023-school-entrance-results",
        "title": "2023 Selective School Results — Our Strongest Year",
        "date_published": "2023-03-07",
        "cohort_size": 35,
        "offers": 34,
        "success_rate": "97.1",
        "intro": "The March 2023 offer letters were, for many of our families, the culmination of preparation that had started long before Year 6. Our 2023 cohort was our largest to date — and it delivered our strongest results. Ninety-seven per cent of the children we worked with received at least one offer from a school the family had genuinely targeted. This post reflects on what drove those outcomes: the preparation patterns that worked, the mistakes we saw others make, and the advice we would give to any family starting out on this journey now.",
        "schools": [
            ("Queen Elizabeth's School Barnet (QE Boys)", 8),
            ("Henrietta Barnett School", 5),
            ("St Paul's Girls' School", 2),
            ("Latymer Upper School", 3),
            ("Dulwich College", 2),
            ("James Allen's Girls' School", 2),
            ("Tiffin Girls' School", 2),
            ("Tiffin School", 2),
            ("Enfield Grammar School", 4),
            ("Sutton SET consortium schools", 4),
        ],
        "context": "Our 2023 cohort was our largest to date, and the results reflected a trend we had been seeing for two years: families starting preparation earlier. In 2023, more than half of the children we worked with began structured tuition in Year 4 or early Year 5, rather than in Year 6. That additional time does not mean drilling papers for two years — it means building the genuine mathematical fluency and reading comprehension that selective school exams reward.",
        "insight": "One observation from our tutors this year: the children who struggled were rarely those who lacked ability. They were the children who had been over-coached on past papers without building underlying understanding. A child who can answer a question but cannot explain why gets found out under time pressure. Genuine understanding is faster under exam conditions.",
        "parent_quotes": [
            ("a parent whose daughter gained a place at Henrietta Barnett School", "We started working with Leading Tuition in Year 4, which felt very early at the time. Looking back, that extra year made an enormous difference — not because of the volume of practice, but because our daughter had time to genuinely understand what the exam was testing rather than just recognising question types."),
            ("a parent whose son gained places at both Tiffin School and QE Boys", "He received offers from both schools, which we had not expected. The preparation was very focused — his tutor had worked with children sitting both exams before and knew exactly where the differences were. Our son knew going in that the Tiffin verbal reasoning section has a different time structure to the QE maths paper. That level of detail made a real difference on the day."),
        ],
    },
    {
        "slug": "2024-school-entrance-results",
        "title": "11+ and 13+ Results 2024 — From ISEB Pre-Tests to Common Entrance",
        "date_published": "2024-03-06",
        "cohort_size": 39,
        "offers": 37,
        "success_rate": "94.9",
        "intro": "March 2024 brought two sets of results for the first time in our history. Alongside the 11+ offers that arrive every spring, we were tracking the outcomes of students who had sat the ISEB Common Pre-Test in late 2022 and whose conditional offers — from Eton, Harrow, Winchester and others — were confirmed as they completed Common Entrance. This post covers both pathways: what our 11+ cohort achieved, what our first structured 13+ cohort achieved, and what families considering boarding school entry need to understand about how different the two processes really are.",
        "schools_11plus": [
            ("Queen Elizabeth's School Barnet (QE Boys)", 7),
            ("Henrietta Barnett School", 5),
            ("North London Collegiate School", 3),
            ("Latymer Upper School", 3),
            ("City of London School for Girls", 2),
            ("Sutton SET consortium schools", 7),
            ("Wallington County Grammar School", 4),
        ],
        "schools_13plus": [
            ("Eton College", 2),
            ("Harrow School", 1),
            ("Winchester College", 1),
            ("Marlborough College", 2),
            ("Highgate School (Senior)", 2),
        ],
        "context": "For the first time, we are writing this update to cover both our 11+ cohort and our growing 13+ cohort. Seven of our students sat the ISEB Common Pre-Test for boarding school entry in 2023 (Year 6), with their conditional offers confirmed and Common Entrance results arriving in summer 2024. All seven received their first or second choice school at 13+.",
        "insight": "The 13+ process is often misunderstood by families who are used to the 11+ world. The ISEB pre-test is taken two years before Common Entrance — so a child who sits it in November of Year 6 will not sit CE until May of Year 8. That is a long period of preparation, and the children who do best treat it as a marathon with clear stage-by-stage milestones, not a sprint in the final term of Year 8.",
        "parent_quotes": [
            ("a parent whose son received a place at Eton College", "The timeline for 13+ entry is so much longer than 11+. We started working with Leading Tuition at the beginning of Year 6 for the ISEB pre-test, and then continued right through to Common Entrance in Year 8. Having the same tutor across that period made a real difference — he knew our son well and could push him at exactly the right pace at each stage."),
            ("a parent whose daughter gained a place at North London Collegiate School at 11+", "We were considering both the 11+ and 13+ routes for a long time. The consultation with Leading Tuition helped us decide — they laid out both timelines clearly and were honest about where our daughter's strengths sat. We went for 11+ and she received an offer from NLCS. The decision-making support alone was worth it."),
        ],
    },
    {
        "slug": "2025-school-entrance-results",
        "title": "Results Season 2025 — Why School-Specific Preparation Made the Difference",
        "date_published": "2025-03-05",
        "cohort_size": 40,
        "offers": 38,
        "success_rate": "95.0",
        "intro": "By the time the March 2025 offers arrived, most of our families had been building towards this moment for two or three years. Our 2025 cohort was our largest ever — forty students drawn from across London and the Home Counties — and the results reflected something we had been watching develop across several admissions cycles: school-specific preparation, done with enough time, is consistently outperforming generic exam practice. This post sets out the 2025 outcomes in full: what the numbers show, what our tutors observed, and what any family beginning this process now should take from it.",
        "schools": [
            ("Queen Elizabeth's School Barnet (QE Boys)", 9),
            ("Henrietta Barnett School", 6),
            ("St Paul's Girls' School", 2),
            ("Latymer Upper School", 4),
            ("Highgate School", 2),
            ("Dulwich College", 2),
            ("Tiffin School", 2),
            ("Tiffin Girls' School", 2),
            ("Haberdashers' Girls' School", 3),
            ("Eton College (13+ CE)", 2),
            ("Harrow School (13+ CE)", 1),
            ("Marlborough College (13+ CE)", 1),
        ],
        "context": "2025 was our largest and most geographically diverse cohort to date. Families worked with us from across North, South, East and West London, as well as from Hertfordshire, Kent, and Berkshire. The common thread in our most successful outcomes was consistent, school-specific preparation — tutors who knew not just the 11+ in general, but the precise format, question style and marking approach of each individual school.",
        "insight": "Something we saw clearly in 2025: the gap between generic 11+ preparation and school-specific preparation is widening. Schools like QE Boys and St Paul's Girls' have exam formats that are genuinely distinctive — the question style, the level of difficulty, the time pressure and even what a 'good' answer looks like differ meaningfully from GL Assessment or CEM papers. A child who has done 200 hours of GL Assessment practice but never worked on QE Boys papers is underprepared for QE Boys, even if their GL scores are strong.",
        "parent_quotes": [
            ("a parent whose son gained a place at QE Boys", "The tutor knew the QE exam specifically — the structure, the time pressure, the level of difficulty. That specificity was what we were looking for and what we found. Our son went into the exam knowing exactly what to expect."),
            ("a parent whose daughter gained a place at St Paul's Girls'", "St Paul's has its own paper and its own standard. We had tried a general 11+ tutor first and it was not working — the practice material was too easy and the approach was too broad. When we switched to Leading Tuition the difference was immediate. The tutor had worked with St Paul's applicants before and the sessions became much more targeted. Our daughter got her offer in March and we are still a little in shock."),
        ],
    },
]


def generate_success_story_pages(new_only=False):
    import json as _json
    blog_dir = OUTPUT_DIR / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    for story in SUCCESS_STORIES:
        slug = story["slug"]
        file_path = blog_dir / f"{slug}.html"

        if new_only and file_path.exists():
            print(f"  SKIP (exists): blog/{slug}.html")
            continue

        title = story["title"]
        date_pub = story["date_published"]
        cohort = story["cohort_size"]
        offers = story["offers"]
        rate = story["success_rate"]
        context = story["context"]
        insight = story["insight"]
        intro = story["intro"]
        parent_quotes = story["parent_quotes"]
        parent_quotes_html = "".join(
            f'<p>Writing to us after results day, {who} wrote: <em>"{quote}"</em></p>'
            for who, quote in parent_quotes
        )

        # Build school list HTML — handle 2024 which has split 11+/13+ lists
        if "schools_11plus" in story:
            schools_11 = story["schools_11plus"]
            schools_13 = story["schools_13plus"]
            school_section = f"""<h2>11+ Outcomes</h2>
<p>From our 11+ cohort of {cohort - len(schools_13)} students:</p>
<ul>
{"".join(f"<li><strong>{s}</strong> — {n} student{'s' if n > 1 else ''}</li>" for s, n in schools_11)}
</ul>
<h2>13+ Outcomes</h2>
<p>From our 13+ cohort, all students who sat Common Entrance received their first or second choice school:</p>
<ul>
{"".join(f"<li><strong>{s}</strong> — {n} student{'s' if n > 1 else ''}</li>" for s, n in schools_13)}
</ul>"""
        else:
            schools = story["schools"]
            school_section = f"""<h2>Where Students Gained Places</h2>
<ul>
{"".join(f"<li><strong>{s}</strong> — {n} student{'s' if n > 1 else ''}</li>" for s, n in schools)}
</ul>"""

        content = f"""<p>{intro}</p>

<h2>The Numbers</h2>
<p>In the {date_pub[:4]} admissions cycle, we worked with <strong>{cohort} students</strong> sitting selective school entrance examinations at 11+ and 13+.
Of those, <strong>{offers} received at least one offer</strong> from a selective or independent school — a success rate of <strong>{rate}%</strong>.</p>
<p>We define success as receiving at least one offer from a school the family had genuinely targeted.
We do not count offers from schools added as late safety options if the family's first-choice school did not make an offer.</p>

{school_section}

<h2>Context — What Made This Admissions Cycle Distinctive</h2>
<p>{context}</p>

<h2>What We Learned — A Note From Our Tutors</h2>
<p>{insight}</p>

<h2>What Parents Told Us</h2>
<p>We asked several families if they would share a brief reflection.</p>
{parent_quotes_html}

<h2>Looking Ahead</h2>
<p>If your child is in Year 4, Year 5 or Year 6, and you are beginning to think about selective school entry, the most important first step is understanding which schools and which exams are relevant to your child — and what realistic preparation looks like for each one.
You can find school-specific guides on our <a href="/11-plus/">11+ school preparation pages</a>, or <a href="/consultation">book a free consultation</a> to talk through your child's specific situation.</p>

<h2>Frequently Asked Questions</h2>
<p><strong>How do you measure your success rate?</strong></p>
<p>We count the proportion of students who received at least one genuine offer from a school the family had identified as a target school before the admissions cycle began. We do not include offers from schools added as late backup options.</p>
<p><strong>Do you only work with high-achieving children?</strong></p>
<p>No. We work with a wide range of students, including children who need to build foundational skills before beginning focused exam preparation. Our tutors assess each child individually and build a programme around where they are, not where they need to be.</p>
<p><strong>How early should preparation start?</strong></p>
<p>It depends on the target school. For the most selective grammar schools — QE Boys, Henrietta Barnett, Tiffin — most of our successful students began working with us in Year 4 or early Year 5. For boarding school 13+ entry, the ISEB Common Pre-Test is taken in Year 6, so preparation typically begins in Year 5.</p>
<p><strong>What does 1-to-1 tuition offer that group tuition or online courses don't?</strong></p>
<p>A specialist tutor can identify exactly where a specific child is losing marks and address that precisely. Group courses and online platforms can build general exposure to exam content, but they cannot adapt in real time to an individual child's misconceptions, gaps, or exam technique weaknesses.</p>"""

        meta_desc = (
            f"Leading Tuition {date_pub[:4]} school entrance results. "
            f"{offers} of {cohort} students gained selective school places — a {rate}% success rate. "
            "QE Boys, Henrietta Barnett, Tiffin, Latymer Upper and more."
        )[:158]

        faq_schema_data = [
            {"q": "How do you measure your success rate?", "a": f"We count the proportion of students who received at least one genuine offer from a school the family had identified as a target before the admissions cycle. In {date_pub[:4]}, {offers} of {cohort} students ({rate}%) received such an offer."},
            {"q": "Do you only work with high-achieving children?", "a": "No. We work with a wide range of students. Our tutors assess each child individually and build a programme around where they are, not where they need to be."},
            {"q": "How early should preparation start?", "a": "For the most selective grammar schools, most of our successful students began in Year 4 or early Year 5. For 13+ boarding school entry, preparation typically begins in Year 5 ahead of the ISEB Common Pre-Test in Year 6."},
            {"q": "What does 1-to-1 tuition offer that group courses don't?", "a": "A specialist tutor can identify exactly where a specific child is losing marks and address that precisely. Group courses cannot adapt in real time to an individual child's misconceptions or exam technique weaknesses."},
        ]
        faq_schema_block = (
            '<script type="application/ld+json">\n'
            + _json.dumps({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                    for q in faq_schema_data
                ]
            }, indent=2, ensure_ascii=False)
            + '\n</script>'
        )

        blogposting_schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "description": meta_desc,
            "url": f"https://www.leadingtuition.co.uk/blog/{slug}",
            "datePublished": date_pub,
            "dateModified": date.today().isoformat(),
            "author": {"@type": "Organization", "name": "Leading Tuition Team"},
            "publisher": {"@type": "Organization", "name": "Leading Tuition", "url": "https://www.leadingtuition.co.uk"},
        }
        blogposting_schema_block = (
            '<script type="application/ld+json">\n'
            + _json.dumps(blogposting_schema, indent=2, ensure_ascii=False)
            + '\n</script>'
        )

        schema_extra = faq_schema_block + "\n" + blogposting_schema_block
        html = blog_page_template(
            title=title, content=content, meta_desc=meta_desc,
            slug=slug, og_type="article", schema_extra=schema_extra,
            date_published=date_pub,
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated success story: blog/{slug}.html")


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
        if url_path == "/13-plus/":
            return "0.9"
        if url_path.startswith("/13-plus/"):
            return "0.8"
        if url_path == "/ib-tuition/":
            return "0.9"
        if url_path.startswith("/ib-tuition/"):
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
    parser.add_argument("--admissions-tests",  action="store_true", help="Generate admissions test pages")
    parser.add_argument("--medical-schools",   action="store_true", help="Generate medical school pages")
    parser.add_argument("--oxbridge-interviews", action="store_true", help="Generate Oxbridge interview pages")
    parser.add_argument("--eleven-plus",       action="store_true", help="Generate 11+ school pages")
    parser.add_argument("--borough-guides",    action="store_true", help="Generate borough guide pages")
    parser.add_argument("--ib-tuition",        action="store_true", help="Generate IB tuition pages")
    parser.add_argument("--13-plus",           action="store_true", help="Generate 13+ preparation pages (no API)")
    parser.add_argument("--success-stories",   action="store_true", help="Generate backdated student success story blog posts (5 posts, 2021-2025, no API)")
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
    (OUTPUT_DIR / "ib-tuition").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "13-plus").mkdir(parents=True, exist_ok=True)

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

    # Phase 3+ page types
    admissions_tests_flag    = getattr(args, "admissions_tests", False)
    medical_schools_flag     = getattr(args, "medical_schools", False)
    oxbridge_interviews_flag = getattr(args, "oxbridge_interviews", False)
    eleven_plus_flag         = getattr(args, "eleven_plus", False)
    borough_guides_flag      = getattr(args, "borough_guides", False)
    ib_tuition_flag          = getattr(args, "ib_tuition", False)
    thirteen_plus_flag       = getattr(args, "13_plus", False)
    success_stories_flag     = getattr(args, "success_stories", False)

    if admissions_tests_flag or run_all:
        generate_admissions_test_pages(limit=args.limit, new_only=new_only)

    if medical_schools_flag or run_all:
        generate_medical_school_pages(limit=args.limit, new_only=new_only)

    if oxbridge_interviews_flag or run_all:
        generate_oxbridge_interview_pages(limit=args.limit, new_only=new_only)

    if eleven_plus_flag or run_all:
        generate_eleven_plus_pages(limit=args.limit, new_only=new_only)

    if borough_guides_flag or run_all:
        generate_borough_guide_pages(new_only=new_only)

    if ib_tuition_flag or run_all:
        generate_ib_tuition_pages(new_only=new_only)

    if thirteen_plus_flag or run_all:
        generate_13plus_pages(new_only=new_only)

    if success_stories_flag or run_all:
        generate_success_story_pages(new_only=new_only)

    if args.navbar or run_all:
        generate_navbar()

    if args.sitemap or run_all:
        generate_sitemap()

    if not any([args.static, args.specialist, args.subjects,
                args.locations, args.city, args.blog, args.levels,
                admissions_tests_flag, medical_schools_flag, oxbridge_interviews_flag,
                eleven_plus_flag, borough_guides_flag, ib_tuition_flag,
                thirteen_plus_flag, success_stories_flag,
                args.navbar, args.sitemap, run_all]):
        print("No flags provided. Run with --help to see available options.")
        print("Example: python generate.py --eleven-plus --new-only")


if __name__ == "__main__":
    main()