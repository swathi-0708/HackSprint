"""CLI: python -m doc_engine.run data/agreements/foo.pdf [--force]"""
import argparse
import json
import logging

from .build import build_agreement_facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--force", action="store_true", help="ignore cache (costs credits)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    f = build_agreement_facts(a.pdf, force=a.force)
    print(f"agreement_id={f['agreement_id']} pages={f['pages']}")
    for t, v in f["terms"].items():
        print(f"{t:22} mentioned={v['mentioned']!s:5} value={v['value']} {v['unit']:14} "
              f"verified={v['verified']} score={v['verification_score']} page={v['page']} kw={v['keyword_hit']}")
    print("full facts in data/cache/%s/facts.json" % f["agreement_id"])


if __name__ == "__main__":
    main()
