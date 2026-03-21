import csv
import os
import re
import json
import argparse
import anthropic
from datetime import date
from pathlib import Path
from templates import (page_template, location_page_template, blog_page_template,
                       service_page_template, breadcrumb_schema)


def parse_faq_schema(response_text):
    """Extract FAQ_JSON block from Claude response. Returns (clean_content, faq_schema_html)."""
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

OUTPUT_DIR = Path("output")


def load_csv(filename):
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def ask_claude(prompt: str, max_tokens: int = 3200) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        temperature=0.35,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.content[0].text.strip()


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
        meta_desc = (
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

Requirements:
- Target length: 950 to 1,100 words
- Opening paragraph must mention {city} by name and acknowledge {local_pressure}
- You MUST mention at least 3 of these real local schools by name: {schools_str}
- You MUST name at least 2 of these local neighbourhoods or areas: {areas_str}
- {gcse_section_note}
{eleven_plus_note}
{oxbridge_note}

Use exactly these <h2> sections in this order:
  1. Tutoring in {city} — What We Offer
  2. {gcse_section_title}
  3. 11+ and Grammar School Preparation  [include even if 11+ is less prominent — adapt tone accordingly]
  4. Medicine and University Admissions Preparation
  5. Why {city} Families Choose Leading Tuition
  6. Frequently Asked Questions about Tutoring in {city}

Additional requirements:
- Include one short <ul> bullet list somewhere in the page (not in the FAQ section)
- In the FAQ section, write 4 questions as <p><strong>Question?</strong></p> followed by a <p> answer
- FAQ questions must be specific to {city} families, not generic
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
- After all HTML content, on a new line, output exactly 4 FAQ pairs in this format (no spaces, no line breaks inside):
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
}


def generate_blog_pages(limit=None):
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

        _ucat_mmi_oxbridge = any(kw in slug for kw in ("ucat", "mmi", "oxbridge"))
        meta_desc = (
            f"{title}. Expert advice from Leading Tuition."
            + (" Book a free consultation." if _ucat_mmi_oxbridge else "")
        )

        related_instruction = BLOG_RELATED_RESOURCES.get(slug, "")
        base_prompt = blog_prompt(title=title, keyword=keyword, slug=slug)
        prompt = base_prompt + (f"\n{related_instruction}" if related_instruction else "")
        raw = ask_claude(prompt, max_tokens=4000)
        content, faq_schema = parse_faq_schema(raw)
        blogposting_schema = build_blogposting_schema(title, meta_desc, slug)
        schema_extra = faq_schema + "\n" + blogposting_schema
        html = blog_page_template(title=title, content=content, meta_desc=meta_desc, slug=slug, og_type="article", schema_extra=schema_extra)

        blog_dir = OUTPUT_DIR / "blog"
        blog_dir.mkdir(parents=True, exist_ok=True)
        file_path = blog_dir / f"{slug}.html"
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


def generate_location_pages(limit=None, new_only=False):
    cities = load_csv("locations.csv")
    if limit is not None:
        cities = cities[:limit]

    for row in cities:
        city = row["city"]
        slug = city.lower().replace(" ", "-")
        title = f"Private Tuition in {city}"
        meta_desc = (
            f"Expert private tutors in {city}. DBS checked. GCSE, A-Level, 11+ and medicine prep. "
            f"4.8/5 Trustpilot. Book a free consultation today."
        )

        prompt = location_prompt(city)
        content = ask_claude(prompt, max_tokens=3600)
        html = location_page_template(city=city, title=title, content=content, meta_desc=meta_desc, slug=slug)

        locations_dir = OUTPUT_DIR / "locations"
        locations_dir.mkdir(parents=True, exist_ok=True)
        file_path = locations_dir / f"{slug}.html"
        if new_only and file_path.exists():
            print(f"  SKIP (exists): {file_path}")
            continue
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated location page: {file_path}")


# ── Admissions Test page prompts ─────────────────────────────────────────────

