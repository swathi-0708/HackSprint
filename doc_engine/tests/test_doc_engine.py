import json
from types import SimpleNamespace as NS

import pytest

from doc_engine import build, cache
from doc_engine.client import DocClient, RateLimiter
from doc_engine.terms import TERMS, UNITS, extract_schema_json

PAGES = [
    {"page": 1, "text": "1. The monthly rent shall be Rs. 15,000 payable by the 5th of each month.\n"
                        "2. The Tenant shall pay a refundable security deposit of Rs. 30,000."},
    {"page": 2, "text": "3. Either party may terminate by giving 30 days written notice.\n"
                        "4. Maintenance charges are included."},
]
EXTRACT = {"job_id": "e1", "status": "completed", "annotations": {}, "result": {
    "monthly_rent": {"mentioned": True, "value": 15000, "unit": "inr",
                     "clause_text": "The monthly rent shall be Rs. 15,000 payable by the 5th of each month."},
    "security_deposit": {"mentioned": True, "value": 30000.0, "unit": "inr",
                         "clause_text": "refundable security deposit of Rs. 30,000"},
    "notice_period": {"mentioned": True, "value": 30, "unit": "days",
                      "clause_text": "terminate by giving 30 days written notice"},
    "lock_in_period": {"mentioned": False, "value": 99, "unit": "months", "clause_text": "invented"},
    "maintenance_charges": {"mentioned": True, "value": 500, "unit": "weird",
                            "clause_text": "Maintenance of Rs 500 is paid to a totally different sentence xyz"},
}}
DIG = {"job_id": "d1", "pages": PAGES}


def facts():
    return build.build_facts("x/a.pdf", "abc123abc123", "f" * 64, DIG, EXTRACT, {"extract_job_id": "e1", "digitise_job_id": "d1"})


def test_all_six_terms_present():
    assert set(facts()["terms"]) == set(TERMS)


def test_verified_and_page():
    t = facts()["terms"]
    assert t["monthly_rent"]["verified"] and t["monthly_rent"]["page"] == 1
    assert t["notice_period"]["verified"] and t["notice_period"]["page"] == 2
    assert t["security_deposit"]["value"] == 30000 and isinstance(t["security_deposit"]["value"], int)


def test_unverified_clause_flagged():
    m = facts()["terms"]["maintenance_charges"]
    assert m["mentioned"] and not m["verified"] and m["page"] is None
    assert m["unit"] == "none"  # invalid unit sanitised


def test_not_mentioned_is_clean_and_never_guessed():
    t = facts()["terms"]["lock_in_period"]
    assert t["mentioned"] is False and t["value"] is None and t["clause_text"] is None


def test_keyword_hit_separate_from_mentioned():
    t = facts()["terms"]
    assert t["deposit_refund_period"]["mentioned"] is False  # absent from extract result
    assert t["maintenance_charges"]["keyword_hit"] is True   # word 'maintenance' is in text
    assert t["lock_in_period"]["keyword_hit"] is False


def test_schema_valid():
    s = json.loads(extract_schema_json())

    def check(n, depth=1):
        assert depth <= 4 and n["type"] in {"string", "number", "integer", "boolean", "object", "array"}
        assert n["description"].strip()
        for c in n.get("properties", {}).values():
            check(c, depth + 1)
    check(s)
    assert s["properties"]["monthly_rent"]["properties"]["unit"]["enum"] == UNITS


def test_cache_means_zero_api_calls(tmp_path):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF-fake")
    aid = cache.agreement_id_for(pdf)
    cache.save(aid, "digitise_raw", DIG, tmp_path)
    cache.save(aid, "extract_raw", EXTRACT, tmp_path)

    class Boom:
        def __getattr__(self, n):
            raise AssertionError("API must not be called")
    f1 = build.build_agreement_facts(pdf, client=Boom(), cache_dir=tmp_path)
    f2 = build.build_agreement_facts(pdf, client=Boom(), cache_dir=tmp_path)
    assert f1["agreement_id"] == aid and f1 == f2


def test_ratelimiter_blocks_after_limit():
    t = {"now": 0.0}
    slept = []
    rl = RateLimiter(max_calls=2, per=60, clock=lambda: t["now"], sleep=lambda s: (slept.append(s), t.update(now=t["now"] + s)))
    for _ in range(3):
        rl.wait()
    assert slept and slept[0] >= 59


class ApiErr(Exception):
    status_code = 429


def test_client_retries_429_and_polls():
    calls = {"status": 0, "dig": 0}

    def digitise(**kw):
        calls["dig"] += 1
        if calls["dig"] == 1:
            raise ApiErr()
        return NS(job_id="d1")

    def get_status(job_id):
        calls["status"] += 1
        return NS(status="completed" if calls["status"] >= 3 else "running")

    sdk = NS(doc_ai=NS(digitise=digitise, extract=lambda **kw: NS(job_id="e1"), get_status=get_status))
    c = DocClient(sdk=sdk, limiter=RateLimiter(max_calls=1000), sleep=lambda s: None, poll_start=0)
    import io, tempfile, os
    p = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); p.write(b"x"); p.close()
    dj, ej = c.submit(p.name)
    os.unlink(p.name)
    assert (dj, ej) == ("d1", "e1") and calls["dig"] == 2
    st = c.wait_all([dj, ej])
    assert st == {"d1": "completed", "e1": "completed"}


def test_failed_job_raises(tmp_path):
    pdf = tmp_path / "a.pdf"; pdf.write_bytes(b"x")

    class C:
        def submit(self, p): return "d", "e"
        def wait_all(self, ids): return {"d": "completed", "e": "failed"}
    with pytest.raises(RuntimeError):
        build.build_agreement_facts(pdf, client=C(), cache_dir=tmp_path)
