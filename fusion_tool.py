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

        # Updated logic: only match users whose non-blank criteria all match the user's input (or are blank in rule)
        def matches(row):
            def field_blocks(row_val, selected_vals):
                if pd.isna(row_val) or str(row_val).strip() == '':
                    return False  # rule is wildcard
                if not selected_vals:
                    return True  # if user hasn't selected a filter, a specific rule blocks
                rule_values = set(x.strip().lower() for x in str(row_val).split(',') if x.strip())
                selected_values = set(x.lower() for x in selected_vals)
                return not rule_values.intersection(selected_values)  # True if rule contradicts the selected

            # If any non-blank rule field contradicts selected filter, exclude the row
            if field_blocks(row.get('country', ''), countries):
                return False
            if field_blocks(row.get('category', ''), categories):
                return False
            if field_blocks(row.get('project_type', ''), project_types):
                return False

            return True

        filtered = data[data.apply(matches, axis=1)]

        # Define sort order for team priority
        team_order = ['WIP', 'Content', 'Messaging', 'Management', 'Executive', 'Production']

        def extract_sort_key(team_val):
            for level in team_order:
                if level.lower() in str(team_val).lower():
                    return team_order.index(level)
            return len(team_order)

        if not filtered.empty:
            filtered = filtered.sort_values(by='team', key=lambda col: col.map(extract_sort_key))

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
