import csv
from pathlib import Path
from templates import page_template

OUTPUT_DIR = Path("output")

def load_csv(filename):
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def generate_keyword_pages():
    keywords = load_csv("keywords.csv")
    for row in keywords:
        slug = row["page_slug"]
        title = row["title"]

        content = f"<p>Placeholder page for {row['keyword']}</p>"
        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")

def generate_subject_pages():
    subjects = load_csv("subjects.csv")
    for row in subjects:
        subject = row["subject"]
        slug = subject.lower().replace(" ", "-")

        title = f"{subject} Tutor"
        content = f"<p>Placeholder page for {subject} tutoring.</p>"

        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}-tutor.html"
        file_path.write_text(html, encoding="utf-8")

def generate_location_pages():
    locations = load_csv("locations.csv")
    for row in locations:
        city = row["city"]
        slug = city.lower().replace(" ", "-")

        title = f"Private Tutor {city}"
        content = f"<p>Placeholder page for tutoring in {city}.</p>"

        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
def generate_blog_pages():
    posts = load_csv("blog_topics.csv")
    for row in posts:
        title = row["title"]
        slug = title.lower().replace(" ", "-").replace("?", "").replace(":", "")

        content = f"<p>Placeholder blog post for {row['keyword']}.</p>"

        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")
def generate_level_pages():
    levels = load_csv("levels.csv")
    for row in levels:
        level = row["level"]
        slug = level.lower().replace("+", "plus").replace(" ", "-")

        title = f"{level} Tuition"
        content = f"<p>Placeholder page for {level} tuition.</p>"

        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}-tuition.html"
        file_path.write_text(html, encoding="utf-8")

def generate_specialist_pages():
    pages = load_csv("specialist_pages.csv")
    for row in pages:
        slug = row["slug"]
        title = row["title"]
        keyword = row["keyword"]

        content = f"<p>Placeholder specialist page for {keyword}.</p>"

        html = page_template(title, content)

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    generate_keyword_pages()
    generate_subject_pages()
    generate_location_pages()
    generate_blog_pages()
    generate_level_pages()
    generate_specialist_pages()
if __name__ == "__main__":
    main()