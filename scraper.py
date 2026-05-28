#!/usr/bin/env python3
"""
MSME Samadhaan Portal Delayed Payments Scraper
----------------------------------------------
A robust Python CLI tool designed to scrape, extract, and structure real-time 
delayed payment and litigation data from the official government MSME Samadhaan portal.

Author: Alfred (HQbot)
License: MIT
"""

import os
import sys
import argparse
import json
import csv
import urllib3
import requests
from bs4 import BeautifulSoup

# Disable SSL verification warnings for government domains
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://samadhaan.msme.gov.in"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text):
    """Clean dirty web text, carriage returns, and extra whitespace."""
    if not text:
        return ""
    return " ".join(text.replace("\r", " ").replace("\n", " ").split()).strip()

def split_count_amount(val_str):
    """
    Splits a cell containing both a count and one or more amounts.
    For example:
      '1741 689.45' -> count=1741, amount1=689.45, amount2=0.0
      '390 282.22 80.67' -> count=390, amount1=282.22, amount2=80.67
    """
    parts = val_str.split()
    if not parts:
        return 0, 0.0, 0.0
    
    count = int(parts[0]) if parts[0].isdigit() else 0
    amounts = []
    for p in parts[1:]:
        try:
            amounts.append(float(p))
        except ValueError:
            amounts.append(0.0)
            
    amt1 = amounts[0] if len(amounts) > 0 else 0.0
    amt2 = amounts[1] if len(amounts) > 1 else 0.0
    return count, amt1, amt2

def fetch_category_amount_report():
    """Scrape the All Category Amount Report (MSEFC_ReportAllAmount.aspx)"""
    url = f"{BASE_URL}/mymsme/msefc/MSEFC_ReportAllAmount.aspx"
    print(f"[*] Accessing Category Amount Audit Registry: {url}")
    
    r = requests.get(url, headers=HEADERS, verify=False, timeout=20)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', id='example11')
    if not table:
        raise ValueError("Error: example11 statistics table not found on page.")
        
    rows = table.find_all('tr')
    # Actual data rows start from index 4
    data_rows = rows[4:]
    
    records = []
    for row in data_rows:
        cells = [clean_text(c.get_text()) for c in row.find_all(['td', 'th'])]
        if not cells or len(cells) < 8:
            continue
            
        s_no = cells[0]
        category = cells[1]
        
        # Skip grand totals
        if "grand total" in category.lower() or not s_no:
            continue
            
        filed_cnt, filed_amt, _ = split_count_amount(cells[2])
        rej_cnt, rej_amt, _ = split_count_amount(cells[3])
        settled_cnt, settled_amt, _ = split_count_amount(cells[4])
        consider_cnt, consider_amt, _ = split_count_amount(cells[5])
        action_cnt, action_amt, _ = split_count_amount(cells[6])
        disposed_cnt, disposed_amt, settled_by_council_amt = split_count_amount(cells[7])
        cases_cnt, cases_amt, _ = split_count_amount(cells[8])
        
        record = {
            "s_no": s_no,
            "category": category,
            "filed_count": filed_cnt,
            "filed_amount_cr": filed_amt,
            "rejected_count": rej_cnt,
            "rejected_amount_cr": rej_amt,
            "mutually_settled_count": settled_cnt,
            "mutually_settled_amount_cr": settled_amt,
            "under_consideration_count": consider_cnt,
            "under_consideration_amount_cr": consider_amt,
            "actionable_count": action_cnt,
            "actionable_amount_cr": action_amt,
            "disposed_count": disposed_cnt,
            "disposed_amount_cr": disposed_amt,
            "disposed_settled_by_council_amount_cr": settled_by_council_amt,
            "converted_cases_count": cases_cnt,
            "converted_cases_amount_cr": cases_amt
        }
        records.append(record)
        
    return records

def fetch_pending_amount_report():
    """Scrape the All Category Pending Amount Report (MSEFC_ReportAllPendingAmount.aspx)"""
    url = f"{BASE_URL}/mymsme/msefc/MSEFC_ReportAllPendingAmount.aspx"
    print(f"[*] Accessing Pending Exposure Registry: {url}")
    
    r = requests.get(url, headers=HEADERS, verify=False, timeout=20)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', id='tableid')
    if not table:
        raise ValueError("Error: tableid statistics table not found on page.")
        
    rows = table.find_all('tr')
    # Actual data starts from row 2
    data_rows = rows[2:]
    
    records = []
    for row in data_rows:
        cells = [clean_text(c.get_text()) for c in row.find_all(['td', 'th'])]
        if not cells or len(cells) < 6:
            continue
            
        s_no = cells[0]
        category = cells[1]
        
        if "grand total" in category.lower() or not s_no:
            continue
            
        filed_cnt, filed_amt, _ = split_count_amount(cells[2])
        pend_app_cnt, pend_app_amt, _ = split_count_amount(cells[3])
        pend_case_cnt, pend_case_amt, _ = split_count_amount(cells[4])
        total_pend_cnt, total_pend_amt, _ = split_count_amount(cells[5])
        
        record = {
            "s_no": s_no,
            "category": category,
            "filed_count": filed_cnt,
            "filed_amount_cr": filed_amt,
            "pending_applications_count": pend_app_cnt,
            "pending_applications_amount_cr": pend_app_amt,
            "pending_cases_count": pend_case_cnt,
            "pending_cases_amount_cr": pend_case_amt,
            "total_pending_count": total_pend_cnt,
            "total_pending_amount_cr": total_pend_amt
        }
        records.append(record)
        
    return records

