"""Compare one spoken Claim with the agreement facts.

Outcomes: MATCH / MISMATCH / NOT_MENTIONED / UNCLEAR. We prefer UNCLEAR over a wrong answer.
Rules:
  - claim has validation issues, no value, or an unusable unit pair  -> UNCLEAR
  - agreement does not mention the term                              -> NOT_MENTIONED
  - agreement clause failed verification against the document        -> UNCLEAR
  - days vs months are compared in days (1 month = 30 days)
  - deposit "N months' rent" vs a rupee amount uses the agreement's monthly rent
  - a hedged claim ("around", "maybe") that differs is UNCLEAR, never a firm MISMATCH
  - "maintenance is included in rent": MATCH only if the agreement charges 0
"""
from claims import DAYS_PER_MONTH, Claim
from models import MATCH, MISMATCH, NOT_MENTIONED, UNCLEAR, ComparisonResult

TOL = 0.5  # rupee / unit tolerance


def _terms(facts: dict) -> dict:
    return facts.get("terms", facts) if isinstance(facts, dict) else {}


def _days(value, unit):
    if unit == "days":
        return value
    if unit == "months":
        return value * DAYS_PER_MONTH
    return None


def _rent(terms: dict):
    r = terms.get("monthly_rent") or {}
    if r.get("mentioned") and r.get("unit") == "inr" and r.get("value"):
        return float(r["value"])
    return None


def _equal(claim: Claim, fact: dict, terms: dict):
    """-> (equal: bool|None, reason, converted_amount, rent_used). None = cannot tell."""
    cv, cu = claim.value, claim.unit
    fv, fu = fact.get("value"), fact.get("unit", "none")
    if fv is None:
        return None, "agreement_no_value", None, None
    if cu == fu and cu in ("inr", "months_of_rent", "days", "months", "none"):
        return abs(cv - fv) <= TOL, "values_equal" if abs(cv - fv) <= TOL else "values_differ", None, None
    cd, fd = _days(cv, cu), _days(fv, fu)
    if cd is not None and fd is not None:
        eq = abs(cd - fd) <= TOL
        return eq, "values_equal_after_unit_conversion" if eq else "values_differ", None, None
    if claim.term == "security_deposit" and {cu, fu} == {"months_of_rent", "inr"}:
        rent = _rent(terms)
        if rent is None:
            return None, "needs_rent_to_convert", None, None
        if cu == "months_of_rent":
            amount = cv * rent
            eq = abs(amount - fv) <= TOL
            return eq, "values_equal_after_unit_conversion" if eq else "values_differ", amount, rent
        amount = fv * rent  # agreement says N months' rent; claim is in rupees
        eq = abs(amount - cv) <= TOL
        return eq, "values_equal_after_unit_conversion" if eq else "values_differ", amount, rent
    return None, "unit_mismatch", None, None


def compare_claim(claim: Claim, facts: dict) -> ComparisonResult:
    terms = _terms(facts)
    fact = terms.get(claim.term) or {}
    mentioned = bool(fact.get("mentioned"))
    r = ComparisonResult(
        term=claim.term, outcome=UNCLEAR, reason="",
        said_value=claim.value, said_unit=claim.unit, quote=claim.quote, hedged=claim.hedged,
        included_in_rent="included_in_rent" in claim.flags, flags=list(claim.flags),
    )
    if mentioned:
        r.agreement_value, r.agreement_unit = fact.get("value"), fact.get("unit", "none")
        r.clause_text, r.page, r.confidence = fact.get("clause_text"), fact.get("page"), fact.get("confidence")

    def done(outcome, reason):
        r.outcome, r.reason = outcome, reason
        return r

    if claim.issues:
        return done(UNCLEAR, "claim_not_understood")
    if r.included_in_rent:
        if not mentioned:
            return done(NOT_MENTIONED, "term_not_in_agreement")
        if fact.get("verified") is False:
            return done(UNCLEAR, "clause_unverified")
        return done(MATCH, "included_and_zero") if not fact.get("value") else done(MISMATCH, "included_but_charged")
    if not mentioned:
        return done(NOT_MENTIONED, "term_not_in_agreement")
    if fact.get("verified") is False:
        return done(UNCLEAR, "clause_unverified")
    if claim.value is None:
        return done(UNCLEAR, "no_value")

    eq, reason, amount, rent = _equal(claim, fact, terms)
    r.converted_amount, r.rent_used = amount, rent
    if eq is None:
        return done(UNCLEAR, reason)
    if eq:
        return done(MATCH, reason)
    return done(UNCLEAR, "speaker_unsure") if claim.hedged else done(MISMATCH, reason)


def compare_all(claims: list, facts: dict) -> list:
    return [compare_claim(c, facts) for c in claims]
