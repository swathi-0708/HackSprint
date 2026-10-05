"""Offline demo of the full chain: sample agreement + sample voice note -> results.
Run: python test.py [clip_id]   (default clip 6)"""
import sys

import services
from compare import compare_all

clip_id = sys.argv[1] if len(sys.argv) > 1 else "6"
clip = next(c for c in services.sample_clips() if str(c["id"]) == clip_id)
facts = services.demo_agreements()["syn_A_flat_standard"]
res = services.claims_from_sample(clip, live=False)
print("Heard:", res["transcript"], f"[{res['source']}]")
for r in compare_all(res["claims"], facts):
    print(f"{r.term:22} {r.outcome:14} said={r.said_value} {r.said_unit} | agreement={r.agreement_value} {r.agreement_unit} | {r.reason}")
