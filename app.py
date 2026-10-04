import streamlit as st

st.title("📄 Agreement Verification Assistant")

st.write("Upload an agreement and verify claims against it.")

st.divider()

st.header("Upload Agreement")

uploaded_file = st.file_uploader(
    "Choose an agreement",
    type=["pdf"]
)

if uploaded_file is not None:
    st.success("Agreement uploaded successfully!")

    st.write("File:", uploaded_file.name)