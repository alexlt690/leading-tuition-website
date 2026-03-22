import requests
from bs4 import BeautifulSoup
import csv
import time

# Mapping: URL pattern → Category
category_map = [
    ("pre-11-plus-exam-papers", "Pre 11 Plus"),
    ("11-plus-exam-papers", "11 Plus"),
    ("13-plus-exam-papers", "13 Plus"),
]

# Only public listing pages we want (GCSE removed)
pages = [
    # Pre 11+
    ("https://piacademy.co.uk/pre-11-plus-exam-papers/7-plus-solved-past-papers/", "Pre 11 Plus"),
    ("https://piacademy.co.uk/pre-11-plus-exam-papers/pre-11-plus-past-papers-answers/", "Pre 11 Plus"),

    # 11+
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-maths-past-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-english-past-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-vr-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-nvr-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/creative-writings-papers-answers/", "11 Plus"),

    # 13+
    ("https://piacademy.co.uk/13-plus-exam-papers/13-plus-maths-past-papers-answers/", "13 Plus"),
    ("https://piacademy.co.uk/13-plus-exam-papers/13-plus-english-past-papers-answers/", "13 Plus"),
    ("https://piacademy.co.uk/13-plus-exam-papers/13-plus-biology-past-papers-answers/", "13 Plus"),
]

papers = []
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for url, explicit_category in pages:
    print(f"Scraping: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code != 200:
            print(f"  → Skipped (status {r.status_code})")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # skip header
                tds = row.find_all("td")
                if len(tds) < 3:
                    continue

                name = tds[1].get_text(strip=True)

                q_td = tds[2]
                a_tag = q_td.find("a", href=True)
                if not a_tag:
                    continue

                link = a_tag["href"]
                if not (link.endswith(".pdf") and link.startswith("https://media.piacademy.co.uk/")):
                    continue

                # Use the explicit category passed with the URL
                category = explicit_category

                papers.append((category, name, link))

    except Exception as e:
        print(f"  → Error: {e}")

    time.sleep(1.2)  # polite delay

# Deduplicate by (category, name, link) and sort
papers = list(dict.fromkeys(papers))  # removes exact duplicate rows
papers.sort(key=lambda x: (x[0], x[1]))  # sort by category → name

# Write CSV
with open("piacademy_public_past_papers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Category", "Name", "Link"])
    writer.writerows(papers)

print(f"\nDone! {len(papers)} public past papers saved to 'piacademy_public_past_papers.csv'")
print("Columns: Category, Name, Link")