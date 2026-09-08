"""Tests for the deterministic consistency validator.

These checks catch the math/calendar errors that a hand-written replacement can
introduce (e.g. changing only the total price, or a date that doesn't match its
declared weekday). They run without any AI/API dependency.
"""

from __future__ import annotations

import pytest

from pdf_modifier.core.consistency import ConsistencyValidator

# A mathematically + calendar consistent booking (Nov 7 2026 is a Saturday).
GOOD = {
    "price": 2404.28,
    "tax": 162.29,
    "total": 2566.57,
    "refund": 2467.86,
    "nights": 26,
    "tax_rate": 0.0675,
    "check_in": "2026-11-07",
    "check_out": "2026-12-03",
    "check_in_day": "Saturday",
    "check_out_day": "Thursday",
    "cutoff_1": "2026-11-05",
    "cutoff_2": "2026-11-06",
}


class TestConsistencyValidator:
    @pytest.fixture
    def validator(self) -> ConsistencyValidator:
        return ConsistencyValidator()

    def test_consistent_values_pass(self, validator: ConsistencyValidator) -> None:
        result = validator.validate(dict(GOOD))
        assert result.success is True
        assert result.issues == []
        assert all(result.checked.values()), f"some checks failed: {result.checked}"

    def test_price_tax_must_sum_to_total(self, validator: ConsistencyValidator) -> None:
        # The v6 bug: only the total was changed, price+tax stays the old sum.
        vals = dict(GOOD)
        vals["price"] = 1819.74
        vals["tax"] = 122.83
        result = validator.validate(vals)
        assert result.success is False
        assert any(i.code == "sum_price_tax" and i.severity == "error" for i in result.issues)

    def test_tax_must_match_rated_price(self, validator: ConsistencyValidator) -> None:
        vals = dict(GOOD)
        vals["tax"] = 171.78  # wrong: not price * 6.75%
        result = validator.validate(vals)
        assert any(i.code == "tax_rate_applied" for i in result.issues)

    def test_refund_plus_first_night_must_equal_total(
        self, validator: ConsistencyValidator
    ) -> None:
        vals = dict(GOOD)
        vals["refund"] = 1730.50  # inconsistent withholding
        result = validator.validate(vals)
        assert any(i.code == "first_night_refund" for i in result.issues)

    def test_night_count_matches_dates(self, validator: ConsistencyValidator) -> None:
        vals = dict(GOOD)
        vals["nights"] = 30  # but check-in -> check-out is 26 days
        result = validator.validate(vals)
        assert any(i.code == "night_count" for i in result.issues)

    def test_check_in_weekday_mismatch(self, validator: ConsistencyValidator) -> None:
        vals = dict(GOOD)
        vals["check_in_day"] = "Monday"  # Nov 7 2026 is actually Saturday
        result = validator.validate(vals)
        assert any(i.code == "check_in_weekday" for i in result.issues)

    def test_check_out_weekday_mismatch(self, validator: ConsistencyValidator) -> None:
        vals = dict(GOOD)
        vals["check_out_day"] = "Sunday"  # Dec 3 2026 is actually Thursday
        result = validator.validate(vals)
        assert any(i.code == "check_out_weekday" for i in result.issues)

    def test_cutoffs_must_be_days_before_arrival(self, validator: ConsistencyValidator) -> None:
        vals = dict(GOOD)
        vals["cutoff_2"] = "2026-11-05"  # should be check-in - 1 day (Nov 6)
        result = validator.validate(vals)
        assert any(i.code == "cutoff_days" for i in result.issues)


class TestConsistencyValidatorTolerance:
    def test_small_rounding_is_accepted(self) -> None:
        result = ConsistencyValidator().validate(dict(GOOD))
        assert result.success is True
