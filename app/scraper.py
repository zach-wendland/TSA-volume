import re
from datetime import datetime
from typing import List
import requests
from bs4 import BeautifulSoup
from .models import VolumeRow
from .settings import SCRAPE_URL

UA = "Mozilla/5.0 (compatible; TSA-Scraper/1.0; +https://example.invalid)"

DATE_FORMATS = [
    "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"
]

def _parse_date(text: str):
    t = re.sub(r"\s+", " ", text.strip())
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    return None

def _parse_int(text: str):
    if not text:
        return None
    t = text.strip()
    if t in ("-", "n/a", "N/A"):
        return None
    t = re.sub(r"[^\d-]", "", t)
    if not t:
        return None
    try:
        return int(t)
    except ValueError:
        return None

def fetch_html(url: str = SCRAPE_URL, timeout: int = 15) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r.text

def parse_volumes(html: str) -> List[VolumeRow]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    rows = table.find_all("tr")
    out: List[VolumeRow] = []
    for tr in rows[1:]:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        date_text = cells[0].get_text(strip=True)
        d = _parse_date(date_text)
        if not d:
            continue
        nums = []
        for i in range(1, len(cells)):
            nums.append(_parse_int(cells[i].get_text(strip=True)))
        while len(nums) < 3:
            nums.append(None)
        row = VolumeRow(
            date=d,
            current_year_volume=nums[0],
            previous_year_volume=nums[1],
            two_years_ago_volume=nums[2],
        )
        out.append(row)
    return out

def scrape() -> List[VolumeRow]:
    html = fetch_html()
    return parse_volumes(html)
