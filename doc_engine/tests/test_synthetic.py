"""Labels must match the committed synthetic PDFs (hash = agreement_id). No network."""
import hashlib
import json
from pathlib import Path

import pytest

from doc_engine.terms import TERMS, UNITS

ROOT = Path(__file__).resolve().parents[2]
SYN = ROOT / "data" / "agreements" / "synthetic"
LAB = ROOT / "data" / "labels"


def test_every_synthetic_pdf_has_valid_label():
    pdfs = sorted(SYN.glob("*.pdf"))
    assert len(pdfs) >= 5
    for p in pdfs:
        aid = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        lp = LAB / f"{aid}.json"
        assert lp.exists(), f"{p.name}: no label {aid}.json (regenerate or PDF changed)"
        lab = json.loads(lp.read_text())
        assert set(lab) == set(TERMS)
        for t, v in lab.items():
            assert v["unit"] in UNITS
            assert v["mentioned"] or (v["value"] is None and v["unit"] == "none")


def test_keywords_absent_when_term_absent():
    """Only syn_B maintenance is allowed to be keyword-only; others absent terms must have no keyword."""
    pypdf = pytest.importorskip("pypdf")
    from doc_engine.build import norm
    from doc_engine.terms import KEYWORDS
    for p in SYN.glob("*.pdf"):
        text = norm(" ".join(pg.extract_text() for pg in pypdf.PdfReader(p).pages))
        aid = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        lab = json.loads((LAB / f"{aid}.json").read_text())
        for t in TERMS:
            hit = any(k in text for k in KEYWORDS[t])
            if not lab[t]["mentioned"]:
                expected_hit = (p.name.startswith("syn_B") and t == "maintenance_charges")
                assert hit == expected_hit, f"{p.name} {t} keyword_hit={hit}"
