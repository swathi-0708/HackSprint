from models import AgreementFact, Claim


agreement_facts = [
    AgreementFact(
        field="monthly_rent",
        value=18000,
        unit="INR",
        source_clause="Clause 4",
        confidence=0.98
    ),

    AgreementFact(
        field="security_deposit",
        value=50000,
        unit="INR",
        source_clause="Clause 5",
        confidence=0.97
    ),

    AgreementFact(
        field="notice_period",
        value=2,
        unit="months",
        source_clause="Clause 8",
        confidence=0.95
    ),

    AgreementFact(
        field="lease_duration",
        value=11,
        unit="months",
        source_clause="Clause 2",
        confidence=0.99
    ),

    AgreementFact(
        field="maintenance_fee",
        value=2000,
        unit="INR",
        source_clause="Clause 6",
        confidence=0.94
    ),
]


claims = [
    Claim(
        field="monthly_rent",
        value=18000,
        unit="INR",
        language="Tamil"
    ),

    Claim(
        field="security_deposit",
        value=30000,
        unit="INR",
        language="Tamil"
    ),

    Claim(
        field="maintenance_fee",
        value=5000,
        unit="INR",
        language="Tamil"
    ),

    Claim(
        field="parking_fee",
        value=1000,
        unit="INR",
        language="Tamil"
    ),
]