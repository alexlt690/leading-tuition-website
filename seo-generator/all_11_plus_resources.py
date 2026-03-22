import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urlparse

# ====================== CONFIG ======================
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# All listing pages (Pi + new sites)
pages = [
    # === PI ACADEMY (unchanged) ===
    ("https://piacademy.co.uk/pre-11-plus-exam-papers/7-plus-solved-past-papers/", "Pre 11 Plus"),
    ("https://piacademy.co.uk/pre-11-plus-exam-papers/pre-11-plus-past-papers-answers/", "Pre 11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-maths-past-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-english-past-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-vr-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/11-plus-nvr-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/11-plus-exam-papers/creative-writings-papers-answers/", "11 Plus"),
    ("https://piacademy.co.uk/13-plus-exam-papers/13-plus-maths-past-papers-answers/", "13 Plus"),
    ("https://piacademy.co.uk/13-plus-exam-papers/13-plus-english-past-papers-answers/", "13 Plus"),
    ("https://piacademy.co.uk/13-plus-exam-papers/13-plus-biology-past-papers-answers/", "13 Plus"),

    # === NEW SITES (added today) ===
    ("https://www.11plusguide.com/11-plus-papers-books/free-11-plus-papers/free-sample-11-plus-independent-school-papers/",
     "11 Plus"),
    ("https://elevenaid.co.uk/independent-schools-sample-papers/", "11 Plus"),
    ("https://creativehare.co.uk/free-11-plus-past-english-papers/", "11 Plus"),
]

papers = []

for url, category in pages:
    domain = urlparse(url).netloc.replace("www.", "")
    print(f"Scraping: {domain} → {category}")

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"  → Skipped (status {r.status_code})")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # === PI ACADEMY: table parser (unchanged) ===
        if "piacademy.co.uk" in url:
            for table in soup.find_all("table"):
                for row in table.find_all("tr")[1:]:
                    tds = row.find_all("td")
                    if len(tds) < 3: continue
                    name = tds[1].get_text(strip=True)
                    link = tds[2].find("a", href=True)["href"] if tds[2].find("a") else ""
                    if link.endswith(".pdf") and "media.piacademy.co.uk" in link:
                        papers.append((category, f"PiAcademy - {name}", link))

        # === NEW SITES: general PDF link extractor ===
        else:
            for a in soup.find_all("a", href=True):
                link = a["href"]
                if link.endswith(".pdf") and link.startswith("http"):
                    # Clean name
                    raw_name = a.get_text(strip=True)
                    if not raw_name:
                        raw_name = link.split("/")[-1].replace(".pdf", "").replace("-", " ").title()
                    name = f"{domain.title().replace('Co.Uk', '').replace('Com', '')} - {raw_name}"

                    papers.append((category, name, link))

    except Exception as e:
        print(f"  → Error: {e}")

    time.sleep(1.3)  # polite delay

# ====================== DEDUPLICATE & SORT ======================
# Remove exact duplicates (same category + name + link)
papers = list(dict.fromkeys(papers))

# Sort: Category → Site → Name
papers.sort(key=lambda x: (x[0], x[1]))

# ====================== SAVE CSV ======================
with open("all_11plus_public_past_papers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Category", "Name", "Link"])
    writer.writerows(papers)

print(f"\n✅ DONE! {len(papers)} papers saved to 'all_11plus_public_past_papers.csv'")
print("Columns: Category, Name (with site prefix), Link")
print("Duplicates automatically removed.")