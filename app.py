import streamlit as st

from mock_data import agreement_facts, claims
from compare import compare_claim


st.set_page_config(
    page_title="Agreement Verification",
    page_icon="📄",
    layout="wide"
)


st.title("📄 Agreement Verification Assistant")

st.write(
    "Upload an agreement and verify user claims against it."
)


st.divider()


# --------------------------------
# AGREEMENT UPLOAD
# --------------------------------

st.header("1. Upload Agreement")

uploaded_file = st.file_uploader(
    "Upload your agreement",
    type=["pdf"]
)

if uploaded_file:

    st.success(
        f"Agreement uploaded: {uploaded_file.name}"
    )


# --------------------------------
# CLAIM
# --------------------------------

st.header("2. User Claims")

st.info(
    "Currently using mock voice claims from P2."
)


# --------------------------------
# RESULTS
# --------------------------------

st.header("3. Verification Results")


for claim in claims:

    result = compare_claim(
        claim,
        agreement_facts
    )

    st.subheader(
        claim.field.replace("_", " ").title()
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write("**User said**")

        st.write(
            f"{claim.value} {claim.unit or ''}"
        )

    with col2:

        st.write("**Agreement says**")

        if result.agreement_value is not None:

            st.write(
                f"{result.agreement_value} "
                f"{claim.unit or ''}"
            )

        else:

            st.write("Not mentioned")


    # RESULT CARD

    if result.outcome == "MATCH":

        st.success(
            "✅ MATCH"
        )

    elif result.outcome == "MISMATCH":

        st.error(
            "❌ MISMATCH"
        )

    elif result.outcome == "NOT MENTIONED":

        st.warning(
            "⚠️ NOT MENTIONED"
        )

    elif result.outcome == "UNCLEAR":

        st.warning(
            "❓ UNCLEAR"
        )


    st.write(
        result.explanation
    )


    if result.source_clause:

        st.caption(
            f"📍 Source: {result.source_clause}"
        )

    st.divider()