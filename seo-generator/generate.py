import csv
import os
import argparse
import anthropic
from pathlib import Path
from templates import page_template, location_page_template, blog_page_template, service_page_template

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
  6. 10 to 12 Week Preparation Timeline
  7. Frequently Asked Questions
- Must explicitly include:
  - The 5 UCAT subtests: Verbal Reasoning, Decision Making, Quantitative Reasoning, Abstract Reasoning, Situational Judgement
  - 2024 average score around 615
  - Competitive scores around 670 to 700+ for top medical schools
  - Oxford, Cambridge, and Imperial now use UCAT
  - BMAT was abolished in 2023
  - Students get one attempt per application cycle
  - UCAT is different from A-Level revision because it tests cognitive speed and decision-making, not just learned content
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs about UCAT timing, score expectations, retakes, and tutoring support
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
  3. The Most Common MMI Station Types
  4. How Leading Tuition MMI Coaching Works
  5. MMI Preparation Timeline
  6. Frequently Asked Questions
- Must explicitly include:
  - Typical MMI format: 5 to 10 stations
  - Typical station length: 5 to 8 minutes
  - Different assessors across stations
  - Common station types: ethical scenarios, role play, data interpretation, written station, presentation, empathy station
  - The difference between MMI and traditional panel interviews
  - A realistic preparation timeline of around 6 to 10 weeks
- Include one short bullet list
- In the FAQ section, include 4 specific parent-facing FAQs
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
"""


def subject_prompt(subject: str) -> str:
    chemistry_extra = ""
    if subject.lower() == "chemistry":
        chemistry_extra = """
- You must explicitly mention Required Practicals and explain why students often lose marks on them.
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
{chemistry_extra}
- In the FAQ section, include 4 specific parent-facing FAQs
- End naturally
"""


def generate_specialist_pages(limit=None):
    pages = load_csv("specialist_pages.csv")
    if limit is not None:
        pages = pages[:limit]

    for row in pages:
        slug = row["slug"]
        title = row["title"]
        keyword = row["keyword"]

        prompt = specialist_prompt(title=title, keyword=keyword, slug=slug)
        content = ask_claude(prompt)
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated specialist page: {file_path}")


def generate_subject_pages(limit=None):
    subjects = load_csv("subjects.csv")
    if limit is not None:
        subjects = subjects[:limit]

    for row in subjects:
        subject = row["subject"]
        slug = subject.lower().replace(" ", "-")
        title = f"{subject} Tutor"

        prompt = subject_prompt(subject)
        content = ask_claude(prompt)
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}-tutor.html"
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
  3. UCAT Score Benchmarks by School Tier
  4. What Happens If Your Score Is Below Average
  5. How to Prepare Effectively
  6. Frequently Asked Questions
- Must include:
  - 2024 average UCAT score approximately 615
  - Competitive scores approximately 670 to 700+ for top medical schools
  - The 5 UCAT subtests: Verbal Reasoning, Decision Making, Quantitative Reasoning, Abstract Reasoning, Situational Judgement
  - Situational Judgement is banded (Band 1 to 4), not scored numerically
  - Oxford, Cambridge, and Imperial now use UCAT (BMAT was abolished in 2023)
  - Students have one attempt per application cycle
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
"""


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

        meta_desc = (
            f"{title} — practical guidance for UK parents and students. "
            f"Leading Tuition covers everything you need to know."
        )

        prompt = blog_prompt(title=title, keyword=keyword, slug=slug)
        content = ask_claude(prompt, max_tokens=4000)
        html = blog_page_template(title=title, content=content, meta_desc=meta_desc)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated blog post: {file_path}")


# ── Level page metadata ───────────────────────────────────────────────────────
LEVEL_METADATA = {
    "Primary": {
        "slug": "primary-tuition",
        "title": "Primary Tuition",
        "keyword": "primary school tutor",
        "meta_desc": "Expert primary school tutors for Years 1–6. Maths, English, verbal reasoning, and SATs preparation. DBS checked tutors. Book a free consultation.",
    },
    "11+": {
        "slug": "11plus-tuition",
        "title": "11+ Tuition",
        "keyword": "11 plus tutor",
        "meta_desc": "Specialist 11+ tutors for grammar and independent school entry. Verbal reasoning, maths, English and NVR. CEM and GL Assessment preparation. Free consultation.",
    },
    "13+": {
        "slug": "13plus-tuition",
        "title": "13+ Tuition",
        "keyword": "13 plus tutor",
        "meta_desc": "Expert 13+ and Common Entrance tutors for independent school entry at Year 9. All subjects. School-specific preparation. Book a free consultation.",
    },
    "GCSE": {
        "slug": "gcse-tuition",
        "title": "GCSE Tuition",
        "keyword": "gcse tutor",
        "meta_desc": "Expert GCSE tutors across all subjects and exam boards — AQA, Edexcel, OCR. Grades 9–1. Targeted support from Year 10 through results day. Free consultation.",
    },
    "A-Level": {
        "slug": "a-level-tuition",
        "title": "A-Level Tuition",
        "keyword": "a level tutor",
        "meta_desc": "Specialist A-Level tutors for all subjects. Linear exam preparation, Russell Group and Oxbridge entry support. AQA, Edexcel, OCR. Book a free consultation.",
    },
    "SATs": {
        "slug": "sats-tuition",
        "title": "SATs Tuition",
        "keyword": "sats tutor",
        "meta_desc": "Expert SATs tutors for KS1 and KS2. Year 2 and Year 6 SATs preparation in maths, reading, and grammar. Confidence-building support. Free consultation.",
    },
    "University": {
        "slug": "university-tuition",
        "title": "University Tuition",
        "keyword": "university tutor",
        "meta_desc": "Expert university tutors for undergraduate and postgraduate students. Essays, dissertations, exam preparation, and subject support. Book a free consultation.",
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
        html = service_page_template(title=title, content=content, meta_desc=meta_desc)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated level page: {file_path}")


def generate_location_pages(limit=None):
    cities = load_csv("locations.csv")
    if limit is not None:
        cities = cities[:limit]

    for row in cities:
        city = row["city"]
        slug = city.lower().replace(" ", "-")
        title = f"Private Tuition in {city}"
        meta_desc = (
            f"Expert private tutors in {city}. Leading Tuition supports GCSE, A-Level, 11+, "
            f"and university admissions preparation across {city} and surrounding areas. "
            f"Book a free consultation today."
        )

        prompt = location_prompt(city)
        content = ask_claude(prompt, max_tokens=3600)
        html = location_page_template(city=city, title=title, content=content, meta_desc=meta_desc)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
        print(f"Generated location page: {file_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--specialist", action="store_true", help="Generate specialist pages")
    parser.add_argument("--subjects", action="store_true", help="Generate subject pages")
    parser.add_argument("--locations", action="store_true", help="Generate location pages")
    parser.add_argument("--blog", action="store_true", help="Generate blog posts")
    parser.add_argument("--levels", action="store_true", help="Generate level pages")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages generated")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.specialist:
        generate_specialist_pages(limit=args.limit)

    if args.subjects:
        generate_subject_pages(limit=args.limit)

    if args.locations:
        generate_location_pages(limit=args.limit)

    if args.blog:
        generate_blog_pages(limit=args.limit)

    if args.levels:
        generate_level_pages(limit=args.limit)

    if not args.specialist and not args.subjects and not args.locations and not args.blog and not args.levels:
        parser.print_help()


if __name__ == "__main__":
    main()