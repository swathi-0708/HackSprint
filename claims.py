"""Claim schema for the P2 voice pipeline.

Matches the parser output format in the answer key: {term, value, unit, hedged, quote}.
`Claim.model_json_schema()` can be pasted into the 105B parser prompt.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Term = Literal[
    "monthly_rent",
    "security_deposit",
    "lock_in_period",
    "notice_period",
    "maintenance_charges",
    "deposit_refund_period",
]
Unit = Literal["inr", "days", "months", "months_of_rent", "none"]

TERMS = set(Term.__args__)
UNITS = set(Unit.__args__)

DAYS_PER_MONTH = 30  # fixed rule from the answer key


class Claim(BaseModel):
    term: Term
    value: Optional[float] = None
    unit: Unit = "none"
    hedged: bool = False
    quote: str = ""
    flags: list[str] = Field(default_factory=list)   # e.g. "included_in_rent"
    issues: list[str] = Field(default_factory=list)  # validation problems; empty = clean

    @property
    def ok(self) -> bool:
        return not self.issues

    def in_days(self) -> Optional[float]:
        """Notice / lock-in / refund periods as days, using 1 month = 30 days."""
        if self.value is None:
            return None
        if self.unit == "days":
            return self.value
        if self.unit == "months":
            return self.value * DAYS_PER_MONTH
        return None
