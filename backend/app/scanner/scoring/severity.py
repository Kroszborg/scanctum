"""OWASP Top 10 (2021) mapping for vulnerability categorization."""

OWASP_TOP_10 = {
    "A01": {
        "name": "Broken Access Control",
        "description": "Failures that allow unauthorized access to resources or actions.",
        "cwes": ["CWE-200", "CWE-352", "CWE-601", "CWE-639"],
    },
    "A02": {
        "name": "Cryptographic Failures",
        "description": "Failures related to cryptography that expose sensitive data.",
        "cwes": ["CWE-319", "CWE-311", "CWE-327", "CWE-523"],
    },
    "A03": {
        "name": "Injection",
        "description": "User-supplied data is not validated, filtered, or sanitized.",
        "cwes": ["CWE-79", "CWE-89"],
    },
    "A04": {
        "name": "Insecure Design",
        "description": "Missing or ineffective control design.",
        "cwes": [],
    },
    "A05": {
        "name": "Security Misconfiguration",
        "description": "Missing or incorrect security configuration.",
        "cwes": ["CWE-16", "CWE-200", "CWE-215", "CWE-548", "CWE-538", "CWE-942", "CWE-1004", "CWE-614", "CWE-1021", "CWE-1275"],
    },
    "A06": {
        "name": "Vulnerable and Outdated Components",
        "description": "Using components with known vulnerabilities.",
        "cwes": [],
    },
    "A07": {
        "name": "Identification and Authentication Failures",
        "description": "Weaknesses in authentication and session management.",
        "cwes": ["CWE-307"],
    },
    "A08": {
        "name": "Software and Data Integrity Failures",
        "description": "Code and infrastructure that does not protect against integrity violations.",
        "cwes": [],
    },
    "A09": {
        "name": "Security Logging and Monitoring Failures",
        "description": "Insufficient logging, detection, monitoring, and active response.",
        "cwes": [],
    },
    "A10": {
        "name": "Server-Side Request Forgery",
        "description": "Fetching a remote resource without validating the user-supplied URL.",
        "cwes": ["CWE-918"],
    },
}


def get_owasp_category(cwe_id: str) -> str:
    """Map CWE ID to OWASP Top 10 category."""
    for category, info in OWASP_TOP_10.items():
        if cwe_id in info["cwes"]:
            return category
    return "A05"  # Default to Security Misconfiguration


def get_owasp_name(category: str) -> str:
    """Get OWASP category name."""
    return OWASP_TOP_10.get(category, {}).get("name", "Unknown")
