"""Generate synthetic printed English rental/PG agreements + hand-set ground-truth labels.
Values are chosen here, so labels do not depend on any model. Deterministic output.
Usage: python eval/doc/gen_agreements.py
Writes PDFs to data/agreements/synthetic/ and labels to data/labels/<agreement_id>.json
Filler clauses deliberately avoid term keywords (deposit, refund, lock-in, notice, maintenance...)
unless a case wants that."""
import hashlib
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "agreements" / "synthetic"
LABELS = ROOT / "data" / "labels"
NM = {"mentioned": False, "value": None, "unit": "none", "keyword_hit": False}
NM_KW = {**NM, "keyword_hit": True}  # word appears in the text but no value is stated


def L(v, u):
    return {"mentioned": True, "value": v, "unit": u}


FILLER = [
    "The Tenant shall use the premises only for residential purposes and shall not carry on any business there.",
    "The Tenant shall not sublet, assign or part with possession of the premises or any part of it to any third party.",
    "The Tenant shall keep the premises clean and shall not cause nuisance or annoyance to neighbours.",
    "The Landlord or his representative may inspect the premises at reasonable hours with prior intimation.",
    "The Tenant shall pay electricity and water bills according to the meter readings directly to the authorities.",
    "The Tenant shall not make structural alterations or drill into walls without written consent of the Landlord.",
    "Pets shall not be kept in the premises without prior permission of the Landlord.",
    "At the end of the tenancy the Tenant shall hand over vacant and peaceful possession along with fixtures and fittings.",
    "This Agreement is governed by the laws of India and courts at the place of the premises shall have jurisdiction.",
    "Any amendment to this Agreement shall be valid only if made in writing and signed by both parties.",
]

