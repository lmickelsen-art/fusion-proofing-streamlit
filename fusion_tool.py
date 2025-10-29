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

        def extract_unique_values(column):
            if column not in data.columns:
                return []
            split_values = data[column].dropna().astype(str).str.split(',')
            flat_list = [item.strip() for sublist in split_values for item in sublist]
            return sorted(set(flat_list))

        countries = st.multiselect("Select Country Stakeholder(s):", options=extract_unique_values('country'))
        categories = st.multiselect("Select Category(s):", options=extract_unique_values('category'))
        project_types = st.multiselect("Select Project Type(s):", options=extract_unique_values('project_type'))

        # Matching logic based on required AND across selected fields, but row values can wildcard if blank
        def matches(row):
            def is_match(rule_values, selected_values):
                if pd.isna(rule_values) or str(rule_values).strip() == '':
                    return True  # wildcard
                rule_set = set([val.strip().lower() for val in str(rule_values).split(',') if val.strip()])
                return bool(rule_set.intersection([v.lower() for v in selected_values]))

            # If user selected a filter, row must pass it; if user didn't, ignore that field
            if countries and not is_match(row.get('country', ''), countries):
                return False
            if categories and not is_match(row.get('category', ''), categories):
                return False
            if project_types and not is_match(row.get('project_type', ''), project_types):
                return False
            return True

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
