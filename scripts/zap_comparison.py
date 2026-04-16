#!/usr/bin/env python3
"""
OWASP ZAP Benchmark Comparison Script

Compares Scanctum findings against OWASP ZAP scan results.
Requires ZAP CLI (zap-cli) to be installed.

Usage:
    python zap_comparison.py --target http://dvwa.local --output report.json
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_zap_scan(target_url: str, output_file: str) -> dict:
    """Run OWASP ZAP scan and return findings."""
    print(f"[*] Starting OWASP ZAP scan on {target_url}")

    # ZAP CLI commands
    commands = [
        f"zap-cli quick-scan -s all -r {output_file} {target_url}",
    ]

    try:
        for cmd in commands:
            print(f"[*] Running: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

        # Parse ZAP report
        zap_findings = parse_zap_report(output_file)
        return zap_findings

    except subprocess.TimeoutExpired:
        print("[!] ZAP scan timed out after 10 minutes")
        return {"alerts": [], "error": "timeout"}
    except Exception as e:
        print(f"[!] ZAP scan failed: {e}")
        return {"alerts": [], "error": str(e)}


def parse_zap_report(report_file: str) -> dict:
    """Parse ZAP HTML report to extract alerts."""
    findings = {"alerts": []}

    try:
        from bs4 import BeautifulSoup

        with open(report_file, "r") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Find all alert tables
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header
                cols = row.find_all("td")
                if len(cols) >= 3:
                    findings["alerts"].append({
                        "alert": cols[0].text.strip(),
                        "risk": cols[1].text.strip(),
                        "url": cols[2].text.strip(),
                    })

    except ImportError:
        print("[!] BeautifulSoup not installed, install with: pip install beautifulsoup4")
    except Exception as e:
        print(f"[!] Failed to parse ZAP report: {e}")

    return findings


def run_scanctum_scan(target_url: str, scanctum_url: str = "http://localhost:8000") -> dict:
    """Run Scanctum scan via API and return findings."""
    import httpx

    print(f"[*] Starting Scanctum scan on {target_url}")

    try:
        with httpx.Client(timeout=300.0) as client:
            # Create scan
            response = client.post(
                f"{scanctum_url}/api/v1/scans",
                json={"target_url": target_url, "scan_mode": "full"},
            )
            response.raise_for_status()
            scan_data = response.json()
            scan_id = scan_data["id"]
            print(f"[*] Scan created: {scan_id}")

            # Poll for completion
            while True:
                import time
                time.sleep(10)
                status = client.get(f"{scanctum_url}/api/v1/scans/{scan_id}")
                status_data = status.json()

                if status_data.get("status") in ["completed", "failed"]:
                    break

            if status_data.get("status") == "failed":
                print(f"[!] Scan failed: {status_data.get('error_message')}")
                return {"vulnerabilities": [], "error": "scan failed"}

            # Get vulnerabilities
            vulns = client.get(
                f"{scanctum_url}/api/v1/scans/{scan_id}/vulnerabilities"
            )
            return vulns.json()

    except Exception as e:
        print(f"[!] Scanctum scan failed: {e}")
        return {"vulnerabilities": [], "error": str(e)}


def compare_findings(zap_findings: dict, scanctum_findings: dict) -> dict:
    """Compare findings from both scanners."""
    comparison = {
        "zap_only": [],
        "scanctum_only": [],
        "both": [],
        "summary": {},
    }

    # Normalize findings for comparison
    zap_alerts = set()
    for alert in zap_findings.get("alerts", []):
        key = f"{alert['alert']}:{alert['url']}"
        zap_alerts.add(key)

    scanctum_vulns = set()
    for vuln in scanctum_findings.get("vulnerabilities", []):
        key = f"{vuln['vuln_type']}:{vuln['affected_url']}"
        scanctum_vulns.add(key)

    # Compare
    comparison["zap_only"] = list(zap_alerts - scanctum_vulns)
    comparison["scanctum_only"] = list(scanctum_vulns - zap_alerts)
    comparison["both"] = list(zap_alerts & scanctum_vulns)

    # Summary
    comparison["summary"] = {
        "zap_total": len(zap_alerts),
        "scanctum_total": len(scanctum_vulns),
        "overlap": len(comparison["both"]),
        "zap_unique": len(comparison["zap_only"]),
        "scanctum_unique": len(comparison["scanctum_only"]),
        "overlap_percentage": (
            len(comparison["both"]) / max(len(zap_alerts), 1) * 100
        ),
    }

    return comparison


def generate_report(comparison: dict, output_file: str):
    """Generate comparison report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "comparison": comparison,
        "analysis": {
            "zap_strengths": "ZAP found these unique issues:",
            "scanctum_strengths": "Scanctum found these unique issues:",
            "agreement": "Both scanners agreed on these issues:",
        },
    }

    report["analysis"]["zap_strengths"] = comparison["zap_only"][:10]
    report["analysis"]["scanctum_strengths"] = comparison["scanctum_only"][:10]
    report["analysis"]["agreement"] = comparison["both"][:10]

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[*] Report saved to {output_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    summary = comparison["summary"]
    print(f"  ZAP Total:       {summary['zap_total']}")
    print(f"  Scanctum Total:  {summary['scanctum_total']}")
    print(f"  Overlap:         {summary['overlap']} ({summary['overlap_percentage']:.1f}%)")
    print(f"  ZAP Unique:      {summary['zap_unique']}")
    print(f"  Scanctum Unique: {summary['scanctum_unique']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Compare Scanctum vs OWASP ZAP")
    parser.add_argument("--target", required=True, help="Target URL to scan")
    parser.add_argument("--output", default="zap_comparison.json", help="Output file")
    parser.add_argument(
        "--scanctum-url",
        default="http://localhost:8000",
        help="Scanctum API URL",
    )
    parser.add_argument("--skip-zap", action="store_true", help="Skip ZAP scan")
    parser.add_argument("--skip-scanctum", action="store_true", help="Skip Scanctum scan")

    args = parser.parse_args()

    zap_findings = {}
    scanctum_findings = {}

    # Run ZAP scan
    if not args.skip_zap:
        zap_output = args.output.replace(".json", "_zap.html")
        zap_findings = run_zap_scan(args.target, zap_output)

    # Run Scanctum scan
    if not args.skip_scanctum:
        scanctum_findings = run_scanctum_scan(args.target, args.scanctum_url)

    # Compare
    comparison = compare_findings(zap_findings, scanctum_findings)

    # Generate report
    generate_report(comparison, args.output)


if __name__ == "__main__":
    main()
