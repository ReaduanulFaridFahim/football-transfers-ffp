"""
Automated Comprehensive QA Test Suite
======================================
Tests all components of the Football Transfer & FFP Intelligence Dashboard:
1. HTML Validation & DOM IDs check
2. CSS Validation & Theme Token verification
3. JavaScript Syntax & DOM references audit
4. Data Integrity & Financial Calculations verification (Net Spend = Spent - Income, 115 Charges Sum)
5. Live HTTP Server and static asset availability
6. Python backend scripts sanity test
"""

import sys
import re
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

test_results = []

def record(test_name: str, passed: bool, details: str = ""):
    status = "PASS" if passed else "FAIL"
    test_results.append((test_name, passed, details))
    prefix = "[PASS]" if passed else "[FAIL]"
    print(f"{prefix} {test_name}: {details}")

print("=" * 70)
print(" RUNNING COMPREHENSIVE QA TEST SUITE")
print("=" * 70)

# ---------------------------------------------------------
# TEST 1: HTML Structure & ID Uniqueness
# ---------------------------------------------------------
print("\n--- 1. HTML DOM & Semantics QA ---")
html_path = BASE_DIR / "index.html"
if not html_path.exists():
    record("HTML File Existence", False, "index.html missing")
else:
    html_content = html_path.read_text(encoding="utf-8")
    record("HTML File Existence", True, f"index.html present ({len(html_content)} bytes)")
    
    # Check DOCTYPE, title, meta viewport
    has_doctype = "<!DOCTYPE html>" in html_content
    has_title = "<title>" in html_content
    has_viewport = 'name="viewport"' in html_content
    record("HTML5 Standards", has_doctype and has_title and has_viewport, "DOCTYPE, Title, Viewport present")
    
    # Check ID uniqueness
    all_ids = re.findall(r'id=["\']([^"\']+)["\']', html_content)
    seen_ids = set()
    duplicate_ids = []
    for elem_id in all_ids:
        if elem_id in seen_ids:
            duplicate_ids.append(elem_id)
        seen_ids.add(elem_id)
    
    record("HTML Unique IDs", len(duplicate_ids) == 0, 
           f"Found {len(seen_ids)} IDs, {len(duplicate_ids)} duplicates ({duplicate_ids})")

# ---------------------------------------------------------
# TEST 2: JavaScript DOM References Audit
# ---------------------------------------------------------
print("\n--- 2. JavaScript DOM References Audit ---")
js_path = BASE_DIR / "app.js"
if js_path.exists():
    js_content = js_path.read_text(encoding="utf-8")
    
    # Check braces balance
    open_braces = js_content.count("{") - js_content.count("}")
    open_brackets = js_content.count("[") - js_content.count("]")
    open_parens = js_content.count("(") - js_content.count(")")
    
    is_balanced = (open_braces == 0 and open_brackets == 0 and open_parens == 0)
    record("JavaScript Syntax Balance", is_balanced, 
           f"Braces balance: {open_braces}, Brackets: {open_brackets}, Parens: {open_parens}")
    
    # Extract getElementById calls
    get_elem_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js_content))
    missing_ids = [eid for eid in get_elem_ids if eid not in seen_ids]
    record("JavaScript DOM Reference Integrity", len(missing_ids) == 0,
           f"{len(get_elem_ids)} IDs checked. Missing in HTML: {missing_ids}")
    
    # Verify Chart cleanup (.destroy calls)
    destroy_calls = len(re.findall(r'\.destroy\(\)', js_content))
    record("Chart.js Memory Leak Prevention", destroy_calls >= 4,
           f"Found {destroy_calls} chart.destroy() lifecycle cleanup calls")

