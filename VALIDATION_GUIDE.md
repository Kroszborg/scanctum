# Scanctum Validation Guide

## Overview

This guide explains how to use Scanctum's validation features to:
1. Measure detection accuracy (precision, recall, F1)
2. Compare against OWASP ZAP
3. Manually verify findings
4. Understand finding categories

---

## Quick Start

### Run Validation Against DVWA

```bash
# 1. Start DVWA
docker run --rm -it -p 8080:80 eikowitch/dvwa:latest

# 2. Login to DVWA and set security to "Low"
# Go to: http://localhost:8080
# Login: admin / password
# DVWA Security → Low → Submit

# 3. Run validation scan
cd backend
python -m app.scanner.validate --target dvwa --url http://localhost:8080

# 4. View report
cat validation_report.txt
```

### Expected Output

```
============================================================
SCANCTUM VALIDATION REPORT
============================================================

Target: DVWA
----------------------------------------
  True Positives:  6
  False Positives: 1
  False Negatives: 2
  Precision:       85.7%
  Recall:          75.0%
  F1 Score:        80.0%

============================================================
```

---

## Finding Categories

All findings are now categorized:

| Category | Description | Action |
|----------|-------------|--------|
| **EXPLOITABLE** | Confirmed exploitation possible | Fix immediately |
| **MISCONFIGURATION** | Security hardening recommended | Schedule fix |
| **INFORMATIONAL** | Awareness only, not a vulnerability | Review if time |

### Examples

**EXPLOITABLE:**
- SQL Injection (error-based, confirmed)
- XSS (reflected, unencoded)
- Command Injection (output confirmed)
- Path Traversal (file contents shown)

**MISCONFIGURATION:**
- Missing security headers (CSP, X-Frame-Options)
- CORS misconfiguration
- CSRF (without exploit proof)

**INFORMATIONAL:**
- Server header disclosure
- Missing Referrer-Policy
- robots.txt entries

---

## API Endpoints

### Get Findings Summary

```bash
curl http://localhost:8000/api/v1/scans/{scan_id}/findings/summary
```

Response:
```json
{
  "scan_id": "abc123",
  "total_findings": 45,
  "by_category": {
    "exploitable": [
      {"vuln_type": "SQL Injection", "url": "...", "confidence": "confirmed"}
    ],
    "misconfiguration": [...],
    "informational": [...]
  },
  "by_confidence": {
    "confirmed": 5,
    "firm": 10,
    "tentative": 15,
    "low": 15
  }
}
```

### Manual Verification

```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://target.com/vuln",
    "payload": "'\'' OR '\''1'\''='\''1",
    "vuln_type": "SQL Injection",
    "method": "GET"
  }'
```

Response:
```json
{
  "verified": true,
  "confidence": "confirmed",
  "evidence": {
    "response_contains_error": true,
    "error_type": "MySQL syntax error"
  },
  "explanation": "SQL error message confirms injection"
}
```

---

## OWASP ZAP Comparison

### Prerequisites

```bash
# Install ZAP CLI
pip install zap-cli

# Or download from: https://www.zaproxy.org/download/
```

### Run Comparison

```bash
cd scripts
python zap_comparison.py \
  --target http://localhost:8080 \
  --output zap_comparison.json \
  --scanctum-url http://localhost:8000
```

### Output

```
============================================================
COMPARISON SUMMARY
============================================================
  ZAP Total:       25
  Scanctum Total:  22
  Overlap:         18 (72.0%)
  ZAP Unique:      7
  Scanctum Unique: 4
============================================================
```

### Interpreting Results

- **High overlap (>70%)**: Both scanners find same vulnerabilities
- **ZAP unique**: May be false positives or Scanctum blind spot
- **Scanctum unique**: May be better detection or false positives

**Manual review required** for unique findings.

---

## Ground Truth Validation

### How It Works

1. **Ground truth database**: Known vulnerabilities in test apps
   - DVWA: 8 known vulns (SQLi, XSS, CSRF, Command Injection)
   - Juice Shop: 100+ challenges
   - WebGoat: 30+ lessons

2. **Matching algorithm**:
   ```python
   # Finding matches ground truth if:
   - URL contains ground truth location
   - Vulnerability type matches (case-insensitive)
   - Parameter matches (if specified)
   ```

3. **Metrics calculated**:
   - **True Positives (TP)**: Found known vulns
   - **False Positives (FP)**: Exploitable findings with no ground truth
   - **False Negatives (FN)**: Ground truth vulns not found

### Target Ground Truth

