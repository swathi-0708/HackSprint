from models import (
    MATCH,
    MISMATCH,
    NOT_MENTIONED,
    UNCLEAR,
    ComparisonResult
)


def compare_claim(claim, agreement_facts):

    matching_facts = [
        fact
        for fact in agreement_facts
        if fact.field == claim.field
    ]

    # Nothing found in agreement
    if len(matching_facts) == 0:

        return ComparisonResult(
            field=claim.field,
            claim_value=claim.value,
            agreement_value=None,
            outcome=NOT_MENTIONED,
            explanation="This information was not mentioned in the agreement."
        )

    # Multiple possible facts
    if len(matching_facts) > 1:

        return ComparisonResult(
            field=claim.field,
            claim_value=claim.value,
            agreement_value=None,
            outcome=UNCLEAR,
            explanation="Multiple possible values were found."
        )

    fact = matching_facts[0]

    # Compare values
    if claim.value == fact.value and claim.unit == fact.unit:

        return ComparisonResult(
            field=claim.field,
            claim_value=claim.value,
            agreement_value=fact.value,
            outcome=MATCH,
            source_clause=fact.source_clause,
            explanation="The claim matches the agreement."
        )

    else:

        return ComparisonResult(
            field=claim.field,
            claim_value=claim.value,
            agreement_value=fact.value,
            outcome=MISMATCH,
            source_clause=fact.source_clause,
            explanation="The claim does not match the agreement."
        )