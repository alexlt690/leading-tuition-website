import csv
import os
import argparse
import anthropic
from pathlib import Path
from templates import page_template

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--specialist", action="store_true", help="Generate specialist pages")
    parser.add_argument("--subjects", action="store_true", help="Generate subject pages")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages generated")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.specialist:
        generate_specialist_pages(limit=args.limit)

    if args.subjects:
        generate_subject_pages(limit=args.limit)

    if not args.specialist and not args.subjects:
        parser.print_help()


if __name__ == "__main__":
    main()