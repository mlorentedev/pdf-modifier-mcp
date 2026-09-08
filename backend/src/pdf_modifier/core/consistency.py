"""Deterministic consistency checks for text-replacement targets.

These validators catch the math/calendar errors a hand-written replacement can
introduce (e.g. changing only the total price, or a date that does not match its
declared weekday). They are pure Python — no AI/API dependency — so they are
reliable in CI and locally.

The ``ConsistencyValidator`` consumes a flat dict of target values (the values a
replacement is going to write) and reports any internal inconsistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import StrEnum

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_TOLERANCE = 0.02  # currency tolerance (amounts rounded to cents)


class Severity(StrEnum):
    """Issue severity."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ConsistencyIssue:
    """A single consistency finding."""

    severity: Severity
    code: str
    message: str
    field: str


@dataclass(frozen=True)
class ReviewResult:
    """Result of a consistency review."""

    success: bool
    issues: list[ConsistencyIssue] = field(default_factory=list)
    checked: dict[str, bool] = field(default_factory=dict)


def _is_close(a: float, b: float, tolerance: float = _TOLERANCE) -> bool:
    return abs(a - b) <= max(tolerance, abs(b) * 1e-6)


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


class ConsistencyValidator:
    """Validates a set of financial/calendar target values for consistency.

    Example:
        >>> result = ConsistencyValidator().validate(values)
        >>> result.success
        True
    """

    def __init__(self, tolerance: float = _TOLERANCE) -> None:
        self.tolerance = tolerance

    def _check(
        self,
        issues: list[ConsistencyIssue],
        checked: dict[str, bool],
        code: str,
        field: str,
        ok: bool,
        message: str,
        severity: Severity,
    ) -> None:
        checked[code] = ok
        if not ok:
            issues.append(
                ConsistencyIssue(severity=severity, code=code, message=message, field=field)
            )

    def validate(self, values: dict[str, object]) -> ReviewResult:
        """Check ``values`` for internal consistency and return findings."""
        issues: list[ConsistencyIssue] = []
        checked: dict[str, bool] = {}

        price = values.get("price")
        tax = values.get("tax")
        total = values.get("total")
        refund = values.get("refund")
        nights = values.get("nights")
        tax_rate = values.get("tax_rate")

        # --- Arithmetic ---
        if (
            isinstance(price, int | float)
            and isinstance(tax, int | float)
            and isinstance(total, int | float)
        ):
            self._check(
                issues,
                checked,
                "sum_price_tax",
                "total",
                _is_close(float(price) + float(tax), float(total), self.tolerance),
                f"price ({price}) + tax ({tax}) != total ({total})",
                Severity.ERROR,
            )

        if (
            isinstance(price, int | float)
            and isinstance(tax, int | float)
            and isinstance(tax_rate, int | float)
        ):
            self._check(
                issues,
                checked,
                "tax_rate_applied",
                "tax",
                _is_close(float(tax), float(price) * float(tax_rate), self.tolerance),
                f"tax ({tax}) != price ({price}) * rate ({tax_rate})",
                Severity.ERROR,
            )

        if (
            isinstance(total, int | float)
            and isinstance(refund, int | float)
            and isinstance(nights, int)
            and nights > 0
        ):
            first_night = float(total) / nights
            self._check(
                issues,
                checked,
                "first_night_refund",
                "refund",
                _is_close(float(refund) + first_night, float(total), self.tolerance),
                f"refund ({refund}) + first night (~{first_night:.2f}) != total ({total})",
                Severity.ERROR,
            )

        # --- Calendar ---
        check_in = _parse_date(values.get("check_in"))
        check_out = _parse_date(values.get("check_out"))

        if check_in is not None and check_out is not None and isinstance(nights, int):
            delta = (check_out - check_in).days
            self._check(
                issues,
                checked,
                "night_count",
                "nights",
                delta == nights,
                f"check-in {check_in} -> check-out {check_out} is {delta} nights, not {nights}",
                Severity.ERROR,
            )

        if check_in is not None:
            expected = _WEEKDAYS[check_in.weekday()]
            declared = values.get("check_in_day")
            self._check(
                issues,
                checked,
                "check_in_weekday",
                "check_in_day",
                declared == expected,
                f"check-in {check_in} is a {expected}, declared {declared}",
                Severity.ERROR,
            )

        if check_out is not None:
            expected = _WEEKDAYS[check_out.weekday()]
            declared = values.get("check_out_day")
            self._check(
                issues,
                checked,
                "check_out_weekday",
                "check_out_day",
                declared == expected,
                f"check-out {check_out} is a {expected}, declared {declared}",
                Severity.ERROR,
            )

        if check_in is not None:
            cutoff_1 = _parse_date(values.get("cutoff_1"))
            cutoff_2 = _parse_date(values.get("cutoff_2"))
            if cutoff_2 is not None:
                self._check(
                    issues,
                    checked,
                    "cutoff_days",
                    "cutoff_2",
                    cutoff_2 == check_in - timedelta(days=1),
                    f"cutoff_2 {cutoff_2} != check-in - 1 day",
                    Severity.ERROR,
                )
            if cutoff_1 is not None:
                self._check(
                    issues,
                    checked,
                    "cutoff_days_1",
                    "cutoff_1",
                    cutoff_1 == check_in - timedelta(days=2),
                    f"cutoff_1 {cutoff_1} != check-in - 2 days",
                    Severity.WARNING,
                )
            if cutoff_1 is None and cutoff_2 is None:
                checked["cutoff_days"] = True

        return ReviewResult(success=len(issues) == 0, issues=issues, checked=checked)
