from claims import Claim
from compare import compare_claim
from models import MATCH, MISMATCH, NOT_MENTIONED, UNCLEAR

FACTS = {"terms": {
    "monthly_rent": {"mentioned": True, "value": 18000, "unit": "inr"},
    "security_deposit": {"mentioned": True, "value": 36000, "unit": "inr"},
    "deposit_refund_period": {"mentioned": True, "value": 30, "unit": "days"},
    "lock_in_period": {"mentioned": False, "value": None, "unit": "none"},
    "notice_period": {"mentioned": True, "value": 1, "unit": "months"},
    "maintenance_charges": {"mentioned": True, "value": 1500, "unit": "inr"},
}}


def c(term, value, unit, **kw):
    return Claim(term=term, value=value, unit=unit, **kw)


def test_equal_rupees_match():
    assert compare_claim(c("monthly_rent", 18000, "inr"), FACTS).outcome == MATCH


def test_different_rupees_mismatch():
    assert compare_claim(c("monthly_rent", 20000, "inr"), FACTS).outcome == MISMATCH


def test_days_vs_months_match():
    r = compare_claim(c("notice_period", 30, "days"), FACTS)
    assert r.outcome == MATCH and r.reason == "values_equal_after_unit_conversion"
    assert compare_claim(c("deposit_refund_period", 1, "months"), FACTS).outcome == MATCH


def test_days_vs_months_mismatch():
    assert compare_claim(c("notice_period", 15, "days"), FACTS).outcome == MISMATCH


def test_deposit_months_of_rent_converts_with_agreement_rent():
    r = compare_claim(c("security_deposit", 2, "months_of_rent"), FACTS)
    assert r.outcome == MATCH and r.converted_amount == 36000 and r.rent_used == 18000


def test_deposit_rupees_vs_months_of_rent_agreement():
    f = {"terms": {**FACTS["terms"], "security_deposit": {"mentioned": True, "value": 2, "unit": "months_of_rent"}}}
    r = compare_claim(c("security_deposit", 40000, "inr"), f)
    assert r.outcome == MISMATCH and r.converted_amount == 36000


def test_deposit_conversion_without_rent_is_unclear():
    f = {"terms": {**FACTS["terms"], "monthly_rent": {"mentioned": False}}}
    assert compare_claim(c("security_deposit", 2, "months_of_rent"), f).outcome == UNCLEAR


def test_not_mentioned_term():
    assert compare_claim(c("lock_in_period", 6, "months"), FACTS).outcome == NOT_MENTIONED


def test_claim_with_issues_is_unclear():
    cl = c("monthly_rent", 18000, "inr", issues=["out_of_range:18000"])
    assert compare_claim(cl, FACTS).outcome == UNCLEAR


def test_missing_value_is_unclear():
    assert compare_claim(c("monthly_rent", None, "none"), FACTS).outcome == UNCLEAR


def test_hedged_equal_is_match_but_hedged_differ_is_unclear():
    assert compare_claim(c("maintenance_charges", 1500, "inr", hedged=True), FACTS).outcome == MATCH
    assert compare_claim(c("maintenance_charges", 1200, "inr", hedged=True), FACTS).outcome == UNCLEAR


def test_included_in_rent():
    cl = c("maintenance_charges", None, "none", flags=["included_in_rent"])
    assert compare_claim(cl, FACTS).outcome == MISMATCH          # agreement charges 1500
    zero = {"terms": {**FACTS["terms"], "maintenance_charges": {"mentioned": True, "value": 0, "unit": "inr"}}}
    assert compare_claim(cl, zero).outcome == MATCH
    none = {"terms": {**FACTS["terms"], "maintenance_charges": {"mentioned": False}}}
    assert compare_claim(cl, none).outcome == NOT_MENTIONED


def test_unverified_clause_is_unclear():
    f = {"terms": {**FACTS["terms"], "monthly_rent": {"mentioned": True, "value": 18000, "unit": "inr", "verified": False}}}
    assert compare_claim(c("monthly_rent", 18000, "inr"), f).outcome == UNCLEAR


def test_unit_mismatch_is_unclear():
    assert compare_claim(c("monthly_rent", 18000, "days"), FACTS).outcome == UNCLEAR


def test_accepts_bare_terms_dict():
    assert compare_claim(c("monthly_rent", 18000, "inr"), FACTS["terms"]).outcome == MATCH
