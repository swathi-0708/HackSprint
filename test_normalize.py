"""24 answer-key claims (clips 1-10, T1-T8) as raw parser output -> expected normalized claim.

Raw values mimic what Saaras/the parser may return: words, digits or Tamil script.
"""
import pytest

from normalize import canon_unit, normalize_claim, parse_number

# (clip, raw parser dict, expected (term, value, unit, hedged))
CASES = [
    (1, dict(term="monthly_rent", value="twenty thousand", unit="rupees"),
     ("monthly_rent", 20000, "inr", False)),
    (2, dict(term="security_deposit", value="two", unit="months_of_rent"),
     ("security_deposit", 2, "months_of_rent", False)),
    (3, dict(term="security_deposit", value="do", unit="months_of_rent"),
     ("security_deposit", 2, "months_of_rent", False)),
    (3, dict(term="notice_period", value="ek", unit="mahine"),
     ("notice_period", 1, "months", False)),
    (4, dict(term="lock_in_period", value=None, unit="none", quote="There's no lock-in period."),
     ("lock_in_period", 0, "months", False)),
    (5, dict(term="maintenance_charges", value="fifteen hundred", unit="inr", hedged=True),
     ("maintenance_charges", 1500, "inr", True)),
    (6, dict(term="monthly_rent", value="eighteen thousand", unit="inr"),
     ("monthly_rent", 18000, "inr", False)),
    (6, dict(term="security_deposit", value="40,000", unit="rupees"),
     ("security_deposit", 40000, "inr", False)),
    (6, dict(term="deposit_refund_period", value="thirty", unit="days"),
     ("deposit_refund_period", 30, "days", False)),
    (7, dict(term="lock_in_period", value="chhe", unit="mahine"),
     ("lock_in_period", 6, "months", False)),
    (8, dict(term="notice_period", value="fifteen", unit="days"),
     ("notice_period", 15, "days", False)),
    (9, dict(term="maintenance_charges", value=None, unit="none",
             quote="Maintenance rent mein hi included hai."),
     ("maintenance_charges", None, "none", False)),
    (10, dict(term="monthly_rent", value="twenty-two thousand", unit="inr"),
     ("monthly_rent", 22000, "inr", False)),
    (10, dict(term="security_deposit", value="three", unit="months_of_rent"),
     ("security_deposit", 3, "months_of_rent", False)),
    (10, dict(term="lock_in_period", value="eleven", unit="months"),
     ("lock_in_period", 11, "months", False)),
    (10, dict(term="notice_period", value="two", unit="months"),
     ("notice_period", 2, "months", False)),
    ("T1", dict(term="monthly_rent", value="இருபதாயிரம்", unit="ரூபாய்"),
     ("monthly_rent", 20000, "inr", False)),
    ("T2", dict(term="security_deposit", value="இரண்டு", unit="months_of_rent"),
     ("security_deposit", 2, "months_of_rent", False)),
    ("T4", dict(term="lock_in_period", value=None, unit="none",
                quote="லாக்-இன் பீரியட் எதுவும் இல்லை."),
     ("lock_in_period", 0, "months", False)),
    ("T5", dict(term="maintenance_charges", value="ஆயிரத்து ஐநூறு", unit="ரூபாய்", hedged=True),
     ("maintenance_charges", 1500, "inr", True)),
    ("T6", dict(term="monthly_rent", value="பதினெட்டாயிரம்", unit="inr"),
     ("monthly_rent", 18000, "inr", False)),
    ("T6", dict(term="security_deposit", value="நாற்பதாயிரம்", unit="inr"),
     ("security_deposit", 40000, "inr", False)),
    ("T6", dict(term="deposit_refund_period", value="முப்பது", unit="நாட்கள்"),
     ("deposit_refund_period", 30, "days", False)),
    ("T8", dict(term="notice_period", value="பதினைந்து", unit="days"),
     ("notice_period", 15, "days", False)),
]


def test_case_count_matches_answer_key():
    assert len(CASES) == 24


@pytest.mark.parametrize("clip,raw,expected", CASES, ids=[f"clip{c}-{r['term']}" for c, r, _ in CASES])
def test_answer_key(clip, raw, expected):
    c = normalize_claim(raw)
    assert c.issues == []
    assert (c.term, c.value, c.unit, c.hedged) == expected


def test_included_in_rent_is_flagged_not_zeroed():
    c = normalize_claim(CASES[11][1])
    assert c.value is None and c.flags == ["included_in_rent"]


def test_months_to_days_fixed_rule():
    assert normalize_claim(dict(term="notice_period", value="ek", unit="mahine")).in_days() == 30
    assert normalize_claim(dict(term="notice_period", value="fifteen", unit="days")).in_days() == 15
    assert normalize_claim(dict(term="monthly_rent", value=20000, unit="inr")).in_days() is None


@pytest.mark.parametrize("text,val", [
    ("₹20,000", 20000), ("Rs. 18000", 18000), ("२०००", 2000), ("௨௦", 20),
    ("two lakh", 200000), ("one hundred twenty", 120), ("1.5 lakh", 150000),
    ("hazaar", 1000), ("aayiram", 1000),
])
def test_parse_number_variants(text, val):
    assert parse_number(text) == val


def test_unknown_words_are_not_guessed():
    assert parse_number("banana") is None
    c = normalize_claim(dict(term="monthly_rent", value="baais hazaar", unit="inr"))
    assert any(i.startswith("unparsed_number") for i in c.issues)


def test_bad_unit_and_term_and_range_become_issues():
    assert any("unknown_unit" in i for i in normalize_claim(dict(term="monthly_rent", value=1, unit="parsecs")).issues)
    assert any("unknown_term" in i for i in normalize_claim(dict(term="pets", value=1, unit="none")).issues)
    assert any("out_of_range" in i for i in normalize_claim(dict(term="monthly_rent", value=5, unit="inr")).issues)
    assert any("unit_not_allowed" in i for i in normalize_claim(dict(term="monthly_rent", value=2, unit="months")).issues)
    assert normalize_claim(dict(term="notice_period", value=None, unit="none", quote="")).issues == ["no_value"]


def test_unit_aliases():
    assert canon_unit("ரூபாய்") == "inr" and canon_unit("din") == "days" and canon_unit("Mahine") == "months"
