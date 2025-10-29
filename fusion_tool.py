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

        # Improved logic: Only rows that match ALL selected filters
        def matches(row):
            def field_matches(rule_val, selected_vals):
                if not selected_vals:
                    return True  # no filtering on this field
                if pd.isna(rule_val) or str(rule_val).strip() == '':
                    return False  # field must match, but rule is blank (not eligible)
                rule_set = set([x.strip().lower() for x in str(rule_val).split(',')])
                return any(sv.lower() in rule_set for sv in selected_vals)

            conditions = []
            if countries:
                conditions.append(field_matches(row.get('country', ''), countries))
            if categories:
                conditions.append(field_matches(row.get('category', ''), categories))
            if project_types:
                conditions.append(field_matches(row.get('project_type', ''), project_types))

            return all(conditions)

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
