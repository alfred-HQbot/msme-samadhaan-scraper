#!/usr/bin/env python3
"""
MSME Samadhaan Master Disputes Scraper (High-Value Index)
--------------------------------------
Scrapes detailed delayed payment dispute rows for thousands of major Indian corporate buyers,
public sector undertakings (PSUs), government departments, and ministries.
Compiles them into a single master search database index.

Author: Alfred (HQbot)
License: MIT
"""

import os
import json
import urllib3
import requests
from bs4 import BeautifulSoup

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://samadhaan.msme.gov.in"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CATEGORIES_TO_SCRAPE = [
    {"bcat": 5, "cat_name": "Central Ministries"},
    {"bcat": 9, "cat_name": "Central Department"},
    {"bcat": 1, "cat_name": "Central PSU"},
    {"bcat": 10, "cat_name": "Railway Zone"},
    {"bcat": 11, "cat_name": "Railway Division"},
    {"bcat": 12, "cat_name": "Ordnance Factory"},
    {"bcat": 15, "cat_name": "Statutory Bodies"}
]

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.replace("\r", " ").replace("\n", " ").split()).strip()

def scrape_category(bcat, cat_name):
    url = f"{BASE_URL}/MyMsme/MSEFC/MSEFC_ReportWelcome2.aspx?BuyerCat={bcat}&Category={cat_name}&InnerRpt=1"
    print(f"[*] Scraping Category '{cat_name}' (BuyerCat={bcat})...")
    
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=12)
        r.raise_for_status()
    except Exception as e:
        print(f"[-] Network error scraping {cat_name}: {e}")
        return []
        
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', id='example1')
    if not table:
        print(f"[-] Table 'example1' not found for category {cat_name}")
        return []
        
    rows = table.find_all('tr')
    data_rows = rows[1:] # Index 0 is the headers
    
    records = []
    for row in data_rows:
        cells = [clean_text(c.get_text()) for c in row.find_all(['td', 'th'])]
        if not cells or len(cells) < 11:
            continue
            
        s_no = cells[0]
        entity_name = cells[1]
        
        # Skip grand totals
        if "grand total" in entity_name.lower() or not s_no:
            continue
            
        record = {
            "entity": entity_name,
            "category": cat_name,
            "filed_applications": int(cells[2]) if cells[2].isdigit() else 0,
            "visible_to_council_15d": int(cells[3]) if cells[3].isdigit() else 0,
            "converted_into_cases": int(cells[4]) if cells[4].isdigit() else 0,
            "disposed_by_council": int(cells[5]) if cells[5].isdigit() else 0,
            "rejected_by_council": int(cells[6]) if cells[6].isdigit() else 0,
            "pending": int(cells[7]) if cells[7].isdigit() else 0,
            "mutually_settled": int(cells[8]) if cells[8].isdigit() else 0,
            "responded_by_govt_agency": int(cells[9]) if cells[9].isdigit() else 0,
            "total_active_disputes": int(cells[10]) if cells[10].isdigit() else 0
        }
        records.append(record)
        
    print(f"[+] Scraped {len(records)} active corporate/department entities for {cat_name}")
    return records

def main():
    master_records = []
    for cat in CATEGORIES_TO_SCRAPE:
        records = scrape_category(cat["bcat"], cat["cat_name"])
        master_records.extend(records)
        
    print(f"\n[+] Scrape complete. Compiled {len(master_records)} total disputable entities.")
    
    out_dir = "data"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "msme_master_disputes.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(master_records, f, indent=4, ensure_ascii=False)
        
    print(f"[+] Master Search database successfully compiled & saved to: {out_path}")

if __name__ == "__main__":
    main()
