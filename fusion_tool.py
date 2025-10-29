import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fusion Proofing Assignment Tool", layout="centered")

st.title("Fusion Proofing Assignment Tool")

# Upload Excel file
uploaded_file = st.file_uploader("Upload Fusion Assignment Excel", type=[".xlsx"])

if uploaded_file:
    try:
        data = pd.read_excel(uploaded_file)
        st.success("Excel file loaded successfully!")

        # Clean column names
        data.columns = data.columns.str.strip().str.lower().str.replace(" ", "_")

        # User input widgets
        countries = st.multiselect("Select Country Stakeholder(s):", options=sorted(data['country'].dropna().unique()))
        categories = st.multiselect("Select Category(s):", options=sorted(data['category'].dropna().unique()))
        project_types = st.multiselect("Select Project Type(s):", options=sorted(data['project_type'].dropna().unique()))

        # Apply filtering logic
        def matches(row):
            def match(col, selected):
                if pd.isna(row[col]) or not selected:
                    return True
                row_values = [x.strip().lower() for x in str(row[col]).split(",")]
                return any(val.lower() in row_values for val in selected)

            return (
                match('country', countries) and
                match('category', categories) and
                match('project_type', project_types)
            )

        filtered = data[data.apply(matches, axis=1)]

        st.markdown("---")
        st.subheader(f"Matching Assignments ({len(filtered)} found)")

        if not filtered.empty:
            st.dataframe(filtered[['name', 'team']].drop_duplicates().reset_index(drop=True))
        else:
            st.warning("No matching assignments found.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload an Excel file with columns: name, country, category, project_type, team.")
