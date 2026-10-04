"""Score cached facts against hand-written labels. No API calls.
Usage: python eval/doc/evaluate.py [--cache-dir DIR] [--out eval/doc/RESULTS.txt]
Reads data/labels/*.json and <cache-dir>/<id>/facts.json.
Label term keys: mentioned, value, unit, and optional keyword_hit (checked only if present).
--out writes UTF-8 (avoids the UTF-16 file PowerShell '>' creates)."""
import argparse
import io
import json
import sys
from contextlib import redirect_stdout
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
        k_ok = None if "keyword_hit" not in l else (f["keyword_hit"] == l["keyword_hit"])
        rows.append((t, m_ok, v_ok, f["verified"] if l["mentioned"] else None, k_ok))
    return rows


def run(cache_dir):
    tot = ok_m = ok_v = ver = ver_n = kw = kw_n = 0
    for lp in sorted((ROOT / "data" / "labels").glob("*.json")):
        if lp.stem.startswith("_"):
            continue
        fp = Path(cache_dir) / lp.stem / "facts.json"
        if not fp.exists():
            print(f"[skip] {lp.stem}: no cached facts")
            continue
        facts, label = json.loads(fp.read_text(encoding="utf-8")), json.loads(lp.read_text(encoding="utf-8"))
        print(f"\n== {lp.stem} ({facts['source_file']})")
        for t, m, v, vr, k in score(facts, label):
            ktxt = "" if k is None else f" keyword_hit={'OK ' if k else 'BAD'}"
            print(f"  {t:22} mentioned={'OK ' if m else 'BAD'} value+unit={'OK ' if v else 'BAD'} verified={vr}{ktxt}")
            tot += 1; ok_m += m; ok_v += v
            if vr is not None:
                ver_n += 1; ver += bool(vr)
            if k is not None:
                kw_n += 1; kw += bool(k)
    if tot:
        print(f"\nmentioned accuracy: {ok_m}/{tot}  value+unit accuracy: {ok_v}/{tot}  "
              f"clause verified: {ver}/{ver_n}  keyword_hit: {kw}/{kw_n}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default=str(ROOT / "data" / "cache"))
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.out:
        buf = io.StringIO()
        with redirect_stdout(buf):
            run(a.cache_dir)
        Path(a.out).write_text(buf.getvalue(), encoding="utf-8")
        print(buf.getvalue())
    else:
        run(a.cache_dir)


if __name__ == "__main__":
    main()