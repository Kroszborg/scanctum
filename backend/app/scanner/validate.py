#!/usr/bin/env python3
"""
Scanctum Validation Runner

Run validation scans against DVWA, Juice Shop, and WebGoat.
Generates a report with precision, recall, and F1 scores.

Usage:
    # Run against all targets
    python -m app.scanner.validate --all

    # Run against specific target
    python -m app.scanner.validate --target dvwa --url http://localhost:8080

    # Run with custom Scanctum URL
    python -m app.scanner.validate --target juice_shop --scanctum-url http://localhost:8000
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scanner.validation import (
    ScannerValidator,
    print_validation_report,
    DVWA_GROUND_TRUTH,
    JUICE_SHOP_GROUND_TRUTH,
    WEBGOAT_GROUND_TRUTH,
)


TARGETS = {
    "dvwa": {
        "name": "DVWA",
        "default_url": "http://localhost:8080",
        "description": "Damn Vulnerable Web Application (Low difficulty)",
        "ground_truth": DVWA_GROUND_TRUTH,
    },
    "juice_shop": {
        "name": "OWASP Juice Shop",
        "default_url": "http://localhost:3000",
        "description": "OWASP Juice Shop v15.x",
        "ground_truth": JUICE_SHOP_GROUND_TRUTH,
    },
    "webgoat": {
        "name": "WebGoat",
        "default_url": "http://localhost:8080/WebGoat",
        "description": "OWASP WebGoat 2023.x",
        "ground_truth": WEBGOAT_GROUND_TRUTH,
    },
}


async def run_validation(
    target_name: str,
    target_url: str,
    scanctum_url: str,
    scan_mode: str = "full",
):
    """Run validation against a single target."""
    validator = ScannerValidator(scanctum_url)

    logger.info(f"Running validation against {target_name} at {target_url}")
    logger.info(f"Scanctum API: {scanctum_url}")
    logger.info(f"Scan mode: {scan_mode}")

    metrics = await validator.run_validation_scan(
        target_name=target_name,
        target_url=target_url,
        scan_mode=scan_mode,
    )

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Run Scanctum validation scans")
    parser.add_argument(
        "--target",
        choices=["dvwa", "juice_shop", "webgoat", "all"],
        required=True,
        help="Target to validate against",
    )
    parser.add_argument(
        "--url",
        help="Target URL (default depends on target)",
    )
    parser.add_argument(
        "--scanctum-url",
        default="http://localhost:8000",
        help="Scanctum API URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--scan-mode",
        choices=["quick", "full"],
        default="full",
        help="Scan mode (default: full)",
    )
    parser.add_argument(
        "--output",
        default="validation_report.txt",
        help="Output file for report",
    )

    args = parser.parse_args()

    if args.target == "all":
        # Run against all targets
        results = {}
        for target_name, target_info in TARGETS.items():
            url = args.url or target_info["default_url"]
            try:
                metrics = asyncio.run(
                    run_validation(
                        target_name=target_name,
                        target_url=url,
                        scanctum_url=args.scanctum_url,
                        scan_mode=args.scan_mode,
                    )
                )
                results[target_name] = metrics
            except Exception as e:
                logger.error(f"Failed to validate {target_name}: {e}")
                results[target_name] = None

        # Generate report
        if results:
            valid_results = {k: v for k, v in results.items() if v is not None}
            if valid_results:
                report = print_validation_report(valid_results)
                print(report)

                # Save to file
                with open(args.output, "w") as f:
                    f.write(report)
                logger.info(f"Report saved to {args.output}")
    else:
        # Run against single target
        target_info = TARGETS[args.target]
        url = args.url or target_info["default_url"]

        metrics = asyncio.run(
            run_validation(
                target_name=args.target,
                target_url=url,
                scanctum_url=args.scanctum_url,
                scan_mode=args.scan_mode,
            )
        )

        # Print report
        report = print_validation_report({args.target: metrics})
        print(report)

        # Save to file
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
