"""CVSS v3.1 Base Score calculator using official FIRST.org equations."""

import math
from dataclasses import dataclass

# Metric value mappings from CVSS v3.1 specification
AV_VALUES = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}  # Network, Adjacent, Local, Physical
AC_VALUES = {"L": 0.77, "H": 0.44}  # Low, High
PR_VALUES_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_VALUES_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.50}
UI_VALUES = {"N": 0.85, "R": 0.62}  # None, Required
CIA_VALUES = {"N": 0.0, "L": 0.22, "H": 0.56}  # None, Low, High
SCOPE_VALUES = {"U", "C"}  # Unchanged, Changed


@dataclass
class CVSSMetrics:
    attack_vector: str  # N, A, L, P
    attack_complexity: str  # L, H
    privileges_required: str  # N, L, H
    user_interaction: str  # N, R
    scope: str  # U, C
    confidentiality: str  # N, L, H
    integrity: str  # N, L, H
    availability: str  # N, L, H

    @classmethod
    def from_vector(cls, vector: str) -> "CVSSMetrics":
        """Parse a CVSS v3.1 vector string like CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"""
        parts = {}
        for component in vector.replace("CVSS:3.1/", "").split("/"):
            key, val = component.split(":")
            parts[key] = val

        return cls(
            attack_vector=parts["AV"],
            attack_complexity=parts["AC"],
            privileges_required=parts["PR"],
            user_interaction=parts["UI"],
            scope=parts["S"],
            confidentiality=parts["C"],
            integrity=parts["I"],
            availability=parts["A"],
        )

    def to_vector(self) -> str:
        return (
            f"CVSS:3.1/AV:{self.attack_vector}/AC:{self.attack_complexity}"
            f"/PR:{self.privileges_required}/UI:{self.user_interaction}"
            f"/S:{self.scope}/C:{self.confidentiality}"
            f"/I:{self.integrity}/A:{self.availability}"
        )


def _roundup(value: float) -> float:
    """CVSS Roundup function: round up to 1 decimal place."""
    return math.ceil(value * 10) / 10


def calculate_base_score(metrics: CVSSMetrics) -> float:
    """Calculate CVSS v3.1 Base Score from metrics."""
    # Impact Sub Score Base
    isc_base = 1 - (
        (1 - CIA_VALUES[metrics.confidentiality])
        * (1 - CIA_VALUES[metrics.integrity])
        * (1 - CIA_VALUES[metrics.availability])
    )

    # Impact
    if metrics.scope == "U":
        impact = 6.42 * isc_base
    else:
        impact = 7.52 * (isc_base - 0.029) - 3.25 * ((isc_base - 0.02) ** 15)

    # Exploitability
    pr_values = PR_VALUES_CHANGED if metrics.scope == "C" else PR_VALUES_UNCHANGED
    exploitability = (
        8.22
        * AV_VALUES[metrics.attack_vector]
        * AC_VALUES[metrics.attack_complexity]
        * pr_values[metrics.privileges_required]
        * UI_VALUES[metrics.user_interaction]
    )

    # Base Score
    if impact <= 0:
        return 0.0

    if metrics.scope == "U":
        base_score = _roundup(min(impact + exploitability, 10))
    else:
        base_score = _roundup(min(1.08 * (impact + exploitability), 10))

    return base_score


def score_from_vector(vector: str) -> float:
    """Convenience function: calculate score directly from vector string."""
    metrics = CVSSMetrics.from_vector(vector)
    return calculate_base_score(metrics)


def severity_from_score(score: float) -> str:
    """Map CVSS score to severity label."""
    if score == 0.0:
        return "info"
    elif score <= 3.9:
        return "low"
    elif score <= 6.9:
        return "medium"
    elif score <= 8.9:
        return "high"
    else:
        return "critical"
