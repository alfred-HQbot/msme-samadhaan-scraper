# MSME Samadhaan Portal Delayed Payments Scraper

A robust, production-grade Python CLI scraper designed to extract, structure, and query real-time delayed payment application and litigation data from the official government **MSME Samadhaan** portal.

This utility bypasses stateful forms and extracts public, un-captcha'd delayed payment datasets, structured by both **Application Count** and **Amount in Rs. Crore**, and exports them cleanly to JSON or CSV.

---

## Features

- **Double-Value Parsing:** Cleans and splits merged government table cells containing both count values and monetary volumes (e.g. separates `'1741 689.45'` into `1741` applications and `₹689.45 Crores`).
- **Multiple Audit Indices:**
  - `category`: Audit amount payable/disposed/settled across Central PSU, Proprietorships, etc.
  - `pending`: Pending applications/cases by respondent categories.
  - `ministry`: Active delayed payment cases specifically filed against Central Ministries.
- **In-Memory Querying:** Instantly search and filter any organization or ministry across scraped results.
- **Flexible Exports:** Supports clean outputs to structured **JSON** or **CSV** formats.
- **SSL Bypass:** Gracefully handles government domain certificate discrepancies automatically.

---

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <repo-url>
   cd msme-samadhaan-scraper
   ```

2. **Setup Virtual Environment & Install Dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## CLI Usage

### 1. Scrape All Category Amounts (Default)
Extracts cumulative filed, rejected, mutually settled, and converted cases by respondent category:
```bash
./scraper.py --report category --format json
```

### 2. Scrape Pending Exposures
Scrapes total pending applications, cases, and amounts currently outstanding across sectors:
```bash
./scraper.py --report pending --format csv
```

### 3. Audit Central Ministries
Scrapes individual active disputes and filings against all 30+ Central Indian Ministries:
```bash
./scraper.py --report ministry --format json
```

### 4. Search & Filter Matches
Instantly filter and display rows matching a specific search keyword directly on the console:
```bash
./scraper.py --report ministry --search railways
```

---

## Example Output Structure (Category Amounts)

```json
[
    {
        "s_no": "1",
        "category": "Central Ministries",
        "filed_count": 1741,
        "filed_amount_cr": 689.45,
        "rejected_count": 442,
        "rejected_amount_cr": 130.1,
        "mutually_settled_count": 380,
        "mutually_settled_amount_cr": 36.58,
        "under_consideration_count": 307,
        "under_consideration_amount_cr": 123.99,
        "actionable_count": 0,
        "actionable_amount_cr": 0.0,
        "disposed_count": 390,
        "disposed_amount_cr": 282.22,
        "disposed_settled_by_council_amount_cr": 80.67,
        "converted_cases_count": 222,
        "converted_cases_amount_cr": 116.56
    }
]
```

---

## Disclaimer
This tool parses publicly available data published by the Ministry of Micro, Small and Medium Enterprises. It is intended strictly for research and credit risk analysis purposes.
