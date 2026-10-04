from mock_data import agreement_facts, claims
from compare import compare_claim


for claim in claims:

    result = compare_claim(claim, agreement_facts)

    print("--------------------")
    print("Field:", result.field)
    print("User said:", result.claim_value)
    print("Agreement says:", result.agreement_value)
    print("Result:", result.outcome)
    print("Explanation:", result.explanation)

    if result.source_clause:
        print("Source:", result.source_clause)