def fetch_ministry_report():
    """Scrape the Central Ministry delayed payment reports (MSEFC_ReportWelcome2.aspx)"""
    url = f"{BASE_URL}/MyMsme/MSEFC/MSEFC_ReportWelcome2.aspx?BuyerCat=5&Category=Central Ministries&InnerRpt=1"
    print(f"[*] Fetching Central Ministries Delayed Payments: {url}")
    
    r = requests.get(url, headers=HEADERS, verify=False, timeout=20)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', id='example1')
    if not table:
        raise ValueError("Error: example1 respondent table not found on page.")
        
    rows = table.find_all('tr')
    data_rows = rows[1:] # Index 0 is the headers
    
    records = []
    for row in data_rows:
        cells = [clean_text(c.get_text()) for c in row.find_all(['td', 'th'])]
        if not cells or len(cells) < 11:
            continue
            
        s_no = cells[0]
        ministry_name = cells[1]
        
        if "grand total" in ministry_name.lower() or not s_no:
            continue
            
        record = {
            "s_no": s_no,
            "ministry": ministry_name,
            "applications_filed": int(cells[2]) if cells[2].isdigit() else 0,
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
        
    return records

def save_data(data, filepath, out_format):
    """Save the structured data into CSV or JSON format."""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    
    if out_format.lower() == "json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] Structured JSON successfully exported to: {filepath}")
    else:
        if not data:
            print("[-] No records found to export to CSV.")
            return
            
        keys = data[0].keys()
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"[+] Structured CSV successfully exported to: {filepath}")

def print_text_table(records, title):
    """Format and print structured records in a beautiful, solid-framed text list."""
    if not records:
        print("[-] No records match the query.")
        return
        
    print(f"\n=== {title.upper()} ===")
    print("-" * 115)
    
    sample = records[0]
    if "ministry" in sample:
        header_line = f"{'S.No':<6} | {'Ministry Name':<45} | {'Filed':<8} | {'Cases':<8} | {'Settled':<8} | {'Disputes':<10}"
        print(header_line)
        print("-" * 115)
        for r in records:
            print(f"{r['s_no']:<6} | {r['ministry'][:45]:<45} | {r['applications_filed']:<8} | {r['converted_into_cases']:<8} | {r['mutually_settled']:<8} | {r['total_active_disputes']:<10}")
    elif "total_pending_amount_cr" in sample:
        header_line = f"{'S.No':<6} | {'Respondent Category':<35} | {'Filed Count':<12} | {'Filed (Cr)':<15} | {'Pend Count':<12} | {'Pend (Cr)':<15}"
        print(header_line)
        print("-" * 115)
        for r in records:
            print(f"{r['s_no']:<6} | {r['category'][:35]:<35} | {r['filed_count']:<12} | {r['filed_amount_cr']:<15,.2f} | {r['total_pending_count']:<12} | {r['total_pending_amount_cr']:<15,.2f}")
    else:
        header_line = f"{'S.No':<6} | {'Respondent Category':<35} | {'Filed Count':<12} | {'Filed (Cr)':<15} | {'Settled Count':<12} | {'Settled (Cr)':<15}"
        print(header_line)
        print("-" * 115)
        for r in records:
            print(f"{r['s_no']:<6} | {r['category'][:35]:<35} | {r['filed_count']:<12} | {r['filed_amount_cr']:<15,.2f} | {r['mutually_settled_count']:<12} | {r['mutually_settled_amount_cr']:<15,.2f}")
    print("-" * 115)

def main():
    parser = argparse.ArgumentParser(description="Official MSME Samadhaan Delayed Payments Index Scraper Utility")
    parser.add_argument("--report", choices=["category", "pending", "ministry"], default="category",
                        help="Select index report category: 'category' (default amount statistics), 'pending' (pending exposure), 'ministry' (detailed central ministries)")
    parser.add_argument("--format", choices=["json", "csv"], default="json",
                        help="Output storage structure format (default: 'json')")
    parser.add_argument("--output", type=str, default="output",
                        help="Output directory path (default: 'output')")
    parser.add_argument("--search", type=str, default="",
                        help="Filter and display rows matching a keyword (e.g. 'railway' or 'proprietorship')")
    
    args = parser.parse_args()
    
    try:
        print("[*] Initializing MSME Samadhaan Scraper Engine...")
        
        # Dispatch fetch operations based on choice
        if args.report == "category":
            data = fetch_category_amount_report()
            title = "All Respondent Category Cumulative Amount Audit"
            filename = "msme_category_amounts"
        elif args.report == "pending":
            data = fetch_pending_amount_report()
            title = "Respondent Pending Exposure Summary"
            filename = "msme_pending_amounts"
        else:
            data = fetch_ministry_report()
            title = "Central Ministries Delayed Payment Audited Ledger"
            filename = "msme_ministry_disputes"
            
        # Filter matching rows if search parameter provided
        if args.search:
            search_key = args.search.lower()
            if args.report == "ministry":
                filtered_data = [r for r in data if search_key in r["ministry"].lower()]
            else:
                filtered_data = [r for r in data if search_key in r["category"].lower()]
            print_text_table(filtered_data, f"Query Filter: '{args.search}' on {title}")
        else:
            print_text_table(data[:15], f"{title} (Top 15 Rows Displayed)")
            if len(data) > 15:
                print(f"  ... and {len(data) - 15} more rows.")
                
        # Exporting structured files
        out_filepath = os.path.join(args.output, f"{filename}.{args.format}")
        save_data(data, out_filepath, args.format)
        
        print("\n[+] Verification: Scraper completed audit cycle successfully.")
        
    except Exception as e:
        print(f"\n[-] Execution Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
