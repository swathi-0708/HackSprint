from dataclasses import dataclass
from typing import Optional


@dataclass
class Claim:
    field: str
    value: float | str
    unit: Optional[str] = None
    language: Optional[str] = None


@dataclass
class AgreementFact:
    field: str
    value: float | str
    unit: Optional[str] = None
    source_clause: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class ComparisonResult:
    field: str
    claim_value: float | str
    agreement_value: float | str | None
    outcome: str
    source_clause: Optional[str] = None
    explanation: Optional[str] = None


MATCH = "MATCH"
MISMATCH = "MISMATCH"
NOT_MENTIONED = "NOT MENTIONED"
UNCLEAR = "UNCLEAR"