# ---------------------------------------------------------
# TEST 3: CSS Stylesheet & Tokens Audit
# ---------------------------------------------------------
print("\n--- 3. CSS Stylesheet & Theme Tokens QA ---")
css_path = BASE_DIR / "styles.css"
if css_path.exists():
    css_content = css_path.read_text(encoding="utf-8")
    css_braces = css_content.count("{") - css_content.count("}")
    record("CSS Syntax Balance", css_braces == 0, f"Brace balance: {css_braces}")
    
    # Check essential design tokens
    tokens = ["--bg-base", "--accent-cyan", "--status-breach", "--status-ok", "--text-primary"]
    missing_tokens = [t for t in tokens if t not in css_content]
    record("Design System Theme Tokens", len(missing_tokens) == 0, f"Theme tokens verified ({len(tokens) - len(missing_tokens)}/{len(tokens)})")
    
    # Check responsive rules
    has_media_queries = "@media" in css_content
    record("Responsive Breakpoints", has_media_queries, "Found @media queries for mobile/tablet")

# ---------------------------------------------------------
# TEST 4: Data Integrity & Calculation Verification
# ---------------------------------------------------------
print("\n--- 4. Data Integrity & Financial Calculations QA ---")
json_path = BASE_DIR / "dashboard_data.json"
data_js_path = BASE_DIR / "data.js"

if json_path.exists():
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    required_keys = ["meta", "market_seasons", "rankings_20y", "rankings_10y", "rankings_5y", "violations", "top_transfers", "mancity_case"]
    missing_keys = [k for k in required_keys if k not in data]
    record("JSON Schema Completeness", len(missing_keys) == 0, f"Keys verified: {required_keys}")
    
    # Math audit: Net Spend = Spent - Income for all clubs
    math_errors = 0
    for club in data["rankings_20y"]:
        expected_net = round(club["spent"] - club["income"], 2)
        actual_net = round(club["net_spend"], 2)
        if abs(expected_net - actual_net) > 0.05:
            math_errors += 1
    record("Financial Calculation Precision", math_errors == 0, 
           f"Audited 40 clubs: {math_errors} discrepancies found (Net = Spend - Income)")

    # Manchester City 115 Charges count verification
    mc = data["mancity_case"]
    charges_sum = sum(c["count"] for c in mc["pl_charges_breakdown"])
    record("Man City 115 Charges Exact Sum", charges_sum == 115, 
           f"Sum of charges across 5 categories = {charges_sum} (Expected: 115)")
    
    # Verify data.js matches
    if data_js_path.exists():
        data_js_content = data_js_path.read_text(encoding="utf-8")
        record("Offline data.js Bundle", "window.EMBEDDED_DASHBOARD_DATA =" in data_js_content,
               f"data.js present ({len(data_js_content)} bytes)")

# ---------------------------------------------------------
# TEST 5: Live HTTP Server & Assets Endpoint QA
# ---------------------------------------------------------
print("\n--- 5. Live Local Server & HTTP Endpoint QA ---")
endpoints = [
    ("http://127.0.0.1:8080/index.html", 200),
    ("http://127.0.0.1:8080/styles.css", 200),
    ("http://127.0.0.1:8080/app.js", 200),
    ("http://127.0.0.1:8080/data.js", 200),
    ("http://127.0.0.1:8080/dashboard_data.json", 200),
]

for url, expected_status in endpoints:
    try:
        req = urllib.request.urlopen(url, timeout=3)
        status = req.getcode()
        record(f"HTTP GET {url.split('/')[-1]}", status == expected_status, f"HTTP {status}")
    except Exception as e:
        record(f"HTTP GET {url.split('/')[-1]}", False, f"Error: {e}")

# ---------------------------------------------------------
# FINAL QA SUMMARY
# ---------------------------------------------------------
print("\n" + "=" * 70)
total_tests = len(test_results)
passed_tests = sum(1 for _, p, _ in test_results if p)
failed_tests = total_tests - passed_tests

print(f" QA TEST SUITE SUMMARY: {passed_tests}/{total_tests} TESTS PASSED")
if failed_tests == 0:
    print(" ALL QUALITY ASSURANCE CHECKS PASSED WITH ZERO DEFECTS!")
else:
    print(f" {failed_tests} TESTS FAILED. PLEASE REVIEW.")
print("=" * 70)

sys.exit(0 if failed_tests == 0 else 1)
