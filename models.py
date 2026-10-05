"""Outcome labels and the result structure shared by compare.py, services.py and the UI.

Input contracts:
  Claim  -> claims.Claim (P2 voice pipeline, after normalize.py)
  facts  -> doc_engine facts.json: {"agreement_id": ..., "terms": {term: {...}}}
"""
from dataclasses import dataclass, field
from typing import Optional

MATCH = "MATCH"
MISMATCH = "MISMATCH"
NOT_MENTIONED = "NOT_MENTIONED"
UNCLEAR = "UNCLEAR"
OUTCOMES = (MATCH, MISMATCH, NOT_MENTIONED, UNCLEAR)


@dataclass
class ComparisonResult:
    term: str
    outcome: str
    reason: str                              # short code, e.g. "values_equal", "unit_mismatch"
    said_value: Optional[float] = None
    said_unit: str = "none"
    agreement_value: Optional[float] = None
    agreement_unit: str = "none"
    clause_text: Optional[str] = None
    page: Optional[int] = None
    confidence: Optional[float] = None
    quote: str = ""
    hedged: bool = False
    included_in_rent: bool = False           # speaker said maintenance is included in rent
    converted_amount: Optional[float] = None  # e.g. 2 months' rent -> 36000
    rent_used: Optional[float] = None
    flags: list = field(default_factory=list)
