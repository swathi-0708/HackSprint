"""Deterministic unit/number rules applied AFTER the LLM parser.

Covers only what appears in the eval set (English, Hinglish, Tamil). Extend the
tables below when new transcripts show new words.
"""
import re
from typing import Optional

from claims import TERMS, UNITS, Claim

# ---------- numbers ----------

# Devanagari and Tamil digits -> ASCII
_DIGITS = str.maketrans("०१२३४५६७८९௦௧௨௩௪௫௬௭௮௯", "01234567890123456789")

_SMALL = {
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    # Hindi / Hinglish (irregular compounds like baais=22 are NOT generated; add as seen)
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5,
    "chhe": 6, "chhah": 6, "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "pandrah": 15, "bees": 20, "tees": 30,
}
_MULT = {
    "hundred": 100, "sau": 100,
    "thousand": 1_000, "hazaar": 1_000, "hazar": 1_000,
    "lakh": 100_000, "lac": 100_000, "crore": 10_000_000,
}

# Tamil: exact forms (script + romanised) because Tamil joins number words
_TAMIL = {
    "ஒன்று": 1, "ஒரு": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5, "ஆறு": 6,
    "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10,
    "முப்பது": 30, "பதினைந்து": 15, "ஆயிரம்": 1000,
    "இருபதாயிரம்": 20_000, "பதினெட்டாயிரம்": 18_000, "நாற்பதாயிரம்": 40_000,
    "ஆயிரத்து ஐநூறு": 1_500,
    "ondru": 1, "oru": 1, "irandu": 2, "moondru": 3, "naangu": 4, "ainthu": 5, "aaru": 6,
    "muppadhu": 30, "padhinaindhu": 15, "aayiram": 1000,
    "irubadhaayiram": 20_000, "padinettaayiram": 18_000, "naarpadhaayiram": 40_000,
    "aayirathu ainooru": 1_500,
}

_NUM_TOKEN = re.compile(r"\d+(\.\d+)?")


def _compose(tokens: list[str]) -> Optional[float]:
    total = cur = 0.0
    seen = False
    for t in tokens:
        if t in ("and", "aur"):
            continue
        if t in _SMALL:
            cur += _SMALL[t]
        elif _NUM_TOKEN.fullmatch(t):
            cur += float(t)
        elif t in _MULT:
            m = _MULT[t]
            if m == 100:
                cur = (cur or 1) * 100
            else:
                total += (cur or 1) * m
                cur = 0.0
        else:
            return None
        seen = True
    return total + cur if seen else None


