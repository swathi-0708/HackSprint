"""Assemble AgreementFacts (contract in the brief) from Sarvam Extract + Digitise output."""
import logging
import re
from datetime import datetime, timezone

from rapidfuzz import fuzz

from . import cache
from .config import LANGUAGE, VERIFY_THRESHOLD
from .terms import KEYWORDS, TERMS, UNITS

log = logging.getLogger("doc_engine")


def norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[*#|_`>]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _find_term_dict(result):
    """Extract result should mirror the schema. Be defensive about a wrapper level."""
    if not isinstance(result, dict):
        return {}
    if any(t in result for t in TERMS):
        return result
    for v in result.values():
        if isinstance(v, dict) and any(t in v for t in TERMS):
            return v
    return {}


def _find_conf(ann, term):
    """Best-effort confidence for a term's value from Extract annotations (shape unverified)."""
    if not isinstance(ann, dict):
        return None
    node = ann.get(term)
    if node is None:
        for v in ann.values():
            if isinstance(v, dict) and term in v:
                node = v[term]
                break
    found = []

    def walk(n, key=None):
        if isinstance(n, dict):
            if isinstance(n.get("confidence"), (int, float)):
                found.append((key, float(n["confidence"])))
            for k, v in n.items():
                walk(v, k)
        elif isinstance(n, list):
            for v in n:
                walk(v, key)
    walk(node)
    if not found:
        return None
    for k, c in found:
        if k == "value":
            return c
    return found[0][1]


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else f


def verify_clause(clause, pages):
    """Return (verified, score 0-100, page). Fuzzy-match the clause against digitised text."""
    c = norm(clause)
    if not c:
        return False, None, None
    full = norm(" ".join(p["text"] for p in pages))
    best_page, best = None, 0.0
    for p in pages:
        s = fuzz.partial_ratio(c, norm(p["text"]))
        if s > best:
            best, best_page = s, p["page"]
    score = max(best, fuzz.partial_ratio(c, full))
    ok = score >= VERIFY_THRESHOLD
    return ok, round(score, 1), (best_page if ok else None)


def build_facts(path, agreement_id, sha, digitise, extract, job_ids):
    pages = digitise["pages"]
    full_norm = norm(" ".join(p["text"] for p in pages))
    raw = _find_term_dict(extract.get("result"))
    terms = {}
    for t in TERMS:
        r = raw.get(t) or {}
        mentioned = bool(r.get("mentioned"))
        value = _num(r.get("value")) if mentioned else None
        unit = r.get("unit") if r.get("unit") in UNITS else "none"
        clause = (r.get("clause_text") or "").strip() or None
        if not mentioned:
            clause, value, unit = None, None, "none"
        verified, score, page = verify_clause(clause, pages) if mentioned else (False, None, None)
        terms[t] = {
            "mentioned": mentioned, "value": value, "unit": unit,
            "clause_text": clause, "verified": verified, "verification_score": score,
            "page": page, "confidence": _find_conf(extract.get("annotations"), t),
            "keyword_hit": any(k in full_norm for k in KEYWORDS[t]),
        }
    return {
        "agreement_id": agreement_id,
        "source_file": str(path).replace("\\", "/").split("/")[-1],
        "pages": max([p["page"] or 0 for p in pages] + [len(pages)]),
        "language": LANGUAGE,
        "terms": terms,
        "digitised_text": "\n\n".join(p["text"] for p in pages),
        # Digitise get_results gives page-level text only, so one block per page, bbox null.
        "blocks": [{"block_id": f"p{p['page']}", "page": p["page"], "text": p["text"], "bbox": None}
                   for p in pages],
        "meta": {**job_ids, "sha256": sha, "created_at": datetime.now(timezone.utc).isoformat()},
    }


def build_agreement_facts(pdf_path, client=None, cache_dir=None, force=False):
    """Main entry. Cached by file hash: a second call makes zero API calls."""
    sha = cache.sha256_file(pdf_path)
    aid = sha[:12]
    if not force:
        hit = cache.load(aid, "facts", cache_dir)
        if hit:
            log.info("cache hit: facts %s", aid)
            return hit
    dig = None if force else cache.load(aid, "digitise_raw", cache_dir)
    ext = None if force else cache.load(aid, "extract_raw", cache_dir)
    if dig is None or ext is None:
        if client is None:
            from .client import DocClient
            client = DocClient()
        dj, ej = client.submit(pdf_path)
        status = client.wait_all([dj, ej])
        bad = {j: s for j, s in status.items() if s in ("failed", "rejected")}
        if bad:
            raise RuntimeError(f"Document AI job(s) did not succeed: {bad}")
        if "partially_completed" in status.values():
            log.warning("partially_completed job(s): %s (some pages may be missing)", status)
        dig, ext = client.digitise_result(dj), client.extract_result(ej)
        cache.save(aid, "digitise_raw", dig, cache_dir)
        cache.save(aid, "extract_raw", ext, cache_dir)
    facts = build_facts(pdf_path, aid, sha, dig, ext,
                        {"extract_job_id": ext.get("job_id"), "digitise_job_id": dig.get("job_id")})
    cache.save(aid, "facts", facts, cache_dir)
    return facts
