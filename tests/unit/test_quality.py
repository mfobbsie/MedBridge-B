"""
Unit tests for quality_service.py

Run: pytest tests/unit/test_quality.py -v
"""

import pytest
from app.services.quality_service import check_summary_quality, measure_reading_level


GOOD_SUMMARY = """
This appears to be a cholesterol blood test result from a recent lab visit.

Your LDL cholesterol (sometimes called "bad cholesterol" because higher levels 
may contribute to plaque buildup in arteries) was 142 mg/dL, which is above 
the typical reference range shown on your report.

Your HDL cholesterol (often called "good cholesterol" because it helps remove 
other forms of cholesterol from the body) was 58 mg/dL, which is within the 
normal range.

You may wish to discuss with your healthcare provider what these results mean 
for your overall health and whether any follow-up is needed.

MedBridge explains information from your uploaded document in plain language. 
It does not provide medical advice, diagnosis, or treatment recommendations. 
Please contact a healthcare provider for medical decisions.
""".strip()

DIAGNOSIS_SUMMARY = """
You have been diagnosed with hyperlipidemia. Your LDL is high.
You should take statins immediately. I recommend starting medication right away.
MedBridge explains information from your uploaded document in plain language.
It does not provide medical advice.
""".strip()

NO_DISCLAIMER_SUMMARY = """
This appears to be a cholesterol test. Your LDL was 142 mg/dL, which is above
the typical reference range. You may wish to discuss this with your provider.
""".strip()

COMPLEX_SUMMARY = """
The patient's eGFR was measured at 58 mL/min/1.73m². 
The HbA1c result was 7.2% indicating suboptimal glycemic control.
Recommend immediate medication adjustment and dietary intervention.
""".strip()


class TestGoodSummary:
    def test_passes_quality_check(self):
        result = check_summary_quality(GOOD_SUMMARY)
        assert result.passed

    def test_has_reading_level(self):
        result = check_summary_quality(GOOD_SUMMARY)
        assert result.reading_level is not None

    def test_no_issues(self):
        result = check_summary_quality(GOOD_SUMMARY)
        assert len(result.issues) == 0


class TestDiagnosisSummary:
    def test_fails_quality_check(self):
        result = check_summary_quality(DIAGNOSIS_SUMMARY)
        assert not result.passed

    def test_flags_forbidden_language(self):
        result = check_summary_quality(DIAGNOSIS_SUMMARY)
        assert any("Forbidden language" in issue for issue in result.issues)


class TestNoDisclaimerSummary:
    def test_fails_without_disclaimer(self):
        result = check_summary_quality(NO_DISCLAIMER_SUMMARY)
        assert not result.passed

    def test_flags_missing_disclaimer(self):
        result = check_summary_quality(NO_DISCLAIMER_SUMMARY)
        assert any("medical advice" in issue for issue in result.issues)


class TestComplexSummary:
    def test_flags_unexplained_terms(self):
        result = check_summary_quality(COMPLEX_SUMMARY)
        # eGFR and HbA1c are not explained — should be flagged
        assert any("Medical terms" in issue for issue in result.issues)


class TestEmptySummary:
    def test_empty_string_fails(self):
        result = check_summary_quality("")
        assert not result.passed

    def test_whitespace_only_fails(self):
        result = check_summary_quality("   \n\n  ")
        assert not result.passed


class TestReadingLevel:
    def test_simple_text_low_grade(self):
        simple = "The test came back normal. Your results look good."
        grade = measure_reading_level(simple)
        assert grade is not None
        assert grade < 8.0

    def test_complex_text_higher_grade(self):
        complex_text = (
            "The electroencephalographic findings demonstrate paroxysmal "
            "epileptiform discharges with hemispheric lateralization."
        )
        grade = measure_reading_level(complex_text)
        assert grade is not None
        assert grade > 8.0
