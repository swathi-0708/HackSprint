"""Score cached facts against hand-written labels. No API calls.
Usage: python eval/doc/evaluate.py   (reads data/labels/*.json and data/cache/<id>/facts.json)"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from doc_engine.terms import TERMS  # noqa: E402


def score(facts, label):
    rows = []
    for t in TERMS:
        f, l = facts["terms"][t], label[t]
        m_ok = f["mentioned"] == l["mentioned"]
        v_ok = m_ok and (not l["mentioned"] or (f["value"] == l["value"] and f["unit"] == l["unit"]))
        rows.append((t, m_ok, v_ok, f["verified"] if l["mentioned"] else None))
    return rows


def main():
    tot = ok_m = ok_v = ver = ver_n = 0
    for lp in sorted((ROOT / "data" / "labels").glob("*.json")):
        fp = ROOT / "data" / "cache" / lp.stem / "facts.json"
        if not fp.exists():
            print(f"[skip] {lp.stem}: no cached facts")
            continue
        facts, label = json.loads(fp.read_text()), json.loads(lp.read_text())
        print(f"\n== {lp.stem} ({facts['source_file']})")
        for t, m, v, vr in score(facts, label):
            print(f"  {t:22} mentioned={'OK ' if m else 'BAD'} value+unit={'OK ' if v else 'BAD'} verified={vr}")
            tot += 1; ok_m += m; ok_v += v
            if vr is not None:
                ver_n += 1; ver += bool(vr)
    if tot:
        print(f"\nmentioned accuracy: {ok_m}/{tot}  value+unit accuracy: {ok_v}/{tot}  clause verified: {ver}/{ver_n}")


if __name__ == "__main__":
    main()