#### DVWA (Low Difficulty)
| Vuln | Location | Parameter |
|------|----------|-----------|
| SQLi | /vulnerabilities/sqli/ | id |
| SQLi (Search) | /vulnerabilities/sqli/ | Search |
| XSS Reflected | /vulnerabilities/xss_r/ | name |
| XSS Stored | /vulnerabilities/xss_s/ | txtName |
| CSRF | /vulnerabilities/csrf/ | password_new |
| Command Injection | /vulnerabilities/exec/ | ip |
| Path Traversal | /vulnerabilities/fi/ | page |
| Blind SQLi | /vulnerabilities/sqli_blind/ | id |

#### OWASP Juice Shop
| Vuln | Location | Parameter |
|------|----------|-----------|
| SQLi (Login) | /rest/user/login | email |
| XSS (Search) | / | q |
| Directory Traversal | /ftp/ | file |
| XXE | /file-upload | file |

---

## Running Full Validation Suite

### All Targets

```bash
cd backend
python -m app.scanner.validate --target all --output full_report.txt
```

### With Custom Scanctum URL

```bash
python -m app.scanner.validate \
  --target dvwa \
  --url http://localhost:8080 \
  --scanctum-url http://scanctum.kroszborg.co:8000
```

### Batch Mode (Multiple Runs)

```bash
#!/bin/bash
# run_validation.sh

for target in dvwa juice_shop webgoat; do
  echo "=== Validating $target ==="
  python -m app.scanner.validate \
    --target $target \
    --output reports/${target}_$(date +%Y%m%d).txt
done
```

---

## Interpreting Results

### Good Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| Precision | >90% | Low false positive rate |
| Recall | >80% | Finding most vulns |
| F1 Score | >85% | Good balance |

### Action Items

**If Precision <80%:**
- Review false positives in report
- Check if WAF is interfering
- Consider raising confidence threshold

**If Recall <70%:**
- Review false negatives
- Add new detection patterns
- Increase scan depth/pages

**If Overlap with ZAP <50%:**
- Manually review unique findings
- Check if one scanner has blind spots
- Verify ground truth coverage

---

## Troubleshooting

### Scan Never Completes

```bash
# Check celery worker status
docker compose -f docker-compose.prod.yml logs celery_worker

# Verify Redis connection
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### All Findings Are False Positives

```bash
# Check if WAF is blocking
curl http://target.com/"' OR '1'='1
# If you see "blocked" response, WAF is active

# Solution: Increase request delay, reduce concurrency
# In .env: SCANNER_REQUEST_DELAY=5.0
```

### Ground Truth Not Matching

```python
# Debug matching
from app.scanner.validation import DVWA_GROUND_TRUTH

for gt in DVWA_GROUND_TRUTH:
    print(f"Looking for: {gt.vuln_type} at {gt.location}")
```

---

## Export Results

### JSON Export

```bash
curl http://localhost:8000/api/v1/scans/{scan_id}/export?format=json \
  -o scan_results.json
```

### CSV Export

```bash
curl http://localhost:8000/api/v1/scans/{scan_id}/export?format=csv \
  -o scan_results.csv
```

### PDF Report

```bash
curl http://localhost:8000/api/v1/scans/{scan_id}/report.pdf \
  -o scan_report.pdf
```

---

## Research Paper Metrics

For the research paper, collect:

1. **Per-target metrics**:
   ```
   DVWA: Precision=85%, Recall=75%, F1=80%
   Juice Shop: Precision=88%, Recall=82%, F1=85%
   WebGoat: Precision=90%, Recall=80%, F1=85%
   ```

2. **Comparison with ZAP**:
   ```
   Overlap: 72%
   ZAP unique: 7 (review for FPs)
   Scanctum unique: 4 (review for better detection)
   ```

3. **Category breakdown**:
   ```
   Exploitable: 5 findings (1.6%)
   Misconfiguration: 46 findings (14.8%)
   Informational: 259 findings (83.6%)
   ```

4. **Confidence distribution**:
   ```
   Confirmed: 5 findings (all exploitable)
   Firm: 40 findings (mix of misconfig)
   Tentative: 100 findings (need review)
   Low: 165 findings (informational)
   ```

---

## Summary

**Before Paper Submission:**
- [ ] Run DVWA validation, collect metrics
- [ ] Run Juice Shop validation
- [ ] Run WebGoat validation
- [ ] Run ZAP comparison
- [ ] Document false positives and root causes
- [ ] Update paper with actual numbers

**Expected Results:**
- Precision: 85-92%
- Recall: 75-85%
- F1 Score: 80-88%
- ZAP Overlap: 70-80%
