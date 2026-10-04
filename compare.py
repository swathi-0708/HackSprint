from models import (
    MATCH,
    CONTRADICTION,
    NOT_FOUND,
    AMBIGUOUS,
    ComparisonResult
)


def compare_claim(claim, agreement_facts):

    matching_facts = [
        fact for fact in agreement_facts
        if fact.field == claim.field
    ]

    # No matching field in agreement
    if len(matching_facts) == 0:
        return ComparisonResult(
            field=claim.field,
            claim_value=claim.value,
            agreement_value=None,
            outcome=NOT_FOUND,
            explanation="This information was not found in the agreement."
        )

    # More than one possible fact
    if len(matching_facts) > 1:
        return ComparisonResult(
            field=claim.field,
            claim_value=claim.value,
            agreement_value=None,
            outcome=AMBIGUOUS,
            explanation="Multiple possible values were found."
        )

    fact = matching_facts[0]

    # Values are exactly the same
    if claim.value == fact.value and claim.unit == fact.unit:
        outcome = MATCH
        explanation = "The claim matches the agreement."

    # Values are different
    else:
        outcome = CONTRADICTION
        explanation = "The claim does not match the agreement."

    return ComparisonResult(
        field=claim.field,
        claim_value=claim.value,
        agreement_value=fact.value,
        outcome=outcome,
        source_clause=fact.source_clause,
        explanation=explanation
    )