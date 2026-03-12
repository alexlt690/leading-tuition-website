import csv
import os
import anthropic
from pathlib import Path
from templates import page_template

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

OUTPUT_DIR = Path("output")


def load_csv(filename):
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_ai_paragraph(topic):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        temperature=0.5,
        messages=[
            {
                "role": "user",
                "content": f"Write one clear, parent-facing paragraph for a UK tutoring website page about {topic}. Keep it helpful, specific, and concise."
            }
        ]
    )
    return response.content[0].text


def generate_keyword_pages():
    keywords = load_csv("keywords.csv")

    for row in keywords:
        slug = row["page_slug"]
        title = row["title"]
        topic = row["keyword"]

        paragraph = generate_ai_paragraph(topic)

        content = f"<p>{paragraph}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")


def generate_subject_pages():
    subjects = load_csv("subjects.csv")

    for row in subjects:
        subject = row["subject"]
        slug = subject.lower().replace(" ", "-")

        title = f"{subject} Tutor"

        paragraph = generate_ai_paragraph(f"{subject} tutoring")

        content = f"<p>{paragraph}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}-tutor.html"
        file_path.write_text(html, encoding="utf-8")


def generate_location_pages():
    locations = load_csv("locations.csv")

    for row in locations:
        city = row["city"]
        slug = city.lower().replace(" ", "-")

        title = f"Private Tutor {city}"

        paragraph = generate_ai_paragraph(f"private tutoring in {city}")

        content = f"<p>{paragraph}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")


def generate_blog_pages():
    posts = load_csv("blog_topics.csv")

    for row in posts:
        title = row["title"]
        topic = row["keyword"]

        slug = title.lower().replace(" ", "-").replace("?", "").replace(":", "")

        paragraph = generate_ai_paragraph(topic)

        content = f"<p>{paragraph}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")


def generate_level_pages():
    levels = load_csv("levels.csv")

    for row in levels:
        level = row["level"]
        slug = level.lower().replace("+", "plus").replace(" ", "-")

        title = f"{level} Tuition"

        paragraph = generate_ai_paragraph(f"{level} tuition")

        content = f"<p>{paragraph}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}-tuition.html"
        file_path.write_text(html, encoding="utf-8")


def generate_specialist_pages():
    pages = load_csv("specialist_pages.csv")

    for row in pages:
        slug = row["slug"]
        title = row["title"]
        keyword = row["keyword"]

        paragraph = generate_ai_paragraph(keyword)

        content = f"<p>{paragraph}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    keywords = load_csv("keywords.csv")
    row = keywords[0]

    slug = row["page_slug"]
    title = row["title"]
    topic = row["keyword"]

    paragraph = generate_ai_paragraph(topic)

    content = f"<p>{paragraph}</p>"
    html = page_template(title, content)

    file_path = OUTPUT_DIR / f"{slug}.html"
    file_path.write_text(html, encoding="utf-8")

    print(f"Generated test page: {file_path}")


if __name__ == "__main__":
    main()