import pytest

from app.scanner.scoring.cvss_lite import (
    CVSSMetrics,
    calculate_base_score,
    score_from_vector,
    severity_from_score,
)


class TestCVSSCalculator:
    """Test CVSS v3.1 Base Score calculations against known NVD vectors."""

    def test_sqli_critical(self):
        # SQL Injection: AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert score == 9.8

    def test_xss_reflected(self):
        # Reflected XSS: AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N = 6.1
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N")
        assert score == 6.1

    def test_info_disclosure(self):
        # AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N = 5.3
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N")
        assert score == 5.3

    def test_zero_impact(self):
        # All CIA = None → score should be 0.0
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
        assert score == 0.0

    def test_local_physical_access(self):
        # AV:P/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N = 1.6
        score = score_from_vector("CVSS:3.1/AV:P/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N")
        assert score == 1.6

    def test_scope_changed_high(self):
        # AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H = 10.0
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
        assert score == 10.0

    def test_cors_misconfiguration(self):
        # AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N = 8.1
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N")
        assert score == 8.1

    def test_medium_severity(self):
        # AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N = 4.3
        score = score_from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N")
        assert score == 4.3


class TestSeverityMapping:
    def test_info(self):
        assert severity_from_score(0.0) == "info"

    def test_low(self):
        assert severity_from_score(1.0) == "low"
        assert severity_from_score(3.9) == "low"

    def test_medium(self):
        assert severity_from_score(4.0) == "medium"
        assert severity_from_score(6.9) == "medium"

    def test_high(self):
        assert severity_from_score(7.0) == "high"
        assert severity_from_score(8.9) == "high"

    def test_critical(self):
        assert severity_from_score(9.0) == "critical"
        assert severity_from_score(10.0) == "critical"


class TestCVSSMetricsParsing:
    def test_from_vector(self):
        metrics = CVSSMetrics.from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        assert metrics.attack_vector == "N"
        assert metrics.attack_complexity == "L"
        assert metrics.privileges_required == "N"
        assert metrics.user_interaction == "N"
        assert metrics.scope == "U"
        assert metrics.confidentiality == "H"
        assert metrics.integrity == "H"
        assert metrics.availability == "H"

    def test_to_vector(self):
        metrics = CVSSMetrics(
            attack_vector="N", attack_complexity="L",
            privileges_required="N", user_interaction="N",
            scope="U", confidentiality="H",
            integrity="H", availability="H",
        )
        assert metrics.to_vector() == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
