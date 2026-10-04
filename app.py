import streamlit as st

from mock_data import agreement_facts, claims
from compare import compare_claim


st.title("📄 Document Verification Assistant")

st.write(
    "Compare user claims with facts extracted from an agreement."
)

st.divider()

st.header("Verification Results")

for claim in claims:

    result = compare_claim(claim, agreement_facts)

    st.subheader(claim.field.replace("_", " ").title())

    col1, col2 = st.columns(2)

    with col1:
        st.write("**User said:**")
        st.write(f"{claim.value} {claim.unit or ''}")

    with col2:
        st.write("**Agreement says:**")
        if result.agreement_value is not None:
            st.write(f"{result.agreement_value} {claim.unit or ''}")
        else:
            st.write("Not found")

    if result.outcome == "MATCH":
        st.success("✅ MATCH")

    elif result.outcome == "CONTRADICTION":
        st.error("❌ CONTRADICTION")

    elif result.outcome == "NOT_FOUND":
        st.warning("⚠️ NOT FOUND")

    elif result.outcome == "AMBIGUOUS":
        st.warning("❓ AMBIGUOUS")

    if result.explanation:
        st.caption(result.explanation)

    if result.source_clause:
        st.caption(f"Source: {result.source_clause}")

    st.divider()