ADMISSIONS_TEST_META = {
    "lnat-preparation": (
        "Expert LNAT preparation from Oxford and Cambridge-educated tutors. "
        "Strategies for all sections of the Law National Aptitude Test. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "mat-preparation": (
        "Expert MAT preparation from Oxford and Cambridge graduates. "
        "Strategies and practice for the Mathematics Admissions Test for Oxford and Imperial. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "pat-preparation": (
        "Expert PAT preparation for Oxford Physics applicants. "
        "Physics Aptitude Test coaching from Oxford-educated tutors. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "tsa-preparation": (
        "Expert TSA preparation for Oxford and Cambridge applicants. "
        "Thinking Skills Assessment coaching covering critical thinking and problem solving. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "hat-preparation": (
        "Expert HAT preparation for Oxford History applicants. "
        "History Aptitude Test coaching and practice from Oxford-educated tutors. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "elat-preparation": (
        "Expert ELAT preparation for Oxford English Literature applicants. "
        "English Literature Admissions Test coaching and essay practice. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "mlat-preparation": (
        "Expert MLAT preparation for Oxford Modern Languages applicants. "
        "Modern Languages Admissions Test coaching and practice. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "step-preparation": (
        "Expert STEP Maths preparation for Cambridge and other university applicants. "
        "Sixth Term Examination Paper coaching from Cambridge-educated mathematicians. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "tmua-preparation": (
        "Expert TMUA preparation for Cambridge, Bath, and other university applicants. "
        "Test of Mathematics for University Admission coaching from specialist tutors. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "esat-preparation": (
        "Expert ESAT preparation for Cambridge Engineering and Science applicants. "
        "Engineering and Science Admissions Test coaching from Cambridge-educated tutors. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "phil-preparation": (
        "Expert Oxford Philosophy Admissions Test (PHIL) preparation. "
        "Coaching on argument analysis, philosophical reasoning, and written response skills. "
        "4.8/5 Trustpilot. Book a free consultation."
    ),
    "bmat-history": (
        "BMAT was abolished in 2023. Find out what replaced it, which universities now use UCAT, "
        "and how Leading Tuition can support your medicine preparation."
    ),
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

Requirements:
- Length: 950 to 1,150 words
- Opening paragraph must acknowledge the challenge the test poses and why specialist preparation matters
- Include these exact <h2> sections in this order:
  1. What Is the {full_name}?
  2. What Does the {full_name} Test?
  3. How the {full_name} Is Scored
  4. How to Prepare Effectively
  5. How Leading Tuition Supports {full_name} Preparation
  6. Frequently Asked Questions
- Must include:
  - Which universities and courses require this test
  - Test format (number of sections, timing, question types)
  - Scoring method and how universities use the score
  - Realistic timeline for preparation (how many weeks/months before the test)
  - Common mistakes and how to avoid them
- Include one short bullet list
- FAQ questions must address: registration deadlines, what score to aim for, whether past papers are available, and how tutoring helps
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

Requirements:
- Length: 1,050 to 1,250 words
- Opening paragraph must explain why a student would choose {name} specifically — make it genuine, not generic
- Include these exact <h2> sections in this order:
  1. Why Choose {name} for Medicine?
  2. Entry Requirements and A-Level Grades
  3. UCAT Requirements at {name}
  4. The Interview Process at {name}
  5. What Makes a Strong {name} Application
  6. Frequently Asked Questions about Applying to {name}
- Must include:
  - Typical A-Level offer (A*AA or AAA with specific subjects)
  - UCAT requirement: {ucat_notes}
  - Interview format: {interview_type} — explain what this involves at {name} specifically
  - Any personal statement or work experience considerations
  - Approximate number of places per year (approximate is fine)
  - Location advantage: {city} — what this means for clinical placements and student life
- Include one short bullet list
- FAQ questions must address: UCAT score needed, whether work experience is required, interview preparation, and whether {name} accepts international students
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
        if url_path.startswith("/admissions-tests/"):
            return "0.8"
        if url_path.startswith("/medical-schools/"):
            return "0.8"
        return "0.6"

    entries = []  # list of (url, lastmod, priority)

    for html_file in sorted(OUTPUT_DIR.rglob("*.html")):
        if html_file.name in SKIP_NAMES:
            continue

        rel = html_file.relative_to(OUTPUT_DIR)
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
    parser.add_argument("--admissions-tests",  action="store_true", help="Generate admissions test pages (LNAT, MAT, PAT, TSA, etc.)")
    parser.add_argument("--medical-schools",   action="store_true", help="Generate medical school entry guide pages (~38 schools)")
    parser.add_argument("--sitemap",           action="store_true", help="Generate sitemap.xml from output/ directory (no API)")
    parser.add_argument("--navbar",            action="store_true", help="Push canonical nav from templates.py to all HTML files in output/ (no API)")
    parser.add_argument("--all",               action="store_true", help="Generate everything (30-45 min)")
    parser.add_argument("--limit",    type=int, default=None,       help="Limit number of pages generated per category")
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

    run_all = args.all
    new_only = args.new_only

    if args.static or run_all:
        generate_static_pages()

    if args.specialist or run_all:
        generate_specialist_pages(limit=args.limit)

    if args.subjects or run_all:
        generate_subject_pages(limit=args.limit)

    if args.locations or run_all:
        generate_location_pages(limit=args.limit, new_only=new_only)

    if args.blog or run_all:
        generate_blog_pages(limit=args.limit)

    if args.levels or run_all:
        generate_level_pages(limit=args.limit)

    # New Phase 3 page types
    admissions_tests_flag = getattr(args, "admissions_tests", False)
    medical_schools_flag  = getattr(args, "medical_schools", False)

    if admissions_tests_flag or run_all:
        generate_admissions_test_pages(limit=args.limit, new_only=new_only)

    if medical_schools_flag or run_all:
        generate_medical_school_pages(limit=args.limit, new_only=new_only)

    # --navbar runs after all generators so manually-written pages get the same nav.
    # It can also be run standalone at any time (no API calls required).
    if args.navbar or run_all:
        generate_navbar()

    # --sitemap runs last so the final sitemap reflects everything just generated.
    # It can also be run standalone at any time (no API calls required).
    if args.sitemap or run_all:
        generate_sitemap()

    if not any([args.static, args.specialist, args.subjects,
                args.locations, args.blog, args.levels,
                admissions_tests_flag, medical_schools_flag,
                args.navbar, args.sitemap, run_all]):
        parser.print_help()


if __name__ == "__main__":
    main()