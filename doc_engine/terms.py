"""The 6 terms, units, keywords, and the Extract schema."""
import json

TERMS = ["monthly_rent", "security_deposit", "deposit_refund_period",
         "lock_in_period", "notice_period", "maintenance_charges"]
UNITS = ["inr", "days", "months", "months_of_rent", "none"]

KEYWORDS = {
    "monthly_rent": ["monthly rent", "rent of", "rent shall be", "per month"],
    "security_deposit": ["security deposit", "deposit", "advance"],
    "deposit_refund_period": ["refund", "returned", "repay", "return of deposit"],
    "lock_in_period": ["lock-in", "lock in", "lockin", "minimum period", "minimum stay"],
    "notice_period": ["notice", "vacate", "terminate"],
    "maintenance_charges": ["maintenance", "society charges", "association charges"],
}

_TERM_DESC = {
    "monthly_rent": "Monthly rent payable by the tenant. value in INR. unit 'inr'.",
    "security_deposit": ("Refundable security deposit. If stated as a rupee amount use unit 'inr'; "
                         "if stated as a number of months of rent use that number with unit 'months_of_rent'."),
    "deposit_refund_period": "Time within which the deposit is refunded after vacating. Use unit 'days' or 'months'.",
    "lock_in_period": "Minimum period the tenant must stay (lock-in). Use unit 'months' or 'days'.",
    "notice_period": "Notice the tenant or landlord must give before vacating or terminating. Use unit 'days' or 'months'.",
    "maintenance_charges": "Maintenance/society charges payable by the tenant per month. value in INR, unit 'inr'.",
}


def _term_schema(term: str) -> dict:
    d = _TERM_DESC[term]
    return {
        "type": "object",
        "description": d,
        "properties": {
            "mentioned": {"type": "boolean",
                          "description": f"True only if the agreement explicitly states {term.replace('_', ' ')}."},
            "value": {"type": "number",
                      "description": "Numeric value exactly as written in the agreement. Omit if not mentioned. Never guess."},
            "unit": {"type": "string", "enum": UNITS,
                     "description": "Unit of the value: inr, days, months, months_of_rent, or none."},
            "clause_text": {"type": "string",
                            "description": "The exact sentence(s) copied verbatim from the agreement stating this term. Empty if not mentioned."},
        },
    }


def extract_schema_json() -> str:
    schema = {"type": "object",
              "description": "Key commercial terms of an Indian residential rental or PG agreement.",
              "properties": {t: _term_schema(t) for t in TERMS}}
    return json.dumps(schema)
