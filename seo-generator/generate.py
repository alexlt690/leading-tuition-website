import csv
from pathlib import Path

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

        html = f"""
        <html>
        <head>
            <title>{title}</title>
        </head>
        <body>
            <h1>{title}</h1>
            <p>Placeholder page for {row["keyword"]}</p>
        </body>
        </html>
        """

        file_path = OUTPUT_DIR / f"{slug}.html"
        file_path.write_text(html, encoding="utf-8")

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    generate_keyword_pages()

if __name__ == "__main__":
    main()