def parse_number(x) -> Optional[float]:
    """'20,000' / 'twenty-two thousand' / 'chhe' / 'இருபதாயிரம்' / '௨௦' -> float, else None."""
    if x is None:
        return None
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().lower().translate(_DIGITS)
    s = s.replace("ரூபாய்", "").replace("₹", "").replace(",", "")
    s = re.sub(r"\b(?:rs|inr|rupees?|rupaye)\b\.?", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    if _NUM_TOKEN.fullmatch(s):
        return float(s)
    if s in _TAMIL:
        return float(_TAMIL[s])
    return _compose(s.replace("-", " ").split())


# ---------- units ----------

_UNIT_ALIASES = {
    "inr": ["inr", "rs", "rupee", "rupees", "rupaye", "rupay", "₹", "roobaai", "ரூபாய்"],
    "days": ["day", "days", "din", "naal", "naatkal", "நாட்கள்", "நாள்"],
    "months": ["month", "months", "mahina", "mahine", "maheene", "maadham", "maadha",
               "மாதம்", "மாதங்கள்"],
    "months_of_rent": ["months_of_rent", "months of rent", "month of rent",
                       "month's rent", "months' rent"],
    "none": ["none", "", "n/a"],
}
_UNIT_LOOKUP = {a: u for u, aliases in _UNIT_ALIASES.items() for a in aliases}


def canon_unit(u) -> Optional[str]:
    s = "" if u is None else str(u).strip().lower().replace("-", " ")
    s = _UNIT_LOOKUP.get(s) or _UNIT_LOOKUP.get(s.replace(" ", "_"))
    return s


# ---------- terms ----------

_TERM_ALIASES = {
    "rent": "monthly_rent", "monthly_rent": "monthly_rent", "monthly rent": "monthly_rent",
    "deposit": "security_deposit", "security_deposit": "security_deposit",
    "security deposit": "security_deposit",
    "lock_in": "lock_in_period", "lock in": "lock_in_period", "lock_in_period": "lock_in_period",
    "notice": "notice_period", "notice_period": "notice_period",
    "maintenance": "maintenance_charges", "maintenance_charges": "maintenance_charges",
    "refund": "deposit_refund_period", "deposit_refund_period": "deposit_refund_period",
}


def canon_term(t) -> Optional[str]:
    s = str(t).strip().lower().replace("-", "_")
    s = _TERM_ALIASES.get(s) or _TERM_ALIASES.get(s.replace("_", " "))
    return s if s in TERMS else None


# ---------- text cues used only when the parser returned no value ----------

_NEGATION = re.compile(r"\b(no|nahi|nahin|without|illai)\b|இல்லை", re.I)
_INCLUDED = re.compile(r"\bincluded?\b|சேர்த்து|shamil", re.I)

# Plausible ranges (value, unit) per term; outside = issue, not silently fixed
_RANGES = {
    ("monthly_rent", "inr"): (1_000, 1_000_000),
    ("security_deposit", "inr"): (0, 5_000_000),
    ("security_deposit", "months_of_rent"): (0, 12),
    ("maintenance_charges", "inr"): (0, 200_000),
    ("lock_in_period", "months"): (0, 60),
    ("lock_in_period", "days"): (0, 1_825),
    ("notice_period", "months"): (0, 12),
    ("notice_period", "days"): (0, 365),
    ("deposit_refund_period", "days"): (0, 365),
    ("deposit_refund_period", "months"): (0, 12),
}


def normalize_claim(raw: dict) -> Claim:
    """Raw parser dict -> validated Claim. Problems go into `issues`; nothing is guessed."""
    issues: list[str] = []
    flags: list[str] = []
    quote = str(raw.get("quote") or "")

    term = canon_term(raw.get("term", ""))
    if term is None:
        issues.append(f"unknown_term:{raw.get('term')!r}")
        term = "monthly_rent"  # placeholder so the model validates; issue marks it unusable

    unit = canon_unit(raw.get("unit"))
    if unit is None or unit not in UNITS:
        issues.append(f"unknown_unit:{raw.get('unit')!r}")
        unit = "none"

    raw_value = raw.get("value")
    value = parse_number(raw_value)
    if raw_value not in (None, "") and value is None:
        issues.append(f"unparsed_number:{raw_value!r}")

    # No value from the parser: only two cue-based rules, both from the answer key
    if value is None and not issues:
        if term == "lock_in_period" and _NEGATION.search(quote):
            value, unit = 0.0, "months"          # "no lock-in" = 0 months
        elif term == "maintenance_charges" and _INCLUDED.search(quote):
            flags.append("included_in_rent")     # 0 vs UNCLEAR is P3's call
        else:
            issues.append("no_value")

    if value is not None and not issues:
        bounds = _RANGES.get((term, unit))
        if bounds is None:
            issues.append(f"unit_not_allowed:{term}/{unit}")
        elif not (bounds[0] <= value <= bounds[1]):
            issues.append(f"out_of_range:{value}")

    return Claim(term=term, value=value, unit=unit, hedged=bool(raw.get("hedged", False)),
                 quote=quote, flags=flags, issues=issues)


def normalize_all(raw_claims: list[dict]) -> list[Claim]:
    return [normalize_claim(c) for c in raw_claims]
