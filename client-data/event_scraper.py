import json, re, time, requests
from bs4 import BeautifulSoup

BASE = "https://thebazaar.wiki.gg"

def clean(text):
    # remove inline image placeholders like "Heal.png20"
    return re.sub(r'\b\w+\.png', '', text).replace('  ', ' ').strip()

def event_links():
    cat = requests.get(f"{BASE}/wiki/Category:Event").text
    soup = BeautifulSoup(cat, "html.parser")
    links = [a['href'] for a in soup.select('#mw-pages a[href^="/wiki/"]')]
    # de-duplicate & keep only direct event pages
    return [BASE + l for l in dict.fromkeys(links)]

def scrape_event(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    name = soup.select_one('#firstHeading').text.strip()
    # Function list
    func = soup.find('span', id='Function')
    if func:
        lis = func.find_parent().find_next('ul')
        options = [clean(li.get_text(" ", strip=True)) for li in lis.select('li')]
    else:
        # fall back to Description
        desc = soup.find('span', id='Description')
        options = [clean(desc.find_parent().find_next('p').text)]
    return {"name": name, "options": options}

all_events = [scrape_event(url) for url in event_links()]
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(all_events, f, ensure_ascii=False, indent=4)
print("Wrote", len(all_events), "events to events.json")