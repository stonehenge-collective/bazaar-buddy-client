import json, re, time, requests
from bs4 import BeautifulSoup

BASE = "https://thebazaar.wiki.gg"

def clean(text: str) -> str:
    """Strip inline image placeholders like “Heal.png20”, collapse doublespaces."""
    return re.sub(r'\b\w+\.png', '', text).replace('  ', ' ').strip()

def event_links() -> list[str]:
    """
    Return a list of full event‑page URLs.

    Instead of reading the #mw‑pages “pages in category” box (which is incomplete),
    we parse the sortable wikitable at the top of the page.  Every row’s first
    <td> holds a single <a> whose href is the page we want.
    """
    html  = requests.get(f"{BASE}/wiki/Category:Event").text
    soup  = BeautifulSoup(html, "html.parser")

    table = soup.select_one("table.wikitable.sortable")
    if not table:                       # Fallback: old behaviour
        print("⚠️  Table not found – falling back to #mw-pages list")
        return [
            BASE + a["href"]
            for a in soup.select('#mw-pages a[href^="/wiki/"]')
        ]

    links = []
    for tr in table.select("tr")[1:]:   # skip header row
        a = tr.select_one("td a[href^='/wiki/']")
        if a:
            links.append(BASE + a["href"])

    # Remove dups while preserving order
    return list(dict.fromkeys(links))

def scrape_event(url: str) -> dict:
    print(url)
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    name = soup.select_one('#firstHeading').text.strip()

    func = soup.find('span', id='Function')
    if func:
        lis     = func.find_parent().find_next('ul')
        options = [clean(li.get_text(" ", strip=True)) for li in lis.select('li')]
    else:
        desc    = soup.find('span', id='Description')
        options = [clean(desc.find_parent().find_next('p').text)]

    return {"name": name, "options": options}
# ---------- main ----------
all_events = [scrape_event(url) for url in event_links()]
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(all_events, f, ensure_ascii=False, indent=4)
print("Wrote", len(all_events), "events to events.json")