CASES = [
    dict(name="syn_A_flat_standard", title="RESIDENTIAL RENTAL AGREEMENT", place="Bengaluru", pages_pad=1,
         clauses=[
             "The Landlord lets the flat to the Tenant for a period of eleven (11) months.",
             "The monthly rent shall be Rs. 18,000 (Rupees Eighteen Thousand only) payable on or before the 5th of each month.",
             "The Tenant has paid a security deposit equivalent to two months' rent, which is interest free.",
             "The security deposit shall be refunded within 30 days of the Tenant vacating the premises.",
             "The Tenant shall remain in the premises for a minimum lock-in period of 6 months.",
             "Either party may end this Agreement by giving one month's written notice.",
             "Maintenance charges of Rs. 1,500 per month shall be paid by the Tenant to the society.",
         ],
         label=dict(monthly_rent=L(18000, "inr"), security_deposit=L(2, "months_of_rent"),
                    deposit_refund_period=L(30, "days"), lock_in_period=L(6, "months"),
                    notice_period=L(1, "months"), maintenance_charges=L(1500, "inr"))),
    dict(name="syn_B_pg_sparse", title="PAYING GUEST ACCOMMODATION AGREEMENT", place="Pune", pages_pad=1,
         clauses=[
             "The Owner provides a shared room with food to the Guest on a monthly basis.",
             "The Guest shall pay Rs. 9,500 per month towards rent, payable in advance by the 1st of each month.",
             "The Guest shall pay a refundable security deposit of Rs. 15,000 at the time of joining.",
             "The deposit will be returned within 15 days after the Guest leaves, subject to no damage.",
             "The Guest must give 30 days notice before vacating.",
             "The Guest shall be responsible for maintenance of the room in good condition during the stay.",
         ],
         label=dict(monthly_rent=L(9500, "inr"), security_deposit=L(15000, "inr"),
                    deposit_refund_period=L(15, "days"), lock_in_period=NM,
                    notice_period=L(30, "days"), maintenance_charges=NM_KW)),  # keyword 'maintenance' present, no charge
    dict(name="syn_C_indian_format", title="LEAVE AND LICENSE / RENT AGREEMENT", place="Mumbai", pages_pad=2,
         clauses=[
             "The term of this tenancy is eleven months commencing from the date of execution.",
             "The Tenant shall pay monthly rent of Rs. 25,000/- (Rupees Twenty Five Thousand only).",
             "The Tenant has paid an interest-free refundable security deposit of Rs. 1,50,000/- (Rupees One Lakh Fifty Thousand only).",
             "The Landlord shall refund the security deposit within 1 month from the date of handing over possession.",
             "There shall be a lock-in period of 11 months during which neither party can terminate this Agreement.",
             "After the lock-in period, either party may terminate by giving 2 months prior written notice.",
             "The Tenant shall pay Rs. 2,500 per month as maintenance charges to the housing society.",
         ],
         label=dict(monthly_rent=L(25000, "inr"), security_deposit=L(150000, "inr"),
                    deposit_refund_period=L(1, "months"), lock_in_period=L(11, "months"),
                    notice_period=L(2, "months"), maintenance_charges=L(2500, "inr"))),
    dict(name="syn_D_minimal", title="RENT AGREEMENT", place="Chennai", pages_pad=0,
         clauses=[
             "The Landlord agrees to let the house to the Tenant at a rent of Rs. 12,000 per month.",
             "The Tenant has given Rs. 36,000 as security deposit to the Landlord.",
             "Termination of this Agreement by the Tenant requires 60 days written intimation.",
         ],
         label=dict(monthly_rent=L(12000, "inr"), security_deposit=L(36000, "inr"),
                    deposit_refund_period=NM, lock_in_period=NM,
                    notice_period=L(60, "days"), maintenance_charges=NM)),
    dict(name="syn_E_distractors_long", title="RESIDENTIAL TENANCY AGREEMENT", place="Hyderabad", pages_pad=4,
         clauses=[
             "The tenancy shall be for twelve months from the date mentioned above.",
             "Rent for the first year is Rs. 30,000 per month. The rent will increase by 5% at renewal.",
             "A late fee of Rs. 500 per day shall be charged if rent is paid after the 10th of the month.",
             "The Tenant shall pay an electricity meter deposit of Rs. 2,000 to the electricity board directly.",
             "The Tenant has paid a security deposit of Rs. 90,000 to the Landlord.",
             "The Landlord shall refund the security deposit within 45 days after vacant possession is handed over.",
             "The Tenant agrees to a lock-in of 3 months from the start date.",
             "The Tenant shall give 15 days notice if he wishes to leave after the lock-in.",
             "Maintenance charges of Rs. 800 per month are payable by the Tenant to the apartment association.",
         ],
         label=dict(monthly_rent=L(30000, "inr"), security_deposit=L(90000, "inr"),
                    deposit_refund_period=L(45, "days"), lock_in_period=L(3, "months"),
                    notice_period=L(15, "days"), maintenance_charges=L(800, "inr"))),
]


def build(case):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{case['name']}.pdf"
    ss = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, invariant=1, title=case["title"],
                            leftMargin=60, rightMargin=60, topMargin=60, bottomMargin=60)
    flow = [Paragraph(f"<b>{case['title']}</b>", ss["Title"]),
            Paragraph(f"This Agreement is made at {case['place']} between the Landlord and the Tenant "
                      "(names withheld; sample document for software testing).", ss["BodyText"]), Spacer(1, 12)]
    n = 1
    for c in case["clauses"]:
        flow += [Paragraph(f"{n}. {c}", ss["BodyText"]), Spacer(1, 8)]
        n += 1
    for i in range(case["pages_pad"]):
        flow.append(PageBreak())
        for c in FILLER[(i * 4) % len(FILLER):] + FILLER[:(i * 4) % len(FILLER)]:
            flow += [Paragraph(f"{n}. {c}", ss["BodyText"]), Spacer(1, 8)]
            n += 1
    flow += [Spacer(1, 30), Paragraph("Landlord: ____________________ &nbsp;&nbsp;&nbsp; Tenant: ____________________", ss["BodyText"])]
    doc.build(flow)
    return path


def main():
    LABELS.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        p = build(case)
        aid = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        (LABELS / f"{aid}.json").write_text(json.dumps(case["label"], indent=2), encoding="utf-8")
        print(f"{p.name}  agreement_id={aid}")


if __name__ == "__main__":
